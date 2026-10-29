"""H1 채점기. 원본 fixture에 에이전트가 고친 sitekit/만 덮어써서 네트워크 없는 컨테이너에서 pytest를 돌린다.
테스트 파일이나 루트 설정을 바꿔 통과시키는 경우를 막기 위해서다. 사용법: python check.py <workspace>"""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixture"
TMP = Path(__file__).parents[2] / "results/tmp"  # OrbStack이 마운트할 수 있는 /Users 아래에 둔다
IMAGE = "agentbench-harness"


def digest(d: Path) -> dict:
    return {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(d.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def check(workspace: str | Path) -> dict:
    ws = Path(workspace)
    if not (ws / "sitekit").is_dir():
        return {"success": False, "error": "sitekit/ 없음"}
    tests_unchanged = digest(ws / "tests") == digest(FIXTURE / "tests")
    TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=TMP) as tmp:
        clean = Path(tmp) / "w"
        shutil.copytree(FIXTURE, clean, ignore=shutil.ignore_patterns("sitekit"))
        shutil.copytree(ws / "sitekit", clean / "sitekit", ignore=shutil.ignore_patterns("__pycache__"))
        p = subprocess.run(["docker", "run", "--rm", "--network", "none", "-v", f"{clean}:/w", "-w", "/w", IMAGE,
                            "python", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                           capture_output=True, text=True, timeout=180)
    summary = (p.stdout.strip().splitlines() or [p.stderr.strip()[-200:]])[-1]
    return {"success": tests_unchanged and p.returncode == 0, "tests_unchanged": tests_unchanged, "pytest": summary}


if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1]), ensure_ascii=False, indent=1))
