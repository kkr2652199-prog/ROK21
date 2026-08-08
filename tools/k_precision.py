# -*- coding: utf-8 -*-
"""k_precision — 측정 정밀도 공용 모듈 (R39).

왜 필요한가
----------
2026-08-08 K-STAT-NOISE-SOURCE 에서 헛수고가 하나 드러났다.

  · 잡음바닥 측정이 뇌별 팽창계수를 stat 1.2739 / markov 0.7329 로 냈다
  · 이 서열을 참으로 놓고 "왜 stat 만 시끄러운가"를 파고들었다
  · 그런데 그 값은 seed **10개**로 잰 표준편차였다
  · 표준편차에도 오차가 있다. 그 오차를 넘는 뇌 쌍은 **0/3** 이었다

즉 존재가 확인되지 않은 차이를 설명하려 한 것이다. 평균을 비교할 때는 표준오차를
따지면서, 표준편차끼리 비교할 때는 그냥 크기만 봤던 게 원인이다.

이 모듈은 그 절차를 강제한다. **표준편차·분산·잡음 크기를 서로 비교하기 전에
반드시 여기를 거친다.**

핵심 공식
--------
정규 표본에서 크기 k 표본표준편차의 표준오차는 근사적으로

    SE(σ̂) ≈ σ / √(2(k−1))

k 가 작으면 이 값이 놀랄 만큼 크다. k=10 이면 σ 의 약 24% 다. 두 표준편차가
20% 차이 나도 구분되지 않는다는 뜻이다.

사용법
------
    from tools.k_precision import pairwise_resolvable

    block = pairwise_resolvable({"stat": 0.011754, "markov": 0.006762}, n_seeds=10)
    if not block["any_resolvable"]:
        ...  # 서열을 인용하면 안 된다

정책
----
순수 계산 모듈. DB·파일·전역상태를 건드리지 않는다.
"""
from __future__ import annotations

import math
from itertools import combinations
from typing import Any

import numpy as np

__all__ = [
    "PRECISION_KEY",
    "PRECISION_RULE",
    "pairwise_resolvable",
    "resolvable",
    "seeds_needed",
    "self_test",
    "std_se",
]

PRECISION_KEY = "precision_check"
PRECISION_RULE = "R39"

Z95 = 1.959964


def std_se(sigma: float, k: int) -> float:
    """표본표준편차 σ̂ 자체의 표준오차. k 는 표본 개수(seed 개수)."""
    if k < 2:
        return float("inf")
    return sigma / math.sqrt(2 * (k - 1))


def resolvable(
    sigma_a: float, sigma_b: float, k: int, z: float = Z95
) -> dict[str, Any]:
    """두 표준편차가 측정 오차를 넘어 구분되는지 판정한다.

    구분 임계 = z·√(SE(σ̂_a)² + SE(σ̂_b)²). 관측 차이가 이보다 작으면
    "차이 없음"이 아니라 **"모른다"** 다. 둘을 혼동하면 안 된다.
    """
    se_a, se_b = std_se(sigma_a, k), std_se(sigma_b, k)
    crit = z * math.sqrt(se_a**2 + se_b**2)
    diff = abs(sigma_a - sigma_b)
    return {
        "sigma": [round(sigma_a, 6), round(sigma_b, 6)],
        "n_samples": k,
        "se": [round(se_a, 6), round(se_b, 6)],
        "diff": round(diff, 6),
        "resolve_threshold": round(crit, 6),
        "resolvable": bool(diff > crit),
        "samples_needed": seeds_needed(sigma_a, sigma_b, z),
    }


def seeds_needed(sigma_a: float, sigma_b: float, z: float = Z95) -> int | None:
    """관측된 차이가 유지된다고 볼 때, 그 차이를 가르는 데 필요한 표본 개수.

    z·√((σa²+σb²)/(2(k−1))) < |σa−σb| 를 k 에 대해 푼다.
    차이가 0 이면 어떤 k 로도 가를 수 없으므로 None.
    """
    d = abs(sigma_a - sigma_b)
    if d <= 0:
        return None
    return int(math.ceil(1 + (z * math.sqrt(sigma_a**2 + sigma_b**2) / d) ** 2 / 2))


