# -*- coding: utf-8 -*-
"""K-PAST-LEARN-TUNE-SOFT — SOFT_WEIGHT / SOFT_CONF_CAP solo n50 스윕.

Usage:
  python tools/_k_past_learn_tune_soft.py
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KPAST_LEARN_TUNE_SOFT.json"
OUT_MD = ROOT / "reports" / "20260808_KPAST_LEARN_TUNE_SOFT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

# WIRE 당시 unseeded 참고값 (셀 비교 SSOT는 스윕 내 base cell)
WIRE_BASELINE_REF = {
    "SOFT_WEIGHT": 0.12,
    "SOFT_CONF_CAP": 3.0,
    "ge3_rate": 0.14,
    "mean_best": 1.58,
    "note": "unseeded · K-PAST-LEARN-WIRE",
}
WEIGHTS = [0.0, 0.06, 0.12, 0.18, 0.24]
CAPS = [1.5, 3.0, 5.0]
SEED_BASE = 42000


def _solo_n50() -> dict:
    from app.testlotto.brains.stat_brain.predict import run
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    actuals = {}
    for r in conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1035 AND 1084"
    ):
        d = dict(r)
        actuals[int(d["draw_no"])] = {int(d[f"num{k}"]) for k in range(1, 7)}
    conn.close()
    bests = []
    for dno in range(1035, 1085):
        # engine.generate 내부 random.choices — 셀 간 공정비교용 (동결코드 미수정)
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
        "n": n,
        "mean_best": round(sum(bests) / n, 6) if n else 0.0,
        "ge3_rate": round(ge3 / n, 6) if n else 0.0,
        "ge3_count": ge3,
    }


def _run_cell(w: float, cap: float) -> dict:
    os.environ["K_PAST_LEARN"] = "1"
    os.environ["K_PAST_LEARN_ASSOC"] = "0"
    os.environ.pop("K_STAT_TRANSITION_V1", None)
    os.environ["K_PAST_LEARN_SOFT_WEIGHT"] = str(w)
    os.environ["K_PAST_LEARN_SOFT_CAP"] = str(cap)
    # drop cached modules that might pin old constants — past_learn reads env each call
    m = _solo_n50()
    return {
        "SOFT_WEIGHT": w,
        "SOFT_CONF_CAP": cap,
        "mean_best": m["mean_best"],
        "ge3_rate": m["ge3_rate"],
        "ge3_count": m["ge3_count"],
    }


def _annotate_deltas(rows: list[dict], base: dict) -> list[dict]:
    out = []
    for r in rows:
        nr = dict(r)
        nr["delta_ge3_vs_base"] = round(r["ge3_rate"] - base["ge3_rate"], 6)
        nr["delta_mean_vs_base"] = round(r["mean_best"] - base["mean_best"], 6)
        out.append(nr)
    return out


def _pick_best(rows: list[dict], base: dict) -> dict:
    """ge3 우선 · 동률 시 mean_best · 동률 시 base(0.12/3.0) 선호."""

    def key(r: dict):
        is_base = abs(r["SOFT_WEIGHT"] - 0.12) < 1e-9 and abs(r["SOFT_CONF_CAP"] - 3.0) < 1e-9
        return (r["ge3_rate"], r["mean_best"], 1 if is_base else 0)

    best = max(rows, key=key)
    keep_base = abs(best["SOFT_WEIGHT"] - 0.12) < 1e-9 and abs(best["SOFT_CONF_CAP"] - 3.0) < 1e-9
    improve = (best["ge3_rate"] > base["ge3_rate"]) or (
        best["ge3_rate"] == base["ge3_rate"] and best["mean_best"] > base["mean_best"]
    )
    return {
        "SOFT_WEIGHT": best["SOFT_WEIGHT"],
        "SOFT_CONF_CAP": best["SOFT_CONF_CAP"],
        "ge3_rate": best["ge3_rate"],
        "mean_best": best["mean_best"],
        "delta_ge3_vs_base": best["delta_ge3_vs_base"],
        "delta_mean_vs_base": best["delta_mean_vs_base"],
        "action": "KEEP_BASE" if (keep_base or not improve) else "CANDIDATE",
        "note": "시드고정 n50 · 상수적용·fusion n200은 형 GO · ASSOC OFF",
        "seed_mode": f"random.seed({SEED_BASE}+draw_no)",
    }


def main() -> int:
    for k in ("K_PAST_LEARN_ASSOC", "K_STAT_TRANSITION_V1"):
        os.environ.pop(k, None)
    os.environ["K_PAST_LEARN_ASSOC"] = "0"

    rows = []
    for w in WEIGHTS:
        for cap in CAPS:
            cell = _run_cell(w, cap)
            rows.append(cell)
            print(
                json.dumps(
                    {"w": w, "cap": cap, "ge3": cell["ge3_rate"], "mean": cell["mean_best"]},
                    ensure_ascii=False,
                ),
                flush=True,
            )

    # restore default env knobs after sweep
    os.environ.pop("K_PAST_LEARN_SOFT_WEIGHT", None)
    os.environ.pop("K_PAST_LEARN_SOFT_CAP", None)

    base_cell = next(
        r for r in rows if abs(r["SOFT_WEIGHT"] - 0.12) < 1e-9 and abs(r["SOFT_CONF_CAP"] - 3.0) < 1e-9
    )
    rows = _annotate_deltas(rows, base_cell)
    best = _pick_best(rows, base_cell)
    applied = False  # 형 GO 전 상수 미적용

    payload = {
        "id": "K-PAST-LEARN-TUNE-SOFT",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": best["action"],
        "wire_baseline_ref": WIRE_BASELINE_REF,
        "seeded_base_cell": {
            "SOFT_WEIGHT": 0.12,
            "SOFT_CONF_CAP": 3.0,
            "ge3_rate": base_cell["ge3_rate"],
            "mean_best": base_cell["mean_best"],
            "seed_mode": f"random.seed({SEED_BASE}+draw_no)",
        },
        "grid": {"SOFT_WEIGHT": WEIGHTS, "SOFT_CONF_CAP": CAPS},
        "n_cells": len(rows),
        "draw_range": [1035, 1084],
        "assoc": False,
        "rows": rows,
        "best": best,
        "applied_to_past_learn": applied,
        "forbid": ["fusion n200 without 형 GO", "ASSOC ON default", "engine random.choices 수정"],
        "tool": "tools/_k_past_learn_tune_soft.py",
        "prior": "docs/benchmarks/20260808_KPAST_LEARN_WIRE.json",
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # top5 table
    top = sorted(rows, key=lambda r: (r["ge3_rate"], r["mean_best"]), reverse=True)[:5]
    lines = [
        "# K-PAST-LEARN-TUNE-SOFT — SOFT 스윕 (2026-08-08)",
        "",
        f"- **판정:** `{best['action']}`",
        f"- 시드고정 base(w0.12/cap3.0): ge3=**{base_cell['ge3_rate']}** mean=**{base_cell['mean_best']}**",
        f"- WIRE참고(unseeded): ge3={WIRE_BASELINE_REF['ge3_rate']} mean={WIRE_BASELINE_REF['mean_best']}",
        f"- 최적후보: w=**{best['SOFT_WEIGHT']}** cap=**{best['SOFT_CONF_CAP']}** · ge3=**{best['ge3_rate']}** mean=**{best['mean_best']}**",
        f"- Δge3=**{best['delta_ge3_vs_base']}** · Δmean=**{best['delta_mean_vs_base']}** (vs 시드고정 base)",
        f"- applied=`{applied}` · ASSOC OFF · 상수적용·fusion n200 = 형 GO",
        "",
        "## Top5 (ge3→mean)",
        "",
        "| w | cap | ge3 | mean | Δge3 |",
        "|---|-----|-----|------|------|",
    ]
    for r in top:
        lines.append(
            f"| {r['SOFT_WEIGHT']} | {r['SOFT_CONF_CAP']} | {r['ge3_rate']} | {r['mean_best']} | {r['delta_ge3_vs_base']} |"
        )
    lines += ["", f"- tool: `{payload['tool']}`", ""]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": best["action"], "best": best, "applied": applied}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
