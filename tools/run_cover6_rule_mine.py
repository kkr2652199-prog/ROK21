# -*- coding: utf-8 -*-
"""P2 cover=6 회차 선별 규칙 마이닝 + WF 재검증 (컨닝 금지).

cover=6인 회차만: 풀 안 당첨 6개의 사후 라벨로
투표수·빈도순위·구조적합 규칙을 탐색하고, target 이전 통계만으로 WF.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import (  # noqa: E402
    odd_even_ratio,
    sorted_nums,
    sum_range,
)
from app.testlotto.models import init_testlotto_db  # noqa: E402
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402
from tools.run_meta_hybrid_wf import (  # noqa: E402
    _load_traps,
    hybrid_assemble,
    pick_aux_seed,
)
from tools.run_meta_vote2_wf import (  # noqa: E402
    _best_single_match,
    _draws_before,
    _hist_freq,
    _load_draws,
    _load_sets_by_draw,
    _similar_past_number_boost,
)

OUT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_형계획_세트합집합_메타선별"
    / "cover6_rule_candidates.json"
)
OUT_TOOLS = ROOT / "tools" / "_cover6_rule_mine_result.json"


def _vote(sets: list[list[int]]) -> Counter:
    c: Counter = Counter()
    for s in sets:
        c.update(set(int(n) for n in s))
    return c


def _struct_ok(nums: list[int], draws_before: list[dict]) -> float:
    """과거 당첨 구조 분포와의 적합 (높을수록 전형적)."""
    if not draws_before:
        return 0.0
    odd, _ = odd_even_ratio(nums)
    s = sum_range(nums)
    odds = Counter()
    sums = Counter()
    for d in draws_before[-200:]:
        an = sorted_nums(d)
        o, _ = odd_even_ratio(an)
        odds[o] += 1
        sums[sum_range(an) // 10] += 1
    return odds.get(odd, 0) / max(1, sum(odds.values())) + sums.get(s // 10, 0) / max(
        1, sum(sums.values())
    )


def rank_pool_numbers(
    sets: list[list[int]], draws_before: list[dict], rule: str
) -> list[int]:
    vote = _vote(sets)
    hist = _hist_freq(draws_before)
    sim = _similar_past_number_boost(draws_before)
    pool = sorted(vote.keys())

    def key(n: int) -> tuple:
        if rule == "vote_hist":
            return (vote[n], hist.get(n, 0), sim.get(n, 0), -n)
        if rule == "vote_sim":
            return (vote[n], sim.get(n, 0), hist.get(n, 0), -n)
        if rule == "sim_hist":
            return (sim.get(n, 0), hist.get(n, 0), vote[n], -n)
        if rule == "hist_only":
            return (hist.get(n, 0), vote[n], -n)
        # vote_only
        return (vote[n], -n)

    return sorted(pool, key=key, reverse=True)


def assemble_top6(ranked: list[int]) -> list[int]:
    return sorted(ranked[:6])


def mine_and_wf() -> dict[str, Any]:
    init_testlotto_db()
    traps = _load_traps()
    all_draws = _load_draws()
    sets_by = _load_sets_by_draw()
    rules = ["vote_hist", "vote_sim", "sim_hist", "hist_only", "vote_only"]

    # diagnostics on cover6: how often winning nums rank in top6 by each rule
    cover6_diag: dict[str, list[float]] = {r: [] for r in rules}
    cover6_diag["hybrid_r2"] = []
    rows: list[dict[str, Any]] = []

    for d in all_draws:
        td = int(d["draw_no"])
        sets = sets_by.get(td) or []
        if len(sets) < 5:
            continue
        before = _draws_before(all_draws, td)
        if not before:
            continue
        actual = sorted_nums(d)
        bonus = int(d["bonus"])
        uniq: set[int] = set()
        for s in sets:
            uniq |= set(s)
        cover = len(set(actual) & uniq)
        if cover < 6:
            continue

        vote = _vote(sets)
        # label features of winning numbers (for candidate report)
        win_votes = [vote[n] for n in actual]
        rule_hits: dict[str, int] = {}
        for rule in rules:
            ranked = rank_pool_numbers(sets, before, rule)
            top6 = set(assemble_top6(ranked))
            hit = len(top6 & set(actual))
            rule_hits[rule] = hit
            cover6_diag[rule].append(hit)

        hy = hybrid_assemble(
            sets, before, td, min_vote=2, replace_slots=2, traps=traps
        )
        hy_hit = score_predicted_set(hy["nums"], actual, bonus)["matched_count"]
        cover6_diag["hybrid_r2"].append(hy_hit)

        # structure fitness of actual (descriptive)
        rows.append(
            {
                "draw_no": td,
                "win_vote_min": min(win_votes),
                "win_vote_mean": round(sum(win_votes) / 6, 3),
                "win_in_vote_ge2": sum(1 for n in actual if vote[n] >= 2),
                "struct_fit": round(_struct_ok(actual, before), 4),
                **{f"hit_{k}": v for k, v in rule_hits.items()},
                "hit_hybrid_r2": hy_hit,
                "oracle_best": _best_single_match(sets, actual, bonus)["matched_count"],
                "seed_match": score_predicted_set(
                    pick_aux_seed(sets, before, td, traps)["nums"], actual, bonus
                )["matched_count"],
            }
        )

    n = len(rows)
    rule_avgs = {
        r: round(sum(cover6_diag[r]) / max(1, len(cover6_diag[r])), 4)
        for r in cover6_diag
    }
    best_rule = max(
        ((r, rule_avgs[r]) for r in rules),
        key=lambda x: x[1],
    )

    # WF on ALL draws with best_rule (not only cover6) for honesty
    all_rows = []
    for d in all_draws:
        td = int(d["draw_no"])
        sets = sets_by.get(td) or []
        if len(sets) < 5:
            continue
        before = _draws_before(all_draws, td)
        if not before:
            continue
        actual = sorted_nums(d)
        bonus = int(d["bonus"])
        ranked = rank_pool_numbers(sets, before, best_rule[0])
        meta = assemble_top6(ranked)
        sc = score_predicted_set(meta, actual, bonus)
        oracle = _best_single_match(sets, actual, bonus)
        uniq = set()
        for s in sets:
            uniq |= set(s)
        cover = len(set(actual) & uniq)
        all_rows.append(
            {
                "draw_no": td,
                "meta_match": sc["matched_count"],
                "oracle_best": oracle["matched_count"],
                "cover": cover,
                "pool_short": cover < 6,
            }
        )

    nn = len(all_rows)
    summary = {
        "ok": True,
        "n_cover6": n,
        "n_all_wf": nn,
        "rule_avg_hit_on_cover6": rule_avgs,
        "best_rule_on_cover6": best_rule[0],
        "best_rule_avg_hit": best_rule[1],
        "avg_win_vote_mean": round(sum(r["win_vote_mean"] for r in rows) / max(1, n), 4),
        "avg_win_in_vote_ge2": round(
            sum(r["win_in_vote_ge2"] for r in rows) / max(1, n), 4
        ),
        "wf_all_avg_meta": round(
            sum(r["meta_match"] for r in all_rows) / max(1, nn), 4
        ),
        "wf_all_avg_oracle": round(
            sum(r["oracle_best"] for r in all_rows) / max(1, nn), 4
        ),
        "wf_cover6_avg_meta": round(
            sum(r["meta_match"] for r in all_rows if not r["pool_short"])
            / max(1, sum(1 for r in all_rows if not r["pool_short"])),
            4,
        ),
        "candidates": [
            {
                "rule": r,
                "avg_hit_cover6": rule_avgs[r],
                "note": "풀 순위에서 top6 조립",
            }
            for r in rules
        ]
        + [
            {
                "rule": "hybrid_r2",
                "avg_hit_cover6": rule_avgs["hybrid_r2"],
                "note": "P1 하이브리드(min_vote=2,replace=2)",
            }
        ],
        "no_peek": True,
    }
    return {"summary": summary, "cover6_rows_sample": rows[:50], "n_cover6_rows": n}


def main() -> int:
    result = mine_and_wf()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result["summary"], ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_TOOLS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
