# /// script
# requires-python = ">=3.12"
# dependencies = ["aiohttp>=3.9"]
# ///
"""OpenRouter 기록 프록시.

/r/<run_id>/api/... 요청을 https://openrouter.ai/api/... 로 전달하고 응답의 usage를 run_id별로 기록한다.
후보 코드는 가짜 키를 쓰고, 실제 키(OPENROUTER_API_KEY)는 이 프로세스만 갖는다.

    kg run --secret OPENROUTER_API_KEY -- uv run bench/proxy.py
"""

import argparse
import asyncio
import hashlib
import json
import os
import time
from pathlib import Path

from aiohttp import ClientSession, ClientTimeout, web

UPSTREAM = "https://openrouter.ai"
ALLOWED = {
    ("POST", "/api/v1/chat/completions"),
    ("POST", "/api/v1/messages"),
    ("POST", "/api/v1/messages/count_tokens"),
    ("POST", "/api/v1/responses"),
    ("POST", "/api/v1/embeddings"),  # CrewAI 메모리가 쓰는 임베딩
    ("GET", "/api/v1/models"),
}
PASS_HEADERS = {"content-type", "accept", "anthropic-version", "anthropic-beta", "user-agent"}
# anthropic/claude-opus-5.5의 OpenRouter 단가(USD/token). 응답에 cost가 없을 때만 쓴다.
PRICE = {"input": 4e-6, "output": 20e-6, "cache_read": 0.2e-6, "cache_write": 5e-6}


