# -*- coding: utf-8 -*-
"""K-10SET-DET-LAB-COMBO — pool10 × deterministic top-k 선별 survey (READ-ONLY live WF).

A baseline_combined(5) · B pool10_combined · C pool5_det_topk · D pool10_det_topk
FULL: A+B only · n=1182 · `--full`
coordinator·predict_*·random.choices 원본 미수정 · 1군 코드 READ-ONLY 참조만.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

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
    SELECT_N,
    SETS_PER_PREDICT_BRAIN,
    WINDOW_SIGNAL,
    WINDOW_WEEKS,
    _best_match,
    _bin_match_score,
    _expand_pool,
    _expected_bins,
    _hint_overlap_score,
    _pick_top_greedy,
)
from tools._k_window_signal_survey import (  # noqa: E402
    _aux_composite_score,
    _build_hint,
    _live_candidates,
)

from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.filters import tier1_filter  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

random.seed(MC_SEED)

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_K10SET_DET_LAB_survey.json"
OUT_MD = ROOT / "reports" / "20260801_K10SET_DET_LAB_SURVEY.md"
OUT_JSON_FULL = ROOT / "docs" / "benchmarks" / "20260801_K10SET_DET_LAB_survey_full.json"
OUT_MD_FULL = ROOT / "reports" / "20260801_K10SET_DET_LAB_FULL.md"

STRATEGIES_ALL = [
    "baseline_combined",
    "pool10_combined",
    "pool5_det_topk",
    "pool10_det_topk",
]
STRATEGIES_FULL = ["baseline_combined", "pool10_combined"]

# 1군 deterministic_sets.py 로직 — survey 내부 lab copy (predict_* 미수정)
DET_POOL_SIZE = 18


def _build_weighted_topk_sets_lab(
    weights: dict[int, float],
    n_sets: int,
    *,
    pool_size: int = DET_POOL_SIZE,
) -> list[dict]:
    ranked = sorted(
        ((n, float(weights.get(n, 0.0))) for n in range(1, 46)),
        key=lambda x: (-x[1], x[0]),
    )
    pool = [n for n, _ in ranked[:pool_size]]
    if len(pool) < 6:
        pool = [n for n, _ in ranked[:6]]
    scored: list[tuple[float, tuple[int, ...]]] = []
    for combo in combinations(pool, 6):
        nums = sorted(combo)
        if not tier1_filter(nums):
            continue
        score = sum(weights.get(n, 0.0) for n in nums)
        scored.append((score, tuple(nums)))
    scored.sort(key=lambda x: (-x[0], x[1]))
    results: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    for score, key in scored:
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "nums": list(key),
                "confidence": round(min(score * 100 * 6, 99.9), 1),
                "brain_tag": "det_lab",
                "pred_set_no": len(results) + 1,
                "set_no": len(results) + 1,
                "det_score": score,
            }
        )
        if len(results) >= n_sets:
            break
    return results


def _number_weights_from_draws(draws: list[dict]) -> dict[int, float]:
    freq: Counter[int] = Counter()
    for d in draws[-80:]:
        for n in sorted_nums(d):
            freq[n] += 1
    if not freq:
        return {n: 1.0 / 45.0 for n in range(1, 46)}
    maxf = max(freq.values())
    return {n: freq.get(n, 0) / maxf for n in range(1, 46)}


def _pool5(draws: list[dict], draw_no: int) -> list[dict]:
    random.seed(MC_SEED)
    return _live_candidates(draws, draw_no)


def _pool10(draws: list[dict], draw_no: int) -> list[dict]:
    return _expand_pool(draws, draw_no)


def _pick_combined(
    pool: list[dict], hint: dict[int, float], expected_bins: dict[str, str]
) -> list[dict]:
    return _pick_top_greedy(
        pool,
        lambda nums: (
            0.5 * _hint_overlap_score(nums, hint)
            + 0.35 * _bin_match_score(nums, expected_bins)
        ),
        diversity_weight=0.15,
    )


def _pick_det_topk_from_pool(
    pool: list[dict], draws: list[dict], draw_no: int
) -> list[dict]:
    """Deterministic: confidence + AUX + 1군-style weight tie-break."""
    weights = _number_weights_from_draws(draws)
    scored: list[tuple[float, int, str, dict]] = []
    for c in pool:
        nums = [int(x) for x in c["nums"]]
        tag = str(c.get("brain_tag") or "")
        aux = _aux_composite_score(nums, draws, draw_no, brain_tag=tag or None)
        conf = float(c.get("confidence", 60))
        wsum = sum(weights.get(n, 0.0) for n in nums)
        score = conf * 0.4 + aux * 40.0 + wsum * 10.0
        sn = int(c.get("pred_set_no") or c.get("set_no") or 99)
        scored.append((score, sn, tag, c))
    scored.sort(key=lambda x: (-x[0], x[1], x[2]))
    selected: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    for _, _, _, c in scored:
        key = tuple(sorted(int(x) for x in c["nums"]))
        if key in seen:
            continue
        seen.add(key)
        selected.append(c)
        if len(selected) >= SELECT_N:
            break
    return selected


def _pick_det_topk_lab_sets(draws: list[dict], draw_no: int) -> list[dict]:
    """1군 build_weighted_topk_sets lab — stat 가중치 벡터로 5장 결정론 생성."""
    weights = _number_weights_from_draws(draws)
    return _build_weighted_topk_sets_lab(weights, SELECT_N)


def _strategy_pick(
    strategy: str,
    *,
    pool: list[dict],
    draws: list[dict],
    draw_no: int,
    hint: dict[int, float],
    expected_bins: dict[str, str],
) -> list[dict]:
    if strategy == "baseline_combined":
        return _pick_combined(pool, hint, expected_bins)
    if strategy == "pool10_combined":
        return _pick_combined(pool, hint, expected_bins)
    if strategy == "pool5_det_topk":
        return _pick_det_topk_from_pool(pool, draws, draw_no)
    if strategy == "pool10_det_topk":
        return _pick_det_topk_from_pool(pool, draws, draw_no)
    raise ValueError(strategy)


def _empty_tier() -> dict[str, int]:
    return {"r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0, "n_sets": 0}


def _prediction_rank_tier(matched_count: int, bonus_matched: int) -> int:
    bm = 1 if bonus_matched else 0
    if matched_count == 6:
        return 1
    if matched_count == 5 and bm:
        return 2
    if matched_count == 5:
        return 3
    if matched_count == 4:
        return 4
    if matched_count == 3:
        return 5
    return 0


def _record_tier(acc: dict[str, int], tier: int) -> None:
    if 1 <= tier <= 5:
        acc[f"r{tier}"] += 1


def run_survey(*, full: bool = False) -> dict[str, Any]:
    strategies = STRATEGIES_FULL if full else STRATEGIES_ALL
    gate_mode = "full" if full else "quick"
    survey_id = "K-10SET-DET-LAB-FULL" if full else "K-10SET-DET-LAB-COMBO"

    init_lotto_db()
    n_target = FULL_N_EVAL if full else QUICK_N_EVAL
    eval_window = resolve_eval_window(
        n_eval=n_target,
        draw_start=DRAW_START,
        draw_end=DRAW_END,
        sample_mode="full" if full else "tail",
    )
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    rows = filter_draw_rows(rows, eval_window)

    acc: dict[str, list[int]] = {s: [] for s in strategies}
    means: dict[str, list[float]] = {s: [] for s in strategies}
    tier_acc: dict[str, dict[str, int]] = {s: _empty_tier() for s in strategies}

    t0 = time.time()
    for ri, row in enumerate(rows):
        if ri % 50 == 0:
            print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        bonus = int(row.get("bonus") or 0)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        hint = _build_hint(draws, WINDOW_WEEKS, WINDOW_SIGNAL, draw_no)
        expected_bins = _expected_bins(draws)

        pools = {
            "baseline_combined": _pool5(draws, draw_no),
            "pool10_combined": _pool10(draws, draw_no),
            "pool5_det_topk": _pool5(draws, draw_no),
            "pool10_det_topk": _pool10(draws, draw_no),
        }

        for strat in strategies:
            selected = _strategy_pick(
                strat,
                pool=pools[strat],
                draws=draws,
                draw_no=draw_no,
                hint=hint,
                expected_bins=expected_bins,
            )
            best = _best_match(selected, actual)
            acc[strat].append(best)
            means[strat].append(float(best))
            for c in selected:
                nums = {int(x) for x in c["nums"]}
                mc = len(nums & actual)
                bm = 1 if bonus in nums else 0
                tier = _prediction_rank_tier(mc, bm)
                _record_tier(tier_acc[strat], tier)
                tier_acc[strat]["n_sets"] += 1

    n_eval = len(acc["baseline_combined"])
    elapsed = round(time.time() - t0, 1)

    strategies_out: dict[str, Any] = {}
    best_id = "pool10_combined"
    best_ge3 = -1.0
    pass_gate = False

    for strat in strategies:
        bests = acc[strat]
        ge3_c = sum(1 for x in bests if x >= 3)
        ge4_c = sum(1 for x in bests if x >= 4)
        mean_v = sum(means[strat]) / n_eval if n_eval else 0.0
        base = enrich_metrics(ge3_c, n_eval, mean_v, gate_mode=gate_mode)
        if full:
            pg = base["ge3_rate"] > WIRE_PIN_GE3 and base["p_value"] < 0.05
        else:
            pg = base["ge3_rate"] > WIRE_PIN_GE3 and base["p_value"] < 0.15
        if strat == "pool10_combined" and pg:
            pass_gate = True
        if base["ge3_rate"] > best_ge3:
            best_ge3 = base["ge3_rate"]
            best_id = strat
        ts = tier_acc[strat]
        strategies_out[strat] = {
            **base,
            "ge4_rate": round(ge4_c / n_eval, 4) if n_eval else 0.0,
            "ge4_count": ge4_c,
            "pool_sets_per_brain": 10 if "10" in strat or strat == "pool10_combined" else 5,
            "selector": "combined" if "combined" in strat else "det_topk",
            "quick_pass_pin": pg if not full else None,
            "full_pass_pin": pg if full else None,
            "tier": {k: ts[k] for k in ("r1", "r2", "r3", "r4", "r5", "n_sets")},
        }

    if full:
        pass_gate = strategies_out["pool10_combined"].get("full_pass_pin", False)
        best_id = "pool10_combined" if pass_gate else max(
            strategies_out,
            key=lambda s: strategies_out[s]["ge3_rate"],
        )
    elif not pass_gate:
        best_id = max(
            strategies_out,
            key=lambda s: (strategies_out[s]["ge3_rate"], -strategies_out[s]["p_value"]),
        )

    out: dict[str, Any] = {
        "id": survey_id,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": elapsed,
        "n_eval": n_eval,
        "draw_range": [int(rows[0]["draw_no"]), int(rows[-1]["draw_no"])] if rows else [],
        "seed": MC_SEED,
        "gate_mode": gate_mode,
        "wire_pin_ge3": WIRE_PIN_GE3,
        "null_ge3": NULL_GE3,
        "exclude_params": {
            "det_pool_size": DET_POOL_SIZE,
            "sets_per_brain_5": 5,
            "sets_per_brain_10": 10,
            "lab_source": "1군 deterministic_sets.py (READ-ONLY logic copy in survey)",
        },
        "strategies": strategies_out,
        "best_strategy": best_id,
        "gates": {
            "quick_pass": pass_gate if not full else False,
            "full_pass": pass_gate if full else False,
            "full_criteria": f"pool10_combined ge3 > {WIRE_PIN_GE3} AND p < 0.05",
            "quick_criteria": f"ge3 > {WIRE_PIN_GE3} AND p < 0.15",
            "criteria_doc": gate_criteria_doc(),
        },
        "pass_gate": pass_gate,
        "verdict": "PASS" if pass_gate else "FAIL",
        "recommended_next": (
            "K-10SET-DET-LAB-WIRE (형 GO 대기)"
            if pass_gate and full
            else ("K-10SET-DET-LAB-FULL" if pass_gate and not full else "K-ATTACK-HOLD")
        ),
        "db_code_write": False,
        "coordinator_modified": False,
    }
    return out


def _write_report(out: dict[str, Any], md_path: Path) -> None:
    n = out["n_eval"]
    full = out["gate_mode"] == "full"
    title_id = out["id"]
    lines = [
        f"# {title_id} — 10pool combined survey ({'전체1182' if full else 'QUICK200'})",
        "",
        f"날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · **{out['verdict']}** · "
        f"seed={out['seed']} · n={n} · gate={out['gate_mode']}",
        "",
        "## 1. 📋 선생님이 준 숙제",
        "| 항목 | 내용 |",
        "|------|------|",
        f"| **ID** | {title_id} |",
        f"| **질문** | pool10_combined FULL pin({WIRE_PIN_GE3}) 초과? |"
        if full
        else f"| **질문** | SETS=10 pool + 선별 pin({WIRE_PIN_GE3}) 초과? |",
        f"| **PASS** | pool10 ge3 > {WIRE_PIN_GE3} AND p < {'0.05' if full else '0.15'} |",
        "| **금지** | coordinator·predict_* · wire |",
        "",
        "## 2. 🔧 학생이 한 일",
        "| 항목 | 값 |",
        "|------|-----|",
        "| 도구 | `tools/_k_10set_det_lab_survey.py` |",
        f"| mode | {'--full n=1182' if full else 'QUICK n=200'} |",
        "| coordinator_modified | false |",
        "",
        "## 3. 📊 풀이",
        "| label | ge3_rate | mean | p | Δpin |",
        "|-------|--------:|-----:|--:|-----:|",
        f"| null | {NULL_GE3} | 0.80 | — | — |",
        f"| pin | {WIRE_PIN_GE3} | {WIRE_PIN_MEAN} | — | — |",
    ]
    for sid, s in out["strategies"].items():
        lines.append(
            f"| {sid} | {s['ge3_rate']} | {s['mean']} | {s['p_value']} | {s['delta_ge3_vs_pin']:+.4f} |"
        )
    if full:
        lines.extend(["", "## tier 피벗 (BENCH §7 · pool10_combined)"])
        ts = out["strategies"]["pool10_combined"]["tier"]
        ge3_s = ts["r3"] + ts["r4"] + ts["r5"]
        lines.extend([
            "| scope | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |",
            "|-------|----|----|----|----|----|----|--------|",
            f"| pool10_combined | {ts['r1']} | {ts['r2']} | {ts['r3']} | {ts['r4']} | {ts['r5']} | {ge3_s} | {ts['n_sets']} |",
        ])
    lines.extend([
        "",
        "## 4. ✅/❌ 맞은·틀린 것",
        f"- pass_gate: **{out['pass_gate']}** · best `{out['best_strategy']}`",
        "",
        "## 5. 📝 복습",
        f"- SELECT-FULL 전례: QUICK 0.145 → FULL 0.1218 · **과장 해석 금지**",
        f"- recommended_next: **{out['recommended_next']}**",
        "",
        "## 6. 📎 근거",
        f"- JSON: `{OUT_JSON_FULL if full else OUT_JSON}`",
        f"- n={n} · seed={out['seed']} · elapsed={out['elapsed_sec']}s",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="FULL n=1182 draw 53~1234")
    ap.add_argument("--n-eval", type=int, default=None)
    ap.add_argument("--seed", type=int, default=MC_SEED)
    args = ap.parse_args()
    if args.seed != MC_SEED:
        random.seed(args.seed)

    full = args.full or (args.n_eval is not None and args.n_eval >= FULL_N_EVAL)
    label = "FULL" if full else "QUICK"
    n_show = FULL_N_EVAL if full else QUICK_N_EVAL
    print(f"K-10SET-DET-LAB {label} n={n_show} seed={args.seed}", flush=True)

    out = run_survey(full=full)
    if full:
        OUT_JSON_FULL.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_report(out, OUT_MD_FULL)
        print(f"wrote {OUT_JSON_FULL}", flush=True)
        print(f"wrote {OUT_MD_FULL}", flush=True)
    else:
        OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_report(out, OUT_MD)
        print(f"wrote {OUT_JSON}", flush=True)
        print(f"wrote {OUT_MD}", flush=True)

    best = out["strategies"][out["best_strategy"]]
    print(
        f"verdict={out['verdict']}: pool10 ge3={out['strategies']['pool10_combined']['ge3_rate']} "
        f"p={out['strategies']['pool10_combined']['p_value']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
