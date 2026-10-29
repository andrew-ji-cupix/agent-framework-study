"""sitetools.py와 sitetools.ts가 같은 입력에 같은 출력을 내는지 확인한다. 실행: python3 shared/parity_check.py"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

CASES = [
    ("searchIssues", "search_issues", {}),
    ("searchIssues", "search_issues", {"level": "3F", "trade": "electrical"}),
    ("searchIssues", "search_issues", {"status": "open"}),
    ("getIssue", "get_issue", {"issue_id": "ISS-014"}),
    ("getIssue", "get_issue", {"issue_id": "ISS-999"}),
    ("listCrew", "list_crew", {"trade": "electrical"}),
    ("getProgress", "get_progress", {}),
    ("getProgress", "get_progress", {"level": "3F"}),
]
PY = {"search_issues": search_issues, "get_issue": get_issue, "list_crew": list_crew, "get_progress": get_progress}

ts = f"""
import * as t from "{HERE / 'sitetools.ts'}";
const cases = {json.dumps([[c[0], c[2]] for c in CASES])};
console.log(JSON.stringify(cases.map(([fn, args]) => (t as any)[fn](args))));
"""
tsx = HERE.parent / "frameworks/mastra/node_modules/.bin/tsx"
ts_out = json.loads(subprocess.run([str(tsx), "-e", ts], capture_output=True, text=True, check=True).stdout)
for (_, py_name, args), got in zip(CASES, ts_out):
    assert PY[py_name](**args) == got, f"mismatch: {py_name}({args})"
print(f"parity OK ({len(CASES)} cases)")
