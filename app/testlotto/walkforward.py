"""walk-forward 복습 루프 — 1회차부터 순차 예측→채점→오답분석→피드백."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.testlotto.brains.coordinator import (
    FEEDBACK_MATCH_MODE,
    PREDICT_MODULES,
    apply_coordinator_scoring,
)
from app.testlotto.brains.registry import PREDICT_BRAINS, SETS_PER_PREDICT_BRAIN
from app.testlotto.aux_analysis import build_brain_aux_json
from app.testlotto.data_service import _get_draws_before
from app.testlotto.draw_analysis import detect_missed_patterns, upsert_draw_features
from app.testlotto.detail_service import upsert_brain_page_from_review
from app.testlotto.learn_state import apply_feedback, get_all_learn_states, reset_learn_states
from app.testlotto.tier_utils import pick_best_set_index, score_predicted_set
from app.testlotto.models import get_lotto_db, init_testlotto_db

logger = logging.getLogger(__name__)


def _get_actual(draw_no: int) -> dict | None:
    conn = get_lotto_db()
    try:
        row = conn.execute("SELECT * FROM lotto_draws WHERE draw_no = ?", (draw_no,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _actual_nums(actual: dict) -> list[int]:
    return sorted(int(actual[f"num{k}"]) for k in range(1, 7))


def _score_sets(
    sets: list[dict[str, Any]],
    actual_set: set[int],
    actual_list: list[int],
    bonus: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    """5세트 각각 채점(보너스·등수 포함) → 등수 우선 best 세트."""
    scored: list[dict[str, Any]] = []
    for i, s in enumerate(sets):
        nums = list(s.get("nums") or [])
        tier_info = score_predicted_set(nums, actual_list, bonus)
        entry = {
            "set_no": i + 1,
            "nums": nums,
            "confidence": float(s.get("confidence") or 0),
            "reasoning": s.get("reasoning") or "",
            **tier_info,
        }
        scored.append(entry)
    best_idx = pick_best_set_index(scored)
    best = scored[best_idx] if scored else {
        "set_no": 1,
        "nums": [],
        "matched_count": 0,
        "bonus_matched": 0,
        "tier_rank": 0,
        "tier_label": "미적중",
    }
    return scored, best, best_idx + 1


def _learn_match_from_sets(
    scored_sets: list[dict[str, Any]],
) -> tuple[int, list[int], int]:
    """K-N: 학습 입력 = 뇌내 세트 mean (best 단독 금지).

    Returns: (learn_matched, learn_nums, learn_set_no)
    FEEDBACK_MATCH_MODE=='best' 일 때만 구경로(비권고).
    """
    if not scored_sets:
        return 0, [], 0
    if FEEDBACK_MATCH_MODE == "best":
        best_idx = pick_best_set_index(scored_sets)
        best = scored_sets[best_idx]
        return (
            int(best.get("matched_count") or 0),
            list(best.get("nums") or []),
            int(best.get("set_no") or best_idx + 1),
        )
    hits = [int(s.get("matched_count") or 0) for s in scored_sets]
    mean_mc = sum(hits) / len(hits)
    learn_matched = int(round(mean_mc))
    # miss 태그용 세트 = mean에 가장 가까운 세트 (동점 시 hits 큰 쪽)
    pick = min(
        scored_sets,
        key=lambda s: (
            abs(int(s.get("matched_count") or 0) - mean_mc),
            -int(s.get("matched_count") or 0),
        ),
    )
    return (
        learn_matched,
        list(pick.get("nums") or []),
        int(pick.get("set_no") or 0),
    )


def review_single_draw(draw_no: int, *, store_features: bool = True) -> dict[str, Any]:
    """한 회차 복습: 3예측뇌 각 5세트 → 표시용 best + 학습용 mean → 피드백.

    K-N: apply_feedback 입력은 mean (고분산 best 오인 차단).
    best/tier는 표시·리뷰 테이블 참고용으로만 유지.
    """
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    draws = _get_draws_before(draw_no)
    if not draws:
        return {"draw_no": draw_no, "skipped": True, "reason": "이전 회차 없음"}

    actual = _get_actual(draw_no)
    if not actual:
        return {"draw_no": draw_no, "skipped": True, "reason": "정답 미확정"}

    # 예측 시점 학습: draw_no 미만만 (CUTOFF 기본 ON)
    set_learn_as_of(int(draw_no))

    actual_list = _actual_nums(actual)
    actual_set = set(actual_list)
    bonus = int(actual.get("bonus") or 0)
    results: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []

    for brain in PREDICT_BRAINS:
        tag = brain["tag"]
        mod = PREDICT_MODULES[tag]
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        if not sets:
            results.append({"brain_tag": tag, "skipped": True})
            continue
        # K-PIPE-A: live coordinator와 동일 AUX·referee confidence (best는 tier 표시용)
        sets = apply_coordinator_scoring(sets, draws, draw_no)
        scored_sets, best, best_set_no = _score_sets(sets, actual_set, actual_list, bonus)
        learn_matched, learn_nums, learn_set_no = _learn_match_from_sets(scored_sets)
        missed = detect_missed_patterns(learn_nums, actual_list, draws)
        pending.append(
            {
                "brain": brain,
                "tag": tag,
                "nums": learn_nums,
                "matched": learn_matched,
                "best_matched": int(best["matched_count"]),
                "bonus_matched": int(best.get("bonus_matched") or 0),
                "tier_rank": int(best.get("tier_rank") or 0),
                "tier_label": best.get("tier_label") or "미적중",
                "missed": missed,
                "predicted_sets": scored_sets,
                "best_set_no": best_set_no,
                "learn_set_no": learn_set_no,
                "feedback_mode": FEEDBACK_MATCH_MODE,
            }
        )

    for item in pending:
        item["state"] = apply_feedback(
            item["tag"], draw_no, item["matched"], item["missed"]
        )

    conn = get_lotto_db()
    try:
        for item in pending:
            tag = item["tag"]
            brain = item["brain"]
            matched = item["matched"]
            missed = item["missed"]
            nums = item["nums"]
            state = item["state"]
            feedback = {
                "missed_patterns": missed,
                "adjustments": state.get("adjustments", {}),
                "recent_avg_match": state.get("recent_avg_match", 0),
                "feedback_mode": item.get("feedback_mode") or FEEDBACK_MATCH_MODE,
                "mean_matched": matched,
                "best_matched": int(item.get("best_matched") or 0),
                "learn_set_no": int(item.get("learn_set_no") or 0),
            }
            weight_snap = get_all_learn_states()
            conn.execute(
                """
                INSERT INTO testlotto_brain_review (
                    draw_no, brain_tag, predicted_nums, predicted_sets_json, best_set_no,
                    matched_count, bonus_matched, missed_patterns, feedback_json, weight_snapshot
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(draw_no, brain_tag) DO UPDATE SET
                    predicted_nums=excluded.predicted_nums,
                    predicted_sets_json=excluded.predicted_sets_json,
                    best_set_no=excluded.best_set_no,
                    matched_count=excluded.matched_count,
                    bonus_matched=excluded.bonus_matched,
                    missed_patterns=excluded.missed_patterns,
                    feedback_json=excluded.feedback_json,
                    weight_snapshot=excluded.weight_snapshot,
                    created_at=datetime('now','localtime')
                """,
                (
                    draw_no,
                    tag,
                    json.dumps(nums, ensure_ascii=False),
                    json.dumps(item["predicted_sets"], ensure_ascii=False),
                    int(item["best_set_no"]),
                    matched,
                    int(item.get("bonus_matched") or 0),
                    json.dumps(missed, ensure_ascii=False),
                    json.dumps(feedback, ensure_ascii=False),
                    json.dumps(weight_snap, ensure_ascii=False),
                ),
            )
            results.append(
                {
                    "brain_tag": tag,
                    "brain_name": brain["name"],
                    "matched_count": matched,
                    "best_matched": int(item.get("best_matched") or 0),
                    "feedback_mode": item.get("feedback_mode") or FEEDBACK_MATCH_MODE,
                    "bonus_matched": int(item.get("bonus_matched") or 0),
                    "tier_rank": int(item.get("tier_rank") or 0),
                    "tier_label": item.get("tier_label") or "미적중",
                    "best_set_no": item["best_set_no"],
                    "learn_set_no": int(item.get("learn_set_no") or 0),
                    "sets_count": len(item["predicted_sets"]),
                    "missed_patterns": missed,
                    "predicted": nums,
                    "predicted_sets": item["predicted_sets"],
                }
            )
        conn.commit()
    finally:
        conn.close()

    feature_row = None
    if store_features:
        feature_row = upsert_draw_features(draw_no)

    for item in pending:
        tag = item["tag"]
        state = item["state"]
        feedback = {
            "missed_patterns": item["missed"],
            "adjustments": state.get("adjustments", {}),
            "recent_avg_match": state.get("recent_avg_match", 0),
        }
        upsert_brain_page_from_review(
            draw_no,
            tag,
            predicted=item["nums"],
            predicted_sets=item["predicted_sets"],
            best_set_no=item["best_set_no"],
            actual=actual_list,
            matched_count=item["matched"],
            bonus_matched=int(item.get("bonus_matched") or 0),
            tier_rank=int(item.get("tier_rank") or 0),
            tier_label=item.get("tier_label") or "미적중",
            missed_patterns=item["missed"],
            feedback=feedback,
            weight_snapshot=get_all_learn_states(),
            feature_row=feature_row,
            aux_analysis_json=build_brain_aux_json(item["nums"], draws, draw_no),
        )

    from app.testlotto.learn_state_cutoff import clear_history_cache

    clear_history_cache()
    return {"draw_no": draw_no, "reviews": results, "feature_stored": store_features}


def run_review_loop(
    start_draw: int = 2,
    end_draw: int = 1231,
    *,
    progress_every: int = 50,
) -> dict[str, Any]:
    """start~end 회차 순차 복습 (기본 2~1231: 1회 정답은 예측 불가)."""
    init_testlotto_db()
    done = 0
    skipped = 0
    last_sample: dict | None = None

    for draw_no in range(start_draw, end_draw + 1):
        out = review_single_draw(draw_no)
        if out.get("skipped"):
            skipped += 1
        else:
            done += 1
            last_sample = out
        if progress_every and draw_no % progress_every == 0:
            logger.info("[복습루프] %d회 완료 (누적 %d, 스킵 %d)", draw_no, done, skipped)

    states = get_all_learn_states()
    return {
        "start_draw": start_draw,
        "end_draw": end_draw,
        "reviewed": done,
        "skipped": skipped,
        "learn_states": states,
        "last_sample": last_sample,
    }


def run_future_after_review(
    future_draw: int = 1232,
    *,
    run_full_review_first: bool = False,
    review_end: int = 1231,
) -> dict[str, Any]:
    """1231회까지 복습 경험 쌓은 뒤 미래 회차 예측."""
    init_testlotto_db()
    review_summary = None
    if run_full_review_first:
        review_summary = run_review_loop(2, review_end)

    from app.testlotto.brains.coordinator import run_coordinated_prediction

    pred = run_coordinated_prediction(future_draw)
    return {
        "future_draw": future_draw,
        "review_summary": review_summary,
        "prediction": pred,
    }


def get_review_progress() -> dict[str, Any]:
    conn = get_lotto_db()
    try:
        row = conn.execute(
            "SELECT COUNT(DISTINCT draw_no), MAX(draw_no), MIN(draw_no) FROM testlotto_brain_review"
        ).fetchone()
        feat = conn.execute("SELECT COUNT(*) FROM testlotto_draw_features").fetchone()
        states = conn.execute(
            "SELECT brain_tag, review_count, last_draw_no FROM testlotto_brain_learn_state"
        ).fetchall()
        return {
            "review_draws": int(row[0] or 0),
            "review_max_draw": int(row[1] or 0),
            "review_min_draw": int(row[2] or 0),
            "feature_rows": int(feat[0] or 0),
            "learn_states": [dict(r) for r in states],
        }
    finally:
        conn.close()
