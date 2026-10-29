import asyncio
import inspect
import json
import shutil
import sys

sys.path.insert(0, "/shared")
from claude_agent_sdk import (AgentDefinition, ClaudeAgentOptions, ResultMessage, create_sdk_mcp_server, query,  # noqa: E402
                              tool)
from ladder import (ANTHROPIC_BASE_URL, API_KEY, INSTRUCTIONS, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, SKILLS,  # noqa: E402
                    STEP, prompt, save)  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

ENV = {  # OpenRouter의 Anthropic 호환 엔드포인트(프록시 경유). 보조 작업용 모델도 같은 모델로 고정한다
    "ANTHROPIC_BASE_URL": ANTHROPIC_BASE_URL, "ANTHROPIC_AUTH_TOKEN": API_KEY, "ANTHROPIC_API_KEY": "",
    **dict.fromkeys(["ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
                     "ANTHROPIC_DEFAULT_HAIKU_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL"], MODEL),
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "IS_SANDBOX": "1",  # 컨테이너의 root 사용자로 bypassPermissions를 쓰기 위해 필요
}


def mcp_tool(fn, params: list[str], required: list[str]):
    """파이썬 함수를 SDK 프로세스 안에서 도는 MCP 도구로 감싼다."""
    schema = {"type": "object", "properties": {p: {"type": "string"} for p in params}, "required": required}

    @tool(fn.__name__, inspect.getdoc(fn), schema)
    async def run(args):
        return {"content": [{"type": "text", "text": json.dumps(fn(**args), ensure_ascii=False)}]}
    return run


site = create_sdk_mcp_server("site", tools=[mcp_tool(search_issues, ["level", "trade", "status"], []),
                                            mcp_tool(get_issue, ["issue_id"], ["issue_id"]),
                                            mcp_tool(list_crew, ["trade"], ["trade"])])
# 서브에이전트 정의는 JSON으로 CLI에 넘어가므로 SDK 서버는 options에 두고 이름으로 참조한다.
# 그래서 메인 에이전트도 이 도구를 보게 된다 (disallowed_tools로 막으면 서브에이전트도 막힌다)
progress = create_sdk_mcp_server("progress", tools=[mcp_tool(get_progress, ["level"], [])])
analyst = AgentDefinition(description=PROGRESS_DESC, prompt=PROGRESS_ANALYST, mcpServers=["progress"],
                          tools=["mcp__progress__get_progress"])
# 메모리: 프로젝트 메모리 파일(CLAUDE.md)은 setting_sources=["project"]로 다음 대화를 시작할 때 자동으로 읽힌다
MEMORY_RULE = "\n다음 대화에서도 지켜야 할 사용자 요청은 /workspace/CLAUDE.md에 적어 두세요."
shutil.copytree(SKILLS, "/workspace/.claude/skills", dirs_exist_ok=True)  # 프로젝트 스킬 위치
options = ClaudeAgentOptions(cwd="/workspace", model=MODEL, env=ENV, permission_mode="bypassPermissions",
                             system_prompt={"type": "preset", "preset": "claude_code", "append": INSTRUCTIONS + MEMORY_RULE},
                             mcp_servers={"site": site, "progress": progress}, setting_sources=["project"],
                             agents={"progress-analyst": analyst})


async def main() -> None:
    async for message in query(prompt=prompt(f"l5-{STEP}"), options=options):
        if isinstance(message, ResultMessage):
            save(message.result, "remember" if STEP == "remember" else "output")


asyncio.run(main())
