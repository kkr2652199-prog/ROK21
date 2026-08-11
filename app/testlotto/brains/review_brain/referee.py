# -*- coding: utf-8 -*-
"""review 전용 감독관 엔진 — 금액뇌 독립 감독."""

from __future__ import annotations

from app.testlotto.brains.shared.referee_by_brain import get_engine

ENGINE = get_engine("review")
BRAIN_TAG = ENGINE.brain_tag


def set_score_from_state(state: dict) -> float:
    return ENGINE.set_score_from_avg(
        float(state.get("recent_avg_match", 0) or 0),
        review_count=int(state.get("review_count", 0) or 0),
    )


def describe_from_state(state: dict) -> str:
    return ENGINE.describe_line(
        float(state.get("recent_avg_match", 0) or 0),
        review_count=int(state.get("review_count", 0) or 0),
    )
