# -*- coding: utf-8 -*-
"""814만(C(45,6)) 조합 공간에서 극소 확률 번들·패턴 탐지.

참고:
- arXiv:math/0507469 — 연속번호 포함 확률 ~49.5% (6/49); 6/45는 유사하게 높음
- Math Doctors / StackExchange — 개별 조합 확률은 동일(1/8145060), 구조별 *개수*가 희귀도
- LotteryCodex — 1-2-3-4-5-6 등 consecutive block은 조합 공간에서 극히 얇은 slice
"""
from __future__ import annotations

import json
import math
from itertools import combinations
from typing import Any

from app.lotto4.combinadic import TOTAL_COMBOS, combo_to_no

# 이론 참고 문헌 (JSON refs 필드용)
REFS = [
    {
        "id": "arxiv-0507469",
        "title": "On the probability of consecutive numbers in a lottery",
        "url": "https://arxiv.org/abs/math/0507469",
        "note": "6/49에서 2연속 포함 ~49.5%; 구조별 빈도 ≠ 개별 조합 확률",
    },
    {
        "id": "mathdoctors-consecutive",
        "title": "Probability of Consecutive Numbers in a Lottery",
        "url": "https://www.themathdoctors.org/probability-of-consecutive-numbers-in-a-lottery/",
    },
    {
        "id": "lotterycodex-consec",
        "title": "Consecutive Block Analysis",
        "url": "https://lotterycodex.com/calculators/consecutive-block-analysis.php",
        "note": "모든 조합 동일 1-draw 확률; consecutive slice는 공간 비율이 작음",
    },
]

# 패턴 메타: (label, theoretical_count_fn or int)
PATTERN_META: dict[str, dict[str, Any]] = {
    "consec_6": {
        "label": "6연속 번들",
        "example": [1, 2, 3, 4, 5, 6],
        "theoretical_count": 40,
        "note": "40개 윈도우 (1-6 … 40-45)",
    },
    "consec_5_window": {
        "label": "5연속 포함(6연속 제외)",
        "theoretical_count": 660,
        "note": "41윈도우×15 여유번호 − 6연속 중복",
    },
    "split_exact_123_434445": {
        "label": "극단 분할 1·2·3 + 43·44·45",
        "example": [1, 2, 3, 43, 44, 45],
        "theoretical_count": 1,
    },
    "split_low3_high3_extreme": {
        "label": "저역3(1-10)+고역3(36-45) · 중간 없음",
        "theoretical_count": 120 * 120,
        "note": "C(10,3)×C(10,3)=14400",
    },
    "zone_all_low_1_15": {
        "label": "전부 1~15 구역",
        "theoretical_count": math.comb(15, 6),
    },
    "zone_all_high_31_45": {
        "label": "전부 31~45 구역",
        "theoretical_count": math.comb(15, 6),
    },
    "parity_all_odd": {
        "label": "전부 홀수",
        "theoretical_count": math.comb(23, 6),
    },
    "parity_all_even": {
        "label": "전부 짝수",
        "theoretical_count": math.comb(22, 6),
    },
    "arithmetic_6": {
        "label": "6개 등차수열",
        "theoretical_count": 165,
        "note": "공차 d≥1 · 시작점별 열거",
    },
    "spread_min_gap7": {
        "label": "정렬 후 인접 간격 전부 ≥7",
        "theoretical_count": None,
        "note": "극소 spread · 열거로 집계",
    },
    "rank_top1000": {
        "label": "814만 순위 상위 1000",
        "theoretical_count": 1000,
    },
    "rank_bottom1000": {
        "label": "814만 순위 하위 1000",
        "theoretical_count": 1000,
    },
}


def sorted_nums(nums: list[int] | tuple[int, ...]) -> list[int]:
    return sorted(int(n) for n in nums)


def max_consecutive_run(nums: list[int] | tuple[int, ...]) -> int:
    s = sorted_nums(nums)
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def is_arithmetic_6(nums: list[int]) -> bool:
    s = sorted_nums(nums)
    gaps = {s[i + 1] - s[i] for i in range(5)}
    return len(gaps) == 1 and next(iter(gaps)) > 0


def detect_patterns(nums: list[int] | tuple[int, ...]) -> list[str]:
    """6수에 매칭되는 패턴 키 목록."""
    s = sorted_nums(nums)
    out: list[str] = []
    run = max_consecutive_run(s)
    if run >= 6:
        out.append("consec_6")
    if run >= 5:
        out.append("consec_5plus")
    if run >= 4:
        out.append("consec_4plus")
    if run >= 3:
        out.append("consec_3plus")

    low10 = sum(1 for x in s if x <= 10)
    high10 = sum(1 for x in s if x >= 36)
    if low10 >= 3 and high10 >= 3:
        out.append("split_low10_high10")
    if s == [1, 2, 3, 43, 44, 45]:
        out.append("split_exact_123_434445")

    if all(x <= 15 for x in s):
        out.append("zone_all_low_1_15")
    if all(x >= 31 for x in s):
        out.append("zone_all_high_31_45")
    if all(x % 2 == 1 for x in s):
        out.append("parity_all_odd")
    if all(x % 2 == 0 for x in s):
        out.append("parity_all_even")
    if is_arithmetic_6(s):
        out.append("arithmetic_6")

    gaps = [s[i + 1] - s[i] for i in range(5)]
    if min(gaps) >= 7:
        out.append("spread_min_gap7")
    if min(gaps) >= 8:
        out.append("spread_min_gap8")

    rank = combo_to_no(s)
    if rank <= 1000:
        out.append("rank_top1000")
    if rank > TOTAL_COMBOS - 1000:
        out.append("rank_bottom1000")

    return out


