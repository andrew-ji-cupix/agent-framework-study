import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402

set_tracing_disabled(True)
agent = Agent(name="assistant", instructions=INSTRUCTIONS,
              model=OpenAIChatCompletionsModel(model=MODEL, openai_client=AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)))
save(Runner.run_sync(agent, prompt("l1")).final_output)
