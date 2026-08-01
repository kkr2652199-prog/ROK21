"""K-BRAIN-SIGNAL-A1 — 패턴 유사도 기반 번호 신호 (coordinator 전용)."""

from __future__ import annotations

from collections import Counter

from app.testlotto.features.draw_features import ac_value, odd_even_ratio, sorted_nums

_UNIFORM = 1.0 / 45.0
_MIN_DRAWS = 15
_MIN_MAX_SIM = 0.90


def _max_consecutive_run(nums: list[int]) -> int:
    s = sorted(nums)
    max_run = 1
    run = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    return max_run


def _range_counts(nums: list[int]) -> list[int]:
    """r1~r5: 1-9, 10-19, 20-29, 30-39, 40-45."""
    buckets = [0, 0, 0, 0, 0]
    for n in nums:
        if 1 <= n <= 9:
            buckets[0] += 1
        elif 10 <= n <= 19:
            buckets[1] += 1
        elif 20 <= n <= 29:
            buckets[2] += 1
        elif 30 <= n <= 39:
            buckets[3] += 1
        elif 40 <= n <= 45:
            buckets[4] += 1
    return buckets


def _extract_features(draw: dict) -> list[float]:
    """9-dim pattern vector per K-BRAIN-SIGNAL-A1 spec."""
    nums = sorted_nums(draw)
    odd, _ = odd_even_ratio(nums)
    ranges = _range_counts(nums)
    return [
        sum(nums) / 270.0,
        odd / 6.0,
        ranges[0] / 6.0,
        ranges[1] / 6.0,
        ranges[2] / 6.0,
        ranges[3] / 6.0,
        ranges[4] / 6.0,
        ac_value(nums) / 10.0,
        _max_consecutive_run(nums) / 5.0,
    ]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    sim = dot / (na * nb)
    return max(0.0, min(1.0, sim))


def _uniform_signal() -> dict[int, float]:
    return {n: _UNIFORM for n in range(1, 46)}


def get_pattern_signal(draws: list[dict], k: int = 10) -> dict[int, float]:
    """Cosine top-k analog next-draw weighted signal, sum-normalized 1~45."""
    if len(draws) < _MIN_DRAWS:
        return _uniform_signal()

    query = _extract_features(draws[-1])
    pool_end = len(draws) - 6
    if pool_end <= 0:
        return _uniform_signal()

    scored: list[tuple[float, int]] = []
    for idx in range(pool_end):
        if idx + 1 >= len(draws) - 1:
            continue
        sim = _cosine_similarity(query, _extract_features(draws[idx]))
        scored.append((sim, idx))

    if not scored:
        return _uniform_signal()

    scored.sort(key=lambda x: (-x[0], -x[1]))
    top_k = scored[:k]
    if top_k[0][0] < _MIN_MAX_SIM:
        return _uniform_signal()

    weights: Counter[int] = Counter()
    for sim, idx in top_k:
        if sim <= 0.0:
            continue
        for n in sorted_nums(draws[idx + 1]):
            weights[n] += sim

    if not weights:
        return _uniform_signal()

    result = {n: float(weights.get(n, 0.0)) for n in range(1, 46)}
    total = sum(result.values())
    if total <= 0.0:
        return _uniform_signal()
    return {n: v / total for n, v in result.items()}
