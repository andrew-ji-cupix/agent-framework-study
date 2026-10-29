import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402

set_tracing_disabled(True)
agent = Agent(name="assistant", instructions=INSTRUCTIONS,
              model=OpenAIChatCompletionsModel(model=MODEL, openai_client=AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)),
              tools=[function_tool(search_issues), function_tool(get_issue), function_tool(list_crew)])
save(Runner.run_sync(agent, prompt("l2")).final_output)
