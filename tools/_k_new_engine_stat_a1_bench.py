# -*- coding: utf-8 -*-
"""K-NEW-ENGINE-STAT-A1 — stat_brain engine v2 dual-window + cycle gap bench (READ-ONLY).

Compare baseline (ENGINE_V2=False) vs v2 (K_STAT_ENGINE_V2=1) on stat solo path.
seed=42 · n=200 · draw 1035~1234 · stat_brain.predict.run(draws, n_sets=5)

Gate: v2 ge3 >= baseline_solo OR (delta >= +0.01 AND p_vs_null < 0.15)
  baseline_solo reference: 0.1125 (document actual baseline from run)
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.stat_brain import engine as stat_engine  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from app.testlotto.tier_utils import pick_best_set_index, score_predicted_set  # noqa: E402
from tools.bench_quick_gate import NULL_GE3  # noqa: E402

SEED = 42
N_EVAL = 200
DRAW_START = 1035
DRAW_END = 1234
N_SETS = 5
OUT = ROOT / "docs" / "benchmarks" / "20260801_KNEW_ENGINE_STAT_A1.json"
BASELINE_SOLO_REF = 0.1125
DELTA_MIN = 0.01
P_MAX = 0.15


def _best_match(sets: list[dict], actual_nums: list[int], bonus: int) -> int:
    if not sets:
        return 0
    scored = [score_predicted_set(s.get("nums") or [], actual_nums, bonus) for s in sets]
    best_idx = pick_best_set_index(scored)
    return int(scored[best_idx]["matched_count"])


def _walkforward(use_v2: bool) -> dict[str, Any]:
    stat_engine.ENGINE_V2 = use_v2
    if use_v2:
        os.environ["K_STAT_ENGINE_V2"] = "1"
    else:
        os.environ.pop("K_STAT_ENGINE_V2", None)

    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    if len(rows) > N_EVAL:
        rows = rows[-N_EVAL:]

    matches: list[int] = []
    ge3_count = 0

    for row in rows:
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual_nums = sorted(int(row[f"num{k}"]) for k in range(1, 7))
        bonus = int(row.get("bonus") or 0)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        random.seed(SEED)
        sets = stat_predict.run(draws, N_SETS)
        mc = _best_match(sets, actual_nums, bonus)
        matches.append(mc)
        if mc >= 3:
            ge3_count += 1

    n = len(matches)
    ge3_rate = ge3_count / n if n else 0.0
    mean_match = sum(matches) / n if n else 0.0
    p_null = float(binomtest(ge3_count, n, NULL_GE3, alternative="greater").pvalue) if n else 1.0

    return {
        "engine_v2": use_v2,
        "n_eval": n,
        "ge3_count": ge3_count,
        "ge3_rate": round(ge3_rate, 6),
        "mean_match": round(mean_match, 6),
        "p_vs_null": round(p_null, 6),
        "null_ge3": NULL_GE3,
    }


def run_bench() -> dict[str, Any]:
    random.seed(SEED)
    baseline = _walkforward(use_v2=False)
    v2 = _walkforward(use_v2=True)

    # restore production default
    stat_engine.ENGINE_V2 = False
    os.environ.pop("K_STAT_ENGINE_V2", None)

    delta_ge3 = round(v2["ge3_rate"] - baseline["ge3_rate"], 6)
    gate_a = v2["ge3_rate"] >= baseline["ge3_rate"]
    gate_b = delta_ge3 >= DELTA_MIN and v2["p_vs_null"] < P_MAX
    passed = gate_a or gate_b

    return {
        "id": "K-NEW-ENGINE-STAT-A1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "path": "stat_brain.predict.run solo (n_sets=5)",
        "baseline": baseline,
        "v2": v2,
        "comparison": {
            "delta_ge3": delta_ge3,
            "baseline_solo_ref": BASELINE_SOLO_REF,
            "gate_a_v2_ge3_gte_baseline": gate_a,
            "gate_b_delta_ge3_gte_0.01_and_p_lt_0.15": gate_b,
        },
        "gate": {
            "rule": "v2 ge3 >= baseline_solo OR (delta >= +0.01 AND p_vs_null < 0.15)",
            "delta_min": DELTA_MIN,
            "p_max": P_MAX,
        },
        "verdict": "PASS" if passed else "FAIL",
        "pass": passed,
    }


def main() -> int:
    result = run_bench()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
