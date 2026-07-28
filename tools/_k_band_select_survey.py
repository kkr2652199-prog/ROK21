# -*- coding: utf-8 -*-
"""K-BAND-SELECT — V2 뇌쿼터 고정 · 티켓 내 LMH 번호대역으로 슬롯 재선택 (READ-ONLY).

가설: V2(m3+s1+r1) 쿼터·풀은 고정하고, set_no 오름 대신
티켓 내 LMH(1-15/16-30/31-45) 이론점수(또는 극단·포트폴리오 다양)로
슬롯을 고르면 ge3가 의미있게 오른다.

직교: 뇌 믹스·파라미터·생성 불변 · 발권 선택 기준만.
재탕금지와 구분: SLICE=당첨/직전 구간일치 승격 · COVER=휠·union ·
SETNO=고정 set_no 격자 · EV-POP=인기도 · 본축=티켓 자체 LMH 형태.

DB mode=ro · coordinator 미수정.
산출: docs/benchmarks/20260729_KBAND_select.json
"""
from __future__ import annotations

import json
import math
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import datetime
from math import comb
from pathlib import Path
from typing import Any

from scipy.stats import binomtest, spearmanr

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KBAND_select.json"

BRAINS = ("stat", "markov", "review")
QUOTA = {"markov": 3, "stat": 1, "review": 1}
D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
V2_GE3 = 0.1447
V2_MEAN = 1.7504
ALPHA = 0.05
DELTA_GE3_HIT = 0.005

_N_COMBOS = comb(45, 6)
_LMH_MODE_P = (comb(15, 2) * comb(15, 2) * comb(15, 2)) / _N_COMBOS


def zone_counts(nums: list[int]) -> tuple[int, int, int]:
    low = sum(1 for n in nums if 1 <= n <= 15)
    mid = sum(1 for n in nums if 16 <= n <= 30)
    high = sum(1 for n in nums if 31 <= n <= 45)
    return low, mid, high


def lmh_p(low: int, mid: int, high: int) -> float:
    if low + mid + high != 6 or min(low, mid, high) < 0:
        return 0.0
    if low > 15 or mid > 15 or high > 15:
        return 0.0
    return (comb(15, low) * comb(15, mid) * comb(15, high)) / _N_COMBOS


def lmh_score(nums: list[int]) -> float:
    """aux_balance_keeper._zone_score_lmh 와 동일 스케일."""
    low, mid, high = zone_counts(nums)
    p = lmh_p(low, mid, high)
    return 0.3 + 0.4 * (p / _LMH_MODE_P)


def lmh_l1_from_222(nums: list[int]) -> int:
    low, mid, high = zone_counts(nums)
    return abs(low - 2) + abs(mid - 2) + abs(high - 2)


