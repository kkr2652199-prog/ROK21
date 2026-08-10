# -*- coding: utf-8 -*-
"""군중 선호·비선호 신호 — 선호번호뇌 / 금액뇌 공통.

데이터 한계 (정직히):
  공개 DB에는 **조합별 판매수**가 없다. 대신
  · `first_winners`(1등 당첨자 수) = 그 회 당첨조합의 **인기 프록시**
  · 학술적으로 알려진 구조 편향(생일대 1~31 = 선호, 고번호·끝수 0/8/9 = 비선호)

벤치 근거 (보고용):
  · Ziemba et al. / Thaler–Ziemba (JEP): 비인기 번호가 당첨 시 분배 몫↑ → EV↑
  · Chernoff / Lotto 6/49: conscious selection → 균일하지 않은 선택
  · 당첨 **확률**은 안 바뀌고, **당첨금 기대값**만 바뀐다.

컨닝: `draws` = target 이전만 (`_get_draws_before` 결과).
random.choices 라인은 수정하지 않는다 — 가중치 테이블만 섞는다.
"""
from __future__ import annotations

import math
import os
from typing import Any

# 구조 ON
PREFER_WIRE: bool = True   # markov → 선호번호
PRIZE_WIRE: bool = True    # review → 금액뇌

# 군중 신호 vs 구조 사전 혼합 (호환 스칼라 · 기본값)
W_CROWD = 0.70
W_STRUCT = 0.30
# 엔진 가중치에 곱할 때 세기 (1.0 = ±100% 범위로 부드럽게)
BLEND_STRENGTH = 0.55

# K-BRAIN-INDEPENDENCE: 예측 과정 계수 뇌별 분리.
# 공유 허용 = lotto_draws(과거 결과)만. markov↔review 노브 공유 금지.
W_CROWD_BY_BRAIN: dict[str, float] = {"markov": 0.70, "review": 0.70}
W_STRUCT_BY_BRAIN: dict[str, float] = {"markov": 0.30, "review": 0.30}
# review=0.85: K-REVIEW-PRIZE-BLEND-TUNE APPLY (1137~1236·seed3·|Δprize|≥0.01·prefer_iso)
BLEND_STRENGTH_BY_BRAIN: dict[str, float] = {"markov": 0.55, "review": 0.85}


def _env_on(name: str, default: bool) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    if v in ("1", "true", "yes", "on"):
        return True
    return default


def prefer_on() -> bool:
    return _env_on("K_CROWD_PREFER", PREFER_WIRE)


def prize_on() -> bool:
    return _env_on("K_PRIZE_EV", PRIZE_WIRE)


def _nums(d: dict) -> list[int]:
    if d.get("nums"):
        return [int(x) for x in d["nums"]]
    return [int(d[f"num{k}"]) for k in range(1, 7)]


def _normalize(raw: dict[int, float]) -> dict[int, float]:
    vals = [max(0.0, float(raw.get(n, 0.0))) for n in range(1, 46)]
    mean = sum(vals) / 45.0
    if mean <= 1e-12:
        return {n: 1.0 for n in range(1, 46)}
    return {n: max(0.05, vals[n - 1] / mean) for n in range(1, 46)}


def structural_popular_prior() -> dict[int, float]:
    """문헌: 생일·저번호 선호 (1~31, 특히 1~12)."""
    out: dict[int, float] = {}
    for n in range(1, 46):
        w = 1.0
        if n <= 12:
            w = 1.35
        elif n <= 31:
            w = 1.20
        else:
            w = 0.85
        out[n] = w
    return _normalize(out)


def structural_unpopular_prior() -> dict[int, float]:
    """문헌: 고번호·끝수 0/8/9 비선호 → 당첨 시 분배 유리."""
    out: dict[int, float] = {}
    for n in range(1, 46):
        w = 1.0
        if n >= 40:
            w = 1.40
        elif n >= 32:
            w = 1.25
        elif n <= 12:
            w = 0.80
        end = n % 10
        if end in (0, 8, 9):
            w *= 1.15
        out[n] = w
    return _normalize(out)


def crowd_popular_from_draws(draws: list[dict]) -> dict[int, float]:
    """1등 당첨자 수가 많은 회차의 번호를 더 세게 누적.

    w = log1p(first_winners) · (판매액 보정은 약하게)
    first_winners=0(이월) 회차는 스킵.
    """
    acc = {n: 0.0 for n in range(1, 46)}
    used = 0
    for d in draws:
        fw = int(d.get("first_winners") or 0)
        if fw <= 0:
            continue
        sales = float(d.get("total_sales") or 0.0)
        # 판매액이 큰 회에서 당첨자 많음 = 더 강한 인기 신호
        w = math.log1p(fw)
        if sales > 0:
            w *= 1.0 + min(0.25, math.log10(sales) / 20.0)
        for n in _nums(d):
            acc[n] += w
        used += 1
    if used < 30:
        return {n: 1.0 for n in range(1, 46)}
    return _normalize(acc)


def crowd_unpopular_from_draws(draws: list[dict]) -> dict[int, float]:
    """1등 당첨자가 적은 회차의 번호를 더 세게 누적 (독식·고액 몫 프록시).

    w = 1 / sqrt(first_winners)  — 1명일수록 큼
    """
    acc = {n: 0.0 for n in range(1, 46)}
    used = 0
    for d in draws:
        fw = int(d.get("first_winners") or 0)
        if fw <= 0:
            continue
        w = 1.0 / math.sqrt(float(fw))
        for n in _nums(d):
            acc[n] += w
        used += 1
    if used < 30:
        return {n: 1.0 for n in range(1, 46)}
    return _normalize(acc)


