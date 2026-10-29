import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import asyncio  # noqa: E402

from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.models.lite_llm import LiteLlm  # noqa: E402
from google.adk.memory import SqliteMemoryService  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.adk.skills import load_skill_from_dir  # noqa: E402
from google.adk.tools.agent_tool import AgentTool  # noqa: E402
from google.adk.tools.preload_memory_tool import PreloadMemoryTool  # noqa: E402
from google.adk.tools.skill_toolset import SkillToolset  # noqa: E402
from google.genai import types  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MEMORY, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, SKILLS, STEP, prompt, save  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

model = LiteLlm(model=f"openrouter/{MODEL}", api_base=BASE_URL, api_key=API_KEY)
progress_analyst = LlmAgent(name="ask_progress_analyst", description=PROGRESS_DESC, model=model,
                            instruction=PROGRESS_ANALYST, tools=[get_progress])
agent = LlmAgent(name="assistant", model=model,
                 tools=[search_issues, get_issue, list_crew, AgentTool(progress_analyst), PreloadMemoryTool(),
                        SkillToolset(skills=[load_skill_from_dir(SKILLS / "site-weekly-report")])],
                 instruction=INSTRUCTIONS)


MEMORY.mkdir(exist_ok=True)
memory = SqliteMemoryService(str(MEMORY / "memory.db"))  # 대화를 넘어 남는 장기 메모리


async def main() -> None:
    runner = Runner(agent=agent, app_name="ladder", session_service=InMemorySessionService(), memory_service=memory)
    session = await runner.session_service.create_session(app_name="ladder", user_id="u")
    message = types.Content(role="user", parts=[types.Part(text=prompt(f"l5-{STEP}"))])
    async for event in runner.run_async(user_id="u", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            # 추론 요약(thought) part가 섞여 오므로 답 텍스트만 모은다
            save("".join(p.text for p in event.content.parts if p.text and not p.thought), "remember" if STEP == "remember" else "output")
    if STEP == "remember":  # 이번 대화를 장기 메모리에 넣는다. 다음 대화에서는 PreloadMemoryTool이 관련 기억을 꺼낸다
        await memory.add_session_to_memory(await runner.session_service.get_session(
            app_name="ladder", user_id="u", session_id=session.id))


asyncio.run(main())
