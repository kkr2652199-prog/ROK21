"""stat_brain.aux — balance 전용 보조."""

from __future__ import annotations

from app.testlotto.brains import aux_balance_keeper


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = "stat",
) -> float:
    """aux_balance_keeper.score_set 래핑."""
    return aux_balance_keeper.score_set(
        nums, draws, target_draw_no, brain_tag=brain_tag
    )


def describe(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = "stat",
) -> str:
    """aux_balance_keeper.describe 래핑."""
    return aux_balance_keeper.describe(
        nums, draws, target_draw_no, brain_tag=brain_tag
    )
