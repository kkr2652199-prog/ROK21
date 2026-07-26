# -*- coding: utf-8 -*-
"""K-09 컷오프 회귀·누수실측·EV 순효과 재검증 (READ/재생성만, 전역 learn_state 행 삭제 금지)."""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.registry import PREDICT_BRAINS, SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.learn_state_cutoff import (  # noqa: E402
    clear_history_cache,
    set_learn_as_of,
)
from app.testlotto.models import init_testlotto_db  # noqa: E402
from tools.run_meta_hybrid_wf import _load_traps  # noqa: E402
from tools.run_meta_vote2_wf import _draws_before, _load_draws  # noqa: E402
from tools.run_portfolio_set_picker_wf import pick_portfolio  # noqa: E402

OUT = ROOT / "docs" / "benchmarks" / "20260726_K09컷오프"
SEED = 20260726
LAST_N = 200
N_PLACEBO = 200
K = 3

PREDICT_MODULES = {
    "stat": "app.testlotto.brains.predict_stat_fairy",
    "markov": "app.testlotto.brains.predict_flow_shaman",
    "review": "app.testlotto.brains.predict_review_king",
}


def import_predict(tag: str):
    import importlib

    return importlib.import_module(PREDICT_MODULES[tag])


def bootstrap_mean_ci(xs, n_boot=4000, seed=SEED):
    rng = random.Random(seed)
    n = len(xs)
    if not n:
        return {"mean": 0.0, "ci95": [0.0, 0.0], "n": 0}
    boots = sorted(
        sum(xs[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot)
    )
    return {
        "mean": round(sum(xs) / n, 6),
        "ci95": [round(boots[int(0.025 * n_boot)], 6), round(boots[int(0.975 * n_boot)], 6)],
        "n": n,
    }


def ci_overlap(a, b):
    return not (a[1] < b[0] or b[1] < a[0])


def gen_brain_sets(tag, draws_before, target, mode: str):
    """mode X=global(cutoff off), Y=cutoff on as_of=target."""
    mod = import_predict(tag)
    os.environ.pop("ROK21_LEARN_CUTOFF", None)
    set_learn_as_of(None)
    if mode == "Y":
        os.environ["ROK21_LEARN_CUTOFF"] = "1"
        set_learn_as_of(target)
    random.seed(SEED + target * 17 + hash(tag) % 1000)
    try:
        sets = mod.predict_sets(draws_before, SETS_PER_PREDICT_BRAIN)
    finally:
        os.environ.pop("ROK21_LEARN_CUTOFF", None)
        set_learn_as_of(None)
    return [list(s.get("nums") or []) for s in (sets or [])]


def pool_hash(pool):
    blob = json.dumps(pool, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


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
    return float(lr.coef_[0]), sigma, n


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
        picked.append(sorted(entries[best_i]["nums"]))
        covered |= set(entries[best_i]["nums"])
    return picked


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
                    "nums": nums,
                }
            )
        prev = nums
    return rows


