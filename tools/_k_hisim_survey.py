# -*- coding: utf-8 -*-
"""K-HISIM-SURVEY — 고차원 구조 유사도 역추적 (READ-ONLY).

analog_service.py 미수정 · find_analogs / predict_from_analogs 참조만.
산출: docs/benchmarks/20260729_KHISIM_survey.json
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KHISIM_survey.json"

HISIM_NORM = {
    "sum": 270,
    "odd": 6,
    "low": 6,
    "mid": 6,
    "hi": 6,
    "ac": 10,
    "consec": 3,
    "pair_top3": 3,
    "gap_mean": 200,
    "gap_max": 1234,
    "carry": 6,
    "end_spread": 10,
    "sum_hi": 1,
}
DIMS = list(HISIM_NORM.keys())
RR_MEAN = 1.7428
RR_GE3 = 0.1337
D_LO, D_HI = 53, 1234  # n_eval≈1182


def summarize(ms: list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3_rate": 0.0, "ge3": 0, "delta_vs_rr": 0.0}
    ge3 = sum(1 for x in ms if x >= 3)
    mean = sum(ms) / n
    return {
        "n": n,
        "mean": round(mean, 4),
        "ge3": ge3,
        "ge3_rate": round(ge3 / n, 4),
        "delta_vs_rr": round(mean - RR_MEAN, 4),
    }


def load_draws() -> list[dict]:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1 AND ? ORDER BY draw_no",
        (D_HI,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def _pair_top3_count(nums: list[int], top_pairs: list[tuple[int, int]]) -> int:
    s = set(nums)
    hit = 0
    for a, b in top_pairs:
        if a in s and b in s:
            hit += 1
    return hit


def hisim_vec(
    nums: list[int],
    *,
    prev_nums: list[int] | None,
    gaps: dict[int, int],
    top_pairs: list[tuple[int, int]],
) -> list[float]:
    from app.testlotto.features.draw_features import ac_value, consecutive_pairs

    odd = sum(1 for n in nums if n % 2 == 1)
    low = sum(1 for n in nums if 1 <= n <= 15)
    mid = sum(1 for n in nums if 16 <= n <= 30)
    hi = sum(1 for n in nums if 31 <= n <= 45)
    sm = sum(nums)
    gvals = [gaps.get(n, 0) for n in nums]
    gap_mean = sum(gvals) / 6.0 if gvals else 0.0
    gap_max = max(gvals) if gvals else 0.0
    carry = len(set(nums) & set(prev_nums)) if prev_nums else 0
    end_spread = len({n % 10 for n in nums})
    raw = {
        "sum": sm,
        "odd": odd,
        "low": low,
        "mid": mid,
        "hi": hi,
        "ac": ac_value(nums),
        "consec": consecutive_pairs(nums),
        "pair_top3": _pair_top3_count(nums, top_pairs),
        "gap_mean": gap_mean,
        "gap_max": min(gap_max, HISIM_NORM["gap_max"]),
        "carry": carry,
        "end_spread": end_spread,
        "sum_hi": 1.0 if sm >= 138 else 0.0,
    }
    return [raw[k] / float(HISIM_NORM[k]) for k in DIMS]


def hisim_score_vecs(
    va: list[float],
    vb: list[float],
    nums_a: list[int],
    nums_b: list[int],
    *,
    w_struct: float,
) -> float:
    l1 = sum(abs(x - y) for x, y in zip(va, vb))
    struct = max(0.0, 1.0 - l1 / len(DIMS))
    inter = len(set(nums_a) & set(nums_b))
    jacc = inter / 6.0
    wj = 1.0 - w_struct
    return w_struct * struct + wj * jacc


def find_analogs_hisim(
    base_nums: list[int],
    base_vec: list[float],
    past_items: list[tuple[int, list[int], list[float]]],
    *,
    top_k: int = 15,
    w_struct: float = 0.80,
    min_score: float = 0.60,
) -> list[dict[str, Any]]:
    cands: list[dict[str, Any]] = []
    for dn, nums, vec in past_items:
        sc = hisim_score_vecs(base_vec, vec, base_nums, nums, w_struct=w_struct)
        if sc < min_score:
            continue
        cands.append(
            {
                "draw_no": dn,
                "nums": nums,
                "overlap": len(set(base_nums) & set(nums)),
                "score": round(sc, 4),
            }
        )
    cands.sort(key=lambda x: (-x["score"], -x["overlap"], -x["draw_no"]))
    return cands[:top_k]


def main() -> None:
    from app.testlotto.analog_service import (
        draw_nums,
        find_analogs,
        matched_count,
        predict_from_analogs,
    )
    from app.testlotto.features.draw_features import build_number_gaps, build_pair_freq

    t0 = time.perf_counter()
    draws = load_draws()
    draw_by_no = {int(d["draw_no"]): d for d in draws}
    ordered = [int(d["draw_no"]) for d in draws]

    # precompute per-draw: nums, vec (as_of = that draw, past-only features)
    print("precompute hisim vectors…")
    nums_by: dict[int, list[int]] = {}
    vec_by: dict[int, list[float]] = {}
    for i, dn in enumerate(ordered):
        nums = draw_nums(draw_by_no[dn])
        nums_by[dn] = nums
        past = [draw_by_no[x] for x in ordered[:i]]  # draw_no < dn
        if not past:
            continue
        prev_nums = nums_by.get(dn - 1)
        gaps = build_number_gaps(past)
        top_pairs = [p for p, _ in build_pair_freq(past, window=100).most_common(3)]
        vec_by[dn] = hisim_vec(
            nums, prev_nums=prev_nums, gaps=gaps, top_pairs=top_pairs
        )

    def eval_methods(w_struct: float, *, with_orig: bool) -> dict[str, list[int]]:
        buckets = {
            "hisim_freq": [],
            "hisim_weighted": [],
            "hisim_chain8": [],
        }
        if with_orig:
            buckets["orig_chain8"] = []

        for dn in ordered:
            if dn < D_LO or dn > D_HI:
                continue
            base_no = dn - 1
            if base_no not in vec_by or base_no not in nums_by:
                continue
            base_nums = nums_by[base_no]
            base_vec = vec_by[base_no]
            past_items = [
                (x, nums_by[x], vec_by[x])
                for x in ordered
                if x < base_no and x in vec_by
            ]
            if len(past_items) < 20:
                continue

            analogs_h = find_analogs_hisim(
                base_nums, base_vec, past_items, top_k=15, w_struct=w_struct
            )
            if not analogs_h:
                continue

            actual = nums_by[dn]
            for method, key in (
                ("M_freq", "hisim_freq"),
                ("M_weighted", "hisim_weighted"),
                ("M_chain8", "hisim_chain8"),
            ):
                pred = predict_from_analogs(
                    base_nums, analogs_h, draw_by_no, method, target_draw_no=dn
                )
                buckets[key].append(matched_count(pred, actual))

            if with_orig:
                past_rows = [draw_by_no[x] for x in ordered if x < base_no]
                analogs_o = find_analogs(base_nums, past_rows, top_k=15)
                if not analogs_o:
                    continue
                pred_o = predict_from_analogs(
                    base_nums,
                    analogs_o,
                    draw_by_no,
                    "M_chain8",
                    target_draw_no=dn,
                )
                buckets["orig_chain8"].append(matched_count(pred_o, actual))
        return buckets

    print("STEP3 w_struct=0.80…")
    b80 = eval_methods(0.80, with_orig=True)
    step3 = {k: summarize(v) for k, v in b80.items()}
    step3["round_robin"] = {
        "mean": RR_MEAN,
        "ge3_rate": RR_GE3,
        "n": None,
        "delta_vs_rr": 0.0,
    }

    print("STEP4 w_struct grid…")
    grid: dict[str, Any] = {}
    for w in (0.60, 0.70, 0.80, 0.90):
        if abs(w - 0.80) < 1e-9:
            grid[f"{w:.2f}"] = {
                "mean": step3["hisim_weighted"]["mean"],
                "ge3_rate": step3["hisim_weighted"]["ge3_rate"],
                "n": step3["hisim_weighted"]["n"],
            }
            continue
        print(f"  w={w}…")
        bw = eval_methods(w, with_orig=False)
        s = summarize(bw["hisim_weighted"])
        grid[f"{w:.2f}"] = {
            "mean": s["mean"],
            "ge3_rate": s["ge3_rate"],
            "n": s["n"],
        }

    best_w = max(grid, key=lambda k: (grid[k]["mean"], grid[k]["ge3_rate"]))
    grid["best_w"] = float(best_w)

    methods = ("hisim_freq", "hisim_weighted", "hisim_chain8", "orig_chain8")
    best_m = max(methods, key=lambda m: (step3[m]["mean"], step3[m]["ge3_rate"]))
    any_delta = any(step3[m]["delta_vs_rr"] > 0 for m in methods)
    best_gt_rr = step3[best_m]["mean"] > RR_MEAN
    best_ge3 = step3[best_m]["ge3_rate"] > RR_GE3

    if any_delta:
        recommended = "K-HISIM-WIRE"
        verdict = "유망"
        if best_ge3:
            verdict = "유망·우선배선후보"
    else:
        recommended = "없음"
        verdict = "관측종료"

    n_eval = step3["hisim_weighted"]["n"]
    out = {
        "id": "K-HISIM-SURVEY",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "n_eval": n_eval,
        "elapsed_sec": round(time.perf_counter() - t0, 1),
        "hisim_norm": HISIM_NORM,
        "step3_comparison": step3,
        "step4_w_struct_grid": grid,
        "gates": {
            "any_method_delta_gt0": any_delta,
            "best_mean_gt_rr_1742": best_gt_rr,
            "best_ge3_gt_rr_1337": best_ge3,
            "best_method": best_m,
        },
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
        "note": "analog_service 미수정 · hisim만 신규 점수",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "n_eval": n_eval,
                "step3_means": {m: step3[m]["mean"] for m in methods},
                "deltas": {m: step3[m]["delta_vs_rr"] for m in methods},
                "best_w": best_w,
                "grid": {k: grid[k] for k in grid if k != "best_w"},
                "recommended": recommended,
                "verdict": verdict,
                "sec": out["elapsed_sec"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
