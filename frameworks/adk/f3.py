import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import asyncio  # noqa: E402

from f3 import (API_KEY, APPROVED, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, STATE, STEP, save_final,  # noqa: E402
                save_pending)
from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.models.lite_llm import LiteLlm  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions.sqlite_session_service import SqliteSessionService  # noqa: E402
from google.adk.tools import FunctionTool  # noqa: E402
from google.genai import types  # noqa: E402
from sitetools import assign_issue, get_issue, list_crew  # noqa: E402

CONFIRM = "adk_request_confirmation"  # ADK가 확인 요청에 쓰는 함수 호출 이름
agent = LlmAgent(name="assigner", model=LiteLlm(model=f"openrouter/{MODEL}", api_base=BASE_URL, api_key=API_KEY),
                 instruction=INSTRUCTIONS,
                 tools=[get_issue, list_crew, FunctionTool(assign_issue, require_confirmation=True)])
sessions = SqliteSessionService(str(STATE))  # 대화와 확인 요청이 파일 DB에 남는다
runner = Runner(agent=agent, app_name="f3", session_service=sessions)


async def run(part: types.Part) -> list:
    message = types.Content(role="user", parts=[part])
    return [e async for e in runner.run_async(user_id="u", session_id="f3", new_message=message)]


async def main() -> None:
    if STEP == "start":
        await sessions.create_session(app_name="f3", user_id="u", session_id="f3")
        events = await run(types.Part(text=PROMPT))
        request = next(c for e in events for c in e.get_function_calls() if c.name == CONFIRM)
        save_pending(request.args["originalFunctionCall"]["name"], request.args["originalFunctionCall"]["args"])
    else:
        session = await sessions.get_session(app_name="f3", user_id="u", session_id="f3")
        request = [c for e in session.events for c in e.get_function_calls() if c.name == CONFIRM][-1]
        reply = types.FunctionResponse(id=request.id, name=CONFIRM, response={"confirmed": APPROVED})
        events = await run(types.Part(function_response=reply))
        texts = [p.text for e in events if e.is_final_response() and e.content for p in e.content.parts or [] if p.text]
        if texts:
            save_final(texts[-1])


asyncio.run(main())
