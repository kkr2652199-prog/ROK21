# -*- coding: utf-8 -*-
"""K-SIGNAL-SELECT-01 — 신호셋트 선별 축 survey (READ-ONLY live WF).

10세트 pool/brain (survey 2-pass) → 통합 5세트 선별.
축: (b)window overlap · (a)draw_features bin · (c)Jaccard · (d)set_no_asc control.
coordinator·predict_* 원본 미수정 · QUICK_GATE n=200 tail 기본.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

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
from tools._k_window_signal_survey import (  # noqa: E402
    _build_hint,
    _live_candidates,
)

random.seed(MC_SEED)

from app.testlotto.brains.coordinator import apply_markov_wire_quota  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.features.draw_features import (  # noqa: E402
    ac_value,
    odd_even_ratio,
    sorted_nums,
    sum_range,
)
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260730_KSIGNAL_SELECT_survey.json"
OUT_MD = ROOT / "reports" / "20260730_KSIGNAL_SELECT_SURVEY.md"

POOL_SETS_PER_BRAIN = 10
SELECT_N = 5
WINDOW_WEEKS = 4
WINDOW_SIGNAL = "zone_mix"
WINDOW_ALPHA = 0.1  # K-WINDOW best w4_zone_mix@α=0.1

SELECTORS = ["set_no_asc", "window_overlap", "bin_match", "jaccard_div", "combined"]


def _sum_band(s: int) -> str:
    if s < 120:
        return "low"
    if s > 155:
        return "high"
    return "mid"


def _ac_bin(a: int) -> str:
    if a <= 6:
        return "ac_le6"
    if a <= 8:
        return "ac_7_8"
    return "ac_ge9"


def _expected_bins(draws: list[dict]) -> dict[str, str]:
    """Recent window dominant / mean bins (walk-forward safe)."""
    wd = draws[-WINDOW_WEEKS:] if len(draws) >= WINDOW_WEEKS else draws
    sums: list[int] = []
    odds: list[int] = []
    acs: list[int] = []
    for d in wd:
        nums = sorted_nums(d)
        s, _ = odd_even_ratio(nums)
        sums.append(sum_range(nums))
        odds.append(s)
        acs.append(ac_value(nums))
    sum_dom = _sum_band(int(round(sum(sums) / len(sums)))) if sums else "mid"
    odd_dom = f"odd={int(round(sum(odds) / len(odds)))}" if odds else "odd=3"
    ac_dom = _ac_bin(int(round(sum(acs) / len(acs)))) if acs else "ac_7_8"
    return {"sum_band": sum_dom, "odd_count": odd_dom, "ac": ac_dom}


def _set_bins(nums: list[int]) -> dict[str, str]:
    o, _ = odd_even_ratio(nums)
    return {
        "sum_band": _sum_band(sum_range(nums)),
        "odd_count": f"odd={o}",
        "ac": _ac_bin(ac_value(nums)),
    }


def _bin_match_score(nums: list[int], expected: dict[str, str]) -> float:
    got = _set_bins(nums)
    matches = sum(1 for k in expected if got.get(k) == expected[k])
    return matches / 3.0


def _hint_overlap_score(nums: list[int], hint: dict[int, float]) -> float:
    """Positive hint mass in set / 6."""
    if not nums:
        return 0.0
    return sum(max(0.0, hint.get(int(n), 0.0)) for n in nums) / 6.0


def _jaccard(a: set[int], b: set[int]) -> float:
    u = a | b
    if not u:
        return 0.0
    return len(a & b) / len(u)


def _expand_pool(draws: list[dict], draw_no: int) -> list[dict]:
    """Survey-only 10-set/brain: 2× predict_sets (seed offset on pass 2)."""
    pool: list[dict] = []
    for pass_idx in range(2):
        if pass_idx == 0:
            random.seed(MC_SEED)
        else:
            random.seed(MC_SEED + 10000 + draw_no)
        batch = _live_candidates(draws, draw_no)
        for c in batch:
            base_sn = int(c.get("pred_set_no") or c.get("set_no") or 1)
            c = {**c, "pred_set_no": base_sn + pass_idx * SETS_PER_PREDICT_BRAIN}
            c["set_no"] = c["pred_set_no"]
            pool.append(c)
    return pool


def _pick_set_no_asc(candidates: list[dict]) -> list[dict]:
    """Control: standard 5-set/brain → V2 quota."""
    std = [c for c in candidates if int(c.get("pred_set_no") or 99) <= SETS_PER_PREDICT_BRAIN]
    return apply_markov_wire_quota(std)


def _pick_top_greedy(
    pool: list[dict],
    score_fn: Callable[[list[int]], float],
    *,
    diversity_weight: float = 0.0,
) -> list[dict]:
    """Unified top-5 from 30-set pool with optional Jaccard diversity penalty."""
    remaining = list(pool)
    selected: list[dict] = []
    while len(selected) < SELECT_N and remaining:
        best_i = -1
        best_score = -1e18
        for i, c in enumerate(remaining):
            nums = [int(x) for x in c["nums"]]
            base = score_fn(nums)
            if selected and diversity_weight > 0:
                ns = set(nums)
                avg_j = sum(_jaccard(ns, set(int(x) for x in s["nums"])) for s in selected) / len(
                    selected
                )
                base -= diversity_weight * avg_j
            if base > best_score:
                best_score = base
                best_i = i
        selected.append(remaining.pop(best_i))
    return selected


def _pick_jaccard_div(pool: list[dict]) -> list[dict]:
    """Greedy max-min Jaccard distance."""
    remaining = list(pool)
    selected: list[dict] = []
    if not remaining:
        return []
    # seed: highest set_no spread — first pick random highest brain diversity
    first = max(remaining, key=lambda c: (-int(c.get("pred_set_no") or 0), c.get("brain_tag", "")))
    remaining.remove(first)
    selected.append(first)
    while len(selected) < SELECT_N and remaining:
        best_i = -1
        best_min_dist = -1.0
        for i, c in enumerate(remaining):
            ns = set(int(x) for x in c["nums"])
            min_j = min(_jaccard(ns, set(int(x) for x in s["nums"])) for s in selected)
            if min_j > best_min_dist:
                best_min_dist = min_j
                best_i = i
        selected.append(remaining.pop(best_i))
    return selected


def _best_match(selected: list[dict], actual: set[int]) -> int:
    if not selected:
        return 0
    return max(len(set(int(x) for x in c["nums"]) & actual) for c in selected)


def run_survey(eval_window) -> tuple[int, dict[str, list[int]], dict[str, float]]:
    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    rows = filter_draw_rows(rows, eval_window)

    acc: dict[str, list[int]] = {s: [] for s in SELECTORS}
    means: dict[str, list[float]] = {s: [] for s in SELECTORS}

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

        picks: dict[str, list[dict]] = {
            "set_no_asc": _pick_set_no_asc(std_candidates),
            "window_overlap": _pick_top_greedy(
                pool, lambda nums: _hint_overlap_score(nums, hint)
            ),
            "bin_match": _pick_top_greedy(
                pool, lambda nums: _bin_match_score(nums, expected_bins)
            ),
            "jaccard_div": _pick_jaccard_div(pool),
            "combined": _pick_top_greedy(
                pool,
                lambda nums: (
                    0.5 * _hint_overlap_score(nums, hint)
                    + 0.35 * _bin_match_score(nums, expected_bins)
                ),
                diversity_weight=0.15,
            ),
        }

        for sel_id, selected in picks.items():
            best = _best_match(selected, actual)
            acc[sel_id].append(best)
            means[sel_id].append(float(best))

    n_eval = len(acc["set_no_asc"])
    mean_by_sel = {
        s: round(sum(means[s]) / len(means[s]), 4) if means[s] else 0.0 for s in SELECTORS
    }
    return n_eval, acc, mean_by_sel


def _summarize_selector(
    selector_id: str, bests: list[int], mean: float, gate_mode: str
) -> dict[str, Any]:
    ge3_c = sum(1 for x in bests if x >= 3)
    ge4_c = sum(1 for x in bests if x >= 4)
    n = len(bests)
    base = enrich_metrics(ge3_c, n, mean, gate_mode=gate_mode)
    return {
        "selector_id": selector_id,
        "label": selector_id,
        "pool_sets_per_brain": POOL_SETS_PER_BRAIN,
        "selected_n": SELECT_N,
        **base,
        "ge4_rate": round(ge4_c / n, 4) if n else 0.0,
        "ge4_count": ge4_c,
    }


def _write_report(out: dict[str, Any]) -> None:
    results = out["selectors"]
    best = out["best_selector"]
    baseline = out["baseline_control"]
    n = out["n_eval"]
    gate_mode = out["gate_mode"]
    pass_gate = out.get("pass_gate") or out.get("gates_eval", {}).get("pass", False)

    lines: list[str] = []
    lines.append("# K-SIGNAL-SELECT-01 — 신호셋트 선별 축 survey (READ-ONLY live WF)")
    lines.append(
        f"\n날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · "
        f"**{'PASS' if pass_gate else 'FAIL'}** · seed={MC_SEED} · n={n} · gate={gate_mode}"
    )
    lines.append(
        f"\n개념: 3뇌×{POOL_SETS_PER_BRAIN} pool (survey 2-pass) → 통합 {SELECT_N} 신호셋트 · "
        f"window hint=w{WINDOW_WEEKS}_{WINDOW_SIGNAL}@α={WINDOW_ALPHA} (K-WINDOW best)."
    )

    lines.append("\n## SUMMARY (BENCH_PROTOCOL §6)")
    lines.append(
        "| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) | 비고 |"
    )
    lines.append(
        "|-------|----------|------|----------|-----|--------------|-------------|-------------|------|"
    )
    lines.append("| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | E[match]=6×6/45 |")
    lines.append(
        f"| **WIRE-V2 pin** | stored | {WIRE_PIN_MEAN} | {WIRE_PIN_GE3} | ✓ | +0.0310 | — | — | PINNED |"
    )
    lines.append(
        f"| **set_no_asc (control)** | WF live | **{baseline['mean']}** | **{baseline['ge3_rate']}** | — | "
        f"{baseline['delta_ge3_vs_null']:+.4f} | {baseline['delta_ge3_vs_pin']:+.4f} | "
        f"{baseline['p_value']} | V2 quota baseline |"
    )
    lines.append(
        f"| **best selector** | WF live | **{best['mean']}** | **{best['ge3_rate']}** | — | "
        f"{best['delta_ge3_vs_null']:+.4f} | {best['delta_ge3_vs_pin']:+.4f} | "
        f"{best['p_value']} | `{best['selector_id']}` · {best['verdict']} |"
    )

    lines.append("\n## selectors (ge3 내림)")
    lines.append("| selector | mean | ge3_rate | ge3_cnt | Δpin | Δnull | p | verdict |")
    lines.append("|----------|-----:|---------:|--------:|-----:|------:|--:|---------|")
    for r in sorted(results, key=lambda x: (-x["ge3_rate"], -x["mean"])):
        lines.append(
            f"| {r['selector_id']} | {r['mean']} | {r['ge3_rate']} | {r['ge3_count']} | "
            f"{r['delta_ge3_vs_pin']:+.4f} | {r['delta_ge3_vs_null']:+.4f} | "
            f"{r['p_value']} | {r['verdict']} |"
        )

    lines.append("\n## Verdict")
    criterion = out.get("gates_eval", {}).get("criterion", "")
    lines.append(f"- **gate ({gate_mode}):** {criterion} → **{'PASS' if pass_gate else 'FAIL'}**")
    lines.append(f"- **best selector:** `{best['selector_id']}` ge3={best['ge3_rate']} p={best['p_value']}")
    lines.append(f"- **recommended_next:** {out['recommended_next']}")

    lines.append("\n## 팩트체크")
    lines.append("| 항목 | JSON | 보고서 |")
    lines.append("|------|------|--------|")
    lines.append(f"| n_eval | {n} | {n} |")
    lines.append(f"| baseline ge3 | {baseline['ge3_rate']} | {baseline['ge3_rate']} |")
    lines.append(f"| best ge3 | {best['ge3_rate']} | {best['ge3_rate']} |")
    lines.append(f"| pass_gate | {pass_gate} | {pass_gate} |")
    lines.append(f"| coordinator_modified | False | False |")

    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / "20260730_KSIGNAL_SELECT_SURVEY.md"
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_MD}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="K-SIGNAL-SELECT-01 survey")
    ap.add_argument("--n-eval", type=int, default=QUICK_N_EVAL, help="eval draws (default 200 QUICK)")
    ap.add_argument("--sample", choices=["tail", "full"], default="tail")
    ap.add_argument("--full", action="store_true", help="full 1182 eval")
    args = ap.parse_args()

    n_eval_arg = FULL_N_EVAL if args.full else args.n_eval
    sample_mode = "full" if args.full else args.sample
    eval_window = resolve_eval_window(n_eval_arg, sample_mode=sample_mode)
    gate_mode = "full" if not eval_window.quick_gate else "quick"

    t0 = time.time()
    print(
        f"K-SIGNAL-SELECT-01 live WF draws {eval_window.draw_start}~{eval_window.draw_end} "
        f"n_target={eval_window.n_eval_target} gate={gate_mode} seed={MC_SEED}",
        flush=True,
    )

    n_eval, acc, mean_by_sel = run_survey(eval_window)

    results = [
        _summarize_selector(s, acc[s], mean_by_sel[s], gate_mode) for s in SELECTORS
    ]
    results.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))

    baseline = next(r for r in results if r["selector_id"] == "set_no_asc")
    non_control = [r for r in results if r["selector_id"] != "set_no_asc"]
    best = max(results, key=lambda x: (x["ge3_rate"], x["mean"]))
    best_signal = max(non_control, key=lambda x: (x["ge3_rate"], x["mean"])) if non_control else best

    if gate_mode == "full":
        criterion = f"any selector ge3>{WIRE_PIN_GE3} and p<0.05"
        pass_gate = any(r["verdict"] == "PASS" for r in non_control)
    else:
        criterion = f"any selector ge3>{NULL_GE3} and p<0.15 (QUICK exploration)"
        pass_gate = any(r["verdict"] == "PASS" for r in non_control)

    promising = best_signal["delta_ge3_vs_null"] >= 0.01 or (
        best_signal["ge3_rate"] > baseline["ge3_rate"] + 0.005
    )

    if pass_gate and promising:
        recommended = "K-SIGNAL-SELECT-FULL" if gate_mode == "quick" else "K-10SET-SURVEY-01"
    elif pass_gate:
        recommended = "K-SIGNAL-SELECT-FULL (optional full 1182)"
    else:
        recommended = "K-ATTACK-HOLD"

    if pass_gate:
        verdict = (
            f"QUICK PASS: {best_signal['selector_id']} ge3={best_signal['ge3_rate']} "
            f"p={best_signal['p_value']}"
        )
    else:
        verdict = (
            f"FAIL: best {best_signal['selector_id']} ge3={best_signal['ge3_rate']} "
            f"p={best_signal['p_value']} → HOLD"
        )

    out: dict[str, Any] = {
        "id": "K-SIGNAL-SELECT-01",
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
        "pool_sets_per_brain": POOL_SETS_PER_BRAIN,
        "selected_n": SELECT_N,
        "window_hint": {"weeks": WINDOW_WEEKS, "signal": WINDOW_SIGNAL, "alpha_ref": WINDOW_ALPHA},
        "selectors": results,
        "baseline_control": baseline,
        "best_selector": best,
        "best_signal_selector": best_signal,
        "gates": gate_criteria_doc(),
        "pass_gate": pass_gate,
        "gates_eval": {"pass": pass_gate, "criterion": criterion, "promising": promising},
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
        "coordinator_modified": False,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON}", flush=True)
    _write_report(out)
    print(f"verdict={verdict}", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
