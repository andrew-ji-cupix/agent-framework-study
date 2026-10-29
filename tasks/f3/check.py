"""F3 채점기. 실행 폴더(<run>/approve, <run>/reject)와 실행기가 남긴 steps.json을 본다.
- start 직후: assign_issue가 실행되지 않았고, 승인 대기 중인 호출의 인자가 맞아야 한다.
- resume 후: 승인이면 정확히 1회 실행, 거절이면 실행 0회. 두 경우 모두 에이전트가 끝까지 응답해야 한다."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))
from sitetools import CREW, ISSUES  # noqa: E402


def expected_assignment() -> dict:
    trade = next(i["trade"] for i in ISSUES if i["id"] == "ISS-021")
    crew = min((c for c in CREW if c["trade"] == trade), key=lambda c: (c["open_assignments"], c["name"]))
    return {"issue_id": "ISS-021", "assignee": crew["name"]}


def load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def check(run_dir: str | Path) -> dict:
    run, exp = Path(run_dir), expected_assignment()
    steps = load(run / "steps.json") or []
    report = {}
    for scenario, executed in (("approve", [exp]), ("reject", [])):
        start, resume = ([s for s in steps if s["scenario"] == scenario] + [None, None])[:2]
        pending = load(run / scenario / "pending.json") or {}
        args = pending.get("args") or {}
        checks = {
            "paused_before_execution": bool(start) and start["returncode"] == 0 and start["assignments"] == [],
            "pending_call_correct": pending.get("tool") == "assign_issue"
                                    and {k: args.get(k) for k in exp} == exp,
            "resumed_in_new_process": bool(resume) and resume["returncode"] == 0,
            "executions_correct": bool(resume) and resume["assignments"] == executed,
            "finished": (run / scenario / "final.json").exists(),
        }
        report[scenario] = checks
    return {"success": all(all(c.values()) for c in report.values()), **report}


if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1]), ensure_ascii=False, indent=1))
