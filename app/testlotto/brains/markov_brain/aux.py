"""markov_brain.aux — pattern 전용 보조."""

from __future__ import annotations

from app.testlotto.brains import aux_pattern_spotlight


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = "markov",
) -> float:
    """aux_pattern_spotlight.score_set 래핑."""
    return aux_pattern_spotlight.score_set(
        nums, draws, target_draw_no, brain_tag=brain_tag
    )


def describe(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = "markov",
) -> str:
    """aux_pattern_spotlight.describe 래핑."""
    return aux_pattern_spotlight.describe(
        nums, draws, target_draw_no, brain_tag=brain_tag
    )
