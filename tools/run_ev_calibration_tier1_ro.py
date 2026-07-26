# -*- coding: utf-8 -*-
"""EV 수령배율 보정 + tier1 완화 오프라인 시뮬 (READ-ONLY · filters.py 미수정)."""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from tools.run_meta_hybrid_wf import _load_traps  # noqa: E402
from tools.run_meta_vote2_wf import _draws_before, _load_draws  # noqa: E402
from tools.run_portfolio_set_picker_wf import pick_portfolio  # noqa: E402
from tools.run_set_picker_wf import _load_tagged_sets  # noqa: E402

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260726_EV보정"
PREV = ROOT / "docs" / "benchmarks" / "20260726_EV리랭커" / "summary.json"
SEED = 20260726
VAL_LO, VAL_HI = 1001, 1234
LAST_N = 100
K = 3


def load_tier3() -> dict[int, dict]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT draw_no, winner_count, prize_per_game FROM testlotto_draw_prize_tiers WHERE tier_rank=3"
        ).fetchall()
        return {int(r["draw_no"]): dict(r) for r in rows}
    finally:
        conn.close()


def feat(nums: list[int], prev: list[int] | None) -> np.ndarray:
    s = sorted(nums)
    return np.array(
        [
            sum(1 for x in s if x <= 31),
            sum(1 for x in s if x <= 12),
            float(sum(s)),
            0.0 if prev is None else float(len(set(s) & set(prev))),
        ],
        dtype=float,
    )


def train_ridge(X: np.ndarray, y: np.ndarray):
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    m = Ridge(alpha=10.0, random_state=SEED)
    m.fit(Xs, y)
    return m, scaler


def predict_pop(model, scaler, nums, prev) -> float:
    return float(model.predict(scaler.transform(feat(nums, prev).reshape(1, -1)))[0])


def build_xy(draws, tier3, before_draw: int, y_perm: dict[int, float] | None = None):
    xs, ys, dns = [], [], []
    prev = None
    for d in draws:
        dn = int(d["draw_no"])
        if dn >= before_draw:
            break
        t = tier3.get(dn)
        sales = float(d.get("total_sales") or 0)
        if not t or sales <= 0 or int(t["winner_count"] or 0) <= 0:
            prev = sorted_nums(d)
            continue
        y = (
            y_perm[dn]
            if y_perm is not None and dn in y_perm
            else math.log(int(t["winner_count"]) / sales)
        )
        xs.append(feat(sorted_nums(d), prev))
        ys.append(y)
        dns.append(dn)
        prev = sorted_nums(d)
    if len(xs) < 50:
        return None
    return np.vstack(xs), np.array(ys), dns


def ols_y_on_hat(y: np.ndarray, hat: np.ndarray) -> dict:
    # y = a + b * hat
    lr = LinearRegression()
    lr.fit(hat.reshape(-1, 1), y)
    pred = lr.predict(hat.reshape(-1, 1))
    resid = y - pred
    n = len(y)
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    # slope SE
    x = hat - hat.mean()
    sxx = float(np.sum(x**2))
    sigma = math.sqrt(ss_res / max(1, n - 2))
    b_se = sigma / math.sqrt(sxx) if sxx > 0 else float("nan")
    return {
        "a": float(lr.intercept_),
        "b": float(lr.coef_[0]),
        "b_se": float(b_se),
        "r2": float(r2),
        "resid_std": float(sigma),
        "n": n,
    }