def theoretical_prob(pattern_key: str) -> float | None:
    meta = PATTERN_META.get(pattern_key.replace("plus", "").replace("_plus", ""))
    if not meta:
        # consec_5plus 등 동적 키
        if pattern_key == "consec_5plus":
            cnt = 750  # approx: 41*15 - overlap
            return cnt / TOTAL_COMBOS
        if pattern_key == "consec_4plus":
            return 0.002  # order ~0.2% from hist survey
        if pattern_key == "consec_3plus":
            return 0.05
        if pattern_key == "split_low10_high10":
            return (120 * 120) / TOTAL_COMBOS
        if pattern_key == "spread_min_gap7":
            return None
        if pattern_key == "spread_min_gap8":
            return None
        return None
    cnt = meta.get("theoretical_count")
    if cnt is None:
        return None
    return cnt / TOTAL_COMBOS


def rarity_score(prob: float | None) -> float:
    """-log10(p) · prob None이면 99."""
    if prob is None or prob <= 0:
        return 99.0
    return -math.log10(prob)


def enumerate_consec_6() -> list[tuple[int, ...]]:
    return [tuple(range(start, start + 6)) for start in range(1, 41)]


def enumerate_arithmetic_6() -> list[tuple[int, ...]]:
    out: set[tuple[int, ...]] = set()
    for d in range(1, 8):
        for start in range(1, 46):
            seq = [start + i * d for i in range(6)]
            if seq[-1] > 45:
                break
            if len(set(seq)) == 6:
                out.add(tuple(seq))
    return sorted(out)


def enumerate_split_low3_high3_extreme() -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []
    for low in combinations(range(1, 11), 3):
        for high in combinations(range(36, 46), 3):
            out.append(tuple(sorted(low + high)))
    return out


def enumerate_ultra_rare_catalog() -> list[dict[str, Any]]:
    """극소 패턴 대표 조합 catalog (814만 subset)."""
    seen: set[tuple[int, ...]] = set()
    catalog: list[dict[str, Any]] = []

    def add(nums: tuple[int, ...], pattern_key: str, *, force_ultra: bool = False) -> None:
        if nums in seen:
            return
        seen.add(nums)
        patterns = detect_patterns(nums)
        if pattern_key not in patterns:
            patterns.append(pattern_key)
        rank = combo_to_no(nums)
        probs = [theoretical_prob(p) for p in patterns]
        probs_valid = [p for p in probs if p is not None]
        min_prob = min(probs_valid) if probs_valid else 1 / TOTAL_COMBOS
        score = rarity_score(min_prob)
        ultra = force_ultra or min_prob <= 1 / 50_000 or score >= 4.5
        catalog.append(
            {
                "nums": list(nums),
                "combo_rank_814": rank,
                "pattern_keys": patterns,
                "primary_pattern": pattern_key,
                "theoretical_prob": min_prob,
                "rarity_score": round(score, 4),
                "is_ultra_rare": ultra,
            }
        )

    for nums in enumerate_consec_6():
        add(nums, "consec_6", force_ultra=True)

    add((1, 2, 3, 43, 44, 45), "split_exact_123_434445", force_ultra=True)
    add((39, 40, 41, 42, 43, 44), "consec_6", force_ultra=True)
    add((40, 41, 42, 43, 44, 45), "consec_6", force_ultra=True)

    for nums in enumerate_arithmetic_6():
        add(nums, "arithmetic_6")

    # split extreme sample (first 50 by rank)
    split_all = enumerate_split_low3_high3_extreme()
    split_sorted = sorted(split_all, key=lambda t: combo_to_no(t))
    for nums in split_sorted[:30]:
        add(nums, "split_low3_high3_extreme")

    # rank extremes
    for rank in [1, 2, 3, 100, 500, 1000]:
        add(no_to_combo_safe(rank), "rank_top1000", force_ultra=True)
    for rank in [TOTAL_COMBOS, TOTAL_COMBOS - 1, TOTAL_COMBOS - 999]:
        add(no_to_combo_safe(rank), "rank_bottom1000", force_ultra=True)

    catalog.sort(key=lambda x: (-x["rarity_score"], x["combo_rank_814"]))
    return catalog


def no_to_combo_safe(no: int) -> tuple[int, ...]:
    from app.lotto4.combinadic import no_to_combo

    return no_to_combo(no)


def refs_json() -> str:
    return json.dumps(REFS, ensure_ascii=False)
