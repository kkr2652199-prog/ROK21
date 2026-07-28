# -*- coding: utf-8 -*-
"""K-PROB-VECTOR — 3뇌 확률벡터 핵심 신호 WF 실측 (READ-ONLY).

산출: docs/benchmarks/20260729_KPROBVEC_survey.json
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime
from math import exp
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KPROBVEC_survey.json"
D_LO, D_HI = 2, 1234
EXPECTED_NUM_HIT = 6 / 45  # 0.1333… single-number hit rate in a draw
EXPECTED_CARRY = 6 * 6 / 45  # 0.8


def spearman(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 5:
        return 0.0

    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
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
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx < 1e-12 or dy < 1e-12:
        return 0.0
    return round(num / (dx * dy), 4)


def z_test_prop(p_hat: float, p0: float, n: int) -> dict[str, Any]:
    """one-sided H1: p > p0"""
    if n <= 0:
        return {"z": 0.0, "p_approx": 1.0, "exceed": False}
    se = math.sqrt(p0 * (1 - p0) / n)
    if se < 1e-12:
        return {"z": 0.0, "p_approx": 1.0, "exceed": False}
    z = (p_hat - p0) / se
    # rough one-sided p from normal
    # Φ(-z) ≈ 0.5 * erfc(z/sqrt(2))
    p_one = 0.5 * math.erfc(z / math.sqrt(2))
    return {
        "z": round(z, 3),
        "p_approx": round(max(0.0, min(1.0, p_one)), 4),
        "exceed": bool(p_hat > p0 and p_one < 0.05),
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


def load_markov_sets() -> dict[int, list[list[int]]]:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT draw_no, predicted_sets_json FROM testlotto_brain_review
        WHERE brain_tag='markov' AND draw_no BETWEEN ? AND ?
        """,
        (D_LO, D_HI),
    ).fetchall()
    con.close()
    out: dict[int, list[list[int]]] = {}
    for r in rows:
        try:
            sets = json.loads(r["predicted_sets_json"] or "[]")
        except Exception:
            sets = []
        out[int(r["draw_no"])] = [
            [int(x) for x in (s.get("nums") or [])] for s in sets if s.get("nums")
        ]
    return out


def freq_vector(window: list[dict], decay: float = 0.02) -> dict[int, float]:
    """stat-like weighted freq on a window (no gap/hot for clean recency test)."""
    freq = {n: 0.1 for n in range(1, 46)}
    t = len(window)
    if t == 0:
        return {n: 1 / 45 for n in range(1, 46)}
    for idx, d in enumerate(window):
        w = exp(-decay * (t - 1 - idx))
        for k in range(1, 7):
            freq[int(d[f"num{k}"])] += w
    s = sum(freq.values())
    return {n: freq[n] / s for n in range(1, 46)}


