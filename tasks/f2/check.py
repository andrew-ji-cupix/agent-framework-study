"""F2 채점기. 정답은 mock 데이터에서 계산한다. 사용법: python check.py <output.json>"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))
from sitetools import ISSUES, PROGRESS  # noqa: E402

# 프롬프트가 데이터 코드를 요구하지 않았으므로 한국어 표기도 같은 값으로 본다 (예: "설비(배관)" → plumbing)
TRADE_ALIASES = {"electrical": ("전기",), "plumbing": ("설비", "배관"), "structural": ("구조", "골조"),
                 "finishing": ("마감",), "fire_protection": ("소방",)}


def norm_trade(text: str) -> str:
    t = text.strip().lower()
    return next((code for code, words in TRADE_ALIASES.items() if t == code or any(w in t for w in words)), t)


def norm_level(text: str) -> str:
    t = text.strip().upper().replace(" ", "")
    if m := re.fullmatch(r"지하(\d)층?", t):
        return f"B{m[1]}"
    if m := re.fullmatch(r"(\d)층", t):
        return f"{m[1]}F"
    return "RF" if t in ("옥상", "지붕") else t


def expected() -> dict:
    delayed = {(r["level"], r["trade"]): r["planned_pct"] - r["actual_pct"]
               for r in PROGRESS if r["planned_pct"] - r["actual_pct"] >= 10}
    critical = Counter(i["level"] for i in ISSUES
                       if i["severity"] == "critical" and i["status"] in ("open", "in_progress"))
    score = Counter(level for level, _ in delayed) + critical
    (focus, top), (_, second) = score.most_common(2)
    assert top > second, "focus_level 정답이 하나로 정해지지 않는다"
    return {"delayed_trades": delayed, "critical_by_level": dict(critical), "focus_level": focus}


def check(path: str | Path) -> dict:
    try:
        out = json.loads(Path(path).read_text())
        got = {
            "delayed_trades": {(norm_level(d["level"]), norm_trade(d["trade"])): d["gap"] for d in out["delayed_trades"]},
            "critical_by_level": {norm_level(c["level"]): c["count"] for c in out["critical_by_level"] if c["count"]},
            "focus_level": norm_level(out["focus_level"]),
        }
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        return {"success": False, "error": f"출력 없음 또는 형식 오류: {e!r}"}
    exp = expected()
    fields = {k: got[k] == v for k, v in exp.items()}
    return {"success": all(fields.values()), "fields": fields,
            "got": {k: (sorted(map(list, v.items())) if k == "delayed_trades" else v) for k, v in got.items()}}


if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1]), ensure_ascii=False, indent=1))
