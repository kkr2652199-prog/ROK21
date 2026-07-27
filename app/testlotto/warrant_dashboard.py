# -*- coding: utf-8 -*-
"""K-P1/P2: 명분·제약·학습키·기각뇌 표시 (표시 전용 · 산출 로직 무관).

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

# K-P2: 라벨별 UI 역할 (WARRANT §0~§2)
LABEL_DISPLAY: dict[str, dict[str, Any]] = {
    "실증": {
        "short": "명분 실증",
        "role_line": "전제 실증·구현 검증. 제약·형태 점수에 기여.",
        "tab_hint": "실증 — 제약 명분",
    },
    "기각": {
        "short": "명분 없음·무해",
        "role_line": "전제 미입증. 당첨확률 동일. 조합 다양성·설명·차후 배선용 유지.",
        "tab_hint": "기각 — 제거 안 함",
    },
    "미정의": {
        "short": "명분 미정의",
        "role_line": "메타 정책. 성적 가중 전달효율 미검증(K-M). 채점 보조.",
        "tab_hint": "미정의 — 메타",
    },
    "전제실증·구현미검증": {
        "short": "전제만 실증",
        "role_line": "draws/이론 OK · 모듈 구현 미검증.",
        "tab_hint": "구현미검증",
    },
}

REJECTED_BRAIN_POLICY: dict[str, Any] = {
    "id": "WARRANT-2",
    "title": "기각·무효 뇌를 제거하지 않는 이유",
    "summary": (
        "확률이 조합불변이므로 명분 없는/기여 0인 산출도 당첨확률은 동일하다. "
        "조합 다양성·설명 문자열·차후 배선에 기여할 수 있다. 제거·비활성은 형 승인 전 금지."
    ),
    "remove_brains_allowed": False,
    "hit_rate_optimization": False,
    "labels_legend": [
        {"label": "실증", "meaning": "전제 실증 + 모듈 구현 검증"},
        {"label": "기각", "meaning": "전제 미입증 · 무해 유지"},
        {"label": "미정의", "meaning": "메타·정책 · 검증 대기"},
    ],
}


def _brain_display_hint(tag: str, label: str, kw_alignment: str | None, role: str) -> dict[str, Any]:
    base = dict(LABEL_DISPLAY.get(label, LABEL_DISPLAY["미정의"]))
    hint = {
        **base,
        "warrant_label": label,
        "kw_alignment": kw_alignment,
        "brain_role": role,
        "removal_allowed": False,
    }
    if tag == "review" and kw_alignment and "끝수" in str(kw_alignment):
        hint["warning"] = "끝수 편향 경보(K-X). 교정은 형 승인 후(P3)."
    if tag == "miss_aux":
        hint["contrib_note"] = "순위 기여 ≈0 (K-Y) · 경고 신호용"
    if tag == "referee_aux":
        hint["contrib_note"] = "가중 실효 ≈균등 (K-M HOLD)"
    return hint


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

        lbl = w.get("label", "미정의")
        kw = w.get("kw_alignment")
        brains.append(
            {
                **get_brain_meta(tag),
                "warrant_label": lbl,
                "warrant_evidence": w.get("evidence", ""),
                "warrant_p": w.get("p"),
                "kw_alignment": kw,
                "source_ids": w.get("source_ids") or [],
                "learn_keys": learn_keys,
                "display_hint": _brain_display_hint(tag, lbl, kw, role),
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
        "rejected_brain_policy": REJECTED_BRAIN_POLICY,
        "label_display": LABEL_DISPLAY,
        "brains": brains,
    }
