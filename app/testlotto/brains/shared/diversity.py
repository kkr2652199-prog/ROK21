"""shared.diversity — 세트 다양성 선별."""

from __future__ import annotations

from typing import Any

from app.testlotto.set_diversity import diversify_pick, oversample_factor


def pick(
    candidates: list[dict[str, Any]],
    k: int,
    *,
    jaccard_penalty: float = 0.85,
    conf_key: str = "confidence",
) -> list[dict[str, Any]]:
    """confidence - penalty*avg_jaccard_to_picked 로 탐욕 선택."""
    return diversify_pick(
        candidates,
        k,
        jaccard_penalty=jaccard_penalty,
        conf_key=conf_key,
    )


def factor(n_sets: int) -> int:
    """최종 n_sets를 위해 요청할 후보 배수."""
    return oversample_factor(n_sets)
