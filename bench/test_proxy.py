"""proxy.py의 usage 파싱 확인. 실행: uv run --with aiohttp python bench/test_proxy.py"""

import json

from proxy import extract_usage, normalize


def sse(*events):
    return "".join(f"data: {json.dumps(e)}\n\n" for e in events).encode()


# OpenAI Chat Completions 스트림: 마지막 청크에 usage와 cost
chat = extract_usage("text/event-stream", sse(
    {"id": "gen-1", "choices": [{"delta": {"content": "O"}}]},
    {"id": "gen-1", "choices": [], "usage": {"prompt_tokens": 100, "completion_tokens": 10, "cost": 0.0006,
                                             "prompt_tokens_details": {"cached_tokens": 40}}},
) + b"data: [DONE]\n\n")
assert normalize(chat) == {"input_tokens": 100, "output_tokens": 10, "cache_read": 40, "cache_write": 0,
                           "reasoning_tokens": 0, "cost": 0.0006}
assert chat["_id"] == "gen-1"

# Anthropic Messages 스트림: input_tokens에 캐시가 빠져 있고 output은 message_delta가 덮는다
anth = normalize(extract_usage("text/event-stream", sse(
    {"type": "message_start", "message": {"id": "msg-1", "usage": {
        "input_tokens": 10, "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 0, "output_tokens": 1}}},
    {"type": "message_delta", "usage": {"output_tokens": 50}},
)))
assert anth["input_tokens"] == 1010 and anth["output_tokens"] == 50 and anth["cache_read"] == 1000
assert anth["cost_estimated"] and abs(anth["cost"] - (10 * 4e-6 + 1000 * 0.2e-6 + 50 * 20e-6)) < 1e-9

# OpenAI Responses 비스트림
resp = normalize(extract_usage("application/json", json.dumps({"id": "r-1", "usage": {
    "input_tokens": 20, "output_tokens": 5, "input_tokens_details": {"cached_tokens": 0}}}).encode()))
assert resp["input_tokens"] == 20 and resp["output_tokens"] == 5

assert normalize({}) == {"usage_missing": True}
print("proxy usage parsing OK")