def main():
    init_testlotto_db()
    clear_history_cache()
    draws = _load_draws()
    traps = _load_traps()
    use = [d for d in draws if int(d["draw_no"]) >= 2][-LAST_N:]

    # ----- P1 OFF hash -----
    print("P1 OFF hash...", flush=True)
    os.environ.pop("ROK21_LEARN_CUTOFF", None)
    set_learn_as_of(None)
    payloads_off = []
    for d in use[-30:]:
        td = int(d["draw_no"])
        before = _draws_before(draws, td)
        pool = []
        for tag in ("stat", "markov", "review"):
            pool.extend(gen_brain_sets(tag, before, td, "X"))
        payloads_off.append(pool)
    h_unset = pool_hash(payloads_off)

    os.environ["ROK21_LEARN_CUTOFF"] = "0"
    payloads_0 = []
    for d in use[-30:]:
        td = int(d["draw_no"])
        before = _draws_before(draws, td)
        pool = []
        for tag in ("stat", "markov", "review"):
            pool.extend(gen_brain_sets(tag, before, td, "X"))
        payloads_0.append(pool)
    h_zero = pool_hash(payloads_0)
    os.environ.pop("ROK21_LEARN_CUTOFF", None)

    # ON/OFF diff sample (3 draws)
    diff_samples = []
    for d in use[-3:]:
        td = int(d["draw_no"])
        before = _draws_before(draws, td)
        px = []
        py = []
        for tag in ("stat", "markov", "review"):
            px.extend(gen_brain_sets(tag, before, td, "X"))
            py.extend(gen_brain_sets(tag, before, td, "Y"))
        diff_samples.append(
            {
                "draw_no": td,
                "x_hash": pool_hash(px),
                "y_hash": pool_hash(py),
                "identical": px == py,
                "x_preview": px[:2],
                "y_preview": py[:2],
            }
        )

    p1 = {
        "off_hash_unset": h_unset,
        "off_hash_explicit0": h_zero,
        "off_identical": h_unset == h_zero,
        "on_off_diff_samples": diff_samples,
        "choice": {
            "method": "b_replay_from_brain_review",
            "rejected_a": "DB 스키마 변경 금지로 history 테이블 불가",
            "cost": "피드백 3698행 1회 재생 O(D)·메모리 수 MB·이후 조회 O(log D)",
        },
    }
    print(json.dumps({"P1": {"off_identical": p1["off_identical"], "diffs": [
        {k: s[k] for k in ("draw_no", "identical")} for s in diff_samples
    ]}}, ensure_ascii=False), flush=True)

    # ----- P2 X vs Y -----
    print("P2 regenerate 200...", flush=True)
    clear_history_cache()
    metrics = {
        "X": {"all_hits": [], "unique": [], "by_brain": defaultdict(list)},
        "Y": {"all_hits": [], "unique": [], "by_brain": defaultdict(list)},
    }
    y_pools = {}  # td -> list of {brain,nums}
    raw_rows = []

    for i, d in enumerate(use):
        td = int(d["draw_no"])
        before = _draws_before(draws, td)
        actual = sorted_nums(d)
        for mode in ("X", "Y"):
            pool_entries = []
            all_sets = []
            for tag in ("stat", "markov", "review"):
                sets = gen_brain_sets(tag, before, td, mode)
                for nums in sets:
                    all_sets.append(nums)
                    pool_entries.append({"brain": tag, "nums": nums})
                    metrics[mode]["by_brain"][tag].append(
                        len(set(nums) & set(actual))
                    )
            if all_sets:
                metrics[mode]["all_hits"].append(
                    sum(len(set(s) & set(actual)) for s in all_sets) / len(all_sets)
                )
                metrics[mode]["unique"].append(
                    len(set().union(*[set(s) for s in all_sets]))
                )
            if mode == "Y":
                y_pools[td] = pool_entries
        if (i + 1) % 20 == 0:
            print(f"  regen {i+1}/{len(use)}", flush=True)
        raw_rows.append({"draw_no": td})

    def pack_mode(mode):
        hit = bootstrap_mean_ci(metrics[mode]["all_hits"], seed=SEED + ord(mode))
        uni = float(np.mean(metrics[mode]["unique"])) if metrics[mode]["unique"] else 0
        brains = {}
        for tag in ("stat", "markov", "review"):
            brains[tag] = bootstrap_mean_ci(
                [float(x) for x in metrics[mode]["by_brain"][tag]],
                seed=SEED + hash(tag) % 99,
            )
        return {
            "mean_hit": hit,
            "unique_nums_mean": round(uni, 4),
            "by_brain_mean": brains,
        }

    pack_X = pack_mode("X")
    pack_Y = pack_mode("Y")
    # delta X - Y bootstrap
    rng = random.Random(SEED + 3)
    n0 = min(len(metrics["X"]["all_hits"]), len(metrics["Y"]["all_hits"]))
    diffs = []
    for _ in range(4000):
        idx = [rng.randrange(n0) for _ in range(n0)]
        mx = sum(metrics["X"]["all_hits"][i] for i in idx) / n0
        my = sum(metrics["Y"]["all_hits"][i] for i in idx) / n0
        diffs.append(mx - my)
    diffs.sort()
    d_ci = [diffs[int(0.025 * 4000)], diffs[int(0.975 * 4000)]]
    leak_sig = d_ci[0] > 0  # X significantly higher than Y

    p2 = {
        "n": n0,
        "X_global": pack_X,
        "Y_cutoff": pack_Y,
        "delta_X_minus_Y_mean": round(pack_X["mean_hit"]["mean"] - pack_Y["mean_hit"]["mean"], 6),
        "delta_X_minus_Y_ci95": [round(d_ci[0], 6), round(d_ci[1], 6)],
        "X_significantly_above_Y": leak_sig,
        "verdict": (
            "누수_부풀림_유의"
            if leak_sig
            else (
                "실질_누수_없음_비유의"
                if d_ci[0] <= 0 <= d_ci[1]
                else "Y가_더_높음"
            )
        ),
        "review_focus": {
            "X": pack_X["by_brain_mean"]["review"],
            "Y": pack_Y["by_brain_mean"]["review"],
            "audit_ref_0_856": 0.856,
        },
    }
    print(json.dumps({"P2": p2}, ensure_ascii=False, indent=2), flush=True)

    # ----- P3 EV on Y pools -----
    print("P3 EV on Y + placebo200...", flush=True)
    tier_rows = load_tier_rows(draws)
    # re-estimate b on val using features of actual draws (not learn_state) — same as before
    # walk-forward style pairs for b: train popularity on draws < dn for each val in use
    y_val, hat_val = [], []
    for d in use:
        td = int(d["draw_no"])
        xs = [r["x"] for r in tier_rows if r["draw_no"] < td]
        ys = [r["y"] for r in tier_rows if r["draw_no"] < td]
        if len(xs) < 50:
            continue
        row = next((r for r in tier_rows if r["draw_no"] == td), None)
        if not row:
            continue
        m, sc = train_ridge(np.vstack(xs), np.array(ys))
        prev_n = None
        for r in tier_rows:
            if r["draw_no"] >= td:
                break
            prev_n = r["nums"]
        hat_val.append(predict_pop(m, sc, row["nums"], prev_n))
        y_val.append(row["y"])
    b_new, _, _ = ols_b(np.array(y_val), np.array(hat_val))

    # actual D vs A on Y pools with model trained before first use (fixed) + b_new
    first_td = int(use[0]["draw_no"])
    xs0 = [r["x"] for r in tier_rows if r["draw_no"] < first_td]
    ys0 = [r["y"] for r in tier_rows if r["draw_no"] < first_td]
    m0, sc0 = train_ridge(np.vstack(xs0), np.array(ys0))

    evA, evD = [], []
    hits_A, hits_D = [], []
    for d in use:
        td = int(d["draw_no"])
        entries = y_pools.get(td) or []
        if len(entries) < K:
            continue
        before = _draws_before(draws, td)
        prev = sorted_nums(before[-1]) if before else None
        actual = sorted_nums(d)
        pops = [predict_pop(m0, sc0, e["nums"], prev) for e in entries]
        evs = [-p for p in pops]
        A = pick_portfolio(entries, before, td, traps, k=K)
        D = pick_hybrid(entries, evs, K)

        def mean_ev(sets):
            return sum(-predict_pop(m0, sc0, s, prev) for s in sets) / K

        def mean_hit(sets):
            a = set(actual)
            return sum(len(set(s) & a) for s in sets) / len(sets)

        evA.append(mean_ev(A))
        evD.append(mean_ev(D))
        hits_A.append(mean_hit(A))
        hits_D.append(mean_hit(D))

    pred_log = float(np.mean(evD) - np.mean(evA))
    actual_realized = math.exp(b_new * pred_log)

    # placebo: shuffle y labels in tier_rows for training only
    y_true = {r["draw_no"]: r["y"] for r in tier_rows}
    dns = sorted(y_true)
    rngp = random.Random(SEED)
    placebo_raw = []
    for rep in range(N_PLACEBO):
        ys = [y_true[d] for d in dns]
        rngp.shuffle(ys)
        y_perm = {d: ys[i] for i, d in enumerate(dns)}
        # rebuild X,y with permuted labels for train < first_td
        xs_p, ys_p = [], []
        for r in tier_rows:
            if r["draw_no"] >= first_td:
                break
            xs_p.append(r["x"])
            ys_p.append(y_perm[r["draw_no"]])
        if len(xs_p) < 50:
            continue
        mp, scp = train_ridge(np.vstack(xs_p), np.array(ys_p))
        eA, eD = [], []
        for d in use:
            td = int(d["draw_no"])
            entries = y_pools.get(td) or []
            if len(entries) < K:
                continue
            before = _draws_before(draws, td)
            prev = sorted_nums(before[-1]) if before else None
            pops = [predict_pop(mp, scp, e["nums"], prev) for e in entries]
            evs = [-p for p in pops]
            A = pick_portfolio(entries, before, td, traps, k=K)
            Dsets = pick_hybrid(entries, evs, K)
            eA.append(sum(-predict_pop(mp, scp, s, prev) for s in A) / K)
            eD.append(sum(-predict_pop(mp, scp, s, prev) for s in Dsets) / K)
        plog = float(np.mean(eD) - np.mean(eA))
        placebo_raw.append(
            {"rep": rep, "pred_log": plog, "realized": math.exp(b_new * plog)}
        )
        if (rep + 1) % 20 == 0:
            print(f"  placebo {rep+1}/{N_PLACEBO}", flush=True)

    pb = np.array([r["realized"] for r in placebo_raw])
    pb_logs = np.array([r["pred_log"] for r in placebo_raw])
    pb_mean = float(pb.mean())
    net0 = actual_realized / pb_mean
    emp_p = float(np.mean(pb >= actual_realized))

    # bootstrap net with b uncertainty from y_val/hat_val
    y_arr = np.array(y_val)
    h_arr = np.array(hat_val)
    rngb = random.Random(SEED + 11)
    nets = []
    n = len(y_arr)
    for _ in range(5000):
        idx = [rngb.randrange(n) for _ in range(n)]
        b_star, _, _ = ols_b(y_arr[idx], h_arr[idx])
        act = math.exp(b_star * pred_log)
        pbm = float(np.mean(np.exp(b_star * pb_logs)))
        nets.append(act / pbm)
    nets.sort()
    ci = [nets[int(0.025 * len(nets))], nets[int(0.975 * len(nets))]]
    survive = ci[0] > 1.0

    p3 = {
        "b_reestimated": round(b_new, 6),
        "n_cal_pairs": len(y_val),
        "mean_hit_A": round(float(np.mean(hits_A)), 6),
        "mean_hit_D": round(float(np.mean(hits_D)), 6),
        "actual_realized": round(actual_realized, 6),
        "placebo_mean": round(pb_mean, 6),
        "empirical_p": round(emp_p, 6),
        "net_ratio": round(net0, 6),
        "net_ci95": [round(ci[0], 6), round(ci[1], 6)],
        "ci_lower_gt_1": survive,
        "stop_rule_verdict": "EV_배선_유지_K09라벨제거" if survive else "EV_철회_기본OFF_K11기록",
    }
    print(json.dumps({"P3": p3}, ensure_ascii=False, indent=2), flush=True)

    # K-09 status
    if not leak_sig and p2["verdict"] == "실질_누수_없음_비유의":
        k09_status = "CLOSED"
        k09_note = "컷오프 구현+실측 비유의 → 실질 무해 CLOSED"
    else:
        k09_status = "PATCHED"
        k09_note = "컷오프 플래그 구현·누수 유의 시 PATCHED 유지"

    if leak_sig:
        k09_status = "PATCHED"
        k09_note = "컷오프 구현 완료. X>Y 유의 → 누수 존재·컷오프로 차단"

    payload = {
        "ok": True,
        "call_sites": [
            {"file": "app/testlotto/learn_state.py", "fn": "load_learn_state", "note": "진입점+컷오프훅"},
            {"file": "app/testlotto/learn_state.py", "fn": "apply_feedback", "note": "전역만 갱신"},
            {"file": "app/testlotto/brains/predict_stat_fairy.py", "fn": "predict_sets", "line": "~23"},
            {"file": "app/testlotto/brains/predict_review_king.py", "fn": "predict_sets", "line": "~20"},
            {"file": "app/testlotto/predict_statistical.py", "fn": "_statistical_predict", "line": "~181"},
            {"file": "app/testlotto/brains/aux_referee.py", "fn": "score_set/get_referee_weights"},
            {"file": "app/testlotto/brains/coordinator.py", "fn": "_apply_aux_scoring", "line": "~48"},
            {"file": "app/testlotto/walkforward.py", "fn": "review_single_draw", "line": "~110 apply_feedback"},
            {"file": "tools/_rerun_lotto_predictions.py", "fn": "apply_feedback"},
        ],
        "P1": p1,
        "P2": p2,
        "P3": p3,
        "K09": {"status": k09_status, "note": k09_note},
        "label_K09_premise_removable": survive,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    OUT.joinpath("summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT.joinpath("placebo_raw.json").write_text(
        json.dumps(placebo_raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT.joinpath("p2_metrics_raw.json").write_text(
        json.dumps(
            {
                "X_hits": metrics["X"]["all_hits"],
                "Y_hits": metrics["Y"]["all_hits"],
                "X_review": list(metrics["X"]["by_brain"]["review"]),
                "Y_review": list(metrics["Y"]["by_brain"]["review"]),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
