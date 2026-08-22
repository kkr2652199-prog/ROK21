# -*- coding: utf-8 -*-
"""금액뇌 예측 전 형태표 — 타깃 회 당첨 미입력.

`draws` = 이미 `_get_draws_before(target)` 인 리스트만.
연번=같은 회 |a-b|=1. 공식 정답 없음. 뇌가 매 예측 전 다시 읽는다.
"""
from __future__ import annotations

from statistics import median
from typing import Any

from app.testlotto.features.draw_features import consecutive_pairs, sorted_nums

# K-REVIEW-SHAPE-CONSEC (20260822) — 3연속 고가중 능선 평탄.
# 롤백: REVIEW_SHAPE_WIRE=False
REVIEW_SHAPE_WIRE: bool = True
REVIEW_SHAPE_FLAT_FACTOR: float = 0.75


def max_run(nums: list[int]) -> int:
    s = sorted(int(x) for x in nums)
    if not s:
        return 0
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def summarize(draws: list[dict]) -> dict[str, Any]:
    """as_of = draws[-1]. 빈 draws면 널 기하만."""
    n = len(draws)
    hist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    pairs: list[int] = []
    if not draws:
        return {
            "n": 0,
            "p_pair": None,
            "p_run3": None,
            "p_run4": None,
            "mean_pairs": None,
            "max_run_hist": hist,
            "as_of": None,
        }
    for d in draws:
        nums = sorted_nums(d)
        r = max_run(nums)
        hist[min(6, max(1, r))] = hist.get(min(6, max(1, r)), 0) + 1
        pairs.append(consecutive_pairs(nums))
    has_pair = sum(1 for p in pairs if p >= 1)
    run3 = sum(hist[k] for k in (3, 4, 5, 6))
    run4 = sum(hist[k] for k in (4, 5, 6))
    return {
        "n": n,
        "as_of": int(draws[-1]["draw_no"]),
        "p_pair": round(has_pair / n, 6),
        "p_run3": round(run3 / n, 6),
        "p_run4": round(run4 / n, 6),
        "mean_pairs": round(sum(pairs) / n, 6),
        "max_run_hist": hist,
    }


def apply_consec_flatten(
    weights: dict[int, float],
    *,
    factor: float = REVIEW_SHAPE_FLAT_FACTOR,
) -> dict[int, float]:
    """3연속 번호가 모두 중앙값 초과면 가운데 질량↓. random.choices 전."""
    if not weights:
        return weights
    med = float(median(float(weights[n]) for n in range(1, 46) if n in weights))
    out = {int(k): float(v) for k, v in weights.items()}
    fac = max(0.05, min(1.0, float(factor)))
    for n in range(1, 44):
        a, b, c = out.get(n, 0.0), out.get(n + 1, 0.0), out.get(n + 2, 0.0)
        if a > med and b > med and c > med:
            out[n + 1] = b * fac
    return out
