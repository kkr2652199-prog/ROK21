# -*- coding: utf-8 -*-
"""K-COVER-SURVEY — F1_V2_STRICT _wheel_pick / WHEEL_POOL 격자 (READ-ONLY).

predict_brain7.py 미수정. 동일 로직을 tools 내부 재구현.
testlotto 3뇌(stat/markov/review) · brain_review 5세트 풀.
산출: docs/benchmarks/20260729_KCOVER_survey.json
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
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KCOVER_survey.json"

POOL_BRAINS = ("stat", "markov", "review")
MIN_POOL_SETS = 15
SETS_TO_PICK = 5
COPY_OVERLAP = 5
F1_MAX_ATTEMPTS = 40
F1_SEED_MULT = 2654435761
POP_PENALTY = 1.5
SUM_CENTER = 138
STRICT_REFILL_ATTEMPTS = 60

RR_MEAN = 1.7428
RR_GE3 = 0.1337
D_LO, D_HI = 53, 1234  # n_eval≈1182

WHEEL_COMBOS: dict[str, tuple[float, float, float]] = {
    "A": (12.0, 1.0, 4.0),
    "B": (18.0, 1.0, 2.0),
    "C": (24.0, 0.5, 1.0),
    "D": (12.0, 1.0, 8.0),
    "E": (15.0, 1.0, 3.0),
}
POOL_SIZES = (15, 25, 40, 60)


def spearman(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3 or n != len(ys):
        return 0.0

    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx = sum(rx) / n
    my = sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx < 1e-12 or dy < 1e-12:
        return 0.0
    return num / (dx * dy)


def summarize(ms: list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3_rate": 0.0}
    ge3 = sum(1 for x in ms if x >= 3)
    return {
        "n": n,
        "mean": round(sum(ms) / n, 4),
        "ge3": ge3,
        "ge3_rate": round(ge3 / n, 4),
    }


# ── F1 helpers (predict_brain7 재구현 · 파라미터화) ───────────────


def _union_presence(
    flat: list[tuple[str, tuple[int, ...]]],
) -> dict[int, set[str]]:
    by_brain: dict[str, set[int]] = defaultdict(set)
    for tag, nums in flat:
        by_brain[tag] |= set(nums)
    pres: dict[int, set[str]] = defaultdict(set)
    for tag, s in by_brain.items():
        for n in s:
            pres[n].add(tag)
    return dict(pres)


def _f1_weights(pres: dict[int, set[str]], rel: dict[str, float]) -> dict[int, float]:
    out: dict[int, float] = {}
    for n, brains in pres.items():
        if not brains:
            continue
        k = len(brains)
        mean_rel = sum(rel.get(b, 0.0) for b in brains) / k
        out[n] = k * mean_rel
    return out


def _weighted_sample6(weights: dict[int, float], rng: random.Random) -> tuple[int, ...]:
    pool = list(weights.items())
    picked: list[int] = []
    for _ in range(6):
        if not pool:
            break
        total = sum(w for _, w in pool)
        if total <= 0:
            rest = [n for n, _ in pool]
            rng.shuffle(rest)
            picked.extend(rest[: 6 - len(picked)])
            break
        r = rng.random() * total
        acc = 0.0
        for i, (n, w) in enumerate(pool):
            acc += w
            if r <= acc:
                picked.append(n)
                pool.pop(i)
                break
    return tuple(sorted(picked[:6]))


def _max_single_overlap(cand: tuple[int, ...], flat: list[tuple[str, tuple[int, ...]]]) -> int:
    return max((len(set(cand) & set(s)) for _, s in flat), default=0)


def _popularity_score(nums: tuple[int, ...]) -> float:
    s = sorted(nums)
    consec = sum(1 for i in range(1, 6) if s[i] == s[i - 1] + 1)
    low31 = sum(1 for n in nums if n <= 31)
    total = sum(nums)
    sum_pop = max(0.0, 1.0 - abs(total - SUM_CENTER) / 40.0)
    return consec * 2.0 + (low31 / 6.0) * 1.5 + sum_pop


def generate_sets_with_weights(
    flat: list[tuple[str, tuple[int, ...]]],
    weights: dict[int, float],
    seed: int,
    n: int,
    copy_filter: bool = True,
) -> list[tuple[tuple[int, ...], float, int]]:
    if len(weights) < 6:
        return []
    rng = random.Random(seed)
    out: list[tuple[tuple[int, ...], float, int]] = []
    seen: set[tuple[int, ...]] = set()
    for _ in range(n):
        best = None
        best_ov = 99
        for _ in range(F1_MAX_ATTEMPTS):
            cand = _weighted_sample6(weights, rng)
            if len(set(cand)) < 6 or cand in seen:
                continue
            ov = _max_single_overlap(cand, flat)
            if not copy_filter or ov < COPY_OVERLAP:
                best, best_ov = cand, ov
                break
            if ov < best_ov:
                best, best_ov = cand, ov
        if best is None:
            continue
        score = sum(weights.get(x, 0.0) for x in best)
        out.append((best, score, best_ov))
        seen.add(best)
    return out


def _generate_popavoid_sets(
    flat: list[tuple[str, tuple[int, ...]]],
    weights: dict[int, float],
    seed: int,
    n: int,
) -> list[tuple[tuple[int, ...], float, int]]:
    if len(weights) < 6:
        return []
    rng = random.Random(seed)
    out: list[tuple[tuple[int, ...], float, int]] = []
    seen: set[tuple[int, ...]] = set()
    for _ in range(n):
        best_cand = None
        best_score = -1e18
        best_ov = 99
        for _ in range(F1_MAX_ATTEMPTS):
            cand = _weighted_sample6(dict(weights), rng)
            if len(set(cand)) < 6 or cand in seen:
                continue
            ov = _max_single_overlap(cand, flat)
            if ov >= COPY_OVERLAP and ov >= best_ov:
                continue
            f1_sc = sum(weights.get(x, 0.0) for x in cand)
            adj = f1_sc - POP_PENALTY * _popularity_score(cand)
            if adj > best_score or (best_cand is None and ov < best_ov):
                best_score = adj
                best_cand = cand
                best_ov = ov
        if best_cand is None:
            continue
        f1_sc = sum(weights.get(x, 0.0) for x in best_cand)
        out.append((best_cand, f1_sc, best_ov))
        seen.add(best_cand)
    return out


def wheel_pick(
    cands: list[tuple[tuple[int, ...], float, int]],
    n: int,
    new_cov_w: float,
    score_w: float,
    avg_ov_w: float,
) -> list[tuple[tuple[int, ...], float, int]]:
    """커버리지 greedy — 계수 파라미터화 (원본 new_cov*12 + score - avg_ov*4)."""
    if not cands:
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


def generate_f1_v2_strict(
    flat: list[tuple[str, tuple[int, ...]]],
    rel: dict[str, float],
    seed: int,
    *,
    new_cov_w: float,
    score_w: float,
    avg_ov_w: float,
    pool_size: int,
    n: int = SETS_TO_PICK,
) -> list[tuple[tuple[int, ...], float, int]]:
    pres = _union_presence(flat)
    if len(pres) < 6:
        return []
    weights = _f1_weights(pres, rel)

    pop_raw = _generate_popavoid_sets(flat, weights, seed, pool_size)
    f1_pool = generate_sets_with_weights(
        flat, weights, seed, pool_size, copy_filter=True,
    )
    by_nums: dict[tuple[int, ...], tuple[tuple[int, ...], float, int]] = {}
    for s in pop_raw + f1_pool:
        if s[2] < COPY_OVERLAP:
            by_nums[s[0]] = s
    cands = list(by_nums.values())

    selected = (
        wheel_pick(cands, n, new_cov_w, score_w, avg_ov_w) if cands else []
    )
    selected = [s for s in selected if s[2] < COPY_OVERLAP]
    seen = {s[0] for s in selected}

    remaining = [s for s in cands if s[0] not in seen]
    while len(selected) < n and remaining:
        add = wheel_pick(remaining, 1, new_cov_w, score_w, avg_ov_w)
        if not add:
            break
        pick = add[0]
        if pick[2] >= COPY_OVERLAP or pick[0] in seen:
            remaining = [s for s in remaining if s[0] != pick[0]]
            continue
        selected.append(pick)
        seen.add(pick[0])
        remaining = [s for s in remaining if s[0] not in seen]

    rs = seed
    for attempt in range(STRICT_REFILL_ATTEMPTS):
        if len(selected) >= n:
            break
        rs = (rs + 7919 + attempt) & 0xFFFFFFFF
        extra = generate_sets_with_weights(flat, weights, rs, 1, copy_filter=True)
        for s in extra:
            if s[2] < COPY_OVERLAP and s[0] not in seen:
                selected.append(s)
                seen.add(s[0])
                break

    return [s for s in selected if s[2] < COPY_OVERLAP][:n]


# ── data load ────────────────────────────────────────────────────


def load_all(con: sqlite3.Connection) -> tuple[
    dict[int, set[int]],
    dict[int, list[tuple[str, tuple[int, ...]]]],
]:
    draws: dict[int, set[int]] = {}
    for r in con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1 AND ?",
        (D_HI,),
    ):
        draws[int(r[0])] = {int(r[i]) for i in range(1, 7)}

    flat_by: dict[int, list[tuple[str, tuple[int, ...]]]] = defaultdict(list)
    for r in con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE brain_tag IN (?,?,?) AND draw_no BETWEEN 2 AND ?",
        (*POOL_BRAINS, D_HI),
    ):
        dn = int(r[0])
        tag = str(r[1])
        try:
            sets = json.loads(r[2] or "[]")
        except json.JSONDecodeError:
            continue
        for s in sets[:5]:
            nums = tuple(sorted(int(x) for x in (s.get("nums") or [])))
            if len(nums) == 6:
                flat_by[dn].append((tag, nums))
    return draws, dict(flat_by)


class RelTracker:
    """walk-forward 번호 정밀도 — target 미만만 누적."""

    def __init__(self) -> None:
        self.pick = {b: 0 for b in POOL_BRAINS}
        self.win = {b: 0 for b in POOL_BRAINS}
        self._done: set[int] = set()

    def ingest(self, dn: int, flat: list[tuple[str, tuple[int, ...]]], actual: set[int]) -> None:
        if dn in self._done or not actual:
            return
        by_brain: dict[str, set[int]] = defaultdict(set)
        for tag, nums in flat:
            by_brain[tag] |= set(nums)
        for tag in POOL_BRAINS:
            s = by_brain.get(tag, set())
            self.pick[tag] += len(s)
            self.win[tag] += sum(1 for n in s if n in actual)
        self._done.add(dn)

    def rel(self) -> dict[str, float]:
        return {b: (self.win[b] + 1) / (self.pick[b] + 2) for b in POOL_BRAINS}


def eval_sets(
    sets: list[tuple[tuple[int, ...], float, int]],
    actual: set[int],
) -> tuple[int, int, float]:
    """return (best_matched, union_size, mean_matched)."""
    if not sets:
        return 0, 0, 0.0
    matches = [len(set(nums) & actual) for nums, _, _ in sets]
    union: set[int] = set()
    for nums, _, _ in sets:
        union |= set(nums)
    return max(matches), len(union), sum(matches) / len(matches)


def run_grid(
    draws: dict[int, set[int]],
    flat_by: dict[int, list[tuple[str, tuple[int, ...]]]],
    new_cov_w: float,
    score_w: float,
    avg_ov_w: float,
    pool_size: int,
) -> dict[str, Any]:
    rel_tr = RelTracker()
    bests: list[int] = []
    unions: list[int] = []
    means: list[float] = []
    pairs_u: list[float] = []
    pairs_m: list[float] = []

    for dn in range(2, D_HI + 1):
        flat = flat_by.get(dn) or []
        actual = draws.get(dn)
        if actual and len(flat) >= MIN_POOL_SETS and dn >= D_LO:
            # reliability: only past draws (already ingested)
            rel = rel_tr.rel()
            seed = (dn * F1_SEED_MULT) & 0xFFFFFFFF
            picked = generate_f1_v2_strict(
                flat,
                rel,
                seed,
                new_cov_w=new_cov_w,
                score_w=score_w,
                avg_ov_w=avg_ov_w,
                pool_size=pool_size,
            )
            if len(picked) >= SETS_TO_PICK:
                best, usz, mmean = eval_sets(picked, actual)
                bests.append(best)
                unions.append(usz)
                means.append(mmean)
                pairs_u.append(float(usz))
                pairs_m.append(float(best))

        # after eval: ingest this draw for future reliability (no peek)
        if actual and len(flat) >= MIN_POOL_SETS:
            rel_tr.ingest(dn, flat, actual)

    s = summarize(bests)
    return {
        **s,
        "mean_union_size": round(sum(unions) / len(unions), 4) if unions else 0.0,
        "mean_matched_allsets": round(sum(means) / len(means), 4) if means else 0.0,
        "union_sizes": unions,
        "best_matches": bests,
        "spearman_union_vs_best": round(spearman(pairs_u, pairs_m), 4) if len(pairs_u) >= 3 else 0.0,
    }


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    draws, flat_by = load_all(con)
    con.close()

    print("[K-COVER] STEP1 baseline combo A pool=25 ...", flush=True)
    base = run_grid(draws, flat_by, 12.0, 1.0, 4.0, 25)
    step1 = {
        "mean_union_size": base["mean_union_size"],
        "mean_matched": base["mean"],
        "mean_matched_allsets": base["mean_matched_allsets"],
        "ge3_rate": base["ge3_rate"],
        "n": base["n"],
        "note": "best-of-5 among F1_V2_STRICT wheel picks · pool=brain_review 3×5",
    }
    print(
        f"  n={base['n']} union={base['mean_union_size']} "
        f"mean={base['mean']} ge3={base['ge3_rate']}",
        flush=True,
    )

    print("[K-COVER] STEP2 wheel grid ...", flush=True)
    step2: dict[str, Any] = {}
    best_combo = "A"
    best_ge3 = -1.0
    best_mean = -1.0
    for name, (nc, sw, ao) in WHEEL_COMBOS.items():
        print(f"  combo {name} nc={nc} sw={sw} ao={ao} ...", flush=True)
        r = run_grid(draws, flat_by, nc, sw, ao, 25)
        step2[name] = {
            "new_cov_w": nc,
            "score_w": sw,
            "avg_ov_w": ao,
            "mean": r["mean"],
            "ge3_rate": r["ge3_rate"],
            "union_size": r["mean_union_size"],
            "n": r["n"],
        }
        print(
            f"    mean={r['mean']} ge3={r['ge3_rate']} union={r['mean_union_size']}",
            flush=True,
        )
        # best: ge3 first, then mean
        if (r["ge3_rate"], r["mean"]) > (best_ge3, best_mean):
            best_ge3 = r["ge3_rate"]
            best_mean = r["mean"]
            best_combo = name
    step2["best_combo"] = best_combo
    bc_w = WHEEL_COMBOS[best_combo]

    print(f"[K-COVER] STEP3 pool grid (combo={best_combo}) ...", flush=True)
    step3: dict[str, Any] = {}
    best_pool = 25
    best_p_ge3 = -1.0
    best_p_mean = -1.0
    for ps in POOL_SIZES:
        print(f"  pool={ps} ...", flush=True)
        r = run_grid(draws, flat_by, bc_w[0], bc_w[1], bc_w[2], ps)
        step3[str(ps)] = {
            "mean": r["mean"],
            "ge3_rate": r["ge3_rate"],
            "union_size": r["mean_union_size"],
            "n": r["n"],
        }
        print(
            f"    mean={r['mean']} ge3={r['ge3_rate']} union={r['mean_union_size']}",
            flush=True,
        )
        if (r["ge3_rate"], r["mean"]) > (best_p_ge3, best_p_mean):
            best_p_ge3 = r["ge3_rate"]
            best_p_mean = r["mean"]
            best_pool = ps
    step3["best_pool"] = best_pool
    step3["fixed_combo"] = best_combo

    # STEP4: coverage corr from baseline A
    sp = base["spearman_union_vs_best"]
    step4 = {
        "spearman_r": sp,
        "note": "union_size vs matched_count (best-of-5) · combo A pool 25",
        "n": base["n"],
    }
    print(f"[K-COVER] STEP4 spearman_r={sp}", flush=True)

    any_ge3 = any(
        step2[k]["ge3_rate"] > RR_GE3 for k in WHEEL_COMBOS
    ) or any(step3[str(p)]["ge3_rate"] > RR_GE3 for p in POOL_SIZES)
    any_mean = any(
        step2[k]["mean"] > RR_MEAN for k in WHEEL_COMBOS
    ) or any(step3[str(p)]["mean"] > RR_MEAN for p in POOL_SIZES)
    corr_gt = sp > 0.03

    gates = {
        "any_combo_ge3_gt_rr": any_ge3,
        "any_combo_mean_gt_rr": any_mean,
        "coverage_corr_gt0": corr_gt,
        "rr_mean": RR_MEAN,
        "rr_ge3": RR_GE3,
    }

    if any_ge3:
        recommended = "K-COVER-WIRE"
        verdict = (
            f"PASS: ge3>{RR_GE3} 달성 (best={best_combo}/pool{best_pool} "
            f"ge3={best_p_ge3}). mean>RR={any_mean} corr={sp}."
        )
    elif any_mean or corr_gt:
        recommended = "K-COVER-TUNE"
        verdict = (
            f"ge3≤RR({RR_GE3}) but mean>RR={any_mean} or corr>0.03={corr_gt}. "
            f"best={best_combo} ge3={step2[best_combo]['ge3_rate']} "
            f"mean={step2[best_combo]['mean']} · corr={sp}. TUNE 후보."
        )
    else:
        recommended = "없음"
        verdict = (
            f"관측종료: wheel 격자 전부 ge3≤RR({RR_GE3}) · mean≤RR · corr≤0.03. "
            f"best={best_combo} ge3={step2[best_combo]['ge3_rate']} "
            f"mean={step2[best_combo]['mean']} · corr={sp}."
        )

    out = {
        "id": "K-COVER-SURVEY",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": base["n"],
        "draw_range": [D_LO, D_HI],
        "pool_brains": list(POOL_BRAINS),
        "source": "testlotto_brain_review predicted_sets_json",
        "metric_note": "mean/ge3 = best-of-5 matched among wheel picks (vs RR best_set)",
        "step1_baseline": step1,
        "step2_wheel_grid": step2,
        "step3_pool_grid": step3,
        "step4_coverage_corr": step4,
        "gates": gates,
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in (
        "n_eval", "gates", "recommended_next", "verdict", "step2_wheel_grid", "step3_pool_grid", "step4_coverage_corr"
    )}, ensure_ascii=False, indent=2))
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
