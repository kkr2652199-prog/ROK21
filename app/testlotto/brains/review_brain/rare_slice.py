# -*- coding: utf-8 -*-
"""금액뇌 예측 전 극소형태표.

개별 조합 확률은 모두 1/C(45,6). 희귀한 것은 *형태 조각*의 두께.
표=814만 전수 + 당첨 1–1237 실측. 타깃 회 당첨 미입력.
1단계 거절=1237에서 0회이고 공간이 얇은 조각만.
"""
from __future__ import annotations

from typing import Any

# K-REVIEW-RARE-SLICE (20260823)
# 롤백: REVIEW_RARE_SLICE_WIRE=False
REVIEW_RARE_SLICE_WIRE: bool = True

C45_6 = 8_145_060
AS_OF_DRAWS = 1237

# 20260823 전수 실측 (itertools.combinations 1..45 C6)
SPACE: dict[str, int] = {
    "run6": 40,
    "run5plus": 1600,
    "run4plus": 32800,
    "run3plus": 458420,
    "arith6": 180,
    "gap8": 210,
    "gap7": 5005,
    "split_l3h3": 14400,
    "exact_123_434445": 1,
    "zone_1_15": 5005,
    "zone_16_30": 5005,
    "zone_31_45": 5005,
    "all_odd": 100947,
    "all_even": 74613,
    "span_lt15": 65065,
    "span_lt20": 329460,
}

# 당첨 1–1237
DRAWS: dict[str, int] = {
    "run6": 0,
    "run5plus": 0,
    "run4plus": 6,
    "run3plus": 67,
    "arith6": 0,
    "gap8": 0,
    "gap7": 1,
    "split_l3h3": 0,
    "exact_123_434445": 0,
    "zone_1_15": 0,
    "zone_16_30": 2,
    "zone_31_45": 1,
    "all_odd": 19,
    "all_even": 17,
    "span_lt15": 12,
    "span_lt20": 57,
}

# 1단계: 공간 얇고 1237=0. run5/6·전홀짝은 tier1이 이미 탈락.
STEP1_REJECT: frozenset[str] = frozenset(
    {
        "arith6",
        "gap8",
        "split_l3h3",
        "zone_1_15",
        "exact_123_434445",
        "run5plus",
        "run6",
    }
)


def max_run(nums: list[int]) -> int:
    s = sorted(int(x) for x in nums)
    if len(s) < 2:
        return len(s)
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def tags(nums: list[int]) -> list[str]:
    s = sorted(int(x) for x in nums)
    if len(s) != 6:
        return []
    out: list[str] = []
    r = max_run(s)
    if r == 6:
        out.append("run6")
    if r >= 5:
        out.append("run5plus")
    if r >= 4:
        out.append("run4plus")
    if r >= 3:
        out.append("run3plus")
    d0 = s[1] - s[0]
    if d0 > 0 and all(s[i + 1] - s[i] == d0 for i in range(5)):
        out.append("arith6")
    gaps = [s[i + 1] - s[i] for i in range(5)]
    if min(gaps) >= 8:
        out.append("gap8")
    if min(gaps) >= 7:
        out.append("gap7")
    low10 = sum(1 for x in s if x <= 10)
    high10 = sum(1 for x in s if x >= 36)
    if low10 >= 3 and high10 >= 3:
        out.append("split_l3h3")
    if s == [1, 2, 3, 43, 44, 45]:
        out.append("exact_123_434445")
    if all(x <= 15 for x in s):
        out.append("zone_1_15")
    if all(16 <= x <= 30 for x in s):
        out.append("zone_16_30")
    if all(x >= 31 for x in s):
        out.append("zone_31_45")
    odd = sum(1 for x in s if x % 2 == 1)
    if odd == 6:
        out.append("all_odd")
    if odd == 0:
        out.append("all_even")
    span = s[5] - s[0]
    if span < 15:
        out.append("span_lt15")
    if span < 20:
        out.append("span_lt20")
    return out


def pass_tags(nums: list[int]) -> list[str]:
    """패스 목록에 쓰는 STEP1 태그만 (run4plus·span 등 제외)."""
    return [t for t in tags(nums) if t in STEP1_REJECT]


def is_step1_rare(nums: list[int]) -> bool:
    return bool(STEP1_REJECT.intersection(tags(nums)))


def summarize() -> dict[str, Any]:
    rows = []
    for k in SPACE:
        c = SPACE[k]
        h = DRAWS.get(k, 0)
        rows.append(
            {
                "key": k,
                "space": c,
                "p_space": round(c / C45_6, 8),
                "draws": h,
                "p_draws": round(h / AS_OF_DRAWS, 8),
                "null_e": round(AS_OF_DRAWS * c / C45_6, 4),
                "step1_reject": k in STEP1_REJECT,
            }
        )
    return {
        "c45_6": C45_6,
        "as_of_draws": AS_OF_DRAWS,
        "step1_reject": sorted(STEP1_REJECT),
        "rows": rows,
    }
