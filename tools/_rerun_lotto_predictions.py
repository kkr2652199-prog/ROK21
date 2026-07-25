#!/usr/bin/env python3
"""lotto_predictions 초기화 + walk-forward 재기록 (boost 0.2/0.3/0.2)."""

from __future__ import annotations

import json
import logging
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.coordinator import run_coordinated_prediction
from app.testlotto.brains import predict_stat_fairy
from app.testlotto.data_service import _get_draws_before
from app.testlotto.draw_analysis import detect_missed_patterns
from app.testlotto.learn_state import apply_feedback, load_learn_state
from app.testlotto.models import get_lotto_db, init_testlotto_db
from app.testlotto.walkforward import _get_actual, _actual_nums, _score_sets

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

SEED_BASE = 20260725
SEED_MUL = 9973
SNAPSHOT_DRAW = 1131
BACKUP_DB = ROOT / "backups/20260725_재기록전_DB전체/lotto_testlotto.db"
LOG_PATH = ROOT / "backups/20260725_예측재기록_progress.log"

# 기존 DB와 동일한 예측 대상 회차
PREDICT_DRAWS = [3] + list(range(1120, 1233))


def seed_for_draw(draw_no: int) -> int:
    return SEED_BASE + draw_no * SEED_MUL


def verify_backup() -> dict:
    if not BACKUP_DB.is_file():
        raise RuntimeError(f"백업 없음: {BACKUP_DB}")
    size = BACKUP_DB.stat().st_size
    if size < 30_000_000:
        raise RuntimeError(f"백업 크기 비정상: {size}")
    return {"path": str(BACKUP_DB), "size_bytes": size}


def snapshot_predictions(conn) -> dict:
    row = conn.execute(
        "SELECT COUNT(*) n, MIN(target_draw_no) mn, MAX(target_draw_no) mx, "
        "COUNT(DISTINCT target_draw_no) d FROM lotto_predictions"
    ).fetchone()
    tags = conn.execute(
        "SELECT brain_tag, COUNT(*) c FROM lotto_predictions GROUP BY brain_tag ORDER BY brain_tag"
    ).fetchall()
    draws = [
        int(r[0])
        for r in conn.execute(
            "SELECT DISTINCT target_draw_no FROM lotto_predictions ORDER BY target_draw_no"
        ).fetchall()
    ]
    return {
        "total_rows": int(row[0]),
        "min_draw": int(row[1] or 0),
        "max_draw": int(row[2] or 0),
        "distinct_draws": int(row[3]),
        "draw_list": draws,
        "by_tag": {str(r[0]): int(r[1]) for r in tags},
    }


def backup_learn_states(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT brain_tag, state_json, review_count, last_draw_no FROM testlotto_brain_learn_state"
    ).fetchall()
    return [dict(r) for r in rows]


def restore_learn_states(conn, rows: list[dict]) -> None:
    for r in rows:
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
            (r["brain_tag"], r["state_json"], int(r["review_count"]), int(r["last_draw_no"])),
        )
    conn.commit()


def backup_brain_weights(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT brain_tag, current_weight, recent_avg_match, total_predictions, "
        "total_matches, last_updated_draw FROM testlotto_brain_weights "
        "WHERE brain_tag IN ('stat','markov','review')"
    ).fetchall()
    return [dict(r) for r in rows]


def restore_brain_weights(conn, rows: list[dict]) -> None:
    for r in rows:
        conn.execute(
            """
            UPDATE testlotto_brain_weights SET
                current_weight=?, recent_avg_match=?, total_predictions=?,
                total_matches=?, last_updated_draw=?, updated_at=datetime('now','localtime')
            WHERE brain_tag=?
            """,
            (
                r["current_weight"],
                r["recent_avg_match"],
                r["total_predictions"],
                r["total_matches"],
                r["last_updated_draw"],
                r["brain_tag"],
            ),
        )
    conn.commit()


def restore_from_review_snapshot(conn, snapshot_draw: int) -> None:
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


def restore_learn_state_for_target(conn, target_draw_no: int) -> None:
    snap_draw = target_draw_no - 1
    if snap_draw < 1:
        return
    row = conn.execute(
        "SELECT weight_snapshot FROM testlotto_brain_review WHERE draw_no=? LIMIT 1",
        (snap_draw,),
    ).fetchone()
    if not row or not row[0]:
        raise RuntimeError(f"no weight_snapshot at draw {snap_draw} for target {target_draw_no}")
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


