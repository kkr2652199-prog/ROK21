"""shared.referee — 뇌별 독립 감독관 디스패치 (K-REFEREE-BY-BRAIN).

각 예측뇌 `*_brain/referee.py` 엔진이 SSOT.
quota 정규화 가중만 learn_state.get_referee_weights() (뇌별 raw→Σ1).
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
