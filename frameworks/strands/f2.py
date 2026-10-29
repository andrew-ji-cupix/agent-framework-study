import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from f2 import (API_KEY, BASE_URL, ISSUE_ANALYST, ISSUE_DESC, MODEL, PROGRESS_ANALYST,  # noqa: E402
                PROGRESS_DESC, PROMPT, SUPERVISOR, WeeklyReport, save)
from sitetools import get_issue, get_progress, search_issues  # noqa: E402
from strands import Agent, tool  # noqa: E402
from strands.models.openai import OpenAIModel  # noqa: E402

model = OpenAIModel(client_args={"base_url": BASE_URL, "api_key": API_KEY}, model_id=MODEL)
progress_analyst = Agent(name="ask_progress_analyst", description=PROGRESS_DESC, model=model,
                         system_prompt=PROGRESS_ANALYST, tools=[tool(get_progress)])
issue_analyst = Agent(name="ask_issue_analyst", description=ISSUE_DESC, model=model,
                      system_prompt=ISSUE_ANALYST, tools=[tool(search_issues), tool(get_issue)])
supervisor = Agent(model=model, system_prompt=SUPERVISOR, tools=[progress_analyst.as_tool(), issue_analyst.as_tool()])
save(supervisor(PROMPT, structured_output_model=WeeklyReport).structured_output)
