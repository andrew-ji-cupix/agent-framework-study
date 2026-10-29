import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import json  # noqa: E402
import re  # noqa: E402

from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MEMORY, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, SKILLS, STEP, prompt, save  # noqa: E402
from pydantic_ai import Agent, RunContext  # noqa: E402
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402


# 이 프레임워크에는 대화를 넘는 장기 메모리가 없어 파일로 직접 만든다: 저장은 도구로, 불러오기는 지시문으로
MEMORY_FILE = MEMORY / "memories.json"


def save_memory(memory: str) -> str:
    """사용자가 다음 대화에서도 지켜 달라고 한 선호나 지시를 장기 메모리에 저장한다.

    Args:
        memory: 기억할 내용
    """
    MEMORY.mkdir(exist_ok=True)
    saved = json.loads(MEMORY_FILE.read_text()) if MEMORY_FILE.exists() else []
    MEMORY_FILE.write_text(json.dumps(saved + [memory], ensure_ascii=False))
    return "저장했습니다."


REMEMBERED = "\n".join(f"- {m}" for m in json.loads(MEMORY_FILE.read_text())) if MEMORY_FILE.exists() else ""
WITH_MEMORY = f"\n\n기억하고 있는 사용자 요청:\n{REMEMBERED}" if REMEMBERED else ""


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


SYSTEM = f"{INSTRUCTIONS}\n\n사용할 수 있는 스킬입니다. 관련 요청이면 load_skill로 지침을 불러와 따르세요.\n{skill_catalog()}"

model = OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=BASE_URL, api_key=API_KEY))
progress_analyst = Agent(model, instructions=PROGRESS_ANALYST, tools=[get_progress])
agent = Agent(model, instructions=SYSTEM + WITH_MEMORY, tools=[search_issues, get_issue, list_crew, load_skill, save_memory])


@agent.tool  # 도구 안에서 하위 에이전트를 실행하고, usage를 넘겨 사용량을 합산한다
async def ask_progress_analyst(ctx: RunContext, question: str) -> str:
    """공정 분석가에게 공정률과 지연 현황을 묻는다."""
    return (await progress_analyst.run(question, usage=ctx.usage)).output


save(agent.run_sync(prompt(f"l5-{STEP}")).output, "remember" if STEP == "remember" else "output")
