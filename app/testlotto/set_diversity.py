# -*- coding: utf-8 -*-
"""세트 다양성 — random.choices 동결 준수.

생성은 기존 predict가 담당(동결 라인 미수정).
여기서는 후보가 많을 때 Jaccard·번호 농축을 보고 K장을 고른다.
"""
from __future__ import annotations

from typing import Any


def jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def avg_pairwise_jaccard(sets: list[list[int]]) -> float:
    if len(sets) < 2:
        return 0.0
    ss = [set(s) for s in sets]
    tot = n = 0
    for i in range(len(ss)):
        for j in range(i + 1, len(ss)):
            tot += jaccard(ss[i], ss[j])
            n += 1
    return tot / max(1, n)


def number_concentration(sets: list[list[int]]) -> dict[str, float]:
    """상위 번호가 풀을 얼마나 먹는지."""
    from collections import Counter

    c: Counter = Counter()
    for s in sets:
        c.update(set(int(x) for x in s))
    if not c:
        return {"top6_share": 0.0, "max_count": 0.0, "unique": 0.0}
    total_slots = sum(c.values())
    top6 = sum(v for _, v in c.most_common(6))
    return {
        "top6_share": round(top6 / max(1, total_slots), 4),
        "max_count": float(max(c.values())),
        "unique": float(len(c)),
    }


def diversify_pick(
    candidates: list[dict[str, Any]],
    k: int,
    *,
    jaccard_penalty: float = 0.85,
    conf_key: str = "confidence",
) -> list[dict[str, Any]]:
    """confidence - penalty*avg_jaccard_to_picked 로 탐욕 선택."""
    if not candidates:
        return []
    if len(candidates) <= k:
        return list(candidates)

    remaining = list(candidates)
    picked: list[dict[str, Any]] = []

    def score(item: dict[str, Any]) -> float:
        conf = float(item.get(conf_key, 50) or 50)
        nums = set(int(x) for x in item["nums"])
        if not picked:
            return conf
        pen = sum(jaccard(nums, set(int(x) for x in p["nums"])) for p in picked) / len(
            picked
        )
        return conf - jaccard_penalty * pen * 40.0  # scale pen into conf units

    while len(picked) < k and remaining:
        best = max(remaining, key=score)
        remaining.remove(best)
        picked.append(best)

    for i, p in enumerate(picked):
        p = dict(p)
        p["rank"] = i + 1
        picked[i] = p
    return picked


def oversample_factor(n_sets: int) -> int:
    """최종 n_sets를 위해 요청할 후보 배수."""
    return max(n_sets * 3, n_sets + 5)
