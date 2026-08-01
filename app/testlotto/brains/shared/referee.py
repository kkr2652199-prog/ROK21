"""shared.referee — brain_w·K-M 메타 채점 (aux_referee 래핑).

referee는 3뇌 파일에 넣지 않음 — coordinator/shared 공용.
"""

from __future__ import annotations

from app.testlotto.brains import aux_referee


def get_brain_weights() -> dict[str, float]:
    return aux_referee.get_predict_brain_weights()


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    return aux_referee.score_set(
        nums, draws, target_draw_no, brain_tag=brain_tag
    )


def describe(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> str:
    return aux_referee.describe(
        nums, draws, target_draw_no, brain_tag=brain_tag
    )
