# -*- coding: utf-8 -*-
"""구조 질량 covering — K-MATH-PATTERN-WARRANT 1축 설계.

목적: 5장 발권이 합·존·홀짝·연속 축에서 '질량 대역'을 넓게 덮게 한다.
1등확률↑ 주장 아님 · 명분=조합 질량 배치 + 1~1235 실측 정합.

WIRE 기본 OFF. survey 통과 후에만 형 GO로 켠다.
"""
from __future__ import annotations

from typing import Any

# live wire 스위치 (survey 전 OFF)
STRUCTURE_COVER_WIRE: bool = False
STRUCTURE_COVER_BRAINS: frozenset[str] = frozenset({"stat", "markov", "review"})
N_COVER = 5

# 질량 대역 가중 (WARRANT: 3홀3짝·합~138·존혼합·연속허용)
_ODD_MASS = {2: 1.0, 3: 1.2, 4: 1.0}  # 그 외 낮음
_SUM_CORE = (100, 180)  # inclusive-ish core band


def set_structure(nums: list[int]) -> dict[str, Any]:
    ns = sorted(int(x) for x in nums)
    if len(ns) != 6:
        return {"ok": False}
    odd = sum(1 for n in ns if n % 2 == 1)
    low = sum(1 for n in ns if 1 <= n <= 15)
    mid = sum(1 for n in ns if 16 <= n <= 30)
    high = sum(1 for n in ns if 31 <= n <= 45)
    s = sum(ns)
    max_run = 1
    cur = 1
    for i in range(1, 6):
        if ns[i] == ns[i - 1] + 1:
            cur += 1
            max_run = max(max_run, cur)
        else:
            cur = 1
    n_consec = sum(1 for i in range(5) if ns[i + 1] == ns[i] + 1)
    return {
        "ok": True,
        "nums": ns,
        "sum": s,
        "sum_bucket": s // 20,
        "odd": odd,
        "zone": (low, mid, high),
        "zone_key": f"{low}-{mid}-{high}",
        "max_run": max_run,
        "n_consec": n_consec,
        "has_consec": n_consec >= 1,
        "span": ns[-1] - ns[0],
        "extreme_odd": odd in (0, 6),
        "extreme_zone": max(low, mid, high) >= 5,
        "sum_in_core": _SUM_CORE[0] <= s <= _SUM_CORE[1],
    }


def structure_keys(st: dict[str, Any]) -> tuple:
    """covering 단위 키 — 이 축을 5장이 다양하게 덮는지 본다."""
    return (
        int(st["sum_bucket"]),
        int(st["odd"]),
        str(st["zone_key"]),
        bool(st["has_consec"]),
    )


def mass_score(st: dict[str, Any]) -> float:
    """단일 세트가 질량 대역에 있는지 (높을수록 우선 후보)."""
    if not st.get("ok"):
        return -1e9
    score = 0.0
    score += _ODD_MASS.get(int(st["odd"]), 0.2)
    if st["sum_in_core"]:
        score += 1.0
    else:
        score -= 0.5
    if st["extreme_odd"] or st["extreme_zone"]:
        score -= 1.5
    # 연속은 감점하지 않음 (W-CONSEC: 배제 금지)
    if st["has_consec"]:
        score += 0.15
    # 존 혼합 보너스
    z = st["zone"]
    if min(z) >= 1 and max(z) <= 3:
        score += 0.4
    return score


def select_structure_cover(
    candidates: list[dict],
    *,
    n_sets: int = N_COVER,
) -> list[dict]:
    """탐욕 covering: 질량 점수 + 새 구조키 보너스.

    candidates: {nums, ...} 리스트 (pool+repack 등)
    """
    scored: list[tuple[float, tuple[int, ...], dict, dict]] = []
    for c in candidates:
        nums = [int(x) for x in c.get("nums") or []]
        st = set_structure(nums)
        if not st.get("ok"):
            continue
        key = structure_keys(st)
        scored.append((mass_score(st), tuple(st["nums"]), c, st))

    # 1차: 질량순
    scored.sort(key=lambda x: (-x[0], x[1]))

    picked: list[dict] = []
    seen_nums: set[tuple[int, ...]] = set()
    covered: set[tuple] = set()

    def pack(c: dict, st: dict, nums: tuple[int, ...]) -> dict:
        out = dict(c)
        out["nums"] = list(nums)
        out["assemble"] = "struct_cover_v1"
        out["structure"] = {
            "sum": st["sum"],
            "odd": st["odd"],
            "zone_key": st["zone_key"],
            "has_consec": st["has_consec"],
            "sum_bucket": st["sum_bucket"],
            "mass_score": round(mass_score(st), 4),
        }
        return out

    # greedy: each next pick maximizes (new keys + mass)
    pool = list(scored)
    while pool and len(picked) < n_sets:
        best_i = None
        best_val = None
        for i, (ms, nums, c, st) in enumerate(pool):
            if nums in seen_nums:
                continue
            keys = structure_keys(st)
            new_bonus = 0.0 if keys in covered else 1.25
            # 부분 축 다양성
            partial = 0.0
            if ("sum", st["sum_bucket"]) not in {( "sum", k[0]) for k in covered}:
                partial += 0.2
            if ("odd", st["odd"]) not in {("odd", k[1]) for k in covered}:
                partial += 0.2
            if ("zone", st["zone_key"]) not in {("zone", k[2]) for k in covered}:
                partial += 0.2
            if ("consec", st["has_consec"]) not in {("consec", k[3]) for k in covered}:
                partial += 0.15
            val = (new_bonus + partial + 0.35 * ms, -i)
            if best_val is None or val > best_val:
                best_val = val
                best_i = i
        if best_i is None:
            break
        ms, nums, c, st = pool.pop(best_i)
        seen_nums.add(nums)
        covered.add(structure_keys(st))
        entry = pack(c, st, nums)
        entry["set_no"] = len(picked) + 1
        entry["repack_rank"] = entry["set_no"]
        entry["pred_set_no"] = entry["set_no"]
        picked.append(entry)

    return picked


def coverage_report(sets: list[dict]) -> dict[str, Any]:
    keys = []
    masses = []
    for s in sets:
        st = s.get("structure") or set_structure(s.get("nums") or [])
        if not st.get("ok") and "sum" not in st:
            continue
        if "zone_key" not in st:
            st = set_structure(s.get("nums") or [])
        keys.append(structure_keys(st))
        masses.append(mass_score(st))
    return {
        "n": len(sets),
        "unique_structure_keys": len(set(keys)),
        "mean_mass": round(sum(masses) / len(masses), 4) if masses else 0.0,
        "keys": [
            {
                "sum_bucket": k[0],
                "odd": k[1],
                "zone": k[2],
                "consec": k[3],
            }
            for k in keys
        ],
    }
