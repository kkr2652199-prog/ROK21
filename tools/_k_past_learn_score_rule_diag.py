# -*- coding: utf-8 -*-
"""K-PAST-LEARN-SCORE-RULE-DIAG — 과거학습(stat) decay 튜닝 정밀진단 (READ-ONLY · wire 없음).

문제: DETAIL_TUNE 은 ge3(n=50 tune / n=50 hold) 로 9칸을 비교했다.
      base 0.5772 vs best 0.5780 = 적중 1건 차이 · seed 민감(K-STAT-SEED-DIAG) → 선택근거 약함.

교체 방법론 (문헌):
  1) 균등성 검정   Genest·Lockhart·Stephens(2002) χ²and the lottery · Joe(1993) · Haigh(1997)
                   6/45 보정계수 (M-1)/(M-m) = 44/39 · df=44
  2) 적정채점규칙  Gneiting & Raftery(2007 JASA) log/Brier score
                   → 번호별 확률벡터를 직접 채점 (표본 = draws×45, ge3보다 검정력↑ · 시드 무관)
  3) 선택편의      Bailey·Borwein·López de Prado·Zhu(2014) PBO via CSCV
                   + Bailey & López de Prado(2014) false-strategy 기대최대

금지 준수: engine 상수 미변경 · random.choices 미사용(샘플링 없음) · _get_draws_before 그대로
          · DB 쓰기 없음(init 제외) · 발권 경로 미호출

Usage:
  python tools/_k_past_learn_score_rule_diag.py
  python tools/_k_past_learn_score_rule_diag.py --n-eval 120   # 빠른 확인
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import NormalDist
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KPAST_LEARN_SCORE_RULE_DIAG.json"
OUT_MD = ROOT / "reports" / "20260808_KPAST_LEARN_SCORE_RULE_DIAG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

M_TOTAL = 45
M_DRAWN = 6
NULL_P = 1.0 / M_TOTAL
NULL_LOG = -math.log(NULL_P)
DEFAULT_N_EVAL = 500

# FRAME 고정 (ENGINE-APPLY 확정값) — 이번 진단에서 건드리지 않음
FRAME = {"short_win": 26, "short_mix": 0.8}
# 현행 확정 decay (DETAIL_KEEP)
BASE_CELL = (0.005, 0.05)
LONG_DECAYS = [0.0005, 0.002, 0.005, 0.01, 0.02]
SHORT_DECAYS = [0.02, 0.05, 0.10]
CSCV_PARTITIONS = 8
EULER_GAMMA = 0.5772156649015329


def cell_key(long_d: float, short_d: float) -> str:
    return f"L{long_d:g}_S{short_d:g}"


def chi2_sf(x: float, df: int) -> float:
    """Wilson-Hilferty 근사 (stdlib only · scipy 미사용)."""
    if x <= 0 or df <= 0:
        return 1.0
    t = (x / df) ** (1.0 / 3.0)
    mean = 1.0 - 2.0 / (9.0 * df)
    sd = math.sqrt(2.0 / (9.0 * df))
    return 1.0 - NormalDist().cdf((t - mean) / sd)


def uniformity_test(draws: list[dict]) -> dict[str, Any]:
    """번호별 출현 균등성 — 비복원 보정 χ² (Genest et al. 2002 · Haigh 1997)."""
    counts = dict.fromkeys(range(1, M_TOTAL + 1), 0)
    for d in draws:
        for k in range(1, 7):
            counts[int(d[f"num{k}"])] += 1
    n_draws = len(draws)
    expected = n_draws * M_DRAWN / M_TOTAL
    naive = sum((counts[n] - expected) ** 2 / expected for n in range(1, M_TOTAL + 1))
    factor = (M_TOTAL - 1) / (M_TOTAL - M_DRAWN)  # 44/39
    adjusted = naive * factor
    df = M_TOTAL - 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:5]
    bottom = sorted(counts.items(), key=lambda kv: kv[1])[:5]
    return {
        "n_draws": n_draws,
        "expected_per_number": round(expected, 3),
        "chi2_naive": round(naive, 4),
        "adjust_factor": round(factor, 6),
        "chi2_adjusted": round(adjusted, 4),
        "df": df,
        "p_value_approx": round(chi2_sf(adjusted, df), 6),
        "crit_005": 60.4809,
        "reject_uniform_005": bool(adjusted > 60.4809),
        "hottest": [{"num": n, "count": c} for n, c in top],
        "coldest": [{"num": n, "count": c} for n, c in bottom],
        "method": "Pearson X2 * (M-1)/(M-m) · Genest·Lockhart·Stephens(2002) · Joe(1993) · Haigh(1997)",
        "note": "귀무=모든 번호 등확률. 기각 못하면 번호별 편향 근거 없음 → decay 튜닝 상한도 없음",
    }


def _prob_vector(draws: list[dict], long_d: float, short_d: float) -> dict[int, float]:
    """engine._build_freq_v2 를 그대로 호출해 정규화 확률벡터 반환 (코드 미변경)."""
    from app.testlotto.brains.stat_brain import engine

    os.environ["K_STAT_ENG_LONG_DECAY"] = repr(long_d)
    os.environ["K_STAT_ENG_SHORT_DECAY"] = repr(short_d)
    freq = engine._build_freq_v2(draws)
    total = sum(freq.values()) or 1.0
    return {n: freq[n] / total for n in range(1, M_TOTAL + 1)}


def _scores(q: dict[int, float], actual: set[int]) -> tuple[float, float, float]:
    """log-score surrogate + Brier (Gneiting & Raftery 2007) + 균등분포 L1 이탈."""
    log_s = 0.0
    for n in actual:
        p = max(q.get(n, 1e-12), 1e-12)
        log_s += -math.log(p)
    log_s /= M_DRAWN
    brier = 0.0
    l1 = 0.0
    for n in range(1, M_TOTAL + 1):
        p_hit = min(1.0, M_DRAWN * q[n])
        y = 1.0 if n in actual else 0.0
        brier += (p_hit - y) ** 2
        l1 += abs(q[n] - NULL_P)
    brier /= M_TOTAL
    return log_s, brier, l1


def _vs_null_verdict(stat: dict[str, Any]) -> str:
    """log-score 는 낮을수록 좋다 → Δ<0 이면 null 우위."""
    if stat["p_two_sided"] >= 0.05:
        return "null과 구분 불가"
    return "null 우위(유의)" if stat["mean_diff"] < 0 else "null보다 유의하게 나쁨"


def pearson_r(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def null_brier() -> float:
    b = (M_TOTAL - M_DRAWN) * (M_DRAWN * NULL_P) ** 2 + M_DRAWN * (1.0 - M_DRAWN * NULL_P) ** 2
    return b / M_TOTAL


def paired_stats(series_a: list[float], series_b: list[float]) -> dict[str, Any]:
    """대응 차이 t·Wilcoxon 부호검정 근사 (lower score = better)."""
    diffs = [a - b for a, b in zip(series_a, series_b)]
    n = len(diffs)
    if n < 2:
        return {"n": n, "mean_diff": 0.0, "t": 0.0, "p_two_sided": 1.0, "sign_wins": 0}
    mean = sum(diffs) / n
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    se = math.sqrt(var / n) if var > 0 else 0.0
    t = mean / se if se > 0 else 0.0
    p = 2.0 * (1.0 - NormalDist().cdf(abs(t)))
    wins = sum(1 for d in diffs if d < 0)
    return {
        "n": n,
        "mean_diff": round(mean, 6),
        "t": round(t, 4),
        "p_two_sided": round(p, 6),
        "sign_wins": wins,
        "sign_win_rate": round(wins / n, 4),
    }


def pbo_cscv(series_by_cell: dict[str, list[float]], partitions: int = CSCV_PARTITIONS) -> dict[str, Any]:
    """PBO — Bailey·Borwein·López de Prado·Zhu(2014) CSCV. score=낮을수록 좋음 → 부호반전."""
    cells = sorted(series_by_cell)
    n_obs = len(series_by_cell[cells[0]])
    if n_obs < partitions * 2 or len(cells) < 2:
        return {"pbo": None, "note": "표본/셀 부족"}
    size = n_obs // partitions
    blocks = [list(range(i * size, (i + 1) * size)) for i in range(partitions)]
    lambdas: list[float] = []
    half = partitions // 2
    for combo in combinations(range(partitions), half):
        is_idx = [i for b in combo for i in blocks[b]]
        oos_idx = [i for b in range(partitions) if b not in combo for i in blocks[b]]
        # 낮은 log-score = 좋음 → perf = -mean
        is_perf = {c: -sum(series_by_cell[c][i] for i in is_idx) / len(is_idx) for c in cells}
        oos_perf = {c: -sum(series_by_cell[c][i] for i in oos_idx) / len(oos_idx) for c in cells}
        best = max(cells, key=lambda c, p=is_perf: p[c])
        ranked = sorted(cells, key=lambda c, p=oos_perf: p[c])  # 낮은 성능 먼저
        rank = ranked.index(best) + 1
        omega = rank / (len(cells) + 1)
        lambdas.append(math.log(omega / (1.0 - omega)))
    pbo = sum(1 for x in lambdas if x <= 0) / len(lambdas)
    return {
        "pbo": round(pbo, 4),
        "n_combinations": len(lambdas),
        "partitions": partitions,
        "n_cells": len(cells),
        "lambda_mean": round(sum(lambdas) / len(lambdas), 4),
        "interpretation": "PBO>=0.5 → 최적셀 선택이 우연 수준(과적합 위험)",
        "ref": "Bailey, Borwein, López de Prado & Zhu (2014) J. Computational Finance",
    }


def expected_max_under_null(n_trials: int, var_across_trials: float) -> float:
    """false-strategy 기대최대 (Bailey & López de Prado 2014)."""
    if n_trials < 2 or var_across_trials <= 0:
        return 0.0
    z = NormalDist()
    sd = math.sqrt(var_across_trials)
    a = z.inv_cdf(1.0 - 1.0 / n_trials)
    b = z.inv_cdf(1.0 - 1.0 / (n_trials * math.e))
    return sd * ((1.0 - EULER_GAMMA) * a + EULER_GAMMA * b)


def run_grid(lo: int, hi: int) -> dict[str, Any]:
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    actuals: dict[int, set[int]] = {}
    for r in conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no BETWEEN ? AND ?",
        (lo, hi),
    ):
        d = dict(r)
        actuals[int(d["draw_no"])] = {int(d[f"num{k}"]) for k in range(1, 7)}
    conn.close()

    os.environ["K_PAST_LEARN"] = "1"
    os.environ["K_PAST_LEARN_ASSOC"] = "0"
    os.environ["K_STAT_ENGINE_V2"] = "1"
    os.environ["K_STAT_ENG_SHORT_WIN"] = str(FRAME["short_win"])
    os.environ["K_STAT_ENG_SHORT_MIX"] = str(FRAME["short_mix"])

    cells = [(ld, sd) for ld in LONG_DECAYS for sd in SHORT_DECAYS]
    log_series: dict[str, list[float]] = {cell_key(*c): [] for c in cells}
    brier_series: dict[str, list[float]] = {cell_key(*c): [] for c in cells}
    l1_series: dict[str, list[float]] = {cell_key(*c): [] for c in cells}
    targets: list[int] = []

    for dno in range(lo, hi + 1):
        act = actuals.get(dno)
        if not act:
            continue
        draws = _get_draws_before(dno)
        if len(draws) < FRAME["short_win"] + 10:
            continue
        targets.append(dno)
        for ld, sd in cells:
            q = _prob_vector(draws, ld, sd)
            ls, bs, l1 = _scores(q, act)
            k = cell_key(ld, sd)
            log_series[k].append(ls)
            brier_series[k].append(bs)
            l1_series[k].append(l1)

    n = len(targets)
    nb = null_brier()
    rows = []
    for ld, sd in cells:
        k = cell_key(ld, sd)
        ls = log_series[k]
        bs = brier_series[k]
        mean_log = sum(ls) / n
        mean_brier = sum(bs) / n
        mean_l1 = sum(l1_series[k]) / n
        rows.append(
            {
                "cell": k,
                "long_decay": ld,
                "short_decay": sd,
                "mean_log_score": round(mean_log, 6),
                "log_skill_vs_null": round(1.0 - mean_log / NULL_LOG, 6),
                "mean_brier": round(mean_brier, 6),
                "brier_skill_vs_null": round(1.0 - mean_brier / nb, 6),
                "mean_l1_dev_from_uniform": round(mean_l1, 6),
                "is_base": bool((ld, sd) == BASE_CELL),
            }
        )
    rows.sort(key=lambda r: r["mean_log_score"])
    base_k = cell_key(*BASE_CELL)
    best = rows[0]

    null_log_series = [NULL_LOG] * n
    vs_null_base = paired_stats(log_series[base_k], null_log_series)
    vs_null_best = paired_stats(log_series[best["cell"]], null_log_series)
    best_vs_base = paired_stats(log_series[best["cell"]], log_series[base_k])

    cell_means = [r["mean_log_score"] for r in rows]
    mean_of_means = sum(cell_means) / len(cell_means)
    var_across = sum((m - mean_of_means) ** 2 for m in cell_means) / (len(cell_means) - 1)

    return {
        "eval_range": [lo, hi],
        "n_targets": n,
        "null_log_score": round(NULL_LOG, 6),
        "null_brier": round(nb, 6),
        "grid": {"long_decay": LONG_DECAYS, "short_decay": SHORT_DECAYS, "n_cells": len(cells)},
        "frame_fixed": FRAME,
        "rows": rows,
        "base_cell": {"long_decay": BASE_CELL[0], "short_decay": BASE_CELL[1], "key": base_k},
        "best_cell": best,
        "tests": {
            "base_vs_null": vs_null_base,
            "best_vs_null": vs_null_best,
            "best_vs_base": best_vs_base,
        },
        "selection_bias": {
            "n_trials": len(cells),
            "var_of_cell_means": round(var_across, 9),
            "expected_max_gain_under_null": round(
                expected_max_under_null(len(cells), var_across), 6
            ),
            "observed_gain_best_vs_base": round(
                rows[-0]["mean_log_score"] * 0 + (
                    next(r["mean_log_score"] for r in rows if r["cell"] == base_k)
                    - best["mean_log_score"]
                ),
                6,
            ),
            "ref": "Bailey & López de Prado (2014) Deflated Sharpe / false-strategy theorem",
        },
        "mechanism": {
            "r_l1dev_vs_logscore": round(
                pearson_r(
                    [r["mean_l1_dev_from_uniform"] for r in rows],
                    [r["mean_log_score"] for r in rows],
                ),
                4,
            ),
            "n_cells": len(rows),
            "claim": "균등분포 이탈이 클수록 log-score 악화 = 최근가중이 정보가 아니라 자기부과 벌점",
            "expected_if_uniform_truth": "r ≈ +1 (이탈=순손실)",
        },
        "pbo": pbo_cscv(log_series),
        "_log_series_keys": sorted(log_series),
    }


def literature() -> list[dict[str, str]]:
    return [
        {
            "ref": "Genest, Lockhart & Stephens (2002) 'χ² and the lottery', JRSS-D",
            "core": "비복원 추첨은 naive Pearson χ² 가 χ² 분포를 안 따름 → 가중합/보정 필요",
            "apply": "6/45 보정 (M-1)/(M-m)=44/39 · df=44 로 번호 균등성 검정 (§3)",
            "url": "https://doi.org/10.1111/1467-9884.00315",
        },
        {
            "ref": "Joe (1993) 'Tests of uniformity for sets of lotto numbers', SPL",
            "core": "단일번호·쌍·삼중 균등성 및 회차간 독립 검정 도출",
            "apply": "번호축 먼저 검정 · 쌍/삼중은 기존 KSIGNAL L3 PMI 트랙과 연결",
            "url": "https://doi.org/10.1016/0167-7152(93)90141-5",
        },
        {
            "ref": "Gneiting & Raftery (2007) 'Strictly Proper Scoring Rules', JASA 102(477)",
            "core": "log/Brier 등 적정채점규칙은 참분포에서 기대점수 최적 → 파라미터 추정에 사용 가능",
            "apply": "decay 를 ge3(0/1) 대신 확률벡터 log-score 로 선택 (§4) · 시드 무관·검정력↑",
            "url": "https://doi.org/10.1198/016214506000001437",
        },
        {
            "ref": "Bailey, Borwein, López de Prado & Zhu (2014) 'The Probability of Backtest Overfitting'",
            "core": "CSCV 로 '최적 IS 셀이 OOS 중위 이하일 확률'(PBO) 추정 · 0.5↑면 선택=우연",
            "apply": "decay 그리드 선택의 과적합 확률 직접 계산 (§5)",
            "url": "https://davidhbailey.com/dhbpapers/backtest-prob.pdf",
        },
        {
            "ref": "Bailey & López de Prado (2014) 'The Deflated Sharpe Ratio', JPM 40(5)",
            "core": "시행수 N·시행간 분산으로 기대최대 성과를 계산해 선택편의 차감",
            "apply": "9~15칸 그리드의 '우연 최대이득' 과 실제 이득 비교 (§5)",
            "url": "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf",
        },
        {
            "ref": "Bodenham & Adams / Plasse & Adams — forgetting factors (categorical streams)",
            "core": "망각계수는 우도(likelihood) 기반으로 온라인 튜닝 · 고정망각은 특수사례",
            "apply": "decay=망각계수 → 우도(log-score)로 고르는 게 표준. 적응형은 신호 확인 후에만",
            "url": "https://doi.org/10.1007/s11222-019-09858-0",
        },
        {
            "ref": "Suetens, Galbo-Jørgensen & Tyran (2016) JEEA 14(3) 584-607",
            "core": "플레이어는 직전 당첨번호를 피하고(도박사오류) 최근 연속출현 번호로 몰린다(핫핸드)",
            "apply": "past_learn 의 '미출30+'·'1yHot' 태그는 플레이어 인기축과 겹침 → 공유당첨 EV 주의 (§6)",
            "url": "https://doi.org/10.1111/jeea.12147",
        },
        {
            "ref": "Cook & Clotfelter (1993) / Baker & McHale (2011) JRSS-A 174(4) — conscious selection",
            "core": "당첨P는 고정 · 비인기 조합은 분배 감소로 기대값(EV)↑",
            "apply": "ROK21 기존 EV축(적중축 폐기)과 정합 · 인기페널티(KSIGNAL L4)로 연결",
            "url": "https://doi.org/10.1111/j.1467-985x.2011.00693.x",
        },
    ]


def build_report(p: dict[str, Any]) -> str:
    g = p["grid_result"]
    u = p["uniformity"]
    rows = g["rows"]
    t = g["tests"]
    sb = g["selection_bias"]
    pbo = g["pbo"]

    top = rows[:5]
    base_row = next(r for r in rows if r["is_base"])
    hot_txt = ", ".join("{}({})".format(x["num"], x["count"]) for x in u["hottest"])
    cold_txt = ", ".join("{}({})".format(x["num"], x["count"]) for x in u["coldest"])

    lines = [
        "# K-PAST-LEARN-SCORE-RULE-DIAG — 과거학습 뇌 튜닝 정밀진단 (논문 방법론)",
        "",
        f"📅 2026-08-08 KST · **{p['verdict']}** · wire=**False** · 수치 SSOT=`{OUT_JSON.name}`",
        "",
        "---",
        "",
        "## 0) 한 줄",
        "",
        p["one_line"],
        "",
        "---",
        "",
        "## 1) 대상 · 범위",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        "| 뇌 | **과거학습**(tag=`stat`) = 테스트로또 3예측뇌 중 1번 |",
        "| 모듈 | `app/testlotto/brains/stat_brain/engine.py` · `past_learn.py` |",
        "| 틀(FRAME) | short_win=**26** · short_mix=**0.8** (ENGINE-APPLY 확정 · 이번 미변경) |",
        "| 현행 decay | long=**0.005** · short=**0.05** (DETAIL_KEEP · 형 GO) |",
        f"| 평가구간 | {g['eval_range'][0]}~{g['eval_range'][1]} · n=**{g['n_targets']}** |",
        "| 변경 | **없음** (READ-ONLY 진단 · 발권/quota/engine 상수 불변) |",
        "",
        "> R34 주의: 여기서 '1번 뇌'는 테스트로또 내부 뇌 순번이며, memoy 관할 1~3군과 무관하다.",
        "",
        "---",
        "",
        "## 2) 왜 지금 방식이 약한가",
        "",
        "`DETAIL_TUNE` 은 ge3(≥3맞음) 비율로 9칸을 비교했다.",
        "",
        "| 항목 | 값 | 문제 |",
        "|------|-----|------|",
        "| base score | 0.5772 | tune 0.28 / hold 0.14 |",
        "| best score | 0.5780 | tune 0.24 / hold 0.16 |",
        "| 차이 | **0.0008** | hold n=50에서 **적중 1건** 차이 |",
        "| fusion Δ | **0.000** | live 반영 없음 |",
        "| 시드 | HIGH_SENSITIVITY | `K-STAT-SEED-DIAG` stat range **0.14** |",
        "",
        "ge3 는 0/1 절단 지표라 정보량이 작고(n=50), 시드 분산이 신호보다 크다.",
        "적정채점규칙은 확률벡터 전체를 쓰므로 같은 표본에서 검정력이 크게 높다 (Gneiting & Raftery 2007).",
        "",
        "---",
        "",
        "## 3) 균등성 검정 — 상한이 있는가",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        f"| n_draws | **{u['n_draws']}** · 번호별 기대 {u['expected_per_number']} |",
        f"| naive χ² | {u['chi2_naive']} |",
        f"| 보정 χ² (×44/39) | **{u['chi2_adjusted']}** (df={u['df']}) |",
        f"| p (근사) | **{u['p_value_approx']}** |",
        f"| 0.05 기각 | **{'예' if u['reject_uniform_005'] else '아니오'}** (임계 {u['crit_005']}) |",
        f"| 최다 | {hot_txt} |",
        f"| 최소 | {cold_txt} |",
        "",
        "방법: Pearson χ² × (M−1)/(M−m) — 비복원 보정 (Genest·Lockhart·Stephens 2002 · Joe 1993 · Haigh 1997).",
        u["note"],
        "",
        "---",
        "",
        "## 4) 적정채점규칙 그리드 (log-score · Brier)",
        "",
        f"- null log-score = **{g['null_log_score']}** (=−log(1/45)) · null Brier = **{g['null_brier']}**",
        f"- 셀 수 = **{g['grid']['n_cells']}** · long_decay {g['grid']['long_decay']} × short_decay {g['grid']['short_decay']}",
        "- skill = 1 − score/null (양수면 null 우위 · 낮은 score가 좋음)",
        "",
        "| 순위 | cell | log-score | log skill | Brier | Brier skill | 균등이탈 L1 |",
        "|------|------|-----------|-----------|-------|-------------|-------------|",
    ]
    for i, r in enumerate(top, 1):
        mark = " **(현행)**" if r["is_base"] else ""
        lines.append(
            f"| {i} | `{r['cell']}`{mark} | {r['mean_log_score']} | {r['log_skill_vs_null']:+} | "
            f"{r['mean_brier']} | {r['brier_skill_vs_null']:+} | {r['mean_l1_dev_from_uniform']} |"
        )
    worst = rows[-1]
    lines += [
        f"| … | `{worst['cell']}` (최악) | {worst['mean_log_score']} | {worst['log_skill_vs_null']:+} | "
        f"{worst['mean_brier']} | {worst['brier_skill_vs_null']:+} | {worst['mean_l1_dev_from_uniform']} |",
        "",
        f"현행 셀 `{base_row['cell']}` = log-score **{base_row['mean_log_score']}** · "
        f"skill **{base_row['log_skill_vs_null']:+}** · 균등이탈 **{base_row['mean_l1_dev_from_uniform']}**",
        "",
        "### 4.0 메커니즘 — 이탈이 곧 벌점",
        "",
        f"- 균등이탈(L1) ↔ log-score 상관 **r={g['mechanism']['r_l1dev_vs_logscore']}** (셀 {g['mechanism']['n_cells']}개)",
        f"- {g['mechanism']['claim']}",
        f"- 진실이 균등이면 기대: {g['mechanism']['expected_if_uniform_truth']}",
        "",
        "### 4.1 대응검정 (per-draw 차이)",
        "",
        "| 비교 | mean Δ | t | p(양측) | 승률 |",
        "|------|--------|---|---------|------|",
        f"| 현행 vs null | {t['base_vs_null']['mean_diff']:+} | {t['base_vs_null']['t']} | "
        f"{t['base_vs_null']['p_two_sided']} | {t['base_vs_null']['sign_win_rate']} |",
        f"| 최적 vs null | {t['best_vs_null']['mean_diff']:+} | {t['best_vs_null']['t']} | "
        f"{t['best_vs_null']['p_two_sided']} | {t['best_vs_null']['sign_win_rate']} |",
        f"| 최적 vs 현행 | {t['best_vs_base']['mean_diff']:+} | {t['best_vs_base']['t']} | "
        f"{t['best_vs_base']['p_two_sided']} | {t['best_vs_base']['sign_win_rate']} |",
        "",
        "(Δ<0 = 앞쪽이 더 좋음 · log-score는 낮을수록 좋다)",
        "",
        "---",
        "",
        "## 5) 선택편의 · 과적합 확률",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        f"| 시행 셀수 N | {sb['n_trials']} |",
        f"| 셀 평균의 분산 | {sb['var_of_cell_means']} |",
        f"| 우연 기대최대 이득 | **{sb['expected_max_gain_under_null']}** |",
        f"| 실측 최적−현행 이득 | **{sb['observed_gain_best_vs_base']}** |",
        f"| PBO (CSCV) | **{pbo.get('pbo')}** · combos {pbo.get('n_combinations')} · S={pbo.get('partitions')} |",
        "",
        f"- PBO 해석: {pbo.get('interpretation')}",
        "- 실측 이득 ≤ 우연 기대최대면 그리드 최적셀은 **선택편의로 설명 가능**.",
        f"- 근거: {sb['ref']} · {pbo.get('ref')}",
        "",
        "---",
        "",
        "## 6) 문헌 → 우리 적용",
        "",
        "| 문헌 | 핵심 | ROK21 적용 |",
        "|------|------|------------|",
    ]
    for it in p["literature"]:
        lines.append(f"| [{it['ref']}]({it['url']}) | {it['core']} | {it['apply']} |")

    lines += [
        "",
        "### 6.1 행동경제 경고 (튜닝 방향에 직결)",
        "",
        "Suetens et al.(2016)은 플레이어가 **직전 당첨번호를 회피**(도박사 오류)하고 "
        "**최근 자주 나온 번호로 몰린다**(핫핸드 오류)는 것을 개인 패널로 보였다.",
        "",
        "우리 `past_learn.soft_delta_for_set` 은 지금",
        "",
        "```",
        "overdue  : gap >= 30      → +0.35/개 (최대 1.5)",
        "hot1y    : rate_1y > 1.15×null → +0.25/개 (최대 1.0)",
        "cold1y   : rate_1y < 0.75×null → +0.10/개 (최대 0.5)",
        "```",
        "",
        "즉 **hot1y 가점 = 대중 인기축 가점**이다. 당첨확률은 안 변하는데(균등) "
        "공유당첨 확률은 올라가므로 EV에는 역방향이다 (Cook & Clotfelter 1993 · Baker & McHale 2011).",
        "반대로 overdue(미출) 가점은 대중이 **피하는** 쪽이라 EV에 유리한 방향이다.",
        "",
        "→ 결론: soft 태그는 '적중↑' 근거가 아니라 **EV(인기회피) 축으로 재해석**해야 한다. "
        "이는 이미 있는 KSIGNAL **L4 popularity penalty**(w=0)와 같은 축이다.",
        "",
        "---",
        "",
        "## 7) 결론 · 채택/기각",
        "",
        "### 결론",
        "",
    ]
    for c in p["conclusions"]:
        lines.append(f"- {c}")
    lines += [
        "",
        "### 채택 (진단·평가 방법 교체 · wire 없음)",
        "",
        "1. decay/망각계수 튜닝 지표를 **ge3 → log-score(적정채점규칙)** 로 교체",
        "2. 그리드 선택에는 항상 **PBO + 기대최대** 동반 보고",
        "3. 번호축 주장 전 **보정 χ² 균등성 검정** 선행",
        "4. soft 태그(hot/overdue)는 **EV·인기축**으로 라벨 재정의 (KSIGNAL L4 연결)",
        "",
        "### 기각",
        "",
        "1. hold n=50 ge3 1건 차이로 상수 변경",
        "2. hot1y 가중 상향 (인기축 = EV 역방향)",
        "3. 적응형 망각계수 즉시 배선 (신호 확인 전)",
        "4. LSTM/시퀀스 예측 부활 · random.choices 개조",
        "",
        "---",
        "",
        f"생성: `tools/_k_past_learn_score_rule_diag.py` · verdict **{p['verdict']}**",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-eval", type=int, default=DEFAULT_N_EVAL)
    args = ap.parse_args()

    from app.testlotto.data_service import get_all_draws

    draws_all = sorted(get_all_draws(), key=lambda d: int(d["draw_no"]))
    if not draws_all:
        print("NO_DRAWS")
        return 1
    max_draw = int(draws_all[-1]["draw_no"])
    lo = max(FRAME["short_win"] + 20, max_draw - args.n_eval + 1)

    uni = uniformity_test(draws_all)
    grid = run_grid(lo, max_draw)
    grid.pop("_log_series_keys", None)

    base_row = next(r for r in grid["rows"] if r["is_base"])
    best = grid["best_cell"]
    t = grid["tests"]
    sb = grid["selection_bias"]
    pbo = grid["pbo"]

    best_beats_base = t["best_vs_base"]["p_two_sided"] < 0.05
    gain_is_noise = sb["observed_gain_best_vs_base"] <= sb["expected_max_gain_under_null"]
    pbo_val = pbo.get("pbo")
    pbo_bad = pbo_val is None or pbo_val >= 0.5
    any_positive_skill = any(r["log_skill_vs_null"] > 0 for r in grid["rows"])
    mech_r = grid["mechanism"]["r_l1dev_vs_logscore"]

    if not any_positive_skill:
        verdict = "NO_SKILL_VS_NULL"
        one = (
            f"셀 {grid['grid']['n_cells']}개 전부 log-score가 null(균등, {grid['null_log_score']})보다 "
            f"**나쁘다** (최선 `{best['cell']}`={best['mean_log_score']} · 현행={base_row['mean_log_score']}). "
            f"균등이탈–점수 상관 r={mech_r} → 최근가중은 정보가 아니라 **자기부과 벌점**이다. "
            "decay 재튜닝으로 null을 넘길 수 없으므로 **KEEP_BASE 유지**가 맞고, "
            "개선은 적중축이 아니라 EV(인기회피)축에서만 가능하다."
        )
    elif best_beats_base and not gain_is_noise and not pbo_bad:
        verdict = "TUNE_CANDIDATE"
        one = (
            f"log-score 기준 최적셀 `{best['cell']}` 이 현행 대비 유의(p={t['best_vs_base']['p_two_sided']}) "
            f"하고 PBO={pbo_val} · 우연 기대최대 초과 → 상수 검토 가치 있음(적용은 형 GO)."
        )
    else:
        verdict = "KEEP_BASE_SUPPORTED"
        one = (
            f"적정채점규칙(n={grid['n_targets']}·셀{grid['grid']['n_cells']})으로 다시 재면 "
            f"최적셀 `{best['cell']}` 의 현행 대비 이득은 p={t['best_vs_base']['p_two_sided']}, "
            f"PBO={pbo_val}, 우연 기대최대 {sb['expected_max_gain_under_null']} vs 실측 "
            f"{sb['observed_gain_best_vs_base']} → **decay 재튜닝 근거 없음 · KEEP_BASE 지지**. "
            "대신 hot1y 가점이 인기축(EV 역방향)이라는 문헌 경고가 실질 개선지점이다."
        )

    conclusions = [
        f"균등성: 보정 χ²={uni['chi2_adjusted']} (df={uni['df']}, p≈{uni['p_value_approx']}) → "
        f"번호별 편향 {'존재 시사' if uni['reject_uniform_005'] else '근거 없음'}",
        f"셀 전체 중 null 초과(skill>0) 존재 = {any_positive_skill} · "
        f"균등이탈↔log-score 상관 r={mech_r}",
        f"현행 decay(0.005/0.05) vs null: mean Δ={t['base_vs_null']['mean_diff']:+} · "
        f"p={t['base_vs_null']['p_two_sided']} → {_vs_null_verdict(t['base_vs_null'])}",
        f"최적셀 `{best['cell']}` vs 현행: p={t['best_vs_base']['p_two_sided']} · "
        f"PBO={pbo_val} · 우연 기대최대 {sb['expected_max_gain_under_null']} ≥ 실측 "
        f"{sb['observed_gain_best_vs_base']} = {gain_is_noise}",
        "ge3(n=50) 대신 log-score 를 쓰면 시드 분산 없이 같은 데이터에서 훨씬 촘촘히 비교된다",
        "실질 개선 후보는 decay 미세조정이 아니라 soft 태그의 EV(인기회피) 재정의",
    ]

    payload: dict[str, Any] = {
        "id": "K-PAST-LEARN-SCORE-RULE-DIAG",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "pass": True,
        "wire": False,
        "applied_change": False,
        "one_line": one,
        "target": {
            "brain": "과거학습",
            "tag": "stat",
            "modules": [
                "app/testlotto/brains/stat_brain/engine.py",
                "app/testlotto/brains/stat_brain/past_learn.py",
            ],
            "note": "테스트로또 내부 1번 예측뇌 · R34의 1~3군(memoy)과 무관",
        },
        "max_draw": max_draw,
        "uniformity": uni,
        "grid_result": grid,
        "prior_method_weakness": {
            "prior": "docs/benchmarks/20260808_KPAST_LEARN_DETAIL_TUNE.json",
            "base_score": 0.5772,
            "best_score": 0.578,
            "score_gap": 0.0008,
            "holdout_n": 50,
            "gap_in_hits": 1,
            "fusion_delta": 0.0,
            "seed_range_ref": "docs/benchmarks/20260805_KSTAT_SEED_DIAG.json (stat range 0.14)",
        },
        "literature": literature(),
        "conclusions": conclusions,
        "adopt": [
            "metric_ge3_to_log_score",
            "always_report_pbo_and_expected_max",
            "adjusted_chi2_before_number_axis_claims",
            "relabel_soft_tags_as_ev_popularity",
        ],
        "reject": [
            "change_decay_on_one_hit_difference",
            "raise_hot1y_weight",
            "wire_adaptive_forgetting_now",
            "revive_lstm_or_patch_random_choices",
        ],
        "beginner": {
            "무엇": "과거학습 뇌의 '얼마나 옛날을 잊을지(decay)' 를 논문식으로 다시 채점",
            "왜": "전에는 50회차 ≥3개 맞춘 횟수로 비교 → 1건 차이로 흔들렸다",
            "결과": one,
            "바뀐것": "없음 (숫자·배선 그대로 · 보고서만)",
        },
    }

    md = build_report(payload)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "verdict": verdict,
                "n_targets": grid["n_targets"],
                "base_log": base_row["mean_log_score"],
                "best_cell": best["cell"],
                "best_log": best["mean_log_score"],
                "best_vs_base_p": t["best_vs_base"]["p_two_sided"],
                "pbo": pbo_val,
                "chi2_adj": uni["chi2_adjusted"],
                "json": str(OUT_JSON),
                "md": str(OUT_MD),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
