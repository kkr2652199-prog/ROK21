# DEPRECATED: markov_brain.predict.run() 사용 — K-BRAIN-PACKAGE-PHASE2 동치 PASS 후 유지(삭제 금지).
"""흐름술사 — 마르코프 전이 + 동반출현 (lottery_predictor STRAT05 벤치마킹).

[명분] 기각 · K-T lag1 중복 χ² p=0.764 (회차의존 전제 기각) · 출처 K-T/K-W
[K-W] 산출 정합성: 균등(C) 근접 (명분 없으나 무해) — WARRANT.md
※ 기각이어도 제거·비활성 금지(조합불변·다양성 기여).
"""

from __future__ import annotations

from app.testlotto.features.draw_features import build_pair_freq, pair_set, sorted_nums
from app.testlotto.predict_markov import _markov_predict


def predict_sets(draws: list[dict], n_sets: int = 5) -> list[dict]:
    """후보 oversample 후 다양성 선별 (random.choices 라인 미수정)."""
    from app.testlotto.set_diversity import diversify_pick, oversample_factor

    base = _markov_predict(draws, oversample_factor(n_sets))
    pair_freq = build_pair_freq(draws)
    out: list[dict] = []
    for i, r in enumerate(base):
        nums = sorted(r["nums"])
        pairs = pair_set(nums)
        hot_pairs = sum(pair_freq.get(p, 0) for p in pairs)
        reasoning = f"흐름술사: 마르코프전이+동반쌍점수{hot_pairs}"
        out.append(
            {
                "nums": sorted(nums),
                "confidence": float(r.get("confidence", 68)),
                "reasoning": reasoning,
                "method": "흐름술사",
                "brain_tag": "markov",
                "rank": i + 1,
            }
        )
    return diversify_pick(out, n_sets)
