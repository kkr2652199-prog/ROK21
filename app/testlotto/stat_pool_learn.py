# -*- coding: utf-8 -*-
"""stat 1~5 풀 확정 → brain_review 미러 (CUTOFF 재생 소스).

발권 없이도 과거학습 가중(overdue/ending/carry, 상한 동결)이
다음 회차 expand 에 들어가게 한다. 타뇌 미기록.
적중 mean 게이트 아님. 롤백: STAT_POOL_LEARN_WIRE=False.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

STAT_POOL_LEARN_WIRE: bool = True
TAG = "stat"


def write_stat_pool_learn(
    draw_no: int,
    skill_sets: list[dict[str, Any]],
    actual: set[int],
    bonus: int,
    draws_before: list[dict],
    *,
    note: str = "stat_pool_learn",
) -> dict[str, Any]:
    """skill 1~5 mean 매치 + 오답태그 → brain_review UPSERT · CUTOFF 캐시 무효."""
    if not STAT_POOL_LEARN_WIRE:
        return {"ok": True, "skipped": True, "wire": False}
    from app.testlotto.brains.coordinator import (
        FEEDBACK_MATCH_MODE,
        _detect_missed_patterns,
    )
    from app.testlotto.brain_review_mirror import (
        invalidate_learn_cutoff_cache,
        upsert_brain_review_feedback,
    )
    from app.testlotto.tier_utils import score_predicted_set

    dno = int(draw_no)
    scored: list[tuple[int, list[int], int, int]] = []
    for s in skill_sets or []:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) != 6:
            continue
        sc = score_predicted_set(nums, sorted(actual), bonus)
        sn = int(s.get("set_no") or s.get("pred_set_no") or 0)
        scored.append(
            (int(sc["matched_count"]), nums, sn, int(sc.get("bonus_matched") or 0))
        )
    if not scored:
        return {"ok": False, "error": "no_skill_sets", "draw_no": dno}

    if FEEDBACK_MATCH_MODE == "best":
        pick = max(scored, key=lambda x: (x[0], -x[2]))
        matched = int(pick[0])
        pred_nums = pick[1]
        best_sn = pick[2]
        bonus_m = pick[3]
    else:
        mean_mc = sum(x[0] for x in scored) / len(scored)
        matched = int(round(mean_mc))
        pick = min(scored, key=lambda x: (abs(x[0] - mean_mc), -x[0]))
        pred_nums = pick[1]
        best_sn = pick[2]
        bonus_m = pick[3]

    missed = _detect_missed_patterns(pred_nums, sorted(actual), draws_before)
    sets_payload = [
        {"set_no": sn, "nums": nums, "matched": mc}
        for mc, nums, sn, _bm in scored
    ]
    st = upsert_brain_review_feedback(
        dno,
        TAG,
        predicted_nums=pred_nums,
        matched_count=matched,
        missed=missed,
        predicted_sets=sets_payload,
        best_set_no=best_sn,
        bonus_matched=bonus_m,
        source=note,
    )
    invalidate_learn_cutoff_cache()
    logger.info(
        "[STAT-POOL-LEARN] draw=%s match=%s missed=%s review=%s",
        dno,
        matched,
        missed,
        st,
    )
    return {
        "ok": True,
        "draw_no": dno,
        "matched_count": matched,
        "missed": missed,
        "best_set_no": best_sn,
        "review": st,
        "n_sets": len(scored),
    }
