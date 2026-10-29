import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402
from strands import Agent  # noqa: E402
from strands.models.openai import OpenAIModel  # noqa: E402

agent = Agent(model=OpenAIModel(client_args={"base_url": BASE_URL, "api_key": API_KEY}, model_id=MODEL),
              system_prompt=INSTRUCTIONS)
save(str(agent(prompt("l1"))))
