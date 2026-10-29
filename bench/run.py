"""과제 실행기와 집계. 프록시(bench/proxy.py)가 떠 있어야 한다.
Framework 후보는 호스트에서, Harness 후보는 agentbench-harness 컨테이너에서 실행한다.

    python3 bench/run.py run f1 langgraph crewai --reps 3 --batch final
    python3 bench/run.py run h1 pi flue --reps 3 --batch final
    python3 bench/run.py summary f1 --batch final
"""

import argparse
import difflib
import importlib.util
import json
import os
import shutil
import statistics
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROXY = "http://127.0.0.1:18790"
PROXY_LOG = ROOT / "results/proxy/calls.jsonl"
RUNS = ROOT / "results/runs"
MODEL = "anthropic/claude-opus-5.5"
IMAGE = "agentbench-harness"
TIMEOUT = {"host": 600, "docker": 1200}
# 여러 프로세스로 나눠 실행하는 과제: (시나리오, 후보 명령 뒤에 붙일 인자). F3는 시작과 재개를 다른 프로세스에서 한다
STEPS = {"f3": [("approve", ["start"]), ("approve", ["resume", "approve"]),
                ("reject", ["start"]), ("reject", ["resume", "reject"])],
         "l5": [(None, ["remember"]), (None, ["report"])]}  # L5: 기억시키는 세션과 새 대화의 리포트 세션
LADDER = [f"l{i}" for i in range(1, 7)]  # 이슈 비서 키우기 단계


def py(name: str, pkg: str) -> dict:
    return {"cmd": [f"frameworks/{name}/.venv/bin/python", f"frameworks/{name}/{{task}}.py"],
            "src": f"frameworks/{name}/{{task}}.py", "pkg": pkg, "env": f"frameworks/{name}/.venv"}


HARNESSES = {
    "claude-agent-sdk": {"docker": ["/opt/h/claude-agent-sdk/.venv/bin/python", "/opt/h/claude-agent-sdk/{task}.py"],
                         "src": "harnesses/claude-agent-sdk/{task}.py", "pkg": "claude-agent-sdk",
                         "env": "harnesses/claude-agent-sdk/.venv"},
    "deepagents": {"docker": ["/opt/h/deepagents/.venv/bin/python", "/opt/h/deepagents/{task}.py"],
                   "src": "harnesses/deepagents/{task}.py", "pkg": "deepagents", "env": "harnesses/deepagents/.venv"},
    "pi": {"docker": ["/opt/h/pi/node_modules/.bin/tsx", "/opt/h/pi/{task}.ts"],
           "src": "harnesses/pi/{task}.ts", "pkg": "@earendil-works/pi-coding-agent", "env": "harnesses/pi/node_modules"},
    "flue": {"docker": ["sh", "/opt/h/flue/run.sh", "{task}"], "mounts": ["harnesses/flue/run.sh"],
             "src": "harnesses/flue/{task}.ts", "pkg": "@flue/runtime", "env": "harnesses/flue/node_modules"},
}

FRAMEWORKS = {
    "langgraph": py("langgraph", "langgraph"),
    "crewai": py("crewai", "crewai"),
    "strands": py("strands", "strands-agents"),
    "adk": py("adk", "google-adk"),
    "openai-agents": py("openai-agents", "openai-agents"),
    "pydantic-ai": py("pydantic-ai", "pydantic-ai-slim"),
    "mastra": {"cmd": ["frameworks/mastra/node_modules/.bin/tsx", "frameworks/mastra/{task}.ts"],
               "src": "frameworks/mastra/{task}.ts", "pkg": "@mastra/core", "env": "frameworks/mastra/node_modules"},
}
CANDIDATES = FRAMEWORKS | HARNESSES


def run_env(run_id: str, out: Path) -> dict:
    # 사용자 셸의 LLM 관련 설정(Bedrock 등)이 후보에 새지 않게 지우고, 모두 같은 조건으로 실행한다
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE", "AWS_", "OPENAI_", "OPENROUTER_"))}
    return env | {
        "LLM_MODEL": MODEL, "LLM_API_KEY": "proxy",
        "LLM_BASE_URL": f"{PROXY}/r/{run_id}/api/v1",
        "LLM_ANTHROPIC_BASE_URL": f"{PROXY}/r/{run_id}/api",
        "RESULT_PATH": str(out / "output.json"),
        "OTEL_SDK_DISABLED": "true", "CREWAI_DISABLE_TELEMETRY": "true", "CREWAI_TRACING_ENABLED": "false",
        "DO_NOT_TRACK": "1",
    }


