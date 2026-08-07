# -*- coding: utf-8 -*-
"""K-STAT-DECISION-GATE — 판정 게이트: "우리 자가 몇 밀리까지 재는지" 확정.

문제
----
과거학습 뇌 튜닝은 대부분 `ge3`(5장 중 최고가 3개 이상 맞을 비율)로 판정해왔다.
그런데 우리 자의 눈금 간격을 한 번도 확정하지 않았다:

  · SEED-DIAG: **같은 파라미터·같은 데이터**인데 seed만 바꾸면 ge3 = 0.09~0.23 (폭 0.14)
  · TUNE-ENGINE: n=50 · 10셀 탐색 · 최선 Δ+0.16 → **적용됨**
  · 그 직후 holdout n=50 → 0.14 (null 0.1136 수준으로 붕괴)
  · fusion n=200 → Δ 0.000

눈금이 0.14인 자로 0.0008 차이를 읽어온 것이다. 이 도구는 자의 눈금을 확정하고,
과거 판정 전부를 그 눈금에 대고 다시 읽는다.

구성
----
1. null ge3 **해석적** 계산 (초기하분포) — MC 측정치와 대조
2. n별 이항 표준오차 · 단일비교 최소검출차(MDD)
3. **선택보정 임계값** — K개 셀 중 최선을 고를 때 순수 잡음이 만드는 Δ의 분포 (MC)
4. 과거 판정 소급감사 — DECIDABLE / SELECTION_SUSPECT / UNDECIDABLE
5. `gate(n, k_cells)` — 앞으로 모든 튜닝 도구가 호출해야 하는 재사용 함수
6. **학습 순서 불변성 증명** — 1→1234 vs 1234→1 이 수학적으로 동일함을 수치로 확인

정책
----
READ-ONLY. DB 쓰기 없음 · 코드·가중 변경 없음 · wire 없음.
수치는 전부 docs/benchmarks/*.json 에서 읽거나 이 파일에서 계산한다.

출력
----
  docs/benchmarks/20260808_KSTAT_DECISION_GATE.json
  reports/20260808_KSTAT_DECISION_GATE.md
"""
from __future__ import annotations

import json
import math
import sys
from math import comb, exp
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BENCH_DIR = ROOT / "docs" / "benchmarks"
OUT_JSON = BENCH_DIR / "20260808_KSTAT_DECISION_GATE.json"
OUT_MD = ROOT / "reports" / "20260808_KSTAT_DECISION_GATE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BENCH_ID = "K-STAT-DECISION-GATE"
M_TOTAL, M_DRAWN = 45, 6
MC_B = 40000
MC_SEED = 20260808

# 참조 벤치 (수치 원본)
REF_NULL = "20260730_KSIGNAL_BACKTEST_tail100.json"
REF_SEED = "20260805_KSTAT_SEED_DIAG.json"
REF_TUNE = "20260808_KPAST_LEARN_TUNE_ENGINE.json"
REF_APPLY = "20260808_KPAST_LEARN_TUNE_ENGINE_APPLY.json"
REF_DETAIL = "20260808_KPAST_LEARN_DETAIL_TUNE.json"
REF_FULL = "20260803_KFUTURE_WIRE_FULL.json"


def load_bench(name: str) -> dict[str, Any]:
    return json.loads((BENCH_DIR / name).read_text(encoding="utf-8"))


# ── 1. null 해석적 계산 ────────────────────────────────────────────────
def hyper_pmf(k: int) -> float:
    """1장으로 정확히 k개 맞을 확률 (초기하)."""
    return comb(M_DRAWN, k) * comb(M_TOTAL - M_DRAWN, M_DRAWN - k) / comb(M_TOTAL, M_DRAWN)


def p_single_ge3() -> float:
    return sum(hyper_pmf(k) for k in (3, 4, 5, 6))


def null_ge3(n_tickets: int) -> float:
    """서로 독립인 n장 중 최고가 3개 이상일 확률."""
    p = p_single_ge3()
    return 1.0 - (1.0 - p) ** n_tickets


# ── 2·3. 눈금 계산 ────────────────────────────────────────────────────
def se_binom(p: float, n: int) -> float:
    return math.sqrt(p * (1.0 - p) / n)