def pairwise_resolvable(
    sigmas: dict[str, float],
    n_seeds: int,
    truth_order: dict[str, float] | None = None,
    z: float = Z95,
) -> dict[str, Any]:
    """여러 계열의 표준편차를 쌍마다 비교한다.

    `truth_order` 를 주면 (예: 파이프라인 실측 seed 표준편차) **구분 가능한 쌍에
    한해** 순서가 일치하는지도 본다. 구분 불가한 쌍을 '불일치'로 세면 정밀도
    부족을 결론으로 착각하게 되므로, 그 쌍은 판정에서 뺀다.
    """
    names = list(sigmas)
    pairs: list[dict[str, Any]] = []
    for a, b in combinations(names, 2):
        r = resolvable(sigmas[a], sigmas[b], n_seeds, z)
        r["pair"] = [a, b]
        if truth_order is not None and r["resolvable"]:
            r["order_agrees"] = (sigmas[a] < sigmas[b]) == (
                truth_order[a] < truth_order[b]
            )
        elif truth_order is not None:
            r["order_agrees"] = None
        pairs.append(r)

    res = [p for p in pairs if p["resolvable"]]
    needs = [p["samples_needed"] for p in pairs if p["samples_needed"]]
    out: dict[str, Any] = {
        "rule": PRECISION_RULE,
        "n_samples": n_seeds,
        "sigma": {k: round(v, 6) for k, v in sigmas.items()},
        "se": {k: round(std_se(v, n_seeds), 6) for k, v in sigmas.items()},
        "pairs": pairs,
        "n_pairs": len(pairs),
        "n_resolvable": len(res),
        "any_resolvable": bool(res),
        "samples_needed_max": max(needs) if needs else None,
        "formula": "SE(sigma_hat) = sigma / sqrt(2(k-1))",
    }
    if truth_order is not None:
        out["n_agree"] = sum(1 for p in res if p["order_agrees"])
        out["order_fully_agrees"] = bool(res) and out["n_agree"] == len(res)
    out["meaning_ko"] = (
        (
            f"구분 가능한 쌍이 0개다. 계열 간 서열은 측정 오차 안의 흔들림이므로 "
            f"서열을 인용하면 안 된다. 가르려면 표본 약 "
            f"{out['samples_needed_max']}개가 필요하다."
        )
        if not res
        else (
            f"구분 가능한 쌍 {len(res)}/{len(pairs)}. 이 쌍들에 한해 서열을 말할 수 있다."
        )
    )
    return out


def self_test(b: int = 4000, k_list: tuple[int, ...] = (5, 10, 24, 60)) -> dict[str, Any]:
    """공식이 맞는지 몬테카를로로 확인한다.

    정규분포에서 크기 k 표본을 B번 뽑아 표본표준편차의 실제 산포를 재고,
    `std_se` 예측과 비교한다. 예측이 근사식이므로 k 가 작을수록 오차가 크다.
    """
    rng = np.random.default_rng(20260808)
    sigma = 0.02
    checks: list[dict[str, Any]] = []

    for k in k_list:
        samples = rng.normal(0.0, sigma, size=(b, k))
        emp = samples.std(axis=1, ddof=0).std()
        pred = std_se(sigma, k)
        rel = abs(emp - pred) / pred
        checks.append(
            {
                "name": f"MC k={k}",
                "empirical_se": round(float(emp), 6),
                "predicted_se": round(pred, 6),
                "rel_err": round(float(rel), 4),
                "pass": bool(rel < 0.20),
            }
        )

    # 필요 표본수가 실제로 그 쌍을 가르는지
    sa, sb = 0.011754, 0.006762
    need = seeds_needed(sa, sb)
    checks.append(
        {
            "name": "seeds_needed 자기일관성",
            "need": need,
            "at_need": resolvable(sa, sb, need)["resolvable"],
            "at_need_minus_1": resolvable(sa, sb, max(2, need - 1))["resolvable"],
            "pass": bool(
                resolvable(sa, sb, need)["resolvable"]
                and not resolvable(sa, sb, max(2, need - 1))["resolvable"]
            ),
        }
    )

    # 표본이 늘면 임계는 반드시 좁아진다
    crits = [resolvable(sa, sb, k)["resolve_threshold"] for k in (5, 10, 40, 200)]
    checks.append(
        {
            "name": "표본↑ → 임계↓ 단조성",
            "crits": crits,
            "pass": all(x > y for x, y in zip(crits, crits[1:])),
        }
    )

    # 실제 사건 재현: seed10 뇌별 팽창차는 구분 불가여야 한다
    hist = pairwise_resolvable(
        {"stat": 0.011754, "markov": 0.006762, "review": 0.008152}, 10
    )
    checks.append(
        {
            "name": "NOISE-SOURCE 재현 (seed10 · 구분가능쌍 0/3)",
            "n_resolvable": hist["n_resolvable"],
            "pass": hist["n_resolvable"] == 0,
        }
    )

    return {
        "checks": checks,
        "n": len(checks),
        "all_pass": all(c["pass"] for c in checks),
    }


if __name__ == "__main__":
    import json

    r = self_test()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    raise SystemExit(0 if r["all_pass"] else 1)
