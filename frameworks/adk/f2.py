import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import asyncio  # noqa: E402

from f2 import (API_KEY, BASE_URL, ISSUE_ANALYST, ISSUE_DESC, MODEL, PROGRESS_ANALYST,  # noqa: E402
                PROGRESS_DESC, PROMPT, SUPERVISOR, WeeklyReport, save)
from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.models.lite_llm import LiteLlm  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.adk.tools.agent_tool import AgentTool  # noqa: E402
from google.genai import types  # noqa: E402
from sitetools import get_issue, get_progress, search_issues  # noqa: E402

model = LiteLlm(model=f"openrouter/{MODEL}", api_base=BASE_URL, api_key=API_KEY)
progress_analyst = LlmAgent(name="ask_progress_analyst", description=PROGRESS_DESC, model=model,
                            instruction=PROGRESS_ANALYST, tools=[get_progress])
issue_analyst = LlmAgent(name="ask_issue_analyst", description=ISSUE_DESC, model=model,
                         instruction=ISSUE_ANALYST, tools=[search_issues, get_issue])
# AgentTool: 하위 에이전트의 결과가 감독에게 돌아온다 (sub_agents는 제어권 자체를 넘긴다)
supervisor = LlmAgent(name="supervisor", model=model, instruction=SUPERVISOR,
                      tools=[AgentTool(progress_analyst), AgentTool(issue_analyst)], output_schema=WeeklyReport)


async def main() -> None:
    runner = InMemoryRunner(agent=supervisor, app_name="f2")
    session = await runner.session_service.create_session(app_name="f2", user_id="u")
    message = types.Content(role="user", parts=[types.Part(text=PROMPT)])
    final = None
    async for event in runner.run_async(user_id="u", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            final = event.content.parts[0].text
    save(WeeklyReport.model_validate_json(final))


asyncio.run(main())
