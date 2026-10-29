"""현장 이슈 분류."""

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def unresolved(issues: list[dict]) -> list[dict]:
    """미해결 이슈(상태가 open 또는 in_progress)를 반환한다."""
    return [i for i in issues if i["status"] in ("open", "in_progress")]


def top_priority(issues: list[dict]) -> dict:
    """미해결 이슈 중 심각도가 가장 높은 이슈. 심각도가 같으면 생성일이 가장 이른 이슈."""
    return min(unresolved(issues), key=lambda i: (SEVERITY_RANK[i["severity"]], i["created_at"]))
