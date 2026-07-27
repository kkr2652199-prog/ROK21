# READ-ONLY: K-T / K-U / K-V premise & portfolio audit (2026-07-27)
from __future__ import annotations

import itertools
import json
import math
import random
import sqlite3
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

DB = Path(__file__).resolve().parents[1] / "data" / "lotto_testlotto.db"
OUT = Path(__file__).resolve().parents[1] / "docs" / "benchmarks" / "20260727_KT_KV_results.json"
N_PERM = 10_000
RNG = random.Random(20260727)
NP_RNG = np.random.default_rng(20260727)


def load_draws():
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6,bonus "
        "FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    con.close()
    draws = []
    for r in rows:
        main = sorted(int(x) for x in r[1:7])
        draws.append(
            {
                "draw_no": int(r[0]),
                "main": main,
                "bonus": int(r[7]),
                "all7": main + [int(r[7])],
            }
        )
    return draws


def chi2_gof(obs_counts, exp_counts, ddof=0):
    obs = np.asarray(obs_counts, dtype=float)
    exp = np.asarray(exp_counts, dtype=float)
    mask = exp > 0
    obs, exp = obs[mask], exp[mask]
    chi2 = float(np.sum((obs - exp) ** 2 / exp))
    df = max(1, len(obs) - 1 - ddof)
    p = float(stats.chi2.sf(chi2, df))
    return {"chi2": chi2, "df": df, "p": p, "n_bins": int(mask.sum())}


def overlap_test(draws, lag: int, h0_mean=0.8):
    """직전 lag회차 본번과 중복개수 분포."""
    overlaps = []
    for i in range(lag, len(draws)):
        a = set(draws[i]["main"])
        b = set(draws[i - lag]["main"])
        overlaps.append(len(a & b))
    overlaps = np.asarray(overlaps, dtype=int)
    n = len(overlaps)
    mean = float(overlaps.mean())
    var = float(overlaps.var(ddof=1))
    # Hypergeometric-like: under independence, X~Hypergeom(N=45,K=6,n=6) ≈ mean 0.8
    # Exact pmf for random 6-subset vs fixed 6: P(X=k)=C(6,k)*C(39,6-k)/C(45,6)
    from math import comb

    total = comb(45, 6)
    pmf = np.array(
        [comb(6, k) * comb(39, 6 - k) / total if 0 <= 6 - k <= 39 else 0.0 for k in range(7)]
    )
    obs = np.bincount(overlaps, minlength=7)[:7].astype(float)
    exp = pmf * n
    gof = chi2_gof(obs, exp)
    # one-sample t vs 0.8
    t_res = stats.ttest_1samp(overlaps, h0_mean)
    return {
        "lag": lag,
        "n_transitions": n,
        "obs_mean": mean,
        "obs_var": var,
        "h0_mean": h0_mean,
        "counts_0_to_6": obs.astype(int).tolist(),
        "exp_0_to_6": exp.tolist(),
        "chi2": gof,
        "ttest_vs_0_8": {"t": float(t_res.statistic), "p": float(t_res.pvalue)},
        "verdict": "기각" if gof["p"] < 0.05 else "실증불가(H0유지/부합)",
    }


def miss_gap_test(draws):
    """번호별 출현 간격 vs 기하분포(성공확률 p=6/45 per draw for main)."""
    # For each number, gaps between consecutive appearances in main (6/45)
    last_seen = {n: None for n in range(1, 46)}
    gaps = []
    for i, d in enumerate(draws):
        s = set(d["main"])
        for n in range(1, 46):
            if n in s:
                if last_seen[n] is not None:
                    gaps.append(i - last_seen[n])  # draws between appearances (= gap length)
                last_seen[n] = i
    gaps = np.asarray(gaps, dtype=float)
    # Geometric: P(G=k)=(1-p)^{k-1}p for k=1,2,... where k=draws until next hit
    # E[G]=1/p=45/6=7.5
    p = 6 / 45
    # KS against geometric (scipy: geom with loc=0 means P(X=k)=(1-p)^{k-1}p for k=1,2,...)
    ks = stats.kstest(gaps, "geom", args=(p,))
    # Chi2 pooled bins 1..20, 21+
    max_bin = 20
    obs = np.bincount(gaps.astype(int), minlength=max_bin + 2)
    # obs[0] unused if gaps start at 1
    obs_bins = obs[1 : max_bin + 1].astype(float)
    obs_tail = float(obs[max_bin + 1 :].sum())
    exp_bins = np.array([(1 - p) ** (k - 1) * p for k in range(1, max_bin + 1)]) * len(gaps)
    exp_tail = ((1 - p) ** max_bin) * len(gaps)
    gof = chi2_gof(
        np.concatenate([obs_bins, [obs_tail]]),
        np.concatenate([exp_bins, [exp_tail]]),
    )
    return {
        "n_gaps": int(len(gaps)),
        "obs_mean": float(gaps.mean()),
        "obs_var": float(gaps.var(ddof=1)),
        "expected_mean": 1 / p,
        "ks": {"stat": float(ks.statistic), "p": float(ks.pvalue)},
        "chi2_pool": gof,
        "verdict": "이탈(실증)" if (ks.pvalue < 0.05 or gof["p"] < 0.05) else "기하부합(이탈미실증)",
    }


