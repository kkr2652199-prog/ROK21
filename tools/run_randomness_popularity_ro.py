# -*- coding: utf-8 -*-
"""랜덤성 정식검정 + 인기도 모델 (READ-ONLY, DB 쓰기 금지)."""
from __future__ import annotations

import json
import math
import random
import sqlite3
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260726_랜덤성검정"
SEED = 20260726
TRAIN_END = 1000
VAL_START = 1001


def load_draws() -> list[dict]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT draw_no, num1,num2,num3,num4,num5,num6,bonus,total_sales "
            "FROM lotto_draws ORDER BY draw_no"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def load_tier3() -> dict[int, dict]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT draw_no, winner_count, prize_per_game
            FROM testlotto_draw_prize_tiers
            WHERE tier_rank = 3
            """
        ).fetchall()
        return {int(r["draw_no"]): dict(r) for r in rows}
    finally:
        conn.close()


def nums_of(d: dict, with_bonus: bool = False) -> list[int]:
    ns = [int(d[f"num{i}"]) for i in range(1, 7)]
    if with_bonus:
        b = int(d.get("bonus") or 0)
        if 1 <= b <= 45 and b not in ns:
            ns = ns + [b]
    return ns


def bh_fdr(pvals: list[tuple[str, float]], alpha: float = 0.05) -> dict[str, Any]:
    """Benjamini-Hochberg. returns rejected ids at FDR alpha."""
    items = [(k, float(p)) for k, p in pvals if p == p]  # drop nan
    m = len(items)
    if m == 0:
        return {"alpha": alpha, "m": 0, "rejected": [], "details": []}
    order = sorted(range(m), key=lambda i: items[i][1])
    thresh_rank = 0
    details = []
    rejected = []
    for rank, i in enumerate(order, start=1):
        name, p = items[i]
        crit = alpha * rank / m
        details.append({"id": name, "p": p, "rank": rank, "bh_crit": crit, "pass": p <= crit})
    # BH: find largest rank with p<=crit, reject all up to that
    max_k = 0
    for d in details:
        if d["pass"]:
            max_k = d["rank"]
    for d in details:
        d["rejected"] = d["rank"] <= max_k and max_k > 0 and d["p"] <= (
            alpha * d["rank"] / m
        )
        # standard: reject all with rank <= max_k where max_k = max{i: p_(i) <= alpha*i/m}
    # recompute properly
    max_k = 0
    for d in sorted(details, key=lambda x: x["rank"]):
        if d["p"] <= alpha * d["rank"] / m:
            max_k = d["rank"]
    rejected = []
    for d in details:
        d["rejected"] = d["rank"] <= max_k
        if d["rejected"]:
            rejected.append(d["id"])
    return {
        "alpha": alpha,
        "m": m,
        "max_reject_rank": max_k,
        "rejected": rejected,
        "n_rejected": len(rejected),
        "details": sorted(details, key=lambda x: x["rank"]),
    }


def chi2_uniform_counts(counts: np.ndarray, expected_each: float) -> dict[str, Any]:
    exp = np.full(45, expected_each, dtype=float)
    # scipy chisquare
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        chi2, p = stats.chisquare(counts, f_exp=exp)
    # Cramer's V for goodness of fit: sqrt(chi2/(n*(k-1))) with n=sum counts, k=45
    n = float(counts.sum())
    v = math.sqrt(float(chi2) / (n * 44)) if n > 0 else 0.0
    return {
        "chi2": round(float(chi2), 6),
        "df": 44,
        "p": float(p),
        "cramers_v": round(v, 6),
        "n_counts_sum": int(n),
        "expected_each": round(expected_each, 6),
        "min_count": int(counts.min()),
        "max_count": int(counts.max()),
    }


def step1_frequency(draws: list[dict], with_bonus: bool, era: tuple[int, int] | None) -> dict:
    if era:
        lo, hi = era
        use = [d for d in draws if lo <= int(d["draw_no"]) <= hi]
        tag = f"{lo}_{hi}"
    else:
        use = draws
        tag = "all"
    counts = np.zeros(45, dtype=int)
    for d in use:
        for n in nums_of(d, with_bonus):
            counts[n - 1] += 1
    n_draws = len(use)
    # expected: main 6/45; with bonus effective 7/45 per draw
    picks = 7.0 if with_bonus else 6.0
    exp_each = n_draws * picks / 45.0
    res = chi2_uniform_counts(counts, exp_each)
    res["era"] = tag
    res["with_bonus"] = with_bonus
    res["n_draws"] = n_draws
    return res


def step1_transition(draws: list[dict], with_bonus: bool) -> dict[str, Any]:
    """45x45: rows=prev presence, cols=curr presence counts for each ordered pair ball i->j.
    Independence: for each (i,j) 2x2 table aggregated into one big test via contingency of
    transitions: count matrix T[i,j] = times j in curr when i in prev.
    Chi2 independence on flattened presence is heavy; use: contingency matrix of
    ball-from to ball-to among the 6*6 directed pairs per consecutive draws.
    """
    # Transition counts among drawn balls (with replacement across positions): 
    # for each consecutive pair of draws, for each a in prev, each b in curr, T[a,b] += 1
    T = np.zeros((45, 45), dtype=float)
    carries = []
    for i in range(1, len(draws)):
        prev = set(nums_of(draws[i - 1], with_bonus=False))  # carry is main-only
        curr_main = set(nums_of(draws[i], with_bonus=False))
        curr = set(nums_of(draws[i], with_bonus))
        prev_b = set(nums_of(draws[i - 1], with_bonus))
        carries.append(len(prev & curr_main))
        for a in prev_b:
            for b in curr:
                T[a - 1, b - 1] += 1

    # Chi-square independence on contingency T (row/col association)
    # Avoid zero expected: add small epsilon or use contingency with mask
    # Standard chi2_contingency
    # If some cells zero, scipy still works with expected from margins
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        chi2, p, dof, expected = stats.chi2_contingency(T + 1e-12)
    n = T.sum()
    # Cramer's V
    k = min(T.shape) - 1
    v = math.sqrt(chi2 / (n * k)) if n > 0 and k > 0 else 0.0

    # Carry vs Hypergeometric(N=45,K=6,n=6)
    # P(X=k) = C(6,k)*C(39,6-k)/C(45,6)
    carry_obs = np.bincount(carries, minlength=7)[:7].astype(float)
    hg = stats.hypergeom(45, 6, 6)
    exp_carry = np.array([hg.pmf(k) * len(carries) for k in range(7)])
    # merge sparse tails if needed for chisquare
    # use all 0..6
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # filter bins with exp < 5 by merging
        c_obs = carry_obs.copy()
        c_exp = exp_carry.copy()
        # merge 5+6 if small
        if c_exp[5] + c_exp[6] < 5 or c_obs[5] + c_obs[6] < 5:
            c_obs = np.concatenate([c_obs[:5], [c_obs[5] + c_obs[6]]])
            c_exp = np.concatenate([c_exp[:5], [c_exp[5] + c_exp[6]]])
        chi2_c, p_c = stats.chisquare(c_obs, f_exp=c_exp * (c_obs.sum() / c_exp.sum()))

    mean_carry = float(np.mean(carries))
    return {
        "with_bonus": with_bonus,
        "transition_chi2": round(float(chi2), 4),
        "transition_df": int(dof),
        "transition_p": float(p),
        "transition_cramers_v": round(v, 6),
        "n_transitions_cells_sum": int(n),
        "carry": {
            "n_pairs": len(carries),
            "mean_obs": round(mean_carry, 6),
            "mean_hypergeom_E": round(6 * 6 / 45, 6),
            "hist_obs_0to6": [int(x) for x in carry_obs],
            "hist_exp_0to6": [round(float(x), 4) for x in exp_carry],
            "chi2": round(float(chi2_c), 6),
            "p": float(p_c),
        },
    }


def step1_gaps(draws: list[dict], with_bonus: bool) -> dict[str, Any]:
    """KS: pooled inter-arrival gaps vs Geometric(p).
    For main: p = 6/45 per draw (approx, ignoring without-replacement).
    For bonus-inclusive appearance: p = 7/45.
    """
    p_appear = 7.0 / 45.0 if with_bonus else 6.0 / 45.0
    last_seen = {n: None for n in range(1, 46)}
    gaps: list[int] = []
    for idx, d in enumerate(draws):
        present = set(nums_of(d, with_bonus))
        for n in range(1, 46):
            if n in present:
                if last_seen[n] is not None:
                    gaps.append(idx - last_seen[n])  # draws between + including current? 
                    # inter-arrival in draws: if seen at t0 and t1, gap = t1-t0
                last_seen[n] = idx
    gaps_arr = np.array(gaps, dtype=float)
    # Geometric with support starting at 1: P(G=k)=(1-p)^{k-1}p, mean 1/p
    # scipy.stats.geom(p) is number of trials until first success, min=1
    # KS against continuous approx or use discrete KS via cdf
    geom = stats.geom(p_appear)

    def cdf(x):
        return geom.cdf(x)

    # ks_1samp against geom cdf
    ks_stat, ks_p = stats.ks_1samp(gaps_arr, cdf)
    return {
        "with_bonus": with_bonus,
        "n_gaps": int(len(gaps_arr)),
        "gap_mean_obs": round(float(gaps_arr.mean()), 6),
        "gap_mean_geom": round(1.0 / p_appear, 6),
        "p_appear": p_appear,
        "ks_stat": round(float(ks_stat), 6),
        "ks_p": float(ks_p),
        "note": "기하분포 근사(복원추출). 비복원 내 회차 의존은 미모형화.",
    }


def bootstrap_mean_ci(xs: list[float], n_boot: int = 4000, seed: int = SEED) -> dict:
    rng = random.Random(seed)
    n = len(xs)
    if n == 0:
        return {"mean": 0.0, "ci95": [0.0, 0.0], "n": 0}
    boots = []
    for _ in range(n_boot):
        boots.append(sum(xs[rng.randrange(n)] for _ in range(n)) / n)
    boots.sort()
    return {
        "mean": round(sum(xs) / n, 6),
        "ci95": [round(boots[int(0.025 * n_boot)], 6), round(boots[int(0.975 * n_boot)], 6)],
        "n": n,
    }


def step2_predictability(draws: list[dict]) -> dict[str, Any]:
    by_no = {int(d["draw_no"]): d for d in draws}
    train = [d for d in draws if int(d["draw_no"]) <= TRAIN_END]
    val = [d for d in draws if VAL_START <= int(d["draw_no"]) <= 1234]
    # precompute train freqs
    freq = np.zeros(45)
    for d in train:
        for n in nums_of(d, False):
            freq[n - 1] += 1
    freq_p = freq / freq.sum()

    # markov: P(j|i appeared last) ~ count
    trans = np.ones((45, 45))  # Laplace
    for i in range(1, len(train)):
        prev = nums_of(train[i - 1], False)
        curr = nums_of(train[i], False)
        for a in prev:
            for b in curr:
                trans[a - 1, b - 1] += 1
    trans = trans / trans.sum(axis=1, keepdims=True)

    def probs_freq(_hist: list[dict]) -> np.ndarray:
        return freq_p.copy()

    def probs_markov(hist: list[dict]) -> np.ndarray:
        if not hist:
            return freq_p.copy()
        prev = nums_of(hist[-1], False)
        p = np.zeros(45)
        for a in prev:
            p += trans[a - 1]
        p /= max(p.sum(), 1e-12)
        return p

    def probs_recency(hist: list[dict], half_life: int = 50) -> np.ndarray:
        w = np.zeros(45)
        for i, d in enumerate(hist):
            age = len(hist) - 1 - i
            ww = 0.5 ** (age / half_life)
            for n in nums_of(d, False):
                w[n - 1] += ww
        if w.sum() <= 0:
            return np.ones(45) / 45
        return w / w.sum()

    models = {
        "freq": probs_freq,
        "markov": probs_markov,
        "recency": probs_recency,
    }
    out = {}
    all_hist = list(train)
    # walk validation in order, expanding hist with actual after scoring
    for name, fn in models.items():
        hist = list(train)
        hits = []
        for d in val:
            p = fn(hist)
            top6 = set(np.argsort(-p)[:6] + 1)
            actual = set(nums_of(d, False))
            hits.append(float(len(top6 & actual)))
            hist.append(d)
        ci = bootstrap_mean_ci(hits, seed=SEED + hash(name) % 1000)
        out[name] = {
            **ci,
            "theory_random_mean": 0.8,
            "ci_lower_gt_0p80": ci["ci95"][0] > 0.80,
        }
    any_yes = any(v["ci_lower_gt_0p80"] for v in out.values())
    return {
        "train": f"1..{TRAIN_END}",
        "val": f"{VAL_START}..1234",
        "n_val": len(val),
        "models": out,
        "any_ci_lower_gt_0p80": any_yes,
        "verdict_abandon_hit_learning": (not any_yes),
    }


def ending_hist(nums: list[int]) -> list[int]:
    h = [0] * 10
    for n in nums:
        h[n % 10] += 1
    return h


def band_hist(nums: list[int]) -> list[int]:
    # 1-10,11-20,...,41-45 → 5 bands
    h = [0] * 5
    for n in nums:
        h[min(4, (n - 1) // 10)] += 1
    return h


def same_ending_pairs(nums: list[int]) -> int:
    ends = [n % 10 for n in nums]
    return sum(1 for i in range(6) for j in range(i + 1, 6) if ends[i] == ends[j])


def has_arithmetic(nums: list[int]) -> int:
    s = sorted(nums)
    # any 3-term AP
    st = set(s)
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            d = s[j] - s[i]
            if d > 0 and (s[j] + d) in st:
                return 1
    return 0


def diagonal_flags(nums: list[int]) -> list[int]:
    """7-column slip geometry: col=(n-1)%7, row=(n-1)//7."""
    cells = [((n - 1) // 7, (n - 1) % 7) for n in nums]
    # main diagonal-ish: row-col constant or row+col
    diffs = [r - c for r, c in cells]
    sums = [r + c for r, c in cells]
    max_same_diff = max(diffs.count(d) for d in set(diffs))
    max_same_sum = max(sums.count(s) for s in set(sums))
    # straight line same row or col
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    max_row = max(rows.count(r) for r in set(rows))
    max_col = max(cols.count(c) for c in set(cols))
    return [max_same_diff, max_same_sum, max_row, max_col]


def build_features(nums: list[int], prev: list[int] | None) -> np.ndarray:
    s = sorted(nums)
    n_le31 = sum(1 for x in s if x <= 31)
    n_le12 = sum(1 for x in s if x <= 12)
    odd = sum(1 for x in s if x % 2)
    consec = sum(1 for i in range(5) if s[i + 1] == s[i] + 1)
    carry = 0 if prev is None else len(set(s) & set(prev))
    dummies = [0] * 45
    for x in s:
        dummies[x - 1] = 1
    feats = (
        [n_le31, n_le12, sum(s), odd, consec, carry]
        + dummies
        + ending_hist(s)
        + band_hist(s)
        + [same_ending_pairs(s), has_arithmetic(s)]
        + diagonal_flags(s)
    )
    return np.array(feats, dtype=float)


def spearman(y_true, y_pred) -> float:
    r, _ = stats.spearmanr(y_true, y_pred)
    return float(r) if r == r else 0.0


def step3_popularity(draws: list[dict], tier3: dict[int, dict]) -> dict[str, Any]:
    rows = []
    prev = None
    for d in draws:
        dn = int(d["draw_no"])
        t = tier3.get(dn)
        sales = float(d.get("total_sales") or 0)
        if not t or sales <= 0 or int(t["winner_count"] or 0) <= 0:
            prev = nums_of(d, False)
            continue
        nums = nums_of(d, False)
        y = math.log(int(t["winner_count"]) / sales)
        x = build_features(nums, prev)
        rows.append(
            {
                "draw_no": dn,
                "x": x,
                "y": y,
                "prize": float(t["prize_per_game"] or 0),
                "winners": int(t["winner_count"]),
            }
        )
        prev = nums

    train = [r for r in rows if r["draw_no"] <= TRAIN_END]
    val = [r for r in rows if r["draw_no"] >= VAL_START]
    Xtr = np.vstack([r["x"] for r in train])
    ytr = np.array([r["y"] for r in train])
    Xva = np.vstack([r["x"] for r in val])
    yva = np.array([r["y"] for r in val])
    prize_va = np.array([r["prize"] for r in val])

    # univariate baseline: sum feature index 2
    sum_tr = Xtr[:, 2]
    sum_va = Xva[:, 2]
    r_uni = float(np.corrcoef(sum_tr, ytr)[0, 1])
    # predict val by univariate ridge on sum only
    slope = np.polyfit(sum_tr, ytr, 1)
    yhat_uni = slope[0] * sum_va + slope[1]
    r2_uni = float(r2_score(yva, yhat_uni))
    sp_uni = spearman(yva, yhat_uni)

    scaler = StandardScaler()
    Xtr_s = scaler.fit_transform(Xtr)
    Xva_s = scaler.transform(Xva)

    models: dict[str, Any] = {}
    # Ridge
    ridge = Ridge(alpha=10.0, random_state=SEED)
    ridge.fit(Xtr_s, ytr)
    pred_r = ridge.predict(Xva_s)
    models["ridge"] = {
        "val_r2": round(float(r2_score(yva, pred_r)), 6),
        "val_spearman": round(spearman(yva, pred_r), 6),
        "pred": pred_r,
    }
    # GBM classic
    gbm = GradientBoostingRegressor(
        random_state=SEED, n_estimators=200, max_depth=3, learning_rate=0.05
    )
    gbm.fit(Xtr, ytr)
    pred_g = gbm.predict(Xva)
    models["gbm"] = {
        "val_r2": round(float(r2_score(yva, pred_g)), 6),
        "val_spearman": round(spearman(yva, pred_g), 6),
        "pred": pred_g,
    }
    # HistGBM second
    hgb = HistGradientBoostingRegressor(
        random_state=SEED, max_depth=4, learning_rate=0.05, max_iter=200
    )
    hgb.fit(Xtr, ytr)
    pred_h = hgb.predict(Xva)
    models["hist_gbm"] = {
        "val_r2": round(float(r2_score(yva, pred_h)), 6),
        "val_spearman": round(spearman(yva, pred_h), 6),
        "pred": pred_h,
    }

    def quintile_ratio(pred: np.ndarray) -> dict:
        # higher y = more winners/sales = more popular
        order = np.argsort(pred)
        n = len(pred)
        q = max(1, n // 5)
        unpop_idx = order[:q]  # lowest predicted popularity
        pop_idx = order[-q:]
        u_prize = float(prize_va[unpop_idx].mean())
        p_prize = float(prize_va[pop_idx].mean())
        u_w = float(np.array([val[i]["winners"] for i in unpop_idx]).mean())
        p_w = float(np.array([val[i]["winners"] for i in pop_idx]).mean())
        return {
            "n_each": q,
            "unpop_avg_prize": round(u_prize, 2),
            "pop_avg_prize": round(p_prize, 2),
            "prize_ratio_unpop_over_pop": round(u_prize / p_prize, 6) if p_prize > 0 else None,
            "unpop_avg_winners": round(u_w, 4),
            "pop_avg_winners": round(p_w, 4),
            "beats_1p20": (u_prize / p_prize > 1.20) if p_prize > 0 else False,
        }

    results = {}
    for name, m in models.items():
        results[name] = {
            "val_r2": m["val_r2"],
            "val_spearman": m["val_spearman"],
            "vs_univariate_r": {
                "univariate_pearson_train_sum": round(r_uni, 6),
                "univariate_val_r2": round(r2_uni, 6),
                "univariate_val_spearman": round(sp_uni, 6),
                "model_minus_uni_spearman": round(m["val_spearman"] - sp_uni, 6),
                "model_minus_uni_r2": round(m["val_r2"] - r2_uni, 6),
            },
            "quintile20": quintile_ratio(m["pred"]),
        }

    return {
        "label": "log(tier3_winners / total_sales)",
        "train": f"1..{TRAIN_END}",
        "val": f"{VAL_START}..1234",
        "n_train": len(train),
        "n_val": len(val),
        "n_features": int(Xtr.shape[1]),
        "feature_groups": [
            "n_le31,n_le12,sum,odd,consec,carry",
            "num_dummy_1_45",
            "ending_0_9",
            "band_5",
            "same_ending_pairs,arithmetic3",
            "diag_diff,diag_sum,max_row,max_col",
        ],
        "univariate_sum_pearson_train": round(r_uni, 6),
        "models": results,
        "best_prize_ratio": max(
            (results[k]["quintile20"]["prize_ratio_unpop_over_pop"] or 0) for k in results
        ),
        "any_beats_1p20": any(results[k]["quintile20"]["beats_1p20"] for k in results),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    draws = load_draws()
    assert len(draws) >= 1234, f"expected >=1234 draws, got {len(draws)}"
    draws = [d for d in draws if int(d["draw_no"]) <= 1234]
    tier3 = load_tier3()

    pvals: list[tuple[str, float]] = []
    step1: dict[str, Any] = {"frequency": {}, "eras": {}, "transition": {}, "gaps": {}}

    for bonus in (False, True):
        key = "with_bonus" if bonus else "main_only"
        freq_all = step1_frequency(draws, bonus, None)
        step1["frequency"][key] = freq_all
        pvals.append((f"freq_all_{key}", freq_all["p"]))
        eras = {}
        for era in ((1, 400), (401, 800), (801, 1234)):
            er = step1_frequency(draws, bonus, era)
            eras[f"{era[0]}_{era[1]}"] = er
            pvals.append((f"freq_{era[0]}_{era[1]}_{key}", er["p"]))
        step1["eras"][key] = eras
        tr = step1_transition(draws, bonus)
        step1["transition"][key] = tr
        pvals.append((f"transition_{key}", tr["transition_p"]))
        pvals.append((f"carry_{key}", tr["carry"]["p"]))
        gp = step1_gaps(draws, bonus)
        step1["gaps"][key] = gp
        pvals.append((f"gaps_ks_{key}", gp["ks_p"]))

    fdr = bh_fdr(pvals, 0.05)
    step1["bh_fdr"] = fdr
    step1["bias_survives_fdr5pct"] = fdr["n_rejected"] > 0
    step1["verdict_YES_NO"] = "YES" if fdr["n_rejected"] > 0 else "NO"

    step2 = step2_predictability(draws)
    step3 = step3_popularity(draws, tier3)

    # strip huge pred arrays from step3 already done
    payload = {
        "ok": True,
        "readonly": True,
        "n_draws": len(draws),
        "step1_randomness": step1,
        "step2_predictability_ceiling": step2,
        "step3_popularity": step3,
    }
    OUT.joinpath("summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # also split files
    OUT.joinpath("step1_randomness.json").write_text(
        json.dumps(step1, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT.joinpath("step2_predictability.json").write_text(
        json.dumps(step2, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT.joinpath("step3_popularity.json").write_text(
        json.dumps(step3, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "step1_verdict": step1["verdict_YES_NO"],
        "fdr_rejected": fdr["rejected"],
        "step2_any_ci_gt_0p80": step2["any_ci_lower_gt_0p80"],
        "step2_models": {k: {kk: vv for kk, vv in v.items() if kk != "pred"} for k, v in step2["models"].items()},
        "step3_best_ratio": step3["best_prize_ratio"],
        "step3_beats_1p20": step3["any_beats_1p20"],
        "step3_models": {
            k: {
                "r2": v["val_r2"],
                "spearman": v["val_spearman"],
                "ratio": v["quintile20"]["prize_ratio_unpop_over_pop"],
                "vs_uni_sp": v["vs_univariate_r"]["model_minus_uni_spearman"],
            }
            for k, v in step3["models"].items()
        },
    }, ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
