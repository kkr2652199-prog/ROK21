"""ROK21 테스트로또 1단계 — 1232~1234 동기화·채점·아틀라스·1235 예측.

원본 kweon 미접촉. random.choices / _get_draws_before 동결 유지.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "tools"
ATLAS_PATH = OUT_DIR / "_testlotto_pattern_atlas_1234.json"
BASELINE_PATH = OUT_DIR / "_testlotto_stage1_baseline_1232_1234.json"
SUMMARY_PATH = OUT_DIR / "_testlotto_stage1_summary.json"


def _sync_draws(start: int = 1232, end: int = 1234) -> dict[str, Any]:
    from app.testlotto.data_service import fetch_single_draw, save_draw
    from app.testlotto.draw_analysis import upsert_draw_features
    from app.testlotto.draw_archive import sync_draw_archive_range
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.prize_tiers import sync_prize_tiers_range

    init_testlotto_db()
    fetched: list[int] = []
    failed: list[int] = []
    for draw_no in range(start, end + 1):
        conn = get_lotto_db()
        exists = conn.execute(
            "SELECT 1 FROM lotto_draws WHERE draw_no = ?", (draw_no,)
        ).fetchone()
        conn.close()
        if exists:
            fetched.append(draw_no)
            upsert_draw_features(draw_no)
            continue
        draw = fetch_single_draw(draw_no)
        if not draw:
            failed.append(draw_no)
            continue
        save_draw(draw)
        upsert_draw_features(draw_no)
        fetched.append(draw_no)
        time.sleep(0.35)

    tiers = sync_prize_tiers_range(start, end, sleep_sec=0.35)
    # stores 수집은 느리고 실패해도 1단계 성공 조건 아님 — detail/tiers 우선
    archive = sync_draw_archive_range(start, end, fetch_stores=False, sleep_sec=0.4)

    conn = get_lotto_db()
    try:
        mx = conn.execute("SELECT MAX(draw_no), COUNT(*) FROM lotto_draws").fetchone()
        feat_mx = conn.execute(
            "SELECT MAX(draw_no), COUNT(*) FROM testlotto_draw_features"
        ).fetchone()
        tier_mx = conn.execute(
            "SELECT MAX(draw_no), COUNT(DISTINCT draw_no) FROM testlotto_draw_prize_tiers"
        ).fetchone()
        detail_mx = conn.execute(
            "SELECT MAX(draw_no), COUNT(*) FROM testlotto_draw_detail"
        ).fetchone()
        latest = [
            dict(r)
            for r in conn.execute(
                "SELECT draw_no, draw_date, num1,num2,num3,num4,num5,num6, bonus "
                "FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
                (start, end),
            )
        ]
    finally:
        conn.close()

    return {
        "fetched_or_present": fetched,
        "failed": failed,
        "tiers": tiers,
        "archive": {
            "synced": archive.get("synced"),
            "failed": archive.get("failed"),
        },
        "max_draw": int(mx[0] or 0),
        "draw_count": int(mx[1] or 0),
        "features_max": int(feat_mx[0] or 0),
        "features_count": int(feat_mx[1] or 0),
        "tiers_max": int(tier_mx[0] or 0),
        "tiers_draw_count": int(tier_mx[1] or 0),
        "detail_max": int(detail_mx[0] or 0) if detail_mx and detail_mx[0] else 0,
        "detail_count": int(detail_mx[1] or 0) if detail_mx else 0,
        "latest_rows": latest,
        "ok": int(mx[0] or 0) >= end and not failed,
    }


def _score_and_feedback(start: int = 1232, end: int = 1234) -> dict[str, Any]:
    from app.testlotto.engine import refresh_prediction_scores_for_target_draw
    from app.testlotto.feedback import maybe_update_brain_weights_after_scoring
    from app.testlotto.learn_state import get_all_learn_states
    from app.testlotto.models import get_lotto_db
    from app.testlotto.walkforward import review_single_draw

    per_draw: list[dict[str, Any]] = []
    for draw_no in range(start, end + 1):
        scored = refresh_prediction_scores_for_target_draw(draw_no)
        maybe_update_brain_weights_after_scoring(draw_no)
        review = review_single_draw(draw_no, store_features=True)

        conn = get_lotto_db()
        try:
            rows = conn.execute(
                """
                SELECT brain_tag,
                       COUNT(*) AS n,
                       ROUND(AVG(matched_count), 4) AS avg_match,
                       SUM(CASE WHEN matched_count=6 THEN 1 ELSE 0 END) AS r1,
                       SUM(CASE WHEN matched_count=5 AND bonus_matched=1 THEN 1 ELSE 0 END) AS r2,
                       SUM(CASE WHEN matched_count=5 AND IFNULL(bonus_matched,0)=0 THEN 1 ELSE 0 END) AS r3,
                       SUM(CASE WHEN matched_count=4 THEN 1 ELSE 0 END) AS r4,
                       SUM(CASE WHEN matched_count=3 THEN 1 ELSE 0 END) AS r5
                FROM lotto_predictions
                WHERE target_draw_no = ?
                  AND brain_tag IN ('stat','markov','review')
                GROUP BY brain_tag
                ORDER BY brain_tag
                """,
                (draw_no,),
            ).fetchall()
            brain_stats = [dict(r) for r in rows]
            overall = conn.execute(
                """
                SELECT COUNT(*) AS n,
                       ROUND(AVG(matched_count), 4) AS avg_match
                FROM lotto_predictions
                WHERE target_draw_no = ?
                  AND brain_tag IN ('stat','markov','review')
                """,
                (draw_no,),
            ).fetchone()
        finally:
            conn.close()

        per_draw.append(
            {
                "draw_no": draw_no,
                "scores_refreshed": bool(scored),
                "review": {
                    "skipped": review.get("skipped"),
                    "reason": review.get("reason"),
                    "brains": [
                        {
                            "brain_tag": b.get("brain_tag"),
                            "matched_count": b.get("matched_count"),
                            "bonus_matched": b.get("bonus_matched"),
                            "tier_label": b.get("tier_label"),
                        }
                        for b in (review.get("results") or [])
                        if not b.get("skipped")
                    ],
                },
                "prediction_stats": brain_stats,
                "overall_avg_match": float(overall["avg_match"] or 0) if overall else 0,
                "prediction_count": int(overall["n"] or 0) if overall else 0,
            }
        )

    states = get_all_learn_states()
    lean = {
        tag: {
            "review_count": s.get("review_count"),
            "last_draw_no": s.get("last_draw_no"),
            "recent_avg_match": s.get("recent_avg_match"),
            "adjustments": s.get("adjustments"),
        }
        for tag, s in states.items()
    }
    out = {"start": start, "end": end, "per_draw": per_draw, "learn_states": lean}
    BASELINE_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _build_atlas(max_draw: int = 1234) -> dict[str, Any]:
    from app.testlotto.features.draw_features import (
        ac_value,
        consecutive_pairs,
        odd_even_ratio,
        sorted_nums,
    )
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT * FROM lotto_draws WHERE draw_no <= ? ORDER BY draw_no",
            (max_draw,),
        ).fetchall()
        draws = [dict(r) for r in rows]
    finally:
        conn.close()

    if not draws:
        raise RuntimeError("draws empty")

    main_c: Counter = Counter()
    bonus_c: Counter = Counter()
    pair_c: Counter = Counter()
    ending_c: Counter = Counter()
    carry_hist: Counter = Counter()
    consec_hist: Counter = Counter()
    odd_hist: Counter = Counter()
    ac_hist: Counter = Counter()
    zone_hist: Counter = Counter()
    sum_list: list[int] = []
    last_seen: dict[int, int] = {}

    prev: dict | None = None
    for d in draws:
        nums = sorted_nums(d)
        main_c.update(nums)
        bonus_c[int(d["bonus"])] += 1
        for a, b in combinations(nums, 2):
            pair_c[(a, b)] += 1
        for n in nums:
            ending_c[n % 10] += 1
            last_seen[n] = int(d["draw_no"])
        if prev:
            carry = len(set(nums) & set(sorted_nums(prev)))
            carry_hist[carry] += 1
        consec_hist[consecutive_pairs(nums)] += 1
        odd, _even = odd_even_ratio(nums)
        odd_hist[odd] += 1
        ac_hist[ac_value(nums)] += 1
        zones = (
            sum(1 for n in nums if 1 <= n <= 15),
            sum(1 for n in nums if 16 <= n <= 30),
            sum(1 for n in nums if 31 <= n <= 45),
        )
        zone_hist[str(list(zones))] += 1
        sum_list.append(sum(nums))
        prev = d

    latest = int(draws[-1]["draw_no"])
    n_draws = len(draws)
    numbers = []
    for n in range(1, 46):
        numbers.append(
            {
                "number": n,
                "main_count": int(main_c.get(n, 0)),
                "bonus_count": int(bonus_c.get(n, 0)),
                "main_rate_per_draw": round(main_c.get(n, 0) / n_draws, 6),
                "gap_since_last": latest - int(last_seen.get(n, 0)),
            }
        )
    numbers_sorted = sorted(numbers, key=lambda x: (-x["main_count"], x["number"]))
    top_pairs = [
        {"pair": [a, b], "count": c}
        for (a, b), c in pair_c.most_common(40)
    ]
    bottom_pairs = [
        {"pair": [a, b], "count": c}
        for (a, b), c in sorted(pair_c.items(), key=lambda x: (x[1], x[0]))[:20]
    ]
    sum_sorted = sorted(sum_list)
    atlas = {
        "meta": {
            "max_draw": latest,
            "draw_count": n_draws,
            "min_draw": int(draws[0]["draw_no"]),
            "note": "historical signal atlas - no future jackpot claim; independent draws",
        },
        "numbers": numbers_sorted,
        "bonus_top": [
            {"number": n, "count": c} for n, c in bonus_c.most_common(15)
        ],
        "ending_digits": {str(k): int(v) for k, v in sorted(ending_c.items())},
        "pairs_top40": top_pairs,
        "pairs_bottom20_observed": bottom_pairs,
        "structure": {
            "carry_over_hist": {str(k): int(v) for k, v in sorted(carry_hist.items())},
            "consecutive_hist": {str(k): int(v) for k, v in sorted(consec_hist.items())},
            "odd_count_hist": {str(k): int(v) for k, v in sorted(odd_hist.items())},
            "ac_hist": {str(k): int(v) for k, v in sorted(ac_hist.items())},
            "zone_lmh_hist_top": [
                {"zones": k, "count": v}
                for k, v in zone_hist.most_common(15)
            ],
            "sum": {
                "min": sum_sorted[0],
                "max": sum_sorted[-1],
                "mean": round(sum(sum_list) / len(sum_list), 3),
                "p25": sum_sorted[len(sum_sorted) // 4],
                "p50": sum_sorted[len(sum_sorted) // 2],
                "p75": sum_sorted[(3 * len(sum_sorted)) // 4],
            },
        },
    }
    ATLAS_PATH.write_text(json.dumps(atlas, ensure_ascii=False, indent=2), encoding="utf-8")
    return atlas


def _predict_1235() -> dict[str, Any]:
    from app.testlotto.brains.coordinator import run_coordinated_prediction
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.models import get_lotto_db

    prior = _get_draws_before(1235)
    max_prior = max(d["draw_no"] for d in prior) if prior else 0
    if max_prior != 1234:
        return {
            "ok": False,
            "error": f"_get_draws_before(1235) max_prior={max_prior}, expected 1234",
            "prior_count": len(prior),
        }

    pred = run_coordinated_prediction(1235)
    conn = get_lotto_db()
    try:
        by = conn.execute(
            """
            SELECT brain_tag, COUNT(*) AS n
            FROM lotto_predictions
            WHERE target_draw_no = 1235
              AND brain_tag IN ('stat','markov','review')
            GROUP BY brain_tag
            ORDER BY brain_tag
            """
        ).fetchall()
        counts = {r["brain_tag"]: int(r["n"]) for r in by}
    finally:
        conn.close()

    return {
        "ok": True,
        "max_prior_draw": max_prior,
        "prior_count": len(prior),
        "prediction_keys": list(pred.keys()) if isinstance(pred, dict) else [],
        "error": pred.get("error") if isinstance(pred, dict) else None,
        "saved_counts": counts,
        "total_saved": sum(counts.values()),
    }


def main() -> int:
    print("=== Step A: sync 1232-1234 ===", flush=True)
    sync = _sync_draws(1232, 1234)
    print(json.dumps({k: sync[k] for k in sync if k != "latest_rows"}, ensure_ascii=False, indent=2), flush=True)
    if not sync.get("ok"):
        print("SYNC FAILED", flush=True)
        SUMMARY_PATH.write_text(json.dumps({"sync": sync}, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    print("=== Step B: score+feedback ===", flush=True)
    baseline = _score_and_feedback(1232, 1234)
    print(
        json.dumps(
            {
                "per_draw_avg": [
                    {"draw_no": d["draw_no"], "avg": d["overall_avg_match"], "n": d["prediction_count"]}
                    for d in baseline["per_draw"]
                ],
                "learn_states": baseline["learn_states"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )

    print("=== Step C: pattern atlas ===", flush=True)
    atlas = _build_atlas(1234)
    print(
        json.dumps(
            {
                "meta": atlas["meta"],
                "top5_numbers": atlas["numbers"][:5],
                "top5_pairs": atlas["pairs_top40"][:5],
                "bonus_top5": atlas["bonus_top"][:5],
                "sum": atlas["structure"]["sum"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )

    print("=== Step D: predict 1235 ===", flush=True)
    pred = _predict_1235()
    print(json.dumps(pred, ensure_ascii=False, indent=2), flush=True)

    summary = {
        "sync": {k: sync[k] for k in sync if k != "latest_rows"},
        "latest_draws": sync.get("latest_rows"),
        "baseline_path": str(BASELINE_PATH),
        "atlas_path": str(ATLAS_PATH),
        "baseline_avgs": [
            {"draw_no": d["draw_no"], "avg_match": d["overall_avg_match"], "n": d["prediction_count"]}
            for d in baseline["per_draw"]
        ],
        "learn_states": baseline["learn_states"],
        "atlas_meta": atlas["meta"],
        "atlas_sum": atlas["structure"]["sum"],
        "atlas_top_numbers": atlas["numbers"][:10],
        "atlas_top_pairs": atlas["pairs_top40"][:10],
        "atlas_bonus_top": atlas["bonus_top"][:10],
        "predict_1235": pred,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", SUMMARY_PATH, flush=True)
    return 0 if pred.get("ok") and pred.get("total_saved", 0) >= 15 else 2


if __name__ == "__main__":
    raise SystemExit(main())
