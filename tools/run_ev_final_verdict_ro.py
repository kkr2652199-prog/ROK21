# -*- coding: utf-8 -*-
"""EV 최종판정 — 위약 200회 · 순효과 · 정지규칙 (READ-ONLY)."""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from pathlib import Path

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
OUT = ROOT / "docs" / "benchmarks" / "20260726_EV최종"
CAL = ROOT / "docs" / "benchmarks" / "20260726_EV보정" / "summary.json"
PREV = ROOT / "docs" / "benchmarks" / "20260726_EV리랭커" / "summary.json"
SEED = 20260726
N_PLACEBO = 200
LAST_N = 100
K = 3
# 사전등록 실측 실현배율 (보정 보고서 고정값 — 재추정으로 바꾸지 않음)
ACTUAL_REALIZED = {"B": 1.055942, "D": 1.049164}
ACTUAL_PRED_LOG = {"B": math.log(1.088287), "D": math.log(1.07745)}


def load_tier3():
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return {
            int(r["draw_no"]): dict(r)
            for r in conn.execute(
                "SELECT draw_no, winner_count, prize_per_game FROM testlotto_draw_prize_tiers WHERE tier_rank=3"
            )
        }
    finally:
        conn.close()


def feat(nums, prev):
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


def train_ridge(X, y):
    sc = StandardScaler()
    Xs = sc.fit_transform(X)
    m = Ridge(alpha=10.0, random_state=SEED)
    m.fit(Xs, y)
    return m, sc


def predict_pop(m, sc, nums, prev):
    return float(m.predict(sc.transform(feat(nums, prev).reshape(1, -1)))[0])


def ols_b(y, hat):
    lr = LinearRegression()
    lr.fit(hat.reshape(-1, 1), y)
    pred = lr.predict(hat.reshape(-1, 1))
    resid = y - pred
    n = len(y)
    ss_res = float(np.sum(resid**2))
    x = hat - hat.mean()
    sxx = float(np.sum(x**2))
    sigma = math.sqrt(ss_res / max(1, n - 2))
    b = float(lr.coef_[0])
    b_se = sigma / math.sqrt(sxx) if sxx > 0 else float("nan")
    return b, b_se, sigma, n


def pick_ev_top(entries, evs, k=K):
    order = sorted(range(len(entries)), key=lambda i: -evs[i])
    return [sorted(entries[i]["nums"]) for i in order[:k]]


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
            scv = 0.5 * float(ev_n[i]) + 0.5 * (len(s - covered) / 6.0)
            if scv > best_sc:
                best_sc, best_i = scv, i
        remaining.remove(best_i)
        nums = sorted(entries[best_i]["nums"])
        picked.append(nums)
        covered |= set(nums)
    return picked


def build_train_mats(draws, tier3):
    """Precompute per-draw features/labels for fast placebo rebuild."""
    rows = []
    prev = None
    for d in draws:
        dn = int(d["draw_no"])
        t = tier3.get(dn)
        sales = float(d.get("total_sales") or 0)
        nums = sorted_nums(d)
        if t and sales > 0 and int(t["winner_count"] or 0) > 0:
            y = math.log(int(t["winner_count"]) / sales)
            rows.append({"draw_no": dn, "x": feat(nums, prev), "y": y, "nums": nums})
        prev = nums
    return rows


def train_from_rows(rows, before_draw, y_by_dn=None):
    xs, ys = [], []
    for r in rows:
        if r["draw_no"] >= before_draw:
            break
        y = y_by_dn[r["draw_no"]] if y_by_dn is not None else r["y"]
        xs.append(r["x"])
        ys.append(y)
    if len(xs) < 50:
        return None
    return train_ridge(np.vstack(xs), np.array(ys))


