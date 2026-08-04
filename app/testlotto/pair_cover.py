# -*- coding: utf-8 -*-
"""저출현쌍 covering — K-MATH-PATTERN-WARRANT W-PAIR-COVERING 축.

as_of 절단: draw < before_draw 만으로 쌍빈도 집계 (컨닝 금지).
WIRE 기본 OFF.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any

PAIR_COVER_WIRE: bool = False
N_COVER = 5
# 기대출현 대비 희소: score = max(0, exp - count) 가중
RARE_TOP_K = 80  # as_of 기준 최저빈도 쌍 풀


def _pair_key(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def load_pair_freq_before(before_draw: int) -> tuple[Counter, float, int]:
    """draw_no < before_draw 쌍 빈도 · 기대값 · n_draws."""
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws
        WHERE draw_no < ? ORDER BY draw_no
        """,
        (int(before_draw),),
    ).fetchall()
    conn.close()
    freq: Counter = Counter()
    n = 0
    for r in rows:
        n += 1
        nums = sorted(int(r[f"num{k}"]) for k in range(1, 7))
        for a, b in combinations(nums, 2):
            freq[_pair_key(a, b)] += 1
    # 기대: n * C(6,2) / C(45,2)
    import math

    exp = (n * math.comb(6, 2) / math.comb(45, 2)) if n else 0.0
    return freq, float(exp), n


def rare_pair_set(freq: Counter, exp: float, *, top_k: int = RARE_TOP_K) -> set[tuple[int, int]]:
    """출현이 기대 이하인 쌍 중 가장 드문 top_k."""
    # 모든 가능 쌍이 freq에 없을 수 있음 → 0회도 희소
    import math

    all_pairs = [_pair_key(a, b) for a, b in combinations(range(1, 46), 2)]
    scored = []
    for p in all_pairs:
        c = int(freq.get(p, 0))
        # 희소도: 기대 대비 부족분
        deficit = exp - c
        scored.append((deficit, -c, p))
    scored.sort(reverse=True)
    return {p for _, __, p in scored[:top_k]}


def set_pair_score(
    nums: list[int],
    freq: Counter,
    exp: float,
    rare: set[tuple[int, int]],
) -> dict[str, Any]:
    ns = sorted(int(x) for x in nums)
    if len(ns) != 6:
        return {"ok": False}
    pairs = [_pair_key(a, b) for a, b in combinations(ns, 2)]
    rare_hits = [p for p in pairs if p in rare]
    # 세트 점수: 희소쌍 개수 + 평균 deficit
    deficits = [max(0.0, exp - float(freq.get(p, 0))) for p in pairs]
    return {
        "ok": True,
        "nums": ns,
        "pairs": pairs,
        "n_rare": len(rare_hits),
        "rare_pairs": rare_hits,
        "mean_deficit": sum(deficits) / len(deficits) if deficits else 0.0,
        "score": len(rare_hits) * 1.5 + (sum(deficits) / len(deficits) if deficits else 0.0),
    }


def select_pair_cover(
    candidates: list[dict],
    before_draw: int,
    *,
    n_sets: int = N_COVER,
    top_k: int = RARE_TOP_K,
    freq: Counter | None = None,
    exp: float | None = None,
    n_hist: int | None = None,
) -> list[dict]:
    if freq is None or exp is None or n_hist is None:
        freq, exp, n_hist = load_pair_freq_before(before_draw)
    rare = rare_pair_set(freq, exp, top_k=top_k)

    scored: list[tuple[float, tuple[int, ...], dict, dict]] = []
    for c in candidates:
        nums = [int(x) for x in c.get("nums") or []]
        st = set_pair_score(nums, freq, exp, rare)
        if not st.get("ok"):
            continue
        scored.append((float(st["score"]), tuple(st["nums"]), c, st))
    scored.sort(key=lambda x: (-x[0], x[1]))

    picked: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    covered_rare: set[tuple[int, int]] = set()

    pool = list(scored)
    while pool and len(picked) < n_sets:
        best_i = None
        best_val = None
        for i, (sc, nums, c, st) in enumerate(pool):
            if nums in seen:
                continue
            new_rare = [p for p in st["rare_pairs"] if p not in covered_rare]
            val = (len(new_rare) * 2.0 + 0.5 * sc, -i)
            if best_val is None or val > best_val:
                best_val = val
                best_i = i
        if best_i is None:
            break
        sc, nums, c, st = pool.pop(best_i)
        seen.add(nums)
        for p in st["rare_pairs"]:
            covered_rare.add(p)
        entry = dict(c)
        entry["nums"] = list(nums)
        entry["assemble"] = "pair_cover_v1"
        entry["set_no"] = len(picked) + 1
        entry["repack_rank"] = entry["set_no"]
        entry["pred_set_no"] = entry["set_no"]
        entry["pair_cover"] = {
            "n_rare": st["n_rare"],
            "mean_deficit": round(st["mean_deficit"], 4),
            "score": round(st["score"], 4),
            "n_hist": n_hist,
            "exp_pair": round(exp, 4),
            "rare_top_k": top_k,
        }
        picked.append(entry)
    return picked
