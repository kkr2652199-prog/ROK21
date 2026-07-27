# -*- coding: utf-8 -*-
"""K-X READ-ONLY: review 끝수 편향 원인 규명. 코드 수정 없음."""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260727_KX_review_ending.json"
SEED = 20260727


def load_draws():
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    con.close()
    return [
        {"draw_no": int(r[0]), "nums": sorted(int(x) for x in r[1:7])} for r in rows
    ]


def load_review(lo=None, hi=None):
    con = sqlite3.connect(str(DB))
    q = (
        "SELECT draw_no, predicted_sets_json FROM testlotto_brain_review "
        "WHERE brain_tag='review'"
    )
    args = []
    if lo is not None:
        q += " AND draw_no>=?"
        args.append(lo)
    if hi is not None:
        q += " AND draw_no<=?"
        args.append(hi)
    q += " ORDER BY draw_no"
    rows = con.execute(q, args).fetchall()
    con.close()
    sets = []
    by_draw = {}
    for dn, js in rows:
        ss = [sorted(int(x) for x in s["nums"]) for s in json.loads(js)]
        by_draw[int(dn)] = ss
        sets.extend(ss)
    return sets, by_draw


def ending_hist(sets):
    c = Counter()
    for s in sets:
        for n in s:
            c[n % 10] += 1
    return [int(c.get(d, 0)) for d in range(10)]


