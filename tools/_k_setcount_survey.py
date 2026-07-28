# -*- coding: utf-8 -*-
"""K-SETCOUNT-SURVEY — 세트 수 확장·뇌 단독 격자 (READ-ONLY).

predict_brain7.py 미수정. wheel combo_B 계수만 재사용.
풀 = testlotto_brain_review 3뇌×5세트 (최대 15).
산출: docs/benchmarks/20260729_KSETCOUNT_survey.json
"""
from __future__ import annotations

import json
import sqlite3
import statistics
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KSETCOUNT_survey.json"

POOL_BRAINS = ("stat", "markov", "review")
MIN_POOL_SETS = 15
RR_MEAN = 1.7428
RR_GE3 = 0.1337
D_LO, D_HI = 53, 1234
# COVER best: combo_B
NEW_COV_W, SCORE_W, AVG_OV_W = 18.0, 1.0, 2.0
N_SETS_GRID = (5, 10, 15, 20)


def summarize(ms: list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3_rate": 0.0, "ge4_rate": 0.0}
    ge3 = sum(1 for x in ms if x >= 3)
    ge4 = sum(1 for x in ms if x >= 4)
    return {
        "n": n,
        "mean": round(sum(ms) / n, 4),
        "ge3": ge3,
        "ge3_rate": round(ge3 / n, 4),
        "ge4": ge4,
        "ge4_rate": round(ge4 / n, 4),
    }


def wheel_pick(
    cands: list[tuple[tuple[int, ...], float, int]],
    n: int,
    new_cov_w: float = NEW_COV_W,
    score_w: float = SCORE_W,
    avg_ov_w: float = AVG_OV_W,
) -> list[tuple[tuple[int, ...], float, int]]:
    if not cands or n <= 0:
        return []
    remaining = list(cands)
    selected: list[tuple[tuple[int, ...], float, int]] = []
    covered: set[int] = set()
    while len(selected) < n and remaining:
        best_i = -1
        best_metric = -1e18
        for i, (nums, score, _ov) in enumerate(remaining):
            ns = set(nums)
            new_cov = len(ns - covered)
            if selected:
                avg_ov = statistics.mean(len(ns & set(s)) for s, _, _ in selected)
            else:
                avg_ov = 0.0
            metric = new_cov * new_cov_w + score * score_w - avg_ov * avg_ov_w
            if metric > best_metric:
                best_metric = metric
                best_i = i
        pick = remaining.pop(best_i)
        selected.append(pick)
        covered |= set(pick[0])
    return selected


def best_match(sets: list[tuple[int, ...]], actual: set[int]) -> int:
    if not sets:
        return 0
    return max(len(set(s) & actual) for s in sets)


def union_size(sets: list[tuple[int, ...]]) -> int:
    u: set[int] = set()
    for s in sets:
        u |= set(s)
    return len(u)


def load_all(con: sqlite3.Connection) -> tuple[
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
        dn = int(r[0])
        tag = str(r[1])
        if tag not in POOL_BRAINS:
            continue
        try:
            sets = json.loads(r[2] or "[]")
        except json.JSONDecodeError:
            continue
        nums_list: list[tuple[int, ...]] = []
        for s in sets[:5]:
            nums = tuple(sorted(int(x) for x in (s.get("nums") or [])))
            if len(nums) == 6:
                nums_list.append(nums)
        by_dn[dn][tag] = nums_list
    return draws, {dn: dict(v) for dn, v in by_dn.items()}


class RelTracker:
    def __init__(self) -> None:
        self.pick = {b: 0 for b in POOL_BRAINS}
        self.win = {b: 0 for b in POOL_BRAINS}
        self._done: set[int] = set()

    def ingest(self, dn: int, by_brain: dict[str, list[tuple[int, ...]]], actual: set[int]) -> None:
        if dn in self._done or not actual:
            return
        for tag in POOL_BRAINS:
            s: set[int] = set()
            for nums in by_brain.get(tag) or []:
                s |= set(nums)
            self.pick[tag] += len(s)
            self.win[tag] += sum(1 for n in s if n in actual)
        self._done.add(dn)

    def rel(self) -> dict[str, float]:
        return {b: (self.win[b] + 1) / (self.pick[b] + 2) for b in POOL_BRAINS}


def set_score(nums: tuple[int, ...], weights: dict[int, float]) -> float:
    return float(sum(weights.get(x, 0.0) for x in nums))


def flat_presence_weights(
    by_brain: dict[str, list[tuple[int, ...]]],
    rel: dict[str, float],
) -> dict[int, float]:
    pres: dict[int, set[str]] = defaultdict(set)
    for tag, sets in by_brain.items():
        for nums in sets:
            for n in nums:
                pres[n].add(tag)
    out: dict[int, float] = {}
    for n, brains in pres.items():
        k = len(brains)
        mean_rel = sum(rel.get(b, 0.0) for b in brains) / k
        out[n] = k * mean_rel
    return out


def to_cands(
    by_brain: dict[str, list[tuple[int, ...]]],
    weights: dict[int, float],
) -> list[tuple[tuple[int, ...], float, int]]:
    """unique sets with (nums, f1_score, max_ov vs other brain sets)."""
    flat: list[tuple[str, tuple[int, ...]]] = []
    for tag, sets in by_brain.items():
        for nums in sets:
            flat.append((tag, nums))
    seen: set[tuple[int, ...]] = set()
    cands: list[tuple[tuple[int, ...], float, int]] = []
    for tag, nums in flat:
        if nums in seen:
            continue
        seen.add(nums)
        ov = max(
            (len(set(nums) & set(s)) for t, s in flat if not (t == tag and s == nums)),
            default=0,
        )
        cands.append((nums, set_score(nums, weights), ov))
    return cands


def eval_best(
    draws: dict[int, set[int]],
    by_dn: dict[int, dict[str, list[tuple[int, ...]]]],
    pick_fn,
) -> dict[str, Any]:
    """pick_fn(by_brain, rel) -> list[tuple[int,...]] or None to skip draw."""
    rel_tr = RelTracker()
    bests: list[int] = []
    unions: list[int] = []
    for dn in range(2, D_HI + 1):
        by_brain = by_dn.get(dn) or {}
        actual = draws.get(dn)
        nsets = sum(len(by_brain.get(b) or []) for b in POOL_BRAINS)
        ready = all(len(by_brain.get(b) or []) >= 5 for b in POOL_BRAINS)
        if actual and ready and dn >= D_LO:
            rel = rel_tr.rel()
            picked = pick_fn(by_brain, rel)
            if picked is not None and len(picked) > 0:
                bests.append(best_match(picked, actual))
                unions.append(union_size(picked))
        if actual and nsets >= MIN_POOL_SETS:
            rel_tr.ingest(dn, by_brain, actual)
    s = summarize(bests)
    s["union_size"] = round(sum(unions) / len(unions), 4) if unions else 0.0
    return s


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    draws, by_dn = load_all(con)
    con.close()

    # ── STEP1: n_sets grid via wheel on brain pool ──
    print("[K-SETCOUNT] STEP1 setcount grid ...", flush=True)
    step1: dict[str, Any] = {}
    for n_sets in N_SETS_GRID:
        if n_sets > 15:
            step1[str(n_sets)] = {
                "mean": None,
                "ge3_rate": None,
                "ge4_rate": None,
                "union_size": None,
                "n": 0,
                "note": "풀 부족(brain_review 최대 15세트) · 스킵",
                "skipped": True,
            }
            print(f"  n={n_sets} SKIP (pool max 15)", flush=True)
            continue

        def make_picker(n: int):
            def pick_fn(by_brain, rel):
                w = flat_presence_weights(by_brain, rel)
                cands = to_cands(by_brain, w)
                if len(cands) < n:
                    return None
                sel = wheel_pick(cands, n)
                return [s[0] for s in sel]

            return pick_fn

        r = eval_best(draws, by_dn, make_picker(n_sets))
        step1[str(n_sets)] = {
            "mean": r["mean"],
            "ge3_rate": r["ge3_rate"],
            "ge4_rate": r["ge4_rate"],
            "union_size": r["union_size"],
            "n": r["n"],
            "skipped": False,
        }
        print(
            f"  n={n_sets} mean={r['mean']} ge3={r['ge3_rate']} "
            f"ge4={r['ge4_rate']} union={r['union_size']}",
            flush=True,
        )

    # ── STEP2: brain solo / mixed15 ──
    print("[K-SETCOUNT] STEP2 brain solo ...", flush=True)
    step2: dict[str, Any] = {}

    for brain in POOL_BRAINS:

        def solo_picker(by_brain, rel, b=brain):
            sets = by_brain.get(b) or []
            return list(sets) if len(sets) >= 5 else None

        r = eval_best(draws, by_dn, solo_picker)
        step2[brain] = {"mean": r["mean"], "ge3_rate": r["ge3_rate"], "ge4_rate": r["ge4_rate"], "n": r["n"]}
        print(f"  {brain} mean={r['mean']} ge3={r['ge3_rate']}", flush=True)

    def mixed15(by_brain, rel):
        out: list[tuple[int, ...]] = []
        seen: set[tuple[int, ...]] = set()
        for b in POOL_BRAINS:
            for nums in by_brain.get(b) or []:
                if nums not in seen:
                    seen.add(nums)
                    out.append(nums)
        return out if len(out) >= 15 else (out if len(out) >= 5 else None)

    r15 = eval_best(draws, by_dn, mixed15)
    step2["mixed_15"] = {
        "mean": r15["mean"],
        "ge3_rate": r15["ge3_rate"],
        "ge4_rate": r15["ge4_rate"],
        "union_size": r15["union_size"],
        "n": r15["n"],
    }
    print(f"  mixed_15 mean={r15['mean']} ge3={r15['ge3_rate']}", flush=True)

    best_solo = max(POOL_BRAINS, key=lambda b: (step2[b]["ge3_rate"], step2[b]["mean"]))
    step2["best_solo_brain"] = best_solo

    # ── STEP3: combos around best solo ──
    print(f"[K-SETCOUNT] STEP3 combos (best={best_solo}) ...", flush=True)
    others = [b for b in POOL_BRAINS if b != best_solo]

    def take(sets: list[tuple[int, ...]], k: int) -> list[tuple[int, ...]]:
        return list(sets[:k])

    def combo_top1_5(by_brain, rel):
        s = by_brain.get(best_solo) or []
        return take(s, 5) if len(s) >= 5 else None

    def combo_top1_3(by_brain, rel):
        # best 3 + each other 1
        out: list[tuple[int, ...]] = []
        seen: set[tuple[int, ...]] = set()
        for nums in take(by_brain.get(best_solo) or [], 3):
            if nums not in seen:
                seen.add(nums)
                out.append(nums)
        for b in others:
            for nums in take(by_brain.get(b) or [], 1):
                if nums not in seen:
                    seen.add(nums)
                    out.append(nums)
        return out if len(out) >= 3 else None

    def combo_balanced(by_brain, rel):
        return mixed15(by_brain, rel)

    step3: dict[str, Any] = {}
    configs = {
        "combo_top1_5": (combo_top1_5, f"{best_solo}×5"),
        "combo_top1_3": (combo_top1_3, f"{best_solo}×3 + {others[0]}×1 + {others[1]}×1"),
        "combo_balanced": (combo_balanced, "3×5"),
    }
    for name, (fn, cfg) in configs.items():
        r = eval_best(draws, by_dn, fn)
        step3[name] = {
            "config": cfg,
            "mean": r["mean"],
            "ge3_rate": r["ge3_rate"],
            "ge4_rate": r["ge4_rate"],
            "n": r["n"],
        }
        print(f"  {name} ({cfg}) mean={r['mean']} ge3={r['ge3_rate']}", flush=True)

    # ── gates / verdict ──
    ge3_vals: list[tuple[str, float, float]] = []  # label, ge3, mean
    for k, v in step1.items():
        if not v.get("skipped") and v.get("ge3_rate") is not None:
            ge3_vals.append((f"n={k}", float(v["ge3_rate"]), float(v["mean"])))
    for b in POOL_BRAINS:
        ge3_vals.append((f"solo_{b}", step2[b]["ge3_rate"], step2[b]["mean"]))
    ge3_vals.append(("mixed_15", step2["mixed_15"]["ge3_rate"], step2["mixed_15"]["mean"]))
    for name, v in step3.items():
        ge3_vals.append((name, v["ge3_rate"], v["mean"]))

    any_ge3 = any(g > RR_GE3 for _, g, _ in ge3_vals)
    any_mean = any(m > RR_MEAN for _, _, m in ge3_vals)
    best_label, best_g, best_m = max(ge3_vals, key=lambda x: (x[1], x[2]))

    step1_pass = any(
        (not v.get("skipped") and v.get("ge3_rate") is not None and v["ge3_rate"] > RR_GE3)
        for v in step1.values()
    )
    step2_solo_pass = any(step2[b]["ge3_rate"] > RR_GE3 for b in POOL_BRAINS)
    step3_pass = any(v["ge3_rate"] > RR_GE3 for v in step3.values())

    if step1_pass:
        recommended = "K-SETCOUNT-WIRE"
    elif step2_solo_pass or step3_pass:
        recommended = "K-BRAIN-SOLO-WIRE"
    else:
        recommended = "없음"

    # best_n from step1 non-skipped
    best_n = None
    best_n_g = -1.0
    for k, v in step1.items():
        if v.get("skipped") or v.get("ge3_rate") is None:
            continue
        if (v["ge3_rate"], v["mean"]) > (best_n_g, -1):
            best_n_g = v["ge3_rate"]
            best_n = int(k)

    best_combo = max(step3.keys(), key=lambda n: (step3[n]["ge3_rate"], step3[n]["mean"]))

    gates = {
        "any_ge3_gt_rr_1337": any_ge3,
        "any_mean_gt_rr_1742": any_mean,
        "step1_ge3_pass": step1_pass,
        "step2_solo_ge3_pass": step2_solo_pass,
        "step3_ge3_pass": step3_pass,
        "best_n": best_n,
        "best_combo": best_combo,
        "best_overall": best_label,
        "best_overall_ge3": best_g,
        "best_overall_mean": best_m,
    }

    if recommended == "없음":
        verdict = (
            f"FAIL: 전 격자 ge3≤RR({RR_GE3}). best={best_label} "
            f"ge3={best_g} mean={best_m}."
        )
    else:
        verdict = (
            f"PASS→{recommended}: best={best_label} ge3={best_g} mean={best_m}. "
            f"step1={step1_pass} solo={step2_solo_pass} combo={step3_pass}. "
            f"주의: best-of-N↑는 발권수 효과(K-08·null MC) 가능."
        )

    out = {
        "id": "K-SETCOUNT-SURVEY",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": step1.get("5", {}).get("n") or step2.get(best_solo, {}).get("n") or 0,
        "draw_range": [D_LO, D_HI],
        "pool_brains": list(POOL_BRAINS),
        "wheel_fixed": {
            "combo": "B",
            "new_cov_w": NEW_COV_W,
            "score_w": SCORE_W,
            "avg_ov_w": AVG_OV_W,
            "note": "COVER best · brain_review 15세트 후보에 wheel 적용(F1 재생성 없음)",
        },
        "baseline_rr": {"mean": RR_MEAN, "ge3_rate": RR_GE3},
        "step1_setcount_grid": step1,
        "step2_brain_solo": step2,
        "step3_combo_grid": step3,
        "gates": gates,
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "gates": gates,
        "recommended_next": recommended,
        "verdict": verdict,
        "step1": step1,
        "step2": step2,
        "step3": step3,
    }, ensure_ascii=False, indent=2))
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
