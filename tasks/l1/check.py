"""L1 기본 호출: `공종=electrical, 심각도=critical` 한 줄을 답해야 한다."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from ladder_check import load_text, result  # noqa: E402


def check(run_dir) -> dict:
    text = load_text(run_dir).replace("`", "")
    trade, severity = re.search(r"공종\s*=\s*(\w+)", text), re.search(r"심각도\s*=\s*(\w+)", text)
    return result({"trade": bool(trade) and trade[1] == "electrical",
                   "severity": bool(severity) and severity[1] == "critical"}, answer=text[:200])
