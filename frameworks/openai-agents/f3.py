import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import asyncio  # noqa: E402

from agents import (Agent, OpenAIChatCompletionsModel, Runner, RunState, function_tool,  # noqa: E402
                    set_tracing_disabled)
from f3 import (API_KEY, APPROVED, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, REJECT_MESSAGE, STATE,  # noqa: E402
                STEP, save_final, save_pending)
from openai import AsyncOpenAI  # noqa: E402
from sitetools import assign_issue, get_issue, list_crew  # noqa: E402

set_tracing_disabled(True)
agent = Agent(
    name="assigner",
    instructions=INSTRUCTIONS,
    model=OpenAIChatCompletionsModel(model=MODEL, openai_client=AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)),
    tools=[function_tool(get_issue), function_tool(list_crew), function_tool(assign_issue, needs_approval=True)],
)


async def main() -> None:
    if STEP == "start":
        result = await Runner.run(agent, PROMPT)
        item = result.interruptions[0]
        save_pending(item.tool_name, item.raw_item.arguments)
        STATE.write_text(result.to_state().to_string())  # 대기 중인 실행 상태를 직렬화해 둔다
    else:
        state = await RunState.from_string(agent, STATE.read_text())
        for item in state.get_interruptions():
            if APPROVED:
                state.approve(item)
            else:
                state.reject(item, rejection_message=REJECT_MESSAGE)
        save_final((await Runner.run(agent, state)).final_output)


asyncio.run(main())
