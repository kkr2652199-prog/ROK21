"""review_brain.engine — 복습·이월·neutralize 생성 엔진."""

from __future__ import annotations

import random

from app.testlotto.features.draw_features import repeat_rate_after_draw, sorted_nums
from app.testlotto.filters import tier1_filter


def build_review_weights(draws: list[dict], adj: dict | None = None) -> dict[int, float]:
    """review 가중치 구성 (K-X 경로). random.choices 직전까지."""
    if not draws:
        return {n: 1.0 for n in range(1, 46)}
    prev = draws[-1]
    prev_nums = sorted_nums(prev)
    rates = repeat_rate_after_draw(draws)
    carry_boost = 1.0 + float((adj or {}).get("carry_over_boost", 0))
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


def generate(draws: list[dict], n_sets: int = 5, adj: dict | None = None) -> list[dict]:
    if not draws:
        return []

    prev = draws[-1]
    prev_nums = sorted_nums(prev)
    rates = repeat_rate_after_draw(draws)
    weights = build_review_weights(draws, adj)

    results: list[dict] = []
    used: set[tuple[int, ...]] = set()
    attempts = 0
    while len(results) < n_sets and attempts < 3000:
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
            }
        )
    return results
