"""L4 서브에이전트: L3 + 공정 분석가(서브에이전트)에게 받은 지연 공종 줄. 메인 에이전트에는 공정 도구가 없다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from ladder_check import agents, load_text, report_checks, result  # noqa: E402


def check(run_dir) -> dict:
    checks = report_checks(load_text(run_dir), delay=True)
    checks["subagent_used"] = agents(run_dir) >= 2
    return result(checks, agents=agents(run_dir))
