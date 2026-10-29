import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import re  # noqa: E402
from typing import TypedDict  # noqa: E402

from ladder import (
    ANALYST,
    API_KEY,
    BASE_URL,
    MODEL,
    REVIEWER,
    SKILLS,
    WRITER,
    approved,
    prompt,  # noqa: E402
    reviewer_input,
    save,
    writer_input,
)
from langchain.agents import create_agent  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
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


CATALOG = f"\n\n사용할 수 있는 스킬입니다. 관련 요청이면 load_skill로 지침을 불러와 따르세요.\n{skill_catalog()}"

model = ChatOpenAI(model=MODEL, base_url=BASE_URL, api_key=API_KEY)
analyst = create_agent(
    model,
    tools=[search_issues, get_issue, list_crew, get_progress, load_skill],
    system_prompt=ANALYST + CATALOG,
)
writer = create_agent(model, tools=[load_skill], system_prompt=WRITER + CATALOG)
reviewer = create_agent(model, tools=[load_skill], system_prompt=REVIEWER + CATALOG)


def ask(agent, text: str) -> str:
    return agent.invoke({"messages": [{"role": "user", "content": text}]})["messages"][
        -1
    ].text


class Report(TypedDict, total=False):
    facts: str
    draft: str
    feedback: str
    rounds: int


def analyze(state: Report) -> Report:
    return {"facts": ask(analyst, prompt("l6")), "rounds": 0}


def write(state: Report) -> Report:
    return {
        "draft": ask(writer, writer_input(state["facts"], state.get("feedback", ""))),
        "rounds": state["rounds"] + 1,
    }


def review(state: Report) -> Report:
    return {"feedback": ask(reviewer, reviewer_input(state["facts"], state["draft"]))}


def route(state: Report) -> str:  # 반려되면 작성자에게 되돌린다 (작성은 최대 3번)
    return END if approved(state["feedback"]) or state["rounds"] >= 3 else "write"


graph = StateGraph(Report)
graph.add_node("analyze", analyze)
graph.add_node("write", write)
graph.add_node("review", review)
graph.add_edge(START, "analyze")
graph.add_edge("analyze", "write")
graph.add_edge("write", "review")
graph.add_conditional_edges("review", route)
save(graph.compile().invoke({})["draft"])
