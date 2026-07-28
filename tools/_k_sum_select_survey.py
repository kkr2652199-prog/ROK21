# -*- coding: utf-8 -*-
"""K-SUM-SELECT — V2 뇌쿼터 고정 · 티켓 합(이론 138)으로 슬롯 재선택 (READ-ONLY).

가설: V2(m3+s1+r1) 쿼터·풀은 고정하고, set_no 오름 대신
티켓 합 sum이 이론평균 138에 가까운(또는 극단·포트폴리오 다양) 슬롯을
고르면 ge3가 의미있게 오른다.

직교: 뇌 믹스·파라미터·생성 불변 · 발권 선택 기준만.
재탕금지와 구분: BAND-SELECT=LMH(1-15/16-30/31-45) · odd_bal은 BAND 부차정책
· SLICE=당첨/직전 구간일치 · COVER=휠 · SETNO=set_no 격자 · EV-POP=인기도
· 본축=티켓 합(sum) 형태 (aux_balance_keeper sum_score / K-Z·K-AA 폴백합138).

DB mode=ro · coordinator 미수정.
산출: docs/benchmarks/20260729_KSUM_select.json
"""
from __future__ import annotations

import json
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest, spearmanr

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KSUM_select.json"

BRAINS = ("stat", "markov", "review")
QUOTA = {"markov": 3, "stat": 1, "review": 1}
D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
V2_GE3 = 0.1447
V2_MEAN = 1.7504
ALPHA = 0.05
DELTA_GE3_HIT = 0.005

# K-Z / K-AA: C(45,6) 합 이론평균 ≈ 138
SUM_TARGET = 138.0
# 이론 합 범위 대략 21..255; score 감쇠폭은 balance_keeper 와 동일 /60
SUM_SCALE = 60.0


def sum_score(nums: list[int]) -> float:
    """aux_balance_keeper sum_score 와 동일 스케일 (history 미사용 · 이론 138 고정)."""
    s = sum(nums)
    return 1.0 - min(1.0, abs(s - SUM_TARGET) / SUM_SCALE)


