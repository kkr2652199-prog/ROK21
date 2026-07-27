# -*- coding: utf-8 -*-
"""K-W READ-ONLY: 뇌 산출 vs 당첨 draws vs 균등 무작위 정합성 측정."""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260727_KW_alignment.json"
SEED = 20260727
BRAINS = ("stat", "markov", "review")


def load_draws_A():
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    con.close()
    return [sorted(int(x) for x in r) for r in rows]


def load_brain_B():
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE draw_no >= (SELECT MAX(draw_no)-99 FROM lotto_draws)"
    ).fetchall()
    con.close()
    by = {b: [] for b in BRAINS}
    for tag, js in rows:
        if tag not in by:
            continue
        for s in json.loads(js):
            by[tag].append(sorted(int(x) for x in s["nums"]))
    return by


def sample_uniform_C(n: int, rng: random.Random) -> list[list[int]]:
    pool = list(range(1, 46))
    out = []
    for _ in range(n):
        out.append(sorted(rng.sample(pool, 6)))
    return out


def feats(sets: list[list[int]]):
    sums, odds, zones, consecs = [], [], [], []
    endings = Counter()
    for sc in sets:
        sc = sorted(sc)
        sums.append(sum(sc))
        odds.append(sum(1 for x in sc if x % 2 == 1))
        l = sum(1 for x in sc if x <= 15)
        m = sum(1 for x in sc if 16 <= x <= 30)
        h = 6 - l - m
        zones.append((l, m, h))
        consecs.append(sum(1 for i in range(5) if sc[i + 1] - sc[i] == 1))
        for x in sc:
            endings[x % 10] += 1
    return {
        "sums": np.asarray(sums, float),
        "odds": np.asarray(odds, int),
        "zones": zones,
        "consecs": np.asarray(consecs, int),
        "endings": endings,
        "n": len(sets),
    }


def ks_dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(stats.ks_2samp(a, b).statistic)


def chi2_df_dist(counts_a: np.ndarray, counts_b: np.ndarray) -> float:
    """2-sample contingency chi2/df as distance (larger = farther)."""
    tbl = np.vstack([counts_a, counts_b]).astype(float)
    # drop all-zero cols
    tbl = tbl[:, tbl.sum(axis=0) > 0]
    if tbl.shape[1] < 2:
        return 0.0
    # merge rare cols (<5 total)
    keep = []
    rare_a = rare_b = 0.0
    for j in range(tbl.shape[1]):
        if tbl[:, j].sum() >= 5:
            keep.append(j)
        else:
            rare_a += tbl[0, j]
            rare_b += tbl[1, j]
    cols = [tbl[:, j] for j in keep]
    if rare_a + rare_b > 0:
        cols.append(np.array([rare_a, rare_b]))
    if len(cols) < 2:
        return 0.0
    t = np.column_stack(cols)
    chi2, p, dof, _ = stats.chi2_contingency(t)
    dof = max(1, int(dof))
    return float(chi2 / dof)


def ending_counts(endings: Counter, n_sets: int) -> np.ndarray:
    # slot counts 0..9
    return np.array([endings.get(d, 0) for d in range(10)], dtype=float)


def zone_counts(zones: list, keys: list) -> np.ndarray:
    c = Counter(zones)
    return np.array([c.get(k, 0) for k in keys], dtype=float)


def distances(brain_f, ref_f, zone_keys):
    """brain vs ref distances per metric."""
    odd_b = np.bincount(brain_f["odds"], minlength=7).astype(float)
    odd_r = np.bincount(ref_f["odds"], minlength=7).astype(float)
    cons_b = np.bincount(brain_f["consecs"], minlength=6).astype(float)
    cons_r = np.bincount(ref_f["consecs"], minlength=6).astype(float)
    return {
        "sum_KS": ks_dist(brain_f["sums"], ref_f["sums"]),
        "odd_chi2_df": chi2_df_dist(odd_b, odd_r),
        "zone_chi2_df": chi2_df_dist(
            zone_counts(brain_f["zones"], zone_keys),
            zone_counts(ref_f["zones"], zone_keys),
        ),
        "consec_chi2_df": chi2_df_dist(cons_b, cons_r),
        "ending_chi2_df": chi2_df_dist(
            ending_counts(brain_f["endings"], brain_f["n"]),
            ending_counts(ref_f["endings"], ref_f["n"]),
        ),
    }