def _enumerate_combo_features():
    """이론분포: C(45,6) 전수 (약 8M — 한 번만)."""
    # Too heavy for full enum in some envs; use exact combinatorial formulas where possible
    # and MC for harder ones. Prefer exact.
    from math import comb

    N = comb(45, 6)
    # sum distribution
    sum_counts = Counter()
    oe_counts = Counter()  # odd count 0..6
    zone_counts = Counter()  # tuple (l,m,h)
    consec_counts = Counter()
    ending_counts = Counter()  # count of ending digit d in a set? use multiset of endings
    # Full enum is ~8e6 — acceptable in numpy loop
    nums = np.arange(1, 46, dtype=np.int16)
    # iterate combinations in chunks via itertools
    ending_digit_hist = Counter()  # per-ball ending across all combo slots
    for combo in itertools.combinations(range(1, 46), 6):
        s = sum(combo)
        sum_counts[s] += 1
        odd = sum(1 for x in combo if x % 2 == 1)
        oe_counts[odd] += 1
        l = sum(1 for x in combo if x <= 15)
        m = sum(1 for x in combo if 16 <= x <= 30)
        h = 6 - l - m
        zone_counts[(l, m, h)] += 1
        sc = sorted(combo)
        consec = sum(1 for i in range(5) if sc[i + 1] - sc[i] == 1)
        consec_counts[consec] += 1
        for x in combo:
            ending_digit_hist[x % 10] += 1
    return {
        "N": N,
        "sum": sum_counts,
        "odd": oe_counts,
        "zone": zone_counts,
        "consec": consec_counts,
        "ending": ending_digit_hist,
    }


