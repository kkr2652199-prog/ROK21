"""stat boost 그리드 역산 — READ-ONLY, 최적화(회차별 base weights 1회 계산)."""
from __future__ import annotations

import copy
import itertools
import json
import random
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.testlotto.data_service import _get_draws_before
from app.testlotto.filters import tier1_filter
from app.testlotto.predict_statistical import _statistical_predict
from app.testlotto.tier_utils import pick_best_set_index, score_predicted_set

DB = ROOT / "data" / "lotto_testlotto.db"
BOOST_VALUES = (0.0, 0.1, 0.2, 0.3, 0.5)
SEED_BASE = 20260725


def ro_conn():
    uri = f"file:{DB.as_posix()}?mode=ro"
    c = sqlite3.connect(uri, uri=True)
    c.row_factory = sqlite3.Row
    return c


def load_reviews():
    conn = ro_conn()
    try:
        rows = conn.execute(
            """
            SELECT r.draw_no, r.weight_snapshot,
                   d.num1,d.num2,d.num3,d.num4,d.num5,d.num6,d.bonus
            FROM testlotto_brain_review r
            INNER JOIN lotto_draws d ON d.draw_no = r.draw_no
            WHERE r.brain_tag = 'stat'
            ORDER BY r.draw_no
            """
        ).fetchall()
        snap_by_draw = {}
        reviews = []
        for r in rows:
            dno = int(r["draw_no"])
            if r["weight_snapshot"]:
                snap_by_draw[dno] = json.loads(r["weight_snapshot"])
            reviews.append(
                {
                    "draw_no": dno,
                    "actual": [int(r[f"num{k}"]) for k in range(1, 7)],
                    "bonus": int(r["bonus"]),
                }
            )
        return reviews, snap_by_draw
    finally:
        conn.close()


def miss_counts_before(draw_no: int, snap_by_draw: dict) -> dict:
    prev = snap_by_draw.get(draw_no - 1, {})
    st = prev.get("stat") or {}
    return dict(st.get("miss_counts") or {})


def apply_boosts(
    base_weights: dict[int, float],
    *,
    carry: float,
    ending: float,
    overdue: float,
    draws: list[dict],
    last_seen: dict[int, int],
    latest_draw_no: int,
    miss_counts: dict,
) -> dict[int, float]:
    w = dict(base_weights)
    if overdue > 0:
        for n in range(1, 46):
            if latest_draw_no - last_seen[n] >= 30:
                w[n] *= 1.0 + overdue
    if ending > 0 and int(miss_counts.get("ending_digit", 0) or 0) > 0 and draws:
        prev_endings = {int(draws[-1][f"num{k}"]) % 10 for k in range(1, 7)}
        for n in range(1, 46):
            if n % 10 in prev_endings:
                w[n] *= 1.0 + ending
    if carry > 0 and draws:
        for n in [int(draws[-1][f"num{k}"]) for k in range(1, 7)]:
            if n in w:
                w[n] *= 1.0 + carry
    total = sum(w.values())
    return {n: w[n] / total for n in range(1, 46)}


def predict_with_weights(
    weights: dict[int, float],
    pair_freq: dict,
    n_sets: int = 5,
) -> list[list[int]]:
    """_statistical_predict 샘플링 루프만 재현 (random.choices 동일)."""
    results: list[list[int]] = []
    used: set[tuple[int, ...]] = set()
    attempts = 0
    while len(results) < n_sets and attempts < 5000:
        attempts += 1
        pool = list(range(1, 46))
        w = [weights[n] for n in pool]
        nums: list[int] = []
        for pick_idx in range(6):
            chosen = random.choices(pool, weights=w, k=1)[0]
            nums.append(chosen)
            idx = pool.index(chosen)
            pool.pop(idx)
            w.pop(idx)
            if pick_idx < 5:
                for p_idx, p_num in enumerate(pool):
                    pk = (min(chosen, p_num), max(chosen, p_num))
                    pc = pair_freq.get(pk, 0)
                    if pc >= 5:
                        w[p_idx] *= 1 + min(pc * 0.02, 0.4)
        nums.sort()
        if not tier1_filter(nums):
            continue
        key = tuple(nums)
        if key in used:
            continue
        used.add(key)
        results.append(nums)
    return results


