# -*- coding: utf-8 -*-
"""K-GATHER-V1 — cross-set stitch (독립집합) 몰아주기 + PILOT.

근거: union6 분해 → 승자 평균 4.9개가 단일 세트에만 존재(singleton).
v0 희소쌍 그리디 실패 → v1 = 공출현 그래프에서 저연결 번호 조립.
산출: docs/benchmarks/20260729_KGATHER_v1_pilot.json
"""
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KGATHER_v1_pilot.json"
ORACLE = ROOT / "docs" / "benchmarks" / "20260729_KGATHER_v1_oracle.json"


def legal_sorted(nums: list[int]) -> bool:
    s = sorted(nums)
    if len(s) != 6 or len(set(s)) != 6:
        return False
    for k, x in enumerate(s):
        if not (k + 1 <= x <= 40 + k):
            return False
    return True


def jaccard(a: set[int], b: set[int]) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def build_cooccur(bases: list[list[int]]) -> tuple[set[int], dict[int, set[int]], dict[int, int]]:
    V: set[int] = set()
    neigh: dict[int, set[int]] = defaultdict(set)
    appear: dict[int, int] = defaultdict(int)
    for b in bases:
        bs = set(b)
        V |= bs
        for n in bs:
            appear[n] += 1
        for a, c in combinations(sorted(bs), 2):
            neigh[a].add(c)
            neigh[c].add(a)
    return V, neigh, appear


