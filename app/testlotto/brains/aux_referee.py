"""심판관 — 최근 성적 좋은 예측뇌에 가중치 배분.

[명분] 미정의 · 추첨 생성 전제 아님(메타정책) · 출처 K-T/K-M/K-N
※ 삭제·비활성 금지. UI 명분 노출은 별도 승인.
"""

from __future__ import annotations

from app.testlotto.learn_state import get_referee_weights


def get_predict_brain_weights() -> dict[str, float]:
    """K-J: 발권 가중 SSOT = live get_referee_weights()."""
    return get_referee_weights()


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    """K-HIGHWAY-REFEREE: brain_tag별 recent_avg_match 기반 심판 가중 → 0~1 점수."""
    try:
        if not brain_tag:
            return 0.5
        referee_weights = get_referee_weights()
        normalized_weight = referee_weights.get(brain_tag, 1.0 / 3.0)
        return min(1.0, max(0.0, 0.5 + (normalized_weight - 1.0 / 3.0) * 1.5))
    except Exception:
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
