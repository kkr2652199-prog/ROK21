# -*- coding: utf-8 -*-
"""k_gate — 판정 게이트 공용 모듈 (R38).

목적
----
ROK21 테스트로또의 튜닝 판정은 대부분 `ge3`(5장 중 최고가 3개 이상 맞을 비율)로
내려왔다. 그런데 그 지표의 **분해능**을 확정하지 않은 채 판정해왔다.

  · 같은 파라미터·같은 데이터에서 seed만 바꿔도 ge3 는 0.09~0.23 (폭 0.14)
  · n=50 에서 10셀을 훑으면 **순수 잡음만으로** Δ 0.16 이 나온다
  · 그런데도 Δ 0.0008 짜리 차이를 "후보"로 올려왔다

이 모듈은 그 눈금을 계산하고, 판정을 자동으로 등급화한다.
**모든 튜닝·비교 도구는 벤치 JSON 에 `gate_block(...)` 결과를 넣어야 한다.**

사용법
------
    from tools.k_gate import gate_block

    payload["decision_gate"] = gate_block(
        n=200, k_cells=9, delta=0.012, metric="ge3",
        holdout_value=0.118, label="short_decay 스윕",
    )

`verdict` 가 DECIDABLE 이 아니면 그 판정은 **"차이 없음"** 으로 보고해야 한다.

정책
----
순수 계산 모듈. DB·파일·전역상태를 건드리지 않는다. 발권 경로와 무관하다.
"""
from __future__ import annotations

import math
from math import comb
from typing import Any

import numpy as np

__all__ = [
    "GATE_KEY",
    "GATE_RULE",
    "classify",
    "gate",
    "gate_block",
    "null_ge3",
    "p_single_ge3",
    "se_binom",
]

GATE_KEY = "decision_gate"
GATE_RULE = "R38"

M_TOTAL = 45
M_DRAWN = 6
DEFAULT_TICKETS = 5

MC_B = 40000
MC_SEED = 20260808

# 판정 등급
DECIDABLE = "DECIDABLE"
SELECTION_SUSPECT = "SELECTION_SUSPECT"
UNDECIDABLE = "UNDECIDABLE"
NOISE_SELECTION_CONFIRMED = "NOISE_SELECTION_CONFIRMED"


def hyper_pmf(k: int, *, total: int = M_TOTAL, drawn: int = M_DRAWN) -> float:
    """1장으로 정확히 k개 맞을 확률 (초기하분포)."""
    if k < 0 or k > drawn:
        return 0.0
    return comb(drawn, k) * comb(total - drawn, drawn - k) / comb(total, drawn)


def p_single_ge3() -> float:
    """1장이 3개 이상 맞을 확률."""
    return sum(hyper_pmf(k) for k in range(3, M_DRAWN + 1))


def null_ge3(n_tickets: int = DEFAULT_TICKETS) -> float:
    """서로 독립인 n장 중 최고가 3개 이상일 확률 (= ge3 의 null).

    20260730 몬테카를로 측정치와 소수 넷째 자리까지 일치한다
    (5장 0.113624 vs 0.1137 · 15장 0.303607 vs 0.3036).
    """
    return 1.0 - (1.0 - p_single_ge3()) ** n_tickets


def se_binom(p: float, n: int) -> float:
    """비율 추정치의 이항 표준오차."""
    if n <= 0:
        raise ValueError("n must be positive")
    return math.sqrt(p * (1.0 - p) / n)


def mc_selection(
    n: int, k_cells: int, p0: float, *, b: int = MC_B, seed: int = MC_SEED
) -> dict[str, float]:
    """K셀 중 최선을 골랐을 때 순수 잡음이 만드는 (최선 − 기준셀) Δ 분포.

    최선을 고르는 행위는 한쪽 방향만 보므로 여기서 얻는 분위는 **단측**이다.
    """
    rng = np.random.default_rng(seed + n * 131 + k_cells)
    base = rng.binomial(n, p0, size=b) / n
    cells = rng.binomial(n, p0, size=(b, max(1, k_cells))) / n
    delta = cells.max(axis=1) - base
    return {
        "delta_mean": float(delta.mean()),
        "delta_p50": float(np.quantile(delta, 0.50)),
        "delta_p95": float(np.quantile(delta, 0.95)),
        "delta_p99": float(np.quantile(delta, 0.99)),
    }


def gate(n: int, k_cells: int, p0: float | None = None) -> dict[str, Any]:
    """판정 눈금.

    n        : 평가 회차 수
    k_cells  : 그 판정에서 비교·탐색한 셀(설정) 개수. 그리드 전체를 세야 한다.
    p0       : null 비율. 생략하면 ge3(5장) null.

    반환 `mdd_selection_p95` 를 넘지 못한 Δ 는 '차이 없음'으로 보고한다.
    """
    p = null_ge3() if p0 is None else p0
    se = se_binom(p, n)
    sel = mc_selection(n, k_cells, p)
    return {
        "n": n,
        "k_cells": k_cells,
        "p0": round(p, 6),
        "se_single": round(se, 6),
        "ci95_halfwidth": round(1.96 * se, 6),
        "mdd_single_pair": round(1.96 * se * math.sqrt(2.0), 6),
        "mdd_selection_p95": round(sel["delta_p95"], 6),
        "mdd_selection_p99": round(sel["delta_p99"], 6),
        "noise_delta_expected": round(sel["delta_mean"], 6),
    }