def arm_pred_log_diffs(draws, tagged, traps, rows, use, y_by_dn, mode: str):
    """
    mode='wf': walk-forward retrain each draw (slow)
    mode='fixed': one model trained before first use draw (fast placebo)
    Returns mean pred_log_diff for B and D vs A (= mean_ev_arm - mean_ev_A)
    """
    first_td = int(use[0]["draw_no"])
    fixed = None
    if mode == "fixed":
        fixed = train_from_rows(rows, first_td, y_by_dn)
        if fixed is None:
            return None
    evA, evB, evD = [], [], []
    for d in use:
        td = int(d["draw_no"])
        entries = tagged.get(td, [])[:15]
        if len(entries) < K:
            continue
        before = _draws_before(draws, td)
        prev = sorted_nums(before[-1]) if before else None
        if mode == "wf":
            packed = train_from_rows(rows, td, y_by_dn)
            if packed is None:
                continue
            m, sc = packed
        else:
            m, sc = fixed
        pops = [predict_pop(m, sc, e["nums"], prev) for e in entries]
        evs = [-p for p in pops]
        A = pick_portfolio(entries, before, td, traps, k=K)
        B = pick_ev_top(entries, evs, K)
        D = pick_hybrid(entries, evs, K)

        def mean_ev(sets):
            return sum(-predict_pop(m, sc, s, prev) for s in sets) / K

        evA.append(mean_ev(A))
        evB.append(mean_ev(B))
        evD.append(mean_ev(D))
    if len(evA) < 20:
        return None
    return {
        "B": float(np.mean(evB) - np.mean(evA)),
        "D": float(np.mean(evD) - np.mean(evA)),
        "n": len(evA),
        "mean_ev_A": float(np.mean(evA)),
        "mean_ev_B": float(np.mean(evB)),
        "mean_ev_D": float(np.mean(evD)),
    }


def structural_diagnostics(draws, tagged, traps, rows, use):
    """Cause of placebo > 1: compare score spreads."""
    # Real labels, fixed model before first use
    first_td = int(use[0]["draw_no"])
    m, sc = train_from_rows(rows, first_td, None)
    # Within-pool: max EV - mean EV, max - portfolio EV, etc.
    gaps_max_vs_mean = []
    gaps_max_vs_port = []
    gaps_hybrid_vs_port = []
    pool_ev_std = []
    for d in use:
        td = int(d["draw_no"])
        entries = tagged.get(td, [])[:15]
        if len(entries) < K:
            continue
        before = _draws_before(draws, td)
        prev = sorted_nums(before[-1]) if before else None
        pops = [predict_pop(m, sc, e["nums"], prev) for e in entries]
        evs = np.array([-p for p in pops])
        A = pick_portfolio(entries, before, td, traps, k=K)
        port_ev = np.mean([-predict_pop(m, sc, s, prev) for s in A])
        gaps_max_vs_mean.append(float(evs.max() - evs.mean()))
        # top3 mean vs port
        top3 = np.sort(evs)[-3:].mean()
        gaps_max_vs_port.append(float(top3 - port_ev))
        hyb = pick_hybrid(entries, list(evs), K)
        hyb_ev = np.mean([-predict_pop(m, sc, s, prev) for s in hyb])
        gaps_hybrid_vs_port.append(float(hyb_ev - port_ev))
        pool_ev_std.append(float(evs.std()))
    return {
        "avg_top3_minus_pool_mean": round(float(np.mean(gaps_max_vs_mean)), 6),
        "avg_top3_minus_portfolioA": round(float(np.mean(gaps_max_vs_port)), 6),
        "avg_hybrid_minus_portfolioA": round(float(np.mean(gaps_hybrid_vs_port)), 6),
        "avg_pool_ev_std": round(float(np.mean(pool_ev_std)), 6),
        "implication": (
            "B=EV상위3 정의상 pool 내 점수 상단을 고르므로, "
            "A(aux+다양성)가 EV를 최대화하지 않는 한 E[EV_B]>E[EV_A]가 항상 성립. "
            "라벨 셔플로 점수축만 바꿔도 동일 부등호 → 구조적 선별 편향."
        ),
    }


