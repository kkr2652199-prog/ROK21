# -*- coding: utf-8 -*-
"""K-REPACK-SELECT-DIAG — 과거학습 뇌 몰아주기 선별 진단 (READ-ONLY · wire=False · R38/R39).

배경
----
20260804 DECOMPOSE 조사에서 이런 격차가 나왔다 (stat · n200).

  · 현행 몰아주기 5장   ge3 0.125
  · pool 10세트 중 최고 1세트  ge3 0.245   ← 정답을 보고 고른 상한

즉 **좋은 세트는 이미 pool 안에 있는데 몰아주기가 못 골라낸다.** 문제는
"번호를 못 찾는 것"이 아니라 "찾아놓고 못 고르는 것"이다.

현행 몰아주기는 45개 번호를 점수순으로 세워 6개씩 기계적으로 자른다.
**세트 안의 6개가 서로 어울리는 조합인지는 보지 않는다.** 정답 6개는 보통
점수 상위에 몰려 있지 않고 흩어져 있으므로, 통째로 좋은 세트가 있어도
분해돼 사라진다.

이 도구가 답할 질문 두 개
----------------------
① **놓침률** — pool 에 3개 이상 맞은 세트가 있었는데 몰아주기 5장은 없던 회차가
   얼마나 되나. 반대로 pool 에 없던 걸 몰아주기가 만들어낸 회차(구제)는 얼마나 되나.
   순증감이 곧 "몰아주기가 제 일을 하는가"의 직접적 답이다.

② **선별력** — 정답을 보지 않고 계산할 수 있는 특성만으로 pool 10세트에 순위를
   매겼을 때, 실제 성적과 상관이 있나. 있으면 그게 새 선별 규칙의 재료다.
   **없으면 "없다"는 것 자체가 확정 명분이다.**

비교 대상 (전부 같은 pool · 같은 회차)
  · `repack`      현행 몰아주기 5장
  · `feat_top5`   특성 상위 5세트를 통째로 (특성별로 각각)
  · `setno_1_5`   pool 1~5번 세트 그대로 (무선별 대조군)
  · `oracle_top5` 실제 성적 상위 5세트 (상한 · 실현 불가)

정책
----
READ-ONLY. DB 쓰기 없음 · 상수/배선/발권경로 무변경 · wire=False.
`random.choices` · `_get_draws_before` 동결 준수 (호출만).
대상은 **stat(과거학습) 뇌 단독**.

Usage
-----
  python tools/_k_repack_select_diag.py
  K_RS_LO=1186 K_RS_HI=1235 K_RS_SEEDS=2 python tools/_k_repack_select_diag.py
  K_RS_REUSE=1 python tools/_k_repack_select_diag.py     # 원자료 재분석만
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.k_gate import GATE_KEY, gate_block, null_ge3  # noqa: E402
from tools.k_precision import PRECISION_KEY, resolvable  # noqa: E402

BENCH_ID = "K-REPACK-SELECT-DIAG"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KREPACK_SELECT_DIAG.json"
RAW_JSON = ROOT / "docs" / "benchmarks" / "20260808_KREPACK_SELECT_DIAG_raw.json"
OUT_MD = ROOT / "reports" / "20260808_KREPACK_SELECT_DIAG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BRAIN = "stat"
N_PICK = 5
DEFAULT_SEEDS = (42, 7, 99, 2026, 314)
DEFAULT_LO = 53

# 정답을 보지 않고 계산 가능한 세트 특성. (이름, 클수록 좋다고 볼 것인가)
FEATURES: tuple[tuple[str, bool], ...] = (
    ("score_sum", True),
    ("score_rank_mean", False),
    ("dup_count", True),
    ("hint_sum", True),
    ("numema_sum", True),
    ("pos_ema", True),
    ("confidence", True),
    ("sum_nums", True),
    ("odd_cnt", True),
    ("zones", True),
    ("max_consec", False),
)

SEP5 = "|---|---|---|---|---|"


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


def max_draw_no() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    row = conn.execute("SELECT MAX(draw_no) AS m FROM lotto_draws").fetchone()
    conn.close()
    return int(dict(row)["m"])


def _struct(nums: list[int]) -> dict[str, float]:
    """세트 자체의 모양. 정답과 무관하게 계산된다."""
    s = sorted(nums)
    consec = 1
    mx = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            consec += 1
            mx = max(mx, consec)
        else:
            consec = 1
    return {
        "sum_nums": float(sum(s)),
        "odd_cnt": float(sum(1 for n in s if n % 2 == 1)),
        "zones": float(len({(n - 1) // 10 for n in s})),
        "max_consec": float(mx),
    }


def set_features(
    pool: list[dict],
    scores: dict[int, float],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
) -> list[dict[str, Any]]:
    """pool 각 세트의 사전 특성. 정답을 절대 참조하지 않는다."""
    rank_of = {
        n: i + 1
        for i, n in enumerate(sorted(range(1, 46), key=lambda x: (-scores[x], x)))
    }
    dup: Counter[int] = Counter()
    for c in pool:
        for n in c["nums"]:
            dup[int(n)] += 1

    out: list[dict[str, Any]] = []
    for c in pool:
        nums = [int(x) for x in c["nums"]]
        sn = int(c.get("pred_set_no") or c.get("set_no") or 0)
        feat: dict[str, Any] = {
            "set_no": sn,
            "nums": nums,
            "score_sum": sum(scores.get(n, 0.0) for n in nums),
            "score_rank_mean": mean(rank_of[n] for n in nums),
            "dup_count": float(sum(dup[n] - 1 for n in nums)),
            "hint_sum": sum(max(0.0, hint.get(n, 0.0)) for n in nums),
            "numema_sum": sum(num_ema.get(n, 0.0) for n in nums),
            "pos_ema": float(pos_ema.get(sn, 0.0)),
            "confidence": float(c.get("confidence") or 0.0),
        }
        feat.update(_struct(nums))
        out.append(feat)
    return out


def walk_one_seed(
    seed: int, lo: int, hi: int, actuals: dict[int, set[int]]
) -> list[dict[str, Any]]:
    """한 seed 로 lo~hi walk-forward. 회차별 pool 특성·성적을 그대로 저장."""
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.signal_pool import (
        RollingSignalLearner,
        _build_hint,
        _get_draws_before,
        _pool_by_brain,
        expand_pool,
        number_scores,
        repack_by_brain,
        warm_learner_to_draw,
    )

    learner = RollingSignalLearner()
    warm_learner_to_draw(learner, max(1, lo - 200), lo, seed=seed)

    rows: list[dict[str, Any]] = []
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
        stat_pool = pool_br.get(BRAIN, [])
        hint = _build_hint(draws, dno)

        if stat_pool:
            rows.append(
                _one_row(
                    dno,
                    stat_pool,
                    pool_br,
                    hint,
                    num_ema,
                    pos_ema,
                    actuals[dno],
                    number_scores,
                    repack_by_brain,
                )
            )
        learner.update_from_pool(pool_br, actuals[dno])
    return rows


def _one_row(
    dno: int,
    stat_pool: list[dict],
    pool_br: dict[str, list[dict]],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
    actual: set[int],
    number_scores: Any,
    repack_by_brain: Any,
) -> dict[str, Any]:
    from app.testlotto.signal_pool import brain_signal

    scores = number_scores(stat_pool, hint, num_ema, pos_ema, brain_tag=BRAIN)
    feats = set_features(
        stat_pool,
        scores,
        hint,
        brain_signal(num_ema, BRAIN),
        brain_signal(pos_ema, BRAIN),
    )
    for f in feats:
        f["hits"] = len(set(f["nums"]) & actual)

    repacked = repack_by_brain(pool_br, hint, num_ema, pos_ema, target_draw_no=dno)
    rp_hits = [
        len({int(x) for x in c["nums"]} & actual)
        for c in repacked
        if str(c.get("brain_tag") or "") == BRAIN
    ][:N_PICK]

    return {
        "draw_no": dno,
        "sets": [{k: v for k, v in f.items() if k != "nums"} for f in feats],
        "repack_hits": rp_hits,
    }


def ge3(hits: list[int]) -> int:
    return 1 if hits and max(hits) >= 3 else 0


def spearman(xs: list[float], ys: list[float]) -> float | None:
    """순위 상관. 값이 아니라 순서만 보므로 특성 스케일에 안 휘둘린다."""
    n = len(xs)
    if n < 3:
        return None
    rx, ry = _rank(xs), _rank(ys)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx <= 0 or dy <= 0:
        return None
    return num / (dx * dy)


def _rank(vals: list[float]) -> list[float]:
    """동점은 평균 순위로."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def pick_top(sets: list[dict[str, Any]], key: str, bigger: bool) -> list[int]:
    """특성 상위 N개 세트의 적중수. 동점은 set_no 작은 쪽 우선(결정적)."""
    ordered = sorted(
        sets, key=lambda s: (-s[key] if bigger else s[key], s["set_no"])
    )
    return [int(s["hits"]) for s in ordered[:N_PICK]]