def build_draw_cache(reviews, snap_by_draw):
    """회차별 base_weights·pair_freq — learn_state/boost 제외, feedback까지."""
    import app.testlotto.learn_state as ls

    orig = ls.load_learn_state
    ls.load_learn_state = lambda tag: ls._empty_state()  # type: ignore
    cache = []
    try:
        for rev in reviews:
            dno = rev["draw_no"]
            draws = _get_draws_before(dno)
            if not draws:
                continue
            # _statistical_predict with zero boosts via empty learn state
            sets = _statistical_predict(draws, 5)
            if not sets:
                continue
            # Re-derive: call once more extracting internals via duplicate predict path
            # Use get_statistical_prob_vector + feedback already in weights from predict
            # Simpler: store draws + miss_counts; compute base via monkeypatch returning zeros
            from math import exp

            freq: dict[int, float] = {}
            last_seen: dict[int, int] = {}
            total_draws = len(draws)
            for idx, d in enumerate(draws):
                rw = exp(-0.02 * (total_draws - 1 - idx))
                for k in ["num1", "num2", "num3", "num4", "num5", "num6"]:
                    n = d[k]
                    freq[n] = freq.get(n, 0.0) + rw
                    last_seen[n] = d["draw_no"]
            for n in range(1, 46):
                if n not in freq:
                    freq[n] = 0.1
                if n not in last_seen:
                    last_seen[n] = 0
            latest = draws[-1]["draw_no"]
            for n in range(1, 46):
                gap = latest - last_seen[n]
                if gap >= 50:
                    freq[n] *= 1.3
                elif gap >= 30:
                    freq[n] *= 1.15
            recent_5 = draws[-5:] if len(draws) >= 5 else draws
            hot: dict[int, int] = {}
            for d in recent_5:
                for k in ["num1", "num2", "num3", "num4", "num5", "num6"]:
                    hot[d[k]] = hot.get(d[k], 0) + 1
            for n, c in hot.items():
                if c >= 2:
                    freq[n] *= 1.2
            recent_for_pairs = draws[-200:] if len(draws) >= 200 else draws
            pair_freq: dict[tuple[int, int], int] = {}
            for d in recent_for_pairs:
                ns = sorted([d["num1"], d["num2"], d["num3"], d["num4"], d["num5"], d["num6"]])
                for i in range(len(ns)):
                    for j in range(i + 1, len(ns)):
                        pair = (ns[i], ns[j])
                        pair_freq[pair] = pair_freq.get(pair, 0) + 1
            top_pairs = sorted(pair_freq.items(), key=lambda x: x[1], reverse=True)[:30]
            pbn: dict[int, float] = {}
            for (a, b), cnt in top_pairs:
                bns = 0.05 * cnt
                pbn[a] = pbn.get(a, 0) + bns
                pbn[b] = pbn.get(b, 0) + bns
            for n, b in pbn.items():
                freq[n] *= 1 + min(b, 0.5)
            total = sum(freq.values())
            weights = {n: freq[n] / total for n in range(1, 46)}
            try:
                from app.testlotto.feedback import get_feedback_summary

                fb = get_feedback_summary(last_n=20)
                if fb.get("has_feedback"):
                    for trap_n in fb.get("frequent_traps", []):
                        if trap_n in weights:
                            weights[trap_n] *= 0.8
                    for hit_n in fb.get("frequent_hits", []):
                        if hit_n in weights:
                            weights[hit_n] *= 1.15
            except Exception:
                pass
            cache.append(
                {
                    "draw_no": dno,
                    "actual": rev["actual"],
                    "bonus": rev["bonus"],
                    "draws": draws,
                    "base_weights": weights,
                    "last_seen": last_seen,
                    "latest_draw_no": latest,
                    "pair_freq": pair_freq,
                    "miss_counts": miss_counts_before(dno, snap_by_draw),
                }
            )
    finally:
        ls.load_learn_state = orig
    return cache


def main():
    t0 = time.time()
    reviews, snap_by_draw = load_reviews()
    print(f"building cache for {len(reviews)} draws...", file=sys.stderr)
    cache = build_draw_cache(reviews, snap_by_draw)
    print(f"cached {len(cache)} draws", file=sys.stderr)

    combos = list(itertools.product(BOOST_VALUES, repeat=3))
    results = []

    for ci, (carry, ending, overdue) in enumerate(combos):
        matches = []
        for item in cache:
            random.seed(SEED_BASE + item["draw_no"] * 9973)
            w = apply_boosts(
                item["base_weights"],
                carry=carry,
                ending=ending,
                overdue=overdue,
                draws=item["draws"],
                last_seen=item["last_seen"],
                latest_draw_no=item["latest_draw_no"],
                miss_counts=item["miss_counts"],
            )
            sets = predict_with_weights(w, item["pair_freq"], 5)
            if not sets:
                continue
            scored = [
                {**score_predicted_set(s, item["actual"], item["bonus"]), "nums": s}
                for s in sets
            ]
            idx = pick_best_set_index(scored)
            matches.append(int(scored[idx]["matched_count"]))
        avg = sum(matches) / len(matches) if matches else 0.0
        results.append(
            {
                "carry_over_boost": carry,
                "ending_digit_boost": ending,
                "overdue_boost": overdue,
                "avg_match": round(avg, 4),
                "match_sum": sum(matches),
                "reviewed": len(matches),
            }
        )

    sorted_all = sorted(results, key=lambda x: (-x["avg_match"], -x["match_sum"]))
    rank_current = next(
        i + 1
        for i, r in enumerate(sorted_all)
        if r["carry_over_boost"] == 0.5 and r["ending_digit_boost"] == 0.5 and r["overdue_boost"] == 0.5
    )
    current_row = next(
        r for r in results
        if r["carry_over_boost"] == 0.5 and r["ending_digit_boost"] == 0.5 and r["overdue_boost"] == 0.5
    )

    out = {
        "method": "offline grid re-score READ-ONLY (optimized)",
        "boost_values": list(BOOST_VALUES),
        "draws_used": len(cache),
        "draw_range": [cache[0]["draw_no"], cache[-1]["draw_no"]] if cache else [],
        "seed_per_draw": f"random.seed({SEED_BASE} + draw_no * 9973)",
        "miss_counts_source": "weight_snapshot stat at draw_no-1",
        "total_combos": len(combos),
        "elapsed_sec": round(time.time() - t0, 1),
        "current_all_0.5": current_row,
        "current_rank": rank_current,
        "top3": sorted_all[:3],
        "all_combos": sorted_all,
    }

    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "backups/20260725_boost_grid.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "top3": out["top3"],
                "current_all_0.5": out["current_all_0.5"],
                "current_rank": out["current_rank"],
                "elapsed_sec": out["elapsed_sec"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
