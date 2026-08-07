# -*- coding: utf-8 -*-
"""K-PAST-LEARN-DETAIL-TUNE — decay 세부 스윕 (틀 win26/mix0.8 고정).

Usage:
  python tools/_k_past_learn_detail_tune.py
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KPAST_LEARN_DETAIL_TUNE.json"
OUT_MD = ROOT / "reports" / "20260808_KPAST_LEARN_DETAIL_TUNE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SEED_BASE = 42000
FUSION_SEED = 42
BASELINE_FUSION_GE3 = 0.135
LONG_DECAYS = [0.002, 0.005, 0.01]
SHORT_DECAYS = [0.02, 0.05, 0.10]
BASE = {"long_decay": 0.005, "short_decay": 0.05}


def _clear_env() -> None:
    for k in (
        "K_STAT_ENG_SHORT_WIN",
        "K_STAT_ENG_SHORT_MIX",
        "K_STAT_ENG_LONG_DECAY",
        "K_STAT_ENG_SHORT_DECAY",
        "K_STAT_ENGINE_V2",
        "K_STAT_TRANSITION_V1",
    ):
        os.environ.pop(k, None)
    os.environ["K_PAST_LEARN"] = "1"
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
    }


def _set_decay(long_d: float, short_d: float) -> None:
    _clear_env()
    os.environ["K_STAT_ENG_LONG_DECAY"] = str(long_d)
    os.environ["K_STAT_ENG_SHORT_DECAY"] = str(short_d)


def _fusion_n200() -> dict:
    from tools._k_transition_fusion_n200 import fuse_one, load_actuals

    actuals = load_actuals()
    bests = []
    t0 = time.time()
    lo, hi = 1035, 1234
    total = hi - lo + 1
    for i, dno in enumerate(range(lo, hi + 1), 1):
        random.seed(FUSION_SEED + dno)
        bests.append(fuse_one(dno, actuals[dno]))
        if i % 50 == 0 or i == total:
            print(f"  [fusion {i}/{total}] {time.time()-t0:.0f}s", flush=True)
    n = len(bests)
    ge3 = sum(1 for b in bests if b >= 3)
    ge3_rate = ge3 / n if n else 0.0
    return {
        "n": n,
        "ge3_rate": round(ge3_rate, 6),
        "ge3_count": ge3,
        "mean_hit": round(sum(bests) / n, 6) if n else 0.0,
        "hit_dist": {str(k): int(Counter(bests).get(k, 0)) for k in range(7)},
        "baseline_ge3": BASELINE_FUSION_GE3,
        "delta_vs_baseline": round(ge3_rate - BASELINE_FUSION_GE3, 6),
    }


def main() -> int:
    rows = []
    for ld in LONG_DECAYS:
        for sd in SHORT_DECAYS:
            _set_decay(ld, sd)
            tune = _solo_range(1035, 1084)
            hold = _solo_range(1085, 1134)
            # holdout 우선 점수 (과적합 방지)
            score = round(hold["ge3_rate"] * 2.0 + tune["ge3_rate"] + hold["mean_best"] * 0.01, 6)
            cell = {
                "long_decay": ld,
                "short_decay": sd,
                "tune": tune,
                "holdout": hold,
                "score": score,
            }
            rows.append(cell)
            print(
                json.dumps(
                    {
                        "ld": ld,
                        "sd": sd,
                        "tune_ge3": tune["ge3_rate"],
                        "hold_ge3": hold["ge3_rate"],
                        "score": score,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    def is_base(r: dict) -> bool:
        return abs(r["long_decay"] - BASE["long_decay"]) < 1e-12 and abs(
            r["short_decay"] - BASE["short_decay"]
        ) < 1e-12

    base = next(r for r in rows if is_base(r))

    def key(r: dict):
        return (
            r["holdout"]["ge3_rate"],
            r["tune"]["ge3_rate"],
            r["holdout"]["mean_best"],
            r["tune"]["mean_best"],
            1 if is_base(r) else 0,
        )

    best = max(rows, key=key)
    improve = key(best)[:4] > key(base)[:4]
    action = "KEEP_BASE" if (is_base(best) or not improve) else "CANDIDATE"

    fusion_base = None
    fusion_best = None
    print("[fusion] base frame decay", flush=True)
    _set_decay(BASE["long_decay"], BASE["short_decay"])
    fusion_base = _fusion_n200()
    if action == "CANDIDATE":
        print("[fusion] candidate", best["long_decay"], best["short_decay"], flush=True)
        _set_decay(best["long_decay"], best["short_decay"])
        fusion_best = _fusion_n200()
        if fusion_best["ge3_rate"] + 1e-12 < fusion_base["ge3_rate"]:
            action = "CANDIDATE_FUSION_HOLD"  # solo↑ but fusion↓ → 적용 보류 권고
    else:
        fusion_best = fusion_base

    _clear_env()

    payload = {
        "id": "K-PAST-LEARN-DETAIL-TUNE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": action,
        "frame_fixed": {"short_win": 26, "short_mix": 0.8},
        "seed_mode": f"random.seed({SEED_BASE}+draw_no)",
        "grid": {"long_decay": LONG_DECAYS, "short_decay": SHORT_DECAYS},
        "base_cell": {
            "long_decay": BASE["long_decay"],
            "short_decay": BASE["short_decay"],
            "tune_ge3": base["tune"]["ge3_rate"],
            "hold_ge3": base["holdout"]["ge3_rate"],
            "score": base["score"],
        },
        "best": {
            "long_decay": best["long_decay"],
            "short_decay": best["short_decay"],
            "tune_ge3": best["tune"]["ge3_rate"],
            "hold_ge3": best["holdout"]["ge3_rate"],
            "tune_mean": best["tune"]["mean_best"],
            "hold_mean": best["holdout"]["mean_best"],
            "score": best["score"],
            "action": action,
            "note": "상수 미적용 · 적용은 형 GO",
        },
        "fusion_base": fusion_base,
        "fusion_best": fusion_best,
        "applied": False,
        "rows": rows,
        "env_keys": ["K_STAT_ENG_LONG_DECAY", "K_STAT_ENG_SHORT_DECAY"],
        "tool": "tools/_k_past_learn_detail_tune.py",
        "prior": "docs/benchmarks/20260808_KPAST_LEARN_FRAME_DONE.json",
        "beginner": {
            "decay": "옛날 회차를 얼마나 빨리 잊을지(클수록 최근만 봄)",
            "done": "9칸 시험 · 후보는 보고만",
            "next": "형 GO면 상수 적용 + 재검증",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    top = sorted(rows, key=key, reverse=True)[:5]
    lines = [
        "# K-PAST-LEARN-DETAIL-TUNE — decay 세부 (2026-08-08)",
        "",
        f"- **판정:** `{action}`",
        f"- 틀 고정: win**26** / mix**0.8**",
        f"- base decay L**{BASE['long_decay']}**/S**{BASE['short_decay']}** · tune_ge3=**{base['tune']['ge3_rate']}** hold_ge3=**{base['holdout']['ge3_rate']}**",
        f"- 최적: L**{best['long_decay']}**/S**{best['short_decay']}** · tune=**{best['tune']['ge3_rate']}** hold=**{best['holdout']['ge3_rate']}**",
        f"- fusion base ge3=**{fusion_base['ge3_rate']}** · best ge3=**{fusion_best['ge3_rate']}**",
        f"- applied=`False`",
        "",
        "## 초보용",
        "",
        "- decay = 과거를 잊는 속도. 숫자↑ → 최근만 더 봄",
        "- 이번엔 **시험만**. 코드 기본값은 아직 안 바꿈",
        "",
        "## Top5 (hold→tune)",
        "",
        "| L | S | tune_ge3 | hold_ge3 | score |",
        "|---|---|----------|----------|-------|",
    ]
    for r in top:
        lines.append(
            f"| {r['long_decay']} | {r['short_decay']} | {r['tune']['ge3_rate']} | {r['holdout']['ge3_rate']} | {r['score']} |"
        )
    lines += ["", f"- tool: `{payload['tool']}`", ""]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {"verdict": action, "best": payload["best"], "fusion_best": fusion_best["ge3_rate"]},
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
