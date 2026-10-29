import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from f3 import (API_KEY, APPROVED, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, REJECT_MESSAGE, STATE,  # noqa: E402
                STEP, save_final, save_pending)
from pydantic_ai import (Agent, DeferredToolRequests, DeferredToolResults, ModelMessagesTypeAdapter,  # noqa: E402
                         Tool, ToolDenied)
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from sitetools import assign_issue, get_issue, list_crew  # noqa: E402

agent = Agent(
    OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=BASE_URL, api_key=API_KEY)),
    instructions=INSTRUCTIONS,
    tools=[get_issue, list_crew, Tool(assign_issue, requires_approval=True)],
    output_type=[str, DeferredToolRequests],  # 승인이 필요한 호출이 나오면 실행을 멈추고 요청 목록을 돌려준다
)
if STEP == "start":
    result = agent.run_sync(PROMPT)
    call = result.output.approvals[0]
    save_pending(call.tool_name, call.args)
    STATE.write_bytes(result.all_messages_json())  # 대화 기록 전체를 저장해 두고 다음 실행에 넘긴다
else:
    history = ModelMessagesTypeAdapter.validate_json(STATE.read_bytes())
    call = next(p for p in history[-1].parts if getattr(p, "tool_name", None) == "assign_issue")
    decision = True if APPROVED else ToolDenied(REJECT_MESSAGE)
    result = agent.run_sync(message_history=history,
                            deferred_tool_results=DeferredToolResults(approvals={call.tool_call_id: decision}))
    save_final(result.output)