def proxy_calls(run_id: str) -> list[dict]:
    calls = [json.loads(line) for line in PROXY_LOG.open()] if PROXY_LOG.exists() else []
    return [c for c in calls if c["run_id"] == run_id and c["path"] != "/api/v1/models"]


def load_check(task: str):
    spec = importlib.util.spec_from_file_location(f"check_{task}", ROOT / f"tasks/{task}/check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check


def target_of(task: str, cand: str, out: Path) -> Path:
    """채점기에 넘길 경로. 하네스의 H 과제는 작업 폴더, 여러 단계나 단계 실험 과제는 실행 폴더, 나머지는 출력 파일."""
    if task in LADDER or task in STEPS:
        return out
    return out / "workspace" if cand in HARNESSES else out / "output.json"


def execute(cmd: list[str], env: dict, timeout: int, container: str | None) -> tuple:
    try:
        p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        if container:
            subprocess.run(["docker", "kill", container], capture_output=True)
        return "timeout", *[s.decode(errors="replace") if isinstance(s, bytes) else (s or "") for s in (e.stdout, e.stderr)]


def run_one(task: str, cand: str, rep: int, batch: str) -> dict:
    run_id = f"{task}-{cand}-{rep}-{datetime.now():%m%d%H%M%S}"
    out = RUNS / run_id
    out.mkdir(parents=True)
    spec = CANDIDATES[cand]
    target = target_of(task, cand, out)
    if "docker" in spec:
        # 작업 폴더, 과제, 공통 자산, 후보 스크립트만 마운트한다. 키는 넣지 않고 호스트의 프록시를 쓴다
        workspace, fixture = out / "workspace", ROOT / f"tasks/{task}/fixture"
        shutil.copytree(fixture, workspace) if fixture.exists() else workspace.mkdir()
        host = "http://host.docker.internal" + PROXY[PROXY.rindex(":"):]
        env = {"LLM_MODEL": MODEL, "LLM_API_KEY": "proxy", "LLM_BASE_URL": f"{host}/r/{run_id}/api/v1",
               "LLM_ANTHROPIC_BASE_URL": f"{host}/r/{run_id}/api", "RESULT_PATH": "/out/output.json"}
        scripts = [spec["src"].format(task=task), *spec.get("mounts", [])]
        mounts = [f"{workspace}:/workspace", f"{ROOT / 'tasks' / task}:/task:ro", f"{out}:/out",
                  f"{ROOT / 'shared'}:/shared:ro",
                  *[f"{ROOT / s}:/opt/h/{cand}/{Path(s).name}:ro" for s in scripts]]
        cmd = ["docker", "run", "--rm", "--name", run_id, *[a for m in mounts for a in ("-v", m)],
               *[a for k, v in env.items() for a in ("-e", f"{k}={v}")], IMAGE,
               *[c.format(task=task) for c in spec["docker"]]]
        timeout = TIMEOUT["docker"]
    else:
        cmd = [c.format(task=task) for c in spec["cmd"]]
        timeout = TIMEOUT["host"]
    t0, rcs, steps = time.monotonic(), [], []
    stdout_log, stderr_log = (out / "stdout.log").open("w"), (out / "stderr.log").open("w")
    for scenario, args in STEPS.get(task, [(None, [])]):
        env = run_env(run_id, out)
        if scenario:  # 시나리오마다 상태 저장 폴더를 따로 둔다
            (out / scenario).mkdir(exist_ok=True)
            env["SCENARIO_DIR"] = str(out / scenario)
        rc, stdout, stderr = execute(cmd + args, env, timeout, run_id if "docker" in spec else None)
        rcs.append(rc)
        for log, text in ((stdout_log, stdout), (stderr_log, stderr)):
            log.write((f"### {scenario} {' '.join(args)} (rc={rc})\n" if scenario else "") + text)
        if scenario:  # 이 단계가 끝난 시점의 실제 배정 기록
            path = out / scenario / "assignments.jsonl"
            done = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
            steps.append({"scenario": scenario, "args": args, "returncode": rc, "assignments": done})
    wall = time.monotonic() - t0
    stdout_log.close()
    stderr_log.close()
    if steps:
        (out / "steps.json").write_text(json.dumps(steps, ensure_ascii=False, indent=1))

    calls = proxy_calls(run_id)
    (out / "calls.json").write_text(json.dumps(calls, ensure_ascii=False))  # 채점기가 에이전트 수를 셀 때 쓴다
    total = lambda k: sum(c.get(k) or 0 for c in calls)  # noqa: E731
    result = {
        "run_id": run_id, "batch": batch, "task": task, "candidate": cand, "rep": rep,
        "returncode": rcs[0] if len(rcs) == 1 else rcs,
        "wall_secs": round(wall, 2), **load_check(task)(target),
        "llm_calls": len(calls), "input_tokens": total("input_tokens"), "output_tokens": total("output_tokens"),
        "cache_read": total("cache_read"), "cache_write": total("cache_write"),
        "reasoning_tokens": total("reasoning_tokens"), "cost": round(total("cost"), 6),
        "first_input_tokens": calls[0].get("input_tokens") if calls else None,
        "api": sorted({c["path"] for c in calls}),
        "http_errors": [c.get("error", "")[:300] for c in calls if c["status"] >= 400][:3],
    }
    (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    return result


RUN_KEYS = ("run_id", "batch", "task", "candidate", "rep", "returncode", "wall_secs", "llm_calls", "input_tokens",
            "output_tokens", "cache_read", "cache_write", "reasoning_tokens", "cost", "first_input_tokens", "api",
            "http_errors")


def regrade(task: str) -> int:
    """채점기를 고친 뒤 기존 실행 결과를 같은 기준으로 다시 채점한다."""
    check, runs = load_check(task), list(RUNS.glob(f"{task}-*/result.json"))
    for path in runs:
        res = json.loads(path.read_text())
        res = {k: res[k] for k in RUN_KEYS if k in res} | check(target_of(task, res["candidate"], path.parent))
        res["regraded"] = True
        path.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    return len(runs)


def code_lines(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text().splitlines()]
    return [line for line in lines if line and not line.startswith(("#", "//"))]


def loc(path: Path) -> int:
    return len(code_lines(path))


LADDER_BASE = {"l2": "l1", "l3": "l2", "l4": "l3", "l5": "l4", "l6": "l4"}  # L5, L6는 각각 L4 위에 얹었다


def changed_lines(old: Path, new: Path) -> int:
    """이전 단계 파일 대비 새로 쓰거나 바꾼 줄 수(비어 있지 않은 비주석 줄 기준)."""
    ops = difflib.SequenceMatcher(None, code_lines(old), code_lines(new)).get_opcodes()
    return sum(j2 - j1 for tag, _, _, j1, j2 in ops if tag in ("insert", "replace"))


def ladder_summary(batch: str) -> str:
    rs = [json.loads(p.read_text()) for p in RUNS.glob("l[1-6]-*/result.json")]
    res = {(r["candidate"], r["task"]): r for r in rs if r["batch"] == batch}
    head = "| 후보 | " + " | ".join(t.upper() for t in LADDER) + " |\n|" + " --- |" * (len(LADDER) + 1)
    loc_rows, ok_rows, cost_rows = [head], [head], [head]
    for cand, spec in CANDIDATES.items():
        src = lambda t: ROOT / spec["src"].format(task=t)  # noqa: E731
        if not all((cand, t) in res for t in LADDER):
            continue
        locs = [f"{loc(src(t))}" + (f" (+{changed_lines(src(LADDER_BASE[t]), src(t))})" if t in LADDER_BASE else "")
                for t in LADDER]
        loc_rows.append(f"| {cand} | " + " | ".join(locs) + " |")
        ok_rows.append(f"| {cand} | " + " | ".join("✓" if res[cand, t]["success"] else "✗" for t in LADDER) + " |")
        cost_rows.append(f"| {cand} | " + " | ".join(f"{res[cand, t]['cost']:.3f} / {res[cand, t]['llm_calls']}"
                                                    for t in LADDER) + " |")
    text = (f"# 이슈 비서 키우기 (batch: {batch}, 모델: {MODEL})\n\n"
            "## 코드 줄 수 (괄호: 이전 단계 대비 새로 쓰거나 바꾼 줄. L5·L6는 L4 대비)\n\n" + "\n".join(loc_rows) +
            "\n\n## 동작 확인 (단계별 1회)\n\n" + "\n".join(ok_rows) +
            "\n\n## 비용($) / LLM 호출 수\n\n" + "\n".join(cost_rows) + "\n")
    (ROOT / f"results/summary-ladder-{batch}.md").write_text(text)
    return text


def footprint(cand: str) -> dict:
    c = CANDIDATES[cand]
    env = ROOT / c["env"]
    size_mb = int(subprocess.run(["du", "-sk", str(env)], capture_output=True, text=True).stdout.split()[0]) // 1024
    if c["env"].endswith("node_modules"):
        pkgs = len([p for p in (env / ".pnpm").iterdir() if "@" in p.name])
        version = json.loads((env / c["pkg"] / "package.json").read_text())["version"]
    else:
        code = ("import importlib.metadata as m, sys; "
                f"print(len(list(m.distributions())), m.version('{c['pkg']}'))")
        n, version = subprocess.run([str(env / "bin/python"), "-I", "-c", code],
                                    capture_output=True, text=True).stdout.split()
        pkgs = int(n)
    return {"version": version, "packages": pkgs, "size_mb": size_mb}


def summary(task: str, batch: str) -> str:
    results = [json.loads(p.read_text()) for p in RUNS.glob(f"{task}-*/result.json")]
    results = [r for r in results if r["batch"] == batch]
    med = lambda rs, k: statistics.median([r[k] for r in rs if r[k] is not None] or [0])  # noqa: E731
    harness = any(r["candidate"] in HARNESSES for r in results)
    head = ["후보", "버전", "성공", "시간(s)", "LLM 호출", "입력 토큰", "캐시 읽기", "출력 토큰", "첫 요청 입력", "비용($)"]
    head += ["연동 코드 줄"] if harness else ["코드 줄", "패키지 수", "설치(MB)"]
    rows = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
    for cand in CANDIDATES:
        rs = [r for r in results if r["candidate"] == cand]
        if not rs:
            continue
        fp = footprint(cand)
        src = ROOT / CANDIDATES[cand]["src"].format(task=task)
        cells = [cand, fp["version"], f"{sum(r['success'] for r in rs)}/{len(rs)}", f"{med(rs, 'wall_secs'):.1f}",
                 f"{med(rs, 'llm_calls'):g}", f"{med(rs, 'input_tokens'):,.0f}", f"{med(rs, 'cache_read'):,.0f}",
                 f"{med(rs, 'output_tokens'):,.0f}", f"{med(rs, 'first_input_tokens'):,.0f}", f"{med(rs, 'cost'):.4f}"]
        cells += [str(loc(src))] if harness else [str(loc(src)), str(fp["packages"]), str(fp["size_mb"])]
        rows.append("| " + " | ".join(cells) + " |")
    table = "\n".join(rows)
    (ROOT / f"results/summary-{task}-{batch}.md").write_text(
        f"# {task} 결과 (batch: {batch}, 모델: {MODEL})\n\n값은 중앙값이다. 코드 줄 수는 비어 있지 않은 비주석 줄이다.\n\n{table}\n")
    return table


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("task")
    r.add_argument("candidates", nargs="+", choices=list(CANDIDATES))
    r.add_argument("--reps", type=int, default=1)
    r.add_argument("--batch", default="dev")
    s = sub.add_parser("summary")
    s.add_argument("task")
    s.add_argument("--batch", required=True)
    g = sub.add_parser("regrade")
    g.add_argument("task")
    lad = sub.add_parser("ladder")
    lad.add_argument("--batch", required=True)
    args = ap.parse_args()

    if args.cmd == "ladder":
        print(ladder_summary(args.batch))
        return

    if args.cmd == "summary":
        print(summary(args.task, args.batch))
        return
    if args.cmd == "regrade":
        print(f"regraded {regrade(args.task)} runs")
        return
    for rep in range(1, args.reps + 1):
        for cand in args.candidates:
            res = run_one(args.task, cand, rep, args.batch)
            print(json.dumps({k: res.get(k) for k in ("run_id", "success", "returncode", "wall_secs", "llm_calls",
                                                       "input_tokens", "output_tokens", "cost", "http_errors", "error")},
                             ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
