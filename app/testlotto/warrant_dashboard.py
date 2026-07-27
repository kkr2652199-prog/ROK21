# -*- coding: utf-8 -*-
"""K-P1: 명분·제약·학습키 대시보드 (표시 전용 · 산출 로직 무관).

SSOT: My_Drive_Sync/SUMMARY/WARRANT.md · PINNED_BASELINE.md
"""
from __future__ import annotations

import os
from typing import Any

from app.testlotto.brains.registry import ALL_BRAINS, get_brain_meta
from app.testlotto.brains.warrant import get_brain_warrant
from app.testlotto.learn_state import BOOST_CAPS, DEFAULT_ADJUSTMENTS, PREDICT_BRAIN_TAGS
from app.testlotto.learn_state_cutoff import cutoff_enabled, get_learn_as_of, set_learn_as_of
from app.testlotto.models import get_lotto_db
from app.testlotto.ticket_dedup import dedup_enabled

BASELINE_PIN = "640cb67"

# K-AG 배선: 키 → 소비 뇌(표시용)
LEARN_KEY_WIRING: dict[str, str] = {
    "carry_over_boost": "stat",
    "ending_digit_boost": "stat",
    "overdue_boost": "stat",
    "pair_boost": "pattern_aux",
    "consecutive_boost": "pattern_aux",
    "odd_even_balance": "balance_aux",
}

FROZEN_TOKENS = [
    "random.choices (predict_statistical)",
    "_get_draws_before",
    "boost 상한 (carry 0.2 / ending 0.3 / overdue 0.2)",
]


def _max_draw_no() -> int | None:
    conn = get_lotto_db()
    try:
        row = conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()
        return int(row[0]) if row and row[0] is not None else None
    finally:
        conn.close()


def _load_learn_adjustments(brain_tag: str, as_of: int) -> dict[str, float]:
    from app.testlotto.learn_state import load_learn_state

    prev = get_learn_as_of()
    set_learn_as_of(int(as_of))
    try:
        st = load_learn_state(brain_tag)
        adj = st.get("adjustments") or {}
        out = dict(DEFAULT_ADJUSTMENTS)
        for k in DEFAULT_ADJUSTMENTS:
            try:
                out[k] = float(adj.get(k, 0.0) or 0.0)
            except (TypeError, ValueError):
                out[k] = 0.0
        return out
    finally:
        set_learn_as_of(prev)


def build_warrant_dashboard(as_of: int | None = None) -> dict[str, Any]:
    """명분·게이트·학습키 스냅샷 (READ-ONLY)."""
    warrant = get_brain_warrant()
    max_d = _max_draw_no()
    effective_as_of = int(as_of) if as_of and as_of > 0 else (max_d + 1 if max_d else 1)

    learn_by_brain: dict[str, dict[str, float]] = {}
    if cutoff_enabled():
        for tag in PREDICT_BRAIN_TAGS:
            try:
                learn_by_brain[tag] = _load_learn_adjustments(tag, effective_as_of)
            except ValueError:
                learn_by_brain[tag] = dict(DEFAULT_ADJUSTMENTS)
    else:
        from app.testlotto.learn_state import load_learn_state

        for tag in PREDICT_BRAIN_TAGS:
            try:
                st = load_learn_state(tag)
                adj = st.get("adjustments") or {}
                learn_by_brain[tag] = {
                    k: float(adj.get(k, 0.0) or 0.0) for k in DEFAULT_ADJUSTMENTS
                }
            except Exception:
                learn_by_brain[tag] = dict(DEFAULT_ADJUSTMENTS)

    predict_adjustments: dict[str, dict[str, float]] = {}
    for tag in PREDICT_BRAIN_TAGS:
        predict_adjustments[tag] = learn_by_brain.get(tag, dict(DEFAULT_ADJUSTMENTS))

    brains: list[dict[str, Any]] = []
    for meta in ALL_BRAINS:
        tag = meta["tag"]
        role = meta.get("role", "")
        w = warrant.get(tag, {})

        learn_keys: list[dict[str, Any]] = []
        if role == "predict":
            adj = predict_adjustments.get(tag, {})
            for key in DEFAULT_ADJUSTMENTS:
                cap = BOOST_CAPS.get(key)
                learn_keys.append(
                    {
                        "key": key,
                        "value": round(float(adj.get(key, 0) or 0), 4),
                        "cap": cap,
                        "wired_to": tag,
                    }
                )
        else:
            for key, owner in LEARN_KEY_WIRING.items():
                if owner != tag:
                    continue
                cap = BOOST_CAPS.get(key)
                sample = {
                    pt: round(float(predict_adjustments[pt].get(key, 0) or 0), 4)
                    for pt in PREDICT_BRAIN_TAGS
                }
                learn_keys.append(
                    {
                        "key": key,
                        "value": max(sample.values()) if sample else 0.0,
                        "cap": cap,
                        "wired_to": tag,
                        "per_predict_brain": sample,
                    }
                )

        brains.append(
            {
                **get_brain_meta(tag),
                "warrant_label": w.get("label", "미정의"),
                "warrant_evidence": w.get("evidence", ""),
                "warrant_p": w.get("p"),
                "kw_alignment": w.get("kw_alignment"),
                "source_ids": w.get("source_ids") or [],
                "learn_keys": learn_keys,
            }
        )

    ctx_as_of = get_learn_as_of()

    return {
        "baseline_pin": BASELINE_PIN,
        "head_note": os.environ.get("ROK21_BASELINE_PIN_DOC", BASELINE_PIN),
        "evaluation_axis": "적중↑ 폐기 · 명분=WARRANT · 1등확률 동일",
        "structure": "3예측(stat/markov/review) + 4보조(miss/pattern/balance/referee)",
        "gates": {
            "learn_cutoff": cutoff_enabled(),
            "dedup": dedup_enabled(),
            "learn_as_of": effective_as_of,
            "context_learn_as_of": ctx_as_of,
            "db_max_draw": max_d,
        },
        "frozen": FROZEN_TOKENS,
        "learn_key_wiring": LEARN_KEY_WIRING,
        "predict_adjustments": predict_adjustments,
        "brains": brains,
    }
