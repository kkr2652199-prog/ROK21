# -*- coding: utf-8 -*-
"""K-KK-FEEDBACK-WIRE — 클릭/수집 경로용 회차 결과 → learn_state 피드백.

coordinator._auto_feedback 와 동일 의미(직전 회차 채점)를 routes에서도
명시 호출할 수 있게 한다. weight_applied Phase1=0.0 불변.
ticket/predictions 테이블은 쓰지 않는다.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db

logger = logging.getLogger(__name__)

BRAIN_TAGS = ("stat", "markov", "review")
FEEDBACK_NOTE_TAG = "K-KK-FEEDBACK"
WEIGHT_APPLIED = 0.0  # Phase1 고정 · K-M 범위 밖


def _actual_nums(conn, draw_no: int) -> list[int] | None:
    row = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?",
        (int(draw_no),),
    ).fetchone()
    if not row:
        return None
    return [int(row[f"num{k}"]) for k in range(1, 7)]


def _evolve_has_feedback_mark(conn, draw_no: int, brain_tag: str) -> bool:
    row = conn.execute(
        "SELECT note FROM testlotto_evolve_log WHERE draw_no=? AND brain_tag=?",
        (int(draw_no), brain_tag),
    ).fetchone()
    if not row:
        return False
    note = str(row["note"] or "")
    return FEEDBACK_NOTE_TAG in note


def _mark_evolve_feedback(
    conn,
    draw_no: int,
    brain_tag: str,
    *,
    actual_nums: list[int],
    matched_count: int,
    missed: list[str],
) -> str:
    """evolve_log에 feedback 기록. 기존 행이면 note만 갱신 · 없으면 최소 INSERT."""
    from app.testlotto.evolve_log import WEIGHT_APPLIED as EV_W, ensure_evolve_log_table

    ensure_evolve_log_table(conn)
    assert float(EV_W) == 0.0
    note_bit = (
        f"{FEEDBACK_NOTE_TAG} · as_of={draw_no} · match={matched_count} "
        f"· missed={missed} · weight={WEIGHT_APPLIED}"
    )
    existing = conn.execute(
        "SELECT note, weight_applied FROM testlotto_evolve_log "
        "WHERE draw_no=? AND brain_tag=?",
        (int(draw_no), brain_tag),
    ).fetchone()
    if existing:
        old = str(existing["note"] or "")
        if FEEDBACK_NOTE_TAG in old:
            return "already_marked"
        new_note = (old + " | " + note_bit).strip(" |")
        conn.execute(
            """
            UPDATE testlotto_evolve_log
            SET note=?,
                weight_applied=?,
                miss_tags_json=?,
                updated_at=datetime('now','localtime')
            WHERE draw_no=? AND brain_tag=?
            """,
            (
                new_note,
                WEIGHT_APPLIED,
                json.dumps(missed, ensure_ascii=False),
                int(draw_no),
                brain_tag,
            ),
        )
        return "updated"
    # 최소 INSERT (pool/repack 빈 배열 · Phase1 weight=0)
    conn.execute(
        """
        INSERT INTO testlotto_evolve_log (
            draw_no, brain_tag, as_of, schema_version, weight_applied,
            actual_nums_json, pool_json, repack_json,
            pool_hits_json, repack_hits_json,
            best_hits, mean_hits, best_set_kind, best_set_no,
            features_json, miss_tags_json, assemble_mode, note
        ) VALUES (
            ?,?,?,1,?,
            ?,'[]','[]',
            '[]','[]',
            ?,?,?,?,
            ?,?,?,?
        )
        """,
        (
            int(draw_no),
            brain_tag,
            int(draw_no),
            WEIGHT_APPLIED,
            json.dumps(actual_nums),
            int(matched_count),
            float(matched_count),
            "feedback",
            None,
            json.dumps({"weight_applied": WEIGHT_APPLIED, "source": FEEDBACK_NOTE_TAG}),
            json.dumps(missed, ensure_ascii=False),
            "click_feedback",
            note_bit,
        ),
    )
    return "inserted"


def apply_draw_result_feedback(draw_no: int) -> dict[str, Any]:
    """회차 결과가 DB에 있으면 3뇌에 apply_feedback + evolve_log 마크.

    guard_future: lotto_draws 없으면 SKIP
    guard_duplicate: evolve_log note에 K-KK-FEEDBACK 있으면 해당 뇌 SKIP
    learn 중복: last_draw_no >= draw_no 이면 apply_feedback 생략(마크만)
    """
    from app.testlotto.brains.coordinator import (
        FEEDBACK_MATCH_MODE,
        PREDICT_TAGS,
        _detect_missed_patterns,
        _prediction_row_nums,
    )
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state import _load_global_learn_state, apply_feedback

    init_testlotto_db()
    dno = int(draw_no)
    out: dict[str, Any] = {
        "draw_no": dno,
        "ok": False,
        "skipped": None,
        "brains": {},
    }

    # 읽기만 — apply_feedback 이 별도 커넥션을 쓰므로 잠금 방지 위해 먼저 닫음
    conn = get_lotto_db()
    try:
        actual_nums = _actual_nums(conn, dno)
        if actual_nums is None:
            out["skipped"] = "guard_future_no_draw"
            return out
        pred_rows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM lotto_predictions WHERE target_draw_no=?",
                (dno,),
            ).fetchall()
        ]
        marked = {
            tag: _evolve_has_feedback_mark(conn, dno, tag) for tag in BRAIN_TAGS
        }
    finally:
        conn.close()

    if not pred_rows:
        out["skipped"] = "no_predictions"
        return out

    actual_set = set(actual_nums)
    draws_before = _get_draws_before(dno)
    by_brain: dict[str, list[dict]] = {}
    for row in pred_rows:
        tag = str(row.get("brain_tag") or "")
        if tag not in PREDICT_TAGS:
            continue
        by_brain.setdefault(tag, []).append(row)

    any_work = False
    for tag in BRAIN_TAGS:
        rows = by_brain.get(tag) or []
        if not rows:
            out["brains"][tag] = {"status": "no_brain_preds"}
            continue
        if marked.get(tag):
            out["brains"][tag] = {"status": "skip_duplicate_evolve"}
            continue

        scored: list[tuple[int, list[int], dict]] = []
        for row in rows:
            pred_nums = _prediction_row_nums(row)
            mc = len(set(pred_nums) & actual_set)
            if int(row.get("matched_count") or -1) >= 0:
                mc = int(row["matched_count"])
            scored.append((mc, pred_nums, row))

        if FEEDBACK_MATCH_MODE == "best":
            pick = max(
                scored, key=lambda s: (s[0], float(s[2].get("confidence") or 0))
            )
            matched_count = int(pick[0])
            pred_nums = pick[1]
        else:
            mean_mc = sum(s[0] for s in scored) / len(scored)
            matched_count = int(round(mean_mc))
            pred_nums = min(scored, key=lambda s: (abs(s[0] - mean_mc), -s[0]))[1]

        missed = _detect_missed_patterns(pred_nums, actual_nums, draws_before)
        state = _load_global_learn_state(tag)
        last = int(state.get("last_draw_no", 0) or 0)
        learn_applied = False
        if last < dno:
            apply_feedback(tag, dno, matched_count, missed)
            learn_applied = True

        conn_w = get_lotto_db()
        try:
            mark = _mark_evolve_feedback(
                conn_w,
                dno,
                tag,
                actual_nums=actual_nums,
                matched_count=matched_count,
                missed=missed,
            )
            conn_w.commit()
        finally:
            conn_w.close()

        any_work = True
        out["brains"][tag] = {
            "status": "ok",
            "learn_applied": learn_applied,
            "evolve_mark": mark,
            "matched_count": matched_count,
            "missed": missed,
            "weight_applied": WEIGHT_APPLIED,
        }
        logger.info(
            "[K-KK-FEEDBACK] %s draw=%d learn=%s evolve=%s match=%d",
            tag,
            dno,
            learn_applied,
            mark,
            matched_count,
        )

    out["ok"] = True
    if not any_work and not out.get("skipped"):
        out["skipped"] = "all_brains_duplicate_or_empty"
    return out


def apply_feedback_after_predict(target_draw_no: int) -> dict[str, Any]:
    """클릭 발권(target) 직후 → 직전 회차(target-1) 결과 피드백."""
    prev = int(target_draw_no) - 1
    if prev < 1:
        return {"draw_no": prev, "ok": False, "skipped": "no_prev"}
    return apply_draw_result_feedback(prev)
