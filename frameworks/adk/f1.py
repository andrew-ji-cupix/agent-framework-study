import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import asyncio  # noqa: E402

from f1 import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, TriageReport, save  # noqa: E402
from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.models.lite_llm import LiteLlm  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402

agent = LlmAgent(
    name="triage",
    model=LiteLlm(model=f"openrouter/{MODEL}", api_base=BASE_URL, api_key=API_KEY),
    instruction=INSTRUCTIONS,
    tools=[search_issues, get_issue, list_crew],
    output_schema=TriageReport,
)


async def main() -> None:
    runner = InMemoryRunner(agent=agent, app_name="f1")
    session = await runner.session_service.create_session(app_name="f1", user_id="u")
    message = types.Content(role="user", parts=[types.Part(text=PROMPT)])
    final = None
    async for event in runner.run_async(user_id="u", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            final = event.content.parts[0].text
    save(TriageReport.model_validate_json(final))


asyncio.run(main())
