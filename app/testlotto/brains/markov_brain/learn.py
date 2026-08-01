"""markov_brain.learn — 마르코프뇌 학습 상태 로드·조정."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_adjustments() -> dict[str, Any]:
    """learn_state('markov') adjustments·miss_counts 반환."""
    from app.testlotto.learn_state import load_learn_state

    learn = load_learn_state("markov")
    return {
        "adjustments": learn.get("adjustments") or {},
        "miss_counts": learn.get("miss_counts") or {},
    }
