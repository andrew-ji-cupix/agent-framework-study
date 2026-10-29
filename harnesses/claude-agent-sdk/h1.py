"""Claude Agent SDK로 하네스 과제를 실행한다. 컨테이너 안에서 /workspace를 대상으로 동작한다."""

import asyncio
import json
import os
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

MODEL = os.environ["LLM_MODEL"]
ENV = {
    # OpenRouter의 Anthropic 호환 엔드포인트(프록시 경유). 보조 작업용 모델도 같은 모델로 고정한다
    "ANTHROPIC_BASE_URL": os.environ["LLM_ANTHROPIC_BASE_URL"],
    "ANTHROPIC_AUTH_TOKEN": os.environ["LLM_API_KEY"],
    "ANTHROPIC_API_KEY": "",
    **dict.fromkeys(["ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
                     "ANTHROPIC_DEFAULT_HAIKU_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL"], MODEL),
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "IS_SANDBOX": "1",  # 컨테이너의 root 사용자로 bypassPermissions를 쓰기 위해 필요
}


async def main() -> None:
    options = ClaudeAgentOptions(
        cwd="/workspace",
        model=MODEL,
        env=ENV,
        system_prompt={"type": "preset", "preset": "claude_code"},
        permission_mode="bypassPermissions",
    )
    result = None
    async for message in query(prompt=Path("/task/prompt.md").read_text(), options=options):
        if isinstance(message, ResultMessage):
            result = message
    Path("/out/final.json").write_text(json.dumps(
        {"result": result.result, "num_turns": result.num_turns, "sdk_cost_usd": result.total_cost_usd},
        ensure_ascii=False))


asyncio.run(main())