def interpret(d_vs_A: dict, d_vs_C: dict) -> dict:
    """각 지표 + 종합: closer to A / C / both far."""
    metrics = list(d_vs_A.keys())
    per = {}
    votes_A = votes_C = votes_far = 0
    for m in metrics:
        a, c = d_vs_A[m], d_vs_C[m]
        # both far if both distances large relative to each other and absolute
        # rule: closer side wins; if min(a,c) > median of all distances for this brain → far?
        # User: A에 가까움 / C에 가까움 / 양쪽 모두 멀다
        # "양쪽 모두 멀다": both distances high. Use: if a>0.15 and c>0.15 for KS,
        # for chi2/df if both > 3 (rough). Better: if abs(a-c)/max(a,c,1e-9) < 0.15 and min(a,c) > threshold
        ratio = abs(a - c) / max(a, c, 1e-12)
        if a < c * 0.9:
            verdict = "closer_A"
            votes_A += 1
        elif c < a * 0.9:
            verdict = "closer_C"
            votes_C += 1
        else:
            # nearly equidistant
            if min(a, c) >= 0.12 and m.startswith("sum"):
                verdict = "far_both"
                votes_far += 1
            elif min(a, c) >= 2.0 and not m.startswith("sum"):
                verdict = "far_both"
                votes_far += 1
            elif a <= c:
                verdict = "closer_A_tieish"
                votes_A += 1
            else:
                verdict = "closer_C_tieish"
                votes_C += 1
        per[m] = {"d_A": a, "d_C": c, "verdict": verdict, "ratio_gap": ratio}

    # overall: majority of metrics
    if votes_far >= 3:
        overall = "편향경보_A·C양쪽원격"
    elif votes_A > votes_C:
        overall = "정합_A근접"
    elif votes_C > votes_A:
        overall = "무해_C근접"
    else:
        overall = "경합_동률"
    return {
        "per_metric": per,
        "votes": {"A": votes_A, "C": votes_C, "far": votes_far},
        "overall": overall,
    }


def hist_odd(sets):
    o = [sum(1 for x in s if x % 2 == 1) for s in sets]
    return np.bincount(o, minlength=7).astype(int).tolist()


def hist_consec(sets):
    c = []
    for s in sets:
        sc = sorted(s)
        c.append(sum(1 for i in range(5) if sc[i + 1] - sc[i] == 1))
    return np.bincount(c, minlength=6).astype(int).tolist()


def hist_ending(sets):
    e = Counter()
    for s in sets:
        for x in s:
            e[x % 10] += 1
    return [int(e.get(d, 0)) for d in range(10)]


def hist_sum_bins(sets, edges=None):
    sums = [sum(s) for s in sets]
    if edges is None:
        edges = list(range(60, 221, 10))
    hist, _ = np.histogram(sums, bins=edges)
    return {"edges": edges, "counts": hist.astype(int).tolist(), "mean": float(np.mean(sums))}


def hist_zone(sets):
    c = Counter()
    for s in sets:
        l = sum(1 for x in s if x <= 15)
        m = sum(1 for x in s if 16 <= x <= 30)
        h = 6 - l - m
        c[(l, m, h)] += 1
    # top 15
    top = c.most_common(15)
    return [{"zone": list(k), "count": v} for k, v in top]


