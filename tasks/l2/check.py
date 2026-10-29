"""L2 도구: 도구로 조사해 `최우선=ISS-014, 담당자=이서연` 한 줄을 답해야 한다."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from ladder_check import expected_report, load_text, result  # noqa: E402


def check(run_dir) -> dict:
    exp, text = expected_report(), load_text(run_dir).replace("`", "")
    top, who = re.search(r"최우선\s*=\s*([\w-]+)", text), re.search(r"담당자\s*=\s*([^\s,.]+)", text)
    return result({"top_priority": bool(top) and f"최우선: {top[1]}" == exp["top_priority"],
                   "assignee": bool(who) and f"담당 추천: {who[1]}" == exp["assignee"]}, answer=text[:200])
