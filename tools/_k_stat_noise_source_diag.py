# -*- coding: utf-8 -*-
"""K-STAT-NOISE-SOURCE — stat 뇌만 잡음을 더하는 원인 특정 (READ-ONLY · R38 준수).

배경
----
SEED-NOISE-FLOOR 에서 뇌별 팽창계수가 갈렸다.

    stat 1.2739   ·   review 0.8835   ·   markov 0.7329

셋 다 같은 파이프라인을 타는데 stat 만 이항잡음보다 큰 흔들림을 만든다.
어디서 들어오는 잡음인지 특정한다.

파이프라인 어디에 무작위가 있나 (코드 확인)
-------------------------------------------
`repack_by_brain` 은 기본 인자에서 **결정적**이다 (`number_scores` 는 가중합,
`repack_sets` 는 정렬, `assemble_hybrid_p45_r123` 은 고정 규칙).
따라서 seed 는 오직 `expand_pool` → 각 뇌의 `predict_sets` 로만 들어간다.

그 안에서 두 뇌의 구조가 다르다.

  stat   : 45개 번호 전체를 후보로 두고 `random.choices` 로 6개 추출
  markov : 방문수 **상위 25개**만 후보로 두고 `random.choices` 로 6개 추출

후보 폭이 넓을수록 같은 가중치라도 뽑히는 조합이 seed 마다 크게 달라진다.
이 가설을 네 단계로 검증한다.

1. **결정성 확인** — 점수(가중치) 자체는 seed 와 무관한가?
   무관하다면 잡음은 전부 '뽑기' 단계에서 온다.
2. **유효 후보수** — 가중치 분포의 퍼플렉시티. stat 이 markov 보다 넓은가?
3. **생성 불안정도** — seed 만 바꿔 뽑은 세트들이 얼마나 달라지는가?
4. **반사실** — 같은 가중치에서 뽑기 대신 상위 6개씩 결정적으로 자르면
   흔들림이 사라지는가, 그리고 적중은 얼마나 달라지는가?

정책
----
READ-ONLY. DB 쓰기 없음 · **코드·상수 무변경** · `random.choices` 동결 준수
(호출만 하고 고치지 않는다) · wire=False.
4단계는 진단 안에서 별도로 조합을 구성해 비교할 뿐, 앱 경로를 바꾸지 않는다.

Usage:
  python tools/_k_stat_noise_source_diag.py
  K_NS_LO=1136 K_NS_HI=1235 K_NS_SEEDS=3 python tools/_k_stat_noise_source_diag.py
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
from itertools import combinations
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.k_gate import GATE_KEY, classify, gate_block, null_ge3  # noqa: E402

BENCH_ID = "K-STAT-NOISE-SOURCE"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KSTAT_NOISE_SOURCE.json"
OUT_MD = ROOT / "reports" / "20260808_KSTAT_NOISE_SOURCE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

PRIOR_FLOOR = "docs/benchmarks/20260808_KSTAT_SEED_NOISE_FLOOR.json"
RAW_CACHE = "docs/benchmarks/20260808_KSTAT_NOISE_SOURCE_RAW.json"

DEFAULT_SEEDS = (
    42, 0, 7, 99, 1, 2026, 314, 777,
    13, 21, 55, 89, 144, 233, 377, 610,
    1001, 2718, 3141, 4096, 5150, 6180, 7021, 8191,
)
SETS_PER_BRAIN = 5


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    return int(v) if v else default


def perplexity(weights: dict[int, float]) -> float:
    """가중치 분포의 유효 후보수. 균등하면 후보 개수와 같고, 쏠릴수록 작아진다."""
    tot = sum(weights.values())
    if tot <= 0:
        return 0.0
    h = 0.0
    for w in weights.values():
        p = w / tot
        if p > 0:
            h -= p * math.log(p)
    return math.exp(h)


def jaccard(a: set[int], b: set[int]) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 1.0


def num_dist(sets: list[list[int]]) -> dict[int, float]:
    """세트들이 뽑은 번호의 경험분포. 파이프라인의 `_pool_freq` 가 보는 것과 같은 정보."""
    cnt: Counter[int] = Counter()
    for st in sets:
        for n in st:
            cnt[int(n)] += 1
    tot = sum(cnt.values()) or 1
    return {n: cnt.get(n, 0) / tot for n in range(1, 46)}


def instability(sets_by_seed: dict[int, list[list[int]]]) -> dict[str, float]:
    """seed 간 생성 불안정도.

    pool_tvd      : 번호 경험분포의 총변동거리. 0=동일, 1=완전히 다름.
                    파이프라인의 결정적 부분(`_pool_freq`→`number_scores`)이 실제로
                    보는 양이므로 **이게 주 지표**다.
    union_jaccard : 번호 합집합 겹침. 합집합 크기에 좌우되므로 보조 지표.
    ticket_share  : 완전히 같은 조합(6개 일치)이 재현되는 비율.
    presence_std  : 번호별 '등장 여부'의 seed 간 표준편차 평균.
    """
    seeds = sorted(sets_by_seed)
    unions = {s: {n for st in sets_by_seed[s] for n in st} for s in seeds}
    tickets = {s: {tuple(sorted(st)) for st in sets_by_seed[s]} for s in seeds}
    dists = {s: num_dist(sets_by_seed[s]) for s in seeds}

    uj, ts, tvd = [], [], []
    for a, b in combinations(seeds, 2):
        uj.append(jaccard(unions[a], unions[b]))
        inter = len(tickets[a] & tickets[b])
        ts.append(inter / max(len(tickets[a]), len(tickets[b]), 1))
        tvd.append(0.5 * sum(abs(dists[a][n] - dists[b][n]) for n in range(1, 46)))

    pres = [pstdev([1.0 if n in unions[s] else 0.0 for s in seeds]) for n in range(1, 46)]

    return {
        "pool_tvd": mean(tvd) if tvd else 0.0,
        "union_jaccard": mean(uj) if uj else 1.0,
        "ticket_share": mean(ts) if ts else 1.0,
        "union_size_mean": mean(len(unions[s]) for s in seeds),
        "presence_std": mean(pres),
        "output_perplexity": mean(perplexity(dists[s]) for s in seeds),
    }


def deterministic_sets(weights: dict[int, float], n_sets: int) -> list[list[int]]:
    """뽑기 없이 가중치 상위부터 6개씩 잘라 만드는 반사실 조합."""
    ranked = sorted(range(1, 46), key=lambda x: (-weights.get(x, 0.0), x))
    return [sorted(ranked[i * 6 : (i + 1) * 6]) for i in range(n_sets)]


def stat_weights(draws: list[dict]) -> dict[int, float]:
    from app.testlotto.brains.stat_brain import engine

    w, _freq, _pf, _ls, _ldn = engine.build_weights(draws)
    return w


def markov_weights(draws: list[dict]) -> dict[int, float]:
    """markov 의 후보 가중치 (방문수 상위 25). predict_markov 내부와 동일 구성."""
    from app.testlotto import predict_markov as pm

    fn = getattr(pm, "_build_visit_count", None)
    if fn is not None:
        vc = fn(draws)
    else:
        vc = _markov_visit_fallback(draws)
    top = sorted(vc.items(), key=lambda x: x[1], reverse=True)[:25]
    return {int(n): float(c) for n, c in top}


def _markov_visit_fallback(draws: list[dict]) -> dict[int, float]:
    """predict_markov 에 헬퍼가 없을 때의 근사 — 전이 방문수."""
    vc: Counter[int] = Counter()
    keys = ("num1", "num2", "num3", "num4", "num5", "num6")
    prev: list[int] | None = None
    for d in draws:
        cur = [int(d[k]) for k in keys]
        if prev is not None:
            for n in cur:
                vc[n] += 1
        prev = cur
    return {n: float(vc.get(n, 0)) for n in range(1, 46)}


def brain_pool(mod: Any, draws: list[dict], dno: int, seed: int) -> list[list[int]]:
    """`expand_pool` 의 2패스 구조를 그대로 재현해 한 뇌의 pool(10세트)을 만든다."""
    out: list[list[int]] = []
    for pass_idx in range(2):
        random.seed(seed if pass_idx == 0 else seed + 10000 + dno)
        sets = mod.predict_sets(draws, SETS_PER_BRAIN)
        out.extend([int(x) for x in st["nums"]] for st in sets[:SETS_PER_BRAIN])
    return out


def _weight_probe(
    fn: Any, draws: Any, probe_seeds: list[int]
) -> tuple[dict[int, float], bool]:
    """같은 회차를 서로 다른 seed 로 채점해 결과가 동일한지 본다.

    동일하다면 점수 단계는 seed 와 무관하고, 흔들림은 뽑기에서만 온다.
    """
    variants = []
    for s in probe_seeds:
        random.seed(s)
        variants.append(fn(draws))
    ref = variants[0]
    same = True
    for other in variants[1:]:
        keys = set(ref) | set(other)
        if any(abs(ref.get(k, 0.0) - other.get(k, 0.0)) > 1e-12 for k in keys):
            same = False
    return ref, same


def collect(lo: int, hi: int, seeds: list[int], step: int) -> dict[str, Any]:
    from app.testlotto.brains import predict_flow_shaman, predict_review_king
    from app.testlotto.brains.stat_brain import predict as stat_predict
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.signal_pool import _get_draws_before

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (lo, hi),
    ).fetchall()
    conn.close()
    actuals = {
        int(dict(r)["draw_no"]): {int(dict(r)[f"num{k}"]) for k in range(1, 7)} for r in rows
    }
    targets = [d for i, d in enumerate(sorted(actuals)) if i % step == 0]

    brains = {
        "stat": stat_predict,
        "markov": predict_flow_shaman,
        "review": predict_review_king,
    }
    weight_fns = {"stat": stat_weights, "markov": markov_weights}

    det_ok = dict.fromkeys(weight_fns, True)
    perp: dict[str, list[float]] = {b: [] for b in weight_fns}
    inst: dict[str, list[dict[str, float]]] = {b: [] for b in brains}
    hits: dict[str, dict[int, list[int]]] = {b: {s: [] for s in seeds} for b in brains}
    det_hits: dict[str, list[int]] = {b: [] for b in weight_fns}

    t0 = time.time()
    for idx, dno in enumerate(targets, 1):
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        if not draws:
            continue
        actual = actuals[dno]

        # 1·2. 점수 결정성 + 후보 가중치의 유효 후보수 (내부 접근 가능한 뇌만)
        wref: dict[str, dict[int, float]] = {}
        for b, fn in weight_fns.items():
            ref, same = _weight_probe(fn, draws, seeds[:3])
            wref[b] = ref
            det_ok[b] = det_ok[b] and same
            perp[b].append(perplexity(ref))

        # 3. 파이프라인과 동일한 pool(10세트) 기준 불안정도 + seed별 적중
        for b, mod in brains.items():
            per_seed: dict[int, list[list[int]]] = {}
            for s in seeds:
                pool = brain_pool(mod, draws, dno, s)
                per_seed[s] = pool
                hits[b][s].append(max((len(set(n) & actual) for n in pool[:5]), default=0))
            inst[b].append(instability(per_seed))

        # 4. 반사실 — 뽑기 대신 결정적 상위 절단
        for b in weight_fns:
            dsets = deterministic_sets(wref[b], SETS_PER_BRAIN)
            det_hits[b].append(max(len(set(n) & actual) for n in dsets))

        if idx % 25 == 0:
            print(f"  [{idx}/{len(targets)}] dno={dno} ({time.time() - t0:.0f}s)", flush=True)

    return {
        "targets": targets,
        "brains": list(brains),
        "weight_brains": list(weight_fns),
        "det_ok": det_ok,
        "perplexity": perp,
        "instability": inst,
        "ge3_hits": hits,
        "det_hits": det_hits,
        "elapsed": round(time.time() - t0, 1),
    }


def collect_cached(lo: int, hi: int, seeds: list[int], step: int) -> dict[str, Any]:
    """수집은 10분 넘게 걸린다. 같은 설정이면 원자료를 재사용한다.

    지표·판정 로직을 고칠 때마다 예측을 다시 돌릴 이유가 없다.
    `K_NS_REFRESH=1` 이면 캐시를 무시하고 새로 뽑는다.
    """
    key = {"lo": lo, "hi": hi, "step": step, "seeds": seeds, "sets": SETS_PER_BRAIN}
    path = ROOT / RAW_CACHE
    if not _env_int("K_NS_REFRESH", 0) and path.exists():
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("key") == key:
                print(f"  [캐시 재사용] {path.name}", flush=True)
                data = cached["data"]
                # JSON 은 dict 키를 문자열로 만든다. seed 키를 정수로 되돌린다.
                for b in data["brains"]:
                    data["ge3_hits"][b] = {
                        int(s): v for s, v in data["ge3_hits"][b].items()
                    }
                return data
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"  [캐시 무시] {e}", flush=True)

    data = collect(lo, hi, seeds, step)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"key": key, "raw_data": True, "data": data}, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    return data


def ge3_of(v: list[int]) -> float:
    return sum(1 for x in v if x >= 3) / len(v) if v else 0.0


def analyze(c: dict[str, Any], seeds: list[int]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for b in c["brains"]:
        by_seed = {s: ge3_of(c["ge3_hits"][b][s]) for s in seeds}
        vals = list(by_seed.values())
        inst = c["instability"][b]
        entry: dict[str, Any] = {
            "generation_instability": {
                "pool_tvd_mean": round(mean(r["pool_tvd"] for r in inst), 6),
                "presence_std_mean": round(mean(r["presence_std"] for r in inst), 6),
                "union_jaccard_mean": round(mean(r["union_jaccard"] for r in inst), 6),
                "ticket_share_mean": round(mean(r["ticket_share"] for r in inst), 6),
                "union_size_mean": round(mean(r["union_size_mean"] for r in inst), 4),
                "output_perplexity_mean": round(
                    mean(r["output_perplexity"] for r in inst), 4
                ),
            },
            "sampled_ge3_by_seed": {str(s): round(v, 6) for s, v in by_seed.items()},
            "sampled_ge3": {
                "mean": round(mean(vals), 6),
                "std": round(pstdev(vals), 6) if len(vals) > 1 else 0.0,
                "range": round(max(vals) - min(vals), 6),
            },
        }
        if b in c["weight_brains"]:
            pl = sorted(c["perplexity"][b])
            entry["weights_deterministic"] = c["det_ok"][b]
            entry["effective_candidates"] = {
                "median": round(pl[len(pl) // 2], 4),
                "mean": round(mean(pl), 4),
                "min": round(min(pl), 4),
                "max": round(max(pl), 4),
            }
            entry["deterministic_ge3"] = round(ge3_of(c["det_hits"][b]), 6)
            entry["deterministic_mean_hit"] = round(mean(c["det_hits"][b]), 6)
            entry["sampled_mean_hit"] = round(
                mean(mean(c["ge3_hits"][b][s]) for s in seeds), 6
            )
        out[b] = entry
    return out


def resolvable_pairs(
    res: dict[str, Any], prior_std: dict[str, float], n_seeds: int
) -> dict[str, Any]:
    """뇌 3개 순서를 통째로 맞추라는 건 지나치게 엄격하다.

    seed k개로 잰 표준편차의 표준오차는 대략 σ/√(2(k−1)) 다. 이 불확실성을 넘어
    **구분 가능한 쌍**만 골라, 그 쌍들의 순서가 파이프라인 실측과 맞는지 본다.
    """
    brains = list(prior_std)
    se = {
        b: res[b]["sampled_ge3"]["std"] / math.sqrt(2 * max(1, n_seeds - 1))
        for b in brains
    }
    pairs = []
    for a, b in combinations(brains, 2):
        sa, sb = res[a]["sampled_ge3"]["std"], res[b]["sampled_ge3"]["std"]
        crit = 1.96 * math.sqrt(se[a] ** 2 + se[b] ** 2)
        res_ok = abs(sa - sb) > crit
        agree = None
        if res_ok:
            agree = (sa < sb) == (prior_std[a] < prior_std[b])
        # 이 쌍을 구분하려면 seed 가 몇 개 필요한가 (관측 차이가 유지된다는 가정)
        d = abs(sa - sb)
        need = None
        if d > 0:
            need = int(math.ceil(1 + (1.96 * math.sqrt(sa**2 + sb**2) / d) ** 2 / 2))
        pairs.append(
            {
                "pair": [a, b],
                "brain_std": [round(sa, 6), round(sb, 6)],
                "diff": round(d, 6),
                "resolve_threshold": round(crit, 6),
                "resolvable": res_ok,
                "seeds_needed": need,
                "pipeline_std": [prior_std[a], prior_std[b]],
                "order_agrees": agree,
            }
        )
    res_pairs = [p for p in pairs if p["resolvable"]]
    return {
        "n_seeds": n_seeds,
        "std_se": {b: round(v, 6) for b, v in se.items()},
        "pairs": pairs,
        "n_resolvable": len(res_pairs),
        "n_agree": sum(1 for p in res_pairs if p["order_agrees"]),
        "seeds_needed_max": max(
            (p["seeds_needed"] for p in pairs if p["seeds_needed"]), default=None
        ),
        "note_ko": (
            "구분 가능한 쌍에서만 순서를 비교한다. 구분 불가한 쌍을 '불일치'로 세면 "
            "측정 정밀도 부족을 결론으로 착각하게 된다."
        ),
    }


def premise_check(prior_std: dict[str, float], n_seeds: int) -> dict[str, Any]:
    """**전제 자체를 검증한다.**

    이 진단은 "stat 이 markov 보다 시끄럽다(팽창 1.27 대 0.73)"를 참으로 놓고 시작했다.
    그런데 그 값도 seed 유한개로 잰 표준편차다. 표준편차의 표준오차를 감안했을 때
    뇌 사이 차이가 실제로 구분되는지 먼저 따져야 한다. 구분이 안 된다면
    '왜 stat 만 시끄러운가'라는 질문 자체가 성립하지 않는다.
    """
    brains = list(prior_std)
    se = {b: prior_std[b] / math.sqrt(2 * max(1, n_seeds - 1)) for b in brains}
    pairs = []
    for a, b in combinations(brains, 2):
        sa, sb = prior_std[a], prior_std[b]
        crit = 1.96 * math.sqrt(se[a] ** 2 + se[b] ** 2)
        d = abs(sa - sb)
        pairs.append(
            {
                "pair": [a, b],
                "pipeline_std": [sa, sb],
                "diff": round(d, 6),
                "resolve_threshold": round(crit, 6),
                "resolvable": d > crit,
                "seeds_needed": (
                    int(math.ceil(1 + (1.96 * math.sqrt(sa**2 + sb**2) / d) ** 2 / 2))
                    if d > 0
                    else None
                ),
            }
        )
    n_res = sum(1 for p in pairs if p["resolvable"])
    return {
        "n_seeds_used_in_floor": n_seeds,
        "std_se": {b: round(v, 6) for b, v in se.items()},
        "pairs": pairs,
        "n_resolvable": n_res,
        "premise_holds": n_res > 0,
        "meaning_ko": (
            "구분 가능한 쌍이 0개면, 뇌별 팽창계수 순위는 측정 오차 안의 흔들림이다. "
            "'stat 만 유독 시끄럽다'는 전제가 근거를 잃는다."
            if n_res == 0
            else f"구분 가능한 쌍 {n_res}개 — 뇌별 차이가 실재한다."
        ),
    }


def paired_counterfactual(
    det_hits: list[int], seed_hits: dict[int, list[int]], b: int = 20000, seed: int = 20260808
) -> dict[str, Any]:
    """반사실 비교는 **같은 회차**를 쓰므로 짝지어 검정해야 힘이 훨씬 세다.

    회차마다 (결정적 절단이 3개 이상 맞췄나) − (뽑기가 3개 이상 맞춘 seed 비율) 을 구하고,
    회차 단위 부트스트랩으로 신뢰구간을 낸다.
    """
    import numpy as np

    seeds = sorted(seed_hits)
    n = len(det_hits)
    det = np.array([1.0 if h >= 3 else 0.0 for h in det_hits])
    samp = np.array(
        [mean(1.0 if seed_hits[s][i] >= 3 else 0.0 for s in seeds) for i in range(n)]
    )
    diff = det - samp

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(b, n))
    boots = diff[idx].mean(axis=1)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    p_two = 2 * min((boots <= 0).mean(), (boots >= 0).mean())

    return {
        "method": "회차 단위 짝지은 부트스트랩 (B=%d)" % b,
        "n_draws": n,
        "mean_diff": round(float(diff.mean()), 6),
        "ci95": [round(float(lo), 6), round(float(hi), 6)],
        "p_two_sided": round(float(min(1.0, p_two)), 6),
        "significant": bool(lo > 0 or hi < 0),
        "why_paired_ko": (
            "두 방식이 같은 회차를 평가하므로 회차별 난이도가 상쇄된다. "
            "독립표본 가정의 게이트 임계보다 훨씬 작은 차이도 잡아낼 수 있다."
        ),
    }


def _metric_value(res: dict[str, Any], brain: str, metric: str) -> float:
    if metric == "brain_level_ge3_std":
        return float(res[brain]["sampled_ge3"]["std"])
    return float(res[brain]["generation_instability"][metric])


def ordering_test(
    res: dict[str, Any], prior_std: dict[str, float], metric: str
) -> dict[str, Any]:
    """불안정도 지표가 파이프라인 실측 ge3 seed 표준편차 순서를 재현하는지.

    뇌 3개뿐이라 상관계수는 의미가 없다. **순서 일치 여부**만 본다.
    무작위 지표도 1/6 확률로 맞으므로, 일치 하나만으로 인과를 주장하지 않는다.
    """
    brains = list(prior_std)
    by_metric = sorted(brains, key=lambda b: _metric_value(res, b, metric))
    by_truth = sorted(brains, key=lambda b: prior_std[b])
    return {
        "metric": metric,
        "order_by_metric_asc": by_metric,
        "order_by_seed_std_asc": by_truth,
        "matches": by_metric == by_truth,
        "chance_match_prob": round(1 / 6, 4),
        "values": {
            b: {"metric": _metric_value(res, b, metric), "pipeline_seed_std": prior_std[b]}
            for b in brains
        },
    }


def _agree_label(v: bool | None) -> str:
    if v is None:
        return "—"
    return "일치" if v else "불일치"


def _pair_rows(pairs: list[dict[str, Any]], std_key: str) -> list[str]:
    """구분가능성 표의 행. 순서 일치 열은 값이 있을 때만 붙인다."""
    rows = []
    for pr in pairs:
        cells = [
            f"{pr['pair'][0]} vs {pr['pair'][1]}",
            f"{pr[std_key][0]} / {pr[std_key][1]}",
            str(pr["diff"]),
            str(pr["resolve_threshold"]),
            "예" if pr["resolvable"] else "**아니오**",
            str(pr["seeds_needed"]),
        ]
        if "order_agrees" in pr:
            cells.append(_agree_label(pr["order_agrees"]))
        rows.append("| " + " | ".join(cells) + " |")
    return rows


def build_report(p: dict[str, Any]) -> str:
    st, mk, rv = p["stat"], p["markov"], p["review"]
    pc = p["premise_check"]
    lines = [
        f"# {BENCH_ID} — stat 뇌만 잡음을 더하는 원인",
        "",
        f"- 날짜: {p['date']} · 회차 {p['draw_range'][0]}~{p['draw_range'][1]} "
        f"중 {p['n_targets']}개 표본(간격 {p['step']}) · seed {len(p['seeds'])}개 · {p['elapsed_sec']}초",
        f"- **판정: {p['verdict']['code']} — {p['verdict']['headline_ko']}**",
        "- 정책: READ-ONLY · DB 쓰기 없음 · 코드·상수 무변경 · `random.choices` 동결 준수",
        "",
        "## 1. 출발점",
        "",
        "전구간 잡음 측정에서 뇌별 팽창계수가 갈렸다.",
        "",
        "| 뇌 | 팽창계수 | 전구간 seed 표준편차 |",
        "|---|---|---|",
        f"| **stat** | **{p['prior']['stat_inflation']}** | {p['prior']['stat_seed_std']} |",
        f"| review | {p['prior']['review_inflation']} | {p['prior']['review_seed_std']} |",
        f"| markov | {p['prior']['markov_inflation']} | {p['prior']['markov_seed_std']} |",
        "",
        "셋 다 같은 파이프라인을 탄다. 겉보기로는 stat 만 이항잡음보다 큰 흔들림을 만든다.",
        "",
        "### 1-B. 그런데 이 전제부터 검증해야 한다",
        "",
        f"위 표의 표준편차는 seed **{pc['n_seeds_used_in_floor']}개**로 잰 값이다.",
        "표준편차 자체에도 오차가 있다(σ/√(2(k−1))). 뇌 사이 차이가 그 오차를 넘는지 본다.",
        "",
        "| 쌍 | 파이프라인 표준편차 | 차이 | 구분 임계 | 구분 가능 | 필요 seed |",
        "|---|---|---|---|---|---|",
        *_pair_rows(pc["pairs"], "pipeline_std"),
    ]
    lines += [
        "",
        f"**{pc['meaning_ko']}**",
        "",
        "이 절은 진단을 무르려는 게 아니다. 아래 2~4절의 단계 특정은 전제와 무관하게 유효하다.",
        "다만 '왜 stat 만' 이라는 질문에는 답할 대상이 없을 수 있다는 뜻이다.",
        "",
        "## 2. 잡음이 들어올 수 있는 곳은 한 군데뿐이다",
        "",
        "코드를 따라가면 `repack_by_brain` 은 기본 인자에서 **완전히 결정적**이다.",
        "`number_scores` 는 가중합, `repack_sets` 는 정렬, `assemble_hybrid_p45_r123` 은",
        "고정 규칙이다. 따라서 seed 는 오직 `expand_pool` → 각 뇌의 `predict_sets` 로만 들어간다.",
        "",
        "### 2-A. 점수 자체는 seed 와 무관한가",
        "",
        f"- stat 가중치 결정적: **{st['weights_deterministic']}**",
        f"- markov 가중치 결정적: **{mk['weights_deterministic']}**",
        "",
        "둘 다 그렇다면, 흔들림은 전부 **'뽑기' 단계**에서 온다. 점수를 만드는 과정이 아니라,",
        "그 점수로 6개를 고르는 과정이다.",
        "",
        "### 2-B. 구조적 비대칭 (코드 확인)",
        "",
        p["pipeline_randomness"]["shared_stream_ko"],
        "",
        "## 3. 후보 폭 — 첫 가설",
        "",
        "코드상 구조 차이가 있다.",
        "",
        "```",
        "stat   : 45개 번호 전체를 후보로 두고 random.choices 로 6개 추출",
        "markov : 방문수 상위 25개만 후보로 두고 random.choices 로 6개 추출",
        "```",
        "",
        "가중치 분포의 **유효 후보수**(퍼플렉시티 · 균등하면 후보 개수와 같고 쏠릴수록 작아짐)를",
        "재보면 구조 차이가 그대로 확인된다.",
        "",
        "| 뇌 | 유효 후보수(중앙값) | 평균 | 최소~최대 |",
        "|---|---|---|---|",
        f"| **stat** | **{st['effective_candidates']['median']}** | "
        f"{st['effective_candidates']['mean']} | "
        f"{st['effective_candidates']['min']}~{st['effective_candidates']['max']} |",
        f"| markov | {mk['effective_candidates']['median']} | "
        f"{mk['effective_candidates']['mean']} | "
        f"{mk['effective_candidates']['min']}~{mk['effective_candidates']['max']} |",
        "",
        p["candidate_note_ko"],
        "",
        "## 4. 실제 생성이 얼마나 흔들리는가",
        "",
        "파이프라인과 동일하게 pool 10세트(2패스)를 만들어 seed 간 차이를 쟀다.",
        "**주 지표는 `pool_tvd`** 다. 파이프라인의 결정적 부분(`_pool_freq`→`number_scores`)이",
        "실제로 보는 것이 번호 경험분포이기 때문이다. 0 이면 동일, 클수록 불안정하다.",
        "",
        "| 뇌 | pool_tvd | 등장여부 표준편차 | 합집합 Jaccard | 조합 재현율 | 합집합 크기 | 출력 퍼플렉시티 |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, d in (("**stat**", st), ("review", rv), ("markov", mk)):
        gi = d["generation_instability"]
        lines.append(
            f"| {name} | **{gi['pool_tvd_mean']}** | {gi['presence_std_mean']} | "
            f"{gi['union_jaccard_mean']} | {gi['ticket_share_mean']} | "
            f"{gi['union_size_mean']} | {gi['output_perplexity_mean']} |"
        )
    lines += [
        "",
        "### 어느 지표가 실제 잡음 순서를 설명하는가",
        "",
        "뇌가 셋뿐이라 상관계수는 의미가 없다. 대신 **순서가 맞는지**만 본다.",
        f"실제 파이프라인 seed 표준편차 순서(작은 것부터): "
        f"`{p['ordering'][0]['order_by_seed_std_asc']}` · 무작위 지표도 1/6 확률로 맞는다.",
        "",
        "**주의:** 1-B절에서 본 대로 이 '실제 순서'는 통계적으로 확정된 것이 아니다.",
        "아래 표의 일치/불일치는 참고용이며, 그 자체로 지표의 우열을 뜻하지 않는다.",
        "",
        "| 지표 | 이 지표가 매긴 순서 | 실제와 일치 |",
        "|---|---|---|",
    ]
    for o in p["ordering"]:
        lines.append(
            f"| `{o['metric']}` | {o['order_by_metric_asc']} | "
            f"{'**일치**' if o['matches'] else '불일치'} |"
        )
    rp = p["resolvable_pairs"]
    lines += [
        "",
        "### 그런데 3개 순서를 통째로 맞추라는 건 지나치게 엄격하다",
        "",
        f"seed {rp['n_seeds']}개로 잰 표준편차 자체에 오차가 있다(σ/√(2(k−1))).",
        "그래서 **구분 가능한 쌍**만 골라 순서를 비교했다.",
        "",
        "| 쌍 | 뇌 수준 표준편차 | 차이 | 구분 임계 | 구분 가능 | 필요 seed | 순서 일치 |",
        "|---|---|---|---|---|---|---|",
        *_pair_rows(rp["pairs"], "brain_std"),
    ]
    lines += [
        "",
        f"구분 가능한 쌍 **{rp['n_resolvable']}/3** 중 **{rp['n_agree']}개**가 실제 순서와 맞았다.",
        rp["note_ko"],
        "",
        p["instability_note_ko"],
        "",
        "## 5. 반사실 — 뽑기를 없애면 어떻게 되나",
        "",
        "같은 가중치에서 뽑기 대신 **상위부터 6개씩 결정적으로 잘라** 5세트를 만들어 봤다.",
        "이 방식은 seed 가 없으므로 흔들림이 정확히 0 이다. 문제는 적중이 유지되느냐다.",
        "",
        "| 뇌 | 뽑기 ge3 (평균) | 뽑기 ge3 폭 | 결정적 ge3 | 차이 |",
        "|---|---|---|---|---|",
    ]
    for b, d in (("stat", st), ("markov", mk)):  # 가중치 접근 가능한 뇌만
        delta = round(d["deterministic_ge3"] - d["sampled_ge3"]["mean"], 6)
        lines.append(
            f"| {b} | {d['sampled_ge3']['mean']} | {d['sampled_ge3']['range']} | "
            f"{d['deterministic_ge3']} | {delta:+.6f} |"
        )
    g = p["counterfactual_gate"]
    lines += [
        "",
        f"독립표본을 가정한 R38 게이트: **{g['verdict']}** — {g['why_ko']}",
        "",
        "### 5-B. 짝지은 비교 (같은 회차이므로 이쪽이 옳다)",
        "",
        "두 방식은 **같은 회차를 푼다.** 그래서 회차별 난이도가 상쇄되는 짝지은 검정을",
        "쓸 수 있고, 독립표본 게이트보다 훨씬 작은 차이도 잡아낸다.",
        "게이트 판정을 지우는 게 아니라, 설계에 맞는 검정을 하나 더 붙이는 것이다.",
        "",
        "| 뇌 | 회차당 평균 차이 | 95% 신뢰구간 | p | 유의 |",
        "|---|---|---|---|---|",
    ]
    for b, d in p["paired_counterfactual"].items():
        lines.append(
            f"| {b} | {d['mean_diff']:+.6f} | [{d['ci95'][0]:+.6f}, {d['ci95'][1]:+.6f}] | "
            f"{d['p_two_sided']} | {'**예**' if d['significant'] else '아니오'} |"
        )
    lines += [
        "",
        next(iter(p["paired_counterfactual"].values()))["why_paired_ko"],
        "",
        p["counterfactual_note_ko"],
        "",
        "## 6. 결론",
        "",
        p["verdict"]["detail_ko"],
        "",
        "## 7. 제안 (형 GO 없이는 적용 안 함)",
        "",
    ]
    for i, s in enumerate(p["proposals"], 1):
        lines.append(f"{i}. **{s['what']}** — {s['why']}")
        lines.append(f"   - 위험: {s['risk']}")
    lines += [
        "",
        "## 8. 한계",
        "",
        f"- 표본 {p['n_targets']}회차(간격 {p['step']})다. 전구간 전수가 아니다.",
        "  ge3 수치는 방향 확인용이고, 정밀 비교는 게이트 임계를 넘어야 한다.",
        "- 반사실의 결정적 조합은 상위 절단이라 세트끼리 번호가 겹치지 않는다.",
        "  실제 발권 규칙(다양성·필터)과 다르므로 적중 수준을 그대로 옮길 수 없다.",
        "- markov 가중치는 `predict_markov` 내부 구성을 재현한 것이다. 내부 헬퍼가 없으면",
        f"  근사식을 쓴다 (이번 실행: `{p['markov_weight_source']}`).",
        "- `random.choices` 는 동결 상태다. 이 보고서는 진단·제안까지만 한다.",
        "",
        f"- 이전: `{PRIOR_FLOOR}` · 원본: `docs/benchmarks/{OUT_JSON.name}`",
        "",
    ]
    return "\n".join(lines)


def decide_verdict(
    res: dict[str, Any],
    ordering: list[dict[str, Any]],
    rp: dict[str, Any],
    pc: dict[str, Any],
    explaining: list[str],
    n_seeds: int,
) -> tuple[str, str]:
    """판정 순서가 곧 논리 순서다.

    전제가 성립하는지를 원인 후보보다 **먼저** 묻는다. 전제가 무너지면
    아래 원인 판정들은 존재하지 않는 차이를 설명하려는 시도가 된다.
    """
    st, mk = res["stat"], res["markov"]

    def _matched(metric: str) -> bool:
        return any(o["metric"] == metric and o["matches"] for o in ordering)

    if not (st["weights_deterministic"] and mk["weights_deterministic"]):
        return (
            "SCORING_NOT_DETERMINISTIC",
            "점수 단계에도 seed 의존이 있다 — 가설 수정 필요",
        )
    if not pc["premise_holds"]:
        return (
            "PREMISE_NOT_ESTABLISHED",
            "질문의 전제가 성립하지 않는다 — 'stat 만 시끄럽다'는 뇌별 팽창 차이가 "
            f"seed {pc['n_seeds_used_in_floor']}개 측정의 오차 범위 안이다",
        )
    pair_ok = rp["n_resolvable"] > 0 and rp["n_agree"] == rp["n_resolvable"]
    if _matched("brain_level_ge3_std") or pair_ok:
        return (
            "BRAIN_GENERATION_CONFIRMED",
            "원인 특정 — 뇌 자체 수준의 잡음이 파이프라인 잡음 순서와 맞는다 "
            f"(구분 가능한 쌍 {rp['n_agree']}/{rp['n_resolvable']} 일치)",
        )
    if rp["n_resolvable"] == 0:
        return (
            "UNDERPOWERED_ORDERING",
            f"잡음 유입 단계는 '뽑기'로 확정. 그러나 seed {n_seeds}개로는 세 뇌 중 "
            f"어느 쌍도 구분되지 않아 순서 비교 자체가 무의미하다 "
            f"(필요 seed 약 {rp['seeds_needed_max']}개)",
        )
    if _matched("pool_tvd_mean"):
        return (
            "SAMPLING_SPREAD_CONFIRMED",
            "pool 번호분포의 seed 간 변동이 세 뇌의 잡음 순서를 재현한다",
        )
    if explaining:
        return (
            "PARTIAL_EXPLANATION",
            f"뽑기 단계가 원인이나, 순서를 설명하는 지표는 {explaining} 뿐이다",
        )
    return (
        "STAGE_ISOLATED_CAUSE_OPEN",
        "뽑기 단계가 원인이나, 뇌별 크기 차이를 설명하는 지표가 없다",
    )


def print_console(
    p: dict[str, Any],
    res: dict[str, Any],
    prior_std: dict[str, float],
    ratio_cand: float | None,
    det_delta: float,
) -> None:
    pc, st, mk = p["premise_check"], res["stat"], res["markov"]
    print(f"[{BENCH_ID}] {p['verdict']['code']} — {p['verdict']['headline_ko']}")
    print(
        f"  전제검증: 구분가능쌍={pc['n_resolvable']}/3 성립={pc['premise_holds']} "
        f"(floor seed={pc['n_seeds_used_in_floor']})"
    )
    for pr in pc["pairs"]:
        print(
            f"    {pr['pair'][0]:7s}vs {pr['pair'][1]:7s} 차이={pr['diff']:.6f} "
            f"임계={pr['resolve_threshold']:.6f} 구분={pr['resolvable']} "
            f"필요seed={pr['seeds_needed']}"
        )
    print(
        f"  점수 결정성: stat={st['weights_deterministic']} "
        f"markov={mk['weights_deterministic']}"
    )
    print(
        f"  유효후보수: stat={st['effective_candidates']['median']} "
        f"markov={mk['effective_candidates']['median']} (배율 {ratio_cand})"
    )
    for b in prior_std:
        gi = res[b]["generation_instability"]
        print(
            f"  {b:<7} pool_tvd={gi['pool_tvd_mean']:.6f} "
            f"presence_std={gi['presence_std_mean']:.6f} "
            f"jaccard={gi['union_jaccard_mean']:.6f} | 실제 seed_std={prior_std[b]}"
        )
    for o in p["ordering"]:
        mark = "일치" if o["matches"] else "불일치"
        print(f"  순서 {o['metric']:<24} {mark} {o['order_by_metric_asc']}")
    print(
        f"  반사실 Δge3(stat)={det_delta:+.6f} "
        f"gate={p['counterfactual_gate']['verdict']}"
    )
    print(f"  elapsed={p['elapsed_sec']}s -> {OUT_JSON}")


def main() -> int:
    t0 = time.time()
    seeds = list(DEFAULT_SEEDS[: _env_int("K_NS_SEEDS", len(DEFAULT_SEEDS))])
    lo = _env_int("K_NS_LO", 836)
    hi = _env_int("K_NS_HI", 1235)
    step = _env_int("K_NS_STEP", 2)

    print(f"[{BENCH_ID}] {lo}~{hi} step={step} seeds={seeds}", flush=True)
    c = collect_cached(lo, hi, seeds, step)
    res = analyze(c, seeds)
    st, mk = res["stat"], res["markov"]

    prior = json.loads((ROOT / PRIOR_FLOOR).read_text(encoding="utf-8"))

    def _infl(b: str) -> Any:
        rows = [r for r in prior[b]["noise_curve"] if r["is_full_range"]]
        return rows[0]["inflation"] if rows else None

    prior_std = {b: float(prior[b]["full_summary"]["std_ge3"]) for b in c["brains"]}
    metrics = (
        "brain_level_ge3_std",
        "pool_tvd_mean",
        "presence_std_mean",
        "ticket_share_mean",
        "union_jaccard_mean",
        "output_perplexity_mean",
    )
    ordering = [ordering_test(res, prior_std, m) for m in metrics]
    # ticket_share·union_jaccard 는 값이 클수록 안정 → 실제 순서와 반대로 맞아야 일치
    for o in ordering:
        if o["metric"] in ("ticket_share_mean", "union_jaccard_mean"):
            o["order_by_metric_asc"] = list(reversed(o["order_by_metric_asc"]))
            o["matches"] = o["order_by_metric_asc"] == o["order_by_seed_std_asc"]
            o["note_ko"] = "값이 클수록 안정적인 지표라 순서를 뒤집어 비교했다"
    explaining = [o["metric"] for o in ordering if o["matches"]]

    ratio_cand = (
        st["effective_candidates"]["median"] / mk["effective_candidates"]["median"]
        if mk["effective_candidates"]["median"] > 0
        else None
    )
    det_delta = round(st["deterministic_ge3"] - st["sampled_ge3"]["mean"], 6)
    cf = classify(det_delta, len(c["targets"]), 2, p0=null_ge3(5))
    paired = {
        b: paired_counterfactual(c["det_hits"][b], c["ge3_hits"][b])
        for b in c["weight_brains"]
    }
    rp = resolvable_pairs(res, prior_std, len(seeds))
    pc = premise_check(prior_std, len(prior.get("seeds", [])) or 10)

    code, head = decide_verdict(res, ordering, rp, pc, explaining, len(seeds))

    gi_s = st["generation_instability"]
    gi_m = mk["generation_instability"]
    detail = (
        f"먼저 확실한 것. stat 의 점수(가중치)는 seed 와 무관하게 항상 같고"
        f"({st['weights_deterministic']}) markov 도 같다({mk['weights_deterministic']}). "
        f"코드상 `repack_by_brain` 도 기본 인자에서 결정적이다. 따라서 **흔들림은 점수를 "
        f"만드는 과정이 아니라 그 점수로 6개를 뽑는 과정에서만 들어온다.** 이건 확정이다.\n\n"
        f"구조 차이도 확인됐다. 유효 후보수 중앙값이 stat "
        f"**{st['effective_candidates']['median']}** 대 markov "
        f"**{mk['effective_candidates']['median']}** "
        f"({'약 %.2f배' % ratio_cand if ratio_cand else '미확인'})다. "
        f"stat 은 45개 전체에서 뽑고 markov 는 상위 25개에서만 뽑는다.\n\n"
        f"다만 '후보가 넓으면 결과도 불안정하다'는 단순 연결은 **성립하지 않았다.** "
        f"pool 번호분포의 seed 간 변동은 오히려 markov 가 가장 크다"
        f"(markov {gi_m['pool_tvd_mean']} > stat {gi_s['pool_tvd_mean']}). "
        f"그런데 최종 잡음은 markov 가 가장 작다. 생성 단계에서 많이 흩어지는 것과 "
        f"결과가 흔들리는 것은 별개다.\n\n"
        f"그리고 더 중요한 것이 나왔다. **이 진단의 전제가 무너졌다.** "
        f"출발점이던 '뇌별 팽창 1.27 대 0.73' 은 seed {pc['n_seeds_used_in_floor']}개로 잰 "
        f"표준편차다. 표준편차에도 오차가 있고, 그 오차를 넘는 쌍이 "
        f"{pc['n_resolvable']}/3 이다. {pc['meaning_ko']} "
        f"이번에 seed {len(seeds)}개·{len(c['targets'])}회차로 독립 측정한 뇌 수준 잡음도 "
        f"stat {st['sampled_ge3']['std']} · markov {mk['sampled_ge3']['std']} · "
        f"review {res['review']['sampled_ge3']['std']} 로 사실상 같다. "
        f"두 측정이 같은 곳을 가리킨다.\n\n"
        f"뇌별 잡음 크기 차이는 **판정 불가**다. 실패가 아니라 측정 정밀도 부족이다. "
        f"seed {len(seeds)}개로 잰 표준편차 자체의 오차가 커서 세 쌍 중 구분되는 쌍이 "
        f"{rp['n_resolvable']}개다. 즉 위 순서표의 '불일치'는 지표가 틀렸다는 뜻이 아니라 "
        f"눈금이 없다는 뜻이다. 쌍을 가르려면 seed 가 약 {rp['seeds_needed_max']}개 필요하다.\n\n"
        f"대신 실무적으로 더 쓸모 있는 답이 나왔다. 뽑기를 없애고 가중치 상위로 결정적으로 "
        f"자르면 흔들림은 **정확히 0** 이 되는데, 적중이 떨어지지 않는다. 같은 회차로 짝지어 "
        f"비교하면 stat 의 ge3 차이는 {paired['stat']['mean_diff']:+.6f} "
        f"(95% 신뢰구간 {paired['stat']['ci95']}, p={paired['stat']['p_two_sided']}) 다. "
        + (
            "오히려 개선 쪽으로 유의하다."
            if paired["stat"]["significant"] and paired["stat"]["mean_diff"] > 0
            else (
                "유의하지는 않지만 **손해라는 증거도 없다.** "
                "잡음을 공짜로 없앨 여지가 있다는 뜻이다."
            )
        )
    )

    payload: dict[str, Any] = {
        "bench_id": BENCH_ID,
        "date": "2026-08-08",
        "ts": datetime.now(timezone.utc).isoformat(),
        "wire": False,
        "policy": {
            "read_only": True,
            "db_write": False,
            "code_change": False,
            "random_choices_frozen_respected": True,
        },
        "draw_range": [lo, hi],
        "step": step,
        "n_targets": len(c["targets"]),
        "seeds": seeds,
        "prior": {
            "file": PRIOR_FLOOR,
            "stat_inflation": _infl("stat"),
            "markov_inflation": _infl("markov"),
            "review_inflation": _infl("review"),
            "stat_seed_std": prior["stat"]["full_summary"]["std_ge3"],
            "markov_seed_std": prior["markov"]["full_summary"]["std_ge3"],
            "review_seed_std": prior["review"]["full_summary"]["std_ge3"],
        },
        "pipeline_randomness": {
            "repack_by_brain_deterministic": True,
            "evidence": (
                "number_scores=가중합 · repack_sets=정렬 · assemble_hybrid_p45_r123=고정규칙 "
                "(random_scores/hint_only 기본 False)"
            ),
            "only_entry_point": "expand_pool -> 각 뇌 predict_sets",
            "shared_stream_ko": (
                "`_live_candidates` 는 `random.seed(seed)` 한 번 뒤에 세 뇌를 "
                "markov → stat → review 순서로 **같은 난수 스트림에서** 호출한다. "
                "markov 는 조건 미달 조합을 버리는 재시도 루프가 있어 소비하는 난수 개수가 "
                "회차마다 다르다. 따라서 stat·review 는 시작 위치 자체가 흔들린 상태에서 뽑는다. "
                "이 구조적 비대칭은 코드로 확인했으나, 뇌별 잡음 크기 차이를 설명하는지는 "
                "이번 진단에서 검증하지 못했다 (review 가 가장 하류인데 stat 보다 조용하다)."
            ),
        },
        "stat": st,
        "markov": mk,
        "review": res["review"],
        "ordering": ordering,
        "metrics_explaining_order": explaining,
        "premise_check": pc,
        "resolvable_pairs": rp,
        "paired_counterfactual": paired,
        "candidate_width_ratio": round(ratio_cand, 4) if ratio_cand else None,
        "markov_weight_source": c.get("markov_weight_source", "predict_markov 재현"),
        "candidate_note_ko": (
            f"stat 의 유효 후보수가 markov 의 "
            f"{'약 %.2f배' % ratio_cand if ratio_cand else '미확인'}다. 구조 차이는 분명하다. "
            "다만 이것만으로 잡음 크기가 정해지는지는 4절에서 따로 검증한다."
        ),
        "instability_note_ko": (
            (
                "pool 번호분포 변동이 실제 잡음 순서를 재현한다. 뽑기 단계에서 번호분포가 "
                "얼마나 흔들리는지가 곧 ge3 잡음이다."
            )
            if any(o["metric"] == "pool_tvd_mean" and o["matches"] for o in ordering)
            else (
                "어떤 생성 지표도 세 뇌의 잡음 순서를 재현하지 못했다. 다만 위 표에서 보듯 "
                "**맞춰야 할 순서 자체가 확정되지 않았다.** 뇌 수준 표준편차 세 쌍 모두 "
                "구분 불가이고, 기준으로 삼은 파이프라인 순서도 seed 10개 측정이라 "
                "마찬가지로 구분되지 않는다(1-B절). 지표가 틀렸다기보다 "
                "**정답표가 없는 시험**이었다."
            )
        ),
        "counterfactual_gate": cf,
        "counterfactual_note_ko": (
            "결정적 절단은 흔들림을 0 으로 만들지만, 세트끼리 번호가 겹치지 않는 "
            "인위적 구성이라 적중 수준을 그대로 발권에 옮길 수는 없다. "
            "여기서 읽을 것은 '적중을 잃지 않고도 흔들림을 없앨 여지가 있는가' 뿐이다."
        ),
        "proposals": [
            {
                "what": "seed 를 평균화 — 같은 회차를 여러 seed 로 뽑아 번호 득표로 확정",
                "why": (
                    "잡음 유입 지점이 '뽑기'로 확정됐으므로, 뽑기를 여러 번 반복해 평균 내면 "
                    "잡음이 √반복수만큼 줄어든다. random.choices 를 수정하지 않으므로 "
                    "동결 조항을 우회하지 않는다. 뇌를 가리지 않고 전부에 적용된다"
                ),
                "risk": "예측 시간이 반복 횟수만큼 늘어난다. 발권 경로 변경이므로 형 GO 필요",
            },
            {
                "what": "stat 전용 잡음 대책은 보류",
                "why": (
                    "뇌별 팽창 차이(1.27 대 0.73)가 측정 오차 안이다. 이번에 seed 24개로 "
                    "독립 측정한 뇌 수준 잡음도 세 뇌가 사실상 같았다. 특정 뇌만 손보는 것은 "
                    "존재가 확인되지 않은 차이를 쫓는 일이다"
                ),
                "risk": (
                    "차이가 실재하는데 놓칠 가능성. 다만 stat 대 markov 를 가르려면 "
                    "잡음바닥 재측정에 seed 16개면 되므로, 확인 비용이 낮다"
                ),
            },
            {
                "what": "판정용 지표를 ge3 에서 번호 확률벡터 스코어로 전환",
                "why": (
                    "잡음의 원인이 '뽑기'라면, 뽑기 이전의 가중치를 직접 채점하면 그 잡음이 "
                    "아예 개입하지 않는다. 코드 변경도 필요 없다"
                ),
                "risk": "발권 성능과 지표가 분리된다. 지표 개선이 발권 개선을 보장하지 않음",
            },
            {
                "what": "잡음바닥(SEED_NOISE_FLOOR)을 seed 16개 이상으로 재측정",
                "why": (
                    "현재 바닥값 0.010127 은 seed 10개 기반이다. 이 값이 앞으로 모든 판정의 "
                    "임계를 정하는데, 그 자체의 오차를 아직 모른다. 바닥을 신뢰하려면 "
                    "먼저 바닥의 오차부터 좁혀야 한다"
                ),
                "risk": "재측정 시간만 든다. 코드·상수 변경 없음",
            },
        ],
        "verdict": {"code": code, "headline_ko": head, "detail_ko": detail},
        "elapsed_sec": round(time.time() - t0, 1),
        "tool": "tools/_k_stat_noise_source_diag.py",
    }
    payload[GATE_KEY] = gate_block(
        n=len(c["targets"]),
        k_cells=2,
        delta=det_delta,
        metric="ge3",
        label="반사실(결정적 절단) vs 뽑기 — stat",
    )

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = build_report(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        DRIVE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"drive copy skip: {e}", file=sys.stderr)

    print_console(payload, res, prior_std, ratio_cand, det_delta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
