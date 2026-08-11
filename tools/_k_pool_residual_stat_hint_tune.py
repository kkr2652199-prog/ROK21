# -*- coding: utf-8 -*-
"""K-POOL-RESIDUAL-STAT-HINT — 단계②b stat pool hit 잔여.

노브: HINT_WEIGHT_BY_BRAIN['stat'] (base=0.15) — pick_score→diversify 영향.
축: pool best |∩actual|/6 ↑ · |Δ|≥0.005 · markov prefer / review prize iso.
ge3미사용. SCORE/BLEND 불변.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KPOOL_RESIDUAL_STAT_HINT.json"
OUT_MD = ROOT / "reports" / "20260812_KPOOL_RESIDUAL_STAT_HINT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80
ABS_THR = 0.005
ISO_THR = 0.005
BASE_W = 0.15
CANDS = [0.0, 0.15, 0.30, 0.45]


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _patch(w: float):
    from app.testlotto.brains.shared import aux_hint as ah
    from app.testlotto.brains.stat_brain import predict as st

    saved_by = dict(ah.HINT_WEIGHT_BY_BRAIN)
    saved_st = float(st.HINT_WEIGHT)
    ah.HINT_WEIGHT_BY_BRAIN["stat"] = float(w)
    st.HINT_WEIGHT = float(w)

    def restore() -> None:
        ah.HINT_WEIGHT_BY_BRAIN.clear()
        ah.HINT_WEIGHT_BY_BRAIN.update(saved_by)
        st.HINT_WEIGHT = saved_st

    return restore


def _run(seed: int, w: float) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy

    restore = _patch(w)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer: list[float] = []
        prize: list[float] = []
        hits: list[float] = []
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
            ssets = [[int(x) for x in c["nums"]] for c in pool_br.get("stat", [])]
            act = _actual(dno)
            if ssets:
                hits.append(max(len(set(s) & act) for s in ssets) / 6.0)
            learner.update_from_pool(pool_br, act)
        return {
            "seed": seed,
            "n": len(hits),
            "prefer": round(mean(prefer), 6) if prefer else None,
            "prize": round(mean(prize), 6) if prize else None,
            "stat_hit": round(mean(hits), 6) if hits else None,
        }
    finally:
        restore()


def _agg(w: float, by: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    hit = mean(d["stat_hit"] for d in by if d["stat_hit"] is not None)
    if base is None:
        return {
            "w": w,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "stat_hit": round(hit, 6),
            "gate_pass": True,
            "gate_detail": {"is_baseline": True},
            "per_seed": by,
        }
    dhit = hit - base["stat_hit"]
    detail = {
        "improve": dhit >= ABS_THR,
        "prefer_iso": abs(prefer - base["prefer"]) < ISO_THR,
        "prize_iso": abs(prize - base["prize"]) < ISO_THR,
        "dhit": round(dhit, 6),
    }
    return {
        "w": w,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "stat_hit": round(hit, 6),
        "gate_pass": all(detail[k] for k in ("improve", "prefer_iso", "prize_iso")),
        "gate_detail": detail,
        "per_seed": by,
    }


def _apply(w: float) -> None:
    path = ROOT / "app" / "testlotto" / "brains" / "shared" / "aux_hint.py"
    text = path.read_text(encoding="utf-8")
    text2, n = re.subn(
        r'(HINT_WEIGHT_BY_BRAIN: dict\[str, float\] = \{[^}]*"stat": )([0-9.]+)',
        rf"\g<1>{w}",
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError("HINT_WEIGHT_BY_BRAIN stat replace failed")
    path.write_text(text2, encoding="utf-8")
    from app.testlotto.brains.shared import aux_hint as ah
    from app.testlotto.brains.stat_brain import predict as st

    ah.HINT_WEIGHT_BY_BRAIN["stat"] = float(w)
    st.HINT_WEIGHT = float(w)


def main() -> None:
    from app.testlotto.brains.shared import aux_hint as ah

    results: list[dict] = []
    print(f"== stat HINT_WEIGHT base={BASE_W} ==", flush=True)
    base_rows = [_run(s, BASE_W) for s in SEEDS]
    base = _agg(BASE_W, base_rows, None)
    results.append(base)
    for w in CANDS:
        if abs(w - BASE_W) < 1e-12:
            continue
        print(f"  run stat hint_w={w} ...", flush=True)
        rows = [_run(s, w) for s in SEEDS]
        results.append(
            _agg(
                w,
                rows,
                {
                    "prefer": base["prefer"],
                    "prize": base["prize"],
                    "stat_hit": base["stat_hit"],
                },
            )
        )

    passers = [r for r in results if r["gate_pass"] and abs(r["w"] - BASE_W) > 1e-12]
    best = max(passers, key=lambda r: r["stat_hit"]) if passers else None
    chosen = float(best["w"]) if best else BASE_W
    if best:
        _apply(chosen)
        verdict = "APPLY"
    else:
        verdict = "NO_IMPROVE_HOLD"

    out = {
        "id": "K-POOL-RESIDUAL-STAT-HINT",
        "ts": _now(),
        "range": [LO, HI],
        "seeds": SEEDS,
        "base_w": BASE_W,
        "cands": CANDS,
        "live_before": dict(ah.HINT_WEIGHT_BY_BRAIN),
        "results": results,
        "chosen": chosen,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "step": "2b",
        "note": "양산前 · pool축 · SCORE미사용(풀생성무관) · 1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-POOL-RESIDUAL-STAT-HINT",
        "",
        f"시각: {out['ts']} · 단계②b · {LO}~{HI} · seeds={SEEDS}",
        "",
        f"## 판정 **{verdict}** · chosen stat HINT_WEIGHT=`{chosen}`",
        "",
        "| w | prefer | prize | hit | gate |",
        "|---|--------|-------|-----|------|",
    ]
    for r in results:
        lines.append(
            f"| {r['w']} | {r.get('prefer')} | {r.get('prize')} | {r.get('stat_hit')} | {r['gate_pass']} |"
        )
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print("VERDICT", verdict, "chosen", chosen, flush=True)
    print("WROTE", OUT_JSON, flush=True)


if __name__ == "__main__":
    main()
