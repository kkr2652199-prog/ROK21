# -*- coding: utf-8 -*-
"""K-GATHER-V2 — V축소(단독·자리·구간·confidence) + covering 5장 PILOT."""
from __future__ import annotations

import json
import math
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KGATHER_v2_pilot.json"
ORACLE = ROOT / "docs" / "benchmarks" / "20260729_KGATHER_v1_oracle.json"


def zones(n: int) -> int:
    if n <= 15:
        return 0
    if n <= 30:
        return 1
    return 2


def legal(nums: list[int]) -> bool:
    s = sorted(nums)
    if len(s) != 6 or len(set(s)) != 6:
        return False
    return all(k + 1 <= x <= 40 + k for k, x in enumerate(s))


def shrink_V(bases: list[list[int]], confs: list[float]) -> list[int]:
    """단독출현 우선 + confidence 가중 + 구간 균형 목표로 |V'|≈12."""
    appear = Counter()
    score: dict[int, float] = defaultdict(float)
    for b, c in zip(bases, confs):
        w = 0.5 + (c / 100.0 if c else 0.5)
        for n in set(b):
            appear[n] += 1
            score[n] += w
    # exclusives first
    excl = [n for n, a in appear.items() if a == 1]
    multi = [n for n, a in appear.items() if a > 1]
    excl.sort(key=lambda n: (-score[n], n))
    multi.sort(key=lambda n: (-score[n], n))
    # target ~12 with zone balance
    picked: list[int] = []
    zcnt = [0, 0, 0]
    for pool in (excl, multi):
        for n in pool:
            if len(picked) >= 12:
                break
            z = zones(n)
            if zcnt[z] >= 5 and len(picked) < 10:
                continue
            picked.append(n)
            zcnt[z] += 1
        if len(picked) >= 12:
            break
    if len(picked) < 6:
        rest = sorted(appear.keys(), key=lambda n: (-score[n], n))
        for n in rest:
            if n not in picked:
                picked.append(n)
            if len(picked) >= 6:
                break
    return sorted(picked)


