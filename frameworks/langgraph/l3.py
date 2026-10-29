import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import re  # noqa: E402

from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, SKILLS, prompt, save  # noqa: E402
from langchain.agents import create_agent  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402


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

agent = create_agent(
    ChatOpenAI(model=MODEL, base_url=BASE_URL, api_key=API_KEY),
    system_prompt=SYSTEM,
    tools=[search_issues, get_issue, list_crew, load_skill],
)
result = agent.invoke({"messages": [{"role": "user", "content": prompt("l3")}]})
save(result["messages"][-1].text)
