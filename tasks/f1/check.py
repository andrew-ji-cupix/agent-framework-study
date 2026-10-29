"""F1 채점기. 정답은 mock 데이터에서 계산한다. 사용법: python check.py <output.json>"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))
from sitetools import CREW, ISSUES, SEVERITY_RANK  # noqa: E402


def expected() -> dict:
    unresolved = [
        i for i in ISSUES
        if i["level"] == "3F" and i["trade"] == "electrical" and i["status"] in ("open", "in_progress")
    ]
    top = min(unresolved, key=lambda i: (SEVERITY_RANK[i["severity"]], i["created_at"]))
    crew = min((c for c in CREW if c["trade"] == "electrical"), key=lambda c: (c["open_assignments"], c["name"]))
    return {
        "open_count": len(unresolved),
        "critical_ids": sorted(i["id"] for i in unresolved if i["severity"] == "critical"),
        "top_priority_issue_id": top["id"],
        "recommended_assignee": crew["name"],
    }


def check(path: str | Path) -> dict:
    try:
        out = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        return {"success": False, "error": f"출력 없음 또는 JSON 아님: {e}"}
    exp = expected()
    got = {
        "open_count": out.get("open_count"),
        "critical_ids": sorted(str(x).strip().upper() for x in out.get("critical_ids") or []),
        "top_priority_issue_id": str(out.get("top_priority_issue_id", "")).strip().upper(),
        "recommended_assignee": str(out.get("recommended_assignee", "")).strip(),
    }
    fields = {k: got[k] == v for k, v in exp.items()}
    return {"success": all(fields.values()), "fields": fields, "got": got, "expected": exp}


if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1]), ensure_ascii=False, indent=1))