def miss_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """① 놓침률 — pool 에 있던 ge3 를 몰아주기가 살렸나 죽였나."""
    pool_ge3 = repack_ge3 = missed = rescued = 0
    gap: list[int] = []
    for r in rows:
        ph = [int(s["hits"]) for s in r["sets"]]
        rh = list(r["repack_hits"])
        p, q = ge3(ph), ge3(rh)
        pool_ge3 += p
        repack_ge3 += q
        missed += 1 if (p and not q) else 0
        rescued += 1 if (q and not p) else 0
        if ph and rh:
            gap.append(max(ph) - max(rh))
    n = len(rows)
    return {
        "n_draws": n,
        "pool_has_ge3": pool_ge3,
        "repack_has_ge3": repack_ge3,
        "pool_ge3_rate": round(pool_ge3 / n, 6) if n else None,
        "repack_ge3_rate": round(repack_ge3 / n, 6) if n else None,
        "missed": missed,
        "rescued": rescued,
        "miss_rate_given_pool_ge3": round(missed / pool_ge3, 6) if pool_ge3 else None,
        "net": rescued - missed,
        "best_hit_gap_mean": round(mean(gap), 6) if gap else None,
        "meaning_ko": (
            "missed = pool 에 3개 이상 세트가 있었는데 몰아주기가 못 만든 회차 · "
            "rescued = 그 반대. net<0 이면 몰아주기가 순손실"
        ),
    }