def survey_stat(draws: list[dict]) -> dict[str, Any]:
    by_no = {int(d["draw_no"]): d for d in draws}
    ordered = [int(d["draw_no"]) for d in draws]
    actual = {
        dn: set(int(by_no[dn][f"num{k}"]) for k in range(1, 7)) for dn in ordered
    }

    # A) recency windows
    windows = {"all": None, 50: 50, 100: 100, 200: 200}
    recency_rows = []
    for label, wsize in windows.items():
        overlaps = []
        # number-level: for each draw, prob of each num vs appeared(0/1)
        xs: list[float] = []
        ys: list[float] = []
        for dn in ordered:
            if dn < D_LO or dn > D_HI:
                continue
            hist = [by_no[x] for x in ordered if x < dn]
            if len(hist) < 10:
                continue
            if wsize is not None:
                hist = hist[-wsize:]
            pv = freq_vector(hist)
            top6 = sorted(pv, key=lambda n: (-pv[n], n))[:6]
            overlaps.append(len(set(top6) & actual[dn]) / 6.0)
            for n in range(1, 46):
                xs.append(pv[n])
                ys.append(1.0 if n in actual[dn] else 0.0)
        recency_rows.append(
            {
                "window": label if label == "all" else wsize,
                "overlap_mean": round(sum(overlaps) / len(overlaps), 4) if overlaps else 0,
                "spearman_r": spearman(xs, ys),
                "n_draws": len(overlaps),
            }
        )
    best_rec = max(recency_rows, key=lambda r: (r["spearman_r"], r["overlap_mean"]))

    # B) gap_boost hit rates
    hits30 = trials30 = 0
    hits50 = trials50 = 0
    for dn in ordered:
        if dn < D_LO or dn > D_HI:
            continue
        hist = [by_no[x] for x in ordered if x < dn]
        if len(hist) < 50:
            continue
        last_seen = {n: 0 for n in range(1, 46)}
        for d in hist:
            for k in range(1, 7):
                last_seen[int(d[f"num{k}"])] = int(d["draw_no"])
        prev_no = hist[-1]["draw_no"]
        for n in range(1, 46):
            gap = prev_no - last_seen[n] if last_seen[n] else prev_no
            in_act = n in actual[dn]
            if gap >= 30:
                trials30 += 1
                hits30 += int(in_act)
            if gap >= 50:
                trials50 += 1
                hits50 += int(in_act)

    rate30 = hits30 / trials30 if trials30 else 0.0
    rate50 = hits50 / trials50 if trials50 else 0.0
    zt30 = z_test_prop(rate30, EXPECTED_NUM_HIT, trials30)
    zt50 = z_test_prop(rate50, EXPECTED_NUM_HIT, trials50)

    return {
        "recency_windows": recency_rows,
        "recency_window_best": {
            "window": best_rec["window"],
            "spearman_r": best_rec["spearman_r"],
            "overlap_mean": best_rec["overlap_mean"],
        },
        "gap_boost_hit_rate": {
            "ge30": round(rate30, 4),
            "ge50": round(rate50, 4),
            "expected": round(EXPECTED_NUM_HIT, 4),
            "n_ge30": trials30,
            "n_ge50": trials50,
            "ztest_ge30": zt30,
            "ztest_ge50": zt50,
        },
    }


def survey_markov(draws: list[dict], markov_sets: dict[int, list[list[int]]]) -> dict[str, Any]:
    from app.testlotto.predict_markov import build_transition_matrix, markov_random_walk

    by_no = {int(d["draw_no"]): d for d in draws}
    ordered = [int(d["draw_no"]) for d in draws]
    actual = {
        dn: set(int(by_no[dn][f"num{k}"]) for k in range(1, 7)) for dn in ordered
    }

    top_k_rows = []
    for k in (6, 10, 15):
        overlaps = []
        xs: list[float] = []
        ys: list[float] = []
        for dn in ordered:
            if dn < D_LO or dn > D_HI or dn < 20:
                continue
            hist = [by_no[x] for x in ordered if x < dn]
            if len(hist) < 2:
                continue
            matrix = build_transition_matrix(hist, decay=0.02)
            start = [hist[-1][f"num{j}"] for j in range(1, 7)]
            # aggregate outgoing weight from last 6
            score = {n: 0.0 for n in range(1, 46)}
            for a in start:
                for b in range(1, 46):
                    score[b] += matrix[a][b]
            ranked = sorted(score, key=lambda n: (-score[n], n))
            top = ranked[:k]
            overlaps.append(len(set(top) & actual[dn]) / 6.0)
            # spearman: score vs appear for all nums (heavy) — sample top15+actual
            focus = set(ranked[:20]) | actual[dn]
            for n in focus:
                xs.append(score[n])
                ys.append(1.0 if n in actual[dn] else 0.0)
        top_k_rows.append(
            {
                "k": k,
                "overlap_mean": round(sum(overlaps) / len(overlaps), 4) if overlaps else 0,
                "spearman_r": spearman(xs, ys),
                "n_draws": len(overlaps),
            }
        )

    # pool vs single (use stored 5 sets; single = deterministic visit top6)
    pool_hits = []
    single_hits = []
    for dn in ordered:
        if dn < D_LO or dn > D_HI or dn < 20:
            continue
        sets = markov_sets.get(dn) or []
        if len(sets) < 1:
            continue
        hist = [by_no[x] for x in ordered if x < dn]
        if len(hist) < 2:
            continue
        union = set()
        for s in sets:
            union |= set(s)
        pool_hits.append(len(union & actual[dn]) / 6.0)

        matrix = build_transition_matrix(hist, decay=0.02)
        start = [hist[-1][f"num{j}"] for j in range(1, 7)]
        random.seed(dn * 31 + 7)
        visits = markov_random_walk(matrix, start, steps=80)
        top6 = [n for n, _ in sorted(visits.items(), key=lambda x: (-x[1], x[0]))[:6]]
        single_hits.append(len(set(top6) & actual[dn]) / 6.0)

    pool_m = sum(pool_hits) / len(pool_hits) if pool_hits else 0
    single_m = sum(single_hits) / len(single_hits) if single_hits else 0
    # null for union: E[|W∩U|/6] ≈ |U|/45
    union_sizes = []
    for dn in ordered:
        if dn < D_LO or dn > D_HI or dn < 20:
            continue
        sets = markov_sets.get(dn) or []
        if not sets:
            continue
        u: set[int] = set()
        for s in sets:
            u |= set(s)
        union_sizes.append(len(u))
    mean_u = sum(union_sizes) / len(union_sizes) if union_sizes else 0
    null_pool = mean_u / 45.0
    return {
        "transition_top_k": top_k_rows,
        "pool_vs_single": {
            "pool_union_hit_rate": round(pool_m, 4),
            "single_hit_rate": round(single_m, 4),
            "delta": round(pool_m - single_m, 4),
            "mean_union_size": round(mean_u, 2),
            "null_pool_rate": round(null_pool, 4),
            "delta_vs_null": round(pool_m - null_pool, 4),
            "n": len(pool_hits),
            "note": "pool=brain_review 5세트 합집합 / single=visit top6 / null≈|U|/45",
        },
    }


