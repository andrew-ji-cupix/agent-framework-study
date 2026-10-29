from sitekit.issues import top_priority, unresolved

ISSUES = [
    {"id": "A", "status": "open", "severity": "medium", "created_at": "2026-10-01"},
    {"id": "B", "status": "in_progress", "severity": "low", "created_at": "2026-09-01"},
    {"id": "C", "status": "resolved", "severity": "critical", "created_at": "2026-08-01"},
]


def test_unresolved_includes_in_progress():
    assert {i["id"] for i in unresolved(ISSUES)} == {"A", "B"}


def test_unresolved_excludes_resolved():
    assert "C" not in {i["id"] for i in unresolved(ISSUES)}


def test_top_priority_prefers_severity_over_age():
    assert top_priority(ISSUES)["id"] == "A"


def test_top_priority_breaks_ties_by_oldest():
    issues = [
        {"id": "X", "status": "in_progress", "severity": "critical", "created_at": "2026-10-14"},
        {"id": "Y", "status": "open", "severity": "critical", "created_at": "2026-10-20"},
        {"id": "Z", "status": "open", "severity": "high", "created_at": "2026-10-11"},
    ]
    assert top_priority(issues)["id"] == "X"
