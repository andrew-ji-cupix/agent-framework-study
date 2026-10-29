"""L1~L6 채점 공통 함수. 실행 폴더의 output.json(에이전트 답)과 calls.json(프록시 기록)을 읽는다.
정답은 mock 데이터에서 계산하고, 리포트는 마크다운 기호와 공백 차이를 무시하고 줄 단위로 비교한다."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "shared"))
from sitetools import CREW, ISSUES, PROGRESS, SEVERITY_RANK  # noqa: E402

KO = {"electrical": "전기", "plumbing": "설비", "structural": "골조", "finishing": "마감", "fire_protection": "소방"}


def expected_report() -> dict:
    unresolved = [i for i in ISSUES if i["level"] == "3F" and i["trade"] == "electrical"
                  and i["status"] in ("open", "in_progress")]
    top = min(unresolved, key=lambda i: (SEVERITY_RANK[i["severity"]], i["created_at"]))
    crew = min((c for c in CREW if c["trade"] == "electrical"), key=lambda c: (c["open_assignments"], c["name"]))
    delays = sorted(((r["planned_pct"] - r["actual_pct"], r["trade"]) for r in PROGRESS
                     if r["level"] == "3F" and r["planned_pct"] - r["actual_pct"] >= 10), reverse=True)
    return {
        "first_line": "[주간 리포트] 3F 전기",
        "unresolved": f"미해결: {len(unresolved)}건",
        "top_priority": f"최우선: {top['id']}",
        "assignee": f"담당 추천: {crew['name']}",
        "delay_line": "지연 공종: " + ", ".join(f"{KO[t]} {g}%p" for g, t in delays),
        "doc_number_last": "문서번호: WR-3F-EL",
        "review_line_before_last": "검토 요청: 김현장 소장",
    }


def load_text(run_dir, name: str = "output") -> str:
    try:
        data = json.loads((Path(run_dir) / f"{name}.json").read_text())
    except (OSError, ValueError):
        return ""
    return data.get("result") or data.get("message") or ""  # Flue의 --json 결과는 message


def norm(line: str) -> str:
    line = re.sub(r"^[\s>*#\-•]+", "", line).replace("**", "").replace("`", "")
    return re.sub(r"\s+", "", line).rstrip(".")


def lines(text: str) -> list[str]:
    return [n for n in (norm(line) for line in text.splitlines()) if n]


def report_block(ls: list[str]) -> list[str]:
    """답에서 리포트 부분(`[주간 리포트]` 줄부터 마지막 `문서번호:` 줄까지)만 잘라 낸다.
    스킬은 리포트의 형식을 정할 뿐, 리포트 앞뒤에 덧붙이는 설명까지 금지하지는 않는다."""
    start = next((i for i, line in enumerate(ls) if line.startswith(norm("[주간 리포트]"))), None)
    end = next((i for i in range(len(ls) - 1, -1, -1) if ls[i].startswith(norm("문서번호:"))), None)
    return ls[start:end + 1] if start is not None and end is not None and start <= end else []


def report_checks(text: str, delay: bool = False, review: bool = False) -> dict:
    exp, ls = {k: norm(v) for k, v in expected_report().items()}, report_block(lines(text))
    checks = {
        "first_line": bool(ls) and ls[0] == exp["first_line"],
        "unresolved": exp["unresolved"] in ls,
        "top_priority": exp["top_priority"] in ls,
        "assignee": exp["assignee"] in ls,
        "doc_number_last": bool(ls) and ls[-1] == exp["doc_number_last"],
    }
    if delay:
        checks["delay_line"] = exp["delay_line"] in ls
    if review:
        checks["review_line_before_last"] = len(ls) >= 2 and ls[-2] == exp["review_line_before_last"]
    return checks


def agents(run_dir) -> int:
    """LLM 호출에 쓰인 서로 다른 시스템 프롬프트 수. 참여한 에이전트 수의 근사치다."""
    try:
        calls = json.loads((Path(run_dir) / "calls.json").read_text())
    except (OSError, ValueError):
        return 0
    return len({c.get("system_hash") for c in calls})


def result(checks: dict, **info) -> dict:
    return {"success": all(checks.values()), "checks": checks, **info}
