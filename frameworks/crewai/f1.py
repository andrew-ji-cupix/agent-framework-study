import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from crewai import LLM, Agent, Crew, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402
from f1 import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, TriageReport, save  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402

analyst = Agent(
    role="현장 이슈 분석가",
    goal=INSTRUCTIONS,
    backstory=INSTRUCTIONS,
    tools=[tool(search_issues), tool(get_issue), tool(list_crew)],
    llm=LLM(model=f"openai/{MODEL}", base_url=BASE_URL, api_key=API_KEY),
)
task = Task(description=PROMPT, expected_output="우선순위 리포트", agent=analyst, output_pydantic=TriageReport)
save(Crew(agents=[analyst], tasks=[task]).kickoff().pydantic)
