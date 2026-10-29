"""건설 현장 mock 도구. Python 후보는 모두 이 함수를 그대로 도구로 등록한다."""

import csv
import json
import os
from pathlib import Path

DATA = Path(__file__).parent / "data"
ISSUES = json.loads((DATA / "issues.json").read_text())
CREW = json.loads((DATA / "crew.json").read_text())
PROGRESS = [{**r, "planned_pct": int(r["planned_pct"]), "actual_pct": int(r["actual_pct"])}
            for r in csv.DictReader((DATA / "progress.csv").open())]
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def search_issues(level: str = "", trade: str = "", status: str = "") -> list[dict]:
    """현장 이슈를 층, 공종, 상태로 검색한다. 빈 문자열인 조건은 무시한다. 요약 필드만 반환한다.

    Args:
        level: 층. B1, 1F, 2F, 3F, 4F, RF 중 하나
        trade: 공종. electrical, plumbing, structural, finishing, fire_protection 중 하나
        status: 상태. open, in_progress, resolved 중 하나
    """
    return [
        {k: i[k] for k in ("id", "title", "level", "trade", "status", "severity")}
        for i in ISSUES
        if (not level or i["level"] == level)
        and (not trade or i["trade"] == trade)
        and (not status or i["status"] == status)
    ]


def get_issue(issue_id: str) -> dict:
    """이슈 ID로 상세 정보(구역, 생성일 created_at, 담당자, 설명)를 조회한다.

    Args:
        issue_id: 이슈 ID. 예: ISS-001
    """
    return next((i for i in ISSUES if i["id"] == issue_id), {"error": f"{issue_id} 이슈가 없습니다"})


def list_crew(trade: str) -> list[dict]:
    """공종별 작업자와 각 작업자의 현재 배정 건수(open_assignments)를 반환한다.

    Args:
        trade: 공종. electrical, plumbing, structural, finishing, fire_protection 중 하나
    """
    return [c for c in CREW if c["trade"] == trade]


def get_progress(level: str = "") -> list[dict]:
    """층별·공종별 계획 공정률(planned_pct)과 실적 공정률(actual_pct)을 반환한다.

    Args:
        level: 층. B1, 1F, 2F, 3F, 4F, RF 중 하나. 빈 문자열이면 전체 층
    """
    return [r for r in PROGRESS if not level or r["level"] == level]


def assign_issue(issue_id: str, assignee: str) -> dict:
    """이슈에 담당자를 배정한다. 배정 기록을 실제로 남기는 작업이다.

    Args:
        issue_id: 이슈 ID. 예: ISS-021
        assignee: 배정할 작업자 이름
    """
    with (Path(os.environ["SCENARIO_DIR"]) / "assignments.jsonl").open("a") as f:
        f.write(json.dumps({"issue_id": issue_id, "assignee": assignee}, ensure_ascii=False) + "\n")
    return {"ok": True, "issue_id": issue_id, "assignee": assignee}
