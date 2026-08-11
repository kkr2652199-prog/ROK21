"""심판관 파사드 — 뇌별 독립 감독관 엔진으로 위임 (K-REFEREE-BY-BRAIN).

[명분] 미정의 · 추첨 생성 전제 아님(메타정책) · 출처 K-T/K-M/K-N/K-J
※ 삭제·비활성 금지. UI 명분 노출은 별도 승인.
"""

from __future__ import annotations

from app.testlotto.learn_state import (
    get_referee_independent_scores,
    get_referee_weights,
    load_learn_state,
)


def get_predict_brain_weights() -> dict[str, float]:
    """K-J: 발권 quota SSOT = live get_referee_weights()."""
    return get_referee_weights()


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    """뇌별 독립 감독 점수 0~1.

    구버전은 3뇌 정규화 가중을 써 타뇌 성적에 점수가 묶였다.
    지금은 해당 뇌 learn_state 만으로 set_score 계산.
    """
    try:
        if not brain_tag:
            return 0.5
        from app.testlotto.brains.shared.referee_by_brain import get_engine

        state = load_learn_state(brain_tag)
        return get_engine(brain_tag).set_score_from_avg(
            float(state.get("recent_avg_match", 0) or 0),
            review_count=int(state.get("review_count", 0) or 0),
        )
    except Exception:
        return 0.5


def describe(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> str:
    try:
        indep = get_referee_independent_scores()
        if brain_tag and brain_tag in indep:
            from app.testlotto.brains.shared.referee_by_brain import get_engine

            eng = get_engine(brain_tag)
            d = indep[brain_tag]
            return eng.describe_line(
                d["recent_avg_match"], review_count=int(d["review_count"])
            )
        parts = [
            f"{k}:{indep[k]['set_score']:.2f}"
            for k in sorted(indep)
        ]
        return f"심판관(독립): {' '.join(parts)}"
    except Exception:
        w = get_predict_brain_weights()
        parts = [f"{k}:{v:.2f}" for k, v in sorted(w.items())]
        return f"심판관:가중치 {' '.join(parts)}"
