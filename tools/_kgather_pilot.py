# -*- coding: utf-8 -*-
"""K-GATHER-PILOT — 뇌내 몰아주기 v0 오프라인 시뮬 (READ-ONLY).

기존 5세트 합집합 V에서 비랜덤 그리디 재배치 → gather 5세트 채점.
산출: docs/benchmarks/20260729_KGATHER_pilot.json
"""
from __future__ import annotations

import json
import random
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KGATHER_pilot.json"


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


def pair_counts(sets: list[list[int]]) -> Counter:
    c: Counter = Counter()
    for nums in sets:
        for p in combinations(sorted(nums), 2):
            c[p] += 1
    return c


def gather_v0(base_sets: list[list[int]], *, seed: int) -> list[list[int]]:
    """비랜덤 뼈대: V 합집합에서 '드물게 같이 나온 쌍'을 모으는 그리디 5장.

    - 기존 5장에 이미 자주 같이 나온 쌍은 우선순위↓ (재결합)
    - 자리 합법 · 기존장과 Jaccard 과다 중복 회피
    - random은 동점 깨기용만 (seed 고정) — 번호 균등 샘플 아님
    """
    rng = random.Random(seed)
    bases = [sorted(s) for s in base_sets if len(s) == 6]
    if len(bases) < 3:
        return []
    V = sorted({n for s in bases for n in s})
    if len(V) < 6:
        return []

    existing_pairs = pair_counts(bases)
    # rare pairs among V = appear 0 times together in base → high priority to join
    all_pairs = list(combinations(V, 2))
    all_pairs.sort(key=lambda p: (existing_pairs.get(p, 0), p[0], p[1]))

    base_sets_as_sets = [set(s) for s in bases]
    out: list[list[int]] = []

    for slot in range(5):
        # start from rarest unused-ish pair
        best_combo = None
        best_score = -1e18
        # candidate starts: top rare pairs
        starts = all_pairs[: min(40, len(all_pairs))]
        rng.shuffle(starts)  # tie-break only among rare tier
        for a, b in starts[:25]:
            chosen = {a, b}
            # greedily add numbers maximizing new rare pairs + zone balance
            while len(chosen) < 6:
                cand_scores = []
                for x in V:
                    if x in chosen:
                        continue
                    trial = chosen | {x}
                    # score: sum of rarity of new pairs
                    sc = 0.0
                    for y in chosen:
                        p = tuple(sorted((x, y)))
                        sc += 3.0 - min(3, existing_pairs.get(p, 0))
                    # prefer mid sum
                    ssum = sum(trial)
                    sc -= abs(ssum - 138) * 0.02
                    cand_scores.append((sc, x))
                cand_scores.sort(key=lambda t: (-t[0], t[1]))
                if not cand_scores:
                    break
                chosen.add(cand_scores[0][1])
            combo = sorted(chosen)
            if len(combo) != 6 or not legal_sorted(combo):
                continue
            # diversity vs base and vs already gathered
            div_pen = 0.0
            cs = set(combo)
            for bs in base_sets_as_sets:
                j = jaccard(cs, bs)
                if j >= 0.99:
                    div_pen += 50
                elif j > 0.5:
                    div_pen += (j - 0.5) * 10
            for prev in out:
                j = jaccard(cs, set(prev))
                if j > 0.66:
                    div_pen += 20
            # reward covering rare pairs
            rare = sum(
                1
                for p in combinations(combo, 2)
                if existing_pairs.get(p, 0) == 0
            )
            score = rare * 2.0 - div_pen - abs(sum(combo) - 138) * 0.05
            if score > best_score:
                best_score = score
                best_combo = combo
        if best_combo is None:
            # fallback: take 6 from V by positional spread
            vs = list(V)
            idxs = [0, len(vs) // 5, 2 * len(vs) // 5, 3 * len(vs) // 5, 4 * len(vs) // 5, len(vs) - 1]
            best_combo = sorted({vs[min(i, len(vs) - 1)] for i in idxs})
            while len(best_combo) < 6:
                for x in vs:
                    if x not in best_combo:
                        best_combo.append(x)
                        break
                best_combo = sorted(best_combo)
            if not legal_sorted(best_combo):
                best_combo = sorted(vs[:6])
        out.append(best_combo)
        # lightly mark used pairs so next sets differ
        for p in combinations(best_combo, 2):
            existing_pairs[p] = existing_pairs.get(p, 0) + 2
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
        """
        SELECT draw_no, brain_tag, predicted_sets_json
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN 2 AND 1234
        ORDER BY draw_no
        """
    ).fetchall()
    con.close()

    stats: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    oracle_hits = defaultdict(int)  # union==6 and gather best==6
    union6 = defaultdict(int)
    gather6 = defaultdict(int)
    jacc_samples = defaultdict(list)

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
        gsets = gather_v0(bases, seed=d * 17 + hash(tag) % 1000)
        if not gsets:
            continue
        g_best = max(len(set(g) & act) for g in gsets)
        # jaccard gather vs nearest base
        for g in gsets:
            js = [jaccard(set(g), set(b)) for b in bases]
            jacc_samples[tag].append(min(js) if js else 0)

        stats[tag]["base_best"].append(base_best)
        stats[tag]["gather_best"].append(g_best)
        stats[tag]["union"].append(union_n)
        stats[tag]["delta"].append(g_best - base_best)
        if union_n >= 6:
            union6[tag] += 1
            if g_best >= 6:
                gather6[tag] += 1
                oracle_hits[tag] += 1

    out_brains = {}
    for tag, st in stats.items():
        n = len(st["base_best"])
        out_brains[tag] = {
            "n": n,
            "base_best_mean": round(sum(st["base_best"]) / n, 4),
            "gather_best_mean": round(sum(st["gather_best"]) / n, 4),
            "delta_mean": round(sum(st["delta"]) / n, 4),
            "base_ge4_rate": round(sum(1 for x in st["base_best"] if x >= 4) / n, 4),
            "gather_ge4_rate": round(sum(1 for x in st["gather_best"] if x >= 4) / n, 4),
            "base_ge3_rate": round(sum(1 for x in st["base_best"] if x >= 3) / n, 4),
            "gather_ge3_rate": round(sum(1 for x in st["gather_best"] if x >= 3) / n, 4),
            "gather_ge6_count": sum(1 for x in st["gather_best"] if x >= 6),
            "union_ge6_count": union6[tag],
            "gather_recovered_ge6_from_union6": gather6[tag],
            "recover_rate_when_union6": round(gather6[tag] / union6[tag], 4)
            if union6[tag]
            else None,
            "mean_min_jaccard_vs_base": round(
                sum(jacc_samples[tag]) / len(jacc_samples[tag]), 4
            )
            if jacc_samples[tag]
            else None,
            "improved_rate": round(sum(1 for x in st["delta"] if x > 0) / n, 4),
            "worsened_rate": round(sum(1 for x in st["delta"] if x < 0) / n, 4),
        }

    payload = {
        "id": "K-GATHER-PILOT",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "version": "gather_v0_greedy_rare_pairs",
        "design_ref": "My_Drive_Sync/SUMMARY/K_GATHER_DESIGN.md",
        "brains": out_brains,
        "verdict": {
            "note": "v0 뼈대 시뮬 — WIRE 전 성적 게이트",
            "ok_to_propose_wire": any(
                (out_brains[t]["gather_ge4_rate"] >= out_brains[t]["base_ge4_rate"])
                or (out_brains[t].get("recover_rate_when_union6") or 0) > 0
                for t in out_brains
            ),
        },
        "next": "K-GATHER-WIRE — 형 GO 필요",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    for tag, s in out_brains.items():
        print(tag, s)


if __name__ == "__main__":
    main()
