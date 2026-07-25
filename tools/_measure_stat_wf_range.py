"""stat walk-forward 구간 성적 측정 — 1131 스냅샷 복원 후 1132~end 재생."""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import predict_stat_fairy
from app.testlotto.data_service import _get_draws_before
from app.testlotto.draw_analysis import detect_missed_patterns
from app.testlotto.learn_state import apply_feedback, load_learn_state
from app.testlotto.models import get_lotto_db
from app.testlotto.tier_utils import pick_best_set_index, score_predicted_set
from app.testlotto.walkforward import _get_actual, _actual_nums, _score_sets

DB = ROOT / "data" / "lotto_testlotto.db"
START = 1132
END = 1231
SEED = 20260725
SNAPSHOT_DRAW = 1131


def backup_learn_states() -> dict:
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT brain_tag, state_json, review_count, last_draw_no FROM testlotto_brain_learn_state"
        ).fetchall()
        return {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "rows": [dict(r) for r in rows],
        }
    finally:
        conn.close()


def restore_learn_states_backup(backup: dict) -> None:
    conn = get_lotto_db()
    try:
        for r in backup.get("rows", []):
            conn.execute(
                """
                INSERT INTO testlotto_brain_learn_state
                    (brain_tag, state_json, review_count, last_draw_no, updated_at)
                VALUES (?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(brain_tag) DO UPDATE SET
                    state_json=excluded.state_json,
                    review_count=excluded.review_count,
                    last_draw_no=excluded.last_draw_no,
                    updated_at=excluded.updated_at
                """,
                (
                    r["brain_tag"],
                    r["state_json"],
                    int(r["review_count"]),
                    int(r["last_draw_no"]),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def restore_from_review_snapshot(snapshot_draw: int) -> dict:
    conn = get_lotto_db()
    try:
        row = conn.execute(
            "SELECT weight_snapshot FROM testlotto_brain_review WHERE draw_no=? LIMIT 1",
            (snapshot_draw,),
        ).fetchone()
        if not row or not row[0]:
            raise RuntimeError(f"no weight_snapshot at draw {snapshot_draw}")
        snap = json.loads(row[0])
        for tag, state in snap.items():
            conn.execute(
                """
                INSERT INTO testlotto_brain_learn_state
                    (brain_tag, state_json, review_count, last_draw_no, updated_at)
                VALUES (?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(brain_tag) DO UPDATE SET
                    state_json=excluded.state_json,
                    review_count=excluded.review_count,
                    last_draw_no=excluded.last_draw_no,
                    updated_at=excluded.updated_at
                """,
                (
                    tag,
                    json.dumps(state, ensure_ascii=False),
                    int(state.get("review_count", 0)),
                    int(state.get("last_draw_no", 0)),
                ),
            )
        conn.commit()
        return snap
    finally:
        conn.close()


def measure_stat_range(start: int, end: int, *, seed: int, label: str) -> dict:
    random.seed(seed)
    restore_from_review_snapshot(SNAPSHOT_DRAW)

    matches: list[int] = []
    per_draw: list[dict] = []
    skipped = 0

    for draw_no in range(start, end + 1):
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
        missed = detect_missed_patterns(best["nums"], actual_list, draws)
        apply_feedback("stat", draw_no, matched, missed)

        matches.append(matched)
        stat_state = load_learn_state("stat")
        per_draw.append(
            {
                "draw_no": draw_no,
                "matched_count": matched,
                "best_set_no": best_set_no,
                "best_nums": best["nums"],
                "adjustments": dict(stat_state.get("adjustments") or {}),
            }
        )

    n = len(matches)
    avg = sum(matches) / n if n else 0.0
    dist = {str(i): matches.count(i) for i in range(7)}

    return {
        "label": label,
        "start_draw": start,
        "end_draw": end,
        "seed": seed,
        "snapshot_restore_draw": SNAPSHOT_DRAW,
        "reviewed": n,
        "skipped": skipped,
        "stat_avg_match": round(avg, 4),
        "stat_match_sum": sum(matches),
        "match_distribution": dist,
        "stat_learn_state_end": load_learn_state("stat"),
        "sample_last_3": per_draw[-3:] if per_draw else [],
    }


def main() -> None:
    out_path = Path(sys.argv[1])
    label = sys.argv[2] if len(sys.argv) > 2 else "measure"
    backup = backup_learn_states()
    try:
        result = measure_stat_range(START, END, seed=SEED, label=label)
        result["learn_state_backup_note"] = "restored after measure"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({k: result[k] for k in result if k != "sample_last_3"}, ensure_ascii=False, indent=2))
    finally:
        restore_learn_states_backup(backup)


if __name__ == "__main__":
    main()
