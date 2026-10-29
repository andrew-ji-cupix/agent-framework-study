import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from f1 import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, TriageReport, save  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402
from strands import Agent, tool  # noqa: E402
from strands.models.openai import OpenAIModel  # noqa: E402

agent = Agent(
    model=OpenAIModel(client_args={"base_url": BASE_URL, "api_key": API_KEY}, model_id=MODEL),
    system_prompt=INSTRUCTIONS,
    tools=[tool(search_issues), tool(get_issue), tool(list_crew)],
)
save(agent(PROMPT, structured_output_model=TriageReport).structured_output)
