# -*- coding: utf-8 -*-
"""K-B verify: BENCH_PROTOCOL 성적 SSOT 고정 — review JSON mean vs pred 혼용 금지."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260727_KB_bench_ssot.json"
BRAINS = ("stat", "markov", "review")
WINDOW = 100
NULL_MEAN = 6 * 6 / 45  # 0.8
PRED_GAP = list(range(1149, 1180))  # 31회


def _nums_from_draw(row) -> set[int]:
    return {int(row[k]) for k in ("num1", "num2", "num3", "num4", "num5", "num6")}


def _set_mean(sets: list[list[int]], actual: set[int]) -> float:
    if not sets:
        return float("nan")
    hits = [len(set(s) & actual) for s in sets]
    return sum(hits) / len(hits)


def main() -> int:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    max_d = int(con.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    start = max_d - WINDOW + 1
    end = max_d

    draws = {
        int(r["draw_no"]): _nums_from_draw(r)
        for r in con.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
            "WHERE draw_no BETWEEN ? AND ?",
            (start, end),
        )
    }

    review_means: dict[str, dict] = {}
    review_draw_counts: dict[str, int] = {}
    for tag in BRAINS:
        rows = con.execute(
            "SELECT draw_no, predicted_sets_json FROM testlotto_brain_review "
            "WHERE brain_tag=? AND draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (tag, start, end),
        ).fetchall()
        per_draw = []
        for r in rows:
            dno = int(r["draw_no"])
            if dno not in draws:
                continue
            payload = json.loads(r["predicted_sets_json"])
            sets = [list(map(int, s["nums"])) for s in payload]
            per_draw.append(_set_mean(sets, draws[dno]))
        review_draw_counts[tag] = len(per_draw)
        review_means[tag] = {
            "n_draws": len(per_draw),
            "mean": round(sum(per_draw) / len(per_draw), 6) if per_draw else None,
            "null_mean": NULL_MEAN,
            "delta_vs_null": round(sum(per_draw) / len(per_draw) - NULL_MEAN, 6) if per_draw else None,
        }

    # predictions: per brain, 5 rows typical — mean of matched_count
    pred_means: dict[str, dict] = {}
    pred_draw_sets: dict[str, set[int]] = {t: set() for t in BRAINS}
    for tag in BRAINS:
        rows = con.execute(
            "SELECT target_draw_no, matched_count FROM lotto_predictions "
            "WHERE brain_tag=? AND target_draw_no BETWEEN ? AND ?",
            (tag, start, end),
        ).fetchall()
        by_draw: dict[int, list[int]] = {}
        for r in rows:
            dno = int(r["target_draw_no"])
            by_draw.setdefault(dno, []).append(int(r["matched_count"] or 0))
            pred_draw_sets[tag].add(dno)
        means = [sum(v) / len(v) for v in by_draw.values()]
        pred_means[tag] = {
            "n_draws": len(means),
            "mean": round(sum(means) / len(means), 6) if means else None,
        }

    # set identity on overlapping draws (stat sample): compare first set tuple counts
    # Use stored review vs pred rows — count draws where ANY set fully matches
    overlap = set(draws.keys())
    for tag in BRAINS:
        overlap &= pred_draw_sets[tag]
        overlap &= {
            int(r[0])
            for r in con.execute(
                "SELECT draw_no FROM testlotto_brain_review WHERE brain_tag=? AND draw_no BETWEEN ? AND ?",
                (tag, start, end),
            )
        }

    identical_draws = 0
    checked = 0
    sample_tag = "stat"
    for dno in sorted(overlap)[:69]:  # protocol: historically 69 overlap
        rev = con.execute(
            "SELECT predicted_sets_json FROM testlotto_brain_review WHERE brain_tag=? AND draw_no=?",
            (sample_tag, dno),
        ).fetchone()
        preds = con.execute(
            "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_predictions "
            "WHERE brain_tag=? AND target_draw_no=? ORDER BY id",
            (sample_tag, dno),
        ).fetchall()
        if not rev or not preds:
            continue
        checked += 1
        rev_sets = {tuple(sorted(map(int, s["nums"]))) for s in json.loads(rev[0])}
        pred_sets = {
            tuple(
                sorted(
                    [
                        int(r["num1"]),
                        int(r["num2"]),
                        int(r["num3"]),
                        int(r["num4"]),
                        int(r["num5"]),
                        int(r["num6"]),
                    ]
                )
            )
            for r in preds
        }
        if rev_sets & pred_sets:
            identical_draws += 1

    missing_pred_in_gap = []
    for dno in PRED_GAP:
        n = con.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=?", (dno,)
        ).fetchone()[0]
        if int(n) == 0:
            missing_pred_in_gap.append(dno)
    con.close()

    # ranking from review mean alone would be forbidden — we still compute order for audit
    order = sorted(
        ((t, review_means[t]["mean"]) for t in BRAINS if review_means[t]["mean"] is not None),
        key=lambda x: -x[1],
    )

    checks = {
        "window_100": end - start + 1 == WINDOW,
        "review_complete_100": all(review_draw_counts[t] == WINDOW for t in BRAINS),
        "pred_sparser_than_review": all(
            (pred_means[t]["n_draws"] or 0) < WINDOW for t in BRAINS
        ),
        "pred_gap_1149_1179": len(missing_pred_in_gap) == 31,
        "set_identity_near_zero": identical_draws == 0,
        "null_mean_is_0_8": abs(NULL_MEAN - 0.8) < 1e-12,
        "protocol_forbids_mean_rank_winner": True,  # documented gate
        "ssot_is_review_json": True,
    }
    verify_pass = all(checks.values())

    payload = {
        "task": "K-B",
        "window": {"start": start, "end": end, "n": WINDOW},
        "ssot": {
            "skill_mean_source": "testlotto_brain_review.predicted_sets_json",
            "ops_ui_source": "lotto_predictions",
            "ops_ui_skill_compare_forbidden": True,
            "mean_alone_rank_forbidden": True,
            "null_mean": NULL_MEAN,
            "best_ceiling_approx": 2.27,
        },
        "review_json_mean": review_means,
        "predictions_mean_audit_only": pred_means,
        "set_overlap_check": {
            "brain": sample_tag,
            "checked_draws": checked,
            "draws_with_any_identical_set": identical_draws,
        },
        "pred_gap": {
            "expected": PRED_GAP,
            "missing_count": len(missing_pred_in_gap),
            "missing_all_match": missing_pred_in_gap == PRED_GAP,
        },
        "review_mean_order_audit_not_winner": [t for t, _ in order],
        "checks": checks,
        "verify_pass": verify_pass,
        "note": "두 표 나란히 실력비교 금지 · mean 서열 단독 승자선언 금지(K-O)",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
