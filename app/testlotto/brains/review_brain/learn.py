"""review_brain.learn — 복습뇌 학습 상태 로드·조정."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_adjustments() -> dict[str, Any]:
    """learn_state('review') 전체 반환."""
    try:
        from app.testlotto.learn_state import load_learn_state

        return load_learn_state("review")
    except Exception as e:  # noqa: BLE001
        logger.debug("review learn_state 로드 스킵: %s", e)
        return {}