def survey_review(draws: list[dict]) -> dict[str, Any]:
    by_no = {int(d["draw_no"]): d for d in draws}
    ordered = [int(d["draw_no"]) for d in draws]
    actual = {
        dn: set(int(by_no[dn][f"num{k}"]) for k in range(1, 7)) for dn in ordered
    }

    carry_counts = []
    ending_hits = ending_trials = 0
    # ending expected: each prev ending digit class size ~4.5 nums; rough p = 6/45 still for a random num
    # Better: for each prev number's ending e, P(some number with ending e appears) is messy.
    # Measure: fraction of prev endings that appear at least once in current draw.
    ending_match_rates = []

    for dn in ordered:
        if dn < D_LO or dn > D_HI:
            continue
        prev = by_no.get(dn - 1)
        if not prev:
            continue
        prev_nums = set(int(prev[f"num{k}"]) for k in range(1, 7))
        cur = actual[dn]
        carry_counts.append(len(prev_nums & cur))

        prev_end = {n % 10 for n in prev_nums}
        cur_end = {n % 10 for n in cur}
        ending_match_rates.append(len(prev_end & cur_end) / max(1, len(prev_end)))
        # number-level ending boost probe: nums sharing prev endings
        for n in range(1, 46):
            if n % 10 in prev_end:
                ending_trials += 1
                ending_hits += int(n in cur)

    carry_mean = sum(carry_counts) / len(carry_counts) if carry_counts else 0
    # carry count is sum of 6 bernoullis approx; mean of count vs 0.8
    # for z-test on mean of counts: treat as continuous with var≈0.8*(1-6/45)*6 rough
    # simpler: convert to per-slot hit rate carry_mean/6 vs 6/45
    carry_rate = carry_mean / 6.0
    zt_carry = z_test_prop(carry_rate, EXPECTED_NUM_HIT, len(carry_counts) * 6)

    end_rate = ending_hits / ending_trials if ending_trials else 0
    zt_end = z_test_prop(end_rate, EXPECTED_NUM_HIT, ending_trials)
    end_set_mean = (
        sum(ending_match_rates) / len(ending_match_rates) if ending_match_rates else 0
    )
    # expected ending-set overlap: rough 1 - (1-6/45)^(avg endings~6) messy; use digit hit rate as primary

    return {
        "carry_over": {
            "actual_mean": round(carry_mean, 4),
            "expected": EXPECTED_CARRY,
            "delta": round(carry_mean - EXPECTED_CARRY, 4),
            "per_num_rate": round(carry_rate, 4),
            "ztest": zt_carry,
            "valid": bool(
                carry_mean > EXPECTED_CARRY and zt_carry.get("exceed")
            )
            or bool(carry_mean - EXPECTED_CARRY > 0.05),
            "n": len(carry_counts),
        },
        "ending_digit": {
            "hit_rate": round(end_rate, 4),
            "expected": round(EXPECTED_NUM_HIT, 4),
            "delta": round(end_rate - EXPECTED_NUM_HIT, 4),
            "ending_set_overlap_mean": round(end_set_mean, 4),
            "ztest": zt_end,
            "n_trials": ending_trials,
            "valid": bool(zt_end.get("exceed")),
        },
    }


