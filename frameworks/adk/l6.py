import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import asyncio  # noqa: E402

from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent  # noqa: E402
from google.adk.models.lite_llm import LiteLlm  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.adk.skills import load_skill_from_dir  # noqa: E402
from google.adk.tools import exit_loop  # noqa: E402
from google.adk.tools.skill_toolset import SkillToolset  # noqa: E402
from google.genai import types  # noqa: E402
from ladder import ANALYST, API_KEY, BASE_URL, MODEL, REVIEWER, SKILLS, WRITER, prompt, save  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

model = LiteLlm(model=f"openrouter/{MODEL}", api_base=BASE_URL, api_key=API_KEY)


def skills() -> SkillToolset:
    return SkillToolset(skills=[load_skill_from_dir(SKILLS / "site-weekly-report")])


# 에이전트끼리는 세션 상태(output_key, 지시문의 {키})로 결과를 넘긴다
analyst = LlmAgent(name="analyst", model=model, instruction=ANALYST, output_key="facts",
                   tools=[search_issues, get_issue, list_crew, get_progress, skills()])
writer = LlmAgent(name="writer", model=model, output_key="draft", tools=[skills()],
                  instruction=WRITER + "\n\n분석가의 사실:\n{facts}\n\n검토 의견(있으면 반영해서 고치세요):\n{feedback?}")
reviewer = LlmAgent(name="reviewer", model=model, output_key="feedback", tools=[skills(), exit_loop],
                    instruction=REVIEWER + " 승인할 때는 exit_loop 도구도 호출하세요.\n\n분석가의 사실:\n{facts}\n\n리포트:\n{draft}")
# 분석 다음에 작성·검토를 반복한다. 검토자가 exit_loop를 부르거나 3번 돌면 끝난다
team = SequentialAgent(name="team", sub_agents=[analyst, LoopAgent(name="write_review", sub_agents=[writer, reviewer],
                                                                   max_iterations=3)])


async def main() -> None:
    runner = InMemoryRunner(agent=team, app_name="ladder")
    session = await runner.session_service.create_session(app_name="ladder", user_id="u")
    message = types.Content(role="user", parts=[types.Part(text=prompt("l6"))])
    async for _ in runner.run_async(user_id="u", session_id=session.id, new_message=message):
        pass
    session = await runner.session_service.get_session(app_name="ladder", user_id="u", session_id=session.id)
    save(session.state["draft"])


asyncio.run(main())
