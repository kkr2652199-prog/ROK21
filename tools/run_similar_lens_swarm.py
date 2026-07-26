# -*- coding: utf-8 -*-
"""P3 유사과거 렌즈 5종 swarm + 렌즈별 WF 리프트 (컨닝 금지).

렌즈: L_struct, L_ending, L_gap, L_zone, L_pair
각 렌즈: 유사과거 → next&lt;target 당첨 빈도 → top6 vs 실제 / vs hist baseline.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.models import get_lotto_db, init_testlotto_db  # noqa: E402

OUT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_형계획_세트합집합_메타선별"
    / "similar_lens_swarm.json"
)


def feats_struct(nums: list[int]) -> dict:
    s = sorted(nums)
    odd = sum(1 for n in s if n % 2)
    high = sum(1 for n in s if n >= 23)
    ac = len({abs(s[j] - s[i]) for i in range(6) for j in range(i + 1, 6)}) - 5
    return {
        "odd_even": f"{odd}:{6 - odd}",
        "high_low": f"{high}:{6 - high}",
        "sum": sum(s),
        "ac": ac,
    }


def similar_struct(a: dict, b: dict) -> bool:
    return (
        a["odd_even"] == b["odd_even"]
        and a["high_low"] == b["high_low"]
        and abs(a["sum"] - b["sum"]) <= 12
        and abs(a["ac"] - b["ac"]) <= 2
    )


def feats_ending(nums: list[int]) -> frozenset:
    return frozenset(n % 10 for n in nums)


def similar_ending(a: frozenset, b: frozenset) -> bool:
    return len(a & b) / max(1, len(a | b)) >= 0.5


def feats_gap(nums: list[int]) -> tuple:
    s = sorted(nums)
    gaps = [s[i + 1] - s[i] for i in range(5)]
    return (round(sum(gaps) / 5), max(gaps))


def similar_gap(a: tuple, b: tuple) -> bool:
    return abs(a[0] - b[0]) <= 2 and abs(a[1] - b[1]) <= 3


def feats_zone(nums: list[int]) -> tuple:
    z1 = sum(1 for n in nums if n <= 15)
    z2 = sum(1 for n in nums if 16 <= n <= 30)
    z3 = sum(1 for n in nums if n >= 31)
    return (z1, z2, z3)


def similar_zone(a: tuple, b: tuple) -> bool:
    return a == b


def feats_pair(nums: list[int]) -> frozenset:
    return frozenset(combinations(sorted(nums), 2))


def similar_pair(a: frozenset, b: frozenset, *, min_overlap: int = 2) -> bool:
    return len(a & b) >= min_overlap


LENSES: list[tuple[str, Callable, Callable]] = [
    ("L_struct", feats_struct, similar_struct),
    ("L_ending", feats_ending, similar_ending),
    ("L_gap", feats_gap, similar_gap),
    ("L_zone", feats_zone, similar_zone),
    ("L_pair", feats_pair, similar_pair),
]


def load_draws() -> list[tuple[int, list[int]]]:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT draw_no, num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
        ).fetchall()
        return [(int(r[0]), [int(x) for x in r[1:7]]) for r in rows]
    finally:
        conn.close()


def past_next_freq(
    draws: list[tuple[int, list[int]]],
    target_idx: int,
    lens_name: str,
    feat_fn: Callable,
    sim_fn: Callable,
) -> Counter:
    """패턴 기준=직전 회차. 유사과거 next 당첨만 (next < target)."""
    if target_idx < 1:
        return Counter()
    prev_nums = draws[target_idx - 1][1]
    pat = feat_fn(prev_nums)
    target_dn = draws[target_idx][0]
    by_dn = {d: n for d, n in draws}
    freq: Counter = Counter()
    for i in range(target_idx):  # only before target
        dn, nums = draws[i]
        if dn == draws[target_idx - 1][0]:
            continue
        try:
            ok = sim_fn(pat, feat_fn(nums))
        except TypeError:
            ok = sim_fn(pat, feat_fn(nums))
        if not ok:
            continue
        nxt = dn + 1
        if nxt < target_dn and nxt in by_dn:
            freq.update(by_dn[nxt])
    return freq


def main() -> int:
    draws = load_draws()
    # evaluate from draw index 50 onward for stable history
    lens_stats: dict[str, dict[str, Any]] = {}
    for name, feat_fn, sim_fn in LENSES:
        overlaps_top6: list[int] = []
        overlaps_top15: list[int] = []
        baseline_top6: list[int] = []
        n_similar: list[int] = []
        for i in range(50, len(draws)):
            td, actual = draws[i]
            freq = past_next_freq(draws, i, name, feat_fn, sim_fn)
            # baseline: hist frequency from draws before target
            hist: Counter = Counter()
            for j in range(i):
                hist.update(draws[j][1])
            top6 = [n for n, _ in freq.most_common(6)]
            top15 = [n for n, _ in freq.most_common(15)]
            base6 = [n for n, _ in hist.most_common(6)]
            overlaps_top6.append(len(set(top6) & set(actual)))
            overlaps_top15.append(len(set(top15) & set(actual)))
            baseline_top6.append(len(set(base6) & set(actual)))
            # count similar pasts (not next)
            prev = draws[i - 1][1]
            pat = feat_fn(prev)
            sim_c = 0
            for j in range(i - 1):
                try:
                    if sim_fn(pat, feat_fn(draws[j][1])):
                        sim_c += 1
                except TypeError:
                    if sim_fn(pat, feat_fn(draws[j][1])):
                        sim_c += 1
            n_similar.append(sim_c)

        n = len(overlaps_top6)
        avg6 = sum(overlaps_top6) / n
        avg_base = sum(baseline_top6) / n
        lift = avg6 - avg_base
        lens_stats[name] = {
            "n": n,
            "avg_overlap_top6": round(avg6, 4),
            "avg_overlap_top15": round(sum(overlaps_top15) / n, 4),
            "avg_baseline_hist_top6": round(avg_base, 4),
            "lift_vs_hist_top6": round(lift, 4),
            "avg_similar_past_count": round(sum(n_similar) / n, 2),
            "keep": lift > 0.02,  # small positive lift threshold
            "verdict": "KEEP" if lift > 0.02 else "REJECT",
        }

    payload = {
        "ok": True,
        "no_peek": True,
        "lenses": lens_stats,
        "kept": [k for k, v in lens_stats.items() if v["keep"]],
        "rejected": [k for k, v in lens_stats.items() if not v["keep"]],
        "note": "리프트=유사과거 next빈도 top6 ∩ actual − 역사빈도 top6 ∩ actual. keep if lift>0.02",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
