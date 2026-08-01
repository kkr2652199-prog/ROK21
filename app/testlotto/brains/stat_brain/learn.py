"""stat_brain.learn — 통계뇌 학습 상태 로드·조정."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_adjustments() -> dict[str, Any]:
    """learn_state('stat') adjustments·miss_counts 반환."""
    from app.testlotto.learn_state import load_learn_state

    learn = load_learn_state("stat")
    return {
        "adjustments": learn.get("adjustments") or {},
        "miss_counts": learn.get("miss_counts") or {},
    }


def apply_learn_boost(
    weights: dict[int, float],
    draws: list[dict],
    last_seen: dict[int, int],
    latest_draw_no: int,
) -> dict[int, float]:
    """learn_state adjustments → weights (walk-forward load_learn_state)."""
    try:
        from app.testlotto.learn_state import BOOST_CAPS, load_learn_state

        learn = load_learn_state("stat")
        adj = learn.get("adjustments") or {}
        miss_counts = learn.get("miss_counts") or {}

        overdue_b = min(
            float(adj.get("overdue_boost", 0) or 0),
            BOOST_CAPS["overdue_boost"],
        )
        if overdue_b > 0:
            for n in range(1, 46):
                gap = latest_draw_no - last_seen[n]
                if gap >= 30:
                    weights[n] *= 1.0 + overdue_b

        ending_b = min(
            float(adj.get("ending_digit_boost", 0) or 0),
            BOOST_CAPS["ending_digit_boost"],
        )
        if ending_b > 0 and int(miss_counts.get("ending_digit", 0) or 0) > 0 and draws:
            prev_endings = {int(draws[-1][f"num{k}"]) % 10 for k in range(1, 7)}
            for n in range(1, 46):
                if n % 10 in prev_endings:
                    weights[n] *= 1.0 + ending_b

        carry_b = min(
            float(adj.get("carry_over_boost", 0) or 0),
            BOOST_CAPS["carry_over_boost"],
        )
        if carry_b > 0 and draws:
            prev_nums = [int(draws[-1][f"num{k}"]) for k in range(1, 7)]
            for n in prev_nums:
                if n in weights:
                    weights[n] *= 1.0 + carry_b

        total_w = sum(weights.values())
        if total_w > 0:
            weights = {n: weights[n] / total_w for n in range(1, 46)}
    except Exception as e:
        logger.debug("learn_state freq 배선 스킵: %s", e)

    return weights
