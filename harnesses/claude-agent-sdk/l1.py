import asyncio
import sys

sys.path.insert(0, "/shared")
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query  # noqa: E402
from ladder import ANTHROPIC_BASE_URL, API_KEY, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402

ENV = {  # OpenRouter의 Anthropic 호환 엔드포인트(프록시 경유). 보조 작업용 모델도 같은 모델로 고정한다
    "ANTHROPIC_BASE_URL": ANTHROPIC_BASE_URL, "ANTHROPIC_AUTH_TOKEN": API_KEY, "ANTHROPIC_API_KEY": "",
    **dict.fromkeys(["ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
                     "ANTHROPIC_DEFAULT_HAIKU_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL"], MODEL),
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "IS_SANDBOX": "1",  # 컨테이너의 root 사용자로 bypassPermissions를 쓰기 위해 필요
}
options = ClaudeAgentOptions(cwd="/workspace", model=MODEL, env=ENV, permission_mode="bypassPermissions",
                             system_prompt={"type": "preset", "preset": "claude_code", "append": INSTRUCTIONS})


async def main() -> None:
    async for message in query(prompt=prompt("l1"), options=options):
        if isinstance(message, ResultMessage):
            save(message.result)


asyncio.run(main())
