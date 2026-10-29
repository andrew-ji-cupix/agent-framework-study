"""L5 메모리: 세션 1(remember)에서 들은 선호를, 새 대화인 세션 2(report)의 리포트에 반영해야 한다.
세션 2 프롬프트에는 선호가 없으므로 장기 메모리를 거쳐야만 `검토 요청` 줄을 넣을 수 있다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from ladder_check import agents, load_text, report_checks, result  # noqa: E402


def check(run_dir) -> dict:
    checks = {"remember_step_answered": bool(load_text(run_dir, "remember")),
              **report_checks(load_text(run_dir), delay=True, review=True)}
    return result(checks, agents=agents(run_dir))
