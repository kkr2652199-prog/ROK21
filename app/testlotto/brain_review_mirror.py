# -*- coding: utf-8 -*-
"""brain_review 미러 — live/click 피드백 → CUTOFF SSOT (LIST_V3 L9b)."""
from __future__ import annotations

import json
import logging
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db

logger = logging.getLogger(__name__)


def invalidate_learn_cutoff_cache() -> None:
    from app.testlotto import learn_state_cutoff as cut

    cut._history_cache = None


def upsert_brain_review_feedback(
    draw_no: int,
    brain_tag: str,
    *,
    predicted_nums: list[int],
    matched_count: int,
    missed: list[str],
    predicted_sets: list[Any] | None = None,
    best_set_no: int = 1,
    bonus_matched: int = 0,
    source: str = "live_feedback",
) -> str:
    """testlotto_brain_review UPSERT · CUTOFF 재생 소스와 동일 grain."""
    init_testlotto_db()
    dno = int(draw_no)
    tag = str(brain_tag)
    nums = [int(x) for x in predicted_nums]
    best = int(best_set_no)
    if predicted_sets:
        try:
            for s in predicted_sets:
                if int(s.get("set_no", 0) or 0) == best and s.get("nums"):
                    nums = [int(x) for x in s["nums"]]
                    break
        except Exception:
            pass
    sets_json = (
        json.dumps(predicted_sets, ensure_ascii=False)
        if predicted_sets is not None
        else json.dumps([{"set_no": best, "nums": nums}], ensure_ascii=False)
    )
    feedback = {
        "source": source,
        "matched_count": int(matched_count),
        "missed": list(missed),
    }
    conn = get_lotto_db()
    try:
        conn.execute(
            """
            INSERT INTO testlotto_brain_review (
                draw_no, brain_tag, predicted_nums, predicted_sets_json, best_set_no,
                matched_count, bonus_matched, missed_patterns, feedback_json, weight_snapshot
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(draw_no, brain_tag) DO UPDATE SET
                predicted_nums=excluded.predicted_nums,
                predicted_sets_json=COALESCE(excluded.predicted_sets_json, predicted_sets_json),
                best_set_no=excluded.best_set_no,
                matched_count=excluded.matched_count,
                bonus_matched=excluded.bonus_matched,
                missed_patterns=excluded.missed_patterns,
                feedback_json=excluded.feedback_json,
                created_at=datetime('now','localtime')
            """,
            (
                dno,
                tag,
                json.dumps(nums, ensure_ascii=False),
                sets_json,
                int(best_set_no),
                int(matched_count),
                int(bonus_matched),
                json.dumps(list(missed), ensure_ascii=False),
                json.dumps(feedback, ensure_ascii=False),
                json.dumps({"source": source}, ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    invalidate_learn_cutoff_cache()
    logger.info(
        "[L9b-REVIEW-MIRROR] upsert draw=%s brain=%s match=%s source=%s",
        dno,
        tag,
        matched_count,
        source,
    )
    return "upserted"