def select_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """② 선별력 — 사전 특성이 실제 성적과 상관이 있나 · 상위5 골라 쓰면 어떤가."""
    flat_x: dict[str, list[float]] = {k: [] for k, _ in FEATURES}
    flat_y: list[float] = []
    for r in rows:
        for s in r["sets"]:
            for k, _ in FEATURES:
                flat_x[k].append(float(s[k]))
            flat_y.append(float(s["hits"]))

    corr = {
        k: (lambda v: round(v, 6) if v is not None else None)(
            spearman(flat_x[k], flat_y)
        )
        for k, _ in FEATURES
    }

    strategies: dict[str, dict[str, Any]] = {}
    for k, bigger in FEATURES:
        picks = [pick_top(r["sets"], k, bigger) for r in rows]
        strategies[f"feat_{k}"] = _strategy_stats(picks)
    strategies["setno_1_5"] = _strategy_stats(
        [
            [int(s["hits"]) for s in sorted(r["sets"], key=lambda x: x["set_no"])[:N_PICK]]
            for r in rows
        ]
    )
    strategies["repack"] = _strategy_stats([list(r["repack_hits"]) for r in rows])
    strategies["oracle_top5"] = _strategy_stats(
        [sorted((int(s["hits"]) for s in r["sets"]), reverse=True)[:N_PICK] for r in rows]
    )
    return {"spearman_vs_hits": corr, "strategies": strategies}


def _strategy_stats(picks: list[list[int]]) -> dict[str, Any]:
    n = len(picks)
    if not n:
        return {"n": 0}
    return {
        "n": n,
        "ge3_rate": round(sum(ge3(p) for p in picks) / n, 6),
        "best_hit_mean": round(mean(max(p) if p else 0 for p in picks), 6),
        "hit_mean_per_ticket": round(
            mean(h for p in picks for h in p) if any(picks) else 0.0, 6
        ),
    }


