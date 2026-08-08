# -*- coding: utf-8 -*-
"""K-SEED-AVERAGE-DESIGN — seed 평균화 설계·검증 (READ-ONLY · wire=False · R38/R39).

배경
----
NOISE-SOURCE 진단에서 잡음 유입점이 **가중치 계산이 아니라 '뽑기'** 로 확정됐다.
가중치는 seed 를 바꿔도 완전히 같은 값이 나왔고, 흔들리는 것은 그 가중치로
후보 세트를 뽑는 단계였다. 뽑기가 잡음원이면 처방은 하나다: **같은 회차를
여러 번 뽑아 합친 뒤 결정한다.** 독립 반복 R회면 뽑기 잡음은 √R 로 줄어든다.

이 도구는 그 설계가 실제로 √R 로 줄어드는지, 그리고 적중(ge3)을 깎지 않는지
**배선 없이** 검증한다.

두 가지 합치는 방식
-----------------
1. `hybrid_R` — 현행 발권경로 그대로. R개 pool 을 이어붙여 `repack_by_brain`
   에 넣는다. 점수몰아주기(rank1~3)는 R배 표본으로 안정되지만, 하이브리드가
   집는 **pool 세트 4·5 슬롯은 평균되지 않는다** (`pred_set_no` 로 dict 를
   만들기 때문에 마지막 pool 것만 남는다). 즉 절반만 평균된다.
2. `score_R` — 5장 전부를 평균 점수 순위로 만든다. pool 슬롯을 쓰지 않으므로
   뽑기 잡음이 원리적으로 전부 제거된다. 대신 하이브리드 조립을 버린다.

이 둘을 같이 재야 "어디까지 평균이 먹히는가"와 "그 대가는 얼마인가"가 갈린다.

측정 구조
--------
- 바깥 seed(outer) O개 = 서로 다른 '반복 묶음'. 이들 사이의 표준편차가 잔여 잡음.
- 각 outer 안에서 안쪽 seed R개를 뽑아 합친다.
- 학습기(learner)는 outer 마다 따로 두고, **R=1 pool 로만** 갱신한다
  (현행 단일 seed 경로와 같은 상태를 유지해 비교를 공정하게 만든다).

정책
----
READ-ONLY. DB 쓰기 없음 · 상수/배선/발권경로 무변경 · wire=False.
`random.choices` · `_get_draws_before` 동결 준수 (호출만).

Usage
-----
  python tools/_k_seed_average_design.py
  K_SA_LO=1206 K_SA_HI=1235 K_SA_OUTER=2 python tools/_k_seed_average_design.py
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

from tools.k_gate import GATE_KEY, gate_block, null_ge3  # noqa: E402
from tools.k_precision import PRECISION_KEY, resolvable  # noqa: E402

BENCH_ID = "K-SEED-AVERAGE-DESIGN"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KSEED_AVERAGE_DESIGN.json"
RAW_JSON = ROOT / "docs" / "benchmarks" / "20260808_KSEED_AVERAGE_DESIGN_raw.json"
OUT_MD = ROOT / "reports" / "20260808_KSEED_AVERAGE_DESIGN.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BRAINS = ("stat", "markov", "review")
R_LIST = (1, 2, 4, 8)
R_MAX = max(R_LIST)
METHODS = ("hybrid", "score")
DEFAULT_OUTER = 10
DEFAULT_SPAN = 300
SEED_BASE = 20260808

SEP7 = "|---|---|---|---|---|---|---|"


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    return int(v) if v else default


def inner_seeds(outer_idx: int, r_max: int = R_MAX) -> list[int]:
    """outer 묶음 하나가 쓸 안쪽 seed 목록. 묶음끼리 겹치지 않게 뽑는다."""
    rng = random.Random(SEED_BASE + outer_idx * 7919)
    return rng.sample(range(1, 1_000_000), r_max)


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


def max_draw_no() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    row = conn.execute("SELECT MAX(draw_no) AS m FROM lotto_draws").fetchone()
    conn.close()
    return int(dict(row)["m"])


def _best_from_repacked(repacked: list[dict[str, Any]], actual: set[int]) -> dict[str, int] | None:
    """뇌별 상위 5세트의 최고 적중수 (잡음바닥 도구와 동일 규칙)."""
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


def _score_only_sets(
    pool_br: dict[str, list[dict]],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
) -> dict[str, list[list[int]]]:
    """평균 점수 순위만으로 5장을 만든다 (pool 슬롯 미사용)."""
    from app.testlotto.signal_pool import number_scores, repack_sets

    out: dict[str, list[list[int]]] = {}
    for tag in BRAINS:
        pool = pool_br.get(tag, [])
        if not pool:
            continue
        out[tag] = repack_sets(number_scores(pool, hint, num_ema, pos_ema))
    return out


def _best_from_sets(
    sets_by_tag: dict[str, list[list[int]]], actual: set[int]
) -> dict[str, int] | None:
    vals: dict[str, int] = {}
    for tag in BRAINS:
        sets = sets_by_tag.get(tag, [])
        if not sets:
            return None
        vals[tag] = max(len(set(s) & actual) for s in sets[:5])
    return vals


def _eval_one_draw(
    pools: list[list[dict]],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
    actual: set[int],
    dno: int,
) -> dict[str, dict[str, int]] | None:
    """한 회차에서 R별·방식별 뇌 적중수. 하나라도 비면 그 회차를 버린다."""
    from app.testlotto.signal_pool import _pool_by_brain, repack_by_brain

    got: dict[str, dict[str, int]] = {}
    for r in R_LIST:
        merged = [c for p in pools[:r] for c in p]
        pool_br = _pool_by_brain(merged)

        hy = _best_from_repacked(
            repack_by_brain(pool_br, hint, num_ema, pos_ema, target_draw_no=dno),
            actual,
        )
        sc = _best_from_sets(_score_only_sets(pool_br, hint, num_ema, pos_ema), actual)
        if hy is None or sc is None:
            return None
        got[f"hybrid_R{r}"] = hy
        got[f"score_R{r}"] = sc
    return got


def walk_one_outer(
    outer_idx: int, lo: int, hi: int, actuals: dict[int, set[int]]
) -> tuple[list[int], dict[str, dict[str, list[int]]]]:
    """outer 묶음 하나로 lo~hi walk-forward. 회차별 적중수를 원자료 그대로 반환."""
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.signal_pool import (
        RollingSignalLearner,
        _build_hint,
        _get_draws_before,
        _pool_by_brain,
        expand_pool,
        warm_learner_to_draw,
    )

    seeds = inner_seeds(outer_idx)
    learner = RollingSignalLearner()
    warm_learner_to_draw(learner, max(1, lo - 200), lo, seed=seeds[0])

    draw_nos: list[int] = []
    hits: dict[str, dict[str, list[int]]] = {
        f"{m}_R{r}": {b: [] for b in BRAINS} for m in METHODS for r in R_LIST
    }

    for dno in range(lo, hi + 1):
        if dno not in actuals:
            continue
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        if not draws:
            continue

        num_ema, pos_ema = learner.snapshot()
        pools = [_seeded_pool(expand_pool, draws, dno, s) for s in seeds]
        hint = _build_hint(draws, dno)

        actual = actuals[dno]
        got = _eval_one_draw(pools, hint, num_ema, pos_ema, actual, dno)
        if got is not None:
            draw_nos.append(dno)
            _record(hits, got)

        learner.update_from_pool(_pool_by_brain(pools[0]), actual)

    return draw_nos, hits


def _seeded_pool(expand_pool: Any, draws: list[dict], dno: int, seed: int) -> list[dict]:
    """전역 seed 까지 맞춘 뒤 pool 하나를 뽑는다 (현행 경로와 동일 순서)."""
    random.seed(seed)
    return expand_pool(draws, dno, seed=seed)


def _record(hits: dict[str, dict[str, list[int]]], got: dict[str, dict[str, int]]) -> None:
    for key, vals in got.items():
        for b in BRAINS:
            hits[key][b].append(vals[b])


def ge3_of(vals: list[int]) -> float:
    return sum(1 for v in vals if v >= 3) / len(vals) if vals else 0.0


def loglog_slope(xs: list[float], ys: list[float]) -> float | None:
    """ln y = a + b·ln x 의 b. 잡음이 √R 로 줄면 b ≈ −0.5."""
    pts = [(math.log(x), math.log(y)) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len(pts) < 2:
        return None
    mx = mean(p[0] for p in pts)
    my = mean(p[1] for p in pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den <= 0:
        return None
    return sum((p[0] - mx) * (p[1] - my) for p in pts) / den


def fit_decomposition(stds: list[float]) -> dict[str, Any]:
    """σ²(R) = A + B/R 로 분해한다.

    B/R 은 뽑기 잡음 — R 을 키우면 사라진다.
    A 는 R 과 무관한 잔여 — 학습기 경로처럼 평균되지 않는 부분이다.
    이 A 가 '평균화로 갈 수 있는 한계'를 정한다.
    """
    xs = [1.0 / r for r in R_LIST]
    ys = [s * s for s in stds]
    mx, my = mean(xs), mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    if den <= 0:
        return {"fit_ok": False}
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    a = my - b * mx
    a_c, b_c = max(a, 0.0), max(b, 0.0)
    tot = a_c + b_c
    return {
        "fit_ok": True,
        "sigma_floor_A": round(math.sqrt(a_c), 6),
        "sigma_draw_B": round(math.sqrt(b_c), 6),
        "removable_share_at_R1": round(b_c / tot, 4) if tot > 0 else None,
        "sigma_at_R_inf": round(math.sqrt(a_c), 6),
        "note_ko": "A>0 이면 평균화만으로는 그 아래로 못 내려간다 (학습기 경로 등)",
    }


def resolution_gain(stds: list[float], n_draws: int, p0: float) -> dict[str, Any]:
    """평균화가 '판정 해상도'를 얼마나 올려주는지 비용과 함께 계산한다.

    튜닝 판정의 총 잡음은 두 갈래가 겹친 것이다.
      · 추첨이 랜덤이라 생기는 이항 잡음 — 우리가 못 줄인다
      · 파이프라인이 만드는 seed 잡음 — 평균화 대상
    총합은 √(이항² + seed²) 이므로, seed 쪽을 반으로 줄여도 총합은 그만큼 안 준다.
    비용은 R배로 정직하게 붙으므로 둘을 나란히 놓아야 판단할 수 있다.
    """
    bse = math.sqrt(p0 * (1.0 - p0) / n_draws)
    tot = [math.sqrt(bse**2 + s**2) for s in stds]
    rows = []
    for r, s, t in zip(R_LIST, stds, tot):
        rows.append(
            {
                "R": r,
                "seed_std": round(s, 6),
                "total_std": round(t, 6),
                "resolution_gain_vs_R1": round(tot[0] / t, 4) if t > 0 else None,
                "cost_multiplier": r,
                "gain_per_cost": round((tot[0] / t) / r, 4) if t > 0 else None,
            }
        )
    return {
        "binomial_se": round(bse, 6),
        "ceiling_gain_if_seed_noise_zero": round(tot[0] / bse, 4),
        "rows": rows,
    }


def budget_compare(res: dict[str, Any], n_draws: int) -> dict[str, Any]:
    """같은 해상도를 'seed 반복' 대신 '회차 늘리기'로 사면 얼마인가.

    잡음바닥 도구(24 seed)의 분산모형은 seed_var ≈ a²/n · b≈0 이었다. 즉 seed
    잡음도 이항 잡음도 둘 다 1/√n 로 준다. 그러면 총 잡음은 R=1 에서 C/√n 이고,
    어떤 총 잡음이든 그것을 내는 **등가 회차수** n' 을 역산할 수 있다.
    R배 반복의 비용은 n·R, 회차 늘리기의 비용은 n' 이다. 둘을 나란히 놓으면
    "이 잡음을 사는 가장 싼 방법"이 바로 나온다.
    """
    rows = res["rows"]
    c = rows[0]["total_std"] * math.sqrt(n_draws)
    out = []
    for r in rows:
        t = r["total_std"]
        n_eq = (c / t) ** 2 if t > 0 else None
        cost_avg = n_draws * r["R"]
        out.append(
            {
                "R": r["R"],
                "total_std": t,
                "equiv_n_at_R1": round(n_eq, 1) if n_eq else None,
                "cost_seed_averaging": cost_avg,
                "cost_more_draws": round(n_eq, 1) if n_eq else None,
                "averaging_overpay": (
                    round(cost_avg / n_eq, 2) if n_eq and n_eq > 0 else None
                ),
            }
        )
    return {
        "basis_ko": "잡음바닥 24seed 분산모형 b≈0 → 총 잡음 ∝ 1/√n",
        "n_draws": n_draws,
        "rows": out,
    }


def summarize(
    raw: dict[str, Any], brain: str
) -> dict[str, Any]:
    """한 뇌에 대해 방식×R 별 ge3 평균·outer 표준편차."""
    outers = raw["outers"]
    rows: dict[str, dict[str, Any]] = {}
    for m in METHODS:
        for r in R_LIST:
            key = f"{m}_R{r}"
            per_outer = [ge3_of(o["hits"][key][brain]) for o in outers]
            rows[key] = {
                "method": m,
                "R": r,
                "ge3_by_outer": [round(v, 6) for v in per_outer],
                "ge3_mean": round(mean(per_outer), 6),
                "outer_std": round(pstdev(per_outer), 6),
            }
    return rows


def decay_check(rows: dict[str, Any], method: str, n_outer: int) -> dict[str, Any]:
    """R 을 키울 때 잔여 잡음이 1/√R 로 줄었는지."""
    xs = [float(r) for r in R_LIST]
    ys = [rows[f"{method}_R{r}"]["outer_std"] for r in R_LIST]
    slope = loglog_slope(xs, ys)
    s1, s8 = ys[0], ys[-1]
    res = resolvable(s1, s8, n_outer)
    if min(s1, s8) <= 0.0:
        # σ̂=0 은 표본이 모자라 우연히 겹친 경우다. 정규근사 임계가 0 으로 붕괴해
        # '구분됨' 이 거짓 양성으로 나오므로 판정에서 뺀다.
        res = {**res, "resolvable": False, "degenerate_zero_sigma": True}
    return {
        "method": method,
        "R": list(R_LIST),
        "outer_std": [round(v, 6) for v in ys],
        "std_R1_over_std_Rmax": round(s1 / s8, 4) if s8 > 0 else None,
        "expected_ratio_sqrtR": round(math.sqrt(R_MAX), 4),
        "loglog_slope": round(slope, 4) if slope is not None else None,
        "slope_target": -0.5,
        "R1_vs_Rmax_resolvable": res,
        "seeds_needed_if_unresolved": (
            None if res["resolvable"] else res["samples_needed"]
        ),
        "decomposition": fit_decomposition(ys),
    }


def _payload_meta(lo: int, hi: int, n_outer: int, n_draws: int, secs: float) -> dict[str, Any]:
    return {
        "id": BENCH_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "read_only": True,
            "wire": False,
            "db_write": False,
            "frozen_respected": ["random.choices", "_get_draws_before", "boost_caps"],
        },
        "design": {
            "range": [lo, hi],
            "n_draws": n_draws,
            "n_outer": n_outer,
            "R_list": list(R_LIST),
            "methods": {
                "hybrid": "R개 pool 이어붙여 현행 repack_by_brain (pool 4·5 슬롯은 평균 안 됨)",
                "score": "평균 점수 순위로 5장 전부 구성 (pool 슬롯 미사용)",
            },
            "learner_update": "R=1 pool 로만 갱신 (현행 경로와 동일 상태 유지)",
        },
        "elapsed_sec": round(secs, 1),
    }


def build_payload(raw: dict[str, Any], secs: float) -> dict[str, Any]:
    lo, hi = raw["range"]
    n_outer = len(raw["outers"])
    n_draws = len(raw["outers"][0]["draw_nos"])
    p0 = null_ge3()

    per_brain: dict[str, Any] = {}
    for b in BRAINS:
        rows = summarize(raw, b)
        base = rows["hybrid_R1"]
        best_key = max(
            (k for k in rows if k != "hybrid_R1"),
            key=lambda k, _r=rows: _r[k]["ge3_mean"],
        )
        delta = rows[best_key]["ge3_mean"] - base["ge3_mean"]
        per_brain[b] = {
            "rows": rows,
            "baseline": "hybrid_R1",
            "baseline_ge3": base["ge3_mean"],
            "best_key": best_key,
            "best_ge3": rows[best_key]["ge3_mean"],
            "delta_vs_baseline": round(delta, 6),
            "decay": {m: decay_check(rows, m, n_outer) for m in METHODS},
            "resolution": {
                m: resolution_gain(
                    [rows[f"{m}_R{r}"]["outer_std"] for r in R_LIST], n_draws, p0
                )
                for m in METHODS
            },
        }
        per_brain[b]["budget"] = {
            m: budget_compare(per_brain[b]["resolution"][m], n_draws)
            for m in METHODS
        }

    stat = per_brain["stat"]
    payload = _payload_meta(lo, hi, n_outer, n_draws, secs)
    payload["null_ge3_5tickets"] = round(p0, 6)
    payload["per_brain"] = per_brain
    payload[GATE_KEY] = gate_block(
        n=n_draws,
        k_cells=len(METHODS) * len(R_LIST) - 1,
        delta=stat["delta_vs_baseline"],
        metric="ge3(stat, best-of-5)",
        label="seed 평균화 최선안 vs 현행 단일 seed",
    )
    payload[PRECISION_KEY] = {
        "rule": "R39",
        "module": "tools/k_precision.py",
        "note": "잔여 잡음 감소는 σ̂ 비교이므로 σ̂ 자체의 오차를 넘는지 확인한다",
        "stat_hybrid": stat["decay"]["hybrid"]["R1_vs_Rmax_resolvable"],
        "stat_score": stat["decay"]["score"]["R1_vs_Rmax_resolvable"],
    }
    payload["verdict"] = verdict_of(payload)
    return payload


def verdict_of(payload: dict[str, Any]) -> dict[str, Any]:
    """잡음이 실제로 줄었는가 · 적중을 깎았는가 를 분리해 판정한다."""
    stat = payload["per_brain"]["stat"]
    noise_cut: list[str] = []
    for m in METHODS:
        d = stat["decay"][m]
        if d["R1_vs_Rmax_resolvable"]["resolvable"] and d["outer_std"][-1] < d["outer_std"][0]:
            noise_cut.append(m)

    gate_ok = bool(payload[GATE_KEY]["actionable"])
    if not noise_cut:
        code = "NOISE_CUT_NOT_ESTABLISHED"
        why = (
            f"outer {payload['design']['n_outer']}개로는 R1↔R{R_MAX} 잔여 잡음 차이가 "
            "측정 오차를 넘지 못했다. 감소했다고 주장할 수 없다 (R39)."
        )
    elif gate_ok:
        code = "NOISE_CUT_AND_HIT_CHANGE"
        why = "잡음 감소가 확인됐고 ge3 변화도 눈금을 넘었다. 배선 검토 대상."
    else:
        code = "NOISE_CUT_ONLY"
        why = (
            "잡음은 줄었으나 ge3 변화는 눈금 미달 = 적중은 그대로. "
            "'같은 적중을 더 안정적으로' 라는 뜻이며, 그 자체로는 성능 개선이 아니다."
        )
    return {
        "code": code,
        "noise_cut_methods": noise_cut,
        "hit_change_actionable": gate_ok,
        "why_ko": why,
    }


def _md_rows_table(rows: dict[str, Any]) -> list[str]:
    out = ["|방식|R|ge3 평균|outer 표준편차|최소|최대|Δ vs hybrid_R1|", SEP7]
    base = rows["hybrid_R1"]["ge3_mean"]
    for m in METHODS:
        for r in R_LIST:
            x = rows[f"{m}_R{r}"]
            vals = x["ge3_by_outer"]
            out.append(
                f"|{m}|{r}|{x['ge3_mean']:.4f}|{x['outer_std']:.6f}|"
                f"{min(vals):.4f}|{max(vals):.4f}|{x['ge3_mean'] - base:+.4f}|"
            )
    return out


def _md_decay(d: dict[str, Any]) -> list[str]:
    r = d["R1_vs_Rmax_resolvable"]
    lines = [
        f"- **{d['method']}** 잔여 잡음 σ: "
        + " → ".join(f"R{a}={b:.6f}" for a, b in zip(d["R"], d["outer_std"])),
        f"  - R1/R{R_MAX} 비 = {d['std_R1_over_std_Rmax']} "
        f"(1/√R 이면 {d['expected_ratio_sqrtR']})",
        f"  - log-log 기울기 = {d['loglog_slope']} (√R 감소면 −0.5)",
        f"  - R39 구분가능: **{r['resolvable']}** "
        f"(관측차 {r['diff']:.6f} vs 임계 {r['resolve_threshold']:.6f})",
    ]
    if d["seeds_needed_if_unresolved"]:
        lines.append(f"  - 이 차이를 가르려면 outer {d['seeds_needed_if_unresolved']}개 필요")
    fd = d["decomposition"]
    if fd.get("fit_ok"):
        lines.append(
            f"  - σ²=A+B/R 분해: 평균화로 지울 수 있는 몫 "
            f"**{fd['removable_share_at_R1']}** · 못 지우는 바닥 A={fd['sigma_floor_A']:.6f} "
            f"(뽑기 몫 B^½={fd['sigma_draw_B']:.6f})"
        )
    return lines


def _md_resolution(res_by_method: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for m, res in res_by_method.items():
        out += [
            f"**{m}** (이항 SE {res['binomial_se']:.6f} · seed 잡음이 0이 돼도 "
            f"해상도는 최대 {res['ceiling_gain_if_seed_noise_zero']}배)",
            "",
            "|R|seed 잡음|총 잡음|해상도 이득|비용|이득/비용|",
            "|---|---|---|---|---|---|",
        ]
        for r in res["rows"]:
            out.append(
                f"|{r['R']}|{r['seed_std']:.6f}|{r['total_std']:.6f}|"
                f"{r['resolution_gain_vs_R1']}배|{r['cost_multiplier']}배|"
                f"{r['gain_per_cost']}|"
            )
        out.append("")
    return out


def _md_budget(bud: dict[str, Any]) -> list[str]:
    out = [
        "|R|총 잡음|등가 회차수(R=1)|반복 비용|회차 비용|평균화 과지불|",
        "|---|---|---|---|---|---|",
    ]
    for r in bud["rows"]:
        out.append(
            f"|{r['R']}|{r['total_std']:.6f}|{r['equiv_n_at_R1']}|"
            f"{r['cost_seed_averaging']}|{r['cost_more_draws']}|"
            f"**{r['averaging_overpay']}배**|"
        )
    return out


def _md_wiring(payload: dict[str, Any], v: dict[str, Any]) -> list[str]:
    res = payload["per_brain"]["stat"]["resolution"]["score"]
    bud = payload["per_brain"]["stat"]["budget"]["score"]["rows"][-1]
    best = res["rows"][-1]
    if v["code"] == "NOISE_CUT_NOT_ESTABLISHED":
        return [
            f"**배선하지 않는다.** R={R_MAX} 까지 올려도 잔여 잡음 감소가 측정 오차를 "
            "넘지 못했고 (R39), 점 추정만 봐도 √R 이 예측하는 "
            f"{math.sqrt(R_MAX):.2f}배 감소가 나오지 않았다.",
            "",
            f"결정적인 것은 손익이다. 뽑기를 {R_MAX}배 하고 얻는 판정 해상도는 "
            f"**{best['resolution_gain_vs_R1']}배**에 그친다. "
            f"seed 잡음을 완전히 0으로 만들어도 상한이 "
            f"{res['ceiling_gain_if_seed_noise_zero']}배다 — 총 잡음의 큰 몫이 "
            "추첨 자체의 이항 잡음이기 때문이다.",
            "",
            f"게다가 같은 해상도를 회차 늘리기로 사면 **{bud['averaging_overpay']}배 싸다** "
            f"(R={R_MAX} 반복 비용 {bud['cost_seed_averaging']} vs 등가 회차 "
            f"{bud['equiv_n_at_R1']}). 반복은 이항 잡음을 못 건드리지만 회차는 둘 다 줄이기 "
            "때문이다.",
            "",
            "즉 **평균화는 이 파이프라인에서 값어치가 없다.** 잡음을 더 줄이려면",
            "뽑기가 아니라 평균되지 않는 쪽(학습기 경로)을 봐야 한다.",
        ]
    if v["code"] == "NOISE_CUT_ONLY":
        return [
            "잡음은 줄었고 적중은 그대로다. **성능 개선이 아니라 재현성 개선**이다.",
            "",
            f"- 얻는 것: 판정 해상도 {best['resolution_gain_vs_R1']}배 "
            f"(상한 {res['ceiling_gain_if_seed_noise_zero']}배)",
            f"- 치르는 것: 발권 1회당 뽑기 {R_MAX}배",
            f"- 이득/비용 = {best['gain_per_cost']}",
            "- 적중 기대치 변화: 없음 (게이트 미달)",
            "",
            "배선 여부는 이 손익만 보고 형이 정하면 된다.",
        ]
    return [
        "잡음 감소와 ge3 변화가 함께 확인됐다. 다만 ge3 변화 방향과 홀드아웃 검증이",
        "선행돼야 하며, 이 도구 하나로 배선을 결정하지 않는다.",
    ]


def build_md(payload: dict[str, Any]) -> str:
    d = payload["design"]
    v = payload["verdict"]
    g = payload[GATE_KEY]
    L: list[str] = [
        f"# {BENCH_ID} — seed 평균화 설계·검증",
        "",
        f"- 생성 {payload['generated_at']} · {d['range'][0]}~{d['range'][1]} "
        f"({d['n_draws']}회차) · outer {d['n_outer']} · R {d['R_list']} "
        f"· {payload['elapsed_sec']}초",
        "- READ-ONLY · **wire=False** (발권경로 무변경) · 동결 준수",
        "",
        "## 0. 결론",
        "",
        f"**{v['code']}** — {v['why_ko']}",
        "",
        "## 1. 무엇을 했나",
        "",
        "잡음 유입점이 '뽑기'로 확정됐으므로, 같은 회차를 R번 뽑아 합친 뒤 5장을 정했다.",
        "합치는 방식 두 가지를 같이 쟀다.",
        "",
        f"- `hybrid` : {d['methods']['hybrid']}",
        f"- `score`  : {d['methods']['score']}",
        "",
        f"학습기 갱신은 {d['learner_update']}.",
        "",
    ]

    for b in BRAINS:
        pb = payload["per_brain"][b]
        L += [f"## 2.{BRAINS.index(b) + 1} {b}", ""]
        L += _md_rows_table(pb["rows"])
        L += ["", "잔여 잡음 감소:", ""]
        for m in METHODS:
            L += _md_decay(pb["decay"][m])
        L += [""]

    L += [
        "## 3. 판정 게이트 (R38)",
        "",
        f"- 대상: stat `{payload['per_brain']['stat']['best_key']}` vs `hybrid_R1`",
        f"- Δ = {g['delta']:+.6f} · n={g['gate']['n']} · 탐색셀 {g['gate']['k_cells']}",
        f"- 선택보정 임계 p95 = {g['gate']['mdd_selection_p95']}",
        f"- **{g['verdict']}** — {g['why_ko']}",
        "",
        "## 4. 비용 대비 판정 해상도 (stat)",
        "",
        "평균화의 값어치는 적중이 아니라 **판정 해상도**다. 그런데 총 잡음은",
        "√(이항² + seed²) 이고 이항 쪽은 못 줄인다. 그래서 seed 잡음을 반으로 줄여도",
        "총합은 반이 되지 않는다. 비용은 정직하게 R배다.",
        "",
    ]
    L += _md_resolution(payload["per_brain"]["stat"]["resolution"])
    L += [
        "### 4-1. 같은 해상도를 '회차 늘리기'로 사면 (stat·score)",
        "",
        f"{payload['per_brain']['stat']['budget']['score']['basis_ko']}. 그러면 어떤",
        "총 잡음이든 그것을 내는 등가 회차수를 역산할 수 있다. 비용 단위는 '회차×반복' 이다.",
        "",
    ]
    L += _md_budget(payload["per_brain"]["stat"]["budget"]["score"])
    L += ["", "## 5. 배선 판단", ""]
    L += _md_wiring(payload, v)

    L += [
        "",
        "## 6. 한계",
        "",
        f"- outer {d['n_outer']}개 → σ̂ 자체의 상대오차 약 "
        f"{100 / math.sqrt(2 * (d['n_outer'] - 1)):.0f}%. R39 로 명시 반영했다.",
        "- `hybrid` 의 pool 4·5 슬롯은 구조상 평균되지 않는다. 완전 평균은 `score` 뿐이며,",
        "  `score` 는 하이브리드 조립을 버리는 대가를 치른다.",
        "- **학습기 경로는 평균하지 않았다.** R 과 무관하게 R=1 pool 로만 갱신했다.",
        "  현행 단일 seed 경로와 학습 상태를 같게 맞춰 발권 단계만 비교하기 위해서다.",
        "  따라서 σ²=A+B/R 의 A 에는 학습기 경로 잡음이 남아 있고, 이것이 평균화의 한계다.",
        "- 원자료: `docs/benchmarks/20260808_KSEED_AVERAGE_DESIGN_raw.json`",
        "",
    ]
    return "\n".join(L)


def print_console(payload: dict[str, Any]) -> None:
    v = payload["verdict"]
    print(f"\n=== {BENCH_ID} ===")
    d = payload["design"]
    print(f"range {d['range']} · n={d['n_draws']} · outer={d['n_outer']} · R={d['R_list']}")
    for b in BRAINS:
        pb = payload["per_brain"][b]
        print(f"\n[{b}] baseline hybrid_R1 ge3={pb['baseline_ge3']:.4f}")
        for m in METHODS:
            dc = pb["decay"][m]
            stds = " ".join(f"R{a}:{c:.5f}" for a, c in zip(dc["R"], dc["outer_std"]))
            print(
                f"  {m:6s} σ {stds} | 비={dc['std_R1_over_std_Rmax']} "
                f"기울기={dc['loglog_slope']} 구분={dc['R1_vs_Rmax_resolvable']['resolvable']}"
            )
        for m in METHODS:
            row = " ".join(
                f"R{r}:{pb['rows'][f'{m}_R{r}']['ge3_mean']:.4f}" for r in R_LIST
            )
            print(f"  {m:6s} ge3 {row}")
    print(f"\nGATE {payload[GATE_KEY]['verdict']} · Δ={payload[GATE_KEY]['delta']:+.6f}")
    print(f"VERDICT {v['code']} — {v['why_ko']}")


def collect(lo: int, hi: int, n_outer: int) -> dict[str, Any]:
    actuals = load_actuals(lo, hi)
    outers: list[dict[str, Any]] = []
    for i in range(n_outer):
        t0 = time.time()
        draw_nos, hits = walk_one_outer(i, lo, hi, actuals)
        outers.append({"outer": i, "seeds": inner_seeds(i), "draw_nos": draw_nos, "hits": hits})
        print(
            f"  outer {i + 1}/{n_outer} · {len(draw_nos)}회차 · {time.time() - t0:.0f}s",
            flush=True,
        )
    return {"range": [lo, hi], "outers": outers}


def main() -> None:
    hi = _env_int("K_SA_HI", 0) or max_draw_no()
    lo = _env_int("K_SA_LO", 0) or max(2, hi - DEFAULT_SPAN + 1)
    n_outer = _env_int("K_SA_OUTER", DEFAULT_OUTER)

    reuse = os.environ.get("K_SA_REUSE", "").strip() == "1" and RAW_JSON.exists()
    if reuse:
        raw = json.loads(RAW_JSON.read_text(encoding="utf-8"))
        secs = float(raw.get("walk_sec") or 0.0)
        print(f"[{BENCH_ID}] 원자료 재사용 {raw['range']} · outer {len(raw['outers'])}")
    else:
        print(f"[{BENCH_ID}] {lo}~{hi} · outer {n_outer} · R {list(R_LIST)}", flush=True)
        t0 = time.time()
        raw = collect(lo, hi, n_outer)
        secs = time.time() - t0
        raw["walk_sec"] = round(secs, 1)
        RAW_JSON.parent.mkdir(parents=True, exist_ok=True)
        RAW_JSON.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    payload = build_payload(raw, secs)
    payload["raw_reused"] = reuse
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = build_md(payload)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")

    print_console(payload)
    print(f"\n-> {OUT_JSON.relative_to(ROOT)}\n-> {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
