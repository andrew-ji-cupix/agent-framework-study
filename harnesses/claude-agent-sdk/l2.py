import asyncio
import inspect
import json
import sys

sys.path.insert(0, "/shared")
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, create_sdk_mcp_server, query, tool  # noqa: E402
from ladder import ANTHROPIC_BASE_URL, API_KEY, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402

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
options = ClaudeAgentOptions(cwd="/workspace", model=MODEL, env=ENV, permission_mode="bypassPermissions",
                             system_prompt={"type": "preset", "preset": "claude_code", "append": INSTRUCTIONS},
                             mcp_servers={"site": site})


async def main() -> None:
    async for message in query(prompt=prompt("l2"), options=options):
        if isinstance(message, ResultMessage):
            save(message.result)


asyncio.run(main())
