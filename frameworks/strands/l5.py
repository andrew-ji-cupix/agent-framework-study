import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

import json  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MEMORY, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, SKILLS, STEP, prompt, save  # noqa: E402
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
from strands import Agent, tool  # noqa: E402
from strands.models.openai import OpenAIModel  # noqa: E402
from strands.vended_plugins.skills import AgentSkills  # noqa: E402

model = OpenAIModel(client_args={"base_url": BASE_URL, "api_key": API_KEY}, model_id=MODEL)
progress_analyst = Agent(name="ask_progress_analyst", description=PROGRESS_DESC, model=model,
                         system_prompt=PROGRESS_ANALYST, tools=[tool(get_progress)])
agent = Agent(model=model, system_prompt=INSTRUCTIONS + WITH_MEMORY,
              tools=[tool(search_issues), tool(get_issue), tool(list_crew), progress_analyst.as_tool(), tool(save_memory)],
              plugins=[AgentSkills(skills=[str(SKILLS)])])
save(str(agent(prompt(f"l5-{STEP}"))), "remember" if STEP == "remember" else "output")
