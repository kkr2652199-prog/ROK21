# -*- coding: utf-8 -*-
"""K-AUX-WEIGHT-SURVEY — 4보조 AUX_WEIGHTS 13조합 live walk-forward (READ-ONLY).

매 draw_no마다 3 predict 뇌 live predict_sets + 커스텀 _aux_score_with_weights
+ apply_markov_wire_quota (MARKOV_WIRE_ENABLED=True).
coordinator.AUX_WEIGHTS 미수정 · stored pool 재사용 금지.
산출: docs/benchmarks/20260729_KAUX_WEIGHT_survey.json
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
random.seed(42)

from app.testlotto.brains import (  # noqa: E402
    aux_balance_keeper,
    aux_miss_detective,
    aux_pattern_spotlight,
    aux_referee,
    predict_flow_shaman,
    predict_review_king,
    predict_stat_fairy,
)
from app.testlotto.brains.coordinator import apply_markov_wire_quota  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

OUT = ROOT / "docs" / "benchmarks" / "20260729_KAUX_WEIGHT_survey.json"

DRAW_START = 53
DRAW_END = 1234
WIRE_PIN_GE3 = 0.1447
WIRE_PIN_MEAN = 1.7504
NULL_GE3 = 0.1137
MC_SEED = 42

PREDICT_MODULES = {
    "markov": predict_flow_shaman,
    "stat": predict_stat_fairy,
    "review": predict_review_king,
}

COMBOS: list[dict[str, Any]] = [
    {"combo_id": "A", "weights": [0.25, 0.25, 0.25, 0.25]},
    {"combo_id": "B", "weights": [0.40, 0.20, 0.20, 0.20]},
    {"combo_id": "C", "weights": [0.20, 0.40, 0.20, 0.20]},
    {"combo_id": "D", "weights": [0.20, 0.20, 0.40, 0.20]},
    {"combo_id": "E", "weights": [0.20, 0.20, 0.20, 0.40]},
    {"combo_id": "F", "weights": [0.10, 0.40, 0.40, 0.10]},
    {"combo_id": "G", "weights": [0.10, 0.30, 0.30, 0.30]},
    {"combo_id": "H", "weights": [0.40, 0.30, 0.20, 0.10]},
    {"combo_id": "I", "weights": [0.10, 0.20, 0.40, 0.30]},
    {"combo_id": "J", "weights": [0.30, 0.30, 0.30, 0.10]},
    {"combo_id": "K", "weights": [0.00, 0.40, 0.40, 0.20]},
    {"combo_id": "L", "weights": [0.40, 0.40, 0.10, 0.10]},
    {"combo_id": "M", "weights": [0.10, 0.10, 0.40, 0.40]},
]


def _aux_score_with_weights(
    candidates: list[dict],
    draws: list[dict],
    target_draw_no: int,
    weights: list[float],
) -> list[dict]:
    """coordinator._apply_aux_scoring 재현 — weights 파라미터화."""
    from app.testlotto.learn_state import get_referee_weights

    aux_modules = [
        aux_miss_detective,
        aux_pattern_spotlight,
        aux_balance_keeper,
        aux_referee,
    ]
    ref_weights = get_referee_weights()
    out: list[dict] = []
    for c in candidates:
        tag = c.get("brain_tag", "") or None
        aux_score = sum(
            w * mod.score_set(c["nums"], draws, target_draw_no, brain_tag=tag)
            for mod, w in zip(aux_modules, weights)
        )
        base = float(c.get("confidence", 60))
        brain_w = ref_weights.get(c.get("brain_tag", ""), 1.0 / 3)
        final_conf = min(99.5, base * 0.5 * brain_w + aux_score * 40 + base * 0.1)
        out.append({**c, "confidence": round(final_conf, 1)})
    return out


def summarize_bests(bests: list[int]) -> dict[str, Any]:
    n = len(bests)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3_rate": 0.0, "ge4_rate": 0.0, "ge3_count": 0}
    ge3_c = sum(1 for x in bests if x >= 3)
    ge4_c = sum(1 for x in bests if x >= 4)
    return {
        "n": n,
        "mean": round(sum(bests) / n, 4),
        "ge3_rate": round(ge3_c / n, 4),
        "ge4_rate": round(ge4_c / n, 4),
        "ge3_count": ge3_c,
    }


def run_walkforward() -> tuple[dict[str, list[int]], int]:
    """draw별 live candidates 1회 생성 → 조합별 scoring+quota."""
    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    combo_keys = [c["combo_id"] for c in COMBOS]
    acc: dict[str, list[int]] = {k: [] for k in combo_keys}
    total = 0

    for ri, row in enumerate(rows):
        if ri % 100 == 0:
            print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {row[f"num{k}"] for k in range(1, 7)}

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        candidates: list[dict] = []
        for tag, mod in PREDICT_MODULES.items():
            sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
            for i, s in enumerate(sets):
                sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
                candidates.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})

        if not candidates:
            continue

        for combo in COMBOS:
            cid = combo["combo_id"]
            scored = _aux_score_with_weights(candidates, draws, draw_no, combo["weights"])
            selected = apply_markov_wire_quota(scored)
            best = max((len(set(s["nums"]) & actual) for s in selected), default=0)
            acc[cid].append(best)
        total += 1

    return acc, total


def enrich_row(row: dict[str, Any]) -> dict[str, Any]:
    ge3 = float(row["ge3_rate"])
    ge3_c = int(row["ge3_count"])
    n = int(row["n"])
    p = float(binomtest(ge3_c, n, NULL_GE3, alternative="greater").pvalue) if n else 1.0
    delta = round(ge3 - WIRE_PIN_GE3, 4)
    verdict = "PASS" if ge3 > WIRE_PIN_GE3 and p < 0.05 else "FAIL"
    return {
        "combo_id": row["combo_id"],
        "weights": row["weights"],
        "ge3_rate": ge3,
        "mean": row["mean"],
        "ge4_rate": row["ge4_rate"],
        "ge3_count": ge3_c,
        "delta_ge3": delta,
        "p_value": round(p, 6),
        "verdict": verdict,
    }


def main() -> None:
    t0 = time.time()
    print(f"K-AUX-WEIGHT-SURVEY live walk-forward n_eval target={DRAW_END - DRAW_START + 1}", flush=True)
    acc, n_eval = run_walkforward()

    step2: list[dict[str, Any]] = []
    for combo in COMBOS:
        cid = combo["combo_id"]
        sm = summarize_bests(acc[cid])
        step2.append({"combo_id": cid, "weights": combo["weights"], **sm})

    step2.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))
    step3_top5 = [enrich_row(r) for r in step2[:5]]
    best_row = enrich_row(step2[0])

    baseline_sm = summarize_bests(acc["A"])
    baseline_live = {
        "weights": [0.25, 0.25, 0.25, 0.25],
        "ge3_rate": baseline_sm["ge3_rate"],
        "mean": baseline_sm["mean"],
        "ge4_rate": baseline_sm["ge4_rate"],
        "ge3_count": baseline_sm["ge3_count"],
        "delta_ge3_vs_pin": round(baseline_sm["ge3_rate"] - WIRE_PIN_GE3, 4),
        "pin_match": abs(baseline_sm["ge3_rate"] - WIRE_PIN_GE3) < 0.002,
    }

    any_gt = any(r["ge3_rate"] > WIRE_PIN_GE3 for r in step2)
    pass_gate = bool(best_row["ge3_rate"] > WIRE_PIN_GE3 and best_row["p_value"] < 0.05)

    if pass_gate:
        recommended = "K-AUX-WEIGHT-WIRE"
        verdict = (
            f"PASS: best {best_row['combo_id']} ge3={best_row['ge3_rate']} "
            f"> pin {WIRE_PIN_GE3} p={best_row['p_value']}."
        )
    else:
        recommended = "K-ATTACK-HOLD"
        verdict = (
            f"FAIL: best {best_row['combo_id']} ge3={best_row['ge3_rate']} "
            f"≤ pin {WIRE_PIN_GE3} (또는 p≥0.05). → K-ATTACK-HOLD."
        )

    out = {
        "id": "K-AUX-WEIGHT-SURVEY",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": n_eval,
        "draw_range": [DRAW_START, DRAW_END],
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "null_ge3": NULL_GE3,
        "mc_seed": MC_SEED,
        "sets_per_predict_brain": SETS_PER_PREDICT_BRAIN,
        "pipeline": "live_predict_sets + _aux_score_with_weights + apply_markov_wire_quota",
        "baseline_live": baseline_live,
        "step2_grid": step2,
        "step3_top5": step3_top5,
        "best_combo": best_row,
        "gates": {
            "any_ge3_gt_pin": any_gt,
            "best_ge3": best_row["ge3_rate"],
            "best_p": best_row["p_value"],
            "pass": pass_gate,
        },
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
        "code_touched": False,
        "coordinator_modified": False,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
