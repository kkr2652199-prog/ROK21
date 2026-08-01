"""markov_brain.predict — 마르코프뇌 단일 진입점."""

from __future__ import annotations

from app.testlotto.brains import aux_pattern_spotlight
from app.testlotto.brains.markov_brain import engine
from app.testlotto.brains.shared import diversity
from app.testlotto.brains.shared.aux_hint import rerank_by_aux
from app.testlotto.features.draw_features import build_pair_freq, pair_set

HINT_WEIGHT = 0.15  # PHASE5 · bench can monkeypatch to 0 / 0.10


def run(draws: list[dict], n_sets: int = 5) -> list[dict]:
    """predict_flow_shaman.predict_sets 와 동치 — engine.generate + diversity.pick."""
    raw_n = diversity.factor(n_sets)
    base = engine.generate(draws, raw_n)
    target_draw_no = int(draws[-1]["draw_no"]) + 1 if draws else 0
    base = rerank_by_aux(
        base, draws, target_draw_no, aux_pattern_spotlight, "markov", hint_weight=HINT_WEIGHT
    )
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
    return diversity.pick(out, n_sets)


predict_sets = run  # coordinator 호환 어댑터 (PHASE4)
