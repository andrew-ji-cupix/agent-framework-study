import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import sqlite3  # noqa: E402

from f3 import (API_KEY, APPROVED, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, REJECT_MESSAGE, STATE,  # noqa: E402
                STEP, save_final, save_pending)
from langchain.agents import create_agent  # noqa: E402
from langchain.agents.middleware import HumanInTheLoopMiddleware  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402
from langgraph.types import Command  # noqa: E402
from sitetools import assign_issue, get_issue, list_crew  # noqa: E402

agent = create_agent(
    ChatOpenAI(model=MODEL, base_url=BASE_URL, api_key=API_KEY),
    tools=[get_issue, list_crew, assign_issue],
    system_prompt=INSTRUCTIONS,
    middleware=[HumanInTheLoopMiddleware(interrupt_on={"assign_issue": True})],  # 실행 전에 멈출 도구
    checkpointer=SqliteSaver(sqlite3.connect(STATE, check_same_thread=False)),  # 프로세스가 끝나도 상태가 남는다
)
config = {"configurable": {"thread_id": "f3"}}
if STEP == "start":
    result = agent.invoke({"messages": [{"role": "user", "content": PROMPT}]}, config)
    request = result["__interrupt__"][0].value["action_requests"][0]
    save_pending(request["name"], request["args"])
else:
    decision = {"type": "approve"} if APPROVED else {"type": "reject", "message": REJECT_MESSAGE}
    result = agent.invoke(Command(resume={"decisions": [decision]}), config)
    save_final(result["messages"][-1].text)
