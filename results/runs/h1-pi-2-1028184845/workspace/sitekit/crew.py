"""작업자 배정."""


def recommend(crew: list[dict], trade: str) -> str:
    """공종 작업자 중 현재 배정 건수가 가장 적은 사람의 이름. 같으면 이름순으로 앞선 사람."""
    members = [c for c in crew if c["trade"] == trade]
    return min(members, key=lambda c: (c["open_assignments"], c["name"]))["name"]
