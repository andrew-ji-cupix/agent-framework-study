import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402
from f2 import (API_KEY, BASE_URL, ISSUE_ANALYST, MODEL, PROGRESS_ANALYST, PROMPT,  # noqa: E402
                SUPERVISOR, WeeklyReport, save)
from sitetools import get_issue, get_progress, search_issues  # noqa: E402

llm = LLM(model=f"openai/{MODEL}", base_url=BASE_URL, api_key=API_KEY)
progress_analyst = Agent(role="공정 분석가", goal=PROGRESS_ANALYST, backstory=PROGRESS_ANALYST,
                         tools=[tool(get_progress)], llm=llm)
issue_analyst = Agent(role="이슈 분석가", goal=ISSUE_ANALYST, backstory=ISSUE_ANALYST,
                      tools=[tool(search_issues), tool(get_issue)], llm=llm)
supervisor = Agent(role="감독", goal=SUPERVISOR, backstory=SUPERVISOR, llm=llm, allow_delegation=True)
report = Task(description=PROMPT, expected_output="주간 현장 리포트", output_pydantic=WeeklyReport)
# hierarchical: 감독(manager)이 과제를 분석가에게 위임한다
crew = Crew(agents=[progress_analyst, issue_analyst], tasks=[report], process=Process.hierarchical,
            manager_agent=supervisor)
save(crew.kickoff().pydantic)
