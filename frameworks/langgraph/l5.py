import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import re  # noqa: E402
import sqlite3  # noqa: E402
import uuid  # noqa: E402

from ladder import (
    API_KEY,
    BASE_URL,
    INSTRUCTIONS,
    MEMORY,
    MODEL,
    PROGRESS_ANALYST,
    PROGRESS_DESC,
    SKILLS,
    STEP,
    prompt,
    save,
)  # noqa: E402
from langchain.agents import create_agent  # noqa: E402
from langchain.tools import ToolRuntime, tool  # noqa: E402
from langgraph.store.sqlite import SqliteStore  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402


# 이 프레임워크에는 스킬 기능이 없어 직접 만든다: 목록은 지시문에, 본문은 load_skill 도구로 필요할 때 불러온다
def skill_catalog() -> str:
    metas = [
        dict(re.findall(r"^(name|description): (.+)$", f.read_text(), re.M))
        for f in SKILLS.glob("*/SKILL.md")
    ]
    return "\n".join(f"- {m['name']}: {m['description']}" for m in metas)


def load_skill(name: str) -> str:
    """스킬 이름으로 SKILL.md 전체 지침을 불러온다.

    Args:
        name: 스킬 이름
    """
    return (SKILLS / name / "SKILL.md").read_text()


SYSTEM = f"{INSTRUCTIONS}\n\n사용할 수 있는 스킬입니다. 관련 요청이면 load_skill로 지침을 불러와 따르세요.\n{skill_catalog()}"

model = ChatOpenAI(model=MODEL, base_url=BASE_URL, api_key=API_KEY)
progress_analyst = create_agent(
    model, tools=[get_progress], system_prompt=PROGRESS_ANALYST
)


@tool(description=PROGRESS_DESC)  # 하위 에이전트를 도구로 감싼다
def ask_progress_analyst(question: str) -> str:
    return progress_analyst.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )["messages"][-1].text


MEMORY.mkdir(exist_ok=True)
# 대화(thread)를 넘어 남는 장기 저장소. 저장소가 트랜잭션을 직접 관리하므로 자동 커밋 연결(isolation_level=None)을 넘긴다
store = SqliteStore(
    sqlite3.connect(MEMORY / "store.db", check_same_thread=False, isolation_level=None)
)
store.setup()


@tool
def save_memory(memory: str, runtime: ToolRuntime) -> str:
    """사용자가 다음 대화에서도 지켜 달라고 한 선호나 지시를 장기 메모리에 저장한다."""
    runtime.store.put(("memories",), str(uuid.uuid4()), {"text": memory})
    return "저장했습니다."


remembered = "\n".join(
    f"- {item.value['text']}" for item in store.search(("memories",))
)  # 저장된 기억을 지시문에 넣는다
agent = create_agent(
    model,
    system_prompt=SYSTEM
    + (f"\n\n기억하고 있는 사용자 요청:\n{remembered}" if remembered else ""),
    tools=[
        search_issues,
        get_issue,
        list_crew,
        load_skill,
        ask_progress_analyst,
        save_memory,
    ],
    store=store,
)
result = agent.invoke({"messages": [{"role": "user", "content": prompt(f"l5-{STEP}")}]})
save(result["messages"][-1].text, "remember" if STEP == "remember" else "output")