def main():
    init_testlotto_db()
    draws = _load_draws()
    tier3 = load_tier3()
    tagged = _load_tagged_sets()
    traps = _load_traps()
    rows = build_train_mats(draws, tier3)
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    b0 = float(cal["p1_calibration"]["walk_forward_pairs_OLS"]["b"])
    y_wf = json.loads(
        (ROOT / "docs/benchmarks/20260726_EV보정/calibration_raw.json").read_text(
            encoding="utf-8"
        )
    )
    y_arr = np.array(y_wf["y_wf"], dtype=float)
    hat_arr = np.array(y_wf["hat_wf"], dtype=float)

    use = [d for d in draws if len(tagged.get(int(d["draw_no"]), [])) >= 5][-LAST_N:]

    # true y map
    y_true = {r["draw_no"]: r["y"] for r in rows}
    dns = sorted(y_true)

    # S1: 200 placebos (fixed-model-per-shuffle for tractability; documented)
    rng = random.Random(SEED)
    placebo_raw = []
    for rep in range(N_PLACEBO):
        ys = [y_true[d] for d in dns]
        rng.shuffle(ys)
        y_perm = {d: ys[i] for i, d in enumerate(dns)}
        diffs = arm_pred_log_diffs(
            draws, tagged, traps, rows, use, y_perm, mode="fixed"
        )
        if diffs is None:
            continue
        # realized scale with fixed b0 (same as actual calibration)
        rec = {
            "rep": rep,
            "seed_offset": SEED + rep,
            "pred_log_B": diffs["B"],
            "pred_log_D": diffs["D"],
            "realized_B": math.exp(b0 * diffs["B"]),
            "realized_D": math.exp(b0 * diffs["D"]),
            "n": diffs["n"],
        }
        placebo_raw.append(rec)
        if (rep + 1) % 20 == 0:
            print(f"placebo {rep+1}/{N_PLACEBO}", flush=True)

    pb_B = np.array([r["realized_B"] for r in placebo_raw])
    pb_D = np.array([r["realized_D"] for r in placebo_raw])

    def dist_stats(arr, actual):
        arr_s = np.sort(arr)
        # empirical p = P(placebo >= actual) 
        p = float(np.mean(arr >= actual))
        # percentile rank of actual in placebo
        pct = float(np.mean(arr < actual) * 100.0)
        return {
            "n": int(len(arr)),
            "mean": round(float(arr.mean()), 6),
            "std": round(float(arr.std()), 6),
            "p50": round(float(np.median(arr)), 6),
            "p95": round(float(np.quantile(arr, 0.95)), 6),
            "p05": round(float(np.quantile(arr, 0.05)), 6),
            "actual_realized": actual,
            "actual_percentile_in_placebo": round(pct, 3),
            "empirical_p_placebo_ge_actual": round(p, 6),
        }

    dist_B = dist_stats(pb_B, ACTUAL_REALIZED["B"])
    dist_D = dist_stats(pb_D, ACTUAL_REALIZED["D"])

    # S2 net effect + bootstrap CI with b uncertainty
    def net_and_ci(arm, actual_realized, pb_realized_arr, pred_log_actual, n_boot=5000):
        rngb = random.Random(SEED + 1000 + ord(arm))
        nets = []
        n = len(y_arr)
        # precompute placebo pred_logs
        if arm == "B":
            plac_logs = np.array([r["pred_log_B"] for r in placebo_raw])
        else:
            plac_logs = np.array([r["pred_log_D"] for r in placebo_raw])
        for _ in range(n_boot):
            idx = [rngb.randrange(n) for _ in range(n)]
            b_star, _, _, _ = ols_b(y_arr[idx], hat_arr[idx])
            # actual realized with b*
            act = math.exp(b_star * pred_log_actual)
            # placebo mean realized with same b*
            pb_mean = float(np.mean(np.exp(b_star * plac_logs)))
            nets.append(act / pb_mean if pb_mean > 0 else float("nan"))
        nets = [x for x in nets if x == x]
        nets.sort()
        pb_mean0 = float(np.mean(pb_realized_arr))
        net0 = actual_realized / pb_mean0
        return {
            "actual_realized": actual_realized,
            "placebo_mean_realized": round(pb_mean0, 6),
            "net_ratio": round(net0, 6),
            "net_ci95": [
                round(nets[int(0.025 * len(nets))], 6),
                round(nets[int(0.975 * len(nets))], 6),
            ],
            "net_ci_lower_gt_1": nets[int(0.025 * len(nets))] > 1.0,
        }

    net_B = net_and_ci("B", ACTUAL_REALIZED["B"], pb_B, ACTUAL_PRED_LOG["B"])
    net_D = net_and_ci("D", ACTUAL_REALIZED["D"], pb_D, ACTUAL_PRED_LOG["D"])

    table = [
        {
            "arm": "B",
            "actual_realized": ACTUAL_REALIZED["B"],
            "placebo_mean": dist_B["mean"],
            "placebo_p": dist_B["empirical_p_placebo_ge_actual"],
            "actual_percentile": dist_B["actual_percentile_in_placebo"],
            "net_ratio": net_B["net_ratio"],
            "net_ci95": net_B["net_ci95"],
        },
        {
            "arm": "D",
            "actual_realized": ACTUAL_REALIZED["D"],
            "placebo_mean": dist_D["mean"],
            "placebo_p": dist_D["empirical_p_placebo_ge_actual"],
            "actual_percentile": dist_D["actual_percentile_in_placebo"],
            "net_ratio": net_D["net_ratio"],
            "net_ci95": net_D["net_ci95"],
        },
    ]

    # S3 structure
    struct = structural_diagnostics(draws, tagged, traps, rows, use)

    # S4 stop rule — pre-registered, do not change reporting
    # 순효과 CI 하한 > 1 → survive; CI includes 1 → CLOSED
    survive_B = net_B["net_ci_lower_gt_1"]
    survive_D = net_D["net_ci_lower_gt_1"]
    survive = survive_B or survive_D
    if survive:
        verdict = "EV_축_생존"
        k11_status = "OPEN"
        k11_note = "순효과 CI하한>1 → 배선 설계 진행 가능"
        remaining_skill_axis = "비인기 EV (순효과 생존 arm 기준)"
    else:
        verdict = "EV_축_CLOSED"
        k11_status = "CLOSED"
        k11_note = (
            "순효과 CI가 1 포함 → EV 축 CLOSED · 재도전 금지 (사전등록 정지규칙)"
        )
        remaining_skill_axis = "없음"

    payload = {
        "ok": True,
        "readonly": True,
        "k09_label": "K-09 미해결 전제",
        "stop_rule": {
            "survive_if": "순효과 CI 하한 > 1.00",
            "close_if": "CI가 1.00 포함 → EV CLOSED · 재도전 금지",
            "pre_registered": True,
        },
        "method_notes": {
            "placebo_reps": N_PLACEBO,
            "placebo_model": (
                "회차 라벨 셔플 후, 평가창 첫 회차 이전 데이터로 Ridge 1회 학습"
                "(fixed-per-shuffle). 200×WF는 비용상 대체. 편향 방향은 WF 1회와 동일."
            ),
            "actual_realized_frozen_from": str(CAL),
            "b0": b0,
            "realized_formula": "exp(b * pred_log_diff)",
            "net_formula": "actual_realized / placebo_mean_realized",
        },
        "S1_placebo_dist": {"B": dist_B, "D": dist_D},
        "S2_net_effect": {"B": net_B, "D": net_D, "table": table},
        "S3_bias_cause": {
            "one_line": (
                "EV_score 정렬 자체(상위k 선별 정의) — "
                "A가 EV비최대라 라벨과 무관하게 E[EV_B]>E[EV_A]"
            ),
            "diagnostics": struct,
            "not_primary": [
                "b 추정만으로는 위약>1 설명 불가(동일 b 적용)",
                "창 100회 소표본은 CI 폭에 영향, 점추정 편향의 아님",
                "15장 상관은 보조(분산)이나 핵심 원인은 선별 정의",
            ],
        },
        "S4_verdict": {
            "verdict": verdict,
            "survive_B": survive_B,
            "survive_D": survive_D,
            "k11_status": k11_status,
            "k11_note": k11_note,
            "remaining_skill_axis": remaining_skill_axis,
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    OUT.joinpath("summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT.joinpath("placebo_200_raw.json").write_text(
        json.dumps(placebo_raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "S1": payload["S1_placebo_dist"],
        "S2_table": table,
        "S3": payload["S3_bias_cause"]["one_line"],
        "S4": payload["S4_verdict"],
    }, ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