def covering_5(V: list[int]) -> list[list[int]]:
    """Abbreviated wheel-ish: greedy maximize new pairs, 5 blocks of 6."""
    if len(V) < 6:
        return []
    pair_cov: set[tuple[int, int]] = set()
    out: list[list[int]] = []
    # seed blocks by sliding windows on sorted V (positional)
    vs = list(V)
    seeds = []
    if len(vs) >= 6:
        step = max(1, (len(vs) - 6) // 4)
        for i in range(5):
            start = min(i * step, len(vs) - 6)
            seeds.append(vs[start : start + 6])
    for seed in seeds:
        # local improve: swap in uncovered rare pairs
        best = sorted(seed)
        best_gain = -1
        for cand in combinations(vs, 6):
            # only evaluate neighborhood: share >=3 with seed
            if len(set(cand) & set(seed)) < 3:
                continue
            pairs = set(combinations(sorted(cand), 2))
            gain = len(pairs - pair_cov)
            if gain > best_gain and legal(list(cand)):
                best_gain = gain
                best = sorted(cand)
        # if too slow path: just use seed if legal
        if not legal(best):
            best = sorted(vs[:6]) if legal(vs[:6]) else sorted(vs[-6:])
        out.append(best)
        pair_cov |= set(combinations(best, 2))
    # ensure 5
    while len(out) < 5 and len(vs) >= 6:
        out.append(sorted(vs[:6]))
    return out[:5]


def covering_5_fast(V: list[int]) -> list[list[int]]:
    """Fast constructive covering without C(n,6) scan."""
    vs = sorted(V)
    n = len(vs)
    if n < 6:
        return []
    out = []
    for i in range(5):
        # rotate start
        rot = vs[i:] + vs[:i]
        # take spread indices
        idxs = [0, n // 5, 2 * n // 5, 3 * n // 5, 4 * n // 5, n - 1]
        combo = sorted({rot[min(j, n - 1) % n] for j in idxs})
        # repair size
        k = 0
        while len(combo) < 6:
            x = rot[k % n]
            if x not in combo:
                combo.append(x)
            k += 1
            combo = sorted(combo)
        if not legal(combo):
            combo = sorted(vs[:6])
        out.append(combo)
    return out


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    actuals = {
        int(r[0]): set(int(r[i]) for i in range(1, 7))
        for r in con.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no BETWEEN 2 AND 1234"
        )
    }
    rows = con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE draw_no BETWEEN 2 AND 1234 ORDER BY draw_no"
    ).fetchall()
    con.close()
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    u6 = set(oracle["summary"]["draws"])

    brains: dict[str, Any] = defaultdict(lambda: defaultdict(list))
    shrink_sizes = []
    u6_rows = []

    for r in rows:
        d = int(r["draw_no"])
        act = actuals.get(d)
        if not act:
            continue
        tag = r["brain_tag"]
        sets = json.loads(r["predicted_sets_json"] or "[]")
        bases, confs = [], []
        for s in sets:
            nums = [int(x) for x in (s.get("nums") or [])]
            if len(nums) == 6:
                bases.append(nums)
                confs.append(float(s.get("confidence") or 60))
        if len(bases) < 5:
            continue
        base_best = max(len(set(b) & act) for b in bases)
        Vp = shrink_V(bases, confs)
        shrink_sizes.append(len(Vp))
        gsets = covering_5_fast(Vp)
        if not gsets:
            continue
        g_best = max(len(set(g) & act) for g in gsets)
        union = {n for b in bases for n in b}
        brains[tag]["base"].append(base_best)
        brains[tag]["gather"].append(g_best)
        brains[tag]["delta"].append(g_best - base_best)
        brains[tag]["Vp"].append(len(Vp))
        if act.issubset(union):
            brains[tag]["u6_g"].append(g_best)
            brains[tag]["u6_b"].append(base_best)
            if tag == "stat" and d in u6:
                u6_rows.append(
                    {
                        "draw": d,
                        "Vp": len(Vp),
                        "act_in_Vp": len(act & set(Vp)),
                        "base": base_best,
                        "gather": g_best,
                    }
                )

    out_b = {}
    for tag, st in brains.items():
        n = len(st["base"])
        out_b[tag] = {
            "n": n,
            "Vp_mean": round(sum(st["Vp"]) / n, 2),
            "base_best_mean": round(sum(st["base"]) / n, 4),
            "gather_best_mean": round(sum(st["gather"]) / n, 4),
            "delta_mean": round(sum(st["delta"]) / n, 4),
            "base_ge4": round(sum(1 for x in st["base"] if x >= 4) / n, 4),
            "gather_ge4": round(sum(1 for x in st["gather"] if x >= 4) / n, 4),
            "u6_n": len(st["u6_g"]),
            "u6_gather_mean": round(sum(st["u6_g"]) / len(st["u6_g"]), 4) if st["u6_g"] else None,
            "u6_base_mean": round(sum(st["u6_b"]) / len(st["u6_b"]), 4) if st["u6_b"] else None,
            "recover_ge5": sum(1 for x in st["u6_g"] if x >= 5),
            "recover_ge6": sum(1 for x in st["u6_g"] if x >= 6),
            "improved_rate": round(sum(1 for x in st["delta"] if x > 0) / n, 4),
        }

    st = out_b.get("stat", {})
    gate = (st.get("recover_ge5") or 0) >= 1 or (
        (st.get("u6_gather_mean") or 0) >= (st.get("u6_base_mean") or 99)
    )
    # also apply AI idea: hybrid keep base+gather max as "10-set pool best"
    hybrid = {}
    for tag, st2 in brains.items():
        n = len(st2["base"])
        hy = [max(b, g) for b, g in zip(st2["base"], st2["gather"])]
        hybrid[tag] = {
            "best_of_base_or_gather_mean": round(sum(hy) / n, 4),
            "ge4_rate": round(sum(1 for x in hy if x >= 4) / n, 4),
        }

    payload = {
        "id": "K-GATHER-V2",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "algo": "shrink_excl_conf_zone + spread_covering5",
        "ai_extras": [
            "hybrid best(base,gather) as 10-set ceiling without WIRE",
            "V shrink target 12 (ensemble literature: reduce candidate set before wheel)",
        ],
        "Vp_mean_all": round(sum(shrink_sizes) / len(shrink_sizes), 2) if shrink_sizes else 0,
        "brains": out_b,
        "hybrid_10set_proxy": hybrid,
        "stat_u6_sample": u6_rows[:8],
        "gate": {
            "recover_ge5_or_gather_ge_base_on_u6": gate,
            "recommend_wire": bool(gate and (st.get("delta_mean") or -1) >= -0.05),
        },
        "next": "K-GATHER-WIRE 형GO"
        if gate
        else "GATHER 관측고정 · NEXT=K-ATTACK-SLICE (구간승격)",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print("Vp_mean", payload["Vp_mean_all"])
    for t, s in out_b.items():
        print(t, s)
    print("hybrid", hybrid)
    print("gate", payload["gate"], "->", payload["next"])


if __name__ == "__main__":
    main()
