import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import json  # noqa: E402
import re  # noqa: E402

from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MEMORY, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, SKILLS, STEP, prompt, save  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402
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


# 이 SDK의 스킬은 SandboxAgent 기능(스킬 파일을 샌드박스에 두고 셸로 읽는 방식)이라 일반 Agent에는 없다.
# OpenRouter Chat Completions 환경에서 3번 시도했지만 동작하지 않아(Filesystem 기능은 Responses API 전용 도구를 포함,
# Docker 샌드박스+Shell은 스킬 파일이 샌드박스에 들어가지 않음) 다른 두 후보처럼 직접 만든다
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

set_tracing_disabled(True)
model = OpenAIChatCompletionsModel(model=MODEL, openai_client=AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY))
progress_analyst = Agent(name="progress_analyst", instructions=PROGRESS_ANALYST, model=model, tools=[function_tool(get_progress)])
agent = Agent(name="assistant", instructions=SYSTEM + WITH_MEMORY, model=model,
              tools=[function_tool(search_issues), function_tool(get_issue), function_tool(list_crew), function_tool(load_skill),
                     function_tool(save_memory),
                     progress_analyst.as_tool(tool_name="ask_progress_analyst", tool_description=PROGRESS_DESC)])
save(Runner.run_sync(agent, prompt(f"l5-{STEP}")).final_output, "remember" if STEP == "remember" else "output")