def mc_selection(
    n: int, k_cells: int, p0: float, b: int = MC_B, seed: int = MC_SEED
) -> dict[str, float]:
    """K셀 중 최선을 골랐을 때 순수 잡음이 만드는 (최선 − 기준셀) Δ 분포."""
    rng = np.random.default_rng(seed + n * 131 + k_cells)
    base = rng.binomial(n, p0, size=b) / n
    cells = rng.binomial(n, p0, size=(b, k_cells)) / n
    delta = cells.max(axis=1) - base
    return {
        "delta_mean": float(delta.mean()),
        "delta_p50": float(np.quantile(delta, 0.50)),
        "delta_p95": float(np.quantile(delta, 0.95)),
        "delta_p99": float(np.quantile(delta, 0.99)),
    }


def gate(n: int, k_cells: int, p0: float | None = None) -> dict[str, Any]:
    """앞으로 모든 튜닝 도구가 호출할 판정 게이트.

    n        : 평가 회차 수
    k_cells  : 그 판정에서 비교·탐색한 셀(설정) 개수
    반환 mdd_selection_p95 를 넘지 못한 Δ 는 '차이 없음'으로 보고해야 한다.
    """
    p = p0 if p0 is not None else null_ge3(5)
    se = se_binom(p, n)
    sel = mc_selection(n, max(1, k_cells), p)
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


# ── 6. 학습 순서 불변성 증명 ───────────────────────────────────────────
def order_invariance_proof() -> dict[str, Any]:
    """1→N 학습과 N→1 학습이 동일 결과임을 수치로 확인.

    engine._window_freq_norm 은 age(=시간상 위치)로 가중을 정하고 **더한다**.
    덧셈은 교환법칙이 성립하므로 순회 순서는 결과를 바꾸지 않는다.
    반대로 리스트 자체를 뒤집으면 '최근'의 정의가 뒤집혀 1회차가 최신이 되는 버그다.
    """
    from app.testlotto.brains.stat_brain import engine

    conn_rows = _load_draw_rows()
    decay = float(engine.v2_params()["long_decay"])

    forward = engine._window_freq_norm(conn_rows, decay)

    # 같은 age 를 유지하면서 역순으로 누적 (형이 말한 "1234 → 1 학습")
    total = len(conn_rows)
    freq: dict[int, float] = dict.fromkeys(range(1, M_TOTAL + 1), 0.0)
    for idx in range(total - 1, -1, -1):
        d = conn_rows[idx]
        w = exp(-decay * (total - 1 - idx))
        for k in ("num1", "num2", "num3", "num4", "num5", "num6"):
            freq[int(d[k])] += w
    for n in range(1, M_TOTAL + 1):
        if freq[n] <= 0.0:
            freq[n] = 0.1
    tot = sum(freq.values())
    backward = {n: freq[n] / tot for n in range(1, M_TOTAL + 1)}

    max_abs = max(abs(forward[n] - backward[n]) for n in range(1, M_TOTAL + 1))

    # 리스트를 실제로 뒤집으면(=age 재배정) 얼마나 달라지는가 → 버그의 크기
    reversed_list = list(reversed(conn_rows))
    corrupted = engine._window_freq_norm(reversed_list, decay)
    max_abs_corrupt = max(abs(forward[n] - corrupted[n]) for n in range(1, M_TOTAL + 1))

    return {
        "n_draws": total,
        "long_decay": decay,
        "max_abs_diff_forward_vs_backward": float(f"{max_abs:.3e}"),
        "identical": max_abs < 1e-12,
        "max_abs_diff_if_list_reversed": round(max_abs_corrupt, 6),
        "conclusion_ko": (
            "순회 순서(1→N vs N→1)는 결과를 전혀 바꾸지 않는다. "
            "가중치는 age 기반 지수가중의 **합**이고 합은 교환법칙이 성립한다. "
            "리스트를 실제로 뒤집으면 '최근'의 정의가 뒤바뀌어 결과가 달라지지만, "
            "그것은 학습 방향이 아니라 시간축 손상(버그)이다."
        ),
    }


