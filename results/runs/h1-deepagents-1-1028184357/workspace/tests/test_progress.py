from sitekit.progress import completion_rate, delayed, gap

ROWS = [
    {"level": "1F", "trade": "electrical", "planned_pct": 80, "actual_pct": 66},
    {"level": "3F", "trade": "plumbing", "planned_pct": 60, "actual_pct": 48},
    {"level": "4F", "trade": "fire_protection", "planned_pct": 25, "actual_pct": 15},
    {"level": "2F", "trade": "electrical", "planned_pct": 70, "actual_pct": 61},
    {"level": "RF", "trade": "finishing", "planned_pct": 0, "actual_pct": 0},
]


def test_gap_is_positive_when_behind():
    assert gap(ROWS[0]) == 14


def test_delayed_includes_threshold_boundary():
    assert {(r["level"], r["trade"]) for r in delayed(ROWS)} == {
        ("1F", "electrical"), ("3F", "plumbing"), ("4F", "fire_protection")}


def test_delayed_is_sorted_by_largest_gap_first():
    assert [gap(r) for r in delayed(ROWS)] == [14, 12, 10]


def test_completion_rate():
    assert completion_rate(ROWS) == 38.0
