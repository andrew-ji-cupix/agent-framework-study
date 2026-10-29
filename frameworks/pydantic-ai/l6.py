import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import re  # noqa: E402

from ladder import (ANALYST, API_KEY, BASE_URL, MODEL, REVIEWER, SKILLS, WRITER, approved, prompt,  # noqa: E402
                    reviewer_input, save, writer_input)
from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402


# 이 프레임워크에는 스킬 기능이 없어 직접 만든다: 목록은 지시문에, 본문은 load_skill 도구로 필요할 때 불러온다
def skill_catalog() -> str:
    metas = [dict(re.findall(r"^(name|description): (.+)$", f.read_text(), re.M)) for f in SKILLS.glob("*/SKILL.md")]
    return "\n".join(f"- {m['name']}: {m['description']}" for m in metas)


def load_skill(name: str) -> str:
    """스킬 이름으로 SKILL.md 전체 지침을 불러온다.

    Args:
        name: 스킬 이름
    """
    return (SKILLS / name / "SKILL.md").read_text()


CATALOG = f"\n\n사용할 수 있는 스킬입니다. 관련 요청이면 load_skill로 지침을 불러와 따르세요.\n{skill_catalog()}"

model = OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=BASE_URL, api_key=API_KEY))
analyst = Agent(model, instructions=ANALYST + CATALOG, tools=[search_issues, get_issue, list_crew, get_progress, load_skill])
writer = Agent(model, instructions=WRITER + CATALOG, tools=[load_skill])
reviewer = Agent(model, instructions=REVIEWER + CATALOG, tools=[load_skill])

# 순서와 반려 루프를 코드로 짠다 (문서의 programmatic hand-off 방식). 작성은 최대 3번
facts, feedback = analyst.run_sync(prompt("l6")).output, ""
for _ in range(3):
    draft = writer.run_sync(writer_input(facts, feedback)).output
    feedback = reviewer.run_sync(reviewer_input(facts, draft)).output
    if approved(feedback):
        break
save(draft)
