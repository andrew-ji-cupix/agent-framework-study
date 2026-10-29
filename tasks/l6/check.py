"""L6 멀티에이전트 구조: L4와 같은 리포트를 역할이 나뉜 에이전트 팀(분석 → 작성 → 검토)이 만든다.
에이전트 3개 이상이 참여해야 한다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from ladder_check import agents, load_text, report_checks, result  # noqa: E402


def check(run_dir) -> dict:
    checks = report_checks(load_text(run_dir), delay=True)
    checks["team_of_3_or_more"] = agents(run_dir) >= 3
    return result(checks, agents=agents(run_dir))
