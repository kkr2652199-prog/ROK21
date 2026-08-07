# -*- coding: utf-8 -*-
"""과거학습(stat) 파이프라인 — 구조 패치 (튜닝 재개용).

단계:
  1) engine 생성 (기본 dual-window v2 = 과거 장·단윈도우)
  2) aux_hint (기존)
  3) past_learn soft: 미출·윈도우hot · (옵션) 번호→다음 연관
  4) reasoning 태깅 · diversity.pick

ASSOC 전수 NOISE_LIKE → PAST_LEARN_ASSOC_HINT 기본 OFF.
발권 가중 대폭↑ 금지 · random.choices 미사용 · transition_v1 기본 OFF 유지.

롤백:
  K_PAST_LEARN=0          → soft/annotate 최소(이름·method만)
  K_STAT_ENGINE_V2=0      → engine v1
  K_PAST_LEARN_ASSOC=1    → 연관 soft ON (튜닝용)
"""
from __future__ import annotations

import os
from typing import Any

# 구조 ON — 과거학습 뇌 본체
PAST_LEARN_WIRE: bool = True
# dual-window engine (과거 장단 윈도우) — 튜닝 베이스
PAST_LEARN_ENGINE_V2: bool = True
# ASSOC 리프트 soft — 전수 NOISE → 기본 OFF · 튜닝 시 env=1
PAST_LEARN_ASSOC_HINT: bool = False

# soft confidence 상한 (세트당)
SOFT_CONF_CAP = 3.0
SOFT_WEIGHT = 0.12  # 튜닝 노브
ASSOC_SOFT_WEIGHT = 0.05  # ASSOC ON일 때만
WIN_1Y = 52
WIN_2Y = 104
NULL_RATE = 6 / 45


def _env_flag(name: str, default: bool) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    if v in ("1", "true", "yes", "on"):
        return True
    return default


def wire_on() -> bool:
    return _env_flag("K_PAST_LEARN", PAST_LEARN_WIRE)


def use_engine_v2() -> bool:
    if not wire_on():
        return _env_flag("K_STAT_ENGINE_V2", False)
    # PAST_LEARN ON이면 v2 기본 · env로 강제 가능
    if os.environ.get("K_STAT_ENGINE_V2", "").strip() != "":
        return _env_flag("K_STAT_ENGINE_V2", PAST_LEARN_ENGINE_V2)
    return PAST_LEARN_ENGINE_V2


def assoc_hint_on() -> bool:
    return wire_on() and _env_flag("K_PAST_LEARN_ASSOC", PAST_LEARN_ASSOC_HINT)


def soft_weight() -> float:
    v = os.environ.get("K_PAST_LEARN_SOFT_WEIGHT", "").strip()
    if v:
        try:
            return float(v)
        except ValueError:
            pass
    return float(SOFT_WEIGHT)


def soft_conf_cap() -> float:
    v = os.environ.get("K_PAST_LEARN_SOFT_CAP", "").strip()
    if v:
        try:
            return float(v)
        except ValueError:
            pass
    return float(SOFT_CONF_CAP)


def _draw_nums(d: dict) -> list[int]:
    if d.get("nums"):
        return [int(x) for x in d["nums"]]
    return [int(d[f"num{k}"]) for k in range(1, 7)]


def build_past_profiles(draws: list[dict]) -> dict[str, Any]:
    """앵커=마지막 draw 기준 번호별 과거 프로파일 (컨닝: draws만)."""
    if not draws:
        return {"gap": {}, "rate_1y": {}, "rate_2y": {}, "appear": {}}
    latest = int(draws[-1].get("draw_no") or 0)
    appear: dict[int, list[int]] = {n: [] for n in range(1, 46)}
    for d in draws:
        dn = int(d["draw_no"])
        for n in _draw_nums(d):
            appear[n].append(dn)
    gap = {}
    rate_1y = {}
    rate_2y = {}
    lo1 = latest - WIN_1Y + 1
    lo2 = latest - WIN_2Y + 1
    for n in range(1, 46):
        apps = appear[n]
        gap[n] = (latest - apps[-1]) if apps else latest
        c1 = sum(1 for dn in apps if dn >= lo1)
        c2 = sum(1 for dn in apps if dn >= lo2)
        span1 = min(WIN_1Y, len(draws))
        span2 = min(WIN_2Y, len(draws))
        rate_1y[n] = c1 / span1 if span1 else 0.0
        rate_2y[n] = c2 / span2 if span2 else 0.0
    return {"gap": gap, "rate_1y": rate_1y, "rate_2y": rate_2y, "appear": appear, "latest": latest}


