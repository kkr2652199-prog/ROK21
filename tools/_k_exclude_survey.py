# -*- coding: utf-8 -*-
"""K-EXCLUDE-SURVEY — combined + 배제 ON/OFF · λ sweep (READ-ONLY live WF).

10세트 pool (survey 2-pass) → 배제 필터(λ) → combined 5세트 선별.
패턴: max_run≥3 · sum p05-p95 밖 · zone skew 4+ low/high.
coordinator·predict_*·_get_draws_before 원본 미수정 · per-draw as_of catalog.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.bench_quick_gate import (  # noqa: E402
    DRAW_END,
    DRAW_START,
    FULL_N_EVAL,
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
    POOL_SETS_PER_BRAIN,
    SELECT_N,
    WINDOW_ALPHA,
    WINDOW_SIGNAL,
    WINDOW_WEEKS,
    _best_match,
    _bin_match_score,
    _expand_pool,
    _expected_bins,
    _hint_overlap_score,
    _live_candidates,
    _pick_top_greedy,
)
from tools._k_window_signal_survey import _build_hint  # noqa: E402

from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

random.seed(MC_SEED)

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KEXCLUDE_survey.json"
OUT_JSON_FULL = ROOT / "docs" / "benchmarks" / "20260801_KEXCLUDE_survey_full.json"
OUT_MD = ROOT / "reports" / "20260801_KEXCLUDE_SURVEY.md"
OUT_MD_FULL = ROOT / "reports" / "20260801_KEXCLUDE_SURVEY_FULL.md"

LAMBDA_SWEEP = [0.0, 0.25, 0.5, 0.75, 1.0]
OVER_EXCLUDE_THRESHOLD = 0.90  # >90% pool killed → FAIL
COMBINED_BASELINE_FULL = 0.1218
COMBINED_BASELINE_QUICK = 0.145


def _max_consecutive_run(nums: list[int]) -> int:
    s = sorted(nums)
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def _zone(n: int) -> str:
    if n <= 15:
        return "low"
    if n <= 30:
        return "mid"
    return "high"


def build_exclude_catalog(draws: list[dict]) -> dict[str, Any]:
    """WF-safe catalog from draws with draw_no < as_of (caller supplies filtered draws)."""
    if not draws:
        return {
            "n_draws": 0,
            "sum_p05": 88,
            "sum_p95": 189,
            "patterns": ["max_run_ge3", "sum_outside_p05_p95", "zone_skew_4plus"],
        }
    sums: list[int] = []
    for d in draws:
        if isinstance(d.get("nums"), list) and d["nums"]:
            sums.append(sum(int(x) for x in d["nums"]))
        else:
            sums.append(sum(int(d[f"num{k}"]) for k in range(1, 7)))
    sums.sort()
    n = len(sums)
    p05_idx = max(0, int(n * 0.05) - 1)
    p95_idx = min(n - 1, int(n * 0.95))
    return {
        "n_draws": n,
        "sum_p05": sums[p05_idx],
        "sum_p95": sums[p95_idx],
        "patterns": ["max_run_ge3", "sum_outside_p05_p95", "zone_skew_4plus"],
        "as_of_policy": "walk_forward_draws_lt_T",
    }


def _nums_from_draw_row(row: dict) -> list[int]:
    if "nums" in row and row["nums"]:
        return [int(x) for x in row["nums"]]
    return [int(row[f"num{k}"]) for k in range(1, 7)]


def _normalize_draws(draws: list[dict]) -> list[dict]:
    out = []
    for d in draws:
        dd = dict(d)
        if "nums" not in dd or not dd["nums"]:
            dd["nums"] = _nums_from_draw_row(dd)
        out.append(dd)
    return out


def exclude_pattern_flags(nums: list[int], catalog: dict[str, Any]) -> list[bool]:
    """Three HIST patterns — True = matches exclude candidate."""
    flags: list[bool] = []
    # max consecutive >= 3
    flags.append(_max_consecutive_run(nums) >= 3)
    s = sum(nums)
    flags.append(s < catalog["sum_p05"] or s > catalog["sum_p95"])
    zones = Counter(_zone(x) for x in nums)
    flags.append(zones.get("low", 0) >= 4 or zones.get("high", 0) >= 4)
    return flags


def exclude_score(nums: list[int], catalog: dict[str, Any]) -> float:
    flags = exclude_pattern_flags(nums, catalog)
    return sum(1 for f in flags if f) / len(flags)


def should_exclude(nums: list[int], catalog: dict[str, Any], lam: float) -> bool:
    if lam <= 0:
        return False
    return exclude_score(nums, catalog) >= lam


def filter_pool(pool: list[dict], catalog: dict[str, Any], lam: float) -> tuple[list[dict], float]:
    """Return (filtered_pool, kill_rate). Empty → fallback to full pool."""
    if lam <= 0:
        return pool, 0.0
    kept = [c for c in pool if not should_exclude([int(x) for x in c["nums"]], catalog, lam)]
    kill_rate = 1.0 - (len(kept) / len(pool)) if pool else 0.0
    if not kept:
        return pool, kill_rate
    return kept, kill_rate


def _pick_combined(pool: list[dict], hint: dict, expected_bins: dict) -> list[dict]:
    return _pick_top_greedy(
        pool,
        lambda nums: (
            0.5 * _hint_overlap_score(nums, hint)
            + 0.35 * _bin_match_score(nums, expected_bins)
        ),
        diversity_weight=0.15,
    )


def run_survey(eval_window) -> tuple[int, dict[float, list[int]], dict[float, list[float]], dict[float, list[float]]]:
    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    rows = filter_draw_rows(rows, eval_window)

    acc: dict[float, list[int]] = {lam: [] for lam in LAMBDA_SWEEP}
    means: dict[float, list[float]] = {lam: [] for lam in LAMBDA_SWEEP}
    kill_rates: dict[float, list[float]] = {lam: [] for lam in LAMBDA_SWEEP}

    for ri, row in enumerate(rows):
        if ri % 50 == 0:
            print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}

        set_learn_as_of(draw_no)
        draws = _normalize_draws(_get_draws_before(draw_no))
        if not draws:
            continue

        random.seed(MC_SEED)
        pool = _expand_pool(draws, draw_no)
        catalog = build_exclude_catalog(draws)
        hint = _build_hint(draws, WINDOW_WEEKS, WINDOW_SIGNAL, draw_no)
        expected_bins = _expected_bins(draws)

        for lam in LAMBDA_SWEEP:
            filtered, kr = filter_pool(pool, catalog, lam)
            selected = _pick_combined(filtered, hint, expected_bins)
            best = _best_match(selected, actual)
            acc[lam].append(best)
            means[lam].append(float(best))
            kill_rates[lam].append(kr)

    n_eval = len(acc[0.0])
    mean_by_lam = {
        lam: round(sum(means[lam]) / len(means[lam]), 4) if means[lam] else 0.0
        for lam in LAMBDA_SWEEP
    }
    avg_kill = {
        lam: round(sum(kill_rates[lam]) / len(kill_rates[lam]), 4) if kill_rates[lam] else 0.0
        for lam in LAMBDA_SWEEP
    }
    return n_eval, acc, mean_by_lam, avg_kill


def _summarize_variant(
    lam: float,
    bests: list[int],
    mean: float,
    avg_kill: float,
    gate_mode: str,
    baseline_ge3: float,
) -> dict[str, Any]:
    ge3_c = sum(1 for x in bests if x >= 3)
    ge4_c = sum(1 for x in bests if x >= 4)
    n = len(bests)
    base = enrich_metrics(ge3_c, n, mean, gate_mode=gate_mode)
    delta_vs_combined = round(base["ge3_rate"] - baseline_ge3, 4)
    label = "combined_baseline" if lam == 0.0 else f"combined_exclude_l{lam:g}"
    return {
        "variant_id": label,
        "lambda": lam,
        "exclude_on": lam > 0,
        "pool_sets_per_brain": POOL_SETS_PER_BRAIN,
        "selected_n": SELECT_N,
        **base,
        "delta_ge3_vs_combined_baseline": delta_vs_combined,
        "ge4_rate": round(ge4_c / n, 4) if n else 0.0,
        "ge4_count": ge4_c,
        "avg_pool_kill_rate": avg_kill,
        "over_exclude": avg_kill > OVER_EXCLUDE_THRESHOLD,
    }


def _p_vs_baseline(baseline_hits: list[int], variant_hits: list[int]) -> float:
    """One-sided: variant better than baseline (more ge3+ draws)."""
    if not baseline_hits or len(baseline_hits) != len(variant_hits):
        return 1.0
    wins = sum(
        1 for b, v in zip(baseline_hits, variant_hits) if v >= 3 and b < 3
    )
    losses = sum(
        1 for b, v in zip(baseline_hits, variant_hits) if b >= 3 and v < 3
    )
    n = len(baseline_hits)
    # McNemar-style: count discordant pairs where variant wins
    if wins + losses == 0:
        return 1.0
    return float(binomtest(wins, wins + losses, 0.5, alternative="greater").pvalue)


def _write_report(out: dict[str, Any], md_path: Path) -> None:
    results = out["variants"]
    baseline = out["baseline"]
    best = out["best_variant"]
    best_ex = out.get("best_exclude_on", best)
    n = out["n_eval"]
    gate_mode = out["gate_mode"]
    pass_gate = out["pass_gate"]
    survey_id = out["id"]

    title = "전체 검증(1182회)" if gate_mode == "full" else "빠른 검증(200회)"
    lines: list[str] = []
    lines.append(f"# {survey_id} — combined + 배제 λ sweep ({title} · READ-ONLY live WF)")
    lines.append(
        f"\n날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · "
        f"**{'PASS' if pass_gate else 'FAIL'}** · seed={MC_SEED} · n={n} · gate={gate_mode}"
    )
    lines.append(
        f"\n개념: 3뇌×{POOL_SETS_PER_BRAIN} pool → **배제 필터(λ)** → combined {SELECT_N}선별 · "
        f"패턴: 3연속+ · 합 p05-p95 밖 · zone 4+ skew · per-draw `build_exclude_catalog(as_of=T)`."
    )

    lines.append("\n## 1. 📋 숙제")
    lines.append("| 항목 | 내용 |")
    lines.append("|------|------|")
    lines.append(f"| **ID** | `{survey_id}` |")
    lines.append("| **질문** | combined 선별에 WF-safe 배제(λ)를 얹으면 ge3가 baseline(0.145 quick / 0.1218 full)을 이기는가? |")
    lines.append("| **PASS** | exclude ON variant > combined baseline **AND** p<0.15(quick)/0.05(full) **AND** 과배제≤90% |")
    lines.append("| **금지** | coordinator wire · `_get_draws_before` 수정 · catalog 미래누수 |")

    lines.append("\n## 2. SUMMARY")
    lines.append("| label | λ | mean | ge3_rate | ge3_cnt | Δpin | Δcombined | p(vs null) | kill% | verdict |")
    lines.append("|-------|--:|-----:|---------:|--------:|-----:|----------:|-----------:|------:|---------|")
    lines.append(
        f"| **theory_baseline** | — | 0.8000 | 0.1137 | — | — | — | — | — | — |"
    )
    lines.append(
        f"| **WIRE-V2 pin** | — | {WIRE_PIN_MEAN} | {WIRE_PIN_GE3} | — | — | — | — | — | stored |"
    )
    ref_ge3 = out["combined_baseline_ref"]
    lines.append(
        f"| **combined ref** | — | — | **{ref_ge3}** | — | — | — | — | — | K-SIGNAL-SELECT |"
    )
    for r in sorted(results, key=lambda x: (-x["ge3_rate"], -x["mean"])):
        lam_s = "OFF" if r["lambda"] == 0 else f"{r['lambda']:g}"
        lines.append(
            f"| {r['variant_id']} | {lam_s} | {r['mean']} | {r['ge3_rate']} | {r['ge3_count']} | "
            f"{r['delta_ge3_vs_pin']:+.4f} | {r['delta_ge3_vs_combined_baseline']:+.4f} | "
            f"{r['p_value']} | {100*r['avg_pool_kill_rate']:.1f}% | {r['verdict']} |"
        )

    lines.append("\n## 3. variants (ge3 내림)")
    lines.append("| variant | λ | ge3_rate | ge3_cnt | Δcombined | p(null) | avg_kill | over_exclude |")
    lines.append("|---------|--:|---------:|--------:|----------:|--------:|---------:|:------------:|")
    for r in sorted(results, key=lambda x: (-x["ge3_rate"], -x["mean"])):
        oe = "⚠" if r["over_exclude"] else "OK"
        lines.append(
            f"| {r['variant_id']} | {r['lambda']} | {r['ge3_rate']} | {r['ge3_count']} | "
            f"{r['delta_ge3_vs_combined_baseline']:+.4f} | {r['p_value']} | "
            f"{100*r['avg_pool_kill_rate']:.1f}% | {oe} |"
        )

    lines.append("\n## 4. Verdict")
    lines.append(f"- **gate ({gate_mode}):** {out['gates_eval']['criterion']} → **{'PASS' if pass_gate else 'FAIL'}**")
    lines.append(
        f"- **baseline (λ=0):** ge3={baseline['ge3_rate']} · ref={ref_ge3}"
    )
    lines.append(
        f"- **best exclude ON:** `{best_ex['variant_id']}` ge3={best_ex['ge3_rate']} "
        f"Δcombined={best_ex['delta_ge3_vs_combined_baseline']:+.4f} p={best_ex['p_value']} "
        f"kill={100*best_ex['avg_pool_kill_rate']:.1f}%"
    )
    lines.append(f"- **recommended_next:** {out['recommended_next']}")

    lines.append("\n## 5. 팩트체크")
    lines.append("| 항목 | JSON | 보고서 |")
    lines.append("|------|------|--------|")
    lines.append(f"| n_eval | {n} | {n} |")
    lines.append(f"| baseline ge3 | {baseline['ge3_rate']} | {baseline['ge3_rate']} |")
    lines.append(f"| best ge3 | {best['ge3_rate']} | {best['ge3_rate']} |")
    lines.append(f"| pass_gate | {pass_gate} | {pass_gate} |")
    lines.append(f"| no_peek | True | True |")
    lines.append(f"| coordinator_modified | False | False |")

    text = "\n".join(lines) + "\n"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / md_path.name
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(f"wrote {md_path}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="K-EXCLUDE-SURVEY")
    ap.add_argument("--quick", action="store_true", help="QUICK tail n=200 (default)")
    ap.add_argument("--full", action="store_true", help="full 1182 eval")
    ap.add_argument("--n-eval", type=int, default=None)
    args = ap.parse_args()

    if args.full:
        n_eval_arg = FULL_N_EVAL
        sample_mode = "full"
    else:
        n_eval_arg = args.n_eval or QUICK_N_EVAL
        sample_mode = "tail"

    eval_window = resolve_eval_window(n_eval_arg, sample_mode=sample_mode)
    gate_mode = "full" if not eval_window.quick_gate else "quick"
    ref_ge3 = COMBINED_BASELINE_FULL if gate_mode == "full" else COMBINED_BASELINE_QUICK

    t0 = time.time()
    print(
        f"K-EXCLUDE-SURVEY live WF draws {eval_window.draw_start}~{eval_window.draw_end} "
        f"n_target={eval_window.n_eval_target} gate={gate_mode} seed={MC_SEED} "
        f"λ={LAMBDA_SWEEP}",
        flush=True,
    )

    n_eval, acc, mean_by_lam, avg_kill = run_survey(eval_window)

    baseline_bests = acc[0.0]
    baseline_ge3_live = round(sum(1 for x in baseline_bests if x >= 3) / n_eval, 4) if n_eval else 0.0

    results = [
        _summarize_variant(lam, acc[lam], mean_by_lam[lam], avg_kill[lam], gate_mode, baseline_ge3_live)
        for lam in LAMBDA_SWEEP
    ]
    results.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))

    baseline = next(r for r in results if r["lambda"] == 0.0)
    exclude_variants = [r for r in results if r["lambda"] > 0]
    best_exclude = max(exclude_variants, key=lambda x: (x["ge3_rate"], x["mean"])) if exclude_variants else baseline
    best_overall = max(results, key=lambda x: (x["ge3_rate"], x["mean"]))

    p_thresh = 0.05 if gate_mode == "full" else 0.15
    criterion = (
        f"exclude ON beats combined baseline AND p<{p_thresh} AND avg_kill<={OVER_EXCLUDE_THRESHOLD*100:.0f}%"
    )

    pass_candidates = [
        r for r in exclude_variants
        if r["ge3_rate"] > baseline["ge3_rate"]
        and r["p_value"] < p_thresh
        and not r["over_exclude"]
    ]
    pass_gate = len(pass_candidates) > 0

    if pass_gate:
        winner = max(pass_candidates, key=lambda x: (x["ge3_rate"], x["mean"]))
        recommended = "K-EXCLUDE-WIRE-01 (형 GO 대기)" if gate_mode == "full" else "K-EXCLUDE-SURVEY-FULL"
        verdict = f"PASS: {winner['variant_id']} ge3={winner['ge3_rate']} Δcombined={winner['delta_ge3_vs_combined_baseline']:+.4f}"
    elif best_exclude["ge3_rate"] > baseline["ge3_rate"]:
        recommended = "K-EXCLUDE-TUNE (λ·패턴 미세조정) 또는 HOLD"
        verdict = (
            f"HOLD: best exclude ge3={best_exclude['ge3_rate']} > baseline {baseline['ge3_rate']} "
            f"but p={best_exclude['p_value']} or over_exclude"
        )
    else:
        recommended = "K-ATTACK-HOLD · SELECT-WIRE HOLD"
        verdict = (
            f"FAIL: best exclude ge3={best_exclude['ge3_rate']} ≤ baseline {baseline['ge3_rate']} → HOLD"
        )

    out: dict[str, Any] = {
        "id": "K-EXCLUDE-SURVEY-FULL" if gate_mode == "full" else "K-EXCLUDE-SURVEY",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": n_eval,
        "draw_range": [eval_window.draw_start, eval_window.draw_end],
        "eval_window": {
            "n_eval_target": eval_window.n_eval_target,
            "sample_mode": eval_window.sample_mode,
            "quick_gate": eval_window.quick_gate,
        },
        "gate_mode": gate_mode,
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "null_ge3": NULL_GE3,
        "mc_seed": MC_SEED,
        "lambda_sweep": LAMBDA_SWEEP,
        "exclude_patterns": ["max_run_ge3", "sum_outside_p05_p95", "zone_skew_4plus"],
        "combined_baseline_ref": ref_ge3,
        "combined_baseline_live": baseline_ge3_live,
        "pool_sets_per_brain": POOL_SETS_PER_BRAIN,
        "selected_n": SELECT_N,
        "window_hint": {"weeks": WINDOW_WEEKS, "signal": WINDOW_SIGNAL, "alpha_ref": WINDOW_ALPHA},
        "variants": results,
        "baseline": baseline,
        "best_variant": best_overall,
        "best_exclude_on": best_exclude,
        "gates": gate_criteria_doc(),
        "pass_gate": pass_gate,
        "gates_eval": {
            "pass": pass_gate,
            "criterion": criterion,
            "over_exclude_threshold": OVER_EXCLUDE_THRESHOLD,
        },
        "no_peek": True,
        "as_of_policy": "walk_forward",
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
        "coordinator_modified": False,
    }

    out_json = OUT_JSON_FULL if gate_mode == "full" else OUT_JSON
    out_md = OUT_MD_FULL if gate_mode == "full" else OUT_MD

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_json}", flush=True)
    _write_report(out, out_md)
    print(f"verdict={verdict}", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