def _load_draw_rows() -> list[dict[str, Any]]:
    import sqlite3

    conn = sqlite3.connect(str(ROOT / "data" / "lotto_testlotto.db"))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 4. 소급감사 ───────────────────────────────────────────────────────
def _verdict(delta: float, g: dict[str, Any], holdout_collapsed: bool) -> tuple[str, str]:
    ad = abs(delta)
    if holdout_collapsed:
        return (
            "NOISE_SELECTION_CONFIRMED",
            "홀드아웃에서 null 수준으로 붕괴 → 선택잡음으로 확정",
        )
    if ad < g["mdd_single_pair"]:
        return ("UNDECIDABLE", "단일비교 최소검출차 미달 → 차이 주장 불가")
    if ad < g["mdd_selection_p95"]:
        return ("SELECTION_SUSPECT", "K셀 탐색 시 순수잡음이 만들 수 있는 범위 → 근거 불충분")
    return ("DECIDABLE", "선택보정 임계값 초과 → 차이 주장 가능")


def retro_audit(p0: float, seed_range: float) -> list[dict[str, Any]]:
    tune = load_bench(REF_TUNE)
    apply_ = load_bench(REF_APPLY)
    detail = load_bench(REF_DETAIL)
    seed = load_bench(REF_SEED)
    full = load_bench(REF_FULL)

    items: list[dict[str, Any]] = []

    # (1) TUNE-ENGINE — 실제로 적용된 판정
    n1 = 50
    k1 = int(tune["n_cells"])
    d1 = float(tune["best"]["delta_ge3_vs_base"])
    g1 = gate(n1, k1, p0)
    hold_ge3 = float(apply_["holdout_n50"]["ge3_rate"])
    collapsed = abs(hold_ge3 - p0) < g1["ci95_halfwidth"]
    v1, why1 = _verdict(d1, g1, collapsed)
    items.append(
        {
            "id": "K-PAST-LEARN-TUNE-ENGINE (win26/mix0.8) — live 적용됨",
            "source": f"docs/benchmarks/{REF_TUNE}, {REF_APPLY}",
            "n": n1,
            "k_cells": k1,
            "claim_ko": f"base ge3 {tune['base_cell']['ge3_rate']} → best {tune['best']['ge3_rate']}",
            "delta": d1,
            "gate": g1,
            "holdout_ge3": hold_ge3,
            "holdout_vs_null": round(hold_ge3 - p0, 6),
            "holdout_collapsed": collapsed,
            "fusion_delta": float(apply_["fusion_n200"]["delta_vs_baseline"]),
            "verdict": v1,
            "why_ko": why1,
        }
    )

    # (2) DETAIL-TUNE — 후보 미채택
    n2 = 50
    k2 = len(detail.get("rows") or []) or 9
    # 이 판정의 실제 선택 기준은 tune/hold 결합 score 였다
    d2 = round(float(detail["best"]["score"]) - float(detail["base_cell"]["score"]), 6)
    g2 = gate(n2, k2, p0)
    v2, why2 = _verdict(d2, g2, False)
    items.append(
        {
            "id": "K-PAST-LEARN-DETAIL-TUNE (decay) — 미채택",
            "source": f"docs/benchmarks/{REF_DETAIL}",
            "n": n2,
            "k_cells": k2,
            "claim_ko": (
                f"선택기준 score {detail['base_cell']['score']} → {detail['best']['score']} "
                f"(tune_ge3 {detail['base_cell']['tune_ge3']}→{detail['best']['tune_ge3']} · "
                f"hold_ge3 {detail['base_cell']['hold_ge3']}→{detail['best']['hold_ge3']})"
            ),
            "delta": d2,
            "tune_ge3_delta": round(
                float(detail["best"]["tune_ge3"]) - float(detail["base_cell"]["tune_ge3"]), 6
            ),
            "gate": g2,
            "fusion_delta": float(detail["fusion_best"]["delta_vs_baseline"]),
            "verdict": v2,
            "why_ko": why2,
        }
    )

    # (3) SEED-DIAG — 잡음 하한 그 자체
    ssum = seed["stat"]["summary"]
    g3 = gate(int(seed["n_draws"]), len(seed["seeds_tested"]), p0)
    items.append(
        {
            "id": "K-STAT-SEED-DIAG — 잡음 하한 실측",
            "source": f"docs/benchmarks/{REF_SEED}",
            "n": int(seed["n_draws"]),
            "k_cells": len(seed["seeds_tested"]),
            "claim_ko": (
                f"동일 파라미터·동일 데이터 · seed만 변경 → ge3 "
                f"{ssum['min_ge3']}~{ssum['max_ge3']} (std {ssum['std_ge3']})"
            ),
            "delta": float(ssum["range_ge3"]),
            "gate": g3,
            "verdict": "NOISE_FLOOR",
            "why_ko": (
                f"이론 이항 SE={g3['se_single']} 인데 seed만으로 표준편차 {ssum['std_ge3']} "
                f"· 폭 {ssum['range_ge3']} 발생 → 파이프라인이 이항잡음 이상을 더한다"
            ),
        }
    )

    # (4) FULL WF — 유일한 대표본 판정
    ov = full["overall"]
    g4 = gate(int(ov["n"]), 1, p0)
    d4 = float(ov["delta_ge3_vs_null"])
    v4, why4 = _verdict(d4, g4, False)
    items.append(
        {
            "id": "K-FUTURE-WIRE-FULL — 전구간 walk-forward",
            "source": f"docs/benchmarks/{REF_FULL}",
            "n": int(ov["n"]),
            "k_cells": 1,
            "claim_ko": f"ge3 {ov['ge3_rate']} vs null {round(p0, 4)} (p={ov.get('p_value')})",
            "delta": d4,
            "gate": g4,
            "verdict": v4,
            "why_ko": why4,
        }
    )
    _ = seed_range
    return items