def filter_t0(nums: list[int]) -> bool:
    s = sum(nums)
    odd = sum(1 for n in nums if n % 2 == 1)
    ranges = len({(n - 1) // 10 for n in nums})
    consec = 1
    max_c = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1] + 1:
            consec += 1
            max_c = max(max_c, consec)
        else:
            consec = 1
    if s < 80 or s > 210:
        return False
    if odd == 0 or odd == 6:
        return False
    if ranges <= 1:
        return False
    if max_c >= 4:
        return False
    return True


def filter_t1(nums: list[int]) -> bool:
    """합만 60~240, 나머지 T0."""
    s = sum(nums)
    odd = sum(1 for n in nums if n % 2 == 1)
    ranges = len({(n - 1) // 10 for n in nums})
    consec = 1
    max_c = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1] + 1:
            consec += 1
            max_c = max(max_c, consec)
        else:
            consec = 1
    if s < 60 or s > 240:
        return False
    if odd == 0 or odd == 6:
        return False
    if ranges <= 1:
        return False
    if max_c >= 4:
        return False
    return True


def filter_t2(nums: list[int]) -> bool:
    """홀짝 0/6 허용, 합·구간·연속은 T0."""
    s = sum(nums)
    ranges = len({(n - 1) // 10 for n in nums})
    consec = 1
    max_c = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1] + 1:
            consec += 1
            max_c = max(max_c, consec)
        else:
            consec = 1
    if s < 80 or s > 210:
        return False
    if ranges <= 1:
        return False
    if max_c >= 4:
        return False
    return True


def filter_t3(nums: list[int]) -> bool:
    """T1+T2: 합60~240, 홀짝 자유, 구간·연속 T0."""
    s = sum(nums)
    ranges = len({(n - 1) // 10 for n in nums})
    consec = 1
    max_c = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1] + 1:
            consec += 1
            max_c = max(max_c, consec)
        else:
            consec = 1
    if s < 60 or s > 240:
        return False
    if ranges <= 1:
        return False
    if max_c >= 4:
        return False
    return True


def is_extreme(nums: list[int]) -> bool:
    s = sorted(nums)
    # 1..6 consecutive block or all <=10 or all >=40
    if s == list(range(s[0], s[0] + 6)):
        return True
    if max(s) <= 10 or min(s) >= 40:
        return True
    return False


def pick_ev_top(entries, evs, k=K):
    order = sorted(range(len(entries)), key=lambda i: -evs[i])
    return [sorted(entries[i]["nums"]) for i in order[:k]]


def pick_coverage(entries, k=K):
    from tools.run_portfolio_set_picker_wf import jaccard

    remaining = list(range(len(entries)))
    picked, covered = [], set()
    while len(picked) < k and remaining:
        best_i, best_sc = None, -1e9
        for i in remaining:
            s = set(entries[i]["nums"])
            gain = len(s - covered)
            pen = (
                sum(jaccard(s, set(p)) for p in picked) / len(picked) if picked else 0
            )
            sc = gain - 0.5 * pen
            if sc > best_sc:
                best_sc, best_i = sc, i
        remaining.remove(best_i)
        nums = sorted(entries[best_i]["nums"])
        picked.append(nums)
        covered |= set(nums)
    return picked


def pick_hybrid(entries, evs, k=K):
    ev_arr = np.array(evs, dtype=float)
    span = max(1e-9, float(ev_arr.max() - ev_arr.min()))
    ev_n = (ev_arr - ev_arr.min()) / span
    remaining = list(range(len(entries)))
    picked, covered = [], set()
    while len(picked) < k and remaining:
        best_i, best_sc = None, -1e9
        for i in remaining:
            s = set(entries[i]["nums"])
            sc = 0.5 * float(ev_n[i]) + 0.5 * (len(s - covered) / 6.0)
            if sc > best_sc:
                best_sc, best_i = sc, i
        remaining.remove(best_i)
        nums = sorted(entries[best_i]["nums"])
        picked.append(nums)
        covered |= set(nums)
    return picked


def mean_hit(sets, actual):
    a = set(actual)
    return sum(len(set(s) & a) for s in sets) / max(1, len(sets))


def arm_deltas_from_prev_summary() -> dict[str, float]:
    prev = json.loads(PREV.read_text(encoding="utf-8"))
    out = {}
    for arm, meta in prev["arms"].items():
        # δ = log(pred_ratio) = mean_ev - mean_ev_A
        # recovered from ratio
        r = float(meta["expected_payout_ratio_vs_A"])
        out[arm] = {
            "pred_ratio": r,
            "pred_log_diff": math.log(r) if r > 0 else 0.0,
            "mean_ev_score": float(meta["mean_ev_score"]),
            "mean_hit": meta["mean_hit"],
        }
    return out


def main() -> int:
    init_testlotto_db()
    draws = _load_draws()
    tier3 = load_tier3()
    tagged = _load_tagged_sets()
    traps = _load_traps()
    rng = random.Random(SEED)

    # ---------- P1-1 fixed split calibration ----------
    # Train on 1..1000, hat on val actual winning sets
    packed = build_xy(draws, tier3, VAL_LO)
    assert packed is not None
    Xtr, ytr, _ = packed
    model, scaler = train_ridge(Xtr, ytr)

    y_val, hat_val, winners_val = [], [], []
    prev = None
    for d in draws:
        dn = int(d["draw_no"])
        if dn < VAL_LO:
            prev = sorted_nums(d)
            continue
        if dn > VAL_HI:
            break
        t = tier3.get(dn)
        sales = float(d.get("total_sales") or 0)
        if not t or sales <= 0 or int(t["winner_count"] or 0) <= 0:
            prev = sorted_nums(d)
            continue
        nums = sorted_nums(d)
        y = math.log(int(t["winner_count"]) / sales)
        hat = predict_pop(model, scaler, nums, prev)
        y_val.append(y)
        hat_val.append(hat)
        winners_val.append(int(t["winner_count"]))
        prev = nums

    y_val_a = np.array(y_val)
    hat_val_a = np.array(hat_val)
    cal_fixed = ols_y_on_hat(y_val_a, hat_val_a)

    # walk-forward b: for each val draw, train <N, hat on actual, then OLS on all pairs
    y_wf, hat_wf = [], []
    b_per_draw = []
    prev = None
    # progressive store for rolling OLS optional; collect pairs then overall OLS + rolling last-50 slope
    for d in draws:
        dn = int(d["draw_no"])
        if dn < VAL_LO:
            prev = sorted_nums(d)
            continue
        if dn > VAL_HI:
            break
        t = tier3.get(dn)
        sales = float(d.get("total_sales") or 0)
        packed_n = build_xy(draws, tier3, dn)
        if packed_n is None or not t or sales <= 0:
            prev = sorted_nums(d)
            continue
        Xn, yn, _ = packed_n
        mn, sn = train_ridge(Xn, yn)
        nums = sorted_nums(d)
        if int(t["winner_count"] or 0) <= 0:
            prev = nums
            continue
        y = math.log(int(t["winner_count"]) / sales)
        hat = predict_pop(mn, sn, nums, prev)
        y_wf.append(y)
        hat_wf.append(hat)
        if len(y_wf) >= 30:
            sub = ols_y_on_hat(np.array(y_wf[-50:]), np.array(hat_wf[-50:]))
            b_per_draw.append({"draw_no": dn, "b_roll50": sub["b"]})
        prev = nums
    cal_wf = ols_y_on_hat(np.array(y_wf), np.array(hat_wf))

    # ---------- P1-2 realized ratios with CI (b unc + residual) ----------
    arms_prev = arm_deltas_from_prev_summary()
    b = cal_wf["b"]  # prefer WF calibration for application
    b_se = cal_wf["b_se"]
    sigma = cal_wf["resid_std"]
    n_val = cal_wf["n"]
    # effective n for arm mean contrast: last100 * K (approx)
    n_eff = LAST_N * K

    def realized_ci(pred_log_diff: float, n_boot: int = 5000) -> dict:
        """realized = exp(b * δ); bootstrap OLS b + residual noise on contrast."""
        ratios = []
        for _ in range(n_boot):
            idx = [rng.randrange(n_val) for _ in range(n_val)]
            yb = y_wf_a[idx] if False else None
        # use fixed-split arrays length match wf
        y_arr = np.array(y_wf)
        h_arr = np.array(hat_wf)
        n = len(y_arr)
        ratios = []
        for _ in range(n_boot):
            idx = [rng.randrange(n) for _ in range(n)]
            fit = ols_y_on_hat(y_arr[idx], h_arr[idx])
            # residual noise for mean contrast of two arms
            eps = rng.gauss(0.0, fit["resid_std"] * math.sqrt(2.0 / n_eff))
            log_r = fit["b"] * pred_log_diff + eps
            ratios.append(math.exp(log_r))
        ratios.sort()
        point = math.exp(b * pred_log_diff)
        return {
            "realized_ratio": round(point, 6),
            "ci95": [
                round(ratios[int(0.025 * n_boot)], 6),
                round(ratios[int(0.975 * n_boot)], 6),
            ],
            "ci_width": round(
                ratios[int(0.975 * n_boot)] - ratios[int(0.025 * n_boot)], 6
            ),
        }

    realized_table = []
    for arm, meta in arms_prev.items():
        δ = meta["pred_log_diff"]
        ci = realized_ci(δ)
        old_ci_w = None
        # from prev summary
        prev_sum = json.loads(PREV.read_text(encoding="utf-8"))
        old = prev_sum["arms"][arm]["payout_ratio_ci95_vs_A"]
        old_w = abs(old[1] - old[0])
        realized_table.append(
            {
                "arm": arm,
                "pred_ratio_old": meta["pred_ratio"],
                "pred_log_diff": round(δ, 6),
                "b_used": round(b, 6),
                "b_source": "walk_forward_OLS_on_val_pairs",
                "realized_ratio": ci["realized_ratio"],
                "realized_ci95": ci["ci95"],
                "realized_ci_width": ci["ci_width"],
                "old_ci_width": round(old_w, 6),
                "ci_wider_than_old": ci["ci_width"] > old_w + 1e-9,
                "mean_hit": meta["mean_hit"],
            }
        )

    # P1-3 CV
    w_arr = np.array(winners_val, dtype=float)
    cv = float(w_arr.std() / w_arr.mean()) if w_arr.mean() > 0 else float("nan")

    # ---------- P1-4 placebo ----------
    # shuffle y by draw among training labels
    all_y_by_dn = {}
    prev = None
    for d in draws:
        dn = int(d["draw_no"])
        t = tier3.get(dn)
        sales = float(d.get("total_sales") or 0)
        if t and sales > 0 and int(t["winner_count"] or 0) > 0:
            all_y_by_dn[dn] = math.log(int(t["winner_count"]) / sales)
        prev = sorted_nums(d)
    dns_sorted = sorted(all_y_by_dn)
    ys_shuffled = list(all_y_by_dn[d] for d in dns_sorted)
    rng2 = random.Random(SEED + 7)
    rng2.shuffle(ys_shuffled)
    y_perm = {d: ys_shuffled[i] for i, d in enumerate(dns_sorted)}

    # recompute arm mean_ev with placebo models on last 100 (same selection? or re-pick)
    # Pipeline bias test: re-pick B vs A with placebo scores → ratio>1?
    use = [
        d
        for d in draws
        if len(tagged.get(int(d["draw_no"]), [])) >= 5
    ][-LAST_N:]
    evA, evB, evD = [], [], []
    for d in use:
        td = int(d["draw_no"])
        entries = tagged[td][:15]
        before = _draws_before(draws, td)
        prevn = sorted_nums(before[-1]) if before else None
        packed_n = build_xy(draws, tier3, td, y_perm=y_perm)
        if packed_n is None or len(entries) < K:
            continue
        Xn, yn, _ = packed_n
        mn, sn = train_ridge(Xn, yn)
        pops = [predict_pop(mn, sn, e["nums"], prevn) for e in entries]
        evs = [-p for p in pops]
        A = pick_portfolio(entries, before, td, traps, k=K)
        B = pick_ev_top(entries, evs, K)
        D = pick_hybrid(entries, evs, K)
        def mean_ev(sets):
            return sum(-predict_pop(mn, sn, s, prevn) for s in sets) / K
        evA.append(mean_ev(A))
        evB.append(mean_ev(B))
        evD.append(mean_ev(D))

    placebo_pred_B = math.exp(float(np.mean(evB) - np.mean(evA)))
    placebo_pred_D = math.exp(float(np.mean(evD) - np.mean(evA)))
    # bootstrap placebo ratios
    def boot_ratio(eva, evb, n_boot=3000):
        n = min(len(eva), len(evb))
        rs = []
        for _ in range(n_boot):
            idx = [rng2.randrange(n) for _ in range(n)]
            rs.append(math.exp(sum(evb[i] - eva[i] for i in idx) / n))
        rs.sort()
        return {
            "ratio": round(math.exp(float(np.mean(evb) - np.mean(eva))), 6),
            "ci95": [round(rs[int(0.025 * n_boot)], 6), round(rs[int(0.975 * n_boot)], 6)],
        }

    plac_B = boot_ratio(evA, evB)
    plac_D = boot_ratio(evA, evD)
    placebo_bias_yes = (plac_B["ci95"][0] > 1.0) or (plac_D["ci95"][0] > 1.0)

    # ---------- P1 verdict ----------
    # focus on B and D
    b_row = next(r for r in realized_table if r["arm"] == "B")
    d_row = next(r for r in realized_table if r["arm"] == "D")
    survive = (b_row["realized_ci95"][0] > 1.0) or (d_row["realized_ci95"][0] > 1.0)
    # if placebo biased, mark caveat
    if placebo_bias_yes:
        # still apply formal rule but flag
        pass
    # Formal: CI lower > 1 on realized
    p1_verdict = (
        "EV_축_생존"
        if (b_row["realized_ci95"][0] > 1.0 or d_row["realized_ci95"][0] > 1.0)
        and not placebo_bias_yes
        else (
            "EV_이득_미입증_위약편향"
            if placebo_bias_yes
            else "EV_이득_미입증"
        )
    )
    # if placebo yes but realized CI>1, still 미입증 due to pipeline bias
    if placebo_bias_yes:
        p1_verdict = "EV_이득_미입증"
        p1_reason = "위약(라벨셔플)에서도 배율>1 → 파이프라인 편향"
    elif b_row["realized_ci95"][0] > 1.0 or d_row["realized_ci95"][0] > 1.0:
        p1_verdict = "EV_축_생존"
        p1_reason = "실현배율 CI 하한>1 (위약 통과)"
    else:
        p1_verdict = "EV_이득_미입증"
        p1_reason = "실현배율 CI가 1 포함"

    withdraw_D = p1_verdict != "EV_축_생존"

    # ---------- PART 2 tier1 sim ----------
    # model for scoring: fixed train 1..1000
    packed0 = build_xy(draws, tier3, VAL_LO)
    X0, y0, _ = packed0
    m0, s0 = train_ridge(X0, y0)
    # universe sample
    uni_pops = []
    for _ in range(8000):
        samp = sorted(rng.sample(range(1, 46), 6))
        uni_pops.append(predict_pop(m0, s0, samp, None))
    uni_pops = np.array(uni_pops)
    uni_q10 = float(np.quantile(uni_pops, 0.10))

    scenarios: dict[str, Callable] = {
        "T0": filter_t0,
        "T1": filter_t1,
        "T2": filter_t2,
        "T3": filter_t3,
    }
    part2 = {}
    # sample until 2000 pass per scenario (or 200 per "round" * 10)
    for name, filt in scenarios.items():
        pops = []
        hits_vs_fake = []  # mean hit vs random actual from val
        extreme_n = 0
        attempts = 0
        target_n = 4000
        while len(pops) < target_n and attempts < target_n * 80:
            attempts += 1
            samp = sorted(rng.sample(range(1, 46), 6))
            if not filt(samp):
                continue
            pops.append(predict_pop(m0, s0, samp, None))
            if is_extreme(samp):
                extreme_n += 1
        pops_a = np.array(pops)
        # mean hit: sample 500 sets vs 100 random actuals
        hit_list = []
        val_actuals = [sorted_nums(d) for d in draws if VAL_LO <= int(d["draw_no"]) <= VAL_HI]
        for _ in range(2000):
            samp = sorted(rng.sample(range(1, 46), 6))
            if not filt(samp):
                continue
            actual = val_actuals[rng.randrange(len(val_actuals))]
            hit_list.append(len(set(samp) & set(actual)))
            if len(hit_list) >= 2000:
                break
        qs = [float(np.quantile(pops_a, q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)]
        # left shift vs universe: mean diff (lower pop = more unpopular = left if we plot pop)
        # reach universe bottom 10%?
        reach_frac = float(np.mean(pops_a <= uni_q10))
        # max realized headroom vs T0: compare mean of bottom-10% pop
        part2[name] = {
            "n_pass": int(len(pops_a)),
            "attempts": attempts,
            "pass_rate": round(len(pops_a) / max(1, attempts), 6),
            "pop_mean": round(float(pops_a.mean()), 6),
            "pop_std": round(float(pops_a.std()), 6),
            "pop_deciles": {
                "p10": qs[0],
                "p25": qs[1],
                "p50": qs[2],
                "p75": qs[3],
                "p90": qs[4],
            },
            "frac_in_universe_bottom10": round(reach_frac, 6),
            "mean_minus_universe": round(float(pops_a.mean() - uni_pops.mean()), 6),
            "extreme_frac": round(extreme_n / max(1, len(pops_a)), 6),
            "mean_hit_vs_val_actuals": {
                "mean": round(float(np.mean(hit_list)), 6) if hit_list else None,
                "n": len(hit_list),
                "theory": 0.8,
            },
        }

    # headroom: bottom-decile mean pop under each T, vs T0; realized ratio via b
    # lower pop → higher EV; δEV = -(pop_Tx_bottom - pop_T0_bottom) roughly using means of bottom 10%
    def bottom10_mean(name):
        # regenerate pops from stored? recompute from part2 only have moments
        return part2[name]["pop_deciles"]["p10"]

    t0_p10 = bottom10_mean("T0")
    headroom = {}
    for name in scenarios:
        # contrast: pick at p10 of scenario vs p10 of T0
        # Δpop = p10_name - p10_T0 (more negative = more unpopular)
        # ΔEV = -Δpop
        # realized = exp(b * ΔEV) = exp(-b * Δpop)
        dpop = part2[name]["pop_deciles"]["p10"] - t0_p10
        d_ev = -dpop
        real = math.exp(b * d_ev)
        # also vs universe p10
        dpop_u = part2[name]["pop_deciles"]["p10"] - uni_q10
        headroom[name] = {
            "p10_pop": part2[name]["pop_deciles"]["p10"],
            "delta_p10_vs_T0": round(dpop, 6),
            "realized_ratio_vs_T0_p10": round(real, 6),
            "p10_vs_universe_p10": round(dpop_u, 6),
            "note": "p10 꼬리 대 p10 꼬리 대비 (최대 근접 헤드룸)",
        }

    # both-tail check: top 10% (popular) expansion
    both_tail = {}
    for name in scenarios:
        both_tail[name] = {
            "p90_pop": part2[name]["pop_deciles"]["p90"],
            "p90_minus_T0_p90": round(
                part2[name]["pop_deciles"]["p90"] - part2["T0"]["pop_deciles"]["p90"], 6
            ),
        }

    # compare to previous rerank gain (realized)
    rerank_gain = {
        "B_realized": b_row["realized_ratio"],
        "D_realized": d_row["realized_ratio"],
        "T3_headroom_vs_T0": headroom["T3"]["realized_ratio_vs_T0_p10"],
    }

    payload = {
        "ok": True,
        "readonly": True,
        "k09_label": "K-09 미해결 전제",
        "p1_calibration": {
            "fixed_split_train_1_1000_val_1001_1234": cal_fixed,
            "walk_forward_pairs_OLS": cal_wf,
            "b_roll50_tail": b_per_draw[-5:] if b_per_draw else [],
            "b_fixed_vs_wf": {
                "b_fixed": cal_fixed["b"],
                "b_wf": cal_wf["b"],
                "abs_diff": abs(cal_fixed["b"] - cal_wf["b"]),
            },
        },
        "p1_realized_table": realized_table,
        "p1_cv_winners": {
            "n": len(winners_val),
            "mean": round(float(w_arr.mean()), 4),
            "std": round(float(w_arr.std()), 4),
            "cv": round(cv, 6),
        },
        "p1_placebo": {
            "B": plac_B,
            "D": plac_D,
            "bias_detected_YES_NO": "YES" if placebo_bias_yes else "NO",
            "note": "라벨 회차 셔플 후 동일 리랭크 파이프라인",
        },
        "p1_verdict": {
            "verdict": p1_verdict,
            "reason": p1_reason,
            "withdraw_D_wiring": withdraw_D,
            "survive_rule": "실현 CI하한>1 AND 위약 NO",
        },
        "p2_tier1_sim": {
            "universe": {
                "n": int(len(uni_pops)),
                "pop_mean": round(float(uni_pops.mean()), 6),
                "p10": round(uni_q10, 6),
            },
            "scenarios": part2,
            "headroom_realized_b": headroom,
            "both_tail_popular": both_tail,
            "vs_rerank": rerank_gain,
            "part2_is_reference_only": withdraw_D,
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    OUT.joinpath("summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT.joinpath("calibration_raw.json").write_text(
        json.dumps(
            {
                "y_val_fixed": y_val,
                "hat_val_fixed": hat_val,
                "y_wf": y_wf,
                "hat_wf": hat_wf,
                "winners_val": winners_val,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    # compact print
    print(
        json.dumps(
            {
                "cal_fixed_b": cal_fixed["b"],
                "cal_wf_b": cal_wf["b"],
                "r2_wf": cal_wf["r2"],
                "resid_std": cal_wf["resid_std"],
                "cv_winners": cv,
                "realized": [
                    {
                        "arm": r["arm"],
                        "old": r["pred_ratio_old"],
                        "new": r["realized_ratio"],
                        "ci": r["realized_ci95"],
                        "wider": r["ci_wider_than_old"],
                    }
                    for r in realized_table
                    if r["arm"] in ("A", "B", "C", "D", "E")
                ],
                "placebo": payload["p1_placebo"],
                "verdict": payload["p1_verdict"],
                "headroom": headroom,
                "mean_hits": {k: part2[k]["mean_hit_vs_val_actuals"] for k in part2},
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
