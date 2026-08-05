# -*- coding: utf-8 -*-
"""predict_transition_v1 — 유사회차→다음빈도 기반 stat 슬롯 엔진 (K-TRANSITION-STEP4).

컨닝 금지: anchor=D_{T-1} (draws[-1]), 유사 next는 T 이전만.
random.choices 미사용. engine.py 미수정.
"""
from __future__ import annotations

import os
from itertools import combinations
from typing import Any

import numpy as np

# 형 STEP4 GO 기본 ON · 롤백: K_STAT_TRANSITION_V1=0 또는 TRANSITION_V1_WIRE=False
TRANSITION_V1_WIRE: bool = True

MIN_COMMON = 2
MIN_SIMILAR = 10
TOP_M = 15


def _use_transition_v1() -> bool:
    env = os.environ.get("K_STAT_TRANSITION_V1", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return TRANSITION_V1_WIRE


def _draw_nums(d: dict) -> list[int]:
    if "nums" in d and d["nums"]:
        return sorted(int(x) for x in d["nums"])
    return sorted(int(d[f"num{k}"]) for k in range(1, 7))


def _masks_from_draws(draws: list[dict]) -> tuple[np.ndarray, list[int]]:
    """Return (masks aligned to draw order, draw_no list)."""
    n = len(draws)
    masks = np.zeros(n, dtype=np.uint64)
    draw_nos: list[int] = []
    for i, d in enumerate(draws):
        draw_nos.append(int(d["draw_no"]))
        m = np.uint64(0)
        for x in _draw_nums(d):
            m |= np.uint64(1) << np.uint64(x - 1)
        masks[i] = m
    return masks, draw_nos


def _popcount_and(past: np.ndarray, target: np.uint64) -> np.ndarray:
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(past & target)
    return np.array(
        [int(bin(int(past[j] & target)).count("1")) for j in range(len(past))],
        dtype=np.int8,
    )


def compute_top_pool(draws: list[dict]) -> dict[str, Any] | None:
    """Anchor=last draw → similar in past → freq of next → top_m + weights."""
    if len(draws) < 3:
        return None
    masks, _draw_nos = _masks_from_draws(draws)
    ni = len(draws) - 1  # anchor index
    target = masks[ni]
    # similar j in 0..ni-2 so next index j+1 <= ni-1 (before target T = ni+1 conceptually)
    commons = _popcount_and(masks[:ni], target)
    if ni < 2:
        return None
    cand = np.flatnonzero(commons[: ni - 1] >= MIN_COMMON)
    n_sim = int(cand.size)
    if n_sim < MIN_SIMILAR:
        return None

    freq = np.zeros(45, dtype=np.float64)
    for j in cand:
        nxt = _draw_nums(draws[int(j) + 1])
        for x in nxt:
            freq[x - 1] += 1.0

    order = np.lexsort((np.arange(45), -freq))
    top = [int(i + 1) for i in order[:TOP_M]]
    weights = {n: float(freq[n - 1]) for n in top}
    return {
        "top_m": top,
        "weights": weights,
        "similar_count": n_sim,
        "anchor_draw_no": int(draws[-1]["draw_no"]),
    }


def _sets_from_pool(pool: dict[str, Any], raw_n: int) -> list[dict]:
    top = pool["top_m"]
    w = pool["weights"]
    scored: list[tuple[float, tuple[int, ...]]] = []
    for combo in combinations(top, 6):
        s = tuple(sorted(combo))
        score = sum(w[n] for n in s)
        scored.append((score, s))
    scored.sort(key=lambda x: (-x[0], x[1]))
    out: list[dict] = []
    for rank, (score, nums) in enumerate(scored[: max(raw_n, 1)]):
        conf = min(95.0, 55.0 + score * 0.5)
        out.append(
            {
                "nums": list(nums),
                "confidence": conf,
                "reasoning": (
                    f"전이v1: anchor={pool['anchor_draw_no']} "
                    f"유사{pool['similar_count']}·top{TOP_M} 빈도합{score:.0f}"
                ),
                "method": "전이패턴v1",
                "brain_tag": "stat",
                "rank": rank + 1,
            }
        )
    return out


def generate(draws: list[dict], n_raw: int) -> list[dict] | None:
    """Return candidate sets or None → caller falls back to engine.generate."""
    pool = compute_top_pool(draws)
    if pool is None:
        return None
    return _sets_from_pool(pool, n_raw)
