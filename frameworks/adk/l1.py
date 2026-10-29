import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import asyncio  # noqa: E402

from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.models.lite_llm import LiteLlm  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402

agent = LlmAgent(name="assistant", model=LiteLlm(model=f"openrouter/{MODEL}", api_base=BASE_URL, api_key=API_KEY),
                 instruction=INSTRUCTIONS)


async def main() -> None:
    runner = InMemoryRunner(agent=agent, app_name="ladder")
    session = await runner.session_service.create_session(app_name="ladder", user_id="u")
    message = types.Content(role="user", parts=[types.Part(text=prompt("l1"))])
    async for event in runner.run_async(user_id="u", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            # 추론 요약(thought) part가 섞여 오므로 답 텍스트만 모은다
            save("".join(p.text for p in event.content.parts if p.text and not p.thought))


asyncio.run(main())
