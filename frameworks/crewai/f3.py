import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from crewai import LLM, Agent  # noqa: E402
from crewai.flow import Flow, human_feedback, listen, start  # noqa: E402
from crewai.flow.async_feedback import HumanFeedbackPending  # noqa: E402
from crewai.flow.persistence import SQLiteFlowPersistence  # noqa: E402
from crewai.tools import tool  # noqa: E402
from f3 import (API_KEY, APPROVED, BASE_URL, DIR, INSTRUCTIONS, MODEL, PROMPT, REJECT_MESSAGE,  # noqa: E402
                STATE, STEP, save_final, save_pending)
from pydantic import BaseModel  # noqa: E402
from sitetools import assign_issue, get_issue, list_crew  # noqa: E402


class Assignment(BaseModel):
    issue_id: str
    assignee: str


class WaitForApproval:
    """승인 요청만 남기고 Flow를 멈춘다. 답은 다른 프로세스에서 resume()으로 받는다."""

    def request_feedback(self, context, flow):
        raise HumanFeedbackPending(context=context)


class AssignFlow(Flow):
    # CrewAI는 도구 호출 단위로 멈춰 다른 프로세스에서 재개하는 기능이 없다.
    # 그래서 에이전트는 배정안만 만들고, Flow가 승인을 기다린 뒤 코드에서 실행한다.
    @start()
    @human_feedback(message="이 배정을 승인할까요?", provider=WaitForApproval())
    def propose(self):
        agent = Agent(role="현장 이슈 관리자", goal=INSTRUCTIONS, backstory=INSTRUCTIONS,
                      tools=[tool(get_issue), tool(list_crew)],
                      llm=LLM(model=f"openai/{MODEL}", base_url=BASE_URL, api_key=API_KEY))
        task = PROMPT + "\n지금은 승인 전이므로 assign_issue를 호출하지 말고 배정안(issue_id, assignee)만 답하세요."
        return agent.kickoff(task, response_format=Assignment).pydantic.model_dump()

    @listen(propose)
    def execute(self):
        proposal = self.last_human_feedback.output
        if self.last_human_feedback.feedback != "approve":
            return "배정이 거절되어 실행하지 않았습니다."
        assign_issue(**proposal)
        return f"{proposal['issue_id']}을(를) {proposal['assignee']}에게 배정했습니다."


persistence = SQLiteFlowPersistence(str(STATE))
if STEP == "start":
    pending = AssignFlow(persistence=persistence).kickoff()
    save_pending("assign_issue", pending.context.method_output)
    (DIR / "flow_id").write_text(pending.context.flow_id)
else:
    flow = AssignFlow.from_pending((DIR / "flow_id").read_text(), persistence)
    save_final(flow.resume("approve" if APPROVED else REJECT_MESSAGE))
