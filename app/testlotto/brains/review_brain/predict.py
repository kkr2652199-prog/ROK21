"""review_brain.predict — 복습뇌 단일 진입점."""

from __future__ import annotations

from app.testlotto.brains import aux_miss_detective
from app.testlotto.brains.review_brain import engine, learn
from app.testlotto.brains.shared import diversity
from app.testlotto.brains.shared.aux_hint import rerank_by_aux
from app.testlotto.features.draw_features import repeat_rate_after_draw, sorted_nums

HINT_WEIGHT = 0.15  # PHASE5 · bench can monkeypatch to 0 / 0.10


def run(draws: list[dict], n_sets: int = 5) -> list[dict]:
    """predict_review_king.predict_sets 와 동치 — engine.generate + diversity.pick."""
    if not draws:
        return []

    prev = draws[-1]
    prev_nums = sorted_nums(prev)
    rates = repeat_rate_after_draw(draws)
    learn_data = learn.get_adjustments()
    adj = learn_data.get("adjustments", {})
    carry_boost = 1.0 + float(adj.get("carry_over_boost", 0))

    raw_n = diversity.factor(n_sets)
    base = engine.generate(draws, raw_n, adj=adj)
    target_draw_no = int(draws[-1]["draw_no"]) + 1 if draws else 0
    base = rerank_by_aux(
        base, draws, target_draw_no, aux_miss_detective, "review", hint_weight=HINT_WEIGHT
    )

    out: list[dict] = []
    for i, r in enumerate(base):
        pick = sorted(r["nums"])
        repeat_hits = [n for n in pick if n in prev_nums]
        conf = 60 + len(repeat_hits) * 5 + sum(rates.get(n, 0) for n in repeat_hits) * 20
        native_conf = min(95, conf)
        out.append(
            {
                "nums": pick,
                "confidence": native_conf,
                "native_confidence": native_conf,
                "aux_hint_score": float(r.get("aux_hint_score", 0.5)),
                "reasoning": (
                    f"복습왕: {prev['draw_no']}회 복습 "
                    f"이월후보{repeat_hits} 반복률가중·끝수질량균등(K-P3)"
                    f" [학습조정 이월×{carry_boost:.2f} 복습{learn_data.get('review_count',0)}회]"
                ),
                "method": "복습왕",
                "brain_tag": "review",
                "rank": i + 1,
            }
        )
    return diversity.pick(out, n_sets)


predict_sets = run  # coordinator 호환 어댑터 (PHASE4)
