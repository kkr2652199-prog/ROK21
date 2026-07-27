# -*- coding: utf-8 -*-
"""발권 후처리 중복제거 (K-V).

뇌 산출 → 기존 파이프라인 → ★본 모듈 → 발권.
뇌 내부·fusion·referee 로직은 수정하지 않는다.

판정 키: 정렬된 6번호 튜플. 회차(배치) 내 전역 유일.
중복 시 같은 뇌만 재요청. 상한 50회. 초과 시 원본 유지 + 미해소 건수 보고.
재요청 후보가 유일하면 즉시 채택. 상한 50회.
스위치: ROK21_DEDUP 기본 ON. 0/false/off/no 만 OFF.
"""
from __future__ import annotations

import logging
import os
from collections import Counter
from typing import Any, Callable

logger = logging.getLogger(__name__)

MAX_DEDUP_RETRIES = 50

# regenerate(brain_tag, seen_keys, replace_of) -> ticket | None
RegenFn = Callable[
    [str, set[tuple[int, ...]], dict[str, Any] | None],
    dict[str, Any] | None,
]


def dedup_enabled() -> bool:
    """기본 ON. 미설정·빈문자도 ON. 명시 0/false/off/no 만 OFF."""
    raw = os.environ.get("ROK21_DEDUP")
    if raw is None or str(raw).strip() == "":
        return True
    v = str(raw).strip().lower()
    if v in ("0", "false", "off", "no"):
        return False
    return v in ("1", "true", "on", "yes")


def combo_key(nums: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def dedup_ticket_list(
    tickets: list[dict[str, Any]],
    *,
    regenerate: RegenFn,
    max_retries: int = MAX_DEDUP_RETRIES,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """회차/배치 전역 중복 제거.

    regenerate(brain_tag, seen_keys, replace_of) -> 대체 티켓 dict 또는 None.
    미해소 시 원본 유지(은폐 금지) · unresolved_count 반환.
    """
    if not dedup_enabled():
        return list(tickets), {
            "dedup_enabled": False,
            "unresolved_count": 0,
            "retries_used": 0,
            "dup_events": 0,
            "regen_by_brain": {},
            "n_in": len(tickets),
            "n_out": len(tickets),
            "unique_out": len({combo_key(t["nums"]) for t in tickets}) if tickets else 0,
        }

    result: list[dict[str, Any]] = []
    seen: set[tuple[int, ...]] = set()
    unresolved = 0
    retries_used = 0
    dup_events = 0
    regen_by_brain: Counter[str] = Counter()

    for t in tickets:
        key = combo_key(t["nums"])
        if key not in seen:
            seen.add(key)
            result.append(t)
            continue

        dup_events += 1
        tag = str(t.get("brain_tag") or "")
        replaced = False

        for _ in range(max_retries):
            retries_used += 1
            regen_by_brain[tag] += 1
            new_t = regenerate(tag, seen, t)
            if new_t is None:
                continue
            nk = combo_key(new_t["nums"])
            if nk in seen:
                continue
            seen.add(nk)
            result.append(new_t)
            replaced = True
            break

        if not replaced:
            unresolved += 1
            result.append(t)
            logger.warning(
                "[ROK21_DEDUP] unresolved duplicate brain=%s key=%s after %d retries",
                tag,
                key,
                max_retries,
            )

    unique_out = len({combo_key(t["nums"]) for t in result})
    stats = {
        "dedup_enabled": True,
        "unresolved_count": unresolved,
        "retries_used": retries_used,
        "dup_events": dup_events,
        "regen_by_brain": dict(regen_by_brain),
        "n_in": len(tickets),
        "n_out": len(result),
        "unique_out": unique_out,
    }
    return result, stats
