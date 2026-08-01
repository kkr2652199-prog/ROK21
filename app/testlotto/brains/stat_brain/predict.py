"""stat_brain.predict — 통계뇌 단일 진입점."""

from __future__ import annotations

from app.testlotto.brains.shared import diversity
from app.testlotto.brains.stat_brain import engine, learn
from app.testlotto.features.draw_features import build_number_gaps, carry_over_from_prev


def run(draws: list[dict], n_sets: int = 5) -> list[dict]:
    """predict_stat_fairy.predict_sets 와 동치 — engine.generate + diversity.pick."""
    raw_n = diversity.factor(n_sets)
    base = engine.generate(draws, raw_n)
    prev = draws[-1] if draws else None
    gaps = build_number_gaps(draws)
    learn_data = learn.get_adjustments()
    adj = learn_data.get("adjustments", {})
    carry_boost = 1.0 + float(adj.get("carry_over_boost", 0))
    ending_boost = 1.0 + float(adj.get("ending_digit_boost", 0))
    tagged: list[dict] = []
    for i, r in enumerate(base):
        nums = sorted(r["nums"])
        carry = carry_over_from_prev(prev, nums)
        endings = sorted({n % 10 for n in nums})
        overdue = sorted([n for n in nums if gaps.get(n, 0) >= 30])
        learn_note = ""
        if adj:
            learn_note = f" [학습조정 이월×{carry_boost:.2f} 끝수×{ending_boost:.2f}]"
        conf = float(r.get("confidence", 70))
        if carry and carry_boost > 1:
            conf = min(95, conf + len(carry) * (carry_boost - 1) * 8)
        reasoning = (
            f"통계요정: 빈도가중+끝수{endings}"
            f"+이월{len(carry)}개{carry if carry else ''}"
            f"+미출30+{overdue if overdue else '없음'}"
            f"{learn_note}"
        )
        tagged.append(
            {
                "nums": sorted(nums),
                "confidence": conf,
                "reasoning": reasoning,
                "method": "통계요정",
                "brain_tag": "stat",
                "rank": i + 1,
            }
        )
    return diversity.pick(tagged, n_sets)
