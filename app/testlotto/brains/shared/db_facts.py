"""shared.db_facts — draws 기반 파생 통계 (Phase1).

번호 빈도·pair 빈도·gap·carry 후보 등 DB/draws 공통 fact 추출.
각 brain engine·aux hint 입력용 — 컨닝 방지 cutoff는 호출측 책임.
"""

from __future__ import annotations

from math import exp


def get_number_freq(draws: list[dict]) -> dict[int, float]:
    """각 번호(1~45) 출현 빈도(정규화 비율)를 반환한다."""
    if not draws:
        return {n: 1.0 / 45 for n in range(1, 46)}

    freq: dict[int, float] = {}
    total_draws = len(draws)

    for idx, d in enumerate(draws):
        recency_weight = exp(-0.02 * (total_draws - 1 - idx))
        for k in ["num1", "num2", "num3", "num4", "num5", "num6"]:
            n = d[k]
            freq[n] = freq.get(n, 0.0) + recency_weight

    for n in range(1, 46):
        if n not in freq:
            freq[n] = 0.1

    total = sum(freq.values())
    return {n: freq[n] / total for n in range(1, 46)}


def get_pair_freq(draws: list[dict]) -> dict[tuple[int, int], int]:
    """번호 쌍 (a, b) 동시 출현 횟수를 반환한다. a < b 정렬 키."""
    recent_for_pairs = draws[-200:] if len(draws) >= 200 else draws
    pair_freq: dict[tuple[int, int], int] = {}
    for d in recent_for_pairs:
        nums_in_draw = sorted(
            [d["num1"], d["num2"], d["num3"], d["num4"], d["num5"], d["num6"]]
        )
        for i in range(len(nums_in_draw)):
            for j in range(i + 1, len(nums_in_draw)):
                pair = (nums_in_draw[i], nums_in_draw[j])
                pair_freq[pair] = pair_freq.get(pair, 0) + 1
    return pair_freq


def get_gap_map(draws: list[dict]) -> dict[int, int]:
    """각 번호의 최근 미출현 회차(gap)를 반환한다."""
    last_seen: dict[int, int] = {}
    for d in draws:
        for k in ["num1", "num2", "num3", "num4", "num5", "num6"]:
            last_seen[d[k]] = d["draw_no"]

    latest_draw_no = draws[-1]["draw_no"] if draws else 0
    return {n: latest_draw_no - last_seen.get(n, 0) for n in range(1, 46)}


def get_carry_candidates(draws: list[dict]) -> list[int]:
    """직전 회차 당첨번호 중 이월(carry-over) 후보 번호 목록을 반환한다."""
    if not draws:
        return []
    prev = draws[-1]
    return sorted(int(prev[f"num{k}"]) for k in range(1, 7))