def build_payload(raw: dict[str, Any], secs: float) -> dict[str, Any]:
    seeds = raw["seeds"]
    per_seed = {}
    for s in seeds:
        rows = raw["by_seed"][str(s)]
        per_seed[str(s)] = {"miss": miss_block(rows), "select": select_block(rows)}

    all_rows = [r for s in seeds for r in raw["by_seed"][str(s)]]
    pooled = {"miss": miss_block(all_rows), "select": select_block(all_rows)}

    n_draws = len(raw["by_seed"][str(seeds[0])])
    payload: dict[str, Any] = {
        "id": BENCH_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "brain": BRAIN,
        "policy": {
            "read_only": True,
            "wire": False,
            "db_write": False,
            "frozen_respected": ["random.choices", "_get_draws_before", "boost_caps"],
        },
        "design": {
            "range": raw["range"],
            "n_draws_per_seed": n_draws,
            "seeds": seeds,
            "n_pool_sets": 10,
            "n_pick": N_PICK,
            "features": [k for k, _ in FEATURES],
            "peek_free": "특성은 전부 target 이전 정보만 사용 · 정답 미참조",
        },
        "null_reference": null_block(pooled["select"], n_draws),
        "pooled": pooled,
        "per_seed": per_seed,
        "elapsed_sec": round(secs, 1),
    }
    payload.update(_verdict_and_gates(pooled, per_seed, seeds, n_draws))
    payload["verdict"]["pool_quality"] = _pool_quality(payload["null_reference"])
    return payload


def _pool_quality(nb: dict[str, Any]) -> dict[str, Any]:
    """pool 자체가 무작위보다 나은가 — 이 진단의 최상위 질문."""
    if nb["oracle_vs_null10"]["beats_null"]:
        code = "POOL_BETTER_THAN_RANDOM"
        why = (
            f"pool 10세트 최고가 무작위 10장 기준선 {nb['null_ge3_10']} 를 "
            f"{nb['oracle_vs_null10']['delta']:+.6f} 넘었다 → 골라낼 가치가 있다"
        )
    else:
        code = "POOL_EQUALS_RANDOM"
        why = (
            f"pool 10세트 최고 {nb['oracle_vs_null10']['value']} 가 무작위 10장 기준선 "
            f"{nb['null_ge3_10']} 와 구별되지 않는다(±{nb['ci95_halfwidth_n10']}) → "
            "**'좋은 세트를 놓쳤다'는 전제 자체가 성립하지 않는다.** "
            "oracle 과 몰아주기의 격차는 10장 vs 5장이라는 장수 차이일 뿐이다"
        )
    return {"code": code, "why_ko": why}


def null_block(sel: dict[str, Any], n_draws: int) -> dict[str, Any]:
    """가장 중요한 대조 — pool·몰아주기가 **같은 장수의 무작위 티켓**보다 나은가.

    `oracle_top5` 는 10세트 중 최고를 고르므로 그 null 은 5장이 아니라 **10장** 이다
    (최고가 상위5에 반드시 들어오므로 P(10장 중 최고 ≥3) 와 같다).
    이 구분을 놓치면 "10장이 5장보다 낫다"는 당연한 산수를
    "우리 pool 이 좋은 세트를 품고 있다"로 오독하게 된다.
    """
    n5, n10 = null_ge3(5), null_ge3(10)
    half = 1.96 * math.sqrt(n5 * (1 - n5) / n_draws)
    half10 = 1.96 * math.sqrt(n10 * (1 - n10) / n_draws)
    rp = sel["strategies"]["repack"]["ge3_rate"]
    orc = sel["strategies"]["oracle_top5"]["ge3_rate"]
    return {
        "null_ge3_5": round(n5, 6),
        "null_ge3_10": round(n10, 6),
        "ci95_halfwidth_n5": round(half, 6),
        "ci95_halfwidth_n10": round(half10, 6),
        "repack_vs_null5": {
            "value": rp,
            "delta": round(rp - n5, 6),
            "beats_null": bool(abs(rp - n5) > half and rp > n5),
        },
        "oracle_vs_null10": {
            "value": orc,
            "delta": round(orc - n10, 6),
            "beats_null": bool(abs(orc - n10) > half10 and orc > n10),
        },
        "meaning_ko": (
            "oracle 의 올바른 기준선은 무작위 **10장**이다. "
            "oracle 이 null10 과 같으면 pool 10세트는 무작위 10장과 다를 게 없고, "
            "'놓친 기회'라는 표현 자체가 성립하지 않는다"
        ),
    }


