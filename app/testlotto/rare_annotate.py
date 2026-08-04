# -*- coding: utf-8 -*-
"""K-RARE annotate stub — 진단 태그 전용 · 발권 wire 기본 OFF.

RARE_ANNOTATE_WIRE=False 이면 signal_pool이 호출하지 않음(삽입점 주석만).
정책 include/exclude/boost 는 별도 형 GO.
"""
from __future__ import annotations

import math
from typing import Any

from app.testlotto.rare_bundle import detect_patterns, rarity_score, theoretical_prob

# 정책·annotate 호출 스위치 (기본 OFF · 형 GO 전 금지)
RARE_ANNOTATE_WIRE: bool = False
RARE_POLICY_MODE: str = "off"  # off | tag_only | exclude_ultra | prefer_ultra

C45_6 = 8_145_060


def annotate_set(nums: list[int] | tuple[int, ...]) -> dict[str, Any]:
    """순수함수: 6수 → rare_tags / rarity_score. DB·발권 부작용 없음."""
    s = sorted(int(x) for x in nums)
    tags = detect_patterns(s)
    probs = [theoretical_prob(t) for t in tags]
    probs_f = [p for p in probs if p is not None]
    # 가장 희귀(작은 p) 기준 스코어; 태그 없으면 0
    if probs_f:
        p_min = min(probs_f)
        score = rarity_score(p_min)
    else:
        p_min = None
        score = 0.0
    ultra = any(
        t
        in (
            "consec_6",
            "split_exact_123_434445",
            "arithmetic_6",
            "parity_all_odd",
            "parity_all_even",
            "zone_all_low_1_15",
            "zone_all_high_31_45",
            "rank_top1000",
            "rank_bottom1000",
        )
        for t in tags
    )
    return {
        "nums": s,
        "rare_tags": tags,
        "rarity_score": round(float(score), 4),
        "p_template_min": p_min,
        "is_ultra_rare_tag": ultra,
        "schema": "rare_tag_v1",
        "wire": RARE_ANNOTATE_WIRE,
        "policy": RARE_POLICY_MODE,
    }


def annotate_sets(sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """pool/repack entry 리스트에 rare 필드 부착(복사). wire OFF여도 호출 가능(진단)."""
    out = []
    for e in sets:
        nums = e.get("nums") or []
        ann = annotate_set(nums)
        ne = dict(e)
        ne["rare_tags"] = ann["rare_tags"]
        ne["rarity_score"] = ann["rarity_score"]
        ne["is_ultra_rare_tag"] = ann["is_ultra_rare_tag"]
        out.append(ne)
    return out


def policy_filter(sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """정책층 · 기본 off는 입력 그대로. wire/정책 GO 전 발권 경로에서 호출 금지."""
    if RARE_POLICY_MODE == "off" or not RARE_ANNOTATE_WIRE:
        return list(sets)
    if RARE_POLICY_MODE == "tag_only":
        return annotate_sets(sets)
    if RARE_POLICY_MODE == "exclude_ultra":
        ann = annotate_sets(sets)
        return [e for e in ann if not e.get("is_ultra_rare_tag")]
    if RARE_POLICY_MODE == "prefer_ultra":
        ann = annotate_sets(sets)
        return sorted(ann, key=lambda e: (-float(e.get("rarity_score") or 0), e.get("set_no") or 0))
    return list(sets)


def template_weight_odd_k(k: int) -> int:
    """홀수 k개 템플릿 크기 w."""
    if k < 0 or k > 6 or k > 23 or (6 - k) > 22:
        return 0
    return math.comb(23, k) * math.comb(22, 6 - k)


def template_prob(w: int) -> float:
    return w / C45_6 if w >= 0 else 0.0