def pattern_balance_test(draws):
    # Observed from main numbers
    sums, odds, zones, consecs, endings = [], [], [], [], Counter()
    for d in draws:
        nums = d["main"]
        sums.append(sum(nums))
        odd = sum(1 for x in nums if x % 2 == 1)
        odds.append(odd)
        l = sum(1 for x in nums if x <= 15)
        m = sum(1 for x in nums if 16 <= x <= 30)
        h = 6 - l - m
        zones.append((l, m, h))
        sc = nums  # already sorted
        consecs.append(sum(1 for i in range(5) if sc[i + 1] - sc[i] == 1))
        for x in nums:
            endings[x % 10] += 1

    print("enumerating C(45,6) theoretical...", flush=True)
    theo = _enumerate_combo_features()
    n = len(draws)
    N = theo["N"]

    # sum: KS vs empirical CDF from theory (weighted)
    sum_keys = sorted(theo["sum"])
    theo_pmf = np.array([theo["sum"][k] / N for k in sum_keys])
    theo_cdf_x = np.array(sum_keys, dtype=float)
    # KS: compare empirical CDF of observed sums to theoretical
    obs_sums = np.asarray(sums, dtype=float)
    # Build theoretical CDF function
    cdf_vals = np.cumsum(theo_pmf)

    def theo_cdf(x):
        idx = np.searchsorted(theo_cdf_x, x, side="right") - 1
        out = np.zeros_like(x, dtype=float)
        out[idx < 0] = 0.0
        m = (idx >= 0) & (idx < len(cdf_vals))
        out[m] = cdf_vals[idx[m]]
        out[idx >= len(cdf_vals)] = 1.0
        return out

    ks_sum = stats.kstest(obs_sums, theo_cdf)

    # odd chi2
    odd_obs = np.bincount(odds, minlength=7).astype(float)
    odd_exp = np.array([theo["odd"].get(k, 0) / N * n for k in range(7)])
    odd_gof = chi2_gof(odd_obs, odd_exp)

    # zone: top patterns + other
    zone_obs = Counter(zones)
    # use all keys with exp>=5 or merge
    all_zone_keys = sorted(set(zone_obs) | set(theo["zone"]), key=lambda t: (-theo["zone"].get(t, 0), t))
    # merge rare
    obs_list, exp_list, labels = [], [], []
    other_o, other_e = 0.0, 0.0
    for k in all_zone_keys:
        e = theo["zone"].get(k, 0) / N * n
        o = zone_obs.get(k, 0)
        if e >= 5:
            obs_list.append(o)
            exp_list.append(e)
            labels.append(str(k))
        else:
            other_o += o
            other_e += e
    if other_e > 0:
        obs_list.append(other_o)
        exp_list.append(other_e)
        labels.append("other")
    zone_gof = chi2_gof(obs_list, exp_list)

    # consecutive pairs count (0..5)
    consec_obs = np.bincount(consecs, minlength=6).astype(float)
    consec_exp = np.array([theo["consec"].get(k, 0) / N * n for k in range(6)])
    consec_gof = chi2_gof(consec_obs, consec_exp)

    # ending digits: 6*n balls, theory from combo slots
    end_obs = np.array([endings.get(d, 0) for d in range(10)], dtype=float)
    end_exp = np.array([theo["ending"].get(d, 0) / N * n for d in range(10)], dtype=float)
    # note: endings not independent across a set; still report chi2 + caveat
    end_gof = chi2_gof(end_obs, end_exp)

    def v(p):
        return "이론부합(제약명분OK)" if p >= 0.05 else "이론이탈"

    return {
        "n_draws": n,
        "sum": {
            "obs_mean": float(obs_sums.mean()),
            "theo_mean": float(sum(k * theo["sum"][k] for k in theo["sum"]) / N),
            "expected_note": 138.0,
            "ks": {"stat": float(ks_sum.statistic), "p": float(ks_sum.pvalue)},
            "verdict": v(ks_sum.pvalue),
        },
        "odd_even": {
            "obs_counts_odd0to6": odd_obs.astype(int).tolist(),
            "exp_counts": odd_exp.tolist(),
            "chi2": odd_gof,
            "verdict": v(odd_gof["p"]),
        },
        "zone": {"chi2": zone_gof, "n_labels": len(labels), "verdict": v(zone_gof["p"])},
        "consecutive_pairs": {
            "obs_0to5": consec_obs.astype(int).tolist(),
            "exp": consec_exp.tolist(),
            "chi2": consec_gof,
            "verdict": v(consec_gof["p"]),
        },
        "ending_digit": {
            "obs_0to9": end_obs.astype(int).tolist(),
            "exp": end_exp.tolist(),
            "chi2": end_gof,
            "verdict": v(end_gof["p"]),
            "caveat": "슬롯비독립 — 참고용",
        },
    }


