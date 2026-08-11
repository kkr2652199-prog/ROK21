# -*- coding: utf-8 -*-
"""뇌별 독립 감독관 엔진 (K-REFEREE-BY-BRAIN).

원칙
  · 공유 허용 = lotto_draws(과거) + 해당 뇌의 learn_state 만
  · 뇌 A의 set_score / raw 는 뇌 B·C 성적에 의존하지 않음
  · 발권 quota 용 정규화 가중만 3뇌를 모아 상대화 (coordinator 메타)

K-M 식 유지: raw = max(floor, 1 + GAIN×(avg−baseline))
노브는 뇌별 dict — 값은 당분간 동일(구조 분리), 튜닝은 게이트 후.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PREDICT_TAGS = ("stat", "markov", "review")


@dataclass(frozen=True)
class BrainRefereeEngine:
    """한 예측뇌 전용 감독관."""

    brain_tag: str
    role_ko: str
    gain: float = 2.5
    baseline: float = 0.8
    floor: float = 0.15
    # set_score: avg→[0,1] 로컬 매핑 (교차정규화 금지)
    set_scale: float = 0.75

    def raw_from_avg(self, recent_avg_match: float, *, review_count: int = 0) -> float:
        if int(review_count or 0) <= 0:
            return 1.0  # 학습 없으면 중립 raw (정규화 시 균등)
        avg = float(recent_avg_match or 0.0)
        return max(self.floor, 1.0 + self.gain * (avg - self.baseline))

    def set_score_from_avg(self, recent_avg_match: float, *, review_count: int = 0) -> float:
        """이 뇌만의 감독 점수 0~1. 다른 뇌 상태 불필요."""
        if int(review_count or 0) <= 0:
            return 0.5
        avg = float(recent_avg_match or 0.0)
        return min(1.0, max(0.0, 0.5 + self.set_scale * (avg - self.baseline)))

    def describe_line(self, recent_avg_match: float, *, review_count: int = 0) -> str:
        s = self.set_score_from_avg(recent_avg_match, review_count=review_count)
        return (
            f"{self.brain_tag}감독({self.role_ko}):"
            f"avg={float(recent_avg_match or 0):.3f} score={s:.2f} n={int(review_count or 0)}"
        )


# 뇌별 엔진 — 파일/상수 분리 SSOT. 값 차별화는 별도 게이트.
ENGINES: dict[str, BrainRefereeEngine] = {
    "stat": BrainRefereeEngine("stat", "과거학습감독"),
    "markov": BrainRefereeEngine("markov", "선호번호감독"),
    "review": BrainRefereeEngine("review", "금액뇌감독"),
}


def get_engine(brain_tag: str) -> BrainRefereeEngine:
    if brain_tag not in ENGINES:
        raise KeyError(f"unknown referee brain_tag={brain_tag!r}")
    return ENGINES[brain_tag]


def knobs_snapshot() -> dict[str, Any]:
    return {
        t: {
            "role_ko": e.role_ko,
            "gain": e.gain,
            "baseline": e.baseline,
            "floor": e.floor,
            "set_scale": e.set_scale,
        }
        for t, e in ENGINES.items()
    }


def independent_scores_from_states(
    states: dict[str, dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """뇌별 로컬 score/raw (교차 정규화 전)."""
    out: dict[str, dict[str, float]] = {}
    for tag in PREDICT_TAGS:
        st = states.get(tag) or {}
        eng = get_engine(tag)
        rc = int(st.get("review_count", 0) or 0)
        avg = float(st.get("recent_avg_match", 0.0) or 0.0)
        out[tag] = {
            "recent_avg_match": avg,
            "review_count": float(rc),
            "raw": eng.raw_from_avg(avg, review_count=rc),
            "set_score": eng.set_score_from_avg(avg, review_count=rc),
        }
    return out


def quota_weights_from_states(states: dict[str, dict[str, Any]]) -> dict[str, float]:
    """발권 quota용 — 뇌별 독립 raw 를 만든 뒤 Σ=1 정규화.

    정규화는 배분 단계일 뿐, 각 raw 계산은 타뇌 상태를 쓰지 않음.
    """
    n = len(PREDICT_TAGS)
    equal = {t: 1.0 / n for t in PREDICT_TAGS}
    indep = independent_scores_from_states(states)
    if all(int(indep[t]["review_count"]) <= 0 for t in PREDICT_TAGS):
        return equal
    raw = {t: float(indep[t]["raw"]) for t in PREDICT_TAGS}
    total = sum(raw.values()) or 1.0
    return {t: raw[t] / total for t in PREDICT_TAGS}
