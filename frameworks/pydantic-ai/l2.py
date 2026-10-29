import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402
from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402

agent = Agent(OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=BASE_URL, api_key=API_KEY)), instructions=INSTRUCTIONS,
              tools=[search_issues, get_issue, list_crew])
save(agent.run_sync(prompt("l2")).output)
