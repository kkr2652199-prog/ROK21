# -*- coding: utf-8 -*-
"""K-LEARN-REFEREE-REFILL — 단계④ learn/referee 재누적.

강제BT 리셋 후 learn_state=0·referee균등0.333 해소.
`walkforward.run_review_loop(1137~1236)` → get_referee_weights 스프레드 측정.
BT pool 캐시 보존 · ge3미클레임 · 1237아님.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KLEARN_REFEREE_REFILL.json"
OUT_MD = ROOT / "reports" / "20260812_KLEARN_REFEREE_REFILL.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _spread(w: dict[str, float]) -> float:
    vals = list(w.values())
    return float(max(vals) - min(vals)) if vals else 0.0


def _snapshot(label: str) -> dict[str, Any]:
    from app.testlotto.learn_state import (
        PREDICT_BRAIN_TAGS,
        get_all_learn_states,
        get_referee_weights,
        get_referee_weights_global,
    )
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db

    set_learn_as_of(HI + 1)
    states = get_all_learn_states()
    live = get_referee_weights()
    glob = get_referee_weights_global()
    conn = get_lotto_db()
    try:
        rev = conn.execute(
            "SELECT brain_tag, COUNT(*) c FROM testlotto_brain_review "
            "WHERE draw_no BETWEEN ? AND ? GROUP BY brain_tag",
            (LO, HI),
        ).fetchall()
        learn_n = conn.execute(
            "SELECT COUNT(*) FROM testlotto_brain_learn_state"
        ).fetchone()[0]
        pool_draws = conn.execute(
            "SELECT COUNT(DISTINCT draw_no) FROM testlotto_pool_view_cache"
        ).fetchone()[0]
    finally:
        conn.close()
    return {
        "label": label,
        "as_of": HI + 1,
        "review_counts": {
            t: int(states[t].get("review_count", 0) or 0) for t in PREDICT_BRAIN_TAGS
        },
        "avgs": {
            t: float(states[t].get("recent_avg_match", 0.0) or 0.0)
            for t in PREDICT_BRAIN_TAGS
        },
        "live_referee": {k: round(float(v), 6) for k, v in live.items()},
        "global_referee": {k: round(float(v), 6) for k, v in glob.items()},
        "spread_live": round(_spread(live), 6),
        "brain_review_counts": {str(r["brain_tag"]): int(r["c"]) for r in rev},
        "learn_state_rows": int(learn_n),
        "pool_cache_draws": int(pool_draws),
    }


def main() -> None:
    from app.testlotto.learn_state_cutoff import clear_history_cache
    from app.testlotto.walkforward import run_review_loop

    before = _snapshot("before")
    print("BEFORE", json.dumps(before, ensure_ascii=False), flush=True)

    clear_history_cache()
    loop = run_review_loop(LO, HI, progress_every=20)
    clear_history_cache()
    print("LOOP", {k: loop.get(k) for k in ("n", "ok", "errors") if k in loop or True}, flush=True)

    after = _snapshot("after")
    print("AFTER", json.dumps(after, ensure_ascii=False), flush=True)

    ok = (
        after["pool_cache_draws"] == 100
        and all(after["review_counts"].get(t, 0) >= 50 for t in ("stat", "markov", "review"))
        and after["spread_live"] > 1e-6
    )
    verdict = "REFILL_OK" if ok else "REFILL_PARTIAL"

    out = {
        "id": "K-LEARN-REFEREE-REFILL",
        "ts": _now(),
        "range": [LO, HI],
        "before": before,
        "loop": loop if isinstance(loop, dict) else {"raw": str(loop)},
        "after": after,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "step": 4,
        "note": "BT v4 pool 보존 · 1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = f"""# K-LEARN-REFEREE-REFILL

시각: {out['ts']} · 단계④ · {LO}~{HI}

## 판정 **{verdict}**

| 항목 | before | after |
|------|--------|-------|
| review_counts | {before['review_counts']} | {after['review_counts']} |
| avgs | {before['avgs']} | {after['avgs']} |
| live_referee | {before['live_referee']} | {after['live_referee']} |
| spread_live | {before['spread_live']} | {after['spread_live']} |
| pool_cache_draws | {before['pool_cache_draws']} | {after['pool_cache_draws']} |
| brain_review | {before['brain_review_counts']} | {after['brain_review_counts']} |

## 참고
- ge3 미클레임 · mean/avgs 서열화 금지(K-O)
- 다음=⑤ K-G ending boost 조사
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict, flush=True)
    print("WROTE", OUT_JSON, flush=True)


if __name__ == "__main__":
    main()