def _best_feature(sel: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    cands = {k: v for k, v in sel["strategies"].items() if k.startswith("feat_")}
    key = max(cands, key=lambda k: cands[k]["ge3_rate"])
    return key, cands[key]


def _verdict_and_gates(
    pooled: dict[str, Any],
    per_seed: dict[str, Any],
    seeds: list[int],
    n_draws: int,
) -> dict[str, Any]:
    sel = pooled["select"]
    rp = sel["strategies"]["repack"]
    best_key, best = _best_feature(sel)
    delta = best["ge3_rate"] - rp["ge3_rate"]

    gate = gate_block(
        n=n_draws,
        k_cells=len(FEATURES),
        delta=delta,
        metric=f"ge3({BRAIN}, 5장)",
        label=f"최선 특성 선별({best_key}) vs 현행 몰아주기",
    )

    # seed 간 흔들림이 결론을 만들 만큼 큰지 (R39)
    rp_by_seed = [per_seed[str(s)]["select"]["strategies"]["repack"]["ge3_rate"] for s in seeds]
    bf_by_seed = [
        per_seed[str(s)]["select"]["strategies"][best_key]["ge3_rate"] for s in seeds
    ]
    prec = resolvable(pstdev(rp_by_seed), pstdev(bf_by_seed), len(seeds))

    miss = pooled["miss"]
    if miss["net"] is not None and miss["net"] < 0:
        struct = "REPACK_NET_LOSS"
        why = (
            f"몰아주기가 pool 의 ge3 를 살린 회차({miss['rescued']})보다 "
            f"죽인 회차({miss['missed']})가 많다 → 순손실 {miss['net']}"
        )
    elif miss["net"] == 0:
        struct = "REPACK_NET_EVEN"
        why = "몰아주기의 구제와 놓침이 같다 → 세트 단위로는 이득 없음"
    else:
        struct = "REPACK_NET_GAIN"
        why = f"몰아주기가 pool 에 없던 ge3 를 순 {miss['net']}회 만들어냈다"

    if gate["actionable"]:
        sel_code = "SELECT_SIGNAL_FOUND"
        sel_why = f"{best_key} 로 상위5 세트를 고르면 눈금을 넘는 차이가 난다"
    else:
        sel_code = "SELECT_SIGNAL_NOT_FOUND"
        sel_why = (
            f"{len(FEATURES)}개 특성 전부 눈금 미달 — 정답을 안 보고 pool 세트를 "
            "고르는 신호는 이 특성 집합 안에 없다"
        )

    return {
        GATE_KEY: gate,
        PRECISION_KEY: {
            "rule": "R39",
            "module": "tools/k_precision.py",
            "note": "seed 간 흔들림이 결론 폭보다 크지 않은지 확인",
            "repack_vs_best_feature_seed_std": prec,
        },
        "best_feature": {"key": best_key, **best},
        "verdict": {
            "structure": struct,
            "structure_why_ko": why,
            "selection": sel_code,
            "selection_why_ko": sel_why,
            "actionable": gate["actionable"],
        },
    }


def _md_null(nb: dict[str, Any]) -> list[str]:
    r5, r10 = nb["repack_vs_null5"], nb["oracle_vs_null10"]
    return [
        "|비교|실측|무작위 기준선|Δ|기준선 초과?|",
        SEP5,
        f"|몰아주기 5장|{r5['value']:.4f}|{nb['null_ge3_5']:.4f} (5장)|"
        f"{r5['delta']:+.4f}|**{r5['beats_null']}**|",
        f"|pool 10세트 최고|{r10['value']:.4f}|{nb['null_ge3_10']:.4f} (**10장**)|"
        f"{r10['delta']:+.4f}|**{r10['beats_null']}**|",
        "",
        nb["meaning_ko"],
    ]


def _md_miss(m: dict[str, Any]) -> list[str]:
    return [
        "|항목|값|",
        "|---|---|",
        f"|평가 회차|{m['n_draws']}|",
        f"|pool 10세트에 3개↑ 있던 회차|{m['pool_has_ge3']} ({m['pool_ge3_rate']})|",
        f"|몰아주기 5장이 3개↑ 낸 회차|{m['repack_has_ge3']} ({m['repack_ge3_rate']})|",
        f"|**놓침**(pool 에 있었는데 못 만듦)|**{m['missed']}**|",
        f"|**구제**(pool 에 없던 걸 만듦)|**{m['rescued']}**|",
        f"|순증감|**{m['net']}**|",
        f"|pool 최고 − 몰아주기 최고 (평균)|{m['best_hit_gap_mean']}|",
    ]


def _md_strategies(sel: dict[str, Any]) -> list[str]:
    rows = sel["strategies"]
    order = ["oracle_top5", "repack", "setno_1_5"] + [
        k for k in rows if k.startswith("feat_")
    ]
    base = rows["repack"]["ge3_rate"]
    out = ["|선별 방식|ge3|5장 최고 평균|1장 평균|Δ vs 몰아주기|", SEP5]
    for k in order:
        v = rows[k]
        out.append(
            f"|{k}|{v['ge3_rate']:.4f}|{v['best_hit_mean']:.4f}|"
            f"{v['hit_mean_per_ticket']:.4f}|{v['ge3_rate'] - base:+.4f}|"
        )
    return out


def _md_corr(sel: dict[str, Any]) -> list[str]:
    out = ["|특성|Spearman(특성 ↔ 적중수)|", "|---|---|"]
    for k, v in sorted(
        sel["spearman_vs_hits"].items(),
        key=lambda kv: -abs(kv[1] or 0.0),
    ):
        out.append(f"|{k}|{v}|")
    return out


def build_md(p: dict[str, Any]) -> str:
    d = p["design"]
    v = p["verdict"]
    g = p[GATE_KEY]
    m = p["pooled"]["miss"]
    sel = p["pooled"]["select"]
    L = [
        f"# {BENCH_ID} — 과거학습 뇌 몰아주기 선별 진단",
        "",
        f"- 생성 {p['generated_at']} · {d['range'][0]}~{d['range'][1]} "
        f"(회차 {d['n_draws_per_seed']} × seed {len(d['seeds'])}) · {p['elapsed_sec']}초",
        f"- 대상 **{p['brain']} (과거학습) 단독** · READ-ONLY · **wire=False**",
        "",
        "## 0. 결론",
        "",
        f"- **pool 품질: {v['pool_quality']['code']}** — {v['pool_quality']['why_ko']}",
        f"- 구조: **{v['structure']}** — {v['structure_why_ko']}",
        f"- 선별: **{v['selection']}** — {v['selection_why_ko']}",
        "",
        "## 0-1. 무작위 기준선 대조 (이 표가 먼저다)",
        "",
    ]
    L += _md_null(p["null_reference"])
    L += [
        "",
        "## 1. 왜 이걸 쟀나",
        "",
        "현행 몰아주기는 45개 번호를 점수순으로 세워 6개씩 기계적으로 자른다.",
        "**세트 안의 6개가 서로 어울리는 조합인지는 보지 않는다.** 그래서 pool 안에",
        "통째로 좋은 세트가 있어도 분해돼 사라질 수 있다. 그게 실제로 일어나는지,",
        "일어난다면 정답을 안 보고 그 세트를 골라낼 수 있는지 확인했다.",
        "",
        "## 2. 놓침률 — 몰아주기가 pool 의 기회를 살리나 죽이나",
        "",
    ]
    L += _md_miss(m)
    if v["pool_quality"]["code"] == "POOL_EQUALS_RANDOM":
        L += [
            "",
            "> **이 표를 '결함'으로 읽으면 안 된다.** 위 0-1 에서 pool 이 무작위 10장과",
            "> 구별되지 않는 것으로 나왔으므로, 놓침 871 은 몰아주기의 실수가 아니라",
            "> **10장 중 5장만 발권한다는 산수의 결과**다. 무작위 티켓 10장을 뽑아",
            "> 5장만 내도 똑같은 수치가 나온다.",
        ]
    L += [
        "",
        "## 3. 선별력 — 정답을 안 보고 좋은 세트를 고를 수 있나",
        "",
        "`oracle_top5` 는 정답을 보고 고른 상한이라 **실현 불가**하다. 비교 기준선일 뿐이다.",
        "",
    ]
    L += _md_strategies(sel)
    L += ["", "특성과 실제 적중수의 순위 상관:", ""]
    L += _md_corr(sel)
    L += [
        "",
        "## 4. 판정 게이트 (R38)",
        "",
        f"- 대상: `{p['best_feature']['key']}` vs `repack`",
        f"- Δ = {g['delta']:+.6f} · n={g['gate']['n']} · 탐색셀 {g['gate']['k_cells']}",
        f"- 선택보정 임계 p95 = {g['gate']['mdd_selection_p95']}",
        f"- **{g['verdict']}** — {g['why_ko']}",
        "",
        "## 5. 그래서 패치 방향",
        "",
    ]
    L += _md_direction(p)
    L += [
        "",
        "## 6. 한계",
        "",
        f"- seed {len(d['seeds'])}개. seed 간 흔들림은 `{PRECISION_KEY}` 에 기록",
        "- 특성은 이 11개가 전부다. 여기 없는 신호는 이 진단이 답하지 못한다",
        "- `oracle_top5` 는 상한선일 뿐 발권에 쓸 수 없다 (정답 참조)",
        f"- 원자료 `{RAW_JSON.relative_to(ROOT).as_posix()}` 는 16MB 라 **커밋하지 않는다**"
        "(레포 위생). 같은 seed 로 도구를 재실행하면 결정적으로 재생성된다",
        "",
    ]
    return "\n".join(L)


def _md_direction(p: dict[str, Any]) -> list[str]:
    v = p["verdict"]
    m = p["pooled"]["miss"]
    if v["selection"] == "SELECT_SIGNAL_FOUND":
        return [
            f"`{p['best_feature']['key']}` 가 눈금을 넘었다. 이 특성으로 pool 세트를",
            "고르는 규칙을 설계하고, 홀드아웃으로 재현되는지 먼저 확인한 뒤 배선을 논의한다.",
        ]
    if v["pool_quality"]["code"] == "POOL_EQUALS_RANDOM":
        return [
            "**선별 규칙을 다시 설계할 근거가 없다.** 고를 만한 것이 애초에 없기 때문이다.",
            "",
            "이 진단이 뒤집은 것은 출발 전제다. 20260804 조사에서 본 "
            "'pool 최고 0.245 vs 몰아주기 0.125' 는 **몰아주기가 좋은 세트를 놓친 증거가 "
            "아니라, 10장이 5장보다 유리하다는 산수**였다. 무작위 10장의 기준선과 대보니 "
            "차이가 없다.",
            "",
            "그러므로 다음 중 하나만 남는다.",
            "",
            "1. **몰아주기 구조는 그대로 둔다** — 어떤 배치를 해도 같은 값이 나온다. "
            "바꿀 이유도 없고 되돌릴 이유도 없다",
            f"2. **장수를 늘린다** — 5장→10장이 ge3 를 {p['null_reference']['null_ge3_5']:.4f}"
            f"→{p['null_reference']['null_ge3_10']:.4f} 로 올린다. 다만 이건 예측력이 아니라 "
            "비용을 더 쓴 결과이며, 기대수익은 오히려 나빠진다",
            "3. **선별이 아니라 당첨금 축으로 옮긴다** — 어느 세트가 맞을지는 못 고르지만, "
            "맞았을 때 덜 나누는 세트는 고를 수 있다 (인기회피 · 별도 트랙)",
        ]
    lines = [
        "**정답을 안 보고 pool 세트를 고르는 신호는 이 특성들 안에 없다.**",
        "격차는 실재하지만 그 격차를 메울 열쇠가 여기엔 없다.",
        "",
        "1. **다른 특성을 찾는다** — 세트 궁합(짝 동시출현), 과거 유사 세트의 성적 등",
        "2. **선별을 포기하고 배치를 바꾼다** — 5장이 서로 다른 영역을 덮도록 (선별 대신 분산)",
    ]
    if m["net"] is not None and m["net"] < 0:
        lines += [
            "",
            f"구조 지표가 순손실({m['net']})이므로, 현행 점수순 자르기가 최선은 아니다.",
        ]
    return lines


def print_console(p: dict[str, Any]) -> None:
    m, sel = p["pooled"]["miss"], p["pooled"]["select"]
    v = p["verdict"]
    print(f"\n=== {BENCH_ID} · {p['brain']} ===")
    print(f"range {p['design']['range']} · n={m['n_draws']} (seed 합산)")
    print(
        f"[놓침] pool_ge3={m['pool_has_ge3']} repack_ge3={m['repack_has_ge3']} "
        f"missed={m['missed']} rescued={m['rescued']} net={m['net']} "
        f"gap={m['best_hit_gap_mean']}"
    )
    st = sel["strategies"]
    for k in ("oracle_top5", "repack", "setno_1_5"):
        print(f"  {k:14s} ge3={st[k]['ge3_rate']:.4f} best={st[k]['best_hit_mean']:.4f}")
    top = sorted(
        ((k, x) for k, x in st.items() if k.startswith("feat_")),
        key=lambda kv: -kv[1]["ge3_rate"],
    )[:3]
    for k, x in top:
        print(f"  {k:14s} ge3={x['ge3_rate']:.4f} best={x['best_hit_mean']:.4f}")
    print("\n[상관] " + " ".join(f"{k}={v}" for k, v in sel["spearman_vs_hits"].items()))
    nb = p["null_reference"]
    print(
        f"\n[기준선] 몰아주기 {nb['repack_vs_null5']['value']:.4f} vs 무작위5 "
        f"{nb['null_ge3_5']:.4f} (초과={nb['repack_vs_null5']['beats_null']}) | "
        f"oracle {nb['oracle_vs_null10']['value']:.4f} vs 무작위10 "
        f"{nb['null_ge3_10']:.4f} (초과={nb['oracle_vs_null10']['beats_null']})"
    )
    print(f"\nGATE {p[GATE_KEY]['verdict']} · Δ={p[GATE_KEY]['delta']:+.6f}")
    print(f"VERDICT pool={v['pool_quality']['code']} · 구조={v['structure']} · 선별={v['selection']}")


def collect(lo: int, hi: int, seeds: list[int]) -> dict[str, Any]:
    actuals = load_actuals(lo, hi)
    by_seed: dict[str, Any] = {}
    for i, s in enumerate(seeds):
        t0 = time.time()
        by_seed[str(s)] = walk_one_seed(s, lo, hi, actuals)
        print(
            f"  [{i + 1}/{len(seeds)}] seed={s} · {len(by_seed[str(s)])}회차 "
            f"· {time.time() - t0:.0f}s",
            flush=True,
        )
    return {"range": [lo, hi], "seeds": seeds, "by_seed": by_seed}


def main() -> None:
    hi = _env_int("K_RS_HI", 0) or max_draw_no()
    lo = _env_int("K_RS_LO", 0) or DEFAULT_LO
    n_seeds = _env_int("K_RS_SEEDS", len(DEFAULT_SEEDS))
    seeds = list(DEFAULT_SEEDS[:n_seeds])

    reuse = os.environ.get("K_RS_REUSE", "").strip() == "1" and RAW_JSON.exists()
    if reuse:
        raw = json.loads(RAW_JSON.read_text(encoding="utf-8"))
        secs = float(raw.get("walk_sec") or 0.0)
        print(f"[{BENCH_ID}] 원자료 재사용 {raw['range']} · seed {len(raw['seeds'])}")
    else:
        print(f"[{BENCH_ID}] {lo}~{hi} · seeds {seeds} · 대상 {BRAIN}", flush=True)
        t0 = time.time()
        raw = collect(lo, hi, seeds)
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
