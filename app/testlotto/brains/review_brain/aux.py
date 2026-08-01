"""review_brain.aux — miss 전용 보조."""

from __future__ import annotations

from app.testlotto.brains import aux_miss_detective


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = "review",
) -> float:
    """aux_miss_detective.score_set 래핑."""
    return aux_miss_detective.score_set(
        nums, draws, target_draw_no, brain_tag=brain_tag
    )


def describe(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = "review",
) -> str:
    """aux_miss_detective.describe 래핑."""
    return aux_miss_detective.describe(
        nums, draws, target_draw_no, brain_tag=brain_tag
    )