def ruler_table(p0: float) -> list[dict[str, Any]]:
    out = []
    for n in (50, 100, 135, 200, 500, 900, 1182):
        for k in (1, 9, 10, 15):
            out.append(gate(n, k, p0))
    return out


# ── 보고서 ────────────────────────────────────────────────────────────
def build_report(p: dict[str, Any]) -> str:
    nl = p["null_analytic"]
    oi = p["order_invariance"]
    lines = [
        f"# {BENCH_ID} — 판정 게이트: 우리 자의 눈금 확정",
        "",
        f"- 날짜: {p['date']} · 범위: {p['scope']}",
        f"- **판정: {p['verdict']['code']} — {p['verdict']['headline_ko']}**",
        "- 정책: READ-ONLY · DB 쓰기 없음 · 코드·가중 무변경 · wire=False",
        "",
        "## 1. 형 질문에 대한 답 — 학습 순서(1→1234 vs 1234→1)",
        "",
        f"**결론: 순서는 결과를 전혀 바꾸지 않는다.** (수치 확인: 최대 절대차 = `{oi['max_abs_diff_forward_vs_backward']}`)",
        "",
        "이유는 엔진 코드에 있다. `engine._window_freq_norm` 은 각 회차의 **나이(age)** 로",
        "가중을 정하고 그것을 **더한다**.",
        "",
        "```",
        "weight[번호] = Σ  exp(−decay × age(회차))",
        "```",
        "",
        "덧셈은 교환법칙이 성립하므로, 1회차부터 더하든 1234회차부터 더하든 합은 같다.",
        f"실제로 두 방식의 최대 차이는 `{oi['max_abs_diff_forward_vs_backward']}` (부동소수 오차 수준)이고,",
        f"동일 판정 = **{oi['identical']}** 이다. (n={oi['n_draws']} · decay={oi['long_decay']})",
        "",
        "다만 리스트를 **실제로 뒤집으면** 결과가 달라진다"
        f" (최대차 `{oi['max_abs_diff_if_list_reversed']}`). 그건 '역방향 학습'이 아니라",
        "1회차를 최신으로 착각하게 만드는 **시간축 손상(버그)** 이다. 학습 방향으로 얻을 것은 없다.",
        "",
        "## 2. 형 질문에 대한 답 — 「1234=문제 / 1235=답」 구조",
        "",
        "이 프레임은 정확하고, **이미 앱에 구현되어 측정까지 끝났다.**",
        "`transition_log` 테이블이 바로 그것이다: `anchor_nums`(=문제) → `next_actual`(=답) → `hit_count`(=채점), n=1134.",
        "",
        "결과가 결정적이다.",
        "",
        "| 방식 | mean_hit | top15 ge3 | 비교 |",
        "|---|---|---|---|",
    ]
    tr = p["problem_answer_frame"]
    lines += [
        f"| 컨닝 포함 (peek) | {tr['peek_mean_hit']} | {tr['peek_ge3']} | 겉보기 강함 |",
        f"| **컨닝 없음 (nopeek · 발권 가능 경로)** | **{tr['nopeek_mean_hit']}** | **{tr['nopeek_ge3']}** | 무작위 top15 = {tr['random_ge3']} |",
        "",
        f"즉 컨닝을 막으면 무작위(**{tr['random_ge3']}**)보다 **오히려 낮다**({tr['nopeek_ge3']}).",
        "'문제→답' 학습기는 이미 정직하게 채점됐고, 통과하지 못했다.",
        f"근거: `docs/benchmarks/{tr['source']}`",
        "",
        "## 3. 그럼 무엇이 문제였나 — 자의 눈금",
        "",
        "### 3-A. null 을 해석적으로 검증했다",
        "",
        "| 항목 | 해석적 계산 | 측정 벤치 | 일치 |",
        "|---|---|---|---|",
        f"| 1장 P(≥3) | {nl['p_single_ge3']} | — | — |",
        f"| 5장 중 최고 ge3 | **{nl['null_ge3_best_of_5']}** | {nl['measured_best_of_5']} | {nl['match_best_of_5']} |",
        f"| 15장 중 최고 ge3 | {nl['null_ge3_best_of_15']} | {nl['measured_best_of_15']} | {nl['match_best_of_15']} |",
        "",
        "초기하분포로 계산한 값이 몬테카를로 측정치와 소수 넷째 자리까지 같다.",
        "**null 기준선은 신뢰할 수 있다.** 문제는 null 이 아니라 우리 관측의 정밀도였다.",
        "",
        "### 3-B. 눈금표 (ge3 기준 · p0=%s)" % nl["null_ge3_best_of_5"],
        "",
        "`단일비교 MDD` = 사전에 정한 두 설정을 비교할 때 필요한 최소 Δ (양측 95%).",
        "`선택보정 p95` = K개 셀 중 **최선을 골랐을 때** 순수 잡음만으로 나오는 Δ의 95분위 (단측).",
        "최선을 고르는 행위는 한쪽 방향만 보므로 단측이 맞다. 그래서 K=1 일 때는 단측 p95 가",
        "양측 MDD 보다 작게 나온다 — 오류가 아니다.",
        "",
        "| n | K셀 | SE | 단일비교 MDD | 선택보정 p95 | 잡음 기대Δ |",
        "|---|---|---|---|---|---|",
    ]
    for g in p["ruler"]:
        lines.append(
            f"| {g['n']} | {g['k_cells']} | {g['se_single']} | **{g['mdd_single_pair']}** | "
            f"**{g['mdd_selection_p95']}** | {g['noise_delta_expected']} |"
        )

    lines += [
        "",
        "읽는 법: **n=50 에서 10셀을 훑었다면, 순수 잡음만으로도 Δ가 "
        f"{p['key_numbers']['n50_k10_p95']} 까지 나온다.** 그보다 작은 Δ는 신호가 아니다.",
        "",
        "## 4. 과거 판정 소급감사",
        "",
        "| 판정 | n | K셀 | 주장 Δ | 단일 MDD | 선택보정 p95 | 결과 |",
        "|---|---|---|---|---|---|---|",
    ]
    for it in p["retro_audit"]:
        g = it["gate"]
        lines.append(
            f"| {it['id']} | {it['n']} | {it['k_cells']} | {it['delta']:+.4f} | "
            f"{g['mdd_single_pair']} | {g['mdd_selection_p95']} | **{it['verdict']}** |"
        )
    lines += ["", "각 항목 해설:", ""]
    for it in p["retro_audit"]:
        lines.append(f"- **{it['id']}** — {it['claim_ko']}")
        lines.append(f"  - {it['why_ko']}")
        if "holdout_ge3" in it:
            lines.append(
                f"  - 홀드아웃 ge3 = {it['holdout_ge3']} (null 대비 {it['holdout_vs_null']:+.4f}) · "
                f"fusion Δ = {it['fusion_delta']}"
            )
        if "tune_ge3_delta" in it:
            lines.append(f"  - 튜닝창 ge3 차이 = {it['tune_ge3_delta']:+.4f} · fusion Δ = {it['fusion_delta']}")
    lines += [
        "",
        "## 5. 가장 중요한 결과",
        "",
        p["verdict"]["detail_ko"],
        "",
        "## 6. 앞으로의 규칙 (게이트)",
        "",
        "모든 튜닝 도구는 판정 전에 `gate(n, k_cells)` 를 호출하고, 그 결과를 벤치 JSON 에",
        "함께 기록해야 한다. 다음 중 하나라도 해당하면 **차이 없음**으로 보고한다.",
        "",
        "1. |Δ| < `mdd_single_pair` → UNDECIDABLE",
        "2. |Δ| < `mdd_selection_p95` (K셀 탐색) → SELECTION_SUSPECT",
        "3. 홀드아웃이 null 신뢰구간 안으로 붕괴 → NOISE_SELECTION_CONFIRMED",
        "",
        "추가로: ge3 는 **매우 둔한 지표**다. 같은 데이터에서 seed만 바꿔도 "
        f"{p['key_numbers']['seed_range']} 폭이 생긴다. 작은 효과를 보려면 ge3 대신",
        "번호 확률벡터에 대한 proper scoring rule 을 써야 한다 (SCORE-RULE-DIAG 방식).",
        "",
        "## 7. 한계",
        "",
        "- 선택보정 MC 는 셀 간 독립을 가정한다. 실제로는 같은 seed 규칙을 공유해 부분적으로",
        "  짝지어져 있으므로, 진짜 임계값은 이 표보다 **더 클 수도 작을 수도** 있다.",
        "  다만 SEED-DIAG 실측 폭이 이론 SE 보다 크므로 표는 **낙관적(느슨한) 하한**으로 보라.",
        "- null 계산은 5장이 서로 독립이라고 본다. 실제 발권은 다양성 선별을 거쳐 약한 음의",
        "  상관이 있어 실제 null 은 미세하게 다를 수 있다. 측정치와 넷째 자리까지 일치하므로",
        "  실용상 무해하다.",
        "- 이 도구는 판정 규칙만 만든다. 어떤 상수도 바꾸지 않는다.",
        "",
        f"근거 원본: `docs/benchmarks/{OUT_JSON.name}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    p0 = null_ge3(5)
    ref_null = load_bench(REF_NULL)
    seed_b = load_bench(REF_SEED)
    step3 = load_bench("20260805_KTRANSITION_STEP3_DESIGN.json")

    measured5 = float(ref_null["null_ge3_default_best_of_5"])
    measured15 = float(ref_null["null_ge3_best_of_15"])
    n15 = null_ge3(15)

    ruler = ruler_table(p0)
    audit = retro_audit(p0, float(seed_b["stat"]["summary"]["range_ge3"]))
    g50_10 = gate(50, 10, p0)

    applied = audit[0]
    if applied["verdict"] in ("NOISE_SELECTION_CONFIRMED", "SELECTION_SUSPECT", "UNDECIDABLE"):
        code = "RULER_TOO_COARSE"
        head = "적용된 엔진 상수(win26/mix0.8)는 잡음 선택으로 판정 — 자의 눈금이 주장보다 굵다"
        detail = (
            f"**live 에 적용된 `win26/mix0.8` 은 out-of-sample 근거가 없다.** "
            f"n=50·{applied['k_cells']}셀 탐색에서 Δ{applied['delta']:+.2f} 로 뽑혔으나, "
            f"순수 잡음만으로도 Δ{g50_10['mdd_selection_p95']} 가 나오는 조건이었다. "
            f"바로 다음 홀드아웃 50회차에서 ge3 는 {applied['holdout_ge3']} "
            f"(null {round(p0, 4)} 대비 {applied['holdout_vs_null']:+.4f}) 로 붕괴했고, "
            f"fusion n=200 에서 Δ는 {applied['fusion_delta']} 였다.\n\n"
            "**상수를 되돌리자는 뜻이 아니다.** 되돌릴 근거도 없다(양쪽 다 무근거). "
            "요점은 이 상수를 '개선'으로 인용하는 문서를 정정하고, 앞으로 같은 방식으로 "
            "상수를 채택하지 않는 것이다."
        )
    else:
        code = "RULER_OK"
        head = "과거 판정이 눈금을 통과함"
        detail = "소급감사에서 결정 가능한 판정으로 확인됨."

    payload: dict[str, Any] = {
        "bench_id": BENCH_ID,
        "date": "2026-08-08",
        "scope": "ROK21 / testlotto / 과거학습(stat) — 판정 방법론",
        "wire": False,
        "policy": {
            "read_only": True,
            "db_write": False,
            "code_change": False,
            "constant_change": False,
        },
        "null_analytic": {
            "method": "초기하분포 (45개 중 6개 추첨)",
            "p_single_ge3": round(p_single_ge3(), 8),
            "pmf": {str(k): round(hyper_pmf(k), 10) for k in range(0, 7)},
            "null_ge3_best_of_5": round(p0, 6),
            "null_ge3_best_of_15": round(n15, 6),
            "measured_best_of_5": measured5,
            "measured_best_of_15": measured15,
            "match_best_of_5": abs(p0 - measured5) < 5e-4,
            "match_best_of_15": abs(n15 - measured15) < 5e-4,
            "source_measured": f"docs/benchmarks/{REF_NULL}",
        },
        "problem_answer_frame": {
            "table": "transition_log",
            "structure_ko": "anchor_nums(=문제 · 직전회차) → next_actual(=답) → hit_count(=채점)",
            "n": 1134,
            "nopeek_mean_hit": step3["backtest_result"]["mean_hit"],
            "nopeek_ge3": step3["backtest_result"]["ge3_rate"],
            "random_ge3": step3["backtest_result"]["random_ge3_rate"],
            "peek_mean_hit": step3["backtest_full_style_holdout"]["mean_hit"],
            "peek_ge3": step3["backtest_full_style_holdout"]["ge3_rate"],
            "source": "20260805_KTRANSITION_STEP3_DESIGN.json",
            "conclusion_ko": (
                "컨닝을 막으면 top15 ge3 가 무작위보다 낮다 → 문제→답 학습기는 이미 채점 실패"
            ),
        },
        "order_invariance": order_invariance_proof(),
        "ruler": ruler,
        "retro_audit": audit,
        "key_numbers": {
            "n50_k10_p95": g50_10["mdd_selection_p95"],
            "n50_single_mdd": g50_10["mdd_single_pair"],
            "seed_range": float(seed_b["stat"]["summary"]["range_ge3"]),
            "seed_std": float(seed_b["stat"]["summary"]["std_ge3"]),
        },
        "mc": {"B": MC_B, "seed": MC_SEED},
        "verdict": {"code": code, "headline_ko": head, "detail_ko": detail},
        "next_rule_ko": [
            "모든 튜닝 도구는 gate(n, k_cells) 결과를 벤치 JSON 에 기록",
            "|Δ| < mdd_selection_p95 이면 '차이 없음'으로 보고",
            "ge3 대신 proper scoring rule 병기 (ge3 는 둔함)",
            "홀드아웃이 null CI 로 붕괴하면 그 판정은 폐기",
        ],
        "tool": "tools/_k_stat_decision_gate.py",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = build_report(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        DRIVE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"drive copy skip: {e}", file=sys.stderr)

    print(f"[{BENCH_ID}] {code} — {head}")
    print(f"  null(해석)={round(p0, 6)} vs 측정={measured5} match={payload['null_analytic']['match_best_of_5']}")
    print(f"  순서불변: 최대차={payload['order_invariance']['max_abs_diff_forward_vs_backward']} identical={payload['order_invariance']['identical']}")
    print(f"  n=50/K=10 선택보정 p95 = {g50_10['mdd_selection_p95']} (단일 MDD {g50_10['mdd_single_pair']})")
    for it in audit:
        print(f"  {it['verdict']:<28} Δ={it['delta']:+.4f}  {it['id'][:52]}")
    print(f"  bench  -> {OUT_JSON}")
    print(f"  report -> {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
