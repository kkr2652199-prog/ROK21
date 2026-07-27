"""심판관 — 최근 성적 좋은 예측뇌에 가중치 배분.

[명분] 미정의 · 추첨 생성 전제 아님(메타정책) · 출처 K-T/K-M/K-N
※ 삭제·비활성 금지. UI 명분 노출은 별도 승인.
"""

from __future__ import annotations

from app.testlotto.learn_state import get_referee_weights


def get_predict_brain_weights() -> dict[str, float]:
    return get_referee_weights()


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    """보조 채점 파이프라인 호환용 — 중립 기본값."""
    return 0.5


def describe(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> str:
    w = get_predict_brain_weights()
    parts = [f"{k}:{v:.2f}" for k, v in sorted(w.items())]
    return f"심판관:가중치 {' '.join(parts)}"
