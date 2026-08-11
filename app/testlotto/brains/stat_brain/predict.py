# -*- coding: utf-8 -*-
"""stat_brain.predict — 과거학습 뇌 단일 진입점 (구조 패치)."""

from __future__ import annotations

from app.testlotto.brains import aux_balance_keeper
from app.testlotto.brains.shared import diversity
from app.testlotto.brains.shared.aux_hint import HINT_WEIGHT_BY_BRAIN, rerank_by_aux
from app.testlotto.brains.stat_brain import engine, learn, past_learn, transition_v1
from app.testlotto.features.draw_features import build_number_gaps, carry_over_from_prev

HINT_WEIGHT = float(HINT_WEIGHT_BY_BRAIN.get("stat", 0.15))


def run(draws: list[dict], n_sets: int = 5) -> list[dict]:
    """과거학습(stat) 슬롯.

    파이프:
      transition_v1(기본 OFF) → engine(v2 기본 ON via past_learn)
      → aux_hint → past_learn soft/태그 → learn boost → diversity
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
        base,
        draws,
        target_draw_no,
        aux_balance_keeper,
        "stat",
        hint_weight=HINT_WEIGHT,
    )
    # 과거학습 soft·reasoning (ASSOC 기본 OFF)
    base = past_learn.apply_to_candidates(draws, base)

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
            # boost 상한 동결: carry 가중은 learn 쪽 값 존중 · 추가 폭주 금지
            conf = min(95, conf + len(carry) * (carry_boost - 1) * 8)
        pl = r.get("past_learn") or {}
        if used_transition and str(r.get("method", "")).startswith("전이"):
            reasoning = str(r.get("reasoning", "전이패턴v1")) + learn_note
            method = "전이패턴v1"
        else:
            reasoning = (
                f"과거학습: 빈도가중+끝수{endings}"
                f"+이월{len(carry)}개{carry if carry else ''}"
                f"+미출30+{overdue if overdue else '없음'}"
            )
            tags = pl.get("tags") or []
            if tags and past_learn.wire_on():
                reasoning += f" [과거학습:{'|'.join(tags)} Δ{pl.get('soft_delta', 0)}]"
            if learn_note:
                reasoning += learn_note
            method = "과거학습"
        aux_s = float(r.get("aux_hint_score", 0.5))
        tagged.append(
            {
                "nums": sorted(nums),
                "confidence": conf,
                "native_confidence": conf,
                "aux_hint_score": aux_s,
                "pick_score": conf * (1.0 + HINT_WEIGHT * (aux_s - 0.5)),
                "reasoning": reasoning,
                "method": method,
                "brain_tag": "stat",
                "rank": i + 1,
                "past_learn": pl,
            }
        )
    return diversity.pick(tagged, n_sets, conf_key="pick_score")


predict_sets = run