def main() -> None:
    t0 = time.perf_counter()
    draws = load_draws()
    markov_sets = load_markov_sets()

    print("stat…")
    st = survey_stat(draws)
    print("markov…")
    mk = survey_markov(draws, markov_sets)
    print("review…")
    rv = survey_review(draws)

    ranking = []

    def add(name: str, r: float | None, valid: bool, extra: str = ""):
        ranking.append(
            {
                "signal": name,
                "spearman_r": r,
                "valid": valid,
                "note": extra,
            }
        )

    # validity rules: spearman > 0.03 OR expect-exceed p<0.05
    best_r = st["recency_window_best"]["spearman_r"]
    add(
        "stat_recency",
        best_r,
        best_r > 0.03,
        f"best_window={st['recency_window_best']['window']}",
    )
    g = st["gap_boost_hit_rate"]
    gap_valid = bool(g["ztest_ge30"]["exceed"] or g["ztest_ge50"]["exceed"])
    add(
        "stat_gap_boost",
        None,
        gap_valid,
        f"ge30={g['ge30']} ge50={g['ge50']} exp={g['expected']}",
    )

    best_mk = max(mk["transition_top_k"], key=lambda x: x["spearman_r"])
    add(
        "markov_transition",
        best_mk["spearman_r"],
        best_mk["spearman_r"] > 0.03,
        f"best_k={best_mk['k']} overlap={best_mk['overlap_mean']}",
    )
    pool_d = mk["pool_vs_single"]["delta_vs_null"]
    add(
        "markov_pool",
        None,
        pool_d > 0.03,
        f"delta_vs_null={pool_d} (vs single={mk['pool_vs_single']['delta']})",
    )

    add(
        "review_carry",
        None,
        bool(rv["carry_over"]["valid"]),
        f"mean={rv['carry_over']['actual_mean']} exp={EXPECTED_CARRY}",
    )
    add(
        "review_ending",
        None,
        bool(rv["ending_digit"]["valid"]),
        f"hit={rv['ending_digit']['hit_rate']}",
    )

    ranking.sort(key=lambda x: (not x["valid"], -(x["spearman_r"] or -1)))
    strengthen = [x["signal"] for x in ranking if x["valid"]]
    verdict = "강화대상 있음" if strengthen else "없음"

    out = {
        "id": "K-PROB-VECTOR",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.perf_counter() - t0, 1),
        "stat": st,
        "markov": mk,
        "review": rv,
        "signal_ranking": ranking,
        "recommended_strengthen": strengthen,
        "verdict": verdict,
        "db_code_write": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "verdict": verdict,
                "strengthen": strengthen,
                "recency_best": st["recency_window_best"],
                "gap": {k: g[k] for k in ("ge30", "ge50", "expected")},
                "markov_best_k": best_mk,
                "pool": mk["pool_vs_single"],
                "carry": rv["carry_over"],
                "ending": {
                    "hit": rv["ending_digit"]["hit_rate"],
                    "valid": rv["ending_digit"]["valid"],
                },
                "sec": out["elapsed_sec"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
