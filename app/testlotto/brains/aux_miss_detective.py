"""오답탐정 — 과거 예측 오답 패턴 페널티 (1군 feedback 벤치마킹).

[명분] 기각 · K-T 미출간격 χ² p=0.483 (기하 이탈 주장 미입증) · 출처 K-T
※ 기각이어도 제거·비활성 금지(조합불변·다양성 기여).
"""

from __future__ import annotations

from app.testlotto.features.draw_features import combo_features


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    """0~1. 과거 frequent_traps 번호 포함 시 감점."""
    feats = combo_features(nums, draws)
    penalty = 0.0
    try:
        from app.testlotto.feedback import get_feedback_summary

        # target 이전 회차만: as_of = target_draw_no - 1 (학습 as_of=target 과 정합)
        as_of = int(target_draw_no) - 1
        if draws:
            as_of = int(draws[-1]["draw_no"])
        fb = get_feedback_summary(last_n=30, as_of=as_of)
        traps = set(fb.get("frequent_traps") or [])
        hits_on_trap = sum(1 for n in nums if n in traps)
        penalty = min(0.5, hits_on_trap * 0.12)
    except Exception:
        penalty = 0.0
    base = 0.75 - penalty
    return max(0.1, min(1.0, base))


def describe(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> str:
    s = score_set(nums, draws, target_draw_no, brain_tag=brain_tag)
    return f"오답탐정:{s:.2f}"
