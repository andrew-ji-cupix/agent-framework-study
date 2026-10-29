import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from crewai import LLM, Agent, Crew, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, SKILLS, prompt, save  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

llm = LLM(model=f"openai/{MODEL}", base_url=BASE_URL, api_key=API_KEY)
progress_analyst = Agent(role="공정 분석가", goal=PROGRESS_ANALYST, backstory=PROGRESS_DESC, llm=llm,
                         tools=[tool(get_progress)])
assistant = Agent(role="현장 이슈 비서", goal=INSTRUCTIONS, backstory=INSTRUCTIONS, llm=llm, allow_delegation=True,
                  tools=[tool(search_issues), tool(get_issue), tool(list_crew)], skills=[SKILLS])
# 위임은 같은 Crew에 있는 동료 에이전트에게만 할 수 있어서 Agent.kickoff 대신 Crew를 쓴다
task = Task(description=prompt("l4"), expected_output="사내 규칙에 맞는 주간 리포트", agent=assistant)
save(Crew(agents=[assistant, progress_analyst], tasks=[task]).kickoff().raw)
