"""stat walk-forward 구간 성적 측정 — READ-ONLY, 회차별 seed (역산 그리드 동일).

DB·learn_state 쓰기 없음. 고정 boost(carry/ending/overdue)로 조건별 재측정.
"""

from __future__ import annotations

import json
import random
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import predict_stat_fairy
from app.testlotto.data_service import _get_draws_before
from app.testlotto.tier_utils import pick_best_set_index, score_predicted_set
from app.testlotto.walkforward import _get_actual, _actual_nums, _score_sets

DB = ROOT / "data" / "lotto_testlotto.db"
SEED_BASE = 20260725
SEED_MUL = 9973
SNAPSHOT_DRAW = 1131


def seed_for_draw(draw_no: int) -> int:
    return SEED_BASE + draw_no * SEED_MUL


def ro_conn() -> sqlite3.Connection:
    uri = f"file:{DB.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_review_snapshots() -> dict[int, dict[str, Any]]:
    """draw_no → weight_snapshot dict (READ-ONLY)."""
    conn = ro_conn()
    try:
        rows = conn.execute(
            """
            SELECT draw_no, weight_snapshot
            FROM testlotto_brain_review
            WHERE brain_tag = 'stat' AND weight_snapshot IS NOT NULL
            ORDER BY draw_no
            """
        ).fetchall()
        out: dict[int, dict[str, Any]] = {}
        for r in rows:
            out[int(r["draw_no"])] = json.loads(r["weight_snapshot"])
        return out
    finally:
        conn.close()


def stat_state_for_draw(
    draw_no: int,
    snap_by_draw: dict[int, dict[str, Any]],
    *,
    carry: float,
    ending: float,
    overdue: float,
) -> dict[str, Any]:
    prev = snap_by_draw.get(draw_no - 1, {})
    st = dict(prev.get("stat") or {})
    miss_counts = dict(st.get("miss_counts") or {})
    return {
        "adjustments": {
            "carry_over_boost": carry,
            "ending_digit_boost": ending,
            "overdue_boost": overdue,
            "pair_boost": float(st.get("adjustments", {}).get("pair_boost", 0.5)),
            "consecutive_boost": float(st.get("adjustments", {}).get("consecutive_boost", 0.5)),
            "odd_even_balance": float(st.get("adjustments", {}).get("odd_even_balance", 0.5)),
        },
        "miss_counts": miss_counts,
        "review_count": int(st.get("review_count", 0)),
        "last_draw_no": int(st.get("last_draw_no", draw_no - 1)),
        "recent_avg_match": float(st.get("recent_avg_match", 0.0)),
    }


