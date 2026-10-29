"""L3 스킬: 사내 리포트 규칙(스킬)에 맞는 리포트. 규칙은 프롬프트에 없고 스킬에만 있다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from ladder_check import agents, load_text, report_checks, result  # noqa: E402


def check(run_dir) -> dict:
    return result(report_checks(load_text(run_dir)), agents=agents(run_dir))
