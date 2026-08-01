# -*- coding: utf-8 -*-
"""K-10SET-DET-LAB-COMBO — pool10 × deterministic top-k 선별 survey (READ-ONLY live WF).

A baseline_combined(5) · B pool10_combined · C pool5_det_topk · D pool10_det_topk
coordinator·predict_*·random.choices 원본 미수정 · 1군 코드 READ-ONLY 참조만.
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

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

STRATEGIES = [
    "baseline_combined",
    "pool10_combined",
    "pool5_det_topk",
    "pool10_det_topk",
]

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

        hint = _build_hint(draws, WINDOW_WEEKS, WINDOW_SIGNAL, draw_no)
        expected_bins = _expected_bins(draws)

        pools = {
            "baseline_combined": _pool5(draws, draw_no),
            "pool10_combined": _pool10(draws, draw_no),
            "pool5_det_topk": _pool5(draws, draw_no),
            "pool10_det_topk": _pool10(draws, draw_no),
        }

        for strat in STRATEGIES:
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

    n_eval = len(acc["baseline_combined"])
    elapsed = round(time.time() - t0, 1)

    strategies_out: dict[str, Any] = {}
    best_id = "baseline_combined"
    best_ge3 = -1.0
    pass_gate = False

    for strat in STRATEGIES:
        bests = acc[strat]
        ge3_c = sum(1 for x in bests if x >= 3)
        ge4_c = sum(1 for x in bests if x >= 4)
        mean_v = sum(means[strat]) / n_eval if n_eval else 0.0
        base = enrich_metrics(ge3_c, n_eval, mean_v, gate_mode="quick")
        qp = base["ge3_rate"] > WIRE_PIN_GE3 and base["p_value"] < 0.15
        if qp:
            pass_gate = True
        if base["ge3_rate"] > best_ge3:
            best_ge3 = base["ge3_rate"]
            best_id = strat
        strategies_out[strat] = {
            **base,
            "ge4_rate": round(ge4_c / n_eval, 4) if n_eval else 0.0,
            "ge4_count": ge4_c,
            "pool_sets_per_brain": 10 if "10" in strat or strat == "pool10_combined" else 5,
            "selector": "combined" if "combined" in strat else "det_topk",
            "quick_pass_pin": qp,
        }

    if not pass_gate:
        best_id = max(
            strategies_out,
            key=lambda s: (strategies_out[s]["ge3_rate"], -strategies_out[s]["p_value"]),
        )

    out: dict[str, Any] = {
        "id": "K-10SET-DET-LAB-COMBO",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": elapsed,
        "n_eval": n_eval,
        "draw_range": [int(rows[0]["draw_no"]), int(rows[-1]["draw_no"])] if rows else [],
        "seed": MC_SEED,
        "gate_mode": "quick",
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
            "quick_pass": pass_gate,
            "quick_criteria": f"ge3 > {WIRE_PIN_GE3} AND p < 0.15",
            "criteria_doc": gate_criteria_doc(),
        },
        "pass_gate": pass_gate,
        "verdict": "PASS" if pass_gate else "FAIL",
        "recommended_next": "K-10SET-DET-LAB-FULL" if pass_gate else "K-ATTACK-HOLD",
        "db_code_write": False,
        "coordinator_modified": False,
    }
    return out


def _write_report(out: dict[str, Any]) -> None:
    n = out["n_eval"]
    lines = [
        "# K-10SET-DET-LAB-COMBO — 10pool × deterministic top-k survey",
        "",
        f"날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · **{out['verdict']}** · "
        f"seed={out['seed']} · n={n} · gate=quick",
        "",
        "## 1. 📋 선생님이 준 숙제",
        "| 항목 | 내용 |",
        "|------|------|",
        f"| **ID** | K-10SET-DET-LAB-COMBO |",
        f"| **질문** | SETS=10 pool + det top-k 선별이 pin({WIRE_PIN_GE3})을 넘는가? |",
        f"| **PASS** | best ge3 > {WIRE_PIN_GE3} AND p < 0.15 |",
        "| **금지** | coordinator·predict_* 수정 · wire |",
        "",
        "## 2. 🔧 학생이 한 일",
        "| 항목 | 값 |",
        "|------|-----|",
        "| 도구 | `tools/_k_10set_det_lab_survey.py` |",
        "| det lab | 1군 `build_weighted_topk_sets` 로직 survey 내부 복사 |",
        "| coordinator_modified | false |",
        "",
        "## 3. 📊 풀이 (§6 baseline + §7 전략)",
        "| label | ge3_rate | mean | p | Δpin |",
        "|-------|--------:|-----:|--:|-----:|",
        f"| null | {NULL_GE3} | 0.80 | — | — |",
        f"| pin | {WIRE_PIN_GE3} | {WIRE_PIN_MEAN} | — | — |",
    ]
    for sid, s in out["strategies"].items():
        lines.append(
            f"| {sid} | {s['ge3_rate']} | {s['mean']} | {s['p_value']} | {s['delta_ge3_vs_pin']:+.4f} |"
        )
    lines.extend([
        "",
        "## 4. ✅/❌ 맞은·틀린 것",
        f"- QUICK PASS (ge3>{WIRE_PIN_GE3} AND p<0.15): **{out['pass_gate']}**",
        f"- best_strategy: `{out['best_strategy']}` ge3={out['strategies'][out['best_strategy']]['ge3_rate']}",
        "",
        "## 5. 📝 복습",
        f"- recommended_next: **{out['recommended_next']}**",
        "",
        "## 6. 📎 근거",
        f"- JSON: `{OUT_JSON}`",
        f"- n_eval={n} · seed={out['seed']} · elapsed={out['elapsed_sec']}s",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print(f"K-10SET-DET-LAB-COMBO QUICK n={QUICK_N_EVAL} seed={MC_SEED}", flush=True)
    out = run_survey()
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(out)
    print(f"wrote {OUT_JSON}", flush=True)
    print(f"wrote {OUT_MD}", flush=True)
    best = out["strategies"][out["best_strategy"]]
    print(
        f"verdict={out['verdict']}: best={out['best_strategy']} ge3={best['ge3_rate']} p={best['p_value']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
