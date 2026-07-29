# -*- coding: utf-8 -*-
"""K-BENCH-02 — confidence/AUX 정렬 vs set_no_asc 쿼터 live walk-forward (READ-ONLY).

비교 축: baseline_set_no_asc · confidence_desc · aux_total_desc ·
confidence_quota · aux_quota.
coordinator·predict_* 미수정 · DB write 금지.
산출: docs/benchmarks/20260729_KBENCH_CONFIDENCE_survey.json
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

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
from app.testlotto.brains.coordinator import (  # noqa: E402
    apply_markov_wire_quota,
)
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state import get_referee_weights  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

OUT = ROOT / "docs" / "benchmarks" / "20260729_KBENCH_CONFIDENCE_survey.json"

DRAW_START = 53
DRAW_END = 1234
WIRE_PIN_GE3 = 0.1447
WIRE_PIN_MEAN = 1.7504
NULL_GE3 = 0.1137
MC_SEED = 42
TARGET_N = 5

QUOTA: dict[str, int] = {"markov": 3, "stat": 1, "review": 1}

PREDICT_MODULES = {
    "markov": predict_flow_shaman,
    "stat": predict_stat_fairy,
    "review": predict_review_king,
}

AUX_MODULES = [
    aux_miss_detective,
    aux_pattern_spotlight,
    aux_balance_keeper,
    aux_referee,
]
AUX_WEIGHTS = [0.25, 0.25, 0.25, 0.25]

VARIANTS: list[tuple[str, str]] = [
    ("baseline_set_no_asc", "V2 set_no 오름차순 쿼터 (markov3+stat1+review1)"),
    ("confidence_desc", "15세트 풀 confidence 내림차순 top 5"),
    ("aux_total_desc", "15세트 풀 AUX 합산(raw) 내림차순 top 5"),
    ("confidence_quota", "뇌별 quota 유지 · 뇌 내 confidence 최고"),
    ("aux_quota", "뇌별 quota 유지 · 뇌 내 AUX 최고"),
]


def _prediction_rank_tier(matched_count: int, bonus_matched: int) -> int:
    """routes._prediction_rank_tier 동일 (1~5 또는 0)."""
    bm = 1 if bonus_matched == 1 else 0
    if matched_count == 6:
        return 1
    if matched_count == 5 and bm == 1:
        return 2
    if matched_count == 5:
        return 3
    if matched_count == 4:
        return 4
    if matched_count == 3:
        return 5
    return 0


def _aux_composite_score(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    total = 0.0
    for mod, w in zip(AUX_MODULES, AUX_WEIGHTS):
        total += w * mod.score_set(nums, draws, target_draw_no, brain_tag=brain_tag)
    return total


def _apply_aux_scoring(
    candidates: list[dict], draws: list[dict], target_draw_no: int
) -> list[dict]:
    """coordinator._apply_aux_scoring 재현 + aux_total 보존."""
    ref_weights = get_referee_weights()
    out: list[dict] = []
    for c in candidates:
        tag = c.get("brain_tag", "") or None
        aux_total = _aux_composite_score(c["nums"], draws, target_draw_no, brain_tag=tag)
        base = float(c.get("confidence", 60))
        brain_w = ref_weights.get(c.get("brain_tag", ""), 1.0 / 3)
        final_conf = min(99.5, base * 0.5 * brain_w + aux_total * 40 + base * 0.1)
        out.append(
            {
                **c,
                "aux_total": round(aux_total, 4),
                "confidence": round(final_conf, 1),
            }
        )
    return out


def _select_confidence_quota(candidates: list[dict]) -> list[dict]:
    brain_buckets: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        tag = str(c.get("brain_tag", "") or "")
        if tag in QUOTA:
            brain_buckets[tag].append(c)

    selected: list[dict] = []
    for tag, cap in QUOTA.items():
        bucket = sorted(
            brain_buckets.get(tag) or [],
            key=lambda x: float(x.get("confidence") or 0),
            reverse=True,
        )
        selected.extend(bucket[:cap])

    if len(selected) < TARGET_N:
        used = {id(c) for c in selected}
        remainder = sorted(
            [c for c in candidates if id(c) not in used],
            key=lambda x: float(x.get("confidence") or 0),
            reverse=True,
        )
        for c in remainder:
            selected.append(c)
            if len(selected) >= TARGET_N:
                break
    return selected[:TARGET_N]


def _select_aux_quota(candidates: list[dict]) -> list[dict]:
    brain_buckets: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        tag = str(c.get("brain_tag", "") or "")
        if tag in QUOTA:
            brain_buckets[tag].append(c)

    selected: list[dict] = []
    for tag, cap in QUOTA.items():
        bucket = sorted(
            brain_buckets.get(tag) or [],
            key=lambda x: float(x.get("aux_total") or 0),
            reverse=True,
        )
        selected.extend(bucket[:cap])

    if len(selected) < TARGET_N:
        used = {id(c) for c in selected}
        remainder = sorted(
            [c for c in candidates if id(c) not in used],
            key=lambda x: float(x.get("aux_total") or 0),
            reverse=True,
        )
        for c in remainder:
            selected.append(c)
            if len(selected) >= TARGET_N:
                break
    return selected[:TARGET_N]


SELECTORS: dict[str, Callable[[list[dict]], list[dict]]] = {
    "baseline_set_no_asc": apply_markov_wire_quota,
    "confidence_desc": lambda c: sorted(
        c, key=lambda x: float(x.get("confidence") or 0), reverse=True
    )[:TARGET_N],
    "aux_total_desc": lambda c: sorted(
        c, key=lambda x: float(x.get("aux_total") or 0), reverse=True
    )[:TARGET_N],
    "confidence_quota": _select_confidence_quota,
    "aux_quota": _select_aux_quota,
}


def _empty_tier_acc() -> dict[str, dict[str, int]]:
    return {b: {"r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0, "n_sets": 0} for b in QUOTA}


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


def run_walkforward() -> tuple[dict[str, list[int]], dict[str, dict[str, dict[str, int]]], int]:
    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    variant_ids = [v[0] for v in VARIANTS]
    acc: dict[str, list[int]] = {k: [] for k in variant_ids}
    tier_acc: dict[str, dict[str, dict[str, int]]] = {
        k: _empty_tier_acc() for k in variant_ids
    }
    total = 0

    for ri, row in enumerate(rows):
        if ri % 100 == 0:
            print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {row[f"num{k}"] for k in range(1, 7)}
        bonus = int(row.get("bonus") or 0)

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

        scored = _apply_aux_scoring(candidates, draws, draw_no)

        for vid in variant_ids:
            selected = SELECTORS[vid](scored)
            best = 0
            for s in selected:
                mc = len(set(s["nums"]) & actual)
                bm = 1 if bonus in set(s["nums"]) else 0
                tier = _prediction_rank_tier(mc, bm)
                tag = str(s.get("brain_tag") or "")
                if tag in tier_acc[vid]:
                    tier_acc[vid][tag]["n_sets"] += 1
                    if tier:
                        tier_acc[vid][tag][f"r{tier}"] += 1
                best = max(best, mc)
            acc[vid].append(best)
        total += 1

    return acc, tier_acc, total


def enrich_row(variant_id: str, sm: dict[str, Any]) -> dict[str, Any]:
    ge3 = float(sm["ge3_rate"])
    ge3_c = int(sm["ge3_count"])
    n = int(sm["n"])
    p_null = float(binomtest(ge3_c, n, NULL_GE3, alternative="greater").pvalue) if n else 1.0
    p_pin = float(binomtest(ge3_c, n, WIRE_PIN_GE3, alternative="greater").pvalue) if n else 1.0
    delta_pin = round(ge3 - WIRE_PIN_GE3, 4)
    delta_null = round(ge3 - NULL_GE3, 4)
    verdict = "PASS" if ge3 > WIRE_PIN_GE3 and p_null < 0.05 else "FAIL"
    return {
        "variant_id": variant_id,
        "ge3_rate": ge3,
        "mean": sm["mean"],
        "ge4_rate": sm["ge4_rate"],
        "ge3_count": ge3_c,
        "delta_ge3_vs_pin": delta_pin,
        "delta_ge3_vs_null": delta_null,
        "p_value_vs_null": round(p_null, 6),
        "p_value_vs_pin": round(p_pin, 6),
        "verdict": verdict,
    }


def tier_pivot(tier_acc: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for brain in QUOTA:
        t = tier_acc[brain]
        ge3 = t["r3"] + t["r4"] + t["r5"]
        n = t["n_sets"]
        rows.append(
            {
                "brain": brain,
                "pipeline": "WF live",
                "r1": t["r1"],
                "r2": t["r2"],
                "r3": t["r3"],
                "r4": t["r4"],
                "r5": t["r5"],
                "ge3": ge3,
                "ge3_rate": round(ge3 / n, 4) if n else 0.0,
                "n_sets": n,
            }
        )
    return rows


def main() -> None:
    t0 = time.time()
    print(
        f"K-BENCH-02 confidence survey live walk-forward n_eval target={DRAW_END - DRAW_START + 1}",
        flush=True,
    )
    acc, tier_acc, n_eval = run_walkforward()

    results: list[dict[str, Any]] = []
    tier_pivots: dict[str, list[dict[str, Any]]] = {}
    for vid, _desc in VARIANTS:
        sm = summarize_bests(acc[vid])
        results.append(enrich_row(vid, sm))
        tier_pivots[vid] = tier_pivot(tier_acc[vid])

    results.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))
    best = results[0]
    baseline = next(r for r in results if r["variant_id"] == "baseline_set_no_asc")

    pass_gate = any(r["verdict"] == "PASS" for r in results)
    any_gt_pin = any(r["ge3_rate"] > WIRE_PIN_GE3 for r in results)

    if pass_gate:
        winners = [r["variant_id"] for r in results if r["verdict"] == "PASS"]
        recommended = "K-BENCH-02-WIRE"
        verdict = (
            f"PASS: {', '.join(winners)} ge3 > pin {WIRE_PIN_GE3} AND p<0.05 vs null. "
            f"→ K-BENCH-02-WIRE (형 승인 대기 · coordinator 수정 금지)."
        )
    else:
        recommended = "K-ATTACK-HOLD"
        verdict = (
            f"FAIL: best {best['variant_id']} ge3={best['ge3_rate']} "
            f"≤ pin {WIRE_PIN_GE3} (또는 p≥0.05). → K-ATTACK-HOLD."
        )

    out = {
        "id": "K-BENCH-02-CONFIDENCE-SURVEY",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": n_eval,
        "draw_range": [DRAW_START, DRAW_END],
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "null_ge3": NULL_GE3,
        "mc_seed": MC_SEED,
        "sets_per_predict_brain": SETS_PER_PREDICT_BRAIN,
        "pipeline": "live_predict_sets + _apply_aux_scoring + variant_select",
        "variants": [{"id": v, "description": d} for v, d in VARIANTS],
        "baseline": baseline,
        "results": results,
        "tier_pivots": tier_pivots,
        "best_variant": best,
        "gates": {
            "any_ge3_gt_pin": any_gt_pin,
            "any_pass": pass_gate,
            "best_ge3": best["ge3_rate"],
            "best_p_vs_null": best["p_value_vs_null"],
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
