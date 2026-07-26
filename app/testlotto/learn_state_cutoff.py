# -*- coding: utf-8 -*-
"""K-09 learn_state 컷오프 — DB 스키마 변경 없이 피드백 재구성.

방식 (b): testlotto_brain_review 의 matched/missed 를 draw_no < N 만
순차 재생해 상태를 복원. 전역 testlotto_brain_learn_state 행은 읽기만
(플래그 OFF) 또는 폴백 시 사용. DELETE/스키마 변경 없음.

활성: ROK21_LEARN_CUTOFF=1 + set_learn_as_of(target)
기본 OFF → load_learn_state 가 전역 행과 동일.
"""
from __future__ import annotations

import copy
import json
import os
from contextvars import ContextVar
from typing import Any

from app.testlotto.learn_state import (
    BOOST_CAPS,
    DEFAULT_ADJUSTMENTS,
    PREDICT_BRAIN_TAGS,
    _empty_state,
)

_learn_as_of: ContextVar[int | None] = ContextVar("rok21_learn_as_of", default=None)

# brain -> sorted list of (draw_no, state_after_feedback)
_history_cache: dict[str, list[tuple[int, dict[str, Any]]]] | None = None


def cutoff_enabled() -> bool:
    return os.environ.get("ROK21_LEARN_CUTOFF", "").strip() == "1"


def set_learn_as_of(target_draw_no: int | None) -> None:
    """예측 target N 에 대해 as_of = N (로드 시 draw_no < N 만 사용)."""
    _learn_as_of.set(int(target_draw_no) if target_draw_no is not None else None)


def get_learn_as_of() -> int | None:
    return _learn_as_of.get()


def clear_history_cache() -> None:
    global _history_cache
    _history_cache = None


def apply_feedback_pure(
    state: dict[str, Any],
    draw_no: int,
    matched_count: int,
    missed_patterns: list[str],
) -> dict[str, Any]:
    """apply_feedback 과 동일 로직, DB 쓰기 없음."""
    state = copy.deepcopy(state)
    adj = state.setdefault("adjustments", dict(DEFAULT_ADJUSTMENTS))
    miss_counts = state.setdefault("miss_counts", {})

    for pattern in missed_patterns:
        miss_counts[pattern] = int(miss_counts.get(pattern, 0)) + 1
        recent = miss_counts[pattern]
        if recent >= 3:
            boost_key = {
                "carry_over": "carry_over_boost",
                "ending_digit": "ending_digit_boost",
                "pair": "pair_boost",
                "consecutive": "consecutive_boost",
                "overdue": "overdue_boost",
                "odd_even": "odd_even_balance",
            }.get(pattern)
            if boost_key:
                cap = BOOST_CAPS.get(boost_key, 0.5)
                cur = float(adj.get(boost_key, 0) or 0)
                if cur < cap:
                    adj[boost_key] = min(cap, cur + 0.05)

    for bk, cap in BOOST_CAPS.items():
        if bk in adj:
            adj[bk] = min(float(cap), float(adj.get(bk, 0) or 0))

    rc = int(state.get("review_count", 0)) + 1
    prev_avg = float(state.get("recent_avg_match", 0.0))
    new_avg = (
        ((prev_avg * (rc - 1)) + matched_count) / rc if rc > 0 else float(matched_count)
    )

    state["review_count"] = rc
    state["last_draw_no"] = int(draw_no)
    state["recent_avg_match"] = round(new_avg, 4)
    state["adjustments"] = adj
    state["miss_counts"] = miss_counts
    return state


def _parse_missed(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(x) for x in data]
        except json.JSONDecodeError:
            return []
    return []


def _load_feedback_events() -> list[tuple[int, str, int, list[str]]]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT draw_no, brain_tag, matched_count, missed_patterns
            FROM testlotto_brain_review
            WHERE brain_tag IN ('stat','markov','review')
            ORDER BY draw_no ASC, brain_tag ASC
            """
        ).fetchall()
    finally:
        conn.close()
    events = []
    for r in rows:
        dn = int(r["draw_no"] if hasattr(r, "keys") else r[0])
        tag = str(r["brain_tag"] if hasattr(r, "keys") else r[1])
        matched = int(r["matched_count"] if hasattr(r, "keys") else r[2] or 0)
        missed = _parse_missed(
            r["missed_patterns"] if hasattr(r, "keys") else r[3]
        )
        events.append((dn, tag, matched, missed))
    return events


def ensure_history_built() -> dict[str, list[tuple[int, dict[str, Any]]]]:
    """한 번만 재생해 brain별 (draw_no, state_after) 리스트 구축."""
    global _history_cache
    if _history_cache is not None:
        return _history_cache

    states = {tag: _empty_state() for tag in PREDICT_BRAIN_TAGS}
    hist: dict[str, list[tuple[int, dict[str, Any]]]] = {
        tag: [] for tag in PREDICT_BRAIN_TAGS
    }
    events = _load_feedback_events()
    # group by draw_no
    by_draw: dict[int, list[tuple[str, int, list[str]]]] = {}
    for dn, tag, matched, missed in events:
        by_draw.setdefault(dn, []).append((tag, matched, missed))

    for dn in sorted(by_draw):
        for tag, matched, missed in by_draw[dn]:
            if tag not in states:
                continue
            states[tag] = apply_feedback_pure(states[tag], dn, matched, missed)
            hist[tag].append((dn, copy.deepcopy(states[tag])))

    _history_cache = hist
    return hist


def rebuild_state_as_of(brain_tag: str, as_of_draw_no: int) -> dict[str, Any]:
    """draw_no < as_of_draw_no 피드백만 반영된 상태."""
    hist = ensure_history_built()
    series = hist.get(brain_tag) or []
    chosen = None
    for dn, st in series:
        if dn < as_of_draw_no:
            chosen = st
        else:
            break
    return copy.deepcopy(chosen) if chosen is not None else _empty_state()


def try_load_cutoff(brain_tag: str) -> dict[str, Any] | None:
    """컷오프 상태 또는 None(→ 호출부가 전역 폴백)."""
    if not cutoff_enabled():
        return None
    as_of = get_learn_as_of()
    if as_of is None:
        return None
    try:
        return rebuild_state_as_of(brain_tag, int(as_of))
    except Exception:
        return None
