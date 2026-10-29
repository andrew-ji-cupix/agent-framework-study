import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, SKILLS, prompt, save  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402
from strands import Agent, tool  # noqa: E402
from strands.models.openai import OpenAIModel  # noqa: E402
from strands.vended_plugins.skills import AgentSkills  # noqa: E402

model = OpenAIModel(client_args={"base_url": BASE_URL, "api_key": API_KEY}, model_id=MODEL)
progress_analyst = Agent(name="ask_progress_analyst", description=PROGRESS_DESC, model=model,
                         system_prompt=PROGRESS_ANALYST, tools=[tool(get_progress)])
agent = Agent(model=model, system_prompt=INSTRUCTIONS,
              tools=[tool(search_issues), tool(get_issue), tool(list_crew), progress_analyst.as_tool()],
              plugins=[AgentSkills(skills=[str(SKILLS)])])
save(str(agent(prompt("l4"))))
