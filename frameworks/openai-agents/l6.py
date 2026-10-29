import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import re  # noqa: E402

from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled  # noqa: E402
from ladder import (ANALYST, API_KEY, BASE_URL, MODEL, REVIEWER, SKILLS, WRITER, approved, prompt,  # noqa: E402
                    reviewer_input, save, writer_input)
from openai import AsyncOpenAI  # noqa: E402
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

set_tracing_disabled(True)
model = OpenAIChatCompletionsModel(model=MODEL, openai_client=AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY))
skill = function_tool(load_skill)
analyst = Agent(name="analyst", instructions=ANALYST + CATALOG, model=model,
                tools=[function_tool(search_issues), function_tool(get_issue), function_tool(list_crew),
                       function_tool(get_progress), skill])
writer = Agent(name="writer", instructions=WRITER + CATALOG, model=model, tools=[skill])
reviewer = Agent(name="reviewer", instructions=REVIEWER + CATALOG, model=model, tools=[skill])

# 그래프 기능이 없어 순서와 반려 루프를 코드로 짠다 (문서의 code orchestration 방식). 작성은 최대 3번
facts, feedback = Runner.run_sync(analyst, prompt("l6")).final_output, ""
for _ in range(3):
    draft = Runner.run_sync(writer, writer_input(facts, feedback)).final_output
    feedback = Runner.run_sync(reviewer, reviewer_input(facts, draft)).final_output
    if approved(feedback):
        break
save(draft)
