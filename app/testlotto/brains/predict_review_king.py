"""복습왕 — 전회차 복습 학습형 (walk-forward 반복률, LotteryML lag 벤치마킹).

[명분] 기각 · K-T 이월성향(lag1 대리) p=0.764 · 출처 K-T/K-W
[K-W] 전반 C근접 · 끝수 지표 A·C 양쪽 원격(편향경보) — WARRANT.md
[K-P3] repeat_rate 끝수 투영 완화 — ending 질량 균등화(random.choices 전, 라인 동결)
※ 기각이어도 제거·비활성 금지(조합불변·다양성 기여).
"""

from __future__ import annotations

import random

from app.testlotto.features.draw_features import repeat_rate_after_draw, sorted_nums
from app.testlotto.filters import tier1_filter
from app.testlotto.learn_state import load_learn_state


def build_review_weights(draws: list[dict]) -> dict[int, float]:
    """review 가중치 구성 (K-X 경로). random.choices 직전까지."""
    if not draws:
        return {n: 1.0 for n in range(1, 46)}
    prev = draws[-1]
    prev_nums = sorted_nums(prev)
    rates = repeat_rate_after_draw(draws)
    learn = load_learn_state("review")
    adj = learn.get("adjustments", {})
    carry_boost = 1.0 + float(adj.get("carry_over_boost", 0))
    weights = {n: rates.get(n, 0.08) for n in range(1, 46)}
    for n in prev_nums:
        weights[n] *= 1.8 * carry_boost
    for n in range(1, 46):
        if n not in prev_nums:
            weights[n] *= 0.85
    return neutralize_ending_digit_mass(weights)


def neutralize_ending_digit_mass(weights: dict[int, float]) -> dict[int, float]:
    """K-P3: 끝수별 총 질량을 균등화해 repeat_rate 끝수 투영 완화.

    random.choices 라인은 건드리지 않음. 가중치만 조정.
    """
    end_sum: dict[int, float] = {d: 0.0 for d in range(10)}
    for n, w in weights.items():
        end_sum[n % 10] += max(float(w), 0.0)
    total = sum(end_sum.values()) or 1.0
    target_per_end = total / 10.0
    out: dict[int, float] = {}
    for n, w in weights.items():
        e = n % 10
        factor = target_per_end / max(end_sum[e], 1e-12)
        out[n] = max(float(w), 0.0) * factor
    return out


def predict_sets(draws: list[dict], n_sets: int = 5) -> list[dict]:
    if not draws:
        return []
    from app.testlotto.set_diversity import diversify_pick, oversample_factor

    prev = draws[-1]
    prev_nums = sorted_nums(prev)
    learn = load_learn_state("review")
    adj = learn.get("adjustments", {})
    carry_boost = 1.0 + float(adj.get("carry_over_boost", 0))
    weights = build_review_weights(draws)

    raw_n = oversample_factor(n_sets)
    results: list[dict] = []
    used: set[tuple[int, ...]] = set()
    attempts = 0
    while len(results) < raw_n and attempts < 3000:
        attempts += 1
        pool = list(range(1, 46))
        w = [weights[n] for n in pool]
        pick: list[int] = []
        for _ in range(6):
            if not pool:
                break
            chosen = random.choices(pool, weights=w, k=1)[0]
            pick.append(chosen)
            idx = pool.index(chosen)
            pool.pop(idx)
            w.pop(idx)
        pick = sorted(pick)
        if len(pick) != 6:
            continue
        key = tuple(pick)
        if key in used:
            continue
        if not tier1_filter(pick):
            continue
        used.add(key)
        repeat_hits = [n for n in pick if n in prev_nums]
        conf = 60 + len(repeat_hits) * 5 + sum(rates.get(n, 0) for n in repeat_hits) * 20
        results.append(
            {
                "nums": pick,
                "confidence": min(95, conf),
                "reasoning": (
                    f"복습왕: {prev['draw_no']}회 복습 "
                    f"이월후보{repeat_hits} 반복률가중·끝수질량균등(K-P3)"
                    f" [학습조정 이월×{carry_boost:.2f} 복습{learn.get('review_count',0)}회]"
                ),
                "method": "복습왕",
                "brain_tag": "review",
                "rank": len(results) + 1,
            }
        )
    return diversify_pick(results, n_sets)
