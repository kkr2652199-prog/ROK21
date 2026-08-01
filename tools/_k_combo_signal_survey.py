# -*- coding: utf-8 -*-
"""K-COMBO-SIGNAL-01 — miss_pattern(α=0.2) AND w4_zone_mix AND gate survey (READ-ONLY live WF).

signal_A: miss_pattern overlap with stat/review sets ≥ 2
signal_B: combined 5 zone vector within Δ≤1.0 of w4 zone_hint
3 strategies: baseline_combined · signal_AB_filter · signal_AB_boost
coordinator·predict_*·_get_draws_before·random.choices 원본 미수정.
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
from tools._k_aux_signal_survey import hint_miss_pattern  # noqa: E402
from tools._k_signal_select_survey import (  # noqa: E402
    SELECT_N,
    WINDOW_SIGNAL,
    WINDOW_WEEKS,
    _best_match,
    _bin_match_score,
    _expand_pool,
    _expected_bins,
    _hint_overlap_score,
    _pick_set_no_asc,
    _pick_top_greedy,
)
from tools._k_window_signal_survey import _build_hint, _live_candidates  # noqa: E402

from app.testlotto.brains.coordinator import apply_markov_wire_quota  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

random.seed(MC_SEED)

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KCOMBO_SIGNAL_survey.json"
OUT_MD = ROOT / "reports" / "20260801_KCOMBO_SIGNAL_SURVEY.md"

SIGNAL_A_ALPHA = 0.2
SIGNAL_A_MISS_WINDOW = 20
SIGNAL_A_OVERLAP_MIN = 2
SIGNAL_B_WEEKS = 4
SIGNAL_B_ZONE_DELTA = 1.0

STRATEGIES = ["baseline_combined", "signal_AB_filter", "signal_AB_boost"]


def _zone_idx(n: int) -> int:
    if n <= 15:
        return 0
    if n <= 30:
        return 1
    return 2


def _zone_counts(nums: list[int]) -> list[float]:
    c = [0.0, 0.0, 0.0]
    for n in nums:
        c[_zone_idx(int(n))] += 1.0
    return c


def _zone_hint_vector(draws: list[dict], weeks: int = SIGNAL_B_WEEKS) -> list[float]:
    """w4 average zone counts per draw."""
    wd = draws[-weeks:] if len(draws) >= weeks else list(draws)
    if not wd:
        return [2.0, 2.0, 2.0]
    per_draw: list[list[float]] = []
    for d in wd:
        nums = sorted_nums(d)
        per_draw.append(_zone_counts(nums))
    n = len(per_draw)
    return [sum(v[i] for v in per_draw) / n for i in range(3)]


def _avg_zone_vector_sets(sets: list[dict]) -> list[float]:
    if not sets:
        return [0.0, 0.0, 0.0]
    vecs = [_zone_counts([int(x) for x in s["nums"]]) for s in sets]
    n = len(vecs)
    return [sum(v[i] for v in vecs) / n for i in range(3)]


def _zone_delta(a: list[float], b: list[float]) -> float:
    return max(abs(a[i] - b[i]) for i in range(3))


def _miss_numbers_recent(draws: list[dict], window: int = SIGNAL_A_MISS_WINDOW) -> set[int]:
    """Numbers not drawn in last `window` draws before T."""
    wd = draws[-window:] if len(draws) >= window else list(draws)
    if not wd:
        return set(range(1, 46))
    seen: set[int] = set()
    for d in wd:
        for n in sorted_nums(d):
            seen.add(int(n))
    return {n for n in range(1, 46) if n not in seen}


def signal_a_miss_pattern(draws: list[dict], draw_no: int, std_candidates: list[dict]) -> bool:
    """miss_pattern α=0.2: miss-window numbers with hint≥α overlap stat/review ≥2."""
    hint = hint_miss_pattern(draws, draw_no)
    miss_nums = _miss_numbers_recent(draws, SIGNAL_A_MISS_WINDOW)
    hot_miss = {n for n in miss_nums if hint.get(n, 0.0) >= SIGNAL_A_ALPHA}
    if len(hot_miss) < SIGNAL_A_OVERLAP_MIN:
        return False
    pred_nums: set[int] = set()
    for c in std_candidates:
        if c.get("brain_tag") in ("stat", "review"):
            for x in c["nums"]:
                pred_nums.add(int(x))
    overlap = len(hot_miss & pred_nums)
    return overlap >= SIGNAL_A_OVERLAP_MIN


def signal_b_zone_match(combined_5: list[dict], zone_hint: list[float]) -> bool:
    avg = _avg_zone_vector_sets(combined_5)
    return _zone_delta(avg, zone_hint) <= SIGNAL_B_ZONE_DELTA


def _pick_combined(pool: list[dict], hint: dict[int, float], expected_bins: dict[str, str]) -> list[dict]:
    return _pick_top_greedy(
        pool,
        lambda nums: (
            0.5 * _hint_overlap_score(nums, hint)
            + 0.35 * _bin_match_score(nums, expected_bins)
        ),
        diversity_weight=0.15,
    )


def _pick_hybrid(
    std_candidates: list[dict], combined_5: list[dict]
) -> list[dict]:
    """set_no_asc 3 + combined 2 (dedupe by nums)."""
    asc = _pick_set_no_asc(std_candidates)
    asc3 = asc[:3]
    used = {tuple(sorted(int(x) for x in s["nums"])) for s in asc3}
    extra: list[dict] = []
    for c in combined_5:
        key = tuple(sorted(int(x) for x in c["nums"]))
        if key not in used:
            extra.append(c)
            used.add(key)
        if len(extra) >= 2:
            break
    if len(extra) < 2:
        for c in combined_5:
            key = tuple(sorted(int(x) for x in c["nums"]))
            if key not in used:
                extra.append(c)
                used.add(key)
            if len(extra) >= 2:
                break
    return asc3 + extra[:2]


def _strategy_pick(
    strategy: str,
    *,
    signal_ab: bool,
    std_candidates: list[dict],
    pool: list[dict],
    hint: dict[int, float],
    expected_bins: dict[str, str],
) -> list[dict]:
    combined = _pick_combined(pool, hint, expected_bins)
    if strategy == "baseline_combined":
        return combined
    if strategy == "signal_AB_filter":
        return combined if signal_ab else _pick_set_no_asc(std_candidates)
    if strategy == "signal_AB_boost":
        return combined if signal_ab else _pick_hybrid(std_candidates, combined)
    raise ValueError(strategy)


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
    signal_ab_flags: list[bool] = []
    signal_a_flags: list[bool] = []
    signal_b_flags: list[bool] = []
    per_draw_log: list[dict[str, Any]] = []

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
        zone_hint = _zone_hint_vector(draws, SIGNAL_B_WEEKS)

        combined_preview = _pick_combined(pool, hint, expected_bins)
        sa = signal_a_miss_pattern(draws, draw_no, std_candidates)
        sb = signal_b_zone_match(combined_preview, zone_hint)
        sab = sa and sb
        signal_a_flags.append(sa)
        signal_b_flags.append(sb)
        signal_ab_flags.append(sab)

        picks: dict[str, list[dict]] = {}
        for strat in STRATEGIES:
            selected = _strategy_pick(
                strat,
                signal_ab=sab,
                std_candidates=std_candidates,
                pool=pool,
                hint=hint,
                expected_bins=expected_bins,
            )
            picks[strat] = selected
            best = _best_match(selected, actual)
            acc[strat].append(best)
            means[strat].append(float(best))

        per_draw_log.append(
            {
                "draw_no": draw_no,
                "signal_A": sa,
                "signal_B": sb,
                "signal_AB": sab,
                "zone_hint": [round(x, 3) for x in zone_hint],
                "zone_delta": round(_zone_delta(_avg_zone_vector_sets(combined_preview), zone_hint), 3),
            }
        )

    n_eval = len(acc["baseline_combined"])
    elapsed = round(time.time() - t0, 1)

    strategies_out: dict[str, Any] = {}
    best_id = "baseline_combined"
    best_ge3 = -1.0
    quick_pass_any = False

    sab_indices = [i for i, f in enumerate(signal_ab_flags) if f]
    sab_n = len(sab_indices)

    for strat in STRATEGIES:
        bests = acc[strat]
        ge3_c = sum(1 for x in bests if x >= 3)
        ge4_c = sum(1 for x in bests if x >= 4)
        mean_v = sum(means[strat]) / n_eval if n_eval else 0.0
        base = enrich_metrics(ge3_c, n_eval, mean_v, gate_mode="quick")
        quick_pass = ge3_c / n_eval > WIRE_PIN_GE3 if n_eval else False
        quick_pass_strict = quick_pass and base["p_value"] < 0.15
        if quick_pass_strict:
            quick_pass_any = True
        if base["ge3_rate"] > best_ge3:
            best_ge3 = base["ge3_rate"]
            best_id = strat

        sab_ge3 = sum(1 for i in sab_indices if bests[i] >= 3) if sab_n else 0
        sab_hit_rate = round(sab_ge3 / sab_n, 4) if sab_n else None

        strategies_out[strat] = {
            **base,
            "ge4_rate": round(ge4_c / n_eval, 4) if n_eval else 0.0,
            "ge4_count": ge4_c,
            "signal_AB_coverage": round(sab_n / n_eval, 4) if n_eval else 0.0,
            "signal_AB_true_count": sab_n,
            "signal_AB_hit_rate": sab_hit_rate,
            "quick_pass_ge3_pin": quick_pass,
            "quick_pass_gate": quick_pass_strict,
        }

    best = strategies_out[best_id]
    pass_gate = best.get("quick_pass_gate", False)

    out: dict[str, Any] = {
        "id": "K-COMBO-SIGNAL-01",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": elapsed,
        "n_eval": n_eval,
        "draw_range": [int(rows[0]["draw_no"]), int(rows[-1]["draw_no"])] if rows else [],
        "seed": MC_SEED,
        "gate_mode": "quick",
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "null_ge3": NULL_GE3,
        "signal_A_params": {
            "alpha": SIGNAL_A_ALPHA,
            "miss_window": SIGNAL_A_MISS_WINDOW,
            "overlap_min": SIGNAL_A_OVERLAP_MIN,
            "brains": ["stat", "review"],
        },
        "signal_B_params": {
            "window_weeks": SIGNAL_B_WEEKS,
            "signal": "w4_zone_mix",
            "zone_delta_max": SIGNAL_B_ZONE_DELTA,
        },
        "signal_summary": {
            "signal_A_rate": round(sum(signal_a_flags) / n_eval, 4) if n_eval else 0.0,
            "signal_B_rate": round(sum(signal_b_flags) / n_eval, 4) if n_eval else 0.0,
            "signal_AB_rate": round(sab_n / n_eval, 4) if n_eval else 0.0,
            "signal_AB_count": sab_n,
        },
        "strategies": strategies_out,
        "best_strategy": best_id,
        "gates": {
            "quick_pass": pass_gate,
            "quick_criteria": gate_criteria_doc(),
            "full_pass_ref": "ge3>0.1447 AND p<0.05",
            "full_pass": False,
        },
        "pass_gate": pass_gate,
        "verdict": "PASS" if pass_gate else "FAIL",
        "recommended_next": "K-COMBO-SIGNAL-FULL" if pass_gate else "K-ATTACK-HOLD",
        "db_code_write": False,
        "coordinator_modified": False,
        "per_draw_sample": per_draw_log[:5] + per_draw_log[-3:],
    }
    return out


def _write_report(out: dict[str, Any]) -> None:
    n = out["n_eval"]
    ss = out["signal_summary"]
    lines: list[str] = [
        "# K-COMBO-SIGNAL-01 — miss_pattern AND w4_zone_mix AND gate survey",
        "",
        f"날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · **{out['verdict']}** · "
        f"seed={out['seed']} · n={n} · gate=quick",
        "",
        "개념: signal_A(miss_pattern α=0.2 · stat/review overlap≥2) **AND** "
        "signal_B(w4 zone_hint Δ≤1.0) → 3전략 live WF.",
        "",
        "## §6 baseline표 (BENCH_PROTOCOL §6)",
        "| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) |",
        "|-------|----------|-----:|---------:|-----:|-------------:|------------:|------------:|",
        f"| **theory_baseline** | — | 0.8000 | {NULL_GE3} | — | — | — | — |",
        f"| **WIRE-V2 pin** | stored | {WIRE_PIN_MEAN} | {WIRE_PIN_GE3} | ✓ | — | — | — |",
    ]
    bl = out["strategies"]["baseline_combined"]
    lines.append(
        f"| baseline_combined | WF live | {bl['mean']} | {bl['ge3_rate']} | — | "
        f"{bl['delta_ge3_vs_null']:+.4f} | {bl['delta_ge3_vs_pin']:+.4f} | {bl['p_value']} |"
    )

    lines.extend(["", "## §7 전략 비교표", "| strategy | ge3_rate | ge3_cnt | mean | ge4_rate | p | Δpin | AB_cov | AB_hit | verdict |", "|----------|--------:|--------:|-----:|---------:|--:|-----:|-------:|-------:|---------|"])
    for sid, s in out["strategies"].items():
        ab_hit = s.get("signal_AB_hit_rate")
        ab_hit_s = f"{ab_hit}" if ab_hit is not None else "—"
        lines.append(
            f"| {sid} | {s['ge3_rate']} | {s['ge3_count']} | {s['mean']} | {s['ge4_rate']} | "
            f"{s['p_value']} | {s['delta_ge3_vs_pin']:+.4f} | {s['signal_AB_coverage']} | {ab_hit_s} | "
            f"{'PASS' if s.get('quick_pass_gate') else 'FAIL'} |"
        )

    best = out["strategies"][out["best_strategy"]]
    lines.extend(
        [
            "",
            "## signal coverage 분석",
            f"| signal | True 비율 | True 회차 |",
            f"|--------|----------:|----------:|",
            f"| signal_A (miss_pattern) | {ss['signal_A_rate']} | {int(ss['signal_A_rate'] * n)} |",
            f"| signal_B (w4 zone) | {ss['signal_B_rate']} | {int(ss['signal_B_rate'] * n)} |",
            f"| **signal_AB (AND)** | **{ss['signal_AB_rate']}** | **{ss['signal_AB_count']}** |",
            "",
            "## Verdict",
            f"- **QUICK PASS:** ge3 > {WIRE_PIN_GE3} AND p < 0.15 → **{out['pass_gate']}**",
            f"- **best_strategy:** `{out['best_strategy']}` ge3={best['ge3_rate']} p={best['p_value']}",
            f"- **recommended_next:** {out['recommended_next']}",
            "",
            "## 팩트체크",
            "| 항목 | JSON |",
            "|------|------|",
            f"| n_eval | {n} |",
            f"| pass_gate | {out['pass_gate']} |",
            f"| coordinator_modified | {out['coordinator_modified']} |",
            "",
            f"*JSON:* `{OUT_JSON}`",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print(f"K-COMBO-SIGNAL-01 QUICK n={QUICK_N_EVAL} seed={MC_SEED}", flush=True)
    out = run_survey()
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(out)
    print(f"wrote {OUT_JSON}", flush=True)
    print(f"wrote {OUT_MD}", flush=True)
    best = out["strategies"][out["best_strategy"]]
    print(
        f"verdict={out['verdict']}: best {out['best_strategy']} ge3={best['ge3_rate']} "
        f"p={best['p_value']} AB_cov={out['signal_summary']['signal_AB_rate']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