def parse_json(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return None


def extract_usage(ctype: str, raw: bytes) -> dict:
    """JSON 응답 또는 SSE 스트림에서 usage를 모은다. 스트림은 뒤에 온 값이 앞의 값을 덮는다."""
    events = []
    if "event-stream" in ctype:
        for line in raw.decode(errors="replace").splitlines():
            if line.startswith("data:"):
                events.append(parse_json(line[5:].strip()))
    else:
        events.append(parse_json(raw))
    usage = {}
    for e in events:
        if not isinstance(e, dict):
            continue
        u = e.get("usage") or (e.get("message") or {}).get("usage") or (e.get("response") or {}).get("usage")
        if isinstance(u, dict):
            usage.update({k: v for k, v in u.items() if v is not None})
        usage.setdefault("_id", e.get("id") or (e.get("message") or {}).get("id"))
    return usage


def normalize(u: dict) -> dict:
    """세 가지 응답 형식의 usage를 input(캐시 포함 전체)/output/cache 형식으로 맞춘다."""
    if "prompt_tokens" in u:  # OpenAI Chat Completions
        pd, cd = u.get("prompt_tokens_details") or {}, u.get("completion_tokens_details") or {}
        n = {"input_tokens": u["prompt_tokens"], "output_tokens": u.get("completion_tokens", 0),
             "cache_read": pd.get("cached_tokens") or 0, "cache_write": pd.get("cache_write_tokens") or 0,
             "reasoning_tokens": cd.get("reasoning_tokens") or 0}
    elif "input_tokens_details" in u:  # OpenAI Responses
        n = {"input_tokens": u["input_tokens"], "output_tokens": u.get("output_tokens", 0),
             "cache_read": u["input_tokens_details"].get("cached_tokens") or 0, "cache_write": 0,
             "reasoning_tokens": (u.get("output_tokens_details") or {}).get("reasoning_tokens") or 0}
    elif "input_tokens" in u:  # Anthropic Messages: input_tokens에 캐시 토큰이 빠져 있다
        cr, cw = u.get("cache_read_input_tokens") or 0, u.get("cache_creation_input_tokens") or 0
        n = {"input_tokens": u["input_tokens"] + cr + cw, "output_tokens": u.get("output_tokens", 0),
             "cache_read": cr, "cache_write": cw, "reasoning_tokens": 0}
    else:
        return {"usage_missing": True}
    if u.get("cost") is not None:
        n["cost"] = u["cost"]
    else:
        fresh = n["input_tokens"] - n["cache_read"] - n["cache_write"]
        n["cost"] = round(fresh * PRICE["input"] + n["cache_read"] * PRICE["cache_read"]
                          + n["cache_write"] * PRICE["cache_write"] + n["output_tokens"] * PRICE["output"], 6)
        n["cost_estimated"] = True
    return n


def describe_request(body: bytes) -> dict:
    req = parse_json(body) or {}
    msgs = req.get("messages") or req.get("input") or []
    msgs = msgs if isinstance(msgs, list) else []
    system = [req.get("system") or "", req.get("instructions") or ""]
    system += [m.get("content") for m in msgs if isinstance(m, dict) and m.get("role") in ("system", "developer")]
    return {
        "model": req.get("model"), "stream": bool(req.get("stream")), "n_messages": len(msgs),
        "n_tools": len(req.get("tools") or []), "req_bytes": len(body),
        "system_chars": len(json.dumps(system, ensure_ascii=False)),
        # 멀티에이전트에서 어느 에이전트의 호출인지 구분하는 용도
        "system_hash": hashlib.sha1(json.dumps(system, ensure_ascii=False).encode()).hexdigest()[:8],
        "tools_chars": len(json.dumps(req.get("tools") or [], ensure_ascii=False)),
        "tool_choice": req.get("tool_choice"),
        "structured": (req.get("response_format") or {}).get("type") or ("output_config" if req.get("output_config") else None),
    }


def log_call(app: web.Application, rec: dict) -> None:
    app["state"]["spent"] += rec.get("cost") or 0
    with app["log"].open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


async def proxy(request: web.Request) -> web.StreamResponse:
    run_id, path = request.match_info["run_id"], "/" + request.match_info["tail"]
    app, state = request.app, request.app["state"]
    if (request.method, path) not in ALLOWED:
        return web.json_response({"error": {"message": f"proxy: {request.method} {path} is not allowed"}}, status=403)
    if state["spent"] >= app["max_cost"]:
        return web.json_response({"error": {"message": "proxy: cost cap reached"}}, status=402)

    body = await request.read()
    headers = {k: v for k, v in request.headers.items() if k.lower() in PASS_HEADERS}
    headers["Authorization"] = f"Bearer {app['key']}"
    t0, chunks = time.monotonic(), []
    base = {"run_id": run_id, "path": path, **describe_request(body)}
    try:
        async with app["session"].request(request.method, UPSTREAM + path, data=body or None,
                                          headers=headers, params=request.query) as up:
            resp = web.StreamResponse(status=up.status)
            resp.headers["Content-Type"] = up.headers.get("Content-Type", "application/json")
            await resp.prepare(request)
            async for chunk in up.content.iter_any():
                chunks.append(chunk)
                await resp.write(chunk)
            await resp.write_eof()
    except (Exception, asyncio.CancelledError) as e:  # 업스트림 지연이나 연결 끊김도 남겨야 원인을 추적할 수 있다
        log_call(app, {"ts": round(time.time(), 3), "status": 599, "secs": round(time.monotonic() - t0, 3),
                       "bytes_received": sum(map(len, chunks)), "error": f"proxy: {type(e).__name__}: {e}", **base})
        raise

    raw = b"".join(chunks)
    usage = extract_usage(up.headers.get("Content-Type", ""), raw)
    rec = {"ts": round(time.time(), 3), "status": up.status, "secs": round(time.monotonic() - t0, 3),
           "gen_id": usage.get("_id"), **base}
    if path != "/api/v1/models":
        rec.update(normalize(usage))
    if up.status >= 400:
        rec["error"] = raw[:800].decode(errors="replace")
    log_call(app, rec)
    first = app["req_dir"] / f"{run_id}.json"  # 시스템 프롬프트·도구 정의 분석용으로 첫 요청만 보관
    if body and not first.exists():
        first.write_bytes(body)
    return resp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=18790)
    ap.add_argument("--log", default="results/proxy/calls.jsonl")
    ap.add_argument("--max-cost", type=float, default=40.0, help="누적 비용 상한(USD). 기존 로그의 비용도 합산한다")
    args = ap.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY가 없습니다. kg run --secret OPENROUTER_API_KEY -- ... 로 실행하세요.")

    log = Path(args.log)
    (log.parent / "first-requests").mkdir(parents=True, exist_ok=True)
    spent = sum(json.loads(line).get("cost") or 0 for line in log.open()) if log.exists() else 0.0

    app = web.Application(client_max_size=64 * 1024 * 1024)
    app["key"], app["log"], app["req_dir"], app["max_cost"] = key, log, log.parent / "first-requests", args.max_cost
    app["state"] = {"spent": spent}

    async def session_ctx(app):
        app["session"] = ClientSession(timeout=ClientTimeout(total=None, sock_read=900))
        yield
        await app["session"].close()

    async def spent_handler(_):
        return web.json_response({"spent": round(app["state"]["spent"], 4), "max_cost": args.max_cost})

    app.cleanup_ctx.append(session_ctx)
    app.router.add_get("/spent", spent_handler)
    app.router.add_route("*", "/r/{run_id}/{tail:.*}", proxy)
    print(f"proxy http://{args.host}:{args.port} spent=${spent:.2f} cap=${args.max_cost}", flush=True)
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