def main():
    A = load_draws_A()
    B = load_brain_B()
    fA = feats(A)
    zone_keys = sorted(set(fA["zones"]) | set().union(*[set(feats(B[b])["zones"]) for b in BRAINS]))

    rng = random.Random(SEED)
    results = {
        "meta": {
            "seed": SEED,
            "n_A": len(A),
            "n_B": {b: len(B[b]) for b in BRAINS},
            "interpretation": {
                "closer_C": "명분은 없으나 무해(균등 근접)",
                "closer_A": "정합(당첨분포 근접) — pattern/balance 명분과 일치 가능",
                "far_both": "편향 경보 — 근거 없는 방향 치우침, 원인 규명 대상",
            },
        },
        "brains": {},
        "A_summary": {
            "sum_mean": float(fA["sums"].mean()),
            "odd_hist": np.bincount(fA["odds"], minlength=7).tolist(),
            "consec_hist": np.bincount(fA["consecs"], minlength=6).tolist(),
            "ending_hist": hist_ending(A),
        },
    }

    all_gap = []  # (brain, metric, d_A, d_C, gap)

    for b in BRAINS:
        sets_b = B[b]
        n = len(sets_b)
        C = sample_uniform_C(n, rng)
        fB, fC = feats(sets_b), feats(C)
        zk = sorted(set(zone_keys) | set(fB["zones"]) | set(fC["zones"]))
        dA = distances(fB, fA, zk)
        dC = distances(fB, fC, zk)
        inter = interpret(dA, dC)
        for m in dA:
            gap = abs(dA[m] - dC[m])
            # "이탈이 큰" = distance to nearer ref is still large, or max(dA,dC)
            all_gap.append(
                {
                    "brain": b,
                    "metric": m,
                    "d_A": dA[m],
                    "d_C": dC[m],
                    "max_d": max(dA[m], dC[m]),
                    "min_d": min(dA[m], dC[m]),
                }
            )
        results["brains"][b] = {
            "n": n,
            "sum_mean": float(fB["sums"].mean()),
            "vs_A": dA,
            "vs_C": dC,
            "interpret": inter,
            "hist": {
                "sum": hist_sum_bins(sets_b),
                "odd_0to6": hist_odd(sets_b),
                "consec_0to5": hist_consec(sets_b),
                "ending_0to9": hist_ending(sets_b),
                "zone_top15": hist_zone(sets_b),
            },
            "C_sum_mean": float(fC["sums"].mean()),
        }

    # top 3 deviation metrics: largest min_d (far from both) then max_d
    ranked = sorted(all_gap, key=lambda x: (x["min_d"], x["max_d"]), reverse=True)
    top3 = ranked[:3]
    # also per-brain top metrics by max(d_A,d_C)
    results["top3_deviation"] = top3
    results["top3_detail"] = []
    for t in top3:
        b = t["brain"]
        m = t["metric"]
        h = results["brains"][b]["hist"]
        if m.startswith("sum"):
            shape = h["sum"]
        elif m.startswith("odd"):
            shape = {"odd_0to6": h["odd_0to6"]}
        elif m.startswith("zone"):
            shape = {"zone_top15": h["zone_top15"]}
        elif m.startswith("consec"):
            shape = {"consec_0to5": h["consec_0to5"]}
        else:
            shape = {"ending_0to9": h["ending_0to9"]}
        results["top3_detail"].append({**t, "histogram": shape})

    # A and C reference hists for report
    C_ref = sample_uniform_C(len(A), random.Random(SEED + 1))
    results["C_ref_nA"] = {
        "sum_mean": float(np.mean([sum(s) for s in C_ref])),
        "odd_hist": hist_odd(C_ref),
        "consec_hist": hist_consec(C_ref),
        "ending_hist": hist_ending(C_ref),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    for b in BRAINS:
        br = results["brains"][b]
        print(b, br["interpret"]["overall"], "votes", br["interpret"]["votes"])
        print("  vsA", {k: round(v, 4) for k, v in br["vs_A"].items()})
        print("  vsC", {k: round(v, 4) for k, v in br["vs_C"].items()})
    print("TOP3", [(t["brain"], t["metric"], round(t["min_d"], 4), round(t["max_d"], 4)) for t in top3])


if __name__ == "__main__":
    main()