def _assoc_next_scores(draws: list[dict], anchor_nums: list[int]) -> dict[int, float]:
    """직전 회 번호들 기준 다음빈도 점수 (간단). ASSOC ON 튜닝용."""
    if len(draws) < 2:
        return {n: 0.0 for n in range(1, 46)}
    # asof = last draw_no as "current problem"; next unknown
    anchor_no = int(draws[-1]["draw_no"])
    score = {n: 0.0 for n in range(1, 46)}
    for x in anchor_nums:
        # appearances of x before last
        hits = []
        for d in draws[:-1]:
            if x in _draw_nums(d):
                hits.append(int(d["draw_no"]))
        ctr: dict[int, int] = {n: 0 for n in range(1, 46)}
        pairs = 0
        by = {int(d["draw_no"]): _draw_nums(d) for d in draws}
        for n in hits:
            n1 = n + 1
            if n1 > anchor_no:
                continue
            nxt = by.get(n1)
            if not nxt:
                continue
            pairs += 1
            for y in nxt:
                ctr[y] += 1
        if pairs <= 0:
            continue
        for y in range(1, 46):
            rate = ctr[y] / pairs
            lift = rate / NULL_RATE if NULL_RATE else 0.0
            score[y] += max(0.0, lift - 1.0)
    # normalize
    mx = max(score.values()) or 1.0
    return {n: score[n] / mx for n in range(1, 46)}


def soft_delta_for_set(
    nums: list[int],
    profile: dict[str, Any],
    assoc_scores: dict[int, float] | None,
) -> tuple[float, list[str]]:
    """confidence soft delta + 태그. 상한 SOFT_CONF_CAP."""
    tags: list[str] = []
    if not wire_on():
        return 0.0, tags
    gap = profile["gap"]
    r1 = profile["rate_1y"]
    overdue = [n for n in nums if gap.get(n, 0) >= 30]
    hot1y = [n for n in nums if r1.get(n, 0) > NULL_RATE * 1.15]
    cold1y = [n for n in nums if r1.get(n, 0) < NULL_RATE * 0.75]
    raw = 0.0
    if overdue:
        tags.append(f"미출30+{overdue}")
        raw += min(1.5, 0.35 * len(overdue))
    if hot1y:
        tags.append(f"1yHot{hot1y}")
        raw += min(1.0, 0.25 * len(hot1y))
    if cold1y:
        tags.append(f"1yCold{cold1y}")
        # mild — cold not always bad
        raw += min(0.5, 0.1 * len(cold1y))
    if assoc_hint_on() and assoc_scores:
        a = sum(assoc_scores.get(n, 0.0) for n in nums) / 6.0
        if a > 0:
            tags.append(f"assocSoft{a:.2f}")
            raw += ASSOC_SOFT_WEIGHT * 10 * a  # scale ~0..0.5
    delta = min(soft_conf_cap(), soft_weight() * 10 * raw / 3.0)
    return round(delta, 3), tags


def apply_to_candidates(
    draws: list[dict],
    candidates: list[dict],
) -> list[dict]:
    """후보에 과거학습 soft·reasoning 부착."""
    if not candidates:
        return candidates
    profile = build_past_profiles(draws)
    prev_nums = _draw_nums(draws[-1]) if draws else []
    assoc_scores = _assoc_next_scores(draws, prev_nums) if assoc_hint_on() else None
    out = []
    for c in candidates:
        nums = sorted(int(x) for x in c["nums"])
        delta, tags = soft_delta_for_set(nums, profile, assoc_scores)
        conf = float(c.get("confidence", 70))
        if wire_on():
            conf = min(95.0, conf + delta)
        reasoning = str(c.get("reasoning", "과거학습"))
        if tags and wire_on():
            reasoning = f"{reasoning} [과거학습:{'|'.join(tags)} Δ{delta}]"
        nc = dict(c)
        nc["nums"] = nums
        nc["confidence"] = conf
        nc["native_confidence"] = conf
        nc["reasoning"] = reasoning
        nc["method"] = "과거학습" if not str(c.get("method", "")).startswith("전이") else c["method"]
        nc["past_learn"] = {
            "wire": wire_on(),
            "engine_v2": use_engine_v2(),
            "assoc": assoc_hint_on(),
            "soft_delta": delta,
            "tags": tags,
        }
        out.append(nc)
    return out


def flags_snapshot() -> dict[str, Any]:
    return {
        "PAST_LEARN_WIRE": wire_on(),
        "PAST_LEARN_ENGINE_V2": use_engine_v2(),
        "PAST_LEARN_ASSOC_HINT": assoc_hint_on(),
        "SOFT_WEIGHT": soft_weight(),
        "SOFT_CONF_CAP": soft_conf_cap(),
        "rollback": "K_PAST_LEARN=0 · K_STAT_ENGINE_V2=0 · K_PAST_LEARN_ASSOC=0",
    }
