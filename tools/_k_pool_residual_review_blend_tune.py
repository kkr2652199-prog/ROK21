# -*- coding: utf-8 -*-
"""K-POOL-RESIDUAL-REVIEW-BLEND — 단계② review pool 몫축 잔여.

노브: BLEND_STRENGTH_BY_BRAIN['review'] (base=0.85).
축: pool nums prize↓ · |Δ|≥0.005 · prefer iso · (base≥0이면 절대음수 면제).
ge3미사용 · markov/stat 노브 불변.
"""
from __future__ import annotations

import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KPOOL_RESIDUAL_REVIEW_BLEND.json"
OUT_MD = ROOT / "reports" / "20260812_KPOOL_RESIDUAL_REVIEW_BLEND.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80
ABS_THR = 0.005
ISO_THR = 0.005
BASE_B = 0.85
CANDS = [0.85, 0.90, 0.95, 1.00]


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _patch(b: float):
    from app.testlotto.brains.shared import crowd_signal as cs

    saved = float(cs.BLEND_STRENGTH_BY_BRAIN.get("review", BASE_B))
    cs.BLEND_STRENGTH_BY_BRAIN["review"] = float(b)

    def restore() -> None:
        cs.BLEND_STRENGTH_BY_BRAIN["review"] = saved

    return restore


def _run(seed: int, b: float) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy

    restore = _patch(b)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer: list[float] = []
        prize: list[float] = []
        for dno in range(LO, HI + 1):
            sp.set_learn_as_of(dno)
            draws = sp._get_draws_before(dno)
            if len(draws) < 50:
                continue
            fw = _fw_proxy(draws)
            all_mean = mean(fw[n] for n in range(1, 46))
            if all_mean <= 1e-12:
                continue
            random.seed(seed)
            pool = sp.expand_pool(draws, dno, seed=seed)
            pool_br = sp._pool_by_brain(pool)
            mnums = [n for c in pool_br.get("markov", []) for n in c["nums"]]
            rnums = [n for c in pool_br.get("review", []) for n in c["nums"]]
            if mnums:
                prefer.append(mean(fw[n] for n in mnums) - all_mean)
            if rnums:
                prize.append(mean(fw[n] for n in rnums) - all_mean)
            learner.update_from_pool(pool_br, _actual(dno))
        return {
            "seed": seed,
            "n": len(prize),
            "prefer": round(mean(prefer), 6) if prefer else None,
            "prize": round(mean(prize), 6) if prize else None,
        }
    finally:
        restore()


def _agg(b: float, by: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    if base is None:
        return {
            "b": b,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "gate_pass": True,
            "gate_detail": {"is_baseline": True, "pool_prize_nonneg": prize >= 0},
            "per_seed": by,
        }
    dprize = prize - base["prize"]
    drift = abs(prefer - base["prefer"])
    need_neg = base["prize"] < 0
    detail = {
        "prize_ok": (prize < 0) if need_neg else True,
        "improve": prize < base["prize"],
        "abs": abs(dprize) >= ABS_THR,
        "iso": drift < ISO_THR,
        "dprize": round(dprize, 6),
        "drift": round(drift, 6),
    }
    return {
        "b": b,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "gate_pass": all(detail[k] for k in ("prize_ok", "improve", "abs", "iso")),
        "gate_detail": detail,
        "per_seed": by,
    }


def _apply(b: float) -> None:
    path = ROOT / "app" / "testlotto" / "brains" / "shared" / "crowd_signal.py"
    text = path.read_text(encoding="utf-8")
    text2, n = re.subn(
        r'(BLEND_STRENGTH_BY_BRAIN: dict\[str, float\] = \{[^}]*"review": )([0-9.]+)',
        rf"\g<1>{b}",
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError("BLEND_STRENGTH_BY_BRAIN review replace failed")
    path.write_text(text2, encoding="utf-8")
    from app.testlotto.brains.shared import crowd_signal as cs

    cs.BLEND_STRENGTH_BY_BRAIN["review"] = float(b)


def main() -> None:
    from app.testlotto.brains.shared import crowd_signal as cs

    results: list[dict] = []
    print(f"== review blend base={BASE_B} ==", flush=True)
    base_rows = [_run(s, BASE_B) for s in SEEDS]
    base = _agg(BASE_B, base_rows, None)
    results.append(base)
    for b in CANDS:
        if abs(b - BASE_B) < 1e-12:
            continue
        print(f"  run review blend={b} ...", flush=True)
        rows = [_run(s, b) for s in SEEDS]
        results.append(
            _agg(b, rows, {"prefer": base["prefer"], "prize": base["prize"]})
        )

    passers = [r for r in results if r["gate_pass"] and abs(r["b"] - BASE_B) > 1e-12]
    best = min(passers, key=lambda r: r["prize"]) if passers else None
    chosen = float(best["b"]) if best else BASE_B
    if best:
        _apply(chosen)
        verdict = "APPLY"
    else:
        verdict = "NO_IMPROVE_HOLD"

    out = {
        "id": "K-POOL-RESIDUAL-REVIEW-BLEND",
        "ts": _now(),
        "range": [LO, HI],
        "seeds": SEEDS,
        "base_b": BASE_B,
        "cands": CANDS,
        "live_before": dict(cs.BLEND_STRENGTH_BY_BRAIN),
        "results": results,
        "chosen": chosen,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "step": 2,
        "note": "양산前 · 1237아님 · markov BLEND 불변",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-POOL-RESIDUAL-REVIEW-BLEND",
        "",
        f"시각: {out['ts']} · 단계② · {LO}~{HI} · seeds={SEEDS}",
        "",
        f"## 판정 **{verdict}** · chosen review BLEND=`{chosen}`",
        "",
        "| b | prefer | prize | gate |",
        "|---|--------|-------|------|",
    ]
    for r in results:
        lines.append(
            f"| {r['b']} | {r.get('prefer')} | {r.get('prize')} | {r['gate_pass']} |"
        )
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print("VERDICT", verdict, "chosen", chosen, flush=True)
    print("WROTE", OUT_JSON, flush=True)


if __name__ == "__main__":
    main()
