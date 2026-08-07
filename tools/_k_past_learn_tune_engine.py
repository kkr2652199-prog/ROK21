# -*- coding: utf-8 -*-
"""K-PAST-LEARN-TUNE-ENGINE — engine v2 윈도우/가중 시드고정 solo n50 스윕.

Usage:
  python tools/_k_past_learn_tune_engine.py
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KPAST_LEARN_TUNE_ENGINE.json"
OUT_MD = ROOT / "reports" / "20260808_KPAST_LEARN_TUNE_ENGINE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SEED_BASE = 42000
SHORT_WINS = [26, 52, 78]
SHORT_MIXES = [0.4, 0.6, 0.8]
# base cell = current defaults
BASE = {"short_win": 52, "short_mix": 0.6, "engine_v2": True}


def _clear_eng_env() -> None:
    for k in (
        "K_STAT_ENG_SHORT_WIN",
        "K_STAT_ENG_SHORT_MIX",
        "K_STAT_ENG_LONG_DECAY",
        "K_STAT_ENG_SHORT_DECAY",
        "K_STAT_ENGINE_V2",
    ):
        os.environ.pop(k, None)


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


def _run_cell(*, engine_v2: bool, short_win: int, short_mix: float) -> dict:
    os.environ["K_PAST_LEARN"] = "1"
    os.environ["K_PAST_LEARN_ASSOC"] = "0"
    os.environ.pop("K_STAT_TRANSITION_V1", None)
    if engine_v2:
        os.environ["K_STAT_ENGINE_V2"] = "1"
        os.environ["K_STAT_ENG_SHORT_WIN"] = str(short_win)
        os.environ["K_STAT_ENG_SHORT_MIX"] = str(short_mix)
    else:
        os.environ["K_STAT_ENGINE_V2"] = "0"
        os.environ.pop("K_STAT_ENG_SHORT_WIN", None)
        os.environ.pop("K_STAT_ENG_SHORT_MIX", None)
    m = _solo_n50()
    return {
        "engine_v2": engine_v2,
        "short_win": short_win if engine_v2 else None,
        "short_mix": short_mix if engine_v2 else None,
        "mean_best": m["mean_best"],
        "ge3_rate": m["ge3_rate"],
        "ge3_count": m["ge3_count"],
    }


def main() -> int:
    _clear_eng_env()
    os.environ["K_PAST_LEARN_ASSOC"] = "0"

    rows: list[dict] = []
    # v1 control
    cell = _run_cell(engine_v2=False, short_win=52, short_mix=0.6)
    rows.append(cell)
    print(json.dumps({"label": "v1", **{k: cell[k] for k in ("ge3_rate", "mean_best")}}, ensure_ascii=False), flush=True)

    for win in SHORT_WINS:
        for mix in SHORT_MIXES:
            cell = _run_cell(engine_v2=True, short_win=win, short_mix=mix)
            rows.append(cell)
            print(
                json.dumps(
                    {"win": win, "mix": mix, "ge3": cell["ge3_rate"], "mean": cell["mean_best"]},
                    ensure_ascii=False,
                ),
                flush=True,
            )

    base = next(
        r
        for r in rows
        if r["engine_v2"]
        and r["short_win"] == BASE["short_win"]
        and abs(float(r["short_mix"]) - BASE["short_mix"]) < 1e-9
    )
    for r in rows:
        r["delta_ge3_vs_base"] = round(r["ge3_rate"] - base["ge3_rate"], 6)
        r["delta_mean_vs_base"] = round(r["mean_best"] - base["mean_best"], 6)

    def key(r: dict):
        is_base = (
            r["engine_v2"]
            and r["short_win"] == 52
            and r["short_mix"] is not None
            and abs(float(r["short_mix"]) - 0.6) < 1e-9
        )
        return (r["ge3_rate"], r["mean_best"], 1 if is_base else 0)

    best = max(rows, key=key)
    improve = best["ge3_rate"] > base["ge3_rate"] or (
        best["ge3_rate"] == base["ge3_rate"] and best["mean_best"] > base["mean_best"]
    )
    is_base = (
        best["engine_v2"]
        and best["short_win"] == 52
        and best["short_mix"] is not None
        and abs(float(best["short_mix"]) - 0.6) < 1e-9
    )
    action = "KEEP_BASE" if (is_base or not improve) else "CANDIDATE"

    _clear_eng_env()

    payload = {
        "id": "K-PAST-LEARN-TUNE-ENGINE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": action,
        "seed_mode": f"random.seed({SEED_BASE}+draw_no)",
        "base_cell": {
            "engine_v2": True,
            "short_win": 52,
            "short_mix": 0.6,
            "ge3_rate": base["ge3_rate"],
            "mean_best": base["mean_best"],
        },
        "grid": {"short_win": SHORT_WINS, "short_mix": SHORT_MIXES, "plus": "v1_control"},
        "n_cells": len(rows),
        "draw_range": [1035, 1084],
        "assoc": False,
        "rows": rows,
        "best": {
            "engine_v2": best["engine_v2"],
            "short_win": best["short_win"],
            "short_mix": best["short_mix"],
            "ge3_rate": best["ge3_rate"],
            "mean_best": best["mean_best"],
            "delta_ge3_vs_base": best["delta_ge3_vs_base"],
            "delta_mean_vs_base": best["delta_mean_vs_base"],
            "action": action,
            "note": "상수 적용·fusion n200은 형 GO · random.choices 동결",
        },
        "applied_to_engine": False,
        "env_keys": [
            "K_STAT_ENGINE_V2",
            "K_STAT_ENG_SHORT_WIN",
            "K_STAT_ENG_SHORT_MIX",
            "K_STAT_ENG_LONG_DECAY",
            "K_STAT_ENG_SHORT_DECAY",
        ],
        "forbid": ["random.choices edit", "fusion n200 without 형 GO", "ASSOC ON"],
        "tool": "tools/_k_past_learn_tune_engine.py",
        "prior": "docs/benchmarks/20260808_KPAST_LEARN_TUNE_SOFT.json",
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    top = sorted(rows, key=lambda r: (r["ge3_rate"], r["mean_best"]), reverse=True)[:6]
    lines = [
        "# K-PAST-LEARN-TUNE-ENGINE — engine v2 스윕 (2026-08-08)",
        "",
        f"- **판정:** `{action}`",
        f"- 시드고정 base(v2 win52/mix0.6): ge3=**{base['ge3_rate']}** mean=**{base['mean_best']}**",
        f"- 최적: v2=`{best['engine_v2']}` win=`{best['short_win']}` mix=`{best['short_mix']}` · ge3=**{best['ge3_rate']}** mean=**{best['mean_best']}**",
        f"- Δge3=**{best['delta_ge3_vs_base']}** · Δmean=**{best['delta_mean_vs_base']}**",
        f"- applied=False · ASSOC OFF · `random.choices` 미수정",
        "",
        "## Top6",
        "",
        "| v2 | win | mix | ge3 | mean | Δge3 |",
        "|----|-----|-----|-----|------|------|",
    ]
    for r in top:
        lines.append(
            f"| {r['engine_v2']} | {r['short_win']} | {r['short_mix']} | {r['ge3_rate']} | {r['mean_best']} | {r['delta_ge3_vs_base']} |"
        )
    lines += ["", f"- tool: `{payload['tool']}`", ""]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": action, "best": payload["best"]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