def odd_balance(nums: list[int]) -> float:
    """홀수 개수 3에 가까울수록 높음 (0~1)."""
    odds = sum(1 for n in nums if n % 2 == 1)
    return 1.0 - min(1.0, abs(odds - 3) / 3.0)


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
            z = zone_counts(nums_s)
            slots.append(
                {
                    "set_no": int(s.get("set_no") or (i + 1)),
                    "nums": nums_s,
                    "matched_count": int(mc),
                    "confidence": float(s.get("confidence") or 0.0),
                    "lmh": z,
                    "lmh_key": f"{z[0]}-{z[1]}-{z[2]}",
                    "lmh_score": lmh_score(nums_s),
                    "lmh_l1": lmh_l1_from_222(nums_s),
                    "odd_bal": odd_balance(nums_s),
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
    return sorted(slots, key=lambda s: (s[key], -s["set_no"] if reverse else s["set_no"]), reverse=reverse)[:k]


def pick_lmh_diverse(slots: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    """탐욕: 이미 고른 LMH 키와 겹침을 최소화 · 동점 시 lmh_score·set_no."""
    if k >= len(slots):
        return list(slots)
    remaining = list(slots)
    picked: list[dict[str, Any]] = []
    # seed: highest lmh_score
    seed = max(remaining, key=lambda s: (s["lmh_score"], -s["set_no"]))
    remaining.remove(seed)
    picked.append(seed)
    while len(picked) < k and remaining:
        seen = Counter(p["lmh_key"] for p in picked)

        def score(s: dict[str, Any]) -> tuple:
            # fewer duplicate keys better; then higher theory score; then lower set_no
            return (-seen[s["lmh_key"]], s["lmh_score"], -s["set_no"])

        best = max(remaining, key=score)
        remaining.remove(best)
        picked.append(best)
    return picked


def pick_for_brain(slots: list[dict[str, Any]], k: int, mode: str) -> list[dict[str, Any]]:
    if mode == "asc":
        return pick_by_set_no(slots, k)
    if mode == "lmh_high":
        return pick_by_key(slots, k, key="lmh_score", reverse=True)
    if mode == "lmh_low":
        return pick_by_key(slots, k, key="lmh_score", reverse=False)
    if mode == "lmh_mid":
        # mid distance from 222 (l1 around median)
        scored = sorted(slots, key=lambda s: (s["lmh_l1"], s["set_no"]))
        n = len(scored)
        if k >= n:
            return scored
        start = max(0, (n - k) // 2)
        return scored[start : start + k]
    if mode == "lmh_diverse":
        return pick_lmh_diverse(slots, k)
    if mode == "odd_bal":
        return pick_by_key(slots, k, key="odd_bal", reverse=True)
    raise ValueError(f"unknown mode {mode}")


POLICIES: dict[str, dict[str, str]] = {
    "v2_asc": {"markov": "asc", "stat": "asc", "review": "asc"},
    "all_lmh_high": {"markov": "lmh_high", "stat": "lmh_high", "review": "lmh_high"},
    "all_lmh_low": {"markov": "lmh_low", "stat": "lmh_low", "review": "lmh_low"},
    "all_lmh_mid": {"markov": "lmh_mid", "stat": "lmh_mid", "review": "lmh_mid"},
    "all_lmh_diverse": {
        "markov": "lmh_diverse",
        "stat": "lmh_diverse",
        "review": "lmh_diverse",
    },
    "markov_asc_others_lmh_high": {
        "markov": "asc",
        "stat": "lmh_high",
        "review": "lmh_high",
    },
    "markov_lmh_high_others_asc": {
        "markov": "lmh_high",
        "stat": "asc",
        "review": "asc",
    },
    "all_odd_bal": {"markov": "odd_bal", "stat": "odd_bal", "review": "odd_bal"},
}


def eval_policy(
    by_dn: dict[int, dict[str, list[dict[str, Any]]]],
    modes: dict[str, str],
) -> dict[str, Any]:
    bests: list[int] = []
    issued_lmh: list[float] = []
    issued_mcs: list[int] = []
    issued_l1: list[int] = []
    zone_keys: list[str] = []

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
            issued_lmh.append(s["lmh_score"])
            issued_mcs.append(s["matched_count"])
            issued_l1.append(s["lmh_l1"])
            zone_keys.append(s["lmh_key"])

    sm = summarize(bests)
    p_null = (
        float(binomtest(sm["ge3"], sm["n"], NULL_GE3, alternative="greater").pvalue)
        if sm["n"]
        else 1.0
    )
    mean_lmh = sum(issued_lmh) / len(issued_lmh) if issued_lmh else 0.0
    mean_l1 = sum(issued_l1) / len(issued_l1) if issued_l1 else 0.0
    sp = sp_p = None
    if len(issued_lmh) >= 30:
        sp_res = spearmanr(issued_lmh, issued_mcs)
        sp = float(sp_res.correlation) if sp_res.correlation is not None else None
        sp_p = float(sp_res.pvalue) if sp_res.pvalue is not None else None

    top_zones = Counter(zone_keys).most_common(5)
    return {
        **sm,
        "p_vs_null": round(p_null, 6),
        "delta_ge3_vs_v2pin": round(sm["ge3_rate"] - V2_GE3, 4),
        "delta_mean_vs_v2pin": round(sm["mean"] - V2_MEAN, 4),
        "mean_lmh_score": round(mean_lmh, 4),
        "mean_lmh_l1_from_222": round(mean_l1, 4),
        "spearman_lmh_vs_matched": None if sp is None else round(sp, 4),
        "spearman_p": None if sp_p is None else round(sp_p, 6),
        "n_issued_sets": len(issued_lmh),
        "top_lmh_keys": [{"key": k, "n": n} for k, n in top_zones],
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

    # ranking of all non-baseline by ge3
    ranked = sorted(
        [(n, r) for n, r in results.items() if n != "v2_asc"],
        key=lambda x: (-x[1]["ge3_rate"], -x[1]["mean"]),
    )
    nearest = ranked[0] if ranked else None

    payload = {
        "id": "K-BAND-SELECT",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 3),
        "db_code_write": False,
        "axis": {
            "id": "K-BAND-SELECT",
            "hypothesis": (
                "V2 m3+s1+r1 fixed; within-brain pick by LMH band score "
                "(theory 2-2-2 / extreme / diverse) instead of set_no asc "
                "→ ge3 lift ≥ +0.005"
            ),
            "orthogonal_to_v2": True,
            "not_rehash_of": [
                "SETNO-HITMAP",
                "EV-POP",
                "COVER-wheel",
                "SLICE-zone-match",
                "SETPACK-TOP6",
                "GATHER",
                "MARKOV-TUNE",
                "conf-quota",
            ],
        },
        "protocol": {
            "draw_range": [D_LO, D_HI],
            "quota": QUOTA,
            "null_ge3": NULL_GE3,
            "v2_ge3_pin": V2_GE3,
            "v2_mean_pin": V2_MEAN,
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
            "mean_lmh_score": v2["mean_lmh_score"],
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
            "K-BAND-SELECT-WIRE (형 GO 전 후보만 · coordinator 패치 금지)"
            if pass_hit
            else "없음(HOLD·V2유지·BAND-SELECT재탕금지)"
        ),
        "note": (
            "READ-ONLY brain_review nums+matched · LMH=aux_balance_keeper 식 · "
            "history/당첨구간 미사용(SLICE와 직교)"
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "verdict": payload["verdict"], "gates": payload["gates"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
