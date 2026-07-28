# -*- coding: utf-8 -*-
"""K-MARKOV-TUNE — markov 파라미터 격자 (READ-ONLY).

predict_markov.py 미수정. build_transition_matrix / markov_random_walk 호출만.
set_no 쿼터(markov×3+stat×1+review×1) 유지.
산출: docs/benchmarks/20260729_KMARKOV_TUNE_survey.json
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
import time
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.filters import tier1_filter  # noqa: E402
from app.testlotto.predict_markov import (  # noqa: E402
    build_transition_matrix,
    markov_random_walk,
)

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KMARKOV_TUNE_survey.json"

D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
WIRE_GE3 = 0.1447
WIRE_MEAN = 1.7504
WIRE = {"decay": 0.02, "steps": 80, "top_candidates": 25}

DECAYS = [0.01, 0.02, 0.05]
STEPS = [50, 80, 120]
TOPS = [20, 25, 35]


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
        "WHERE brain_tag IN ('stat','review') AND draw_no BETWEEN 2 AND ?",
        (D_HI,),
    ):
        dn, tag = int(r[0]), str(r[1])
        by_dn.setdefault(dn, {"stat": [], "review": []})
        try:
            raw = json.loads(r[2] or "[]")
        except json.JSONDecodeError:
            continue
        nums_list: list[tuple[int, ...]] = []
        for s in raw[:5]:
            nums = tuple(sorted(int(x) for x in (s.get("nums") or [])))
            if len(nums) == 6:
                nums_list.append(nums)
        by_dn[dn][tag] = nums_list
    return draws_all, actuals, by_dn


def draws_before(draws_all: list[dict], target: int) -> list[dict]:
    return [d for d in draws_all if d["draw_no"] < target]


def apply_feedback(visit: dict[int, float], as_of: int) -> dict[int, float]:
    out = dict(visit)
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
    except Exception:  # noqa: BLE001
        pass
    return out


def sets_from_visit(
    visit: dict[int, float],
    top_candidates: int,
    n_sets: int,
    seed: int,
) -> list[tuple[int, ...]]:
    random.seed(seed)
    top = sorted(visit.items(), key=lambda x: x[1], reverse=True)[:top_candidates]
    cand_nums = [n for n, _ in top]
    cand_w = [c for _, c in top]
    results: list[tuple[int, ...]] = []
    used: set[tuple[int, ...]] = set()
    attempts = 0
    while len(results) < n_sets and attempts < 5000:
        attempts += 1
        if len(cand_nums) >= 6:
            pool = cand_nums[:]
            w = cand_w[:]
            nums: list[int] = []
            for _ in range(6):
                chosen = random.choices(pool, weights=w, k=1)[0]
                nums.append(chosen)
                ci = pool.index(chosen)
                pool.pop(ci)
                w.pop(ci)
        else:
            nums = random.sample(range(1, 46), 6)
        nums = sorted(nums)
        if not tier1_filter(nums):
            continue
        key = tuple(nums)
        if key in used:
            continue
        used.add(key)
        results.append(key)
    return results


def run_grid(
    draws_all: list[dict],
    actuals: dict[int, set[int]],
    by_dn: dict[int, dict[str, list[tuple[int, ...]]]],
) -> dict[tuple[float, int, int], list[int]]:
    """return combo -> list of best matches."""
    combos = list(product(DECAYS, STEPS, TOPS))
    acc: dict[tuple[float, int, int], list[int]] = {c: [] for c in combos}

    # prefix hist by index for speed
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
        and len((by_dn.get(dn) or {}).get("stat") or []) >= 1
        and len((by_dn.get(dn) or {}).get("review") or []) >= 1
        and len(prefix_map.get(dn) or []) >= 2
    ]
    print(f"[TUNE] eval_draws={len(eval_dns)} combos={len(combos)}", flush=True)

    for di, dn in enumerate(eval_dns):
        if di % 200 == 0:
            print(f"  draw progress {di}/{len(eval_dns)} (dn={dn})", flush=True)
        hist = prefix_map[dn]
        actual = actuals[dn]
        sr = by_dn[dn]
        last = hist[-1]
        start = [last[f"num{k}"] for k in range(1, 7)]
        as_of = int(last["draw_no"])

        for decay in DECAYS:
            matrix = build_transition_matrix(hist, decay=decay)
            for steps in STEPS:
                seed_walk = (dn * 2654435761 + int(decay * 1000) * 7919 + steps * 104729) & 0xFFFFFFFF
                random.seed(seed_walk)
                visit_raw = markov_random_walk(matrix, start, steps=steps)
                visit = apply_feedback(
                    {k: float(v) for k, v in visit_raw.items()}, as_of
                )
                for top in TOPS:
                    seed_set = (seed_walk + top * 2243) & 0xFFFFFFFF
                    mk = sets_from_visit(visit, top, 5, seed_set)
                    if len(mk) < 3:
                        continue
                    issued = mk[:3] + sr["stat"][:1] + sr["review"][:1]
                    best = max(len(set(s) & actual) for s in issued)
                    acc[(decay, steps, top)].append(best)
    return acc


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


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    draws_all, actuals, by_dn = load_data(con)
    con.close()

    acc = run_grid(draws_all, actuals, by_dn)

    step1: list[dict[str, Any]] = []
    for decay, steps, top in product(DECAYS, STEPS, TOPS):
        r = summarize(acc[(decay, steps, top)])
        step1.append(
            {
                "decay": decay,
                "steps": steps,
                "top_candidates": top,
                "mean": r["mean"],
                "ge3_rate": r["ge3_rate"],
                "ge4_rate": r["ge4_rate"],
                "n": r["n"],
                "ge3_count": r["ge3_count"],
            }
        )

    step1.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))
    for rank, row in enumerate(step1, 1):
        row["rank"] = rank

    top5 = []
    for row in step1[:5]:
        ge3 = float(row["ge3_rate"])
        n = int(row["n"])
        ge3_c = int(row["ge3_count"])
        p = float(binomtest(ge3_c, n, NULL_GE3, alternative="greater").pvalue) if n else 1.0
        delta = ge3 - WIRE_GE3
        if delta > 0.001:
            verdict = "개선"
        elif delta < -0.001:
            verdict = "하락"
        else:
            verdict = "동등"
        top5.append(
            {
                "decay": row["decay"],
                "steps": row["steps"],
                "top_candidates": row["top_candidates"],
                "mean": row["mean"],
                "ge3_rate": row["ge3_rate"],
                "ge4_rate": row["ge4_rate"],
                "delta_ge3_vs_wire": round(delta, 4),
                "p_value": round(p, 6),
                "verdict": verdict,
                "n": n,
            }
        )

    best = step1[0]
    best_p = top5[0]["p_value"] if top5 else 1.0
    best_combo = {
        "decay": best["decay"],
        "steps": best["steps"],
        "top_candidates": best["top_candidates"],
        "ge3_rate": best["ge3_rate"],
        "mean": best["mean"],
        "ge4_rate": best["ge4_rate"],
        "p_value": best_p,
    }

    any_gt = any(r["ge3_rate"] > WIRE_GE3 for r in step1)
    pass_gate = bool(best["ge3_rate"] > WIRE_GE3 and best_p < 0.05)

    if pass_gate:
        recommended = "K-MARKOV-TUNE-WIRE"
        verdict = (
            f"PASS→TUNE-WIRE: best decay={best['decay']} steps={best['steps']} "
            f"top={best['top_candidates']} ge3={best['ge3_rate']} > wire {WIRE_GE3} "
            f"p={best_p}."
        )
    else:
        recommended = "K-ATTACK-HOLD"
        verdict = (
            f"FAIL: best ge3={best['ge3_rate']} ≤ wire {WIRE_GE3} "
            f"(또는 p>=0.05). 현재 배선(0.02/80/25) 유지 · HOLD."
        )

    cur_row = next(
        (
            r
            for r in step1
            if r["decay"] == WIRE["decay"]
            and r["steps"] == WIRE["steps"]
            and r["top_candidates"] == WIRE["top_candidates"]
        ),
        None,
    )

    out = {
        "id": "K-MARKOV-TUNE",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": best.get("n") or 0,
        "draw_range": [D_LO, D_HI],
        "current_wire": {
            **WIRE,
            "ge3": WIRE_GE3,
            "mean": WIRE_MEAN,
            "regen_same_params": cur_row,
            "note": "wire ge3=brain_review E pin · regen은 시드고정 재생성(수치 다를 수 있음)",
        },
        "step1_grid": step1,
        "step2_top5": top5,
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
                "top5": top5,
                "current_regen": cur_row,
                "top10": step1[:10],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
