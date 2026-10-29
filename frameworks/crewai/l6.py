import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402
from ladder import (ANALYST, API_KEY, BASE_URL, MODEL, REVIEWER, SKILLS, WRITER, approved, prompt,  # noqa: E402
                    reviewer_input, save)
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

llm = LLM(model=f"openai/{MODEL}", base_url=BASE_URL, api_key=API_KEY)
analyst = Agent(role="현장 데이터 분석가", goal=ANALYST, backstory=ANALYST, llm=llm, skills=[SKILLS],
                tools=[tool(search_issues), tool(get_issue), tool(list_crew), tool(get_progress)])
writer = Agent(role="리포트 작성자", goal=WRITER, backstory=WRITER, llm=llm, skills=[SKILLS])
reviewer = Agent(role="리포트 검토자", goal=REVIEWER, backstory=REVIEWER, llm=llm, skills=[SKILLS])
analysis = Task(description=prompt("l6"), expected_output="리포트에 필요한 사실 목록", agent=analyst)


def review(output):
    """작성 과제의 guardrail. 검토자가 반려하면 의견과 함께 작성자에게 다시 시킨다."""
    verdict = reviewer.kickoff(reviewer_input(analysis.output.raw, output.raw)).raw
    return (True, output.raw) if approved(verdict) else (False, verdict)


writing = Task(description=prompt("l6") + "\n분석가의 사실로 리포트를 쓰세요.", expected_output="사내 규칙에 맞는 주간 리포트",
               agent=writer, context=[analysis], guardrail=review, guardrail_max_retries=2)
save(Crew(agents=[analyst, writer], tasks=[analysis, writing], process=Process.sequential).kickoff().raw)