def pair_layer_test(draws):
    """K-U: pair co-occurrence with label-permutation null."""
    from math import comb

    n_draws = len(draws)
    # observed pairs from main+bonus (C(7,2)=21 per draw)
    pair_idx = {p: i for i, p in enumerate(itertools.combinations(range(1, 46), 2))}
    obs = np.zeros(990, dtype=np.int32)
    for d in draws:
        balls = d["all7"]
        for a, b in itertools.combinations(sorted(balls), 2):
            obs[pair_idx[(a, b)]] += 1

    total_pair_slots = n_draws * 21
    expected = total_pair_slots / 990  # 26.2 if 1234
    var_obs = float(np.var(obs, ddof=0))

    # Chi2 vs flat expected (independence assumption FALSE — report + caveat)
    exp = np.full(990, expected)
    chi2 = chi2_gof(obs.astype(float), exp)

    # Permutation null: shuffle labels 1..45, remap balls, keep 6+1 structure
    labels = np.arange(1, 46)
    # Precompute ball arrays
    ball_arr = np.array([d["all7"] for d in draws], dtype=np.int16)  # (n,7)

    null_vars = np.empty(N_PERM, dtype=np.float64)
    print(f"pair permutation null x{N_PERM}...", flush=True)
    for t in range(N_PERM):
        # random permutation of labels: old->new
        perm = NP_RNG.permutation(labels)
        # map: number k -> perm[k-1]
        mapped = perm[ball_arr - 1]
        cnt = np.zeros(990, dtype=np.int32)
        for row in mapped:
            srow = np.sort(row)
            for a, b in itertools.combinations(srow.tolist(), 2):
                cnt[pair_idx[(a, b)]] += 1
        null_vars[t] = float(np.var(cnt, ddof=0))
        if (t + 1) % 1000 == 0:
            print(f"  perm {t+1}/{N_PERM}", flush=True)

    p_perm = float(np.mean(null_vars >= var_obs))
    # top/bottom 10 pairs
    order = np.argsort(obs)
    bottom = order[:10]
    top = order[-10:][::-1]
    inv = {i: p for p, i in pair_idx.items()}

    def pack(idxs):
        return [
            {"pair": list(inv[int(i)]), "count": int(obs[i]), "rr": float(obs[i] / expected)}
            for i in idxs
        ]

    # Multiple testing: per-pair vs Binomial? Use z vs null mean/sd of single pair under perm
    # Simpler: BH-FDR on poisson/binomial approx vs expected (caveat), report survivors
    # Under hypergeometric-ish: approximate Poisson(lambda=expected) two-sided
    pvals = []
    for c in obs:
        # two-sided poisson test
        # P(X>=c) + P(X<=c) style via scipy
        if c >= expected:
            p = float(stats.poisson.sf(c - 1, expected) + stats.poisson.cdf(2 * expected - c, expected))
        else:
            p = float(stats.poisson.cdf(c, expected) + stats.poisson.sf(2 * expected - c - 1, expected))
        pvals.append(min(1.0, max(0.0, p)))
    pvals = np.asarray(pvals)
    # BH
    m = len(pvals)
    order_p = np.argsort(pvals)
    ranks = np.empty(m, dtype=int)
    ranks[order_p] = np.arange(1, m + 1)
    q = pvals * m / ranks
    # enforce monotone
    q_sorted = np.minimum.accumulate(q[order_p][::-1])[::-1]
    qvals = np.empty(m)
    qvals[order_p] = np.minimum(1.0, q_sorted)
    n_fdr05 = int(np.sum(qvals <= 0.05))

    # Power: detectable RR for chi2 / count — approximate
    # For one pair, n_slots independent-ish: se ≈ sqrt(lambda)/lambda = 1/sqrt(lambda)
    # two-sided alpha=0.05/990 Bonferroni → z≈4.06; detectable RR deviation ≈ z*se
    z_bonf = float(stats.norm.ppf(1 - 0.05 / (2 * 990)))
    se_rr = 1.0 / math.sqrt(expected)
    min_rr_dev = z_bonf * se_rr
    # also uncorrected
    z05 = 1.96
    min_rr_dev_unc = z05 * se_rr

    return {
        "n_draws": n_draws,
        "n_pair_types": 990,
        "pair_slots": total_pair_slots,
        "expected_per_pair": expected,
        "obs_var": var_obs,
        "obs_mean": float(obs.mean()),
        "obs_min": int(obs.min()),
        "obs_max": int(obs.max()),
        "chi2_flat": chi2,
        "chi2_caveat": "쌍 비독립 → 카이제곱 단독해석 금지; 순열 병용",
        "perm": {
            "n": N_PERM,
            "null_var_mean": float(null_vars.mean()),
            "null_var_p5": float(np.percentile(null_vars, 5)),
            "null_var_p95": float(np.percentile(null_vars, 95)),
            "null_var_max": float(null_vars.max()),
            "obs_var": var_obs,
            "p_right": p_perm,
            "percentile_of_obs": float(stats.percentileofscore(null_vars, var_obs, kind="weak")),
        },
        "top10": pack(top),
        "bottom10": pack(bottom),
        "fdr": {"n_survive_q05": n_fdr05, "method": "BH on Poisson(approx) two-sided"},
        "power": {
            "expected": expected,
            "min_detectable_RR_dev_bonferroni": min_rr_dev,
            "min_detectable_RR_bonf": [1 - min_rr_dev, 1 + min_rr_dev],
            "min_detectable_RR_dev_uncorrected": min_rr_dev_unc,
            "min_detectable_RR_unc": [1 - min_rr_dev_unc, 1 + min_rr_dev_unc],
            "note": "대략 Poisson SE; 쌍 의존으로 실제 검정력은 더 약할 수 있음",
        },
        "triple_skip": {
            "reason": "C(45,3)=14190, 기대도수=1234*C(7,3)/14190≈3.04? wait recalc",
            # user said E<1 for triples — with main only C(6,3)=20: 1234*20/C(45,3)=24680/14190≈1.74
            # with 6+1: C(7,3)=35: 1234*35/14190≈3.04
            # User said E<1 — they may mean something else. Record both and follow user skip.
            "E_main_only": n_draws * comb(6, 3) / comb(45, 3),
            "E_main_bonus": n_draws * comb(7, 3) / comb(45, 3),
            "verdict": "검정 생략(지시) — 기대도수 희소·다중검정 벽",
        },
    }