def measure_dynamic_stat_1132_1231() -> dict:
    """apply_feedback 동적 누적 + 회차별 seed (측정 후 learn_state/brain_weights 원복)."""
    conn = get_lotto_db()
    ls_backup = backup_learn_states(conn)
    bw_backup = backup_brain_weights(conn)
    restore_from_review_snapshot(conn, SNAPSHOT_DRAW)
    conn.close()

    matches: list[int] = []
    for draw_no in range(1132, 1232):
        random.seed(seed_for_draw(draw_no))
        draws = _get_draws_before(draw_no)
        actual = _get_actual(draw_no)
        if not draws or not actual:
            continue
        actual_list = _actual_nums(actual)
        actual_set = set(actual_list)
        bonus = int(actual.get("bonus") or 0)
        sets = predict_stat_fairy.predict_sets(draws, 5)
        if not sets:
            continue
        _, best, _ = _score_sets(sets, actual_set, actual_list, bonus)
        matched = int(best["matched_count"])
        missed = detect_missed_patterns(best["nums"], actual_list, draws)
        apply_feedback("stat", draw_no, matched, missed)
        matches.append(matched)

    avg = sum(matches) / len(matches) if matches else 0.0
    end_adj = load_learn_state("stat").get("adjustments", {})

    conn = get_lotto_db()
    restore_learn_states(conn, ls_backup)
    restore_brain_weights(conn, bw_backup)
    conn.close()

    return {
        "start_draw": 1132,
        "end_draw": 1231,
        "seed_formula": f"{SEED_BASE} + draw_no * {SEED_MUL}",
        "path": "dynamic apply_feedback",
        "reviewed": len(matches),
        "stat_avg_match": round(avg, 4),
        "stat_end_adjustments": end_adj,
    }


def delete_predictions(conn) -> int:
    before = conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0]
    conn.execute("DELETE FROM lotto_predictions")
    conn.commit()
    after = conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0]
    return int(before), int(after)


def rerun_predictions(draw_list: list[int]) -> list[dict]:
    init_testlotto_db()
    conn = get_lotto_db()
    ls_backup = backup_learn_states(conn)
    logs: list[dict] = []

    try:
        for i, draw_no in enumerate(draw_list):
            restore_learn_state_for_target(conn, draw_no)
            random.seed(seed_for_draw(draw_no))
            result = run_coordinated_prediction(draw_no)
            err = result.get("error")
            logs.append(
                {
                    "draw_no": draw_no,
                    "index": i + 1,
                    "total": len(draw_list),
                    "error": err,
                    "status": result.get("status"),
                }
            )
            if err:
                raise RuntimeError(f"회차 {draw_no} 예측 실패: {err}")
            if (i + 1) % 10 == 0 or draw_no >= 1230:
                msg = f"[재기록] {i+1}/{len(draw_list)} draw={draw_no} OK"
                logger.info(msg)
                LOG_PATH.open("a", encoding="utf-8").write(msg + "\n")
    finally:
        restore_learn_states(conn, ls_backup)
        conn.close()

    return logs


def stat_sets_for_draw(draw_no: int) -> list[dict]:
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT num1,num2,num3,num4,num5,num6, confidence, brain_tag
        FROM lotto_predictions
        WHERE target_draw_no=? AND brain_tag='stat'
        ORDER BY confidence DESC
        LIMIT 5
        """,
        (draw_no,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def review_alignment(conn) -> dict:
    pred_draws = {
        int(r[0])
        for r in conn.execute("SELECT DISTINCT target_draw_no FROM lotto_predictions").fetchall()
    }
    review_draws = {
        int(r[0])
        for r in conn.execute("SELECT DISTINCT draw_no FROM testlotto_brain_review").fetchall()
    }
    pred_not_review = sorted(pred_draws - review_draws)
    return {
        "pred_distinct": len(pred_draws),
        "review_distinct": len(review_draws),
        "pred_not_in_review": pred_not_review,
    }


def main() -> None:
    init_testlotto_db()
    out: dict = {"started_at": datetime.now(timezone.utc).isoformat()}

    out["step0_backup"] = verify_backup()
    logger.info("0단계 백업 OK size=%d", out["step0_backup"]["size_bytes"])

    conn = get_lotto_db()
    out["step1_before"] = snapshot_predictions(conn)
    conn.close()
    logger.info("1단계 스냅샷 rows=%d", out["step1_before"]["total_rows"])

    out["step2_dynamic"] = measure_dynamic_stat_1132_1231()
    avg = out["step2_dynamic"]["stat_avg_match"]
    logger.info("2단계 동적경로 avg=%.4f", avg)
    if avg <= 1.6:
        out_path = ROOT / "backups/20260725_예측재기록_aborted.json"
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(f"2단계 중단: avg={avg} <= 1.6")

    conn = get_lotto_db()
    deleted_before, deleted_after = delete_predictions(conn)
    out["step3_delete"] = {"deleted_rows": deleted_before, "remaining": deleted_after}
    conn.close()
    logger.info("3단계 DELETE %d rows", deleted_before)

    LOG_PATH.write_text(f"=== 재기록 시작 {out['started_at']} ===\n", encoding="utf-8")
    draw_list = out["step1_before"]["draw_list"]
    out["step4_logs"] = rerun_predictions(draw_list)
    logger.info("4단계 재기록 완료 %d draws", len(draw_list))

    conn = get_lotto_db()
    out["step5_after"] = snapshot_predictions(conn)
    out["step5_alignment"] = review_alignment(conn)
    out["step5_stat_1232"] = stat_sets_for_draw(1232)
    conn.close()

    out["finished_at"] = datetime.now(timezone.utc).isoformat()
    result_path = ROOT / "backups/20260725_예측재기록_result.json"
    result_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(
        {
            "step2_avg": avg,
            "step3_deleted": deleted_before,
            "before_rows": out["step1_before"]["total_rows"],
            "after_rows": out["step5_after"]["total_rows"],
            "stat_1232": out["step5_stat_1232"],
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