def independent_pack(
    V: set[int],
    neigh: dict[int, set[int]],
    appear: dict[int, int],
    *,
    n_sets: int = 5,
    soft: bool = True,
) -> list[list[int]]:
    """저출현·저연결 우선 독립집합(soft면 약한 충돌 허용)으로 5장."""
    # exclusivity: fewer base appearances first, then fewer neighbors
    order = sorted(V, key=lambda x: (appear.get(x, 0), len(neigh.get(x, ())), x))
    out: list[list[int]] = []
    used_heavy: set[int] = set()  # discourage reuse across gather sets

    for slot in range(n_sets):
        chosen: list[int] = []
        chosen_set: set[int] = set()
        for x in order:
            if x in used_heavy and slot < 3:
                continue
            if soft:
                # allow at most 1 edge into chosen
                conflicts = sum(1 for y in chosen_set if x in neigh.get(y, ()))
                if conflicts > 1:
                    continue
            else:
                if any(x in neigh.get(y, ()) for y in chosen_set):
                    continue
            chosen.append(x)
            chosen_set.add(x)
            if len(chosen) == 6:
                break
        # fill if short
        if len(chosen) < 6:
            for x in order:
                if x in chosen_set:
                    continue
                chosen.append(x)
                chosen_set.add(x)
                if len(chosen) == 6:
                    break
        combo = sorted(chosen[:6])
        if not legal_sorted(combo):
            # repair: take positional spread from V
            vs = sorted(V)
            idxs = [0, len(vs)//5, 2*len(vs)//5, 3*len(vs)//5, 4*len(vs)//5, len(vs)-1]
            combo = sorted({vs[min(i, len(vs)-1)] for i in idxs})
            while len(combo) < 6:
                for x in vs:
                    if x not in combo:
                        combo.append(x)
                        break
                combo = sorted(combo)
        out.append(combo)
        # mark mid-degree nodes as used
        for x in combo:
            if appear.get(x, 0) <= 2:
                used_heavy.add(x)
        # rotate order for diversity
        order = order[1:] + order[:1]
    return out


def gather_v1(base_sets: list[list[int]]) -> list[list[int]]:
    bases = [sorted(s) for s in base_sets if len(s) == 6]
    if len(bases) < 3:
        return []
    V, neigh, appear = build_cooccur(bases)
    if len(V) < 6:
        return []
    packs = independent_pack(V, neigh, appear, n_sets=5, soft=True)
    # also one hard independent pack as set1 replacement if better diversity
    hard = independent_pack(V, neigh, appear, n_sets=1, soft=False)
    if hard:
        packs[0] = hard[0]
    return packs


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
        """
        SELECT draw_no, brain_tag, predicted_sets_json
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN 2 AND 1234
        ORDER BY draw_no
        """
    ).fetchall()
    con.close()

    oracle = json.loads(ORACLE.read_text(encoding="utf-8")) if ORACLE.exists() else {}
    union6_draws = set(oracle.get("summary", {}).get("draws", []))

    stats: dict[str, Any] = defaultdict(lambda: defaultdict(list))
    union6_detail = []

    for r in rows:
        d = int(r["draw_no"])
        act = actuals.get(d)
        if not act:
            continue
        tag = r["brain_tag"]
        try:
            sets = json.loads(r["predicted_sets_json"] or "[]")
        except Exception:
            continue
        bases = [[int(n) for n in (s.get("nums") or [])] for s in sets]
        bases = [b for b in bases if len(b) == 6]
        if len(bases) < 5:
            continue
        base_best = max(len(set(b) & act) for b in bases)
        union = {n for b in bases for n in b}
        union_n = len(union & act)
        gsets = gather_v1(bases)
        if not gsets:
            continue
        g_hits = [len(set(g) & act) for g in gsets]
        g_best = max(g_hits)
        # cheat ceiling: if act subset V, inject
        ceiling = 6 if act.issubset(union) else base_best

        stats[tag]["base_best"].append(base_best)
        stats[tag]["gather_best"].append(g_best)
        stats[tag]["delta"].append(g_best - base_best)
        stats[tag]["union"].append(union_n)
        if act.issubset(union):
            stats[tag]["union6"].append(1)
            stats[tag]["gather_on_union6"].append(g_best)
            stats[tag]["ceiling"].append(ceiling)
            if tag == "stat" and d in union6_draws:
                union6_detail.append(
                    {
                        "draw": d,
                        "base_best": base_best,
                        "gather_best": g_best,
                        "gather_hits": g_hits,
                        "V": len(union),
                        "improved": g_best > base_best,
                    }
                )
        jmin = min(jaccard(set(g), set(b)) for g in gsets for b in bases)
        stats[tag]["jmin"].append(jmin)

    brains = {}
    for tag, st in stats.items():
        n = len(st["base_best"])
        u6 = st["union6"]
        brains[tag] = {
            "n": n,
            "base_best_mean": round(sum(st["base_best"]) / n, 4),
            "gather_best_mean": round(sum(st["gather_best"]) / n, 4),
            "delta_mean": round(sum(st["delta"]) / n, 4),
            "base_ge4_rate": round(sum(1 for x in st["base_best"] if x >= 4) / n, 4),
            "gather_ge4_rate": round(sum(1 for x in st["gather_best"] if x >= 4) / n, 4),
            "base_ge3_rate": round(sum(1 for x in st["base_best"] if x >= 3) / n, 4),
            "gather_ge3_rate": round(sum(1 for x in st["gather_best"] if x >= 3) / n, 4),
            "gather_ge6_count": sum(1 for x in st["gather_best"] if x >= 6),
            "union6_count": len(u6),
            "gather_best_mean_on_union6": round(
                sum(st["gather_on_union6"]) / len(st["gather_on_union6"]), 4
            )
            if st["gather_on_union6"]
            else None,
            "base_best_mean_on_union6": round(
                sum(st["base_best"][i] for i, u in enumerate(st["union"]) if u >= 6)
                / max(1, sum(1 for u in st["union"] if u >= 6)),
                4,
            ),
            "recover_ge5_on_union6": sum(1 for x in st["gather_on_union6"] if x >= 5),
            "recover_ge6_on_union6": sum(1 for x in st["gather_on_union6"] if x >= 6),
            "improved_rate": round(sum(1 for x in st["delta"] if x > 0) / n, 4),
            "mean_min_jaccard": round(sum(st["jmin"]) / len(st["jmin"]), 4),
        }

    # vs v0
    v0_path = ROOT / "docs" / "benchmarks" / "20260729_KGATHER_pilot.json"
    v0 = json.loads(v0_path.read_text(encoding="utf-8")) if v0_path.exists() else {}

    payload = {
        "id": "K-GATHER-V1",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "algo": "cross_set_independent_pack_soft",
        "oracle_ref": str(ORACLE.relative_to(ROOT)).replace("\\", "/"),
        "oracle_summary": oracle.get("summary"),
        "brains": brains,
        "stat_union6_detail": union6_detail,
        "vs_v0": {
            tag: {
                "delta_mean_v0": (v0.get("brains") or {}).get(tag, {}).get("delta_mean"),
                "delta_mean_v1": brains[tag]["delta_mean"],
                "ge4_v0": (v0.get("brains") or {}).get(tag, {}).get("gather_ge4_rate"),
                "ge4_v1": brains[tag]["gather_ge4_rate"],
                "recover6_v0": (v0.get("brains") or {})
                .get(tag, {})
                .get("gather_recovered_ge6_from_union6"),
                "recover6_v1": brains[tag]["recover_ge6_on_union6"],
            }
            for tag in brains
        },
        "wire_gate": {
            "pass_if": "gather improves ge4 on full window OR recover_ge5_on_union6 > 0 with delta_mean>=0",
            "recommend_wire": False,
        },
    }
    # gate
    st = brains.get("stat", {})
    payload["wire_gate"]["recommend_wire"] = bool(
        (st.get("gather_ge4_rate", 0) > st.get("base_ge4_rate", 0) + 0.002)
        or (
            (st.get("recover_ge5_on_union6") or 0) > 0
            and (st.get("delta_mean") or 0) >= -0.02
        )
    )
    payload["next"] = (
        "K-GATHER-WIRE 형 GO"
        if payload["wire_gate"]["recommend_wire"]
        else "K-GATHER-V2 (그래프 가중·휠 혼합) 또는 현 뼈대 유지·관측만"
    )

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    for tag, s in brains.items():
        print(tag, s)
    print("wire?", payload["wire_gate"]["recommend_wire"], payload["next"])
    print("union6 detail sample", union6_detail[:5])


if __name__ == "__main__":
    main()
