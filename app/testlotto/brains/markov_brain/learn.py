"""markov_brain.learn — 마르코프뇌 학습 상태 로드·조정."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

LEARN_WIRED = True  # bench sets False for baseline A


def get_adjustments() -> dict[str, Any]:
    """learn_state('markov') adjustments·miss_counts 반환."""
    from app.testlotto.learn_state import load_learn_state

    learn = load_learn_state("markov")
    return {
        "adjustments": learn.get("adjustments") or {},
        "miss_counts": learn.get("miss_counts") or {},
    }


def apply_learn_boost(
    visit_count: dict[int, float],
    draws: list[dict],
) -> dict[int, float]:
    """learn_state adjustments → visit_count (walk-forward load_learn_state)."""
    try:
        from app.testlotto.learn_state import BOOST_CAPS, load_learn_state

        learn = load_learn_state("markov")
        adj = learn.get("adjustments") or {}
        miss_counts = learn.get("miss_counts") or {}

        latest_draw_no = int(draws[-1]["draw_no"]) if draws else 0
        last_seen: dict[int, int] = {}
        for d in draws:
            for k in range(1, 7):
                n = int(d[f"num{k}"])
                last_seen[n] = int(d["draw_no"])
        for n in range(1, 46):
            if n not in last_seen:
                last_seen[n] = 0

        overdue_b = min(
            float(adj.get("overdue_boost", 0) or 0),
            BOOST_CAPS["overdue_boost"],
        )
        if overdue_b > 0:
            for n in range(1, 46):
                gap = latest_draw_no - last_seen[n]
                if gap >= 30:
                    visit_count[n] *= 1.0 + overdue_b

        ending_b = min(
            float(adj.get("ending_digit_boost", 0) or 0),
            BOOST_CAPS["ending_digit_boost"],
        )
        if ending_b > 0 and int(miss_counts.get("ending_digit", 0) or 0) > 0 and draws:
            prev_endings = {int(draws[-1][f"num{k}"]) % 10 for k in range(1, 7)}
            for n in range(1, 46):
                if n % 10 in prev_endings:
                    visit_count[n] *= 1.0 + ending_b

        carry_b = min(
            float(adj.get("carry_over_boost", 0) or 0),
            BOOST_CAPS["carry_over_boost"],
        )
        if carry_b > 0 and draws:
            prev_nums = [int(draws[-1][f"num{k}"]) for k in range(1, 7)]
            for n in prev_nums:
                if n in visit_count:
                    visit_count[n] *= 1.0 + carry_b

        pair_b = min(
            float(adj.get("pair_boost", 0) or 0),
            BOOST_CAPS["pair_boost"],
        )
        if pair_b > 0 and int(miss_counts.get("pair", 0) or 0) > 0 and draws:
            from app.testlotto.features.draw_features import build_pair_freq

            pair_freq = build_pair_freq(draws)
            top_pairs = sorted(pair_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            boost_nums: set[int] = set()
            for (a, b), _ in top_pairs:
                boost_nums.add(a)
                boost_nums.add(b)
            for n in boost_nums:
                if n in visit_count:
                    visit_count[n] *= 1.0 + pair_b
    except Exception as e:
        logger.debug("learn_state markov 배선 스킵: %s", e)

    return visit_count
