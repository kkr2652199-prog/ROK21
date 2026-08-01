"""stat_brain.engine — 통계 예측 생성 엔진."""

from __future__ import annotations

import logging
import random
from math import exp

from app.testlotto.brains.shared import db_facts
from app.testlotto.brains.stat_brain import learn
from app.testlotto.filters import tier1_filter

logger = logging.getLogger(__name__)


def build_weights(draws: list[dict]) -> tuple[
    dict[int, float],
    dict[int, float],
    dict[tuple[int, int], int],
    dict[int, int],
    int,
]:
    """통계 가중치 파이프라인 — predict_statistical._statistical_predict L96-223."""
    if not draws:
        empty_w = {n: 1.0 / 45 for n in range(1, 46)}
        return empty_w, {}, {}, {}, 0

    freq: dict[int, float] = {}
    last_seen: dict[int, int] = {}
    total_draws = len(draws)

    for idx, d in enumerate(draws):
        recency_weight = exp(-0.02 * (total_draws - 1 - idx))
        for k in ["num1", "num2", "num3", "num4", "num5", "num6"]:
            n = d[k]
            freq[n] = freq.get(n, 0.0) + recency_weight
            last_seen[n] = d["draw_no"]

    for n in range(1, 46):
        if n not in freq:
            freq[n] = 0.1
        if n not in last_seen:
            last_seen[n] = 0

    latest_draw_no = draws[-1]["draw_no"] if draws else 0
    gap_map = db_facts.get_gap_map(draws)
    for n in range(1, 46):
        gap = gap_map[n]
        if gap >= 50:
            freq[n] *= 1.3
        elif gap >= 30:
            freq[n] *= 1.15

    recent_5 = draws[-5:] if len(draws) >= 5 else draws
    hot_count: dict[int, int] = {}
    for d in recent_5:
        for k in ["num1", "num2", "num3", "num4", "num5", "num6"]:
            n = d[k]
            hot_count[n] = hot_count.get(n, 0) + 1
    for n, cnt in hot_count.items():
        if cnt >= 2:
            freq[n] *= 1.2

    pair_freq = db_facts.get_pair_freq(draws)
    top_pairs = sorted(pair_freq.items(), key=lambda x: x[1], reverse=True)[:30]
    pair_bonus_nums: dict[int, float] = {}
    for (a, b), cnt in top_pairs:
        bonus = 0.05 * cnt
        pair_bonus_nums[a] = pair_bonus_nums.get(a, 0) + bonus
        pair_bonus_nums[b] = pair_bonus_nums.get(b, 0) + bonus
    for n, bonus in pair_bonus_nums.items():
        freq[n] *= 1 + min(bonus, 0.5)

    total = sum(freq.values())
    weights = {n: freq[n] / total for n in range(1, 46)}

    try:
        from app.testlotto.feedback import get_feedback_summary

        as_of = int(draws[-1]["draw_no"]) if draws else None
        fb = get_feedback_summary(last_n=20, as_of=as_of)
        if fb.get("has_feedback"):
            for trap_n in fb.get("frequent_traps", []):
                if trap_n in weights:
                    weights[trap_n] *= 0.8
            for hit_n in fb.get("frequent_hits", []):
                if hit_n in weights:
                    weights[hit_n] *= 1.15
    except Exception as e:
        logger.debug("피드백 반영 스킵: %s", e)

    weights = learn.apply_learn_boost(weights, draws, last_seen, latest_draw_no)

    return weights, freq, pair_freq, last_seen, latest_draw_no


def generate(draws: list[dict], n_sets: int = 5) -> list[dict]:
    """통계 두뇌: 빈도·구간·홀짝·합계 기반 확률 가중 선택."""
    if not draws:
        return []

    weights, freq, pair_freq, _last_seen, _latest_draw_no = build_weights(draws)

    results = []
    used_combos = set()
    attempts = 0

    while len(results) < n_sets and attempts < 5000:
        attempts += 1
        nums: list[int] = []
        pool = list(range(1, 46))
        w = [weights[n] for n in pool]

        for pick_idx in range(6):
            chosen = random.choices(pool, weights=w, k=1)[0]
            nums.append(chosen)
            idx = pool.index(chosen)
            pool.pop(idx)
            w.pop(idx)

            if pick_idx < 5:
                for p_idx, p_num in enumerate(pool):
                    pair_key = (min(chosen, p_num), max(chosen, p_num))
                    p_count = pair_freq.get(pair_key, 0)
                    if p_count >= 5:
                        boost = 1 + min(p_count * 0.02, 0.4)
                        w[p_idx] *= boost

        nums.sort()

        s = sum(nums)
        odd_count = sum(1 for n in nums if n % 2 == 1)
        ranges_hit = len({(n - 1) // 10 for n in nums})
        consec = 1
        max_consec = 1
        for ci in range(1, len(nums)):
            if nums[ci] == nums[ci - 1] + 1:
                consec += 1
                max_consec = max(max_consec, consec)
            else:
                consec = 1

        if not tier1_filter(nums):
            continue

        key = tuple(nums)
        if key in used_combos:
            continue
        used_combos.add(key)

        confidence = 50.0
        if 100 <= s <= 175:
            confidence += 15
        if 2 <= odd_count <= 4:
            confidence += 10
        if ranges_hit >= 4:
            confidence += 15
        elif ranges_hit >= 3:
            confidence += 8
        avg_freq = sum(freq.get(n, 0) for n in nums) / 6
        max_freq = max(freq.values()) if freq else 1
        confidence += (avg_freq / max_freq) * 10

        confidence = min(round(confidence, 1), 99.0)

        results.append(
            {
                "nums": nums,
                "confidence": confidence,
                "reasoning": f"1티어통계v5(피드백반영), 합계={s}, 홀{odd_count}짝{6 - odd_count}, 구간{ranges_hit}, 연속최대{max_consec}",
            }
        )

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results
