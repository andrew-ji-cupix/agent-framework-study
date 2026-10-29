import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402
from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402

agent = Agent(OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=BASE_URL, api_key=API_KEY)), instructions=INSTRUCTIONS)
save(agent.run_sync(prompt("l1")).output)