def measure_fixed_boost(
    start: int,
    end: int,
    *,
    carry: float,
    ending: float,
    overdue: float,
    label: str,
    snap_by_draw: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """고정 boost + 회차별 seed, DB 쓰기 0."""
    import app.testlotto.learn_state as learn_state_mod

    if snap_by_draw is None:
        snap_by_draw = load_review_snapshots()

    caps = {
        "carry_over_boost": max(carry, learn_state_mod.BOOST_CAPS["carry_over_boost"])
        if carry > learn_state_mod.BOOST_CAPS["carry_over_boost"]
        else carry,
        "ending_digit_boost": max(ending, learn_state_mod.BOOST_CAPS["ending_digit_boost"])
        if ending > learn_state_mod.BOOST_CAPS["ending_digit_boost"]
        else ending,
        "overdue_boost": max(overdue, learn_state_mod.BOOST_CAPS["overdue_boost"])
        if overdue > learn_state_mod.BOOST_CAPS["overdue_boost"]
        else overdue,
        "pair_boost": 0.5,
        "consecutive_boost": 0.5,
        "odd_even_balance": 0.5,
    }
    # 0.5³ 조건: clamp 상한도 0.5로 올려 실제 0.5 적용
    if carry >= 0.5 and ending >= 0.5 and overdue >= 0.5:
        caps = {
            "carry_over_boost": 0.5,
            "ending_digit_boost": 0.5,
            "overdue_boost": 0.5,
            "pair_boost": 0.5,
            "consecutive_boost": 0.5,
            "odd_even_balance": 0.5,
        }

    matches: list[int] = []
    per_draw: list[dict] = []
    skipped = 0
    ctx: dict[str, int] = {"draw_no": start}

    def fake_load(tag: str) -> dict[str, Any]:
        if tag != "stat":
            return learn_state_mod._empty_state()
        return stat_state_for_draw(
            ctx["draw_no"],
            snap_by_draw,
            carry=carry,
            ending=ending,
            overdue=overdue,
        )

    with patch.object(learn_state_mod, "load_learn_state", fake_load), patch.object(
        learn_state_mod, "BOOST_CAPS", caps
    ):
        for draw_no in range(start, end + 1):
            ctx["draw_no"] = draw_no
            random.seed(seed_for_draw(draw_no))

            draws = _get_draws_before(draw_no)
            actual = _get_actual(draw_no)
            if not draws or not actual:
                skipped += 1
                continue

            actual_list = _actual_nums(actual)
            actual_set = set(actual_list)
            bonus = int(actual.get("bonus") or 0)

            sets = predict_stat_fairy.predict_sets(draws, 5)
            if not sets:
                skipped += 1
                continue

            scored_sets, best, best_set_no = _score_sets(sets, actual_set, actual_list, bonus)
            matched = int(best["matched_count"])
            matches.append(matched)
            per_draw.append(
                {
                    "draw_no": draw_no,
                    "seed": seed_for_draw(draw_no),
                    "matched_count": matched,
                    "best_set_no": best_set_no,
                }
            )

    n = len(matches)
    avg = sum(matches) / n if n else 0.0
    dist = {str(i): matches.count(i) for i in range(7)}

    return {
        "label": label,
        "carry_over_boost": carry,
        "ending_digit_boost": ending,
        "overdue_boost": overdue,
        "start_draw": start,
        "end_draw": end,
        "seed_formula": f"{SEED_BASE} + draw_no * {SEED_MUL}",
        "reviewed": n,
        "skipped": skipped,
        "stat_avg_match": round(avg, 4),
        "stat_match_sum": sum(matches),
        "match_distribution": dist,
        "sample_last_3": per_draw[-3:] if per_draw else [],
    }


def run_comparison(
    *,
    ranges: list[tuple[int, int]],
) -> dict[str, Any]:
    snap = load_review_snapshots()
    conditions = [
        ("current_0.5", 0.5, 0.5, 0.5),
        ("recommended", 0.2, 0.3, 0.2),
    ]
    results: list[dict[str, Any]] = []
    for start, end in ranges:
        for label, c, e, o in conditions:
            results.append(
                measure_fixed_boost(
                    start,
                    end,
                    carry=c,
                    ending=e,
                    overdue=o,
                    label=f"{label}_{start}_{end}",
                    snap_by_draw=snap,
                )
            )
    return {
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "method": "READ-ONLY fixed boost + per-draw seed (grid-aligned)",
        "db_writes": 0,
        "conditions": [
            {"key": "current_0.5", "carry": 0.5, "ending": 0.5, "overdue": 0.5},
            {"key": "recommended", "carry": 0.2, "ending": 0.3, "overdue": 0.2},
        ],
        "seed_formula": f"random.seed({SEED_BASE} + draw_no * {SEED_MUL})",
        "miss_counts_source": "weight_snapshot stat at draw_no-1",
        "results": results,
    }


def main() -> None:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "backups/20260725_seed정렬_boost재검증.json"
    payload = run_comparison(
        ranges=[(1132, 1231), (2, 1231)],
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = []
    for r in payload["results"]:
        summary.append(
            {
                "label": r["label"],
                "range": f"{r['start_draw']}~{r['end_draw']}",
                "boost": f"{r['carry_over_boost']}/{r['ending_digit_boost']}/{r['overdue_boost']}",
                "avg": r["stat_avg_match"],
                "sum": r["stat_match_sum"],
                "n": r["reviewed"],
            }
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
