"""균형지킴이 — 홀짝·고저·구간 쏠림 방지 (3예측뇌 결과 균형 조율).

[명분] 실증 · K-T 홀짝·구간·합 이론부합 p≥0.13 · K-Z/K-AA 폴백합=138(이론평균) · 출처 K-T·K-Z·K-AA
[K-AG] zone = LMH C(45,6) 이론 PMF (구 zone_spread·tgt['zone'] 혼용 제거) · odd_even_balance 소비
"""

from __future__ import annotations

from math import comb

from app.testlotto.features.draw_features import odd_even_ratio, sum_range

_N_COMBOS = comb(45, 6)
_LMH_MODE = (2, 2, 2)
_LMH_MODE_P = (comb(15, 2) * comb(15, 2) * comb(15, 2)) / _N_COMBOS  # ≈0.142126


def _zone_counts(nums: list[int]) -> tuple[int, int, int]:
    low = sum(1 for n in nums if 1 <= n <= 15)
    mid = sum(1 for n in nums if 16 <= n <= 30)
    high = sum(1 for n in nums if 31 <= n <= 45)
    return low, mid, high


def _lmh_p(low: int, mid: int, high: int) -> float:
    if low + mid + high != 6 or min(low, mid, high) < 0:
        return 0.0
    if low > 15 or mid > 15 or high > 15:
        return 0.0
    return (comb(15, low) * comb(15, mid) * comb(15, high)) / _N_COMBOS


def _zone_score_lmh(low: int, mid: int, high: int) -> float:
    """K-Z/K-AG: score = 0.3 + 0.4*(p/p_mode), mode=(2,2,2)."""
    p = _lmh_p(low, mid, high)
    return 0.3 + 0.4 * (p / _LMH_MODE_P)


def _historical_targets(draws: list[dict]) -> dict[str, float]:
    """홀·합만 역사 평균. zone 목표키는 더 이상 쓰지 않음(K-AG 정의 충돌 해소)."""
    if not draws:
        return {"odd": 3.0, "sum": 138.0}
    odds, sums = [], []
    for d in draws[-80:]:
        nums = sorted([int(d[f"num{k}"]) for k in range(1, 7)])
        o, _ = odd_even_ratio(nums)
        odds.append(o)
        sums.append(sum_range(nums))
    return {
        "odd": sum(odds) / len(odds),
        "sum": sum(sums) / len(sums),
    }


def _odd_even_boost(brain_tag: str | None) -> float:
    if not brain_tag:
        return 0.0
    try:
        from app.testlotto.learn_state import load_learn_state

        adj = load_learn_state(brain_tag).get("adjustments") or {}
    except (ValueError, Exception):
        return 0.0
    return float(adj.get("odd_even_balance", 0) or 0)


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    tgt = _historical_targets(draws)
    odd, even = odd_even_ratio(nums)
    s = sum_range(nums)
    low, mid, high = _zone_counts(nums)

    odd_score = 1.0 - min(1.0, abs(odd - tgt["odd"]) / 3)
    sum_score = 1.0 - min(1.0, abs(s - tgt["sum"]) / 60)
    zone_score = min(1.0, _zone_score_lmh(low, mid, high))

    oe_b = _odd_even_boost(brain_tag)
    odd_term = min(1.0, odd_score * (1.0 + oe_b))

    return max(0.1, min(1.0, 0.35 * odd_term + 0.35 * sum_score + 0.30 * zone_score))


def describe(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> str:
    odd, even = odd_even_ratio(nums)
    low, mid, high = _zone_counts(nums)
    return (
        f"균형지킴이:홀{odd}짝{even} "
        f"구간{low}-{mid}-{high} 점수{score_set(nums, draws, target_draw_no, brain_tag=brain_tag):.2f}"
    )