def decade_hist(sets):
    # 0:1-9, 1:10-19, ... 4:40-45
    c = Counter()
    for s in sets:
        for n in s:
            c[(n - 1) // 10] += 1
    return [int(c.get(d, 0)) for d in range(5)]


def unique_endings_per_set(sets):
    dist = Counter()
    for s in sets:
        dist[len({n % 10 for n in s})] += 1
    return {str(k): int(dist.get(k, 0)) for k in range(1, 7)}


def residual_top(obs, exp, k=3):
    obs = np.asarray(obs, float)
    exp = np.asarray(exp, float)
    # pearson residual
    r = (obs - exp) / np.sqrt(np.maximum(exp, 1e-9))
    order = np.argsort(-np.abs(r))
    return [
        {
            "digit": int(i),
            "obs": int(obs[i]),
            "exp": float(exp[i]),
            "resid": float(r[i]),
            "dir": "과다" if r[i] > 0 else "과소",
        }
        for i in order[:k]
    ]


def sample_C(n, rng):
    pool = list(range(1, 46))
    return [sorted(rng.sample(pool, 6)) for _ in range(n)]


def numbers_per_ending():
    c = Counter(n % 10 for n in range(1, 46))
    return [c[d] for d in range(10)]


def weight_profile_snapshot(draws_dicts):
    """현재 코드 경로와 동일하게 가중치→끝수 질량 계산 (실행만, 수정 없음)."""
    from app.testlotto.features.draw_features import repeat_rate_after_draw, sorted_nums
    from app.testlotto.learn_state_cutoff import set_learn_as_of, clear_history_cache
    from app.testlotto.learn_state import load_learn_state
    import os

    os.environ.pop("ROK21_LEARN_CUTOFF", None)  # default ON
    # as_of = last+1 style: target next
    target = draws_dicts[-1]["draw_no"] + 1
    clear_history_cache()
    set_learn_as_of(target)
    # convert to draw dicts expected by features
    draws = []
    for d in draws_dicts:
        row = {"draw_no": d["draw_no"]}
        for i, n in enumerate(d["nums"], 1):
            row[f"num{i}"] = n
        draws.append(row)

    rates = repeat_rate_after_draw(draws)
    learn = load_learn_state("review")
    adj = learn.get("adjustments", {})
    carry_boost = 1.0 + float(adj.get("carry_over_boost", 0))
    ending_boost_adj = float(adj.get("ending_digit_boost", 0))
    prev_nums = set(sorted_nums(draws[-1]))
    weights = {n: rates.get(n, 0.08) for n in range(1, 46)}
    for n in prev_nums:
        weights[n] *= 1.8 * carry_boost
    for n in range(1, 46):
        if n not in prev_nums:
            weights[n] *= 0.85
    # mass by ending / decade
    end_mass = Counter()
    dec_mass = Counter()
    rate_by_end = Counter()
    rate_n = Counter()
    for n, w in weights.items():
        end_mass[n % 10] += w
        dec_mass[(n - 1) // 10] += w
        rate_by_end[n % 10] += rates.get(n, 0.08)
        rate_n[n % 10] += 1
    tot = sum(end_mass.values())
    return {
        "carry_boost": carry_boost,
        "ending_digit_boost_in_state": ending_boost_adj,
        "ending_boost_used_in_review_path": False,  # code fact
        "prev_nums": sorted(prev_nums),
        "prev_endings": sorted(n % 10 for n in prev_nums),
        "weight_mass_by_ending": [float(end_mass[d] / tot) for d in range(10)],
        "weight_mass_by_decade": [float(dec_mass[d] / sum(dec_mass.values())) for d in range(5)],
        "mean_rate_by_ending": [
            float(rate_by_end[d] / max(1, rate_n[d])) for d in range(10)
        ],
        "review_count": learn.get("review_count"),
        "adjustments": adj,
    }


def chi2_uniform_slots(hist, n_sets):
    # compare to equal 1/10 of slots — NOT theory; for residual vs proportional to count
    slots = n_sets * 6
    # expected proportional to numbers-per-ending (uniform ball)
    npe = numbers_per_ending()
    exp = np.array(npe, float) / 45.0 * slots
    obs = np.array(hist, float)
    chi2 = float(np.sum((obs - exp) ** 2 / exp))
    p = float(stats.chi2.sf(chi2, 9))
    return {"chi2": chi2, "p": p, "exp_by_ball_count": exp.tolist()}


def main():
    draws = load_draws()
    A_sets = [d["nums"] for d in draws]
    B_all, by_draw = load_review(lo=1135, hi=1234)
    rng = random.Random(SEED)
    C_sets = sample_C(len(B_all), rng)

    hA, hB, hC = ending_hist(A_sets), ending_hist(B_all), ending_hist(C_sets)
    # scale A to same slots as B for residual compare
    slots_B = len(B_all) * 6
    slots_A = len(A_sets) * 6
    hA_scaled = [x * slots_B / slots_A for x in hA]
    hC_f = [float(x) for x in hC]

    resid_vs_A = residual_top(hB, hA_scaled, 3)
    resid_vs_C = residual_top(hB, hC_f, 3)

    early, _ = load_review(lo=1135, hi=1168)
    late, _ = load_review(lo=1201, hi=1234)
    h_early, h_late = ending_hist(early), ending_hist(late)
    # normalize to proportions
    pe = np.array(h_early, float) / max(1, sum(h_early))
    pl = np.array(h_late, float) / max(1, sum(h_late))
    # TV distance / max abs shift
    tv = 0.5 * float(np.abs(pe - pl).sum())
    shift = [
        {"digit": d, "early_p": float(pe[d]), "late_p": float(pl[d]), "delta": float(pl[d] - pe[d])}
        for d in range(10)
    ]
    shift.sort(key=lambda x: -abs(x["delta"]))

    # decade
    dA, dB, dC = decade_hist(A_sets), decade_hist(B_all), decade_hist(C_sets)
    dA_sc = [x * slots_B / slots_A for x in dA]
    resid_dec_A = residual_top(dB, dA_sc, 3)
    resid_dec_C = residual_top(dB, [float(x) for x in dC], 3)

    # unique endings
    ue_B = unique_endings_per_set(B_all)
    ue_A = unique_endings_per_set(A_sets)
    ue_C = unique_endings_per_set(C_sets)

    # weight snapshot at end
    wprof = weight_profile_snapshot(draws)

    # rates by ending aggregated historically (no learn)
    from app.testlotto.features.draw_features import repeat_rate_after_draw

    draws_feat = []
    for d in draws:
        row = {"draw_no": d["draw_no"]}
        for i, n in enumerate(d["nums"], 1):
            row[f"num{i}"] = n
        draws_feat.append(row)
    rates = repeat_rate_after_draw(draws_feat)
    rate_end = [[] for _ in range(10)]
    for n in range(1, 46):
        rate_end[n % 10].append(rates.get(n, 0.08))
    rate_end_mean = [float(np.mean(rate_end[d])) for d in range(10)]

    # prev-draw ending amplification: across 1135-1234, sum endings of prev actual × carry
    prev_end_hits = Counter()
    for dn in range(1135, 1235):
        # review for target dn uses draws before dn → prev = dn-1
        prev = next(d for d in draws if d["draw_no"] == dn - 1)
        for n in prev["nums"]:
            prev_end_hits[n % 10] += 1  # each week 6 prev numbers get ×1.8

    ball_gof = chi2_uniform_slots(hB, len(B_all))

    # correlation: is B ending prop explained by rate_end_mean?
    b_prop = np.array(hB, float) / sum(hB)
    # expected from ball count
    npe = np.array(numbers_per_ending(), float)
    prop_ball = npe / 45.0
    # expected from rates (normalized mass if weight=rate only)
    rate_mass = np.zeros(10)
    for n in range(1, 46):
        rate_mass[n % 10] += rates.get(n, 0.08)
    rate_mass /= rate_mass.sum()

    out = {
        "meta": {"n_A": len(A_sets), "n_B": len(B_all), "n_early": len(early), "n_late": len(late)},
        "ending_counts": {
            "review_B": hB,
            "draws_A": hA,
            "draws_A_scaled_to_B_slots": [float(x) for x in hA_scaled],
            "uniform_C": hC,
            "numbers_per_ending_1to45": numbers_per_ending(),
        },
        "residual_top3_vs_A": resid_vs_A,
        "residual_top3_vs_C": resid_vs_C,
        "unique_endings_per_set": {"A": ue_A, "B": ue_B, "C": ue_C},
        "decade_counts": {
            "A": dA,
            "B": dB,
            "C": dC,
            "resid_top3_vs_A": resid_dec_A,
            "resid_top3_vs_C": resid_dec_C,
            "labels": ["1-9", "10-19", "20-29", "30-39", "40-45"],
        },
        "amplification": {
            "early_1135_1168_ending": h_early,
            "late_1201_1234_ending": h_late,
            "tv_distance": tv,
            "top_shifts": shift[:5],
            "ks_early_late": float(stats.ks_2samp(
                np.repeat(np.arange(10), h_early),
                np.repeat(np.arange(10), h_late),
            ).pvalue) if sum(h_early) and sum(h_late) else None,
        },
        "code_path_facts": {
            "ending_digit_in_score": False,
            "ending_digit_boost_applied_in_review": False,
            "carry_over_boost_applied": True,
            "repeat_rate_drives_weights": True,
            "tier1_mentions_ending": False,
            "tier1_mentions_decade_ranges": True,
            "diversify_uses_ending": False,
            "sorted_pick_after_sample": True,
            "random_choices_frozen": True,
        },
        "weight_snapshot_asof_1235": wprof,
        "rate_mean_by_ending": rate_end_mean,
        "prev_end_hit_counts_1135_1234": [int(prev_end_hits[d]) for d in range(10)],
        "prop_compare": {
            "B": b_prop.tolist(),
            "ball_count": prop_ball.tolist(),
            "rate_mass": rate_mass.tolist(),
            "l1_B_vs_ball": float(np.abs(b_prop - prop_ball).sum()),
            "l1_B_vs_rate": float(np.abs(b_prop - rate_mass).sum()),
        },
        "ball_count_gof_B": ball_gof,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("B", hB)
    print("A_sc", [round(x, 1) for x in hA_scaled])
    print("C", hC)
    print("residA", resid_vs_A)
    print("residC", resid_vs_C)
    print("unique_end B", ue_B, "A", ue_A, "C", ue_C)
    print("decade B", dB, "residA", resid_dec_A)
    print("TV early-late", tv, "top", shift[:3])
    print("carry", wprof["carry_boost"], "ending_adj", wprof["ending_digit_boost_in_state"])
    print("rate_end", [round(x, 4) for x in rate_end_mean])
    print("l1 ball/rate", out["prop_compare"]["l1_B_vs_ball"], out["prop_compare"]["l1_B_vs_rate"])


if __name__ == "__main__":
    main()
