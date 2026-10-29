import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from crewai import LLM, Agent  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402

assistant = Agent(role="현장 이슈 비서", goal=INSTRUCTIONS, backstory=INSTRUCTIONS,
                  llm=LLM(model=f"openai/{MODEL}", base_url=BASE_URL, api_key=API_KEY))
save(assistant.kickoff(prompt("l1")).raw)
