# -*- coding: utf-8 -*-
"""7번 — 4·5·6 읽기 묶음. 미래장에 넣는 자리.

1·2·3 불변. 몰아주기 미접촉. random.choices 라인 동결.
지금은 모으기만. 기어 OFF면 가중·패스 불변.
자동화 시동 아님. 타깃 회 당첨 미입력.
"""
from __future__ import annotations

from typing import Any

# K-REVIEW-KB7-SLOT (20260823) — 자리만. 롤백: 이 파일 호출 제거
# 튜닝 GO 전 금지: True
REVIEW_KB7_WIRE: bool = False

_LAST_BUNDLE: dict[str, Any] | None = None


def collect_before(draws: list[dict]) -> dict[str, Any]:
    """예측 전 4·5·6을 한 묶음으로 읽음. as_of=타깃 이전."""
    global _LAST_BUNDLE
    as_of = int(draws[-1]["draw_no"]) if draws else None
    bundle: dict[str, Any] = {
        "as_of": as_of,
        "n_draws": len(draws),
        "shape": None,
        "consec": None,
        "assoc": None,
        "wire": bool(REVIEW_KB7_WIRE),
    }
    try:
        from app.testlotto.brains.review_brain.draw_shape_kb import (
            REVIEW_SHAPE_KB_READ,
            summarize_before as shape_kb,
        )

        if REVIEW_SHAPE_KB_READ:
            bundle["shape"] = shape_kb(draws)
    except Exception:  # noqa: BLE001
        pass
    try:
        from app.testlotto.brains.review_brain.rare_consec import (
            REVIEW_CONSEC_KB_READ,
            summarize_before as consec_kb,
        )

        if REVIEW_CONSEC_KB_READ:
            bundle["consec"] = consec_kb(draws)
    except Exception:  # noqa: BLE001
        pass
    try:
        from app.testlotto.brains.review_brain.draw_assoc import (
            REVIEW_ASSOC_KB_READ,
            summarize_before as assoc_kb,
        )

        if REVIEW_ASSOC_KB_READ:
            bundle["assoc"] = assoc_kb(draws)
    except Exception:  # noqa: BLE001
        pass
    _LAST_BUNDLE = bundle
    return bundle


def apply_kb7_weights(weights: dict[int, float], bundle: dict[str, Any] | None) -> dict[int, float]:
    """기어 OFF면 그대로. ON은 이후 단계 튜닝(형 GO). 보너스 링크 사용 금지."""
    del bundle
    if not REVIEW_KB7_WIRE:
        return weights
    return weights


def should_skip_kb7(nums: list[int], bundle: dict[str, Any] | None) -> bool:
    """기어 OFF면 거절 없음. ON은 이후 단계 튜닝(형 GO)."""
    del nums, bundle
    if not REVIEW_KB7_WIRE:
        return False
    return False


def last_bundle() -> dict[str, Any] | None:
    return _LAST_BUNDLE
