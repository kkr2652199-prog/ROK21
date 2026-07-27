# -*- coding: utf-8 -*-
"""뇌 명분(warrant) 라벨 — 표시 전용. 산출·dedup 로직과 무관.

SSOT 문서: My_Drive_Sync/SUMMARY/WARRANT.md
UI 노출 금지. 예측 응답 out['brain_warrant'] 데이터만 적재.
"""
from __future__ import annotations

from typing import Any

# label: 실증 | 전제실증·구현미검증 | 기각 | 미정의
BRAIN_WARRANT: dict[str, dict[str, Any]] = {
    "stat": {
        "label": "기각",
        "evidence": "K-Q 볼빈도 균등 χ² p=0.965 → 빈도 전제 미입증; K-W 산출은 당첨분포(A) 쪽 근접(무해·정합 경향)",
        "p": 0.965,
        "source_ids": ["K-Q", "K-W"],
        "kw_alignment": "정합_A근접",
    },
    "markov": {
        "label": "기각",
        "evidence": "K-T lag1 중복 χ² p=0.764 → 회차의존 전제 기각; K-W 산출은 균등(C) 근접(명분없으나 무해)",
        "p": 0.764,
        "source_ids": ["K-T", "K-W"],
        "kw_alignment": "무해_C근접",
    },
    "review": {
        "label": "기각",
        "evidence": "K-T 이월(lag1 대리) p=0.764 → 전제 기각; K-W 전반 C근접·끝수 지표는 A·C 양쪽 원격(편향경보)",
        "p": 0.764,
        "source_ids": ["K-T", "K-W"],
        "kw_alignment": "무해_C근접_끝수편향경보",
    },
    "miss_aux": {
        "label": "기각",
        "evidence": "K-T 간격 χ² p=0.483 → 기하 이탈 주장 미입증(기하 부합)",
        "p": 0.483,
        "source_ids": ["K-T"],
        "kw_alignment": None,
    },
    "pattern_aux": {
        "label": "실증",
        "evidence": (
            "K-T 형태 이론부합 p≥0.13 ∧ K-AA 구현검증: ac_target=8(최빈)·"
            "consec PMF단조점수·배선 PASS(composite 항등·ablation conf 변화)"
        ),
        "p": 0.13,
        "source_ids": ["K-T", "K-Z", "K-AA"],
        "kw_alignment": "무해_C근접",
    },
    "balance_aux": {
        "label": "실증",
        "evidence": (
            "K-T 균형 이론부합 p≥0.13 ∧ K-AA 구현검증: 폴백합=138·"
            "합거리 단조감소·LMH(2,2,2) 최고점(zone_score)"
        ),
        "p": 0.13,
        "source_ids": ["K-T", "K-Z", "K-AA"],
        "kw_alignment": "정합_A근접",
    },
    "referee_aux": {
        "label": "미정의",
        "evidence": "추첨 생성 전제 아님(메타가중 정책). 전달효율은 K-M/K-N HOLD · K-Y 기여0",
        "p": None,
        "source_ids": ["K-T", "K-M", "K-N", "K-Y"],
        "kw_alignment": None,
    },
}


def get_brain_warrant() -> dict[str, dict[str, Any]]:
    """예측 응답용 복사본. UI 노출 금지 — 데이터 적재만."""
    return {k: dict(v) for k, v in BRAIN_WARRANT.items()}
