# -*- coding: utf-8 -*-
"""EV 리랭커 WF — 저장 15장 오프라인 리랭크만 (생성 경로 미패치 · DB READ-ONLY)."""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.filters import tier1_filter  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from tools.run_meta_hybrid_wf import _load_traps  # noqa: E402
from tools.run_meta_vote2_wf import _draws_before, _load_draws  # noqa: E402
from tools.run_portfolio_set_picker_wf import jaccard, pick_portfolio  # noqa: E402
from tools.run_set_picker_wf import _load_tagged_sets  # noqa: E402

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260726_EV리랭커"
SEED = 20260726
LAST_N = 100
K = 3

# step3/뇌감사에서 단변량 FDR·유의 생존 피처만 (odd/consec 등 기각)
FEATURE_NAMES = ["n_le31", "n_le12", "sum_nums", "carry_from_prev"]
DEAD_EXCLUDED = ["odd_count", "consec_pairs", "num_dummies", "ending", "bands", "diag"]


def load_tier3() -> dict[int, dict]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT draw_no, winner_count, prize_per_game
            FROM testlotto_draw_prize_tiers WHERE tier_rank=3
            """
        ).fetchall()
        return {int(r["draw_no"]): dict(r) for r in rows}
    finally:
        conn.close()


def feat(nums: list[int], prev: list[int] | None) -> np.ndarray:
    s = sorted(nums)
    n_le31 = sum(1 for x in s if x <= 31)
    n_le12 = sum(1 for x in s if x <= 12)
    carry = 0 if prev is None else len(set(s) & set(prev))
    return np.array([n_le31, n_le12, float(sum(s)), float(carry)], dtype=float)


def bootstrap_mean_ci(xs: list[float], n_boot: int = 4000, seed: int = SEED) -> dict:
    rng = random.Random(seed)
    n = len(xs)
    if n == 0:
        return {"mean": 0.0, "ci95": [0.0, 0.0], "n": 0}
    boots = sorted(
        sum(xs[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot)
    )
    return {
        "mean": round(sum(xs) / n, 6),
        "ci95": [round(boots[int(0.025 * n_boot)], 6), round(boots[int(0.975 * n_boot)], 6)],
        "n": n,
    }


def ci_overlap(a: list[float], b: list[float]) -> bool:
    return not (a[1] < b[0] or b[1] < a[0])


def build_train_xy(draws: list[dict], tier3: dict, before_draw: int):
    xs, ys = [], []
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
        xs.append(feat(sorted_nums(d), prev))
        ys.append(math.log(int(t["winner_count"]) / sales))
        prev = sorted_nums(d)
    if len(xs) < 50:
        return None, None, None
    X = np.vstack(xs)
    y = np.array(ys)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    model = Ridge(alpha=10.0, random_state=SEED)
    model.fit(Xs, y)
    return model, scaler, len(xs)


def popularity_hat(model, scaler, nums: list[int], prev: list[int] | None) -> float:
    x = feat(nums, prev).reshape(1, -1)
    return float(model.predict(scaler.transform(x))[0])


def mean_hit(sets: list[list[int]], actual: list[int]) -> float:
    if not sets:
        return 0.0
    a = set(actual)
    return sum(len(set(s) & a) for s in sets) / len(sets)


def unique_nums(sets: list[list[int]]) -> int:
    return len(set().union(*[set(s) for s in sets])) if sets else 0


def pick_ev_top(entries: list[dict], evs: list[float], k: int = K) -> list[list[int]]:
    order = sorted(range(len(entries)), key=lambda i: -evs[i])
    return [sorted(entries[i]["nums"]) for i in order[:k]]


def pick_coverage(entries: list[dict], k: int = K) -> list[list[int]]:
    remaining = list(range(len(entries)))
    picked: list[list[int]] = []
    covered: set[int] = set()
    while len(picked) < k and remaining:
        best_i, best_gain = None, -1
        for i in remaining:
            s = set(entries[i]["nums"])
            gain = len(s - covered)
            # tie-break: prefer lower jaccard to picked
            if picked:
                pen = sum(jaccard(s, set(p)) for p in picked) / len(picked)
                score = gain - 0.5 * pen
            else:
                score = float(gain)
            if score > best_gain:
                best_gain, best_i = score, i
        assert best_i is not None
        remaining.remove(best_i)
        nums = sorted(entries[best_i]["nums"])
        picked.append(nums)
        covered |= set(nums)
    return picked


def pick_hybrid(
    entries: list[dict], evs: list[float], k: int = K
) -> list[list[int]]:
    """0.5 normalized EV + 0.5 marginal coverage, greedy."""
    ev_arr = np.array(evs, dtype=float)
    e_min, e_max = float(ev_arr.min()), float(ev_arr.max())
    span = max(1e-9, e_max - e_min)
    ev_n = (ev_arr - e_min) / span
    remaining = list(range(len(entries)))
    picked: list[list[int]] = []
    covered: set[int] = set()
    while len(picked) < k and remaining:
        # max possible new coverage = 6
        best_i, best_sc = None, -1e9
        for i in remaining:
            s = set(entries[i]["nums"])
            cov_n = len(s - covered) / 6.0
            sc = 0.5 * float(ev_n[i]) + 0.5 * cov_n
            if sc > best_sc:
                best_sc, best_i = sc, i
        remaining.remove(best_i)
        nums = sorted(entries[best_i]["nums"])
        picked.append(nums)
        covered |= set(nums)
    return picked


def main() -> int:
    init_testlotto_db()
    traps = _load_traps()
    draws = _load_draws()
    tagged = _load_tagged_sets()
    tier3 = load_tier3()
    by_no = {int(d["draw_no"]): d for d in draws}

    candidates = [
        d
        for d in draws
        if len(tagged.get(int(d["draw_no"]), [])) >= 15
        or len(tagged.get(int(d["draw_no"]), [])) >= 5
    ]
    # prefer draws with >=15 sets; else >=5 (nominal 15)
    use = [d for d in candidates if len(tagged.get(int(d["draw_no"]), [])) >= 12][-LAST_N:]
    if len(use) < LAST_N:
        use = [d for d in candidates if len(tagged.get(int(d["draw_no"]), [])) >= 5][-LAST_N:]

    arms = {k: {"hits": [], "ev": [], "unique": [], "raw": []} for k in "ABCDE"}
    trap_rows = []
    pool_pops = []
    universe_pops = []

    # fixed universe sample for trap (b) using model at mid window
    rng_uni = random.Random(SEED)

    for d in use:
        td = int(d["draw_no"])
        entries = tagged[td][:15]
        if len(entries) < K:
            continue
        before = _draws_before(draws, td)
        prev = sorted_nums(before[-1]) if before else None
        model, scaler, ntr = build_train_xy(draws, tier3, td)
        if model is None:
            continue
        actual = sorted_nums(d)
        pops = [popularity_hat(model, scaler, e["nums"], prev) for e in entries]
        evs = [-p for p in pops]

        # A meta portfolio
        A = pick_portfolio(entries, before, td, traps, k=K)
        B = pick_ev_top(entries, evs, K)
        C = pick_coverage(entries, K)
        D = pick_hybrid(entries, evs, K)

        # E: 30 random samples of 3 from pool
        rng = random.Random(SEED + td)
        e_hits, e_evs, e_uni = [], [], []
        idxs = list(range(len(entries)))
        for _ in range(30):
            chosen = [entries[i]["nums"] for i in rng.sample(idxs, K)]
            e_hits.append(mean_hit(chosen, actual))
            e_evs.append(sum(-popularity_hat(model, scaler, s, prev) for s in chosen) / K)
            e_uni.append(unique_nums(chosen))
        E_sets = None  # aggregate only

        for name, sets in [("A", A), ("B", B), ("C", C), ("D", D)]:
            h = mean_hit(sets, actual)
            ev_m = sum(-popularity_hat(model, scaler, s, prev) for s in sets) / K
            u = unique_nums(sets)
            arms[name]["hits"].append(h)
            arms[name]["ev"].append(ev_m)
            arms[name]["unique"].append(u)
            arms[name]["raw"].append(
                {
                    "draw_no": td,
                    "mean_hit": h,
                    "mean_ev_score": ev_m,
                    "unique_nums": u,
                    "sets": sets,
                    "n_train": ntr,
                }
            )

        arms["E"]["hits"].append(float(np.mean(e_hits)))
        arms["E"]["ev"].append(float(np.mean(e_evs)))
        arms["E"]["unique"].append(float(np.mean(e_uni)))
        arms["E"]["raw"].append(
            {
                "draw_no": td,
                "mean_hit": float(np.mean(e_hits)),
                "mean_ev_score": float(np.mean(e_evs)),
                "unique_nums": float(np.mean(e_uni)),
                "n_train": ntr,
                "random_repeats": 30,
            }
        )

        # trap (a)
        tier1_flags = [bool(tier1_filter(list(e["nums"]))) for e in entries]
        ev_order = sorted(range(len(entries)), key=lambda i: -evs[i])
        top3_t1 = [tier1_flags[i] for i in ev_order[:3]]
        trap_rows.append(
            {
                "draw_no": td,
                "pool_n": len(entries),
                "tier1_pass_frac": sum(tier1_flags) / len(tier1_flags),
                "ev_top3_tier1_pass_frac": sum(top3_t1) / 3,
                "pool_mean_pop": float(np.mean(pops)),
                "ev_top3_mean_pop": float(np.mean([pops[i] for i in ev_order[:3]])),
                "pool_mean_ev": float(np.mean(evs)),
            }
        )
        pool_pops.extend(pops)

        # trap (b): sample 200 random combinations per draw with same model
        for _ in range(40):
            samp = sorted(rng_uni.sample(range(1, 46), 6))
            universe_pops.append(popularity_hat(model, scaler, samp, prev))

    # summarize
    hit_A = bootstrap_mean_ci(arms["A"]["hits"], seed=SEED)
    summary_arms = {}
    for name in "ABCDE":
        hit = bootstrap_mean_ci(arms[name]["hits"], seed=SEED + ord(name))
        ev_m = float(np.mean(arms[name]["ev"])) if arms[name]["ev"] else 0.0
        ev_A = float(np.mean(arms["A"]["ev"])) if arms["A"]["ev"] else 1e-12
        # prize proxy ratio: exp(mean_ev) ratio vs A (higher EV_score = lower popularity)
        # EV_score = -pop; relative expected share inverse ∝ exp(-pop) = exp(EV)
        ratio = float(np.exp(ev_m - ev_A))
        uni = float(np.mean(arms[name]["unique"])) if arms[name]["unique"] else 0.0
        mean_drop = (not ci_overlap(hit["ci95"], hit_A["ci95"])) and (
            hit["mean"] < hit_A["mean"]
        )
        # stricter: mean significantly below A if hit CI upper < A CI lower
        mean_sig_below_A = hit["ci95"][1] < hit_A["ci95"][0]
        mean_near_080 = hit["ci95"][0] <= 0.80 <= hit["ci95"][1] or abs(hit["mean"] - 0.80) < 0.15
        # adopt candidate: CI overlap with A AND ratio > 1 (bootstrap on ratio)
        rng = random.Random(SEED + 99 + ord(name))
        ratios = []
        n0 = min(len(arms[name]["ev"]), len(arms["A"]["ev"]))
        for _ in range(3000):
            idx = [rng.randrange(n0) for _ in range(n0)]
            mb = sum(arms[name]["ev"][i] for i in idx) / n0
            ma = sum(arms["A"]["ev"][i] for i in idx) / n0
            ratios.append(math.exp(mb - ma))
        ratios.sort()
        ratio_ci = [round(ratios[int(0.025 * 3000)], 6), round(ratios[int(0.975 * 3000)], 6)]
        ratio_sig_gt_1 = ratio_ci[0] > 1.0
        if mean_sig_below_A:
            verdict = "폐기(mean 유의 하락)"
        elif ci_overlap(hit["ci95"], hit_A["ci95"]) and ratio_sig_gt_1:
            verdict = "채택후보(mean CI겹침 + 수령배율 유의↑)"
        elif ci_overlap(hit["ci95"], hit_A["ci95"]) and ratio > 1.0:
            verdict = "관찰(배율↑이나 CI가 1 포함)"
        else:
            verdict = "비채택"
        summary_arms[name] = {
            "label": {
                "A": "현행메타_portfolio_K3",
                "B": "EV_top3",
                "C": "coverage_top3",
                "D": "hybrid_EV_cov_0.5",
                "E": "random3_from15_x30",
            }[name],
            "mean_hit": hit,
            "expected_payout_ratio_vs_A": round(ratio, 6),
            "payout_ratio_ci95_vs_A": ratio_ci,
            "unique_nums_mean": round(uni, 4),
            "mean_ev_score": round(ev_m, 6),
            "verdict": verdict,
            "mean_sig_below_A": mean_sig_below_A,
            "ci_overlap_A": ci_overlap(hit["ci95"], hit_A["ci95"]),
        }

    # trap aggregates
    pool_arr = np.array(pool_pops) if pool_pops else np.array([0.0])
    uni_arr = np.array(universe_pops) if universe_pops else np.array([0.0])
    traps_out = {
        "a_tier1": {
            "avg_pool_tier1_pass_frac": round(
                float(np.mean([r["tier1_pass_frac"] for r in trap_rows])), 6
            ),
            "avg_ev_top3_tier1_pass_frac": round(
                float(np.mean([r["ev_top3_tier1_pass_frac"] for r in trap_rows])), 6
            ),
            "avg_pool_mean_pop": round(
                float(np.mean([r["pool_mean_pop"] for r in trap_rows])), 6
            ),
            "avg_ev_top3_mean_pop": round(
                float(np.mean([r["ev_top3_mean_pop"] for r in trap_rows])), 6
            ),
            "note": "풀이 이미 tier1에 갇혀 있으면 EV 상위도 인기 구간에 잔류 가능",
        },
        "b_pool_vs_universe": {
            "pool_pop_mean": round(float(pool_arr.mean()), 6),
            "pool_pop_std": round(float(pool_arr.std()), 6),
            "universe_sample_pop_mean": round(float(uni_arr.mean()), 6),
            "universe_sample_pop_std": round(float(uni_arr.std()), 6),
            "pool_minus_universe_mean": round(
                float(pool_arr.mean() - uni_arr.mean()), 6
            ),
            "n_pool": int(len(pool_arr)),
            "n_universe_sample": int(len(uni_arr)),
            "interpretation": (
                "pool_pop > universe → 15장 풀이 더 인기 편향(리랭크 상한 낮음). "
                "pool_pop < universe → 풀이 이미 비인기 쪽."
            ),
        },
        "c_proxy_limit": (
            "수령배율은 3등 winners/매출 프록시. 1등 당첨자 분포와 다를 수 있음."
        ),
    }

    # K-09
    k09 = {
        "affects_this_run": True,
        "label": "K-09 미해결 전제",
        "reason": (
            "리랭커 자체는 learn_state 미사용·저장 세트만 재정렬. "
            "그러나 후보 15장은 과거 생성 경로(learn_state 전역) 산물 → 간접 영향 가능."
        ),
    }

    payload = {
        "ok": True,
        "readonly": True,
        "no_generation": True,
        "features_used": FEATURE_NAMES,
        "features_excluded_dead": DEAD_EXCLUDED,
        "label": "log(tier3_winners/sales); EV_score=-popularity_hat",
        "train_mode": "walk_forward_ridge_train_draw_no_lt_N",
        "last_n": LAST_N,
        "n_draws_evaluated": len(arms["A"]["hits"]),
        "k": K,
        "baseline_A_mean_hit": hit_A,
        "arms": summary_arms,
        "traps": traps_out,
        "k09": k09,
        "decision_rule": {
            "adopt_candidate": "mean CI overlaps A AND payout_ratio CI lower > 1",
            "reject": "mean CI entirely below A (수령배율 무관)",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    OUT.joinpath("summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT.joinpath("raw_by_arm.json").write_text(
        json.dumps({k: v["raw"] for k, v in arms.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    OUT.joinpath("trap_rows.json").write_text(
        json.dumps(trap_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
