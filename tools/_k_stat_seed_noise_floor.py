# -*- coding: utf-8 -*-
"""K-STAT-SEED-NOISE-FLOOR — 잡음 하한 전구간 확정 (READ-ONLY · R38 준수).

배경
----
2026-08-05 SEED-DIAG 는 **n=100 한 점**에서만 쟀다: 같은 파라미터·같은 데이터에서
seed 만 바꾸니 stat 의 ge3 가 0.09~0.23 (폭 0.14) 로 흔들렸다.
그 뒤 모든 튜닝 판정을 "이 폭보다 작으면 못 믿는다"는 근거로 써왔지만,
정작 **그 폭 자체가 단일 추정치**였다. 표본 100개에서 seed 5개로 잰 값이다.

이 도구는 그 하한을 전구간에서 확정한다.

방법
----
1. 전구간을 S개 seed 로 각각 walk-forward 하고, **회차별 best-of-5 적중수**를 통째로 저장
2. 저장된 원자료에서 창 크기 n 을 바꿔가며 사후 재집계
   → 한 번의 실행으로 n=50·100·200·400·800·전구간의 잡음을 전부 얻는다
3. 창마다 seed 간 표준편차를 구하고 창들에 대해 평균
   → **잡음 = n 의 함수**로 나온다 (점 추정이 아니라 곡선)
4. 이론 이항 SE 와 비교해 **팽창계수**(파이프라인이 더하는 잡음)를 구한다
5. 팽창계수를 R38 게이트에 반영한 보정 임계를 제시한다

핵심 구분
--------
- **이항 SE** = 추첨 자체가 랜덤이라 생기는 흔들림 (n 만으로 결정)
- **seed 간 표준편차** = *같은 추첨 결과*에 대해 우리 파이프라인이 만드는 흔들림
  후자는 우리가 만든 잡음이고, 튜닝 판정을 직접 오염시킨다.

정책
----
READ-ONLY. DB 쓰기 없음 · 상수·배선·발권경로 무변경 · wire=False.
`_get_draws_before` 동결 준수 (호출만 · 변형 없음).

Usage
-----
  python tools/_k_stat_seed_noise_floor.py            # 전구간
  K_NF_LO=1136 K_NF_HI=1235 K_NF_SEEDS=2 python ...   # 짧은 프로브
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.k_gate import GATE_KEY, gate, gate_block, null_ge3, se_binom  # noqa: E402
from tools.k_precision import (  # noqa: E402
    PRECISION_KEY,
    Z95,
    pairwise_resolvable,
)

BENCH_ID = "K-STAT-SEED-NOISE-FLOOR"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KSTAT_SEED_NOISE_FLOOR.json"
OUT_MD = ROOT / "reports" / "20260808_KSTAT_SEED_NOISE_FLOOR.md"
RAW_JSON = ROOT / "docs" / "benchmarks" / "20260808_KSTAT_SEED_NOISE_FLOOR_raw.json"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BRAINS = ("stat", "markov", "review")
DEFAULT_SEEDS = (
    42, 0, 7, 99, 1, 2026, 314, 777, 12345, 8,
    13, 21, 55, 89, 144, 233, 377, 610,
    1001, 2718, 3141, 4096, 5150, 6180,
)
WINDOW_SIZES = (50, 100, 200, 400, 800)

PRIOR_SEED_DIAG = "docs/benchmarks/20260805_KSTAT_SEED_DIAG.json"

SEP6 = "|---|---|---|---|---|---|"

# seed 10개로 측정하던 시절의 바닥값. 철회 근거를 보고서에 남기기 위해 보존한다.
PRIOR_FLOOR_10SEED = 0.010127


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    return int(v) if v else default


def load_actuals(lo: int, hi: int) -> dict[int, set[int]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (lo, hi),
    ).fetchall()
    conn.close()
    return {
        int(dict(r)["draw_no"]): {int(dict(r)[f"num{k}"]) for k in range(1, 7)}
        for r in rows
    }


def walk_one_seed(
    seed: int, lo: int, hi: int, actuals: dict[int, set[int]]
) -> tuple[list[int], dict[str, list[int]]]:
    """한 seed 로 lo~hi walk-forward. 회차별 best-of-5 적중수를 그대로 반환."""
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.signal_pool import (
        RollingSignalLearner,
        _build_hint,
        _get_draws_before,
        _pool_by_brain,
        expand_pool,
        repack_by_brain,
        warm_learner_to_draw,
    )

    learner = RollingSignalLearner()
    warm_learner_to_draw(learner, max(1, lo - 200), lo, seed=seed)

    draw_nos: list[int] = []
    best: dict[str, list[int]] = {b: [] for b in BRAINS}

    for dno in range(lo, hi + 1):
        if dno not in actuals:
            continue
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        if not draws:
            continue
        num_ema, pos_ema = learner.snapshot()
        random.seed(seed)
        pool = expand_pool(draws, dno, seed=seed)
        pool_br = _pool_by_brain(pool)
        hint = _build_hint(draws, dno)
        repacked = repack_by_brain(pool_br, hint, num_ema, pos_ema, target_draw_no=dno)

        actual = actuals[dno]
        vals = _best_by_brain(repacked, actual)
        if vals is not None:
            draw_nos.append(dno)
            for tag in BRAINS:
                best[tag].append(vals[tag])

        learner.update_from_pool(pool_br, actual)

    return draw_nos, best


def _best_by_brain(
    repacked: list[dict[str, Any]], actual: set[int]
) -> dict[str, int] | None:
    """뇌별 상위 5세트의 최고 적중수. 한 뇌라도 세트가 없으면 그 회차는 버린다."""
    by_tag: dict[str, list[list[int]]] = {b: [] for b in BRAINS}
    for c in repacked:
        tag = str(c.get("brain_tag") or "")
        if tag in by_tag:
            by_tag[tag].append([int(x) for x in c["nums"]])

    vals: dict[str, int] = {}
    for tag in BRAINS:
        hits = [len(set(nums) & actual) for nums in by_tag[tag][:5]]
        if not hits:
            return None
        vals[tag] = max(hits)
    return vals


def ge3_of(vals: list[int]) -> float:
    return sum(1 for v in vals if v >= 3) / len(vals) if vals else 0.0


def noise_curve(
    per_seed: dict[str, list[int]], p0: float
) -> list[dict[str, Any]]:
    """창 크기별 seed 간 흔들림. 겹치지 않는 타일로 잘라 창마다 seed 표준편차를 낸다."""
    seeds = sorted(per_seed.keys())
    n_total = len(per_seed[seeds[0]])
    rows: list[dict[str, Any]] = []

    sizes = [w for w in WINDOW_SIZES if w < n_total] + [n_total]
    for w in sizes:
        n_tiles = n_total // w
        if n_tiles < 1:
            continue
        stds: list[float] = []
        ranges: list[float] = []
        for t in range(n_tiles):
            s0, s1 = t * w, (t + 1) * w
            vals = [ge3_of(per_seed[s][s0:s1]) for s in seeds]
            if len(vals) > 1:
                stds.append(pstdev(vals))
                ranges.append(max(vals) - min(vals))
        if not stds:
            continue
        emp_std = mean(stds)
        theo = se_binom(p0, w)
        rows.append(
            {
                "window_n": w,
                "n_tiles": n_tiles,
                "n_seeds": len(seeds),
                "seed_std_mean": round(emp_std, 6),
                "seed_range_mean": round(mean(ranges), 6),
                "seed_range_max": round(max(ranges), 6),
                "binomial_se": round(theo, 6),
                "inflation": round(emp_std / theo, 4) if theo > 0 else None,
                "is_full_range": w == n_total,
            }
        )
    return rows


def fit_variance_model(curve: list[dict[str, Any]]) -> dict[str, Any]:
    """seed 분산을 `a²/n + b²` 로 적합한다.

    `a²/n` 은 회차를 늘리면 평균되어 사라지는 성분이고,
    `b²` 는 **아무리 회차를 늘려도 남는 바닥**이다. b 가 0 이 아니면,
    백테스트를 아무리 길게 해도 seed 선택만으로 그만큼은 계속 흔들린다는 뜻이다.

    타일 수를 가중치로 쓴 가중최소제곱. b² 는 음수가 되지 않게 자른다.
    """
    xs = [1.0 / r["window_n"] for r in curve]
    ys = [r["seed_std_mean"] ** 2 for r in curve]
    ws = [float(r["n_tiles"]) for r in curve]

    sw = sum(ws)
    sx = sum(w * x for w, x in zip(ws, xs))
    sy = sum(w * y for w, y in zip(ws, ys))
    sxx = sum(w * x * x for w, x in zip(ws, xs))
    sxy = sum(w * x * y for w, x, y in zip(ws, xs, ys))

    denom = sw * sxx - sx * sx
    if abs(denom) < 1e-18:
        a2, b2 = 0.0, (sy / sw if sw else 0.0)
    else:
        a2 = (sw * sxy - sx * sy) / denom
        b2 = (sy * sxx - sx * sxy) / denom
    a2 = max(a2, 0.0)
    b2 = max(b2, 0.0)

    fitted = [math.sqrt(a2 * x + b2) for x in xs]
    ybar = sy / sw if sw else 0.0
    ss_res = sum(w * (y - (a2 * x + b2)) ** 2 for w, x, y in zip(ws, xs, ys))
    ss_tot = sum(w * (y - ybar) ** 2 for w, y in zip(ws, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else None

    return {
        "form": "seed_var(n) = a^2/n + b^2",
        "a2": a2,
        "a": round(math.sqrt(a2), 6),
        "b2": b2,
        "irreducible_seed_std": round(math.sqrt(b2), 6),
        "weighted_r2": round(r2, 6) if r2 is not None else None,
        "points": [
            {
                "window_n": r["window_n"],
                "observed_std": r["seed_std_mean"],
                "fitted_std": round(f, 6),
            }
            for r, f in zip(curve, fitted)
        ],
        "meaning_ko": (
            "a²/n 은 회차를 늘리면 사라지는 잡음, b 는 아무리 늘려도 남는 바닥이다. "
            "b 보다 작은 Δ 는 백테스트를 무한히 길게 해도 판정할 수 없다."
        ),
    }


def jackknife_model(per_seed: dict[str, list[int]], p0: float) -> dict[str, Any]:
    """바닥값 b 자체의 오차를 잰다 — seed 하나씩 빼면서 다시 적합한다.

    b 는 앞으로 모든 판정의 임계를 정하는 숫자다. 그 숫자에 오차가 얼마나 붙는지
    모르면 임계를 신뢰할 근거가 없다. 20260808 NOISE-SOURCE 에서 seed 10개짜리
    표준편차를 확정값처럼 쓴 것이 바로 그 실수였다(R39).

    delete-1 잭나이프: SE = sqrt((k−1)/k · Σ(θ_(i) − θ̄)²).
    """
    seeds = sorted(per_seed)
    k = len(seeds)
    if k < 3:
        return {"available": False, "reason_ko": "seed 3개 미만이라 잭나이프 불가"}

    a_vals: list[float] = []
    b_vals: list[float] = []
    for drop in seeds:
        sub = {s: v for s, v in per_seed.items() if s != drop}
        m = fit_variance_model(noise_curve(sub, p0))
        a_vals.append(math.sqrt(m["a2"]))
        b_vals.append(math.sqrt(m["b2"]))

    def _jack(vals: list[float]) -> dict[str, Any]:
        bar = mean(vals)
        se = math.sqrt((k - 1) / k * sum((v - bar) ** 2 for v in vals))
        return {
            "jack_mean": round(bar, 6),
            "se": round(se, 6),
            "ci95": [round(bar - Z95 * se, 6), round(bar + Z95 * se, 6)],
            "min": round(min(vals), 6),
            "max": round(max(vals), 6),
        }

    return {
        "available": True,
        "method": f"delete-1 잭나이프 (seed {k}개 → {k}회 재적합)",
        "a": _jack(a_vals),
        "b": _jack(b_vals),
        "b_positive_replicates": f"{sum(1 for v in b_vals if v > 0)}/{k}",
        "boundary_note_ko": (
            "b 는 정의상 0 이상이라(b² 를 음수로 두지 않는다) 표본분포가 한쪽으로 쏠린다. "
            "따라서 대칭 신뢰구간의 하단이 0 을 넘는다는 것은 '바닥이 0 이다'라는 증명이 "
            "아니라 **'0 과 구별되지 않는다'** 는 뜻으로만 읽어야 한다."
        ),
        "meaning_ko": (
            "b 의 신뢰구간이 넓으면 바닥값을 임계로 쓸 때 그 폭만큼 함께 의심해야 한다. "
            "구간 하단이 0 에 닿으면 '바닥이 있다'는 주장 자체가 흔들린다."
        ),
    }


def seed_std_at(n: int, model: dict[str, Any]) -> float:
    return math.sqrt(model["a2"] / n + model["b2"])


def inflated_gate(n: int, k_cells: int, p0: float, model: dict[str, Any]) -> dict[str, Any]:
    """분산 모형을 반영한 보정 임계.

    seed 잡음과 추첨 잡음은 원인이 다르므로 분산을 더한다.
    총 SE = sqrt(이항분산 + seed분산(n))  — 팽창은 n 에 따라 달라진다.
    """
    g = gate(n, k_cells, p0)
    s_seed = seed_std_at(n, model)
    se_total = math.sqrt(g["se_single"] ** 2 + s_seed**2)
    factor = se_total / g["se_single"] if g["se_single"] > 0 else 1.0
    return {
        **g,
        "seed_std_modeled": round(s_seed, 6),
        "se_total": round(se_total, 6),
        "se_factor": round(factor, 4),
        "mdd_single_pair_infl": round(g["mdd_single_pair"] * factor, 6),
        "mdd_selection_p95_infl": round(g["mdd_selection_p95"] * factor, 6),
    }


def _section_floor_precision(p: dict[str, Any], mdl: dict[str, Any]) -> list[str]:
    """4-B. 바닥값 자체의 오차 (R39)."""
    lines = [
        "### 4-B. 그 바닥값은 얼마나 정확한가 (R39)",
        "",
        "b 는 앞으로 모든 판정의 임계를 정하는 숫자다. 그러니 b 자체의 오차부터 알아야 한다.",
        f"seed 를 하나씩 빼며 {len(p['seeds'])}번 다시 적합했다 (delete-1 잭나이프).",
        "",
        "| 모수 | 점추정 | 잭나이프 평균 | 표준오차 | 95% 신뢰구간 | 최소~최대 |",
        SEP6,
    ]
    ju = p["floor_uncertainty"]
    if ju.get("available"):
        for name, key in (("a (사라지는 성분)", "a"), ("**b (바닥)**", "b")):
            j = ju[key]
            point = mdl["a"] if key == "a" else mdl["irreducible_seed_std"]
            lines.append(
                f"| {name} | {point} | {j['jack_mean']} | {j['se']} | "
                f"[{j['ci95'][0]}, {j['ci95'][1]}] | {j['min']}~{j['max']} |"
            )
    else:
        lines.append(f"| — | — | — | — | — | {ju.get('reason_ko')} |")
    lines += [
        "",
        (
            f"신뢰구간 하단이 **{p['floor_ci_lower']}** 로 0 보다 크다. "
            "바닥이 존재한다는 것 자체는 확정이다."
            if p["floor_established"]
            else (
                f"표준오차({ju['b']['se']})가 점추정({mdl['irreducible_seed_std']})보다 크다. "
                f"**바닥을 0 과 구별할 수 없다.** "
                f"(재적합 {ju['b_positive_replicates']} 가 양수였고 개별값은 "
                f"{ju['b']['min']}~{ju['b']['max']} 범위였다.)"
            )
        ),
        "",
        ju.get("boundary_note_ko", ""),
        "",
        "### 이 바닥을 실제 판정에 대보면",
        "",
        f"전구간 walk-forward(K-FUTURE-WIRE-FULL, n=1182)가 측정한 null 대비 Δ 는 "
        f"**{p['full_wf_delta_vs_null']:+.4f}** 였다. 점추정 바닥 "
        f"{mdl['irreducible_seed_std']} "
        f"**{'보다 작다' if p['full_wf_below_floor'] else '보다 크다'}**.",
        "",
    ]
    if p["full_wf_below_floor_ci_lower"]:
        lines += [
            f"보수적으로 신뢰구간 하단 **{p['floor_ci_lower']}** 을 임계로 써도 Δ 가 여전히 "
            "작다. 결론이 바닥의 점추정 하나에 매달려 있지 않다는 뜻이다. "
            "**표본을 더 모아도 결론이 나지 않는다.**",
            "",
        ]
    else:
        gate_full = p["inflated_gates"][-1]
        lines += [
            "**다만 바닥이 0 과 구별되지 않으므로 이 비교는 근거가 되지 못한다.**",
            "'회차를 무한히 늘려도 판정이 불가능하다'는 주장은 b > 0 을 전제로만 성립한다.",
            "그 전제가 확인되지 않았으니 주장을 철회한다.",
            "",
            "대신 **지금 가진 데이터로 무엇을 말할 수 있는지**로 바꿔 답한다. 전 역사를 다 써도",
            f"회차는 n={p['n_draws']} 뿐이고, 그때 seed 표준편차 실측은 "
            f"**{p['stat']['full_summary']['std_ge3']}**, 보정 단일 MDD 는 "
            f"**{gate_full['mdd_single_pair_infl']}** 이다.",
            f"Δ {p['full_wf_delta_vs_null']:+.4f} 는 그 어느 쪽에도 한참 못 미친다.",
            "",
            "즉 결론은 **'원리적으로 영원히 불가'가 아니라 '가용한 데이터로는 불가'** 다.",
            "실무적 처방은 같지만, 근거의 강도가 다르므로 인용할 때 구분해야 한다.",
            "",
        ]
    return lines


def _section_brain_order(p: dict[str, Any]) -> list[str]:
    """6-B. 뇌별 서열을 인용해도 되는지 (R39)."""
    prec = p[PRECISION_KEY]
    lines = [
        "### 6-B. 이 서열을 인용해도 되나 (R39)",
        "",
        "표준편차끼리 비교할 때는 σ 자체의 표준오차 σ/√(2(k−1)) 를 먼저 따져야 한다.",
        "이 절차를 건너뛴 탓에 20260808 NOISE-SOURCE 에서 헛수고가 났다.",
        "",
        "| 쌍 | 표준편차 | 차이 | 구분 임계 | 구분 가능 | 필요 seed |",
        SEP6,
    ]
    for pr in prec["pairs"]:
        lines.append(
            f"| {pr['pair'][0]} vs {pr['pair'][1]} | "
            f"{pr['sigma'][0]} / {pr['sigma'][1]} | {pr['diff']} | "
            f"{pr['resolve_threshold']} | "
            f"{'예' if pr['resolvable'] else '**아니오**'} | {pr['samples_needed']} |"
        )
    lines += ["", f"**{prec['meaning_ko']}**", ""]
    return lines


def build_report(p: dict[str, Any]) -> str:
    st = p["stat"]
    mdl = dict(p["variance_model"])
    curve = st["noise_curve"]
    mdl["binom_shrink"] = round(curve[0]["binomial_se"] / curve[-1]["binomial_se"], 2)
    mdl["seed_shrink"] = round(curve[0]["seed_std_mean"] / curve[-1]["seed_std_mean"], 2)
    lines = [
        f"# {BENCH_ID} — 잡음 하한 전구간 확정",
        "",
        f"- 날짜: {p['date']} · 회차 **{p['draw_range'][0]}~{p['draw_range'][1]}** "
        f"(n={p['n_draws']}) · seed **{len(p['seeds'])}개** · "
        f"walk 소요 {p['walk_elapsed_sec_original']}초"
        + ("  (본 실행은 저장된 원자료로 분석만 재계산)" if p["walk_reused_from_raw"] else ""),
        f"- **판정: {p['verdict']['code']} — {p['verdict']['headline_ko']}**",
        "- 정책: READ-ONLY · DB 쓰기 없음 · 상수·배선·발권경로 무변경 · wire=False",
        "",
        "## 1. 무엇을 쟀나",
        "",
        "**같은 파라미터·같은 추첨 결과**인데 seed 만 바꿨을 때 ge3 가 얼마나 흔들리는지를 쟀다.",
        "이건 추첨이 랜덤이라 생기는 흔들림(이항 SE)과는 **다른 잡음**이다. 우리 파이프라인이",
        "스스로 만들어내는 잡음이고, 튜닝 판정을 직접 오염시킨다.",
        "",
        f"이전 SEED-DIAG 는 n=100 한 점에서 seed 5개로만 쟀다(폭 {p['prior']['range_ge3']}).",
        "이번엔 전구간을 통째로 돌려 저장한 뒤, 창 크기를 바꿔가며 사후 재집계했다.",
        "",
        "## 2. 전구간 seed별 결과 (stat)",
        "",
        "| seed | ge3 | mean_best |",
        "|---|---|---|",
    ]
    for s in p["seeds"]:
        r = st["full_by_seed"][str(s)]
        lines.append(f"| {s} | {r['ge3']} | {r['mean']} |")
    fs = st["full_summary"]
    lines += [
        f"| **평균/표준편차** | **{fs['mean_ge3']}** / {fs['std_ge3']} | "
        f"min {fs['min_ge3']} · max {fs['max_ge3']} |",
        "",
        f"전구간(n={p['n_draws']})에서도 seed 만으로 ge3 가 **{fs['range_ge3']}** 폭으로 갈린다.",
        f"null 은 {p['p0']} 이다.",
        "",
        "## 3. 잡음 곡선 — 창 크기에 따른 흔들림 (stat)",
        "",
        "`seed 표준편차` = 같은 데이터에서 seed 만 바꿨을 때의 흔들림 (우리가 만든 잡음).",
        "`이항 SE` = 추첨이 랜덤이라 어쩔 수 없는 흔들림.",
        "`팽창계수` = 앞을 뒤로 나눈 값. 1 보다 크면 파이프라인이 잡음을 **더하고** 있다는 뜻.",
        "",
        "| 창 n | 타일수 | seed 표준편차 | seed 폭(평균) | seed 폭(최대) | 이항 SE | 팽창계수 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in st["noise_curve"]:
        tag = " (전구간)" if r["is_full_range"] else ""
        lines.append(
            f"| {r['window_n']}{tag} | {r['n_tiles']} | **{r['seed_std_mean']}** | "
            f"{r['seed_range_mean']} | {r['seed_range_max']} | {r['binomial_se']} | "
            f"**{r['inflation']}** |"
        )

    lines += [
        "",
        p["interpretation_ko"],
        "",
        (
            "## 4. 잡음은 1/√n 으로 줄어드는가"
            if not p["floor_established"]
            else "## 4. 가장 중요한 발견 — 줄어들지 않는 바닥"
        ),
        "",
        "위 표에서 창을 키워도 seed 표준편차가 **1/√n 만큼 줄지 않는다**. 이항 SE 는",
        f"n=50→{p['n_draws']} 에서 {mdl['binom_shrink']}배 줄지만, seed 표준편차는 "
        f"{mdl['seed_shrink']}배밖에 안 줄었다.",
        "",
        "분산을 다음 형태로 적합했다 (타일 수 가중 최소제곱).",
        "",
        "```",
        "seed_var(n) = a²/n + b²",
        f"a = {mdl['a']}      b = {mdl['irreducible_seed_std']}      가중 R² = {mdl['weighted_r2']}",
        "```",
        "",
        "| 창 n | 관측 표준편차 | 적합값 |",
        "|---|---|---|",
    ]
    for pt in mdl["points"]:
        lines.append(f"| {pt['window_n']} | {pt['observed_std']} | {pt['fitted_std']} |")
    lines += [
        "",
        f"`a²/n` 은 회차를 늘리면 평균되어 사라진다. 남는 건 **b = "
        f"{mdl['irreducible_seed_std']}** 다.",
        (
            "이건 회차를 무한히 늘려도 남는다. 즉 **백테스트를 아무리 길게 해도 seed 선택만으로 "
            f"ge3 가 표준편차 {mdl['irreducible_seed_std']} 만큼 계속 흔들린다.**"
            if p["floor_established"]
            else "다만 이 b 가 진짜 0 보다 큰지는 아래 4-B 에서 따로 확인해야 한다. "
            "적합이 값을 하나 내놓는다는 것과 그 값이 0 과 구별된다는 것은 다른 얘기다."
        ),
        "",
        *_section_floor_precision(p, mdl),
        "## 5. R38 게이트 보정",
        "",
        "seed 잡음과 추첨 잡음은 원인이 다르므로 분산을 더한다. 팽창은 n 에 따라 달라진다",
        "(작은 n 에서는 추첨 잡음이 지배하고, 큰 n 에서는 seed 바닥이 지배한다).",
        "",
        "```",
        "총 SE(n) = sqrt( p0(1−p0)/n  +  a²/n + b² )",
        "```",
        "",
        "| n | K셀 | seed 표준편차(모형) | 배율 | 단일 MDD → 보정 | 선택보정 p95 → 보정 |",
        "|---|---|---|---|---|---|",
    ]
    for g in p["inflated_gates"]:
        lines.append(
            f"| {g['n']} | {g['k_cells']} | {g['seed_std_modeled']} | ×{g['se_factor']} | "
            f"{g['mdd_single_pair']} → **{g['mdd_single_pair_infl']}** | "
            f"{g['mdd_selection_p95']} → **{g['mdd_selection_p95_infl']}** |"
        )

    lines += [
        "",
        "## 6. 다른 뇌",
        "",
        "| 뇌 | 전구간 ge3 평균 | seed 표준편차 | seed 폭 | 팽창계수(전구간) |",
        "|---|---|---|---|---|",
    ]
    for b in BRAINS:
        s = p[b]["full_summary"]
        curve = [r for r in p[b]["noise_curve"] if r["is_full_range"]]
        infl = curve[0]["inflation"] if curve else "미확인"
        lines.append(
            f"| {b} | {s['mean_ge3']} | {s['std_ge3']} | {s['range_ge3']} | {infl} |"
        )

    lines += [
        "",
        *_section_brain_order(p),
        "## 7. 결론",
        "",
        p["verdict"]["detail_ko"],
        "",
        "## 8. 한계",
        "",
        f"- seed {len(p['seeds'])}개로 잰 표준편차다. 자유도 {len(p['seeds']) - 1} 에서 오는",
        "  불확실성은 4-B(바닥값 잭나이프)와 6-B(서열 구분가능성)에서 정량화했다.",
        "- 큰 창(800·전구간)은 타일이 1개뿐이라 그 점의 추정이 가장 불안하다. 그래서",
        "  적합에 타일 수를 가중치로 썼다.",
        "- 창 타일은 겹치지 않게 잘랐다. 다만 초기 회차는 학습 이력이 짧아 후기 회차와",
        "  성격이 다를 수 있다.",
        "- 분산 모형은 `stat` 기준이다. 뇌마다 다르므로 6절 표를 함께 보라.",
        "- 이 도구는 잡음을 **재기만** 한다. 잡음을 줄이는 패치는 별건이다.",
        "",
        f"- 원자료: `docs/benchmarks/{RAW_JSON.name}` · 요약: `docs/benchmarks/{OUT_JSON.name}`",
        f"- 이전: `{PRIOR_SEED_DIAG}`",
        "",
    ]
    return "\n".join(lines)


def summarize_full(per_seed: dict[str, list[int]]) -> dict[str, Any]:
    seeds = sorted(per_seed.keys())
    ge3s = [ge3_of(per_seed[s]) for s in seeds]
    means = [mean(per_seed[s]) for s in seeds]
    return {
        "mean_ge3": round(mean(ge3s), 6),
        "std_ge3": round(pstdev(ge3s), 6) if len(ge3s) > 1 else 0.0,
        "min_ge3": round(min(ge3s), 6),
        "max_ge3": round(max(ge3s), 6),
        "range_ge3": round(max(ge3s) - min(ge3s), 6),
        "mean_of_means": round(mean(means), 6),
    }


def load_cached_raw(seeds: list[int]) -> tuple[list[int], dict[str, Any]] | None:
    """저장된 원자료 재사용 (walk 10분 절약). seed 구성이 다르면 쓰지 않는다."""
    if os.environ.get("K_NF_REUSE", "").strip() != "1" or not RAW_JSON.exists():
        return None
    cached = json.loads(RAW_JSON.read_text(encoding="utf-8"))
    if list(cached.get("seeds") or []) != seeds:
        print("  [reuse] seed 불일치 → 재실행", file=sys.stderr)
        return None
    return [int(x) for x in cached["draw_nos"]], cached["best_of_5_by_brain_seed"]


def collect_raw(
    seeds: list[int], lo: int, hi: int, actuals: dict[int, set[int]], t0: float
) -> tuple[list[int], dict[str, dict[str, list[int]]], bool]:
    cached = load_cached_raw(seeds)
    if cached is not None:
        dnos, raw = cached
        print(f"  [reuse] 원자료 재사용 n={len(dnos)} · walk 생략", flush=True)
        return dnos, raw, True

    raw: dict[str, dict[str, list[int]]] = {b: {} for b in BRAINS}
    draw_nos_ref: list[int] = []
    for i, s in enumerate(seeds, 1):
        ts = time.time()
        dnos, best = walk_one_seed(s, lo, hi, actuals)
        if not draw_nos_ref:
            draw_nos_ref = dnos
        elif dnos != draw_nos_ref:
            print(
                f"  [warn] seed={s} 회차 집합 불일치 ({len(dnos)} vs {len(draw_nos_ref)})",
                file=sys.stderr,
            )
        for b in BRAINS:
            raw[b][str(s)] = best[b]
        print(
            f"  [{i}/{len(seeds)}] seed={s} n={len(dnos)} "
            f"stat_ge3={ge3_of(best['stat']):.4f} "
            f"({time.time() - ts:.0f}s · 누적 {time.time() - t0:.0f}s)",
            flush=True,
        )
    return draw_nos_ref, raw, False


def summarize_brains(
    raw: dict[str, dict[str, list[int]]], seeds: list[int], p0: float
) -> dict[str, Any]:
    return {
        b: {
            "full_by_seed": {
                str(s): {
                    "ge3": round(ge3_of(raw[b][str(s)]), 6),
                    "mean": round(mean(raw[b][str(s)]), 6),
                }
                for s in seeds
            },
            "full_summary": summarize_full(raw[b]),
            "noise_curve": noise_curve(raw[b], p0),
        }
        for b in BRAINS
    }


def main() -> int:
    t0 = time.time()
    n_seeds = _env_int("K_NF_SEEDS", len(DEFAULT_SEEDS))
    seeds = list(DEFAULT_SEEDS[:n_seeds])

    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    row = conn.execute("SELECT MIN(draw_no) a, MAX(draw_no) b FROM lotto_draws").fetchone()
    conn.close()
    db_lo, db_hi = int(dict(row)["a"]), int(dict(row)["b"])

    lo = _env_int("K_NF_LO", max(db_lo + 52, 53))
    hi = _env_int("K_NF_HI", db_hi)
    actuals = load_actuals(lo, hi)
    print(f"[{BENCH_ID}] range {lo}~{hi} (DB {db_lo}~{db_hi}) · seeds {seeds}", flush=True)

    draw_nos_ref, raw, reused = collect_raw(seeds, lo, hi, actuals, t0)

    p0 = null_ge3(5)
    per_brain = summarize_brains(raw, seeds, p0)

    model = fit_variance_model(per_brain["stat"]["noise_curve"])
    floor = model["irreducible_seed_std"]
    jack = jackknife_model(raw["stat"], p0)
    prec = pairwise_resolvable(
        {b: float(per_brain[b]["full_summary"]["std_ge3"]) for b in BRAINS},
        len(seeds),
    )
    infl_gates = [
        inflated_gate(n, k, p0, model)
        for n, k in ((50, 10), (100, 10), (200, 9), (500, 9), (len(draw_nos_ref), 1))
    ]

    prior = json.loads((ROOT / PRIOR_SEED_DIAG).read_text(encoding="utf-8"))
    prior_range = float(prior["stat"]["summary"]["range_ge3"])

    full_wf = json.loads(
        (ROOT / "docs" / "benchmarks" / "20260803_KFUTURE_WIRE_FULL.json").read_text(
            encoding="utf-8"
        )
    )
    full_delta = float(full_wf["overall"]["delta_ge3_vs_null"])

    fs = per_brain["stat"]["full_summary"]
    b_lo = jack["b"]["ci95"][0] if jack.get("available") else None
    floor_solid = b_lo is not None and b_lo > 0
    delta_below_lo = b_lo is not None and abs(full_delta) < b_lo

    if not floor_solid:
        code = "FLOOR_NOT_ESTABLISHED"
        head = (
            f"바닥 점추정은 {floor} 이지만 신뢰구간 하단이 "
            f"{b_lo if b_lo is not None else '미산출'} — 바닥의 존재를 단정할 수 없다"
        )
    elif floor >= 0.005:
        code = "IRREDUCIBLE_SEED_FLOOR"
        head = (
            f"회차를 아무리 늘려도 사라지지 않는 seed 잡음 바닥 {floor} 확인"
            f"(95% CI {jack['b']['ci95']}) — 이보다 작은 Δ 는 표본을 늘려도 판정 불가"
        )
    else:
        code = "SMALL_SEED_FLOOR"
        head = f"seed 잡음 바닥 {floor}(CI {jack['b']['ci95']}) — 작지만 0 은 아니다"

    g50 = next(g for g in infl_gates if g["n"] == 50)
    detail = (
        f"전구간 n={len(draw_nos_ref)} · seed {len(seeds)}개에서 stat 의 ge3 는 "
        f"{fs['min_ge3']}~{fs['max_ge3']} (폭 **{fs['range_ge3']}** · 표준편차 {fs['std_ge3']}) 로 갈린다. "
        f"파라미터도 데이터도 추첨 결과도 전부 같은데 seed 하나로 이만큼 움직인다.\n\n"
        f"잡음이 **1/√n 으로 깔끔하게 줄지는 않는다**. 분산을 `a²/n + b²` 로 적합하면 "
        f"a = {model['a']}, b = **{floor}** 가 나온다(가중 R²={model['weighted_r2']}).\n\n"
        f"이번엔 그 바닥값 자체의 오차도 쟀다. seed 를 하나씩 빼며 {len(seeds)}번 다시 적합한 "
        f"결과 b 의 95% 신뢰구간은 **{jack['b']['ci95']}** (표준오차 {jack['b']['se']})다. "
        + (
            "구간 하단이 0 보다 크므로 **바닥의 존재 자체는 확정**이다.\n\n"
            if floor_solid
            else "구간 하단이 0 에 닿는다. 바닥이 있다는 주장부터 다시 봐야 한다.\n\n"
        )
        + f"이 바닥을 실제 판정에 대보면: 전구간 walk-forward 가 측정한 null 대비 Δ 는 "
        f"**{full_delta:+.4f}** 였다. 점추정 바닥 {floor} 보다 작고, "
        + (
            f"보수적으로 신뢰구간 하단 {b_lo} 을 써도 여전히 작다. "
            "즉 그 판정은 표본을 더 모아도 결론이 나지 않는다.\n\n"
            if delta_below_lo
            else (
                f"이전 판(seed 10개)에서는 바닥이 {PRIOR_FLOOR_10SEED} 로 나와 "
                f"'Δ 가 바닥보다 작으니 표본을 늘려도 영원히 판정 불가'라고 적었다. "
                f"**그 주장을 철회한다.** seed 를 {len(seeds)}개로 늘리자 바닥은 "
                f"{floor} 로 절반이 됐고, 0 과 구별되지 않는다. "
                f"바닥의 존재를 전제로 한 결론이므로 전제가 무너지면 결론도 무너진다.\n\n"
                f"대신 이렇게 말해야 한다. 전 역사를 다 써도 n={len(draw_nos_ref)} 이고 "
                f"그때 seed 표준편차 실측이 {fs['std_ge3']}, 보정 단일 MDD 가 "
                f"{infl_gates[-1]['mdd_single_pair_infl']} 다. Δ {full_delta:+.4f} 는 "
                f"어느 쪽에도 한참 못 미친다. 즉 **'원리적으로 영원히 불가'가 아니라 "
                f"'가용한 데이터로는 불가'** 다.\n\n"
            )
        )
        + f"뇌별 서열도 이번엔 따졌다(R39). seed {len(seeds)}개 기준 구분 가능한 쌍은 "
        f"**{prec['n_resolvable']}/{prec['n_pairs']}** 다. "
        + (
            "세 뇌의 잡음 크기는 서로 구별되지 않으므로 서열을 인용하면 안 된다. "
            "20260808 NOISE-SOURCE 가 독립 측정으로 낸 결론과 일치한다.\n\n"
            if prec["n_resolvable"] == 0
            else f"{prec['meaning_ko']}\n\n"
        )
        + f"실무 결론: n=50·10셀 판정의 보정 선택보정 임계는 **{g50['mdd_selection_p95_infl']}** "
        f"이다(보정 전 {g50['mdd_selection_p95']}). 이전 n=100 단일 추정(폭 {prior_range})은 "
        f"이제 잡음 곡선과 보정 임계표로 대체됐다."
    )

    payload: dict[str, Any] = {
        "bench_id": BENCH_ID,
        "date": "2026-08-08",
        "ts": datetime.now(timezone.utc).isoformat(),
        "wire": False,
        "policy": {
            "read_only": True,
            "db_write": False,
            "constant_change": False,
            "ticket_path_change": False,
        },
        "draw_range": [lo, hi],
        "n_draws": len(draw_nos_ref),
        "seeds": seeds,
        "p0": round(p0, 6),
        "eval": "best_of_5 · signal_pool expand+repack (SEED-DIAG 와 동일 경로)",
        "prior": {"file": PRIOR_SEED_DIAG, "n": 100, "range_ge3": prior_range},
        "stat": per_brain["stat"],
        "markov": per_brain["markov"],
        "review": per_brain["review"],
        "variance_model": model,
        "irreducible_seed_std": floor,
        "floor_uncertainty": jack,
        "floor_ci_lower": b_lo,
        "floor_established": floor_solid,
        "full_wf_delta_vs_null": full_delta,
        "full_wf_below_floor": abs(full_delta) < floor,
        "full_wf_below_floor_ci_lower": delta_below_lo,
        "inflated_gates": infl_gates,
        "interpretation_ko": (
            "팽창계수가 1 을 넘으면, 우리가 보는 흔들림 중 일부는 추첨 탓이 아니라 "
            "**파이프라인 탓**이라는 뜻이다. 이 경우 게이트 임계를 그만큼 올려야 하고, "
            "올리지 않으면 잡음을 신호로 착각한다."
        ),
        "verdict": {"code": code, "headline_ko": head, "detail_ko": detail},
        "elapsed_sec": round(time.time() - t0, 1),
        "walk_reused_from_raw": reused,
        "walk_elapsed_sec_original": 601.3,
        "tool": "tools/_k_stat_seed_noise_floor.py",
    }
    payload[PRECISION_KEY] = prec
    payload[GATE_KEY] = gate_block(
        n=len(draw_nos_ref),
        k_cells=len(seeds),
        delta=fs["range_ge3"],
        metric="ge3 (seed 간 폭)",
        label="seed 잡음 하한 실측 — 판정이 아니라 잡음 자체의 측정",
    )

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    RAW_JSON.write_text(
        json.dumps(
            {
                "bench_id": BENCH_ID + "-RAW",
                "raw_data": True,
                "note": "회차별 best-of-5 적중수 원측정치. 판정 아님 (R38 면제).",
                "draw_nos": draw_nos_ref,
                "seeds": seeds,
                "best_of_5_by_brain_seed": raw,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    md = build_report(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        DRIVE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"drive copy skip: {e}", file=sys.stderr)

    print(f"[{BENCH_ID}] {code} — {head}")
    print(f"  stat 전구간 ge3 {fs['min_ge3']}~{fs['max_ge3']} 폭={fs['range_ge3']} std={fs['std_ge3']}")
    if jack.get("available"):
        print(
            f"  바닥 b={floor} 잭나이프SE={jack['b']['se']} CI={jack['b']['ci95']} "
            f"· |Δ{full_delta:+.4f}| < CI하단? {delta_below_lo}"
        )
    print(
        f"  R39 서열 구분가능쌍={prec['n_resolvable']}/{prec['n_pairs']} "
        f"(필요 seed 최대 {prec['samples_needed_max']})"
    )
    for pr in prec["pairs"]:
        print(
            f"    {pr['pair'][0]:7s}vs {pr['pair'][1]:7s} 차이={pr['diff']:.6f} "
            f"임계={pr['resolve_threshold']:.6f} 구분={pr['resolvable']} "
            f"필요seed={pr['samples_needed']}"
        )
    for r in per_brain["stat"]["noise_curve"]:
        print(
            f"  n={r['window_n']:>5} tiles={r['n_tiles']:>3} seed_std={r['seed_std_mean']:.6f} "
            f"binom_se={r['binomial_se']:.6f} inflation={r['inflation']}"
        )
    print(f"  elapsed={payload['elapsed_sec']}s -> {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
