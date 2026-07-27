# -*- coding: utf-8 -*-
"""K-00 — 과거 예측 숙제 확장 (READ-ONLY · testlotto_brain_review SSOT).

1235 대기 중 선행: 1~1234 brain_review 재집계 · stage1 창(1232~1234) · predictions 갭.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260728_K00_homework_expand.json"
LEGACY = ROOT / "docs" / "benchmarks" / "20260726_과거예측숙제_1to1234" / "homework_stats.json"


def _brain_stats(con: sqlite3.Connection, lo: int, hi: int) -> dict[str, Any]:
    rows = con.execute(
        """
        SELECT brain_tag,
               COUNT(*) AS n,
               ROUND(AVG(matched_count), 4) AS avg_m,
               SUM(CASE WHEN matched_count >= 3 THEN 1 ELSE 0 END) AS ge3,
               SUM(CASE WHEN matched_count >= 4 THEN 1 ELSE 0 END) AS ge4,
               SUM(CASE WHEN matched_count >= 5 THEN 1 ELSE 0 END) AS ge5,
               SUM(CASE WHEN IFNULL(bonus_matched,0)=1 THEN 1 ELSE 0 END) AS bonus_hits
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN ? AND ?
        GROUP BY brain_tag
        ORDER BY brain_tag
        """,
        (lo, hi),
    ).fetchall()
    return {
        str(r[0]): {
            "brain_tag": r[0],
            "n": int(r[1]),
            "avg_m": float(r[2] or 0),
            "ge3": int(r[3] or 0),
            "ge4": int(r[4] or 0),
            "ge5": int(r[5] or 0),
            "bonus_hits": int(r[6] or 0),
        }
        for r in rows
    }


def _match_hist(con: sqlite3.Connection, lo: int, hi: int) -> dict[str, int]:
    rows = con.execute(
        """
        SELECT matched_count, COUNT(*) AS n
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN ? AND ?
        GROUP BY matched_count
        ORDER BY matched_count
        """,
        (lo, hi),
    ).fetchall()
    return {str(int(r[0])): int(r[1]) for r in rows}


def _pred_gap(con: sqlite3.Connection, lo: int, hi: int) -> dict[str, Any]:
    review_draws = {
        int(r[0])
        for r in con.execute(
            "SELECT DISTINCT draw_no FROM testlotto_brain_review WHERE draw_no BETWEEN ? AND ?",
            (lo, hi),
        ).fetchall()
    }
    pred_draws = {
        int(r[0])
        for r in con.execute(
            """
            SELECT DISTINCT target_draw_no
            FROM lotto_predictions
            WHERE target_draw_no BETWEEN ? AND ?
              AND brain_tag IN ('stat','markov','review')
            """,
            (lo, hi),
        ).fetchall()
    }
    sparse = sorted(review_draws - pred_draws)
    return {
        "review_draws": len(review_draws),
        "pred_scored_draws": len(pred_draws),
        "review_only_draws": len(sparse),
        "review_only_sample_tail": sparse[-10:] if sparse else [],
    }


def _miss_from_review(con: sqlite3.Connection, lo: int, hi: int) -> dict[str, Any]:
    from collections import Counter

    rows = con.execute(
        """
        SELECT brain_tag, missed_patterns
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN ? AND ? AND missed_patterns IS NOT NULL
        """,
        (lo, hi),
    ).fetchall()
    by_brain: dict[str, Counter] = {}
    for tag, raw in rows:
        if not raw:
            continue
        try:
            missed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(missed, list):
            continue
        c = by_brain.setdefault(str(tag), Counter())
        for item in missed:
            if isinstance(item, dict):
                key = item.get("pattern") or item.get("type") or item.get("name")
            else:
                key = str(item)
            if key:
                c[str(key)] += 1
    out: dict[str, Any] = {}
    for tag, ctr in sorted(by_brain.items()):
        top = ctr.most_common(3)
        out[tag] = {
            "top_miss": [{"pattern": k, "count": v} for k, v in top],
            "ending_digit_count": int(ctr.get("ending_digit", 0)),
            "total_tagged_misses": sum(ctr.values()),
        }
    return out


def _learn_miss(con: sqlite3.Connection) -> dict[str, Any]:
    rows = con.execute(
        "SELECT brain_tag, state_json FROM testlotto_brain_learn_state ORDER BY brain_tag"
    ).fetchall()
    out: dict[str, Any] = {}
    for tag, raw in rows:
        state = json.loads(raw) if raw else {}
        miss = state.get("miss_counts") or {}
        top = sorted(miss.items(), key=lambda x: (-x[1], x[0]))[:3]
        out[str(tag)] = {
            "top_miss": [{"pattern": k, "count": v} for k, v in top],
            "ending_digit_count": int(miss.get("ending_digit") or 0),
            "review_count": state.get("review_count"),
            "last_draw_no": state.get("last_draw_no"),
            "recent_avg_match": state.get("recent_avg_match"),
        }
    return out


def _stage1_compare(con: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = con.execute(
        """
        SELECT r.draw_no, r.brain_tag,
               r.matched_count AS review_match,
               ROUND(AVG(p.matched_count), 4) AS pred_avg_match,
               COUNT(p.rowid) AS pred_n
        FROM testlotto_brain_review r
        LEFT JOIN lotto_predictions p
          ON p.target_draw_no = r.draw_no AND p.brain_tag = r.brain_tag
        WHERE r.draw_no BETWEEN 1232 AND 1234
        GROUP BY r.draw_no, r.brain_tag
        ORDER BY r.draw_no, r.brain_tag
        """
    ).fetchall()
    return [
        {
            "draw_no": int(r[0]),
            "brain_tag": r[1],
            "review_best_match": int(r[2]),
            "pred_avg_match": float(r[3] or 0),
            "pred_n": int(r[4] or 0),
        }
        for r in rows
    ]


def main() -> int:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        mx, cnt = con.execute(
            "SELECT MAX(draw_no), COUNT(*) FROM lotto_draws"
        ).fetchone()
        review_mx, review_n = con.execute(
            "SELECT MAX(draw_no), COUNT(*) FROM testlotto_brain_review"
        ).fetchone()
        pred_dist = con.execute(
            """
            SELECT COUNT(DISTINCT target_draw_no), COUNT(*)
            FROM lotto_predictions
            WHERE brain_tag IN ('stat','markov','review')
            """
        ).fetchone()

        full = _brain_stats(con, 2, int(mx or 0))
        w1132 = _brain_stats(con, 1132, int(mx or 0))
        w1232 = _brain_stats(con, 1232, int(mx or 0))
        hist = _match_hist(con, 2, int(mx or 0))
        gap = _pred_gap(con, 2, int(mx or 0))
        miss_review = _miss_from_review(con, 2, int(mx or 0))
        miss = _learn_miss(con)
        stage1 = _stage1_compare(con)
    finally:
        con.close()

    legacy_avg = {}
    if LEGACY.is_file():
        leg = json.loads(LEGACY.read_text(encoding="utf-8"))
        for tag, v in (leg.get("brain_review") or {}).items():
            legacy_avg[tag] = v.get("avg_m")

    drift_ok = True
    drift_notes: list[str] = []
    for tag, v in full.items():
        old = legacy_avg.get(tag)
        if old is not None and abs(v["avg_m"] - float(old)) > 0.02:
            drift_ok = False
            drift_notes.append(f"{tag}: legacy={old} now={v['avg_m']}")

    checks = {
        "draws_max_1234": int(mx or 0) == 1234,
        "review_max_1234": int(review_mx or 0) == 1234,
        "three_brains_full": set(full.keys()) >= {"stat", "markov", "review"},
        "legacy_avg_drift_lt_0_02": drift_ok,
        "ending_digit_top_miss_all": all(
            (miss_review.get(t) or {}).get("top_miss", [{}])[0].get("pattern") == "ending_digit"
            for t in ("stat", "markov", "review")
            if t in miss_review
        ),
        "stage1_window_present": len(w1232) == 3,
    }
    verify_pass = all(checks.values())

    payload = {
        "task": "K-00",
        "purpose": "homework_expand_readonly",
        "source_table": "testlotto_brain_review",
        "draws_in_db": {"max": int(mx or 0), "count": int(cnt or 0)},
        "brain_review_rows": int(review_n or 0),
        "lotto_predictions": {
            "distinct_targets": int(pred_dist[0] or 0),
            "rows_main_brains": int(pred_dist[1] or 0),
        },
        "brain_review_full": full,
        "match_hist_all_brains": hist,
        "window_1132_1234": w1132,
        "window_1232_1234": w1232,
        "pred_vs_review_gap": gap,
        "stage1_compare_1232_1234": stage1,
        "miss_patterns_from_review": miss_review,
        "learn_state_miss_top": miss,
        "legacy_drift_notes": drift_notes,
        "checks": checks,
        "verify_pass": verify_pass,
        "homework_ssot_decision": "brain_review remains SSOT for 1~1234 homework; lotto_predictions sparse",
        "next_homework": [
            "1235 발표 후 brain_review 1235행 추가 (K-AWAIT execute)",
            "ending_digit miss vs boost 루프 진단 (K-P 계열 후보)",
            "ge4 희귀 케이스 구조 해부",
        ],
        "note": "READ-ONLY · no walkforward rerun · no DB write",
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