def portfolio_audit():
    """K-V: last 100 draws review sets overlap."""
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE draw_no >= (SELECT MAX(draw_no)-99 FROM lotto_draws) "
        "ORDER BY draw_no, brain_tag"
    ).fetchall()
    con.close()
    by_draw: dict[int, dict[str, list]] = {}
    for draw_no, tag, js in rows:
        sets = json.loads(js)
        tuples = [tuple(sorted(s["nums"])) for s in sets]
        by_draw.setdefault(int(draw_no), {})[tag] = tuples

    draws = sorted(by_draw)
    total_sets = 0
    unique_sets = 0
    dup_instances = 0  # extras beyond first occurrence within draw all brains
    per_draw_dup_rates = []
    pairwise = Counter()  # brain pair -> identical combo count
    brains = ["stat", "markov", "review"]
    inter_jaccard_num = []  # mean |A∩B| for sets as number overlap avg

    for d in draws:
        all_list = []
        for b in brains:
            all_list.extend(by_draw[d].get(b, []))
        total_sets += len(all_list)
        uniq = set(all_list)
        unique_sets += len(uniq)
        dup = len(all_list) - len(uniq)
        dup_instances += dup
        per_draw_dup_rates.append(dup / len(all_list) if all_list else 0)

        # pairwise identical
        for i, a in enumerate(brains):
            for b in brains[i + 1 :]:
                sa, sb = set(by_draw[d].get(a, [])), set(by_draw[d].get(b, []))
                pairwise[f"{a}|{b}"] += len(sa & sb)

        # mean number intersection size across all set pairs from different brains
        sets_by_b = {b: by_draw[d].get(b, []) for b in brains}
        for i, a in enumerate(brains):
            for b in brains[i + 1 :]:
                for sa in sets_by_b[a]:
                    for sb in sets_by_b[b]:
                        inter_jaccard_num.append(len(set(sa) & set(sb)))

    # 100-game ticket scenario: if we emit 100 tickets from weekly coordinated output
    # Estimate effective k: simulate sampling 100 from recent pool with replacement of policy
    # Use empirical: average unique rate when taking all 15 sets/draw, scale to 100 tickets
    # Better: for each of last 100 draws, take the 15 sets; pool unique ratio
    # Scenario A: 100 tickets = concatenate sets until 100 (≈6.67 draws of 15) — use bootstrap
    all_recent = []
    for d in draws:
        for b in brains:
            all_recent.extend(by_draw[d].get(b, []))

    # Within-draw: if pick 100 games by repeating weekly 15-set pack with replacement across weeks
    # Estimate E[k] for 100 tickets drawn as: take ceil(100/15) random draws' full packs, then first 100
    # Simpler empirical: unique among first N sets in chronological concat
    chron = []
    for d in draws:
        for b in brains:
            chron.extend(by_draw[d].get(b, []))
    # sliding windows of 100 consecutive sets
    ks = []
    if len(chron) >= 100:
        for i in range(0, len(chron) - 100 + 1, 15):
            ks.append(len(set(chron[i : i + 100])))
    k_mean = float(np.mean(ks)) if ks else float("nan")
    # also: weekly pack unique then pad
    weekly_u = [len(set(sum((by_draw[d].get(b, []) for b in brains), []))) for d in draws]
    # 100 tickets ≈ 100/15 packs — E[unique] via inclusion rough: simulate
    sim_k = []
    for _ in range(2000):
        chosen = []
        while len(chosen) < 100:
            d = RNG.choice(draws)
            pack = []
            for b in brains:
                pack.extend(by_draw[d].get(b, []))
            RNG.shuffle(pack)
            for t in pack:
                chosen.append(t)
                if len(chosen) >= 100:
                    break
        sim_k.append(len(set(chosen)))
    k_sim = float(np.mean(sim_k))
    k_sim_p05 = float(np.percentile(sim_k, 5))
    k_sim_p95 = float(np.percentile(sim_k, 95))

    TOTAL = 8_145_060
    p_at_least_one = lambda k: k / TOTAL  # distinct tickets, 1등
    k_ideal = 100
    p_ideal = p_at_least_one(k_ideal)
    p_sim = p_at_least_one(k_sim)
    loss_ratio = k_sim / k_ideal
    improve_if_dedup = p_ideal / p_sim if p_sim > 0 else float("inf")

    return {
        "window": {"n_draws": len(draws), "min": min(draws) if draws else None, "max": max(draws) if draws else None},
        "sets_per_draw_nominal": 15,
        "total_set_instances": total_sets,
        "unique_set_instances_sum_over_draws": unique_sets,
        "exact_dup_count_within_draw_all_brains": dup_instances,
        "dup_rate_mean": float(np.mean(per_draw_dup_rates)),
        "pairwise_identical_combo_counts": dict(pairwise),
        "mean_number_intersection_cross_brain_sets": float(np.mean(inter_jaccard_num)) if inter_jaccard_num else None,
        "weekly_unique_among_15_mean": float(np.mean(weekly_u)) if weekly_u else None,
        "k_sliding100_sets_mean": k_mean,
        "k_sim_100tickets": {"mean": k_sim, "p05": k_sim_p05, "p95": k_sim_p95, "n_sim": 2000},
        "p_first_prize_at_least_one": {
            "formula": "k/8145060",
            "k_ideal_100": k_ideal,
            "p_ideal": p_ideal,
            "k_sim": k_sim,
            "p_sim": p_sim,
            "loss_fraction_vs_100": 1 - loss_ratio,
            "probability_multiplier_if_full_dedup_to_100": improve_if_dedup,
            "absolute_p_gain": p_ideal - p_sim,
        },
    }