def summarize(ms: list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3": 0, "ge3_rate": 0.0, "ge4": 0, "ge4_rate": 0.0}
    ge3 = sum(1 for x in ms if x >= 3)
    ge4 = sum(1 for x in ms if x >= 4)
    return {
        "n": n,
        "mean": round(sum(ms) / n, 4),
        "ge3": ge3,
        "ge3_rate": round(ge3 / n, 4),
        "ge4": ge4,
        "ge4_rate": round(ge4 / n, 4),
    }


def load_pool(con: sqlite3.Connection) -> dict[int, dict[str, list[dict[str, Any]]]]:
    by_dn: dict[int, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: {b: [] for b in BRAINS}
    )
    for r in con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE brain_tag IN (?,?,?) AND draw_no BETWEEN ? AND ?",
        (*BRAINS, D_LO, D_HI),
    ):
        dn, tag = int(r[0]), str(r[1])
        if tag not in BRAINS:
            continue
        try:
            raw = json.loads(r[2] or "[]")
        except json.JSONDecodeError:
            continue
        slots: list[dict[str, Any]] = []
        for i, s in enumerate(raw[:5]):
            nums = [int(x) for x in (s.get("nums") or []) if 1 <= int(x) <= 45]
            if len(nums) != 6:
                continue
            mc = s.get("matched_count")
            if mc is None:
                continue
            nums_s = sorted(nums)
            total = sum(nums_s)
            slots.append(
                {
                    "set_no": int(s.get("set_no") or (i + 1)),
                    "nums": nums_s,
                    "matched_count": int(mc),
                    "confidence": float(s.get("confidence") or 0.0),
                    "sum": total,
                    "sum_abs": abs(total - SUM_TARGET),
                    "sum_score": sum_score(nums_s),
                    "sum_band": int(total // 20) * 20,  # 20단위 밴드 (다양용)
                }
            )
        if len(slots) >= 5:
            by_dn[dn][tag] = slots[:5]
    return {dn: dict(v) for dn, v in by_dn.items()}


def pick_by_set_no(slots: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    return sorted(slots, key=lambda s: s["set_no"])[:k]


def pick_by_key(
    slots: list[dict[str, Any]],
    k: int,
    *,
    key: str,
    reverse: bool,
) -> list[dict[str, Any]]:
    return sorted(
        slots,
        key=lambda s: (s[key], -s["set_no"] if reverse else s["set_no"]),
        reverse=reverse,
    )[:k]


def pick_sum_mid(slots: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    """합 편차 중간대 (절대편차 중앙 근처)."""
    scored = sorted(slots, key=lambda s: (s["sum_abs"], s["set_no"]))
    n = len(scored)
    if k >= n:
        return scored
    start = max(0, (n - k) // 2)
    return scored[start : start + k]


def pick_sum_diverse(slots: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    """탐욕: 이미 고른 sum_band 중복 최소화 · 동점 시 sum_score·set_no."""
    if k >= len(slots):
        return list(slots)
    remaining = list(slots)
    picked: list[dict[str, Any]] = []
    seed = max(remaining, key=lambda s: (s["sum_score"], -s["set_no"]))
    remaining.remove(seed)
    picked.append(seed)
    while len(picked) < k and remaining:
        seen = Counter(p["sum_band"] for p in picked)

        def score(s: dict[str, Any]) -> tuple:
            return (-seen[s["sum_band"]], s["sum_score"], -s["set_no"])

        best = max(remaining, key=score)
        remaining.remove(best)
        picked.append(best)
    return picked


def pick_for_brain(slots: list[dict[str, Any]], k: int, mode: str) -> list[dict[str, Any]]:
    if mode == "asc":
        return pick_by_set_no(slots, k)
    if mode == "sum_near":
        # 이론 138 근접 = sum_score 높은 순 (abs 작은 순과 동치)
        return pick_by_key(slots, k, key="sum_score", reverse=True)
    if mode == "sum_far":
        return pick_by_key(slots, k, key="sum_score", reverse=False)
    if mode == "sum_high":
        return pick_by_key(slots, k, key="sum", reverse=True)
    if mode == "sum_low":
        return pick_by_key(slots, k, key="sum", reverse=False)
    if mode == "sum_mid":
        return pick_sum_mid(slots, k)
    if mode == "sum_diverse":
        return pick_sum_diverse(slots, k)
    raise ValueError(f"unknown mode {mode}")


POLICIES: dict[str, dict[str, str]] = {
    "v2_asc": {"markov": "asc", "stat": "asc", "review": "asc"},
    "all_sum_near": {"markov": "sum_near", "stat": "sum_near", "review": "sum_near"},
    "all_sum_far": {"markov": "sum_far", "stat": "sum_far", "review": "sum_far"},
    "all_sum_high": {"markov": "sum_high", "stat": "sum_high", "review": "sum_high"},
    "all_sum_low": {"markov": "sum_low", "stat": "sum_low", "review": "sum_low"},
    "all_sum_mid": {"markov": "sum_mid", "stat": "sum_mid", "review": "sum_mid"},
    "all_sum_diverse": {
        "markov": "sum_diverse",
        "stat": "sum_diverse",
        "review": "sum_diverse",
    },
    "markov_asc_others_sum_near": {
        "markov": "asc",
        "stat": "sum_near",
        "review": "sum_near",
    },
    "markov_sum_near_others_asc": {
        "markov": "sum_near",
        "stat": "asc",
        "review": "asc",
    },
}


def eval_policy(
    by_dn: dict[int, dict[str, list[dict[str, Any]]]],
    modes: dict[str, str],
) -> dict[str, Any]:
    bests: list[int] = []
    issued_sum_sc: list[float] = []
    issued_mcs: list[int] = []
    issued_sums: list[int] = []
    issued_abs: list[float] = []
    bands: list[int] = []

    for dn in range(D_LO, D_HI + 1):
        brains = by_dn.get(dn) or {}
        if not all(len(brains.get(b) or []) >= 5 for b in BRAINS):
            continue
        issued: list[dict[str, Any]] = []
        for b, k in QUOTA.items():
            issued.extend(pick_for_brain(brains[b], k, modes[b]))
        if len(issued) != 5:
            continue
        mcs = [s["matched_count"] for s in issued]
        bests.append(max(mcs))
        for s in issued:
            issued_sum_sc.append(s["sum_score"])
            issued_mcs.append(s["matched_count"])
            issued_sums.append(s["sum"])
            issued_abs.append(s["sum_abs"])
            bands.append(s["sum_band"])

    sm = summarize(bests)
    p_null = (
        float(binomtest(sm["ge3"], sm["n"], NULL_GE3, alternative="greater").pvalue)
        if sm["n"]
        else 1.0
    )
    mean_sc = sum(issued_sum_sc) / len(issued_sum_sc) if issued_sum_sc else 0.0
    mean_sum = sum(issued_sums) / len(issued_sums) if issued_sums else 0.0
    mean_abs = sum(issued_abs) / len(issued_abs) if issued_abs else 0.0
    sp = sp_p = None
    if len(issued_sum_sc) >= 30:
        sp_res = spearmanr(issued_sum_sc, issued_mcs)
        sp = float(sp_res.correlation) if sp_res.correlation is not None else None
        sp_p = float(sp_res.pvalue) if sp_res.pvalue is not None else None

    top_bands = Counter(bands).most_common(5)
    return {
        **sm,
        "p_vs_null": round(p_null, 6),
        "delta_ge3_vs_v2pin": round(sm["ge3_rate"] - V2_GE3, 4),
        "delta_mean_vs_v2pin": round(sm["mean"] - V2_MEAN, 4),
        "mean_sum_score": round(mean_sc, 4),
        "mean_sum": round(mean_sum, 4),
        "mean_sum_abs_from_138": round(mean_abs, 4),
        "spearman_sumscore_vs_matched": None if sp is None else round(sp, 4),
        "spearman_p": None if sp_p is None else round(sp_p, 6),
        "n_issued_sets": len(issued_sum_sc),
        "top_sum_bands": [{"band": b, "n": n} for b, n in top_bands],
        "beats_v2_ge3": bool(sm["ge3_rate"] > V2_GE3),
    }


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    by_dn = load_pool(con)
    con.close()

    results: dict[str, Any] = {}
    for name, modes in POLICIES.items():
        results[name] = {"modes": modes, "quota": QUOTA, **eval_policy(by_dn, modes)}

    v2 = results["v2_asc"]
    hit_cands = [
        (name, row)
        for name, row in results.items()
        if name != "v2_asc" and row["ge3_rate"] > V2_GE3
    ]
    hit_cands.sort(key=lambda x: (-x[1]["ge3_rate"], -x[1]["mean"]))
    best_hit = hit_cands[0] if hit_cands else None

    gate_hit_beats = bool(best_hit and best_hit[1]["ge3_rate"] > V2_GE3)
    gate_delta = bool(
        best_hit and best_hit[1]["delta_ge3_vs_v2pin"] >= DELTA_GE3_HIT
    )
    gate_null = bool(best_hit and best_hit[1]["p_vs_null"] < ALPHA)
    pass_hit = bool(gate_hit_beats and gate_delta and gate_null)

    ranked = sorted(
        [(n, r) for n, r in results.items() if n != "v2_asc"],
        key=lambda x: (-x[1]["ge3_rate"], -x[1]["mean"]),
    )
    nearest = ranked[0] if ranked else None

    payload = {
        "id": "K-SUM-SELECT",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 3),
        "db_code_write": False,
        "axis": {
            "id": "K-SUM-SELECT",
            "hypothesis": (
                "V2 m3+s1+r1 fixed; within-brain pick by ticket sum "
                "(theory mean 138 / extreme / diverse) instead of set_no asc "
                "→ ge3 lift ≥ +0.005"
            ),
            "orthogonal_to_v2": True,
            "not_rehash_of": [
                "BAND-SELECT",
                "SETNO-HITMAP",
                "EV-POP",
                "COVER-wheel",
                "SLICE-zone-match",
                "SETPACK-TOP6",
                "GATHER",
                "MARKOV-TUNE",
                "conf-quota",
                "HISIM",
                "STRUCT",
            ],
            "code_anchor": (
                "aux_balance_keeper.sum_score · SUM_TARGET=138 (K-Z/K-AA) · "
                "sum_range in draw_features"
            ),
        },
        "protocol": {
            "draw_range": [D_LO, D_HI],
            "quota": QUOTA,
            "null_ge3": NULL_GE3,
            "v2_ge3_pin": V2_GE3,
            "v2_mean_pin": V2_MEAN,
            "sum_target": SUM_TARGET,
            "sum_scale": SUM_SCALE,
            "pass_hit_WIRE": {
                "ge3_gt_v2": True,
                "delta_ge3_min": DELTA_GE3_HIT,
                "binom_p_lt": ALPHA,
            },
            "pass_rule": "hit_WIRE only (ge3↑); no EV-preserve gate on this axis",
        },
        "v2_baseline": {
            "policy": "v2_asc",
            "mean": v2["mean"],
            "ge3_rate": v2["ge3_rate"],
            "ge3": v2["ge3"],
            "ge4_rate": v2["ge4_rate"],
            "p_vs_null": v2["p_vs_null"],
            "mean_sum_score": v2["mean_sum_score"],
            "mean_sum": v2["mean_sum"],
            "n": v2["n"],
        },
        "policies": results,
        "gates": {
            "hit_beats_v2_ge3": gate_hit_beats,
            "hit_delta_ge3_ge_0_005": gate_delta,
            "hit_pass_vs_null": gate_null,
            "PASS": pass_hit,
            "best_hit_policy": None if not best_hit else best_hit[0],
            "best_hit_ge3": None if not best_hit else best_hit[1]["ge3_rate"],
            "best_hit_delta_ge3": None
            if not best_hit
            else best_hit[1]["delta_ge3_vs_v2pin"],
            "nearest_policy": None if not nearest else nearest[0],
            "nearest_ge3": None if not nearest else nearest[1]["ge3_rate"],
            "nearest_delta_ge3": None
            if not nearest
            else nearest[1]["delta_ge3_vs_v2pin"],
        },
        "verdict": "PASS_CANDIDATE_NO_WIRE" if pass_hit else "FAIL_HOLD_V2",
        "recommended_next": (
            "K-SUM-SELECT-WIRE (형 GO 전 후보만 · coordinator 패치 금지)"
            if pass_hit
            else "없음(HOLD·V2유지·SUM-SELECT재탕금지)"
        ),
        "note": (
            "READ-ONLY brain_review nums+matched · sum=aux_balance_keeper식 "
            "(이론138·history미사용) · BAND/SLICE/COVER와 직교"
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "verdict": payload["verdict"],
                "gates": payload["gates"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
