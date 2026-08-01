# -*- coding: utf-8 -*-
"""K-COMBO-V2 — 번호 steering(배제 B1+B2 + 신호 B3 boost) + combined survey (READ-ONLY live WF).

B1: sum contribution extremes · B2: 3-draw consecutive run · B3: relaxed miss overlap
coordinator·predict_*·random.choices·_get_draws_before 원본 미수정.
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.bench_quick_gate import (  # noqa: E402
    DRAW_END,
    DRAW_START,
    MC_SEED,
    NULL_GE3,
    QUICK_N_EVAL,
    WIRE_PIN_GE3,
    WIRE_PIN_MEAN,
    enrich_metrics,
    filter_draw_rows,
    gate_criteria_doc,
    resolve_eval_window,
)
from tools._k_signal_select_survey import (  # noqa: E402
    SELECT_N,
    WINDOW_SIGNAL,
    WINDOW_WEEKS,
    _best_match,
    _bin_match_score,
    _expand_pool,
    _expected_bins,
    _hint_overlap_score,
    _pick_top_greedy,
)
from tools._k_window_signal_survey import _build_hint, _live_candidates  # noqa: E402

from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

random.seed(MC_SEED)

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KCOMBO_V2_survey.json"
OUT_MD = ROOT / "reports" / "20260801_KCOMBO_V2_SURVEY.md"

B1_TOP_BOTTOM = 3
B1_MIN_CANDIDATES = 35
B2_MAX_EXCLUDE = 6
B3_WINDOW = 10
B3_OVERLAP_MIN = 1
WEIGHT_EXCLUDE = 0.1
WEIGHT_BOOST = 1.5
WEIGHT_DEFAULT = 1.0
MAX_AVG_EXCLUDED = 8

STRATEGIES = [
    "baseline_combined",
    "exclude_only",
    "signal_only",
    "combo_v2",
]


def _nums_in_draw(d: dict) -> list[int]:
    if d.get("nums"):
        return [int(x) for x in d["nums"]]
    return [int(d[f"num{k}"]) for k in range(1, 7)]


def _compute_b1_exclude(draws: list[dict]) -> set[int]:
    """Sum contribution avg per number — top3 + bottom3, cap to keep ≥35 candidates."""
    if not draws:
        return set()
    contrib_sum: dict[int, float] = {n: 0.0 for n in range(1, 46)}
    contrib_cnt: dict[int, int] = {n: 0 for n in range(1, 46)}
    for d in draws:
        for n in _nums_in_draw(d):
            contrib_sum[n] += float(n)
            contrib_cnt[n] += 1
    avg_contrib: dict[int, float] = {}
    for n in range(1, 46):
        if contrib_cnt[n] > 0:
            avg_contrib[n] = contrib_sum[n] / contrib_cnt[n]
        else:
            avg_contrib[n] = float(n)
    ranked = sorted(avg_contrib.items(), key=lambda x: x[1])
    bottom = {n for n, _ in ranked[:B1_TOP_BOTTOM]}
    top = {n for n, _ in ranked[-B1_TOP_BOTTOM:]}
    excl = bottom | top
    while len({n for n in range(1, 46) if n not in excl}) < B1_MIN_CANDIDATES and excl:
        excl.pop()
    return excl


def _compute_b2_exclude(draws: list[dict]) -> set[int]:
    """Numbers appearing in all of last 3 draws."""
    if len(draws) < 3:
        return set()
    last3 = draws[-3:]
    sets3 = [set(_nums_in_draw(d)) for d in last3]
    run3 = sets3[0] & sets3[1] & sets3[2]
    out = set(list(run3)[:B2_MAX_EXCLUDE])
    return out


def _miss_numbers(draws: list[dict], window: int) -> set[int]:
    wd = draws[-window:] if len(draws) >= window else list(draws)
    seen: set[int] = set()
    for d in wd:
        seen.update(_nums_in_draw(d))
    return {n for n in range(1, 46) if n not in seen}


def _compute_b3_signal(
    draws: list[dict], draw_no: int, std_candidates: list[dict]
) -> set[int]:
    """Relaxed miss: window=10 미출현 ∩ stat/review overlap≥1."""
    miss = _miss_numbers(draws, B3_WINDOW)
    pred: set[int] = set()
    for c in std_candidates:
        if c.get("brain_tag") in ("stat", "review"):
            pred.update(int(x) for x in c["nums"])
    signal = miss & pred
    return signal if len(signal) >= B3_OVERLAP_MIN else set()


def _build_steering(
    draws: list[dict],
    draw_no: int,
    std_candidates: list[dict],
) -> tuple[set[int], set[int], set[int]]:
    b1 = _compute_b1_exclude(draws)
    b2 = _compute_b2_exclude(draws)
    exclude = b1 | b2
    if len({n for n in range(1, 46) if n not in exclude}) < B1_MIN_CANDIDATES:
        exclude = set(list(exclude)[: max(0, 45 - B1_MIN_CANDIDATES)])
    b3 = _compute_b3_signal(draws, draw_no, std_candidates)
    return b1, exclude, b3


def _number_weight(n: int, exclude: set[int], boost: set[int], mode: str) -> float:
    if mode == "baseline_combined":
        return WEIGHT_DEFAULT
    if mode == "exclude_only":
        return WEIGHT_EXCLUDE if n in exclude else WEIGHT_DEFAULT
    if mode == "signal_only":
        return WEIGHT_BOOST if n in boost else WEIGHT_DEFAULT
    if mode == "combo_v2":
        if n in boost:
            return WEIGHT_BOOST
        if n in exclude:
            return WEIGHT_EXCLUDE
        return WEIGHT_DEFAULT
    return WEIGHT_DEFAULT


def _steered_score(nums: list[int], exclude: set[int], boost: set[int], mode: str) -> float:
    if not nums:
        return 0.0
    return sum(_number_weight(int(n), exclude, boost, mode) for n in nums) / 6.0


def _pick_combined_steered(
    pool: list[dict],
    hint: dict[int, float],
    expected_bins: dict[str, str],
    exclude: set[int],
    boost: set[int],
    mode: str,
) -> list[dict]:
    if mode == "baseline_combined":
        return _pick_top_greedy(
            pool,
            lambda nums: (
                0.5 * _hint_overlap_score(nums, hint)
                + 0.35 * _bin_match_score(nums, expected_bins)
            ),
            diversity_weight=0.15,
        )

    def score_fn(nums: list[int]) -> float:
        base = 0.5 * _hint_overlap_score(nums, hint) + 0.35 * _bin_match_score(nums, expected_bins)
        steer = _steered_score(nums, exclude, boost, mode)
        return base * (0.5 + 0.5 * steer)

    return _pick_top_greedy(pool, score_fn, diversity_weight=0.15)


def run_survey() -> dict[str, Any]:
    init_lotto_db()
    eval_window = resolve_eval_window(n_eval=QUICK_N_EVAL, sample_mode="tail")
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    rows = filter_draw_rows(rows, eval_window)

    acc: dict[str, list[int]] = {s: [] for s in STRATEGIES}
    means: dict[str, list[float]] = {s: [] for s in STRATEGIES}
    excl_counts: list[int] = []
    boost_counts: list[int] = []
    b3_flags: list[bool] = []

    t0 = time.time()
    for ri, row in enumerate(rows):
        if ri % 50 == 0:
            print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        random.seed(MC_SEED)
        std_candidates = _live_candidates(draws, draw_no)
        pool = _expand_pool(draws, draw_no)
        hint = _build_hint(draws, WINDOW_WEEKS, WINDOW_SIGNAL, draw_no)
        expected_bins = _expected_bins(draws)

        _b1, exclude, boost = _build_steering(draws, draw_no, std_candidates)
        excl_counts.append(len(exclude))
        boost_counts.append(len(boost))
        b3_flags.append(len(boost) > 0)

        for strat in STRATEGIES:
            selected = _pick_combined_steered(pool, hint, expected_bins, exclude, boost, strat)
            best = _best_match(selected, actual)
            acc[strat].append(best)
            means[strat].append(float(best))

    n_eval = len(acc["baseline_combined"])
    elapsed = round(time.time() - t0, 1)
    baseline_ge3 = sum(1 for x in acc["baseline_combined"] if x >= 3) / n_eval if n_eval else 0.0
    avg_excl = round(sum(excl_counts) / n_eval, 2) if n_eval else 0.0
    avg_boost = round(sum(boost_counts) / n_eval, 2) if n_eval else 0.0
    b3_cov = round(sum(b3_flags) / n_eval, 4) if n_eval else 0.0
    over_exclude = avg_excl > MAX_AVG_EXCLUDED

    strategies_out: dict[str, Any] = {}
    best_id = "baseline_combined"
    best_delta = -1.0

    for strat in STRATEGIES:
        bests = acc[strat]
        ge3_c = sum(1 for x in bests if x >= 3)
        ge4_c = sum(1 for x in bests if x >= 4)
        mean_v = sum(means[strat]) / n_eval if n_eval else 0.0
        base = enrich_metrics(ge3_c, n_eval, mean_v, gate_mode="quick")
        delta_vs_bl = round(base["ge3_rate"] - baseline_ge3, 4)
        quick_pass = base["ge3_rate"] > baseline_ge3 and base["p_value"] < 0.15 and not over_exclude
        if strat != "baseline_combined" and delta_vs_bl > best_delta:
            best_delta = delta_vs_bl
            best_id = strat
        strategies_out[strat] = {
            **base,
            "ge4_rate": round(ge4_c / n_eval, 4) if n_eval else 0.0,
            "ge4_count": ge4_c,
            "delta_vs_baseline_ge3": delta_vs_bl,
            "avg_excluded": avg_excl,
            "avg_boosted": avg_boost,
            "signal_B3_coverage": b3_cov,
            "quick_pass_vs_baseline": quick_pass,
        }

    best = strategies_out[best_id]
    pass_gate = (
        best_id != "baseline_combined"
        and best.get("quick_pass_vs_baseline", False)
        and best["ge3_rate"] > baseline_ge3
    )

    out: dict[str, Any] = {
        "id": "K-COMBO-V2",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": elapsed,
        "n_eval": n_eval,
        "draw_range": [int(rows[0]["draw_no"]), int(rows[-1]["draw_no"])] if rows else [],
        "seed": MC_SEED,
        "gate_mode": "quick",
        "wire_pin_ge3": WIRE_PIN_GE3,
        "null_ge3": NULL_GE3,
        "exclude_params": {
            "B1_top_bottom": B1_TOP_BOTTOM,
            "B1_min_candidates": B1_MIN_CANDIDATES,
            "B2_max_exclude": B2_MAX_EXCLUDE,
            "B3_window": B3_WINDOW,
            "B3_overlap_min": B3_OVERLAP_MIN,
            "weight_exclude": WEIGHT_EXCLUDE,
            "weight_boost": WEIGHT_BOOST,
        },
        "avg_excluded_per_draw": avg_excl,
        "avg_boosted_per_draw": avg_boost,
        "signal_B3_coverage": b3_cov,
        "over_exclude_fail": over_exclude,
        "baseline_combined_ge3": round(baseline_ge3, 4),
        "strategies": strategies_out,
        "best_strategy": best_id if pass_gate else "baseline_combined",
        "gates": {
            "quick_pass": pass_gate,
            "quick_criteria": "best ge3 > baseline AND p<0.15 AND avg_excluded<=8",
            "criteria_doc": gate_criteria_doc(),
        },
        "pass_gate": pass_gate,
        "verdict": "PASS" if pass_gate else "FAIL",
        "recommended_next": "K-COMBO-V2-FULL" if pass_gate else "K-ATTACK-HOLD",
        "db_code_write": False,
        "coordinator_modified": False,
    }
    return out


def _write_report(out: dict[str, Any]) -> None:
    n = out["n_eval"]
    bl_ge3 = out["baseline_combined_ge3"]
    lines = [
        "# K-COMBO-V2 — 번호 steering(배제+신호 boost) survey",
        "",
        f"날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · **{out['verdict']}** · "
        f"seed={out['seed']} · n={n} · gate=quick",
        "",
        f"baseline_combined ge3=**{bl_ge3}** · avg_excluded={out['avg_excluded_per_draw']} · "
        f"B3_coverage={out['signal_B3_coverage']}",
        "",
        "## §6 baseline표",
        "| label | ge3_rate | mean | p | Δpin |",
        "|-------|--------:|-----:|--:|-----:|",
        f"| null | {NULL_GE3} | 0.80 | — | — |",
        f"| pin | {WIRE_PIN_GE3} | {WIRE_PIN_MEAN} | — | — |",
    ]
    bl = out["strategies"]["baseline_combined"]
    lines.append(f"| baseline_combined | {bl['ge3_rate']} | {bl['mean']} | {bl['p_value']} | {bl['delta_ge3_vs_pin']:+.4f} |")

    lines.extend([
        "",
        "## §7 전략 비교표",
        "| strategy | ge3 | ge3_cnt | mean | p | Δbaseline | avg_excl | B3_cov | verdict |",
        "|----------|----:|--------:|-----:|--:|----------:|---------:|-------:|---------|",
    ])
    for sid, s in out["strategies"].items():
        vp = "PASS" if s.get("quick_pass_vs_baseline") else "FAIL"
        lines.append(
            f"| {sid} | {s['ge3_rate']} | {s['ge3_count']} | {s['mean']} | {s['p_value']} | "
            f"{s['delta_vs_baseline_ge3']:+.4f} | {s['avg_excluded']} | {s['signal_B3_coverage']} | {vp} |"
        )

    lines.extend([
        "",
        "## Verdict",
        f"- **QUICK PASS:** best > baseline({bl_ge3}) AND p<0.15 AND avg_excl≤8 → **{out['pass_gate']}**",
        f"- **best_strategy:** `{out['best_strategy']}`",
        f"- **recommended_next:** {out['recommended_next']}",
        "",
        f"*JSON:* `{OUT_JSON}`",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print(f"K-COMBO-V2 QUICK n={QUICK_N_EVAL} seed={MC_SEED}", flush=True)
    out = run_survey()
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(out)
    print(f"wrote {OUT_JSON}", flush=True)
    print(f"wrote {OUT_MD}", flush=True)
    best = out["strategies"][out["best_strategy"]]
    print(
        f"verdict={out['verdict']}: best={out['best_strategy']} ge3={best['ge3_rate']} "
        f"p={best['p_value']} B3_cov={out['signal_B3_coverage']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