def main():
    draws = load_draws()
    assert len(draws) == 1234, len(draws)
    print("STEP2 markov overlaps...", flush=True)
    markov = {f"lag{L}": overlap_test(draws, L) for L in (1, 2, 3)}
    print("STEP2 miss gaps...", flush=True)
    miss = miss_gap_test(draws)
    print("STEP2 pattern/balance...", flush=True)
    pat = pattern_balance_test(draws)
    print("STEP3 pairs...", flush=True)
    pairs = pair_layer_test(draws)
    print("STEP4 portfolio...", flush=True)
    port = portfolio_audit()

    # Premise extraction (text)
    premises = {
        "markov": {
            "claim": "회차 간 의존성 존재(직전 출현이 다음 분포에 영향)",
            "H0": "직전회차와 본번 중복개수 ~ Hypergeom 평균 0.8 (독립)",
            "result": markov["lag1"],
        },
        "miss_aux": {
            "claim": "미출현 간격이 기하분포(p=6/45)에서 이탈",
            "H0": "간격 ~ Geom(p=6/45), E=7.5",
            "result": miss,
        },
        "pattern_aux": {
            "claim": "형태(연속·쌍·AC 등)에 구조 존재 — 이론분포 대비 이탈 또는 비균등 제약 명분",
            "H0": "관측 형태통계 = C(45,6) 이론분포",
            "result_keys": ["consecutive_pairs", "sum"],
        },
        "balance_aux": {
            "claim": "홀짝·구간·합 균형에 구조(또는 이론 비균등) 존재",
            "H0": "관측 = 조합론 이론",
            "result_keys": ["odd_even", "zone", "sum", "ending_digit"],
        },
        "review": {
            "claim_extracted": "직전 회차 번호 재출현률이 평균보다 높으므로 carry boost로 가중",
            "testable": True,
            "note": "전제= '이월(재출현) 성향' — lag1 중복 검정과 동일 축. markov lag1 결과로 대리 판정.",
        },
        "referee_aux": {
            "claim_extracted": "최근(누적) best-match 성적이 좋은 뇌에 더 큰 융합 가중",
            "testable_as_premise_on_draws": False,
            "verdict": "전제 미정의(추첨 생성과정 전제가 아니라 메타가중 정책). K-M/K-N이 전달효율만 다룸.",
        },
    }

    out = {
        "meta": {"db": str(DB), "n_draws": 1234, "seed": 20260727, "n_perm": N_PERM},
        "K_T": {"markov": markov, "miss_aux": miss, "pattern_balance": pat, "premises": premises},
        "K_U": pairs,
        "K_V": port,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT, flush=True)
    # compact print
    print("MARKOV_LAG1", json.dumps(markov["lag1"]["chi2"], ensure_ascii=False))
    print("MISS", miss["verdict"], miss["ks"])
    print("PAIR_PERM_P", pairs["perm"]["p_right"], "FDR", pairs["fdr"])
    print("PORT_K", port["k_sim_100tickets"], port["p_first_prize_at_least_one"])


if __name__ == "__main__":
    main()