def classify(
    delta: float,
    n: int,
    k_cells: int,
    *,
    p0: float | None = None,
    holdout_value: float | None = None,
) -> dict[str, Any]:
    """Δ 를 눈금에 대고 등급화.

    holdout_value 를 주면, 그 값이 null 95% 신뢰구간 안으로 붕괴했는지 함께 본다.
    붕괴했다면 튜닝창의 Δ 가 아무리 커도 선택잡음으로 확정한다.
    """
    g = gate(n, k_cells, p0)
    ad = abs(float(delta))

    collapsed: bool | None = None
    if holdout_value is not None:
        collapsed = abs(float(holdout_value) - g["p0"]) < g["ci95_halfwidth"]

    if collapsed:
        verdict = NOISE_SELECTION_CONFIRMED
        why = (
            f"홀드아웃 {holdout_value} 가 null {g['p0']} 의 95% 구간(±{g['ci95_halfwidth']}) "
            "안으로 붕괴 → 선택잡음으로 확정"
        )
    elif ad < g["mdd_single_pair"]:
        verdict = UNDECIDABLE
        why = (
            f"|Δ|={ad:.6f} < 단일비교 최소검출차 {g['mdd_single_pair']} "
            f"(n={n}) → 차이 주장 불가"
        )
    elif ad < g["mdd_selection_p95"]:
        verdict = SELECTION_SUSPECT
        why = (
            f"|Δ|={ad:.6f} < {k_cells}셀 탐색 시 잡음 p95 {g['mdd_selection_p95']} "
            "→ 순수 잡음이 만들 수 있는 범위 · 근거 불충분"
        )
    else:
        verdict = DECIDABLE
        why = (
            f"|Δ|={ad:.6f} ≥ 선택보정 임계 {g['mdd_selection_p95']} "
            f"({k_cells}셀) → 차이 주장 가능"
        )

    return {
        "gate": g,
        "delta": round(float(delta), 6),
        "holdout_value": holdout_value,
        "holdout_collapsed": collapsed,
        "verdict": verdict,
        "why_ko": why,
        "actionable": verdict == DECIDABLE,
    }


def gate_block(
    *,
    n: int,
    k_cells: int,
    delta: float,
    metric: str = "ge3",
    p0: float | None = None,
    holdout_value: float | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    """벤치 JSON 에 그대로 넣는 블록. 키 이름은 `GATE_KEY`(=decision_gate) 로.

    `actionable` 이 False 이면 그 판정은 '차이 없음' 으로 보고해야 한다.
    """
    out = classify(delta, n, k_cells, p0=p0, holdout_value=holdout_value)
    out.update(
        {
            "rule": GATE_RULE,
            "metric": metric,
            "label": label,
            "module": "tools/k_gate.py",
            "report_as_ko": (
                "차이 있음" if out["actionable"] else "차이 없음 (눈금 미달)"
            ),
        }
    )
    return out


def self_test() -> dict[str, Any]:
    """모듈이 확정 수치를 재현하는지 검증. 실패하면 게이트를 신뢰하지 말 것."""
    checks: list[dict[str, Any]] = []

    def add(name: str, got: float, want: float, tol: float) -> None:
        checks.append(
            {
                "name": name,
                "got": round(got, 8),
                "want": want,
                "tol": tol,
                "pass": abs(got - want) <= tol,
            }
        )

    add("null_ge3(5) vs 20260730 측정", null_ge3(5), 0.1137, 5e-4)
    add("null_ge3(15) vs 20260730 측정", null_ge3(15), 0.3036, 5e-4)
    add("p_single_ge3 해석값", p_single_ge3(), 0.02383408, 1e-7)
    add("pmf 합 = 1", sum(hyper_pmf(k) for k in range(0, 7)), 1.0, 1e-12)

    g = gate(50, 10)
    add("n50 SE", g["se_single"], 0.044881, 1e-5)
    add("n50 단일 MDD", g["mdd_single_pair"], 0.124403, 1e-5)
    add("n50·K10 선택보정 p95", g["mdd_selection_p95"], 0.16, 1e-6)

    # 적용상수 win26/mix0.8 은 반드시 NOISE_SELECTION_CONFIRMED 로 나와야 한다
    c = classify(0.16, 50, 10, holdout_value=0.14)
    checks.append(
        {
            "name": "win26/mix0.8 재판정",
            "got": c["verdict"],
            "want": NOISE_SELECTION_CONFIRMED,
            "tol": 0,
            "pass": c["verdict"] == NOISE_SELECTION_CONFIRMED,
        }
    )

    return {
        "all_pass": all(bool(c["pass"]) for c in checks),
        "n_checks": len(checks),
        "checks": checks,
    }
