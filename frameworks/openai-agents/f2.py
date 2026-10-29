import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled  # noqa: E402
from f2 import (API_KEY, BASE_URL, ISSUE_ANALYST, ISSUE_DESC, MODEL, PROGRESS_ANALYST,  # noqa: E402
                PROGRESS_DESC, PROMPT, SUPERVISOR, WeeklyReport, save)
from openai import AsyncOpenAI  # noqa: E402
from sitetools import get_issue, get_progress, search_issues  # noqa: E402

set_tracing_disabled(True)
model = OpenAIChatCompletionsModel(model=MODEL, openai_client=AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY))
progress_analyst = Agent(name="progress_analyst", instructions=PROGRESS_ANALYST, model=model,
                         tools=[function_tool(get_progress)])
issue_analyst = Agent(name="issue_analyst", instructions=ISSUE_ANALYST, model=model,
                      tools=[function_tool(search_issues), function_tool(get_issue)])
# as_tool: 결과가 감독에게 돌아온다 (handoff는 제어권 자체를 넘긴다)
supervisor = Agent(name="supervisor", instructions=SUPERVISOR, model=model, output_type=WeeklyReport, tools=[
    progress_analyst.as_tool(tool_name="ask_progress_analyst", tool_description=PROGRESS_DESC),
    issue_analyst.as_tool(tool_name="ask_issue_analyst", tool_description=ISSUE_DESC),
])
save(Runner.run_sync(supervisor, PROMPT).final_output)
