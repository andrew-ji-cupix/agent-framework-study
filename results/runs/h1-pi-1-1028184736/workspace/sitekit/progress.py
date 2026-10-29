"""공정률 계산."""


def gap(row: dict) -> int:
    """계획 대비 지연 폭(%p). 양수면 지연이다."""
    return row["planned_pct"] - row["actual_pct"]


def delayed(rows: list[dict], threshold: int = 10) -> list[dict]:
    """지연 폭이 threshold(%p) 이상인 행을 지연 폭이 큰 순서로 반환한다."""
    late = [r for r in rows if gap(r) >= threshold]
    return sorted(late, key=gap, reverse=True)


def completion_rate(rows: list[dict]) -> float:
    """실적 공정률의 평균. 소수 첫째 자리에서 반올림한다."""
    return round(sum(r["actual_pct"] for r in rows) / len(rows), 1)
