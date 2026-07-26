# -*- coding: utf-8 -*-
"""다음단계: cover6 심층 선별 + 시드(처음에 고르는 장) 후보 A/B.

컨닝금지: 선별은 target 이전 draws·예측 풀만.
cover6은 평가 분리용(운영에서는 모름) — 풀이 풍부할 때 규칙이 얼마나 버티는지 측정.
시드 후보(운영 가능, 오라클 아님):
  - aux: 보조4뇌 합산 (현재 PIN)
  - vote_sum: 세트 번호들의 출현투표 합이 최대인 장
  - conf: DB confidence 최대 장 (있으면)
  - ending_sum: L_ending 점수 합 최대 장
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.models import get_lotto_db, init_testlotto_db  # noqa: E402
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402
from tools.run_meta_hybrid_ending_wf import ending_next_boost, hybrid_ending  # noqa: E402
from tools.run_meta_hybrid_wf import _load_traps, pick_aux_seed  # noqa: E402
from tools.run_meta_vote2_wf import (  # noqa: E402
    _best_single_match,
    _draws_before,
    _hist_freq,
    _load_draws,
    _load_sets_by_draw,
)

OUT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_형계획_세트합집합_메타선별"
    / "cover6_deep_seed_ab.json"
)
OUT_TOOLS = ROOT / "tools" / "_cover6_deep_seed_ab_result.json"


def _vote(sets: list[list[int]]) -> Counter:
    c: Counter = Counter()
    for s in sets:
        c.update(set(int(n) for n in s))
    return c


def _load_conf_sets() -> dict[int, list[tuple[float, list[int]]]]:
    """target -> [(confidence, nums), ...] from lotto_predictions."""
    init_testlotto_db()
    conn = get_lotto_db()
    by: dict[int, list[tuple[float, list[int]]]] = defaultdict(list)
    try:
        for r in conn.execute(
            """
            SELECT target_draw_no, confidence, num1,num2,num3,num4,num5,num6
            FROM lotto_predictions
            WHERE brain_tag IN ('stat','markov','review')
            ORDER BY target_draw_no, id
            """
        ):
            td = int(r["target_draw_no"])
            conf = float(r["confidence"] or 0)
            nums = [int(r["num1"]), int(r["num2"]), int(r["num3"]),
                     int(r["num4"]), int(r["num5"]), int(r["num6"])]
            by[td].append((conf, nums))
    finally:
        conn.close()
    return dict(by)


def pick_vote_sum_seed(sets: list[list[int]]) -> list[int]:
    vote = _vote(sets)
    best, best_sc = None, -1
    for s in sets:
        sc = sum(vote[int(n)] for n in s)
        if sc > best_sc:
            best_sc = sc
            best = sorted(int(x) for x in s)
    return best or []


def pick_ending_sum_seed(sets: list[list[int]], ending: Counter) -> list[int]:
    best, best_sc = None, -1.0
    for s in sets:
        sc = sum(ending.get(int(n), 0) for n in s)
        if sc > best_sc:
            best_sc = sc
            best = sorted(int(x) for x in s)
    return best or []


def pick_hist_sum_seed(sets: list[list[int]], draws_before: list[dict]) -> list[int]:
    hist = _hist_freq(draws_before)
    best, best_sc = None, -1
    for s in sets:
        sc = sum(hist.get(int(n), 0) for n in s)
        if sc > best_sc:
            best_sc = sc
            best = sorted(int(x) for x in s)
    return best or []


def pick_overlap_top_seed(
    sets: list[list[int]], draws_before: list[dict], ending: Counter
) -> list[int]:
    """풀 순위(hist+ending) top12와 겹침이 가장 많은 기존 장."""
    vote = _vote(sets)
    hist = _hist_freq(draws_before)
    pool = list(vote.keys())
    pool.sort(
        key=lambda n: (hist.get(n, 0), ending.get(n, 0), vote[n], -n), reverse=True
    )
    top = set(pool[:12])
    best, best_sc = None, -1
    for s in sets:
        sc = len(set(int(x) for x in s) & top)
        if sc > best_sc:
            best_sc = sc
            best = sorted(int(x) for x in s)
    return best or []


def pick_conf_seed(conf_rows: list[tuple[float, list[int]]], sets: list[list[int]]) -> list[int]:
    if conf_rows:
        conf_rows = sorted(conf_rows, key=lambda x: -x[0])
        return sorted(int(x) for x in conf_rows[0][1])
    return pick_vote_sum_seed(sets)


def assemble_pool_rank(
    sets: list[list[int]],
    draws_before: list[dict],
    ending: Counter,
    rule: str,
) -> list[int]:
    vote = _vote(sets)
    hist = _hist_freq(draws_before)
    pool = list(vote.keys())

    def key(n: int) -> tuple:
        if rule == "ending_vote_hist":
            return (ending.get(n, 0), vote[n], hist.get(n, 0), -n)
        if rule == "vote_ending_hist":
            return (vote[n], ending.get(n, 0), hist.get(n, 0), -n)
        if rule == "hist_ending":
            return (hist.get(n, 0), ending.get(n, 0), vote[n], -n)
        if rule == "cooccur_greedy":
            return (vote[n], ending.get(n, 0), -n)
        # hist_only
        return (hist.get(n, 0), vote[n], -n)

    if rule != "cooccur_greedy":
        return sorted(sorted(pool, key=key, reverse=True)[:6])

    # greedy: pick highest vote, then prefer numbers that co-occur in same sets
    remaining = set(pool)
    picked: list[int] = []
    co: dict[int, Counter] = defaultdict(Counter)
    for s in sets:
        ss = [int(x) for x in s]
        for a in ss:
            for b in ss:
                if a != b:
                    co[a][b] += 1
    while len(picked) < 6 and remaining:
        if not picked:
            n = max(remaining, key=lambda x: (vote[x], ending.get(x, 0), -x))
        else:
            n = max(
                remaining,
                key=lambda x: (
                    sum(co[x][p] for p in picked),
                    vote[x],
                    ending.get(x, 0),
                    -x,
                ),
            )
        picked.append(n)
        remaining.discard(n)
    return sorted(picked)


def run() -> dict[str, Any]:
    init_testlotto_db()
    traps = _load_traps()
    all_draws = _load_draws()
    sets_by = _load_sets_by_draw()
    conf_by = _load_conf_sets()

    seed_names = ["aux", "vote_sum", "conf", "ending_sum", "hist_sum", "overlap_top"]
    pool_rules = ["hist_only", "ending_vote_hist", "vote_ending_hist", "hist_ending", "cooccur_greedy"]

    # accumulators: method -> list of matches (all / cover6)
    seed_plain: dict[str, list[dict]] = {n: [] for n in seed_names}
    seed_ending_r1: dict[str, list[dict]] = {n: [] for n in seed_names}
    pool_all: dict[str, list[dict]] = {r: [] for r in pool_rules}

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
        uniq: set[int] = set()
        for s in sets:
            uniq |= set(s)
        cover = len(set(actual) & uniq)
        pool_short = cover < 6
        ending = ending_next_boost(before)

        seeds = {
            "aux": pick_aux_seed(sets, before, td, traps)["nums"],
            "vote_sum": pick_vote_sum_seed(sets),
            "conf": pick_conf_seed(conf_by.get(td) or [], sets),
            "ending_sum": pick_ending_sum_seed(sets, ending),
            "hist_sum": pick_hist_sum_seed(sets, before),
            "overlap_top": pick_overlap_top_seed(sets, before, ending),
        }

        for name, sn in seeds.items():
            sc = score_predicted_set(sn, actual, bonus)["matched_count"]
            seed_plain[name].append(
                {"m": sc, "oracle": oracle, "cover": cover, "short": pool_short}
            )
            hy = hybrid_ending(sn, sets, before, ending, min_vote=2, replace_slots=1)
            hm = score_predicted_set(hy["nums"], actual, bonus)["matched_count"]
            seed_ending_r1[name].append(
                {"m": hm, "oracle": oracle, "cover": cover, "short": pool_short}
            )

        for rule in pool_rules:
            nums = assemble_pool_rank(sets, before, ending, rule)
            sc = score_predicted_set(nums, actual, bonus)["matched_count"]
            pool_all[rule].append(
                {"m": sc, "oracle": oracle, "cover": cover, "short": pool_short}
            )

    def pack(rows: list[dict]) -> dict[str, Any]:
        n = len(rows)
        c6 = [r for r in rows if not r["short"]]
        return {
            "n": n,
            "n_cover6": len(c6),
            "avg_all": round(sum(r["m"] for r in rows) / max(1, n), 4),
            "avg_cover6": round(sum(r["m"] for r in c6) / max(1, len(c6)), 4),
            "avg_oracle_all": round(sum(r["oracle"] for r in rows) / max(1, n), 4),
            "avg_oracle_cover6": round(
                sum(r["oracle"] for r in c6) / max(1, len(c6)), 4
            ),
        }

    seed_plain_s = {k: pack(v) for k, v in seed_plain.items()}
    seed_end_s = {k: pack(v) for k, v in seed_ending_r1.items()}
    pool_s = {k: pack(v) for k, v in pool_all.items()}

    # best seed for all / cover6 under ending_r1
    best_seed_all = max(seed_end_s.items(), key=lambda x: x[1]["avg_all"])
    best_seed_c6 = max(seed_end_s.items(), key=lambda x: x[1]["avg_cover6"])
    best_pool_c6 = max(pool_s.items(), key=lambda x: x[1]["avg_cover6"])
    best_pool_all = max(pool_s.items(), key=lambda x: x[1]["avg_all"])

    aux_all = seed_end_s["aux"]["avg_all"]
    recommend_seed = best_seed_all[0]
    improve = best_seed_all[1]["avg_all"] - aux_all

    return {
        "ok": True,
        "no_peek": True,
        "seed_plain": seed_plain_s,
        "seed_plus_ending_r1": seed_end_s,
        "pool_rank_rules": pool_s,
        "best_seed_ending_r1_all": {
            "name": best_seed_all[0],
            **best_seed_all[1],
            "delta_vs_aux": round(improve, 4),
        },
        "best_seed_ending_r1_cover6": {
            "name": best_seed_c6[0],
            **best_seed_c6[1],
        },
        "best_pool_rule_cover6": {"name": best_pool_c6[0], **best_pool_c6[1]},
        "best_pool_rule_all": {"name": best_pool_all[0], **best_pool_all[1]},
        "recommend": {
            "seed": recommend_seed,
            "adopt_seed_change": improve >= 0.05,  # 의미 있는 개선 임계
            "pool_rule_for_cover6_study": best_pool_c6[0],
            "note_ko": (
                "시드 변경은 improve>=0.05일 때만 자동 채택 권고. "
                "cover6 규칙은 평가분리·연구용(운영 시 cover 모름)."
            ),
        },
    }


def main() -> int:
    result = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_TOOLS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
