# -*- coding: utf-8 -*-
"""K-STAT-TUNE — stat 파라미터 격자 (READ-ONLY).

predict_statistical.py / coordinator.py 미수정.
원본 로직을 tools 내부에서 파라미터화 재현.
set_no 쿼터: markov×3(stored) + stat×1(격자) + review×1(stored).
산출: docs/benchmarks/20260729_KSTAT_TUNE_survey.json
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
import time
from datetime import datetime
from itertools import product
from math import exp
from pathlib import Path
from typing import Any

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.filters import tier1_filter  # noqa: E402

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KSTAT_TUNE_survey.json"

D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
WIRE_GE3 = 0.1447
WIRE_MEAN = 1.7504
MC_SEED = 42
SETS_PER = 5

# current wire literals in predict_statistical.py
WIRE = {
    "recency_decay": 0.02,
    "gap_threshold": 30,  # mid; hi = mid+20 → 50 (원본)
    "hot_window": 5,
    "top_pairs": 30,
    "pair_bonus_cap": 0.5,
}

RECENCY = [0.01, 0.02, 0.05]
GAP_TH = [20, 30, 50]
HOT_WIN = [3, 5, 10]
TOP_PAIRS = [15, 30, 50]
PAIR_CAPS = [0.3, 0.5, 0.8]


def load_data(con: sqlite3.Connection) -> tuple[
    list[dict],
    dict[int, set[int]],
    dict[int, dict[str, list[tuple[int, ...]]]],
]:
    draw_rows = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1 AND ? ORDER BY draw_no",
        (D_HI,),
    ).fetchall()
    draws_all: list[dict] = [
        {
            "draw_no": int(r[0]),
            "num1": int(r[1]),
            "num2": int(r[2]),
            "num3": int(r[3]),
            "num4": int(r[4]),
            "num5": int(r[5]),
            "num6": int(r[6]),
        }
        for r in draw_rows
    ]
    actuals = {
        d["draw_no"]: {d[f"num{k}"] for k in range(1, 7)} for d in draws_all
    }

    by_dn: dict[int, dict[str, list[tuple[int, ...]]]] = {}
    for r in con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE brain_tag IN ('markov','review') AND draw_no BETWEEN 2 AND ?",
        (D_HI,),
    ):
        dn, tag = int(r[0]), str(r[1])
        by_dn.setdefault(dn, {"markov": [], "review": []})
        try:
            raw = json.loads(r[2] or "[]")
        except json.JSONDecodeError:
            continue
        nums_list: list[tuple[int, ...]] = []
        # set_no 오름 정렬 후 상단 (V2 set_no_asc와 정합)
        slotted: list[tuple[int, tuple[int, ...]]] = []
        for i, s in enumerate(raw[:5]):
            nums = tuple(sorted(int(x) for x in (s.get("nums") or [])))
            if len(nums) != 6:
                continue
            sn = int(s.get("set_no") or (i + 1))
            slotted.append((sn, nums))
        slotted.sort(key=lambda x: x[0])
        nums_list = [n for _, n in slotted]
        by_dn[dn][tag] = nums_list
    return draws_all, actuals, by_dn


def apply_feedback(weights: dict[int, float], as_of: int) -> dict[int, float]:
    out = dict(weights)
    try:
        from app.testlotto.feedback import get_feedback_summary

        fb = get_feedback_summary(last_n=20, as_of=as_of)
        if fb.get("has_feedback"):
            for trap_n in fb.get("frequent_traps", []):
                if trap_n in out:
                    out[trap_n] *= 0.8
            for hit_n in fb.get("frequent_hits", []):
                if hit_n in out:
                    out[hit_n] *= 1.15
            tot = sum(out.values())
            if tot > 0:
                out = {n: out[n] / tot for n in range(1, 46)}
    except Exception:  # noqa: BLE001
        pass
    return out


def build_stat_weights(
    draws: list[dict],
    *,
    recency_decay: float,
    gap_threshold: int,
    hot_window: int,
    top_pairs_n: int,
    pair_bonus_cap: float,
) -> tuple[dict[int, float], dict[tuple[int, int], int], dict[int, float]]:
    """원본 _statistical_predict 가중 로직 재현 (파라미터화).

    gap_threshold = mid overdue (원본 30). hi = mid+20 (원본 50).
    """
    freq: dict[int, float] = {}
    last_seen: dict[int, int] = {}
    total_draws = len(draws)

    for idx, d in enumerate(draws):
        recency_weight = exp(-recency_decay * (total_draws - 1 - idx))
        for k in ("num1", "num2", "num3", "num4", "num5", "num6"):
            n = d[k]
            freq[n] = freq.get(n, 0.0) + recency_weight
            last_seen[n] = d["draw_no"]

    for n in range(1, 46):
        if n not in freq:
            freq[n] = 0.1
        if n not in last_seen:
            last_seen[n] = 0

    latest_draw_no = draws[-1]["draw_no"] if draws else 0
    gap_mid = int(gap_threshold)
    gap_hi = int(gap_threshold) + 20
    for n in range(1, 46):
        gap = latest_draw_no - last_seen[n]
        if gap >= gap_hi:
            freq[n] *= 1.3
        elif gap >= gap_mid:
            freq[n] *= 1.15

    recent_h = draws[-hot_window:] if len(draws) >= hot_window else draws
    hot_count: dict[int, int] = {}
    for d in recent_h:
        for k in ("num1", "num2", "num3", "num4", "num5", "num6"):
            n = d[k]
            hot_count[n] = hot_count.get(n, 0) + 1
    for n, cnt in hot_count.items():
        if cnt >= 2:
            freq[n] *= 1.2

    recent_for_pairs = draws[-200:] if len(draws) >= 200 else draws
    pair_freq: dict[tuple[int, int], int] = {}
    for d in recent_for_pairs:
        nums_in_draw = sorted(
            [d["num1"], d["num2"], d["num3"], d["num4"], d["num5"], d["num6"]]
        )
        for i in range(len(nums_in_draw)):
            for j in range(i + 1, len(nums_in_draw)):
                pair = (nums_in_draw[i], nums_in_draw[j])
                pair_freq[pair] = pair_freq.get(pair, 0) + 1
    top_pairs = sorted(pair_freq.items(), key=lambda x: x[1], reverse=True)[:top_pairs_n]
    pair_bonus_nums: dict[int, float] = {}
    for (a, b), cnt in top_pairs:
        bonus = 0.05 * cnt
        pair_bonus_nums[a] = pair_bonus_nums.get(a, 0) + bonus
        pair_bonus_nums[b] = pair_bonus_nums.get(b, 0) + bonus
    for n, bonus in pair_bonus_nums.items():
        freq[n] *= 1 + min(bonus, pair_bonus_cap)

    total = sum(freq.values())
    weights = {n: freq[n] / total for n in range(1, 46)}
    as_of = int(draws[-1]["draw_no"]) if draws else 0
    weights = apply_feedback(weights, as_of)
    return weights, pair_freq, freq


def sample_stat_sets(
    weights: dict[int, float],
    pair_freq: dict[tuple[int, int], int],
    freq: dict[int, float],
    n_sets: int,
    seed: int,
) -> list[tuple[int, ...]]:
    """원본 random.choices + 동반출현 실시간 부스트 + tier1_filter."""
    random.seed(seed)
    scored: list[tuple[tuple[int, ...], float]] = []
    used: set[tuple[int, ...]] = set()
    attempts = 0
    while len(scored) < n_sets and attempts < 5000:
        attempts += 1
        nums: list[int] = []
        pool = list(range(1, 46))
        w = [weights[n] for n in pool]
        for pick_idx in range(6):
            chosen = random.choices(pool, weights=w, k=1)[0]
            nums.append(chosen)
            ci = pool.index(chosen)
            pool.pop(ci)
            w.pop(ci)
            if pick_idx < 5:
                for p_idx, p_num in enumerate(pool):
                    pair_key = (min(chosen, p_num), max(chosen, p_num))
                    p_count = pair_freq.get(pair_key, 0)
                    if p_count >= 5:
                        boost = 1 + min(p_count * 0.02, 0.4)
                        w[p_idx] *= boost
        nums_s = sorted(nums)
        if not tier1_filter(nums_s):
            continue
        key = tuple(nums_s)
        if key in used:
            continue
        used.add(key)
        # confidence (원본과 동일 식 · 정렬용)
        s = sum(nums_s)
        odd_count = sum(1 for n in nums_s if n % 2 == 1)
        ranges_hit = len({(n - 1) // 10 for n in nums_s})
        confidence = 50.0
        if 100 <= s <= 175:
            confidence += 15
        if 2 <= odd_count <= 4:
            confidence += 10
        if ranges_hit >= 4:
            confidence += 15
        elif ranges_hit >= 3:
            confidence += 8
        avg_freq = sum(freq.get(n, 0) for n in nums_s) / 6
        max_freq = max(freq.values()) if freq else 1
        confidence += (avg_freq / max_freq) * 10
        scored.append((key, confidence))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in scored]


def summarize(bests: list[int]) -> dict[str, Any]:
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


def verdict_vs_wire(ge3: float) -> str:
    delta = ge3 - WIRE_GE3
    if delta > 0.001:
        return "개선"
    if delta < -0.001:
        return "하락"
    return "동등"


def run_combos(
    draws_all: list[dict],
    actuals: dict[int, set[int]],
    by_dn: dict[int, dict[str, list[tuple[int, ...]]]],
    combos: list[dict[str, Any]],
    label: str,
) -> dict[tuple, list[int]]:
    by_no = {d["draw_no"]: d for d in draws_all}
    ordered = sorted(by_no)
    prefix: list[dict] = []
    prefix_map: dict[int, list[dict]] = {}
    for dn in ordered:
        prefix_map[dn] = list(prefix)
        prefix.append(by_no[dn])

    eval_dns = [
        dn
        for dn in range(D_LO, D_HI + 1)
        if dn in actuals
        and len((by_dn.get(dn) or {}).get("markov") or []) >= 3
        and len((by_dn.get(dn) or {}).get("review") or []) >= 1
        and len(prefix_map.get(dn) or []) >= 2
    ]
    keys = [
        (
            c["recency_decay"],
            c["gap_threshold"],
            c["hot_window"],
            c["top_pairs"],
            c["pair_bonus_cap"],
        )
        for c in combos
    ]
    acc: dict[tuple, list[int]] = {k: [] for k in keys}
    print(f"[{label}] eval_draws={len(eval_dns)} combos={len(combos)}", flush=True)

    for di, dn in enumerate(eval_dns):
        if di % 200 == 0:
            print(f"  {label} progress {di}/{len(eval_dns)} (dn={dn})", flush=True)
        hist = prefix_map[dn]
        actual = actuals[dn]
        mr = by_dn[dn]
        mk3 = mr["markov"][:3]
        rv1 = mr["review"][:1]

        for c in combos:
            key = (
                c["recency_decay"],
                c["gap_threshold"],
                c["hot_window"],
                c["top_pairs"],
                c["pair_bonus_cap"],
            )
            weights, pair_freq, freq = build_stat_weights(
                hist,
                recency_decay=c["recency_decay"],
                gap_threshold=c["gap_threshold"],
                hot_window=c["hot_window"],
                top_pairs_n=c["top_pairs"],
                pair_bonus_cap=c["pair_bonus_cap"],
            )
            # MC seed=42 · draw-scoped for reproducibility
            seed = (MC_SEED * 1_000_003 + dn) & 0xFFFFFFFF
            # param salt so different grids stay deterministic but distinct
            seed = (
                seed
                + int(c["recency_decay"] * 1000) * 7919
                + int(c["gap_threshold"]) * 104729
                + int(c["hot_window"]) * 2243
                + int(c["top_pairs"]) * 9973
                + int(c["pair_bonus_cap"] * 10) * 389
            ) & 0xFFFFFFFF
            st = sample_stat_sets(weights, pair_freq, freq, SETS_PER, seed)
            if not st:
                continue
            issued = mk3 + st[:1] + rv1
            best = max(len(set(s) & actual) for s in issued)
            acc[key].append(best)
    return acc


def rows_from_acc(
    acc: dict[tuple, list[int]],
    combos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for c in combos:
        key = (
            c["recency_decay"],
            c["gap_threshold"],
            c["hot_window"],
            c["top_pairs"],
            c["pair_bonus_cap"],
        )
        r = summarize(acc[key])
        rows.append({**c, **r})
    rows.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return rows


def enrich_top(rows: list[dict[str, Any]], k: int = 5) -> list[dict[str, Any]]:
    out = []
    for row in rows[:k]:
        ge3 = float(row["ge3_rate"])
        n = int(row["n"])
        ge3_c = int(row["ge3_count"])
        p = float(binomtest(ge3_c, n, NULL_GE3, alternative="greater").pvalue) if n else 1.0
        delta = ge3 - WIRE_GE3
        out.append(
            {
                "recency_decay": row["recency_decay"],
                "gap_threshold": row["gap_threshold"],
                "hot_window": row["hot_window"],
                "top_pairs": row.get("top_pairs"),
                "pair_bonus_cap": row.get("pair_bonus_cap"),
                "mean": row["mean"],
                "ge3_rate": row["ge3_rate"],
                "ge4_rate": row["ge4_rate"],
                "delta_ge3_vs_wire": round(delta, 4),
                "p_value": round(p, 6),
                "verdict": verdict_vs_wire(ge3),
                "n": n,
                "ge3_count": ge3_c,
            }
        )
    return out


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    draws_all, actuals, by_dn = load_data(con)
    con.close()

    # STEP1: pair fixed at wire defaults
    step1_combos = [
        {
            "recency_decay": d,
            "gap_threshold": g,
            "hot_window": h,
            "top_pairs": WIRE["top_pairs"],
            "pair_bonus_cap": WIRE["pair_bonus_cap"],
        }
        for d, g, h in product(RECENCY, GAP_TH, HOT_WIN)
    ]
    acc1 = run_combos(draws_all, actuals, by_dn, step1_combos, "STEP1")
    step1 = rows_from_acc(acc1, step1_combos)
    step2_top5 = enrich_top(step1, 5)

    best1 = step1[0]
    # STEP3: fix STEP1 best core, grid pair params
    step3_combos = [
        {
            "recency_decay": best1["recency_decay"],
            "gap_threshold": best1["gap_threshold"],
            "hot_window": best1["hot_window"],
            "top_pairs": tp,
            "pair_bonus_cap": pc,
        }
        for tp, pc in product(TOP_PAIRS, PAIR_CAPS)
    ]
    acc3 = run_combos(draws_all, actuals, by_dn, step3_combos, "STEP3")
    step3 = rows_from_acc(acc3, step3_combos)
    step3_top5 = enrich_top(step3, 5)

    # overall best = max ge3 among step1+step3
    pool = step1 + step3
    pool.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))
    best = pool[0]
    best_p_row = enrich_top([best], 1)[0]
    best_p = best_p_row["p_value"]
    best_combo = {
        "recency_decay": best["recency_decay"],
        "gap_threshold": best["gap_threshold"],
        "hot_window": best["hot_window"],
        "top_pairs": best["top_pairs"],
        "pair_bonus_cap": best["pair_bonus_cap"],
        "ge3_rate": best["ge3_rate"],
        "mean": best["mean"],
        "ge4_rate": best["ge4_rate"],
        "p_value": best_p,
        "delta_ge3_vs_wire": best_p_row["delta_ge3_vs_wire"],
        "verdict": best_p_row["verdict"],
        "source": "step3" if best in step3 or any(
            best["recency_decay"] == r["recency_decay"]
            and best["gap_threshold"] == r["gap_threshold"]
            and best["hot_window"] == r["hot_window"]
            and best["top_pairs"] == r["top_pairs"]
            and best["pair_bonus_cap"] == r["pair_bonus_cap"]
            for r in step3
        ) else "step1",
    }

    any_gt = any(r["ge3_rate"] > WIRE_GE3 for r in pool)
    pass_gate = bool(best["ge3_rate"] > WIRE_GE3 and best_p < 0.05)

    if pass_gate:
        recommended = "K-STAT-TUNE-WIRE"
        verdict = (
            f"PASS→TUNE-WIRE: best decay={best['recency_decay']} gap={best['gap_threshold']} "
            f"hot={best['hot_window']} pairs={best['top_pairs']} cap={best['pair_bonus_cap']} "
            f"ge3={best['ge3_rate']} > wire {WIRE_GE3} p={best_p}."
        )
    else:
        recommended = "K-REVIEW-TUNE"
        verdict = (
            f"FAIL: best ge3={best['ge3_rate']} ≤ wire {WIRE_GE3} "
            f"(또는 p>=0.05). → K-REVIEW-TUNE."
        )

    cur_row = next(
        (
            r
            for r in step1
            if r["recency_decay"] == WIRE["recency_decay"]
            and r["gap_threshold"] == WIRE["gap_threshold"]
            and r["hot_window"] == WIRE["hot_window"]
        ),
        None,
    )

    out = {
        "id": "K-STAT-TUNE",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": best.get("n") or 0,
        "draw_range": [D_LO, D_HI],
        "quota": {"markov": 3, "stat": 1, "review": 1},
        "mc_seed": MC_SEED,
        "sets_per_predict_brain": SETS_PER,
        "null_ge3": NULL_GE3,
        "current_wire": {
            **WIRE,
            "ge3": WIRE_GE3,
            "mean": WIRE_MEAN,
            "regen_same_params": cur_row,
            "note": (
                "wire ge3/mean = KMARKOV_WIRE_V2_verify pin. "
                "gap_threshold=mid overdue(원본30), hi=mid+20(원본50). "
                "regen은 시드고정·stored markov/review 재사용(수치 다를 수 있음)."
            ),
        },
        "step1_grid": step1,
        "step2_top5": step2_top5,
        "step3_grid": step3,
        "step3_top5": step3_top5,
        "best_combo": best_combo,
        "gates": {
            "any_ge3_gt_wire_1447": any_gt,
            "best_ge3": best["ge3_rate"],
            "best_p": best_p,
            "pass": pass_gate,
        },
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
        "code_touched": False,
        "predict_statistical_modified": False,
        "coordinator_modified": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "best_combo": best_combo,
                "gates": out["gates"],
                "recommended_next": recommended,
                "verdict": verdict,
                "step2_top5": step2_top5,
                "step3_top5": step3_top5[:3],
                "current_regen": cur_row,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
