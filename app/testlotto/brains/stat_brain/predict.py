"""stat_brain.predict — 통계뇌 단일 진입점."""

from __future__ import annotations

from app.testlotto.brains import aux_balance_keeper
from app.testlotto.brains.shared import diversity
from app.testlotto.brains.shared.aux_hint import rerank_by_aux
from app.testlotto.brains.stat_brain import engine, learn, transition_v1
from app.testlotto.features.draw_features import build_number_gaps, carry_over_from_prev

HINT_WEIGHT = 0.15  # PHASE5 · bench can monkeypatch to 0 / 0.10


def run(draws: list[dict], n_sets: int = 5) -> list[dict]:
    """stat 슬롯 진입점.

    K-TRANSITION-STEP4: TRANSITION_V1_WIRE(기본 ON) 시 전이 풀 우선.
    실패/롤백(K_STAT_TRANSITION_V1=0) 시 기존 engine.generate.
    """
    raw_n = diversity.factor(n_sets)
    used_transition = False
    base: list[dict] | None = None
    if transition_v1._use_transition_v1():
        base = transition_v1.generate(draws, raw_n)
        used_transition = base is not None
    if not base:
        base = engine.generate(draws, raw_n)
        used_transition = False
    target_draw_no = int(draws[-1]["draw_no"]) + 1 if draws else 0
    base = rerank_by_aux(
        base, draws, target_draw_no, aux_balance_keeper, "stat", hint_weight=HINT_WEIGHT
    )
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
        if used_transition and str(r.get("method", "")).startswith("전이"):
            reasoning = str(r.get("reasoning", "전이패턴v1")) + learn_note
            method = "전이패턴v1"
        else:
            reasoning = (
                f"통계요정: 빈도가중+끝수{endings}"
                f"+이월{len(carry)}개{carry if carry else ''}"
                f"+미출30+{overdue if overdue else '없음'}"
                f"{learn_note}"
            )
            method = "통계요정"
        tagged.append(
            {
                "nums": sorted(nums),
                "confidence": conf,
                "native_confidence": conf,
                "aux_hint_score": float(r.get("aux_hint_score", 0.5)),
                "reasoning": reasoning,
                "method": method,
                "brain_tag": "stat",
                "rank": i + 1,
            }
        )
    return diversity.pick(tagged, n_sets)


predict_sets = run  # coordinator 호환 어댑터 (PHASE4)
