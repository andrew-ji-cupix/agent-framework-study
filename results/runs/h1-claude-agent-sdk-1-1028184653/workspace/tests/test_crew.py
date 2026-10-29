from sitekit.crew import recommend

CREW = [
    {"name": "김민수", "trade": "electrical", "open_assignments": 3},
    {"name": "박지훈", "trade": "electrical", "open_assignments": 1},
    {"name": "이서연", "trade": "electrical", "open_assignments": 1},
    {"name": "최유진", "trade": "electrical", "open_assignments": 4},
    {"name": "오세린", "trade": "plumbing", "open_assignments": 1},
]


def test_recommend_least_loaded():
    assert recommend(CREW[2:], "electrical") == "이서연"


def test_recommend_breaks_ties_by_name():
    assert recommend(CREW, "electrical") == "박지훈"


def test_recommend_only_considers_trade():
    assert recommend(CREW, "plumbing") == "오세린"
