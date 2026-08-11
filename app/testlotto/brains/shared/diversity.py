"""shared.diversity — 세트 다양성 선별."""

from __future__ import annotations

from typing import Any

from app.testlotto.set_diversity import diversify_pick, oversample_factor

# K-POOL-JACCARD-BY-BRAIN: pool 최종선별 Jaccard 패널티 (뇌별 독립 · 기본 0.85)
JACCARD_PENALTY_BY_BRAIN: dict[str, float] = {
    "stat": 0.85,
    "markov": 0.85,
    "review": 0.85,
}

# oversample 배수 (뇌별 · 기본 3 = oversample_factor 기존식)
OVERSAMPLE_MULT_BY_BRAIN: dict[str, int] = {
    "stat": 3,
    "markov": 5,
    "review": 3,
}


def jaccard_penalty_for(brain: str) -> float:
    return float(JACCARD_PENALTY_BY_BRAIN.get(brain, 0.85))


def pick(
    candidates: list[dict[str, Any]],
    k: int,
    *,
    brain: str | None = None,
    jaccard_penalty: float | None = None,
    conf_key: str = "confidence",
) -> list[dict[str, Any]]:
    """confidence - penalty*avg_jaccard_to_picked 로 탐욕 선택."""
    pen = (
        float(jaccard_penalty)
        if jaccard_penalty is not None
        else jaccard_penalty_for(brain or "")
    )
    return diversify_pick(
        candidates,
        k,
        jaccard_penalty=pen,
        conf_key=conf_key,
    )


def factor(n_sets: int, brain: str | None = None) -> int:
    """최종 n_sets를 위해 요청할 후보 배수."""
    if brain and brain in OVERSAMPLE_MULT_BY_BRAIN:
        m = max(1, int(OVERSAMPLE_MULT_BY_BRAIN[brain]))
        return max(n_sets * m, n_sets + 5)
    return oversample_factor(n_sets)
