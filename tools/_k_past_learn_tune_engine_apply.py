# -*- coding: utf-8 -*-
"""K-PAST-LEARN-TUNE-ENGINE-APPLY — 후보 상수 적용 + 시드 n50 + holdout + fusion n200.

Usage:
  python tools/_k_past_learn_tune_engine_apply.py
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KPAST_LEARN_TUNE_ENGINE_APPLY.json"
OUT_MD = ROOT / "reports" / "20260808_KPAST_LEARN_TUNE_ENGINE_APPLY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SEED_BASE = 42000
FUSION_SEED = 42
BASELINE_FUSION_GE3 = 0.135
EXPECT_TUNE = {"ge3_rate": 0.28, "mean_best": 1.88, "range": [1035, 1084]}


def _clear_override_env() -> None:
    for k in (
        "K_STAT_ENG_SHORT_WIN",
        "K_STAT_ENG_SHORT_MIX",
        "K_STAT_ENG_LONG_DECAY",
        "K_STAT_ENG_SHORT_DECAY",
        "K_STAT_ENGINE_V2",
        "K_PAST_LEARN_ASSOC",
        "K_STAT_TRANSITION_V1",
    ):
        os.environ.pop(k, None)
    os.environ["K_PAST_LEARN_ASSOC"] = "0"


def _solo_range(lo: int, hi: int) -> dict:
    from app.testlotto.brains.stat_brain.predict import run
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    actuals = {}
    for r in conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ?",
        (lo, hi),
    ):
        d = dict(r)
        actuals[int(d["draw_no"])] = {int(d[f"num{k}"]) for k in range(1, 7)}
    conn.close()
    bests = []
    for dno in range(lo, hi + 1):
        random.seed(SEED_BASE + dno)
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        sets = run(draws, 5)
        act = actuals[dno]
        best = max(len(set(s["nums"]) & act) for s in sets) if sets else 0
        bests.append(best)
    n = len(bests)
    ge3 = sum(1 for b in bests if b >= 3)
    return {
        "draw_range": [lo, hi],
        "n": n,
        "mean_best": round(sum(bests) / n, 6) if n else 0.0,
        "ge3_rate": round(ge3 / n, 6) if n else 0.0,
        "ge3_count": ge3,
        "seed_mode": f"random.seed({SEED_BASE}+draw_no)",
    }


def _fusion_n200() -> dict:
    """in-memory coordinator · transition OFF 상태 그대로."""
    from tools._k_transition_fusion_n200 import fuse_one, load_actuals

    actuals = load_actuals()
    bests = []
    t0 = time.time()
    lo, hi = 1035, 1234
    total = hi - lo + 1
    for i, dno in enumerate(range(lo, hi + 1), 1):
        random.seed(FUSION_SEED + dno)
        best = fuse_one(dno, actuals[dno])
        bests.append(best)
        if i % 50 == 0 or i == total:
            print(f"  [fusion {i}/{total}] elapsed={time.time()-t0:.0f}s", flush=True)
    n = len(bests)
    ge3 = sum(1 for b in bests if b >= 3)
    ge3_rate = ge3 / n if n else 0.0
    return {
        "draw_range": [lo, hi],
        "n": n,
        "mean_hit": round(sum(bests) / n, 6) if n else 0.0,
        "ge3_rate": round(ge3_rate, 6),
        "ge3_count": ge3,
        "hit_dist": {str(k): int(Counter(bests).get(k, 0)) for k in range(7)},
        "baseline_ge3": BASELINE_FUSION_GE3,
        "delta_vs_baseline": round(ge3_rate - BASELINE_FUSION_GE3, 6),
        "seed": FUSION_SEED,
        "path": "in-memory coordinator · no DB write",
    }


def main() -> int:
    _clear_override_env()
    from app.testlotto.brains.stat_brain import engine, past_learn, transition_v1

    params = engine.v2_params()
    flags = {
        "V2_SHORT_WIN": engine.V2_SHORT_WIN,
        "V2_SHORT_MIX": engine.V2_SHORT_MIX,
        "v2_params": params,
        "past_learn_engine_v2": past_learn.use_engine_v2(),
        "TRANSITION_V1_WIRE": bool(transition_v1.TRANSITION_V1_WIRE),
        "assoc": past_learn.assoc_hint_on(),
    }
    apply_ok = (
        engine.V2_SHORT_WIN == 26
        and abs(engine.V2_SHORT_MIX - 0.8) < 1e-9
        and int(params["short_win"]) == 26
        and abs(float(params["short_mix"]) - 0.8) < 1e-9
        and past_learn.use_engine_v2()
        and not transition_v1.TRANSITION_V1_WIRE
        and not past_learn.assoc_hint_on()
    )
    print("[1] flags", flags, "apply_ok", apply_ok, flush=True)

    print("[2] tune-window solo n50", flush=True)
    tune = _solo_range(1035, 1084)
    print(tune, flush=True)

    print("[3] holdout solo n50 1085-1134", flush=True)
    hold = _solo_range(1085, 1134)
    print(hold, flush=True)

    print("[4] fusion n200", flush=True)
    fusion = _fusion_n200()
    print(
        {"ge3": fusion["ge3_rate"], "mean": fusion["mean_hit"], "d": fusion["delta_vs_baseline"]},
        flush=True,
    )

    tune_match = (
        abs(tune["ge3_rate"] - EXPECT_TUNE["ge3_rate"]) < 1e-9
        and abs(tune["mean_best"] - EXPECT_TUNE["mean_best"]) < 1e-9
    )
    # fusion: 악화 시 ROLLBACK 권고
    fusion_ok = fusion["ge3_rate"] >= BASELINE_FUSION_GE3 - 1e-9
    if not apply_ok:
        verdict = "FAIL_APPLY"
    elif not tune_match:
        verdict = "FAIL_REPRO"
    elif not fusion_ok:
        verdict = "ROLLBACK_REC"  # 상수 유지하되 fusion 악화 보고
    else:
        verdict = "PASS"

    payload = {
        "id": "K-PAST-LEARN-TUNE-ENGINE-APPLY",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "applied": {
            "V2_SHORT_WIN": 26,
            "V2_SHORT_MIX": 0.8,
            "prev": {"V2_SHORT_WIN": 52, "V2_SHORT_MIX": 0.6},
            "module": "app/testlotto/brains/stat_brain/engine.py",
        },
        "flags": flags,
        "apply_ok": apply_ok,
        "tune_window": tune,
        "tune_match_candidate": tune_match,
        "holdout_n50": hold,
        "fusion_n200": fusion,
        "rollback": "V2_SHORT_WIN=52 · V2_SHORT_MIX=0.6",
        "forbid": ["random.choices edit", "ASSOC ON"],
        "tool": "tools/_k_past_learn_tune_engine_apply.py",
        "prior": "docs/benchmarks/20260808_KPAST_LEARN_TUNE_ENGINE.json",
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# K-PAST-LEARN-TUNE-ENGINE-APPLY (2026-08-08)",
        "",
        f"- **판정:** `{verdict}`",
        f"- 적용: V2_SHORT_WIN=**26** · V2_SHORT_MIX=**0.8** (prev 52/0.6)",
        f"- tune n50: ge3=**{tune['ge3_rate']}** mean=**{tune['mean_best']}** · match_candidate=`{tune_match}`",
        f"- holdout n50(1085~1134): ge3=**{hold['ge3_rate']}** mean=**{hold['mean_best']}**",
        f"- fusion n200: ge3=**{fusion['ge3_rate']}** mean=**{fusion['mean_hit']}** · Δbase=**{fusion['delta_vs_baseline']}**",
        f"- TRANSITION OFF · ASSOC OFF · random.choices 미수정",
        f"- 롤백: `{payload['rollback']}`",
        "",
        f"- tool: `{payload['tool']}`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "fusion_ge3": fusion["ge3_rate"]}, ensure_ascii=False), flush=True)
    return 0 if verdict in ("PASS", "ROLLBACK_REC") else 1


if __name__ == "__main__":
    raise SystemExit(main())