def prefer_table(draws: list[dict], *, brain: str = "markov") -> dict[int, float]:
    crowd = crowd_popular_from_draws(draws)
    struct = structural_popular_prior()
    wc = float(W_CROWD_BY_BRAIN.get(brain, W_CROWD))
    ws = float(W_STRUCT_BY_BRAIN.get(brain, W_STRUCT))
    mixed = {n: wc * crowd[n] + ws * struct[n] for n in range(1, 46)}
    return _normalize(mixed)


def prize_table(draws: list[dict], *, brain: str = "review") -> dict[int, float]:
    crowd = crowd_unpopular_from_draws(draws)
    struct = structural_unpopular_prior()
    wc = float(W_CROWD_BY_BRAIN.get(brain, W_CROWD))
    ws = float(W_STRUCT_BY_BRAIN.get(brain, W_STRUCT))
    mixed = {n: wc * crowd[n] + ws * struct[n] for n in range(1, 46)}
    return _normalize(mixed)


def blend_weights(
    base: dict[int, float],
    table: dict[int, float],
    *,
    strength: float | None = None,
    brain: str | None = None,
) -> dict[int, float]:
    """기존 엔진 가중치 × (1 + strength*(table-1)). random.choices 미수정.

    brain 지정 시 BLEND_STRENGTH_BY_BRAIN 사용 (뇌별 독립).
    """
    if strength is None:
        if brain and brain in BLEND_STRENGTH_BY_BRAIN:
            strength = float(BLEND_STRENGTH_BY_BRAIN[brain])
        else:
            strength = float(BLEND_STRENGTH)
    out: dict[int, float] = {}
    for n in range(1, 46):
        b = max(1e-12, float(base.get(n, 0.0)))
        t = float(table.get(n, 1.0))
        out[n] = b * max(0.05, 1.0 + float(strength) * (t - 1.0))
    return out


def set_crowd_score(nums: list[int], table: dict[int, float]) -> tuple[float, list[int]]:
    """세트 평균 신호 + 상위 기여 번호."""
    if not nums:
        return 0.0, []
    scored = sorted(((n, table.get(n, 1.0)) for n in nums), key=lambda x: -x[1])
    avg = sum(v for _, v in scored) / len(scored)
    top = [n for n, v in scored if v >= 1.15][:4]
    return round(avg, 4), top


def annotate_prefer(draws: list[dict], candidates: list[dict]) -> list[dict]:
    if not prefer_on() or not candidates:
        return candidates
    table = prefer_table(draws, brain="markov")
    out = []
    for c in candidates:
        nums = sorted(int(x) for x in c["nums"])
        avg, top = set_crowd_score(nums, table)
        delta = min(4.0, max(-2.0, (avg - 1.0) * 6.0))
        nc = dict(c)
        nc["nums"] = nums
        nc["confidence"] = min(95.0, float(c.get("confidence", 70)) + delta)
        nc["native_confidence"] = nc["confidence"]
        tag = f"선호신호avg{avg}" + (f"|강{top}" if top else "")
        base_r = str(c.get("reasoning", "선호번호"))
        nc["reasoning"] = f"{base_r} [{tag} Δ{delta:.2f}]"
        nc["crowd"] = {"mode": "prefer", "avg": avg, "top": top, "delta": delta}
        out.append(nc)
    return out


def annotate_prize(draws: list[dict], candidates: list[dict]) -> list[dict]:
    if not prize_on() or not candidates:
        return candidates
    table = prize_table(draws, brain="review")
    out = []
    for c in candidates:
        nums = sorted(int(x) for x in c["nums"])
        avg, top = set_crowd_score(nums, table)
        n_hi = sum(1 for n in nums if n >= 32)
        s = sum(nums)
        delta = min(4.0, max(-2.0, (avg - 1.0) * 6.0))
        if n_hi >= 3:
            delta += 0.6
        if s >= 140:
            delta += 0.4
        delta = min(4.0, delta)
        nc = dict(c)
        nc["nums"] = nums
        nc["confidence"] = min(95.0, float(c.get("confidence", 70)) + delta)
        nc["native_confidence"] = nc["confidence"]
        tag = f"금액신호avg{avg}|고번호{n_hi}|합{s}" + (f"|강{top}" if top else "")
        base_r = str(c.get("reasoning", "금액뇌"))
        nc["reasoning"] = f"{base_r} [{tag} Δ{delta:.2f}]"
        nc["crowd"] = {
            "mode": "prize",
            "avg": avg,
            "top": top,
            "n_hi": n_hi,
            "sum": s,
            "delta": round(delta, 3),
        }
        out.append(nc)
    return out


def flags_snapshot() -> dict[str, Any]:
    return {
        "PREFER_WIRE": prefer_on(),
        "PRIZE_WIRE": prize_on(),
        "W_CROWD": W_CROWD,
        "W_STRUCT": W_STRUCT,
        "BLEND_STRENGTH": BLEND_STRENGTH,
        "W_CROWD_BY_BRAIN": dict(W_CROWD_BY_BRAIN),
        "W_STRUCT_BY_BRAIN": dict(W_STRUCT_BY_BRAIN),
        "BLEND_STRENGTH_BY_BRAIN": dict(BLEND_STRENGTH_BY_BRAIN),
        "independence_ko": "공유=lotto_draws만 · 뇌별 예측계수 BY_BRAIN",
        "rollback": "K_CROWD_PREFER=0 · K_PRIZE_EV=0",
        "data_limit_ko": "조합별 판매수 없음 → first_winners 프록시 + 구조 사전",
        "lit": [
            "Thaler & Ziemba JEP 1988 (parimutuel / unpopular numbers)",
            "Chernoff Lotto 6/49 conscious selection",
            "Significance 2012: EV↑ via unpopular combos (P(win) unchanged)",
        ],
    }
