# -*- coding: utf-8 -*-
"""K-SETCOUNT-NULL — 장수효과 vs 실력 분리 (READ-ONLY null MC).

MC seed=42. 기존 코드·DB 배선 수정 없음.
산출: docs/benchmarks/20260729_KSETCOUNT_null.json
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KSETCOUNT_null.json"
SURVEY = ROOT / "docs" / "benchmarks" / "20260729_KSETCOUNT_survey.json"

POOL_BRAINS = ("stat", "markov", "review")
D_LO, D_HI = 53, 1234
N_EVAL_TARGET = 1182
MC_TRIALS = 10000
MC_SAMPLE_DRAWS = 100
SEED = 42
RR_MEAN = 1.7428
RR_GE3 = 0.1337
ALPHA = 0.05


def load_draws_and_sets(con: sqlite3.Connection) -> tuple[
    dict[int, set[int]],
    dict[int, dict[str, list[tuple[int, ...]]]],
]:
    draws: dict[int, set[int]] = {}
    for r in con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1 AND ?",
        (D_HI,),
    ):
        draws[int(r[0])] = {int(r[i]) for i in range(1, 7)}

    by_dn: dict[int, dict[str, list[tuple[int, ...]]]] = defaultdict(
        lambda: {b: [] for b in POOL_BRAINS}
    )
    for r in con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE brain_tag IN (?,?,?) AND draw_no BETWEEN 2 AND ?",
        (*POOL_BRAINS, D_HI),
    ):
        dn, tag = int(r[0]), str(r[1])
        if tag not in POOL_BRAINS:
            continue
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
    return draws, {dn: dict(v) for dn, v in by_dn.items()}


def best_match(sets: list[tuple[int, ...]], actual: set[int]) -> int:
    if not sets:
        return 0
    return max(len(set(s) & actual) for s in sets)


def sample_draw_nos() -> list[int]:
    """균등 간격 100개 in [53, 1234]."""
    lo, hi = D_LO, D_HI
    if MC_SAMPLE_DRAWS <= 1:
        return [lo]
    step = (hi - lo) / (MC_SAMPLE_DRAWS - 1)
    return [int(round(lo + i * step)) for i in range(MC_SAMPLE_DRAWS)]


def null_mc_for_n(
    draws: dict[int, set[int]],
    sample_dns: list[int],
    n_sets: int,
    trials: int,
    rng: random.Random,
) -> dict[str, Any]:
    """각 샘플 draw에서 trials회: n_sets장 랜덤 → best matched 분포."""
    # per-trial aggregates across sample draws
    trial_means: list[float] = []
    trial_ge3: list[float] = []
    trial_ge4: list[float] = []
    # also collect all per-draw bests for overall mean/ge3
    all_bests: list[int] = []

    pool = list(range(1, 46))
    usable = [dn for dn in sample_dns if dn in draws]
    if not usable:
        return {"null_mean": 0.0, "null_ge3": 0.0, "null_ge3_std": 0.0, "null_ge4": 0.0}

    for _t in range(trials):
        bests: list[int] = []
        for dn in usable:
            actual = draws[dn]
            sets: list[tuple[int, ...]] = []
            for _ in range(n_sets):
                picks = tuple(sorted(rng.sample(pool, 6)))
                sets.append(picks)
            b = best_match(sets, actual)
            bests.append(b)
            all_bests.append(b)
        n = len(bests)
        trial_means.append(sum(bests) / n)
        trial_ge3.append(sum(1 for x in bests if x >= 3) / n)
        trial_ge4.append(sum(1 for x in bests if x >= 4) / n)

    n_all = len(all_bests)
    null_mean = sum(all_bests) / n_all
    null_ge3 = sum(1 for x in all_bests if x >= 3) / n_all
    null_ge4 = sum(1 for x in all_bests if x >= 4) / n_all
    ge3_std = statistics.pstdev(trial_ge3) if len(trial_ge3) > 1 else 0.0

    return {
        "null_mean": round(null_mean, 4),
        "null_ge3": round(null_ge3, 4),
        "null_ge3_std": round(ge3_std, 6),
        "null_ge4": round(null_ge4, 4),
        "null_mean_trial_std": round(statistics.pstdev(trial_means), 6) if len(trial_means) > 1 else 0.0,
        "n_sample_draws": len(usable),
        "mc_trials": trials,
    }


def wheel_pick(
    cands: list[tuple[tuple[int, ...], float]],
    n: int,
) -> list[tuple[int, ...]]:
    """간단 커버리지 wheel (combo_B 계수)."""
    if not cands or n <= 0:
        return []
    remaining = list(cands)
    selected: list[tuple[int, ...]] = []
    covered: set[int] = set()
    new_cov_w, score_w, avg_ov_w = 18.0, 1.0, 2.0
    while len(selected) < n and remaining:
        best_i, best_m = -1, -1e18
        for i, (nums, score) in enumerate(remaining):
            ns = set(nums)
            new_cov = len(ns - covered)
            avg_ov = (
                statistics.mean(len(ns & set(s)) for s in selected) if selected else 0.0
            )
            metric = new_cov * new_cov_w + score * score_w - avg_ov * avg_ov_w
            if metric > best_m:
                best_m, best_i = metric, i
        nums, _ = remaining.pop(best_i)
        selected.append(nums)
        covered |= set(nums)
    return selected


def eval_config(
    draws: dict[int, set[int]],
    by_dn: dict[int, dict[str, list[tuple[int, ...]]]],
    pick_fn: Callable[[dict[str, list[tuple[int, ...]]]], list[tuple[int, ...]] | None],
) -> dict[str, Any]:
    bests: list[int] = []
    for dn in range(D_LO, D_HI + 1):
        by_brain = by_dn.get(dn) or {}
        actual = draws.get(dn)
        if not actual:
            continue
        if not all(len(by_brain.get(b) or []) >= 5 for b in POOL_BRAINS):
            continue
        picked = pick_fn(by_brain)
        if not picked:
            continue
        bests.append(best_match(picked, actual))
    n = len(bests)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3": 0.0, "ge3_count": 0, "ge4": 0.0}
    ge3_c = sum(1 for x in bests if x >= 3)
    ge4_c = sum(1 for x in bests if x >= 4)
    return {
        "n": n,
        "mean": round(sum(bests) / n, 4),
        "ge3": round(ge3_c / n, 4),
        "ge3_count": ge3_c,
        "ge4": round(ge4_c / n, 4),
    }


def compare(
    label: str,
    obs: dict[str, Any],
    null: dict[str, Any],
    n_tickets: int,
) -> dict[str, Any]:
    n = int(obs["n"])
    ge3 = float(obs["ge3"])
    mean = float(obs["mean"])
    ge3_c = int(obs["ge3_count"])
    p0 = float(null["null_ge3"])
    m0 = float(null["null_mean"])
    std = float(null["null_ge3_std"]) or 1e-12
    # z: vs MC trial-std of null_ge3 (instruction). also rate-SE for note
    z_mc = (ge3 - p0) / std
    se_rate = math.sqrt(max(p0 * (1 - p0), 1e-12) / max(n, 1))
    z_rate = (ge3 - p0) / se_rate
    # one-sided greater
    bt = binomtest(ge3_c, n, p0, alternative="greater")
    p_val = float(bt.pvalue)
    verdict = "실력" if p_val < ALPHA else "장수효과"
    return {
        "label": label,
        "n_tickets": n_tickets,
        "n": n,
        "mean": mean,
        "ge3": ge3,
        "ge4": obs["ge4"],
        "null_mean": m0,
        "null_ge3": p0,
        "null_ge4": null["null_ge4"],
        "delta_ge3": round(ge3 - p0, 4),
        "delta_mean": round(mean - m0, 4),
        "z": round(z_mc, 4),
        "z_rate_se": round(z_rate, 4),
        "p": round(p_val, 6),
        "verdict": verdict,
    }


def main() -> None:
    t0 = time.time()
    trials = MC_TRIALS
    note_trials = ""

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    draws, by_dn = load_draws_and_sets(con)
    con.close()

    sample_dns = sample_draw_nos()
    rng = random.Random(SEED)

    print(f"[NULL] STEP1 MC trials={trials} sample={len(sample_dns)} seed={SEED}", flush=True)
    step1: dict[str, Any] = {}
    t_mc = time.time()
    for n_sets, key in ((5, "n5"), (10, "n10"), (15, "n15")):
        print(f"  MC n={n_sets} ...", flush=True)
        # re-seed per n for reproducibility of each block from known state
        rng_n = random.Random(SEED + n_sets)
        step1[key] = null_mc_for_n(draws, sample_dns, n_sets, trials, rng_n)
        print(f"    {step1[key]}", flush=True)
        # time gate: if first n takes >90s, shrink remaining
        if n_sets == 5 and time.time() - t_mc > 90 and trials > 1000:
            trials = 1000
            note_trials = f"n5 이후 MC_TRIALS {MC_TRIALS}→1000 (시간)"
            print(f"  WARN {note_trials}", flush=True)

    # if we shrunk mid-way, re-run n10/n15 already done at full — only shrink if we detect early
    # For simplicity: if elapsed for all three with 10k is fine, keep. Else re-run with 1k.
    elapsed_mc = time.time() - t_mc
    if elapsed_mc > 300 and trials == MC_TRIALS:
        trials = 1000
        note_trials = "MC_TRIALS 10000→1000 (시간 과다)"
        print(f"[NULL] re-run with trials=1000", flush=True)
        for n_sets, key in ((5, "n5"), (10, "n10"), (15, "n15")):
            rng_n = random.Random(SEED + n_sets)
            step1[key] = null_mc_for_n(draws, sample_dns, n_sets, trials, rng_n)

    # theoretical refs
    theory = {
        "single_E": 0.8,
        "note": "1장 E[match]=6*(6/45)=0.8 · best-of-N은 null MC로 근사",
        "ktrust_null_mc_ref": {
            "best_of_5_mean": 1.7264,
            "best_of_5_ge3": 0.1164,
            "best_of_15_mean": 2.2832,
            "best_of_15_ge3": 0.3132,
            "source": "docs/benchmarks/20260729_KTRUST_bench.json",
        },
    }

    print("[NULL] STEP2 observed configs ...", flush=True)

    def pick_mixed_wheel(n: int):
        def fn(by_brain):
            flat: list[tuple[tuple[int, ...], float]] = []
            seen: set[tuple[int, ...]] = set()
            for b in POOL_BRAINS:
                for nums in by_brain.get(b) or []:
                    if nums not in seen:
                        seen.add(nums)
                        # score proxy: confidence 대체 → set sum hash-stable
                        flat.append((nums, float(sum(nums))))
            if len(flat) < n:
                return None
            return wheel_pick(flat, n)

        return fn

    def pick_solo(brain: str, k: int = 5):
        def fn(by_brain):
            s = by_brain.get(brain) or []
            return list(s[:k]) if len(s) >= k else None

        return fn

    def pick_markov3_mix():
        def fn(by_brain):
            out: list[tuple[int, ...]] = []
            seen: set[tuple[int, ...]] = set()
            for nums in (by_brain.get("markov") or [])[:3]:
                if nums not in seen:
                    seen.add(nums)
                    out.append(nums)
            for b in ("stat", "review"):
                for nums in (by_brain.get(b) or [])[:1]:
                    if nums not in seen:
                        seen.add(nums)
                        out.append(nums)
            return out if len(out) >= 5 else (out if len(out) >= 3 else None)

        return fn

    obs_B = eval_config(draws, by_dn, pick_mixed_wheel(10))
    obs_C = eval_config(draws, by_dn, pick_mixed_wheel(15))
    obs_D = eval_config(draws, by_dn, pick_solo("markov", 5))
    obs_E = eval_config(draws, by_dn, pick_markov3_mix())
    obs_F = eval_config(draws, by_dn, pick_solo("stat", 5))

    # A: RR constants (BAYES pin) — ge3_count ≈ round(rate * n)
    n_a = obs_D["n"]  # same WF window
    ge3_a = int(round(RR_GE3 * n_a))
    obs_A = {
        "n": n_a,
        "mean": RR_MEAN,
        "ge3": RR_GE3,
        "ge3_count": ge3_a,
        "ge4": None,
        "note": "RR pin from K-ATTACK-BAYES pick_round_robin",
    }

    # Prefer survey JSON if present for B-F alignment (same numbers as report)
    if SURVEY.exists():
        sj = json.loads(SURVEY.read_text(encoding="utf-8"))
        s1, s2, s3 = sj["step1_setcount_grid"], sj["step2_brain_solo"], sj["step3_combo_grid"]

        def from_survey(mean: float, ge3: float, n: int = 1182) -> dict[str, Any]:
            return {
                "n": n,
                "mean": mean,
                "ge3": ge3,
                "ge3_count": int(round(ge3 * n)),
                "ge4": None,
                "source": "KSETCOUNT_survey",
            }

        obs_B = from_survey(s1["10"]["mean"], s1["10"]["ge3_rate"], s1["10"]["n"])
        obs_C = from_survey(s1["15"]["mean"], s1["15"]["ge3_rate"], s1["15"]["n"])
        obs_D = from_survey(s2["markov"]["mean"], s2["markov"]["ge3_rate"], s2["markov"]["n"])
        obs_E = from_survey(
            s3["combo_top1_3"]["mean"], s3["combo_top1_3"]["ge3_rate"], s3["combo_top1_3"]["n"]
        )
        obs_F = from_survey(s2["stat"]["mean"], s2["stat"]["ge3_rate"], s2["stat"]["n"])
        print("  observed: using KSETCOUNT_survey.json pins", flush=True)

    step2 = {
        "A_n5_rr": compare("A_n5_rr", obs_A, step1["n5"], 5),
        "B_n10_mixed": compare("B_n10_mixed", obs_B, step1["n10"], 10),
        "C_n15_mixed": compare("C_n15_mixed", obs_C, step1["n15"], 15),
        "D_markov5": compare("D_markov5", obs_D, step1["n5"], 5),
        "E_markov3mix2": compare("E_markov3mix2", obs_E, step1["n5"], 5),
        "F_n5_stat": compare("F_n5_stat", obs_F, step1["n5"], 5),
    }
    for k, v in step2.items():
        print(
            f"  {k}: ge3={v['ge3']} null={v['null_ge3']} Δ={v['delta_ge3']} "
            f"p={v['p']} → {v['verdict']}",
            flush=True,
        )

    # STEP3
    five_keys = ("A_n5_rr", "D_markov5", "E_markov3mix2", "F_n5_stat")
    wire_5 = [k for k in five_keys if step2[k]["verdict"] == "실력"]
    wire_10 = ["B_n10_mixed"] if step2["B_n10_mixed"]["verdict"] == "실력" else []
    wire_15 = ["C_n15_mixed"] if step2["C_n15_mixed"]["verdict"] == "실력" else []
    candidates = wire_5 + wire_10 + wire_15

    any_5 = len(wire_5) > 0
    any_10 = len(wire_10) > 0
    any_15 = len(wire_15) > 0

    if any_5:
        # prefer markov-related among 5set skills
        if "E_markov3mix2" in wire_5 or "D_markov5" in wire_5:
            recommended = "K-MARKOV-WIRE"
        elif "A_n5_rr" in wire_5:
            recommended = "K-MARKOV-WIRE"  # RR itself skill vs null → keep markov-axis label per spec
        else:
            recommended = "K-MARKOV-WIRE"
    elif any_10 or any_15:
        recommended = "K-SETCOUNT-WIRE"
    else:
        recommended = "없음"

    best_5 = None
    if five_keys:
        best_5 = max(five_keys, key=lambda k: (step2[k]["ge3"] - step2[k]["null_ge3"], -step2[k]["p"]))

    gates = {
        "any_5set_skill": any_5,
        "any_10set_skill": any_10,
        "any_15set_skill": any_15,
        "best_5set_config": best_5,
        "wire_5": wire_5,
        "wire_10_15": wire_10 + wire_15,
    }

    if recommended == "없음":
        verdict = (
            "FAIL: 전 구성 p>=0.05 · 실측≈null → 장수효과만. WIRE 금지 · HOLD."
        )
    elif recommended == "K-MARKOV-WIRE":
        verdict = (
            f"PASS→K-MARKOV-WIRE: 5장 실력={wire_5}. "
            f"10/15실력={wire_10 + wire_15} (비용↑). best_5={best_5}."
        )
    else:
        verdict = (
            f"PASS→K-SETCOUNT-WIRE: 5장 실력 없음 · 10/15={wire_10 + wire_15}. "
            f"발권비용 대비 EV 별도."
        )

    out = {
        "id": "K-SETCOUNT-NULL",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": n_a,
        "mc_trials": trials,
        "mc_sample_draws": len(sample_dns),
        "mc_seed": SEED,
        "mc_note": note_trials or None,
        "theory_ref": theory,
        "step1_null_mc": step1,
        "step2_comparison": step2,
        "step3_wire_candidates": candidates,
        "gates": gates,
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"gates": gates, "recommended_next": recommended, "verdict": verdict}, ensure_ascii=False, indent=2))
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
