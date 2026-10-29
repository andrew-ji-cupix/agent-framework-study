import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from f3 import (API_KEY, APPROVED, BASE_URL, DIR, INSTRUCTIONS, MODEL, PROMPT, REJECT_MESSAGE,  # noqa: E402
                STATE, STEP, save_final, save_pending)
from sitetools import assign_issue, get_issue, list_crew  # noqa: E402
from strands import Agent, tool  # noqa: E402
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry  # noqa: E402
from strands.models.openai import OpenAIModel  # noqa: E402
from strands.session.file_session_manager import FileSessionManager  # noqa: E402


class ApproveAssignments(HookProvider):
    """assign_issue 실행 직전에 멈추고(interrupt) 사람의 답을 기다린다."""

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self.check)

    def check(self, event: BeforeToolCallEvent) -> None:
        if event.tool_use["name"] != "assign_issue":
            return
        answer = event.interrupt("approve_assignment", reason={"tool": "assign_issue", "args": event.tool_use["input"]})
        if answer != "approve":
            event.cancel_tool = REJECT_MESSAGE


agent = Agent(
    model=OpenAIModel(client_args={"base_url": BASE_URL, "api_key": API_KEY}, model_id=MODEL),
    system_prompt=INSTRUCTIONS,
    tools=[tool(get_issue), tool(list_crew), tool(assign_issue)],
    hooks=[ApproveAssignments()],
    session_manager=FileSessionManager(session_id="f3", storage_dir=str(STATE)),  # 대화와 대기 중인 interrupt를 저장
)
if STEP == "start":
    interrupt = agent(PROMPT).interrupts[0]
    save_pending(interrupt.reason["tool"], interrupt.reason["args"])
    (DIR / "interrupt_id").write_text(interrupt.id)
else:
    response = {"interruptId": (DIR / "interrupt_id").read_text(), "response": "approve" if APPROVED else "reject"}
    save_final(str(agent([{"interruptResponse": response}])))
