# -*- coding: utf-8 -*-
"""다음단계: L_ending(끝자리 유사과거)을 하이브리드에 결합한 WF.

PIN 유지: 시드=보조4뇌 합산 최고.
변경: 교체/순위 키에 L_ending past_next 빈도 가중 (컨닝금지: next < target).

변형:
  A) seed + ending으로 교체순위 (replace 0/1/2)
  B) seed 선정 시 aux + ending세트점수 혼합 (핀 시드 철학 유지·KEEP렌즈 결합)
  C) 시드 없이 풀에서 vote+ending top6 (비교용)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402
from tools.run_meta_hybrid_wf import (  # noqa: E402
    _load_traps,
    fast_aux_composite,
    hybrid_from_seed,
    pick_aux_seed,
)
from tools.run_meta_vote2_wf import (  # noqa: E402
    _best_single_match,
    _draws_before,
    _hist_freq,
    _load_draws,
    _load_sets_by_draw,
)
from tools.run_similar_lens_swarm import feats_ending, similar_ending  # noqa: E402

OUT_BENCH = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_형계획_세트합집합_메타선별"
    / "hybrid_ending_wf_summary.json"
)
OUT_TOOLS = ROOT / "tools" / "_meta_hybrid_ending_wf_result.json"


def ending_next_boost(draws_before: list[dict]) -> Counter:
    """직전 회차 끝자리와 비슷한 과거 → 그 다음 회(단 next가 아직 target 전) 번호 빈도."""
    boost: Counter = Counter()
    if len(draws_before) < 2:
        return boost
    prev = sorted_nums(draws_before[-1])
    pat = feats_ending(prev)
    # draw_no -> nums for before
    by_dn = {int(d["draw_no"]): sorted_nums(d) for d in draws_before}
    target_floor = int(draws_before[-1]["draw_no"]) + 1  # anything >= this is "not yet" relative to next after last
    # We need next < actual target. draws_before already excludes target, so next must be in by_dn.
    for dn, nums in by_dn.items():
        if dn == int(draws_before[-1]["draw_no"]):
            continue
        if not similar_ending(pat, feats_ending(nums)):
            continue
        nxt = dn + 1
        if nxt in by_dn:
            boost.update(by_dn[nxt])
    return boost


def pick_seed_aux_ending(
    sets: list[list[int]],
    draws_before: list[dict],
    target: int,
    traps: set[int],
    ending: Counter,
    *,
    aux_w: float = 0.7,
) -> dict[str, Any]:
    """aux + 세트 내 ending 점수 혼합 시드."""
    best_s: list[int] | None = None
    best_score = -1e18
    for s in sets:
        aux = fast_aux_composite(list(s), draws_before, target, traps)
        end_sc = sum(ending.get(int(n), 0) for n in s) / 6.0
        # normalize end roughly
        sc = aux_w * aux + (1.0 - aux_w) * (end_sc / max(1.0, (max(ending.values()) if ending else 1.0)))
        if sc > best_score:
            best_score = sc
            best_s = sorted(int(x) for x in s)
    return {"nums": best_s or [], "score": round(best_score, 4)}


def hybrid_ending(
    seed_nums: list[int],
    sets: list[list[int]],
    draws_before: list[dict],
    ending: Counter,
    *,
    min_vote: int = 2,
    replace_slots: int = 1,
) -> dict[str, Any]:
    """교체 순위를 ending 우선으로."""
    if len(seed_nums) < 6:
        return {"nums": list(seed_nums), "n_replaced": 0}

    vote: Counter = Counter()
    for s in sets:
        vote.update(set(int(n) for n in s))
    hist = _hist_freq(draws_before)

    def cand_key(n: int) -> tuple:
        return (vote[n], ending.get(n, 0), hist.get(n, 0), -n)

    def weak_key(n: int) -> tuple:
        # 약한 슬롯 = vote·ending 낮음
        return (vote[n], ending.get(n, 0), hist.get(n, 0), -n)

    ranked_weak = sorted(seed_nums, key=weak_key)
    to_drop = ranked_weak[: max(0, replace_slots)]
    candidates = [n for n, v in vote.items() if v >= min_vote and n not in seed_nums]
    candidates.sort(key=cand_key, reverse=True)

    picked = [n for n in seed_nums if n not in to_drop]
    n_rep = 0
    for n in candidates:
        if len(picked) >= 6:
            break
        if n in picked:
            continue
        picked.append(n)
        if to_drop:
            to_drop.pop(0)
            n_rep += 1

    if len(picked) < 6:
        for n in seed_nums:
            if n not in picked:
                picked.append(n)
            if len(picked) >= 6:
                break
    return {"nums": sorted(picked[:6]), "n_replaced": n_rep}


def pool_top6_ending(sets: list[list[int]], ending: Counter, draws_before: list[dict]) -> list[int]:
    vote: Counter = Counter()
    for s in sets:
        vote.update(set(int(n) for n in s))
    hist = _hist_freq(draws_before)
    pool = list(vote.keys())
    pool.sort(key=lambda n: (ending.get(n, 0), vote[n], hist.get(n, 0), -n), reverse=True)
    return sorted(pool[:6])


def run() -> dict[str, Any]:
    init_testlotto_db()
    traps = _load_traps()
    all_draws = _load_draws()
    sets_by = _load_sets_by_draw()

    variants = {
        "baseline_aux_r0": [],  # aux seed, no replace
        "ending_r1": [],
        "ending_r2": [],
        "aux_ending_seed_r1": [],
        "pool_ending_top6": [],
    }

    for d in all_draws:
        td = int(d["draw_no"])
        sets = sets_by.get(td) or []
        if len(sets) < 5:
            continue
        before = _draws_before(all_draws, td)
        if len(before) < 3:
            continue
        actual = sorted_nums(d)
        bonus = int(d["bonus"])
        oracle = _best_single_match(sets, actual, bonus)["matched_count"]
        ending = ending_next_boost(before)

        seed = pick_aux_seed(sets, before, td, traps)
        base = hybrid_from_seed(seed["nums"], sets, before, min_vote=2, replace_slots=0)
        e1 = hybrid_ending(seed["nums"], sets, before, ending, min_vote=2, replace_slots=1)
        e2 = hybrid_ending(seed["nums"], sets, before, ending, min_vote=2, replace_slots=2)
        seed2 = pick_seed_aux_ending(sets, before, td, traps, ending, aux_w=0.7)
        ae1 = hybrid_ending(seed2["nums"], sets, before, ending, min_vote=2, replace_slots=1)
        pool6 = pool_top6_ending(sets, ending, before)

        uniq: set[int] = set()
        for s in sets:
            uniq |= set(s)
        cover = len(set(actual) & uniq)

        def row(nums: list[int]) -> dict[str, Any]:
            sc = score_predicted_set(nums, actual, bonus)
            return {
                "draw_no": td,
                "match": sc["matched_count"],
                "oracle": oracle,
                "cover": cover,
                "pool_short": cover < 6,
                "gap_to_oracle": oracle - sc["matched_count"],
            }

        variants["baseline_aux_r0"].append(row(base["nums"]))
        variants["ending_r1"].append(row(e1["nums"]))
        variants["ending_r2"].append(row(e2["nums"]))
        variants["aux_ending_seed_r1"].append(row(ae1["nums"]))
        variants["pool_ending_top6"].append(row(pool6))

    def summarize(rows: list[dict]) -> dict[str, Any]:
        n = len(rows)
        cover_ok = [r for r in rows if not r["pool_short"]]

        def avg(k: str) -> float:
            return round(sum(r[k] for r in rows) / n, 4)

        return {
            "n": n,
            "avg_match": avg("match"),
            "avg_oracle": avg("oracle"),
            "avg_gap_to_oracle": avg("gap_to_oracle"),
            "avg_match_cover6": round(
                sum(r["match"] for r in cover_ok) / max(1, len(cover_ok)), 4
            ),
            "beats_baseline": None,  # filled later
        }

    base_avg = summarize(variants["baseline_aux_r0"])["avg_match"]
    summary_vars = {}
    best_name = None
    best_avg = -1.0
    for name, rows in variants.items():
        s = summarize(rows)
        s["delta_vs_baseline"] = round(s["avg_match"] - base_avg, 4)
        s["beats_baseline"] = s["avg_match"] > base_avg
        # pass-like: better than baseline AND closer to oracle than baseline
        base_gap = summarize(variants["baseline_aux_r0"])["avg_gap_to_oracle"]
        s["closer_than_baseline"] = s["avg_gap_to_oracle"] < base_gap
        summary_vars[name] = s
        if s["avg_match"] > best_avg:
            best_avg = s["avg_match"]
            best_name = name

    # also compare to oracle best single (~2.22)
    payload = {
        "ok": True,
        "no_peek": True,
        "baseline_name": "baseline_aux_r0",
        "best_variant": best_name,
        "variants": summary_vars,
        "improved_over_baseline": [
            k for k, v in summary_vars.items() if v["delta_vs_baseline"] > 0
        ],
        "note": (
            "L_ending=직전 끝자리 유사 과거의 다음회 당첨빈도(target 이전만). "
            "PIN 시드(보조4뇌) 유지 변형 + 혼합시드/풀top6 비교."
        ),
    }
    return payload


def main() -> int:
    result = run()
    OUT_BENCH.parent.mkdir(parents=True, exist_ok=True)
    OUT_BENCH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_TOOLS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("WROTE", OUT_BENCH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
