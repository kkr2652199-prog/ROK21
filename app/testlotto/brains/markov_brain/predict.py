"""markov_brain.predict — 선호번호뇌 단일 진입점 (구 흐름술사 tag=markov)."""

from __future__ import annotations

from app.testlotto.brains import aux_pattern_spotlight
from app.testlotto.brains.markov_brain import engine, learn
from app.testlotto.brains.shared import crowd_signal, diversity
from app.testlotto.brains.shared.aux_hint import HINT_WEIGHT_BY_BRAIN, rerank_by_aux
from app.testlotto.features.draw_features import build_pair_freq, pair_set

# monkeypatch 호환 · SSOT는 HINT_WEIGHT_BY_BRAIN["markov"]
HINT_WEIGHT = float(HINT_WEIGHT_BY_BRAIN.get("markov", 0.15))
METHOD_NAME = "선호번호"


def run(draws: list[dict], n_sets: int = 5) -> list[dict]:
    """전이·동반 기반 생성 + 군중 선호(당첨자수 많은 회) 신호."""
    raw_n = diversity.factor(n_sets, brain="markov")
    base = engine.generate(draws, raw_n)
    target_draw_no = int(draws[-1]["draw_no"]) + 1 if draws else 0
    base = rerank_by_aux(
        base,
        draws,
        target_draw_no,
        aux_pattern_spotlight,
        "markov",
        hint_weight=HINT_WEIGHT,
    )
    pair_freq = build_pair_freq(draws)
    learn_data = learn.get_adjustments()
    adj = learn_data.get("adjustments", {})
    carry_boost = 1.0 + float(adj.get("carry_over_boost", 0))
    ending_boost = 1.0 + float(adj.get("ending_digit_boost", 0))
    overdue_boost = 1.0 + float(adj.get("overdue_boost", 0))
    tagged: list[dict] = []
    for i, r in enumerate(base):
        nums = sorted(r["nums"])
        pairs = pair_set(nums)
        hot_pairs = sum(pair_freq.get(p, 0) for p in pairs)
        learn_note = ""
        if adj:
            learn_note = (
                f" [학습조정 이월×{carry_boost:.2f}"
                f" 끝수×{ending_boost:.2f} 미출×{overdue_boost:.2f}]"
            )
        conf = float(r.get("confidence", 68))
        aux_s = float(r.get("aux_hint_score", 0.5))
        tagged.append(
            {
                "nums": nums,
                "confidence": conf,
                "native_confidence": conf,
                "aux_hint_score": aux_s,
                "pick_score": conf * (1.0 + HINT_WEIGHT * (aux_s - 0.5)),
                "reasoning": (
                    f"{METHOD_NAME}: 인기회차(1등다수)학습+생일대선호"
                    f"+동반쌍{hot_pairs}{learn_note}"
                ),
                "method": METHOD_NAME,
                "brain_tag": "markov",
                "rank": i + 1,
            }
        )
    tagged = crowd_signal.annotate_prefer(draws, tagged)
    for t in tagged:
        t["method"] = METHOD_NAME
        t["brain_tag"] = "markov"
        # annotate 후 confidence가 바뀌면 pick_score 재동기
        aux_s = float(t.get("aux_hint_score", 0.5))
        t["pick_score"] = float(t.get("confidence", 68)) * (
            1.0 + HINT_WEIGHT * (aux_s - 0.5)
        )
    return diversity.pick(tagged, n_sets, brain="markov", conf_key="pick_score")


predict_sets = run
