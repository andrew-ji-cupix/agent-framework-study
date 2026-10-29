"""F3 과제 공통 입력과 시나리오 파일. 실행기는 시나리오(승인/거절)마다 SCENARIO_DIR을 따로 주고
`start`로 한 번, `resume approve|reject`로 한 번, 서로 다른 프로세스에서 실행한다."""

import json
import os
import sys
from pathlib import Path

from f1 import API_KEY, BASE_URL, MODEL  # noqa: F401

PROMPT = (Path(__file__).parents[1] / "tasks/f3/prompt.md").read_text()
INSTRUCTIONS = "당신은 건설 현장 이슈를 관리하는 어시스턴트입니다. 도구로 확인한 정보만 사용합니다."
REJECT_MESSAGE = "현장 관리자가 이 배정을 거절했습니다. 다시 시도하지 말고 작업을 끝내세요."
DIR = Path(os.environ.get("SCENARIO_DIR", "."))
STATE = DIR / "state"  # 후보별 상태 저장 위치(파일 또는 DB)
STEP = sys.argv[1] if len(sys.argv) > 1 else "start"  # start | resume
APPROVED = sys.argv[2:3] == ["approve"]


def save_pending(tool: str, args: dict | str) -> None:
    """승인 대기 중인 도구 호출을 기록한다. 채점기가 인자를 확인한다."""
    args = json.loads(args) if isinstance(args, str) else args
    (DIR / "pending.json").write_text(json.dumps({"tool": tool, "args": args}, ensure_ascii=False))


def save_final(text: str) -> None:
    (DIR / "final.json").write_text(json.dumps({"result": text}, ensure_ascii=False))
