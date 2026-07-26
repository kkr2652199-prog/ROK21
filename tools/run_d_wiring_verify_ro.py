# -*- coding: utf-8 -*-
"""D 배선 검증: OFF 해시 동일 + 창200 순효과(위약200)."""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.ev_rerank import pick_d_hybrid  # noqa: E402
from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.meta_picker import meta_assemble_sets  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from tools.run_meta_hybrid_wf import _load_traps  # noqa: E402
from tools.run_meta_vote2_wf import _draws_before, _load_draws  # noqa: E402
from tools.run_portfolio_set_picker_wf import pick_portfolio  # noqa: E402
from tools.run_set_picker_wf import _load_tagged_sets  # noqa: E402

OUT = ROOT / "docs" / "benchmarks" / "20260726_D배선"
CAL_RAW = ROOT / "docs" / "benchmarks" / "20260726_EV보정" / "calibration_raw.json"
CAL = ROOT / "docs" / "benchmarks" / "20260726_EV보정" / "summary.json"
SEED = 20260726
N_PLACEBO = 200
LAST_N = 200
K = 3


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
    return b, sigma, n


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


def off_hash_test(draws, tagged) -> dict:
    """OFF 시 meta_assemble 출력이 환경변수 제거 전후 동일 해시."""
    os.environ.pop("ROK21_EV_RERANK", None)
    use = [d for d in draws if len(tagged.get(int(d["draw_no"]), [])) >= 5][-30:]
    payloads = []
    for d in use:
        td = int(d["draw_no"])
        pool = [e["nums"] for e in tagged[td][:15]]
        before = _draws_before(draws, td)
        out = meta_assemble_sets(pool, before, td, k=3)
        payloads.append([(x["nums"], x["method"]) for x in out])
    blob = json.dumps(payloads, ensure_ascii=False, sort_keys=True)
    h1 = hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # force OFF explicitly
    os.environ["ROK21_EV_RERANK"] = "0"
    payloads2 = []
    for d in use:
        td = int(d["draw_no"])
        pool = [e["nums"] for e in tagged[td][:15]]
        before = _draws_before(draws, td)
        out = meta_assemble_sets(pool, before, td, k=3)
        payloads2.append([(x["nums"], x["method"]) for x in out])
    h2 = hashlib.sha256(
        json.dumps(payloads2, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    os.environ.pop("ROK21_EV_RERANK", None)

    # ON vs OFF should differ on at least some draws (smoke)
    os.environ["ROK21_EV_RERANK"] = "1"
    differ = 0
    same = 0
    for d in use[:15]:
        td = int(d["draw_no"])
        pool = [e["nums"] for e in tagged[td][:15]]
        before = _draws_before(draws, td)
        os.environ["ROK21_EV_RERANK"] = "0"
        a = [x["nums"] for x in meta_assemble_sets(pool, before, td, k=3)]
        os.environ["ROK21_EV_RERANK"] = "1"
        b = [x["nums"] for x in meta_assemble_sets(pool, before, td, k=3)]
        if a == b:
            same += 1
        else:
            differ += 1
    os.environ.pop("ROK21_EV_RERANK", None)

    return {
        "off_hash_sha256": h1,
        "off_explicit0_hash": h2,
        "off_identical": h1 == h2,
        "on_vs_off_sample15": {"differ": differ, "same": same},
        "n_draws_hashed": len(use),
    }


def load_tier_rows(draws):
    import sqlite3

    db = ROOT / "data" / "lotto_testlotto.db"
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tiers = {
            int(r["draw_no"]): dict(r)
            for r in conn.execute(
                "SELECT draw_no, winner_count FROM testlotto_draw_prize_tiers WHERE tier_rank=3"
            )
        }
    finally:
        conn.close()
    rows = []
    prev = None
    for d in draws:
        dn = int(d["draw_no"])
        t = tiers.get(dn)
        sales = float(d.get("total_sales") or 0)
        nums = sorted_nums(d)
        if t and sales > 0 and int(t["winner_count"] or 0) > 0:
            rows.append(
                {
                    "draw_no": dn,
                    "x": feat(nums, prev),
                    "y": math.log(int(t["winner_count"]) / sales),
                }
            )
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


def arm_deltas(draws, tagged, traps, rows, use, y_by_dn, b0):
    first_td = int(use[0]["draw_no"])
    fixed = train_from_rows(rows, first_td, y_by_dn)
    if fixed is None:
        return None
    m, sc = fixed
    evA, evD = [], []
    hits_A, hits_D = [], []
    for d in use:
        td = int(d["draw_no"])
        entries = tagged.get(td, [])[:15]
        if len(entries) < K:
            continue
        before = _draws_before(draws, td)
        prev = sorted_nums(before[-1]) if before else None
        actual = sorted_nums(d)
        pops = [predict_pop(m, sc, e["nums"], prev) for e in entries]
        evs = [-p for p in pops]
        A = pick_portfolio(entries, before, td, traps, k=K)
        D = pick_hybrid(entries, evs, K)

        def mean_ev(sets):
            return sum(-predict_pop(m, sc, s, prev) for s in sets) / K

        def mean_hit(sets):
            a = set(actual)
            return sum(len(set(s) & a) for s in sets) / len(sets)

        evA.append(mean_ev(A))
        evD.append(mean_ev(D))
        hits_A.append(mean_hit(A))
        hits_D.append(mean_hit(D))
    if len(evA) < 30:
        return None
    pred_log = float(np.mean(evD) - np.mean(evA))
    return {
        "pred_log_D_vs_A": pred_log,
        "realized_D": math.exp(b0 * pred_log),
        "mean_hit_A": float(np.mean(hits_A)),
        "mean_hit_D": float(np.mean(hits_D)),
        "n": len(evA),
    }


def first_vs_third_proxy_check(draws) -> dict:
    """1등 vs 3등 괴리 정량 가능 여부."""
    import sqlite3

    db = ROOT / "data" / "lotto_testlotto.db"
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            """
            SELECT d.draw_no, d.first_winners, d.total_sales,
                   t3.winner_count AS w3, t1.winner_count AS w1
            FROM lotto_draws d
            JOIN testlotto_draw_prize_tiers t3 ON t3.draw_no=d.draw_no AND t3.tier_rank=3
            LEFT JOIN testlotto_draw_prize_tiers t1 ON t1.draw_no=d.draw_no AND t1.tier_rank=1
            WHERE IFNULL(d.total_sales,0)>0 AND IFNULL(t3.winner_count,0)>0
              AND IFNULL(d.first_winners,0)>0
            """
        ).fetchall()
    finally:
        conn.close()
    if len(rows) < 50:
        return {"quantifiable": False, "reason": "표본부족", "n": len(rows)}
    y3 = np.array([math.log(r[3] / r[2]) for r in rows])
    y1 = np.array([math.log(max(1, r[1]) / r[2]) for r in rows])
    # spearman-ish pearson on ranks
    r = float(np.corrcoef(y3, y1)[0, 1])
    return {
        "quantifiable": True,
        "n": len(rows),
        "pearson_log_w3_sales_vs_log_w1_sales": round(r, 6),
        "note": "상관 낮으면 3등 프록시→1등 괴리 큼. 배선 이득을 1등 환급으로 단정 금지.",
    }


def main():
    init_testlotto_db()
    draws = _load_draws()
    tagged = _load_tagged_sets()
    traps = _load_traps()
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    b0 = float(cal["p1_calibration"]["walk_forward_pairs_OLS"]["b"])
    raw = json.loads(CAL_RAW.read_text(encoding="utf-8"))
    y_arr = np.array(raw["y_wf"], dtype=float)
    hat_arr = np.array(raw["hat_wf"], dtype=float)

    print("S2 OFF hash...", flush=True)
    hash_res = off_hash_test(draws, tagged)
    print(json.dumps(hash_res, ensure_ascii=False), flush=True)

    rows = load_tier_rows(draws)
    use = [d for d in draws if len(tagged.get(int(d["draw_no"]), [])) >= 5][-LAST_N:]
    y_true = {r["draw_no"]: r["y"] for r in rows}
    dns = sorted(y_true)

    print("S3 actual window200...", flush=True)
    actual = arm_deltas(draws, tagged, traps, rows, use, None, b0)
    assert actual is not None

    print("S3 placebo200...", flush=True)
    rng = random.Random(SEED)
    placebo_raw = []
    for rep in range(N_PLACEBO):
        ys = [y_true[d] for d in dns]
        rng.shuffle(ys)
        y_perm = {d: ys[i] for i, d in enumerate(dns)}
        dlt = arm_deltas(draws, tagged, traps, rows, use, y_perm, b0)
        if dlt:
            placebo_raw.append(
                {
                    "rep": rep,
                    "realized_D": dlt["realized_D"],
                    "pred_log": dlt["pred_log_D_vs_A"],
                }
            )
        if (rep + 1) % 20 == 0:
            print(f"  placebo {rep+1}/{N_PLACEBO}", flush=True)

    pb = np.array([r["realized_D"] for r in placebo_raw])
    pb_logs = np.array([r["pred_log"] for r in placebo_raw])
    act_r = actual["realized_D"]
    pb_mean = float(pb.mean())
    net0 = act_r / pb_mean
    emp_p = float(np.mean(pb >= act_r))
    pct = float(np.mean(pb < act_r) * 100)

    # bootstrap net with b uncertainty
    rngb = random.Random(SEED + 9)
    nets = []
    n = len(y_arr)
    pred_log_act = actual["pred_log_D_vs_A"]
    for _ in range(5000):
        idx = [rngb.randrange(n) for _ in range(n)]
        b_star, _, _ = ols_b(y_arr[idx], hat_arr[idx])
        act = math.exp(b_star * pred_log_act)
        pbm = float(np.mean(np.exp(b_star * pb_logs)))
        nets.append(act / pbm)
    nets.sort()
    ci = [nets[int(0.025 * len(nets))], nets[int(0.975 * len(nets))]]
    ci_ok = ci[0] > 1.0

    # mean hit CI bootstrap
    def boot_mean(xs, seed):
        rng2 = random.Random(seed)
        n0 = len(xs)
        boots = sorted(
            sum(xs[rng2.randrange(n0)] for _ in range(n0)) / n0 for _ in range(3000)
        )
        return {
            "mean": round(sum(xs) / n0, 6),
            "ci95": [round(boots[int(0.025 * 3000)], 6), round(boots[int(0.975 * 3000)], 6)],
        }

    # recompute hit lists properly - arm_deltas already averaged; re-run quick for CI
    # use stored means only + note
    proxy = first_vs_third_proxy_check(draws)

    # expected real gain vs payout rate honesty
    # Korean lotto roughly returns ~50% to players; EV net +3% on conditional 3rd share
    # is NOT +3% ROI on ticket. Honest line:
    honest = (
        f"순효과 ~{net0:.3f}×는 3등 분배 프록시 상대값이며, "
        f"티켓 환급률(≈50%대) 대비 '구매 기대값 +3%'가 아님. "
        f"당첨 조건부 수령액 쪽 소폭 이득 가설."
    )

    payload = {
        "ok": True,
        "k09_label": "K-09 미해결 전제",
        "S2_off_hash": hash_res,
        "S3_window200": {
            "n_draws": actual["n"],
            "mean_hit_A": round(actual["mean_hit_A"], 6),
            "mean_hit_D": round(actual["mean_hit_D"], 6),
            "actual_realized_D": round(act_r, 6),
            "placebo_mean": round(pb_mean, 6),
            "placebo_p95": round(float(np.quantile(pb, 0.95)), 6),
            "empirical_p": round(emp_p, 6),
            "actual_percentile": round(pct, 3),
            "net_ratio": round(net0, 6),
            "net_ci95": [round(ci[0], 6), round(ci[1], 6)],
            "ci_lower_gt_1": ci_ok,
            "verdict_YES_NO": "YES" if ci_ok else "NO",
            "default_off_if_NO": (not ci_ok),
        },
        "S4_risks": {
            "k09_snapshot_design": {
                "table": "testlotto_brain_learn_state_history",
                "pk": "(brain_tag, as_of_draw_no)",
                "load": "as_of = max{k | k < target}",
                "note": "패치 전 설계만. 본 턴 스키마 미적용",
            },
            "tier1_vs_first": proxy,
            "honest_roi_vs_payout_rate": honest,
        },
        "wiring": {
            "env": "ROK21_EV_RERANK=1",
            "default": "OFF",
            "entry": "meta_picker.meta_assemble_sets → maybe_apply_d_rerank",
            "new_file": "app/testlotto/ev_rerank.py",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    OUT.joinpath("summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT.joinpath("placebo_200_window200_raw.json").write_text(
        json.dumps(placebo_raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
