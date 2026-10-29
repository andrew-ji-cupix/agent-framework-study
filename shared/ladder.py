"""이슈 비서 키우기(L1~L6) 공통 입력. 호스트와 하네스 컨테이너(/shared에 마운트) 양쪽에서 쓰므로 표준 라이브러리만 쓴다."""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
INSTRUCTIONS = "당신은 건설 현장 이슈 비서입니다. 확인한 정보만 사용하고 추측하지 않습니다."
SKILLS = HERE / "skills"  # 스킬 원본: skills/site-weekly-report/SKILL.md
PROGRESS_ANALYST = "당신은 공정 분석가입니다. get_progress 도구로 확인한 공정률만 사용해 질문에 답합니다."
PROGRESS_DESC = "공정 분석가에게 공정률과 지연 현황을 묻는다."
MODEL = os.environ.get("LLM_MODEL", "anthropic/claude-opus-5.5")
BASE_URL = os.environ.get("LLM_BASE_URL", "")  # OpenAI 호환 (프록시)
ANTHROPIC_BASE_URL = os.environ.get("LLM_ANTHROPIC_BASE_URL", "")  # Anthropic 호환 (프록시)
API_KEY = os.environ.get("LLM_API_KEY", "proxy")
OUT = Path(os.environ.get("RESULT_PATH", "/out/output.json")).parent
MEMORY = OUT / "memory"  # L5: 세션(프로세스)을 넘어 남는 저장소 위치
STEP = sys.argv[1] if len(sys.argv) > 1 else ""  # L5: remember | report


def prompt(name: str) -> str:
    return (HERE / "prompts" / f"{name}.md").read_text()


def save(text: str, name: str = "output") -> None:
    (OUT / f"{name}.json").write_text(json.dumps({"result": text}, ensure_ascii=False))

# L6 멀티에이전트 구조: 분석가 → 작성자 → 검토자 (반려되면 작성자가 다시 고친다)
ANALYST = ("당신은 현장 데이터 분석가입니다. 사내 '현장 주간 리포트' 규칙에 필요한 값(미해결 건수, 최우선 이슈, 담당 추천, "
           "10%p 이상 지연된 공종과 지연 폭)을 도구로 확인해 사실 목록으로만 답합니다.")
WRITER = "당신은 리포트 작성자입니다. 분석가가 정리한 사실만 사용해 사내 '현장 주간 리포트' 규칙에 맞는 리포트를 쓰고, 리포트만 답합니다."
REVIEWER = ("당신은 리포트 검토자입니다. 사내 '현장 주간 리포트' 규칙과 분석가의 사실에 비추어 리포트를 검토합니다. "
            "문제가 없으면 '승인'만, 고칠 점이 있으면 '반려: <고칠 점>'으로 답합니다.")
ORCHESTRATOR = ("분석가 → 작성자 → 검토자 순서로 서브에이전트에게 일을 맡기세요. 작성자와 검토자에게는 분석가의 사실을 함께 넘기세요. "
                "검토자가 반려하면 작성자에게 고치게 하고(최대 2번), 승인된 리포트만 그대로 답하세요.")
ROLE_DESC = {"analyst": "리포트에 필요한 사실을 도구로 확인해 정리한다.",
             "writer": "분석가의 사실로 사내 규칙에 맞는 리포트를 쓴다.",
             "reviewer": "리포트가 사내 규칙과 분석가의 사실에 맞는지 검토한다."}


def writer_input(facts: str, feedback: str = "") -> str:
    note = f"\n\n검토 의견(반영해서 고치세요):\n{feedback}" if feedback else ""
    return f"{prompt('l6')}\n분석가의 사실:\n{facts}{note}"


def reviewer_input(facts: str, draft: str) -> str:
    return f"분석가의 사실:\n{facts}\n\n리포트:\n{draft}"


def approved(verdict: str) -> bool:
    return verdict.strip().startswith("승인")
