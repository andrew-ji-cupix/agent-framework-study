import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import asyncio  # noqa: E402

from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.models.lite_llm import LiteLlm  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.adk.skills import load_skill_from_dir  # noqa: E402
from google.adk.tools.agent_tool import AgentTool  # noqa: E402
from google.adk.tools.skill_toolset import SkillToolset  # noqa: E402
from google.genai import types  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, SKILLS, prompt, save  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

model = LiteLlm(model=f"openrouter/{MODEL}", api_base=BASE_URL, api_key=API_KEY)
progress_analyst = LlmAgent(name="ask_progress_analyst", description=PROGRESS_DESC, model=model,
                            instruction=PROGRESS_ANALYST, tools=[get_progress])
agent = LlmAgent(name="assistant", model=model,
                 tools=[search_issues, get_issue, list_crew, AgentTool(progress_analyst),
                        SkillToolset(skills=[load_skill_from_dir(SKILLS / "site-weekly-report")])],
                 instruction=INSTRUCTIONS)


async def main() -> None:
    runner = InMemoryRunner(agent=agent, app_name="ladder")
    session = await runner.session_service.create_session(app_name="ladder", user_id="u")
    message = types.Content(role="user", parts=[types.Part(text=prompt("l4"))])
    async for event in runner.run_async(user_id="u", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            # 추론 요약(thought) part가 섞여 오므로 답 텍스트만 모은다
            save("".join(p.text for p in event.content.parts if p.text and not p.thought))


asyncio.run(main())
