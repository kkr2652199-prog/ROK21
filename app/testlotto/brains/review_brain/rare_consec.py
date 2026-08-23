# -*- coding: utf-8 -*-
"""극소 연속번호 세분화 표 — 순수 엔진 틀(중립).

개별 조합 확률은 1/C(45,6). 여기는 *연속 run 서명*만.
814만 전수 + 당첨 1–1238 실측. 타깃 회 당첨 미입력.
금액뇌 가중·flatten·몰아주기 미접촉(기어 중립).
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from app.testlotto.features.draw_features import sorted_nums

# K-REVIEW-RARE-CONSEC (20260823)
# 읽기만. 패스 기어 OFF. 롤백: REVIEW_CONSEC_KB_READ=False
REVIEW_CONSEC_KB_READ: bool = True
REVIEW_CONSEC_PASS_WIRE: bool = False

C45_6 = 8_145_060
AS_OF_DRAWS = 1238

# 20260823 전수 실측 (itertools.combinations 1..45 C6) · 당첨 1–1238
SPACE: dict[str, int] = {
    "6": 40,
    "5+1": 1560,
    "4+2": 1560,
    "4+1+1": 29640,
    "3+3": 780,
    "3+2+1": 59280,
    "3+1+1+1": 365560,
    "2+2+2": 9880,
    "2+2+1+1": 548340,
    "2+1+1+1+1": 3290040,
    "1+1+1+1+1+1": 3838380,
}

DRAWS: dict[str, int] = {
    "6": 0,
    "5+1": 0,
    "4+2": 1,
    "4+1+1": 5,
    "3+3": 1,
    "3+2+1": 8,
    "3+1+1+1": 52,
    "2+2+2": 6,
    "2+2+1+1": 82,
    "2+1+1+1+1": 484,
    "1+1+1+1+1+1": 599,
}

# 0회이고 공간 얇음. 4+2·3+3은 당첨 1회라 안 넣음.
STEP1_CONSEC: frozenset[str] = frozenset({"6", "5+1"})

_LAST_READ: dict[str, Any] | None = None


def run_parts(nums: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    s = sorted(int(x) for x in nums)
    if len(s) != 6:
        return tuple()
    out: list[int] = []
    cur = 1
    for i in range(1, 6):
        if s[i] == s[i - 1] + 1:
            cur += 1
        else:
            out.append(cur)
            cur = 1
    out.append(cur)
    return tuple(sorted(out, reverse=True))


def sig_key(nums: list[int] | tuple[int, ...]) -> str:
    p = run_parts(nums)
    return "+".join(str(x) for x in p) if p else ""


def is_step1_consec(nums: list[int]) -> bool:
    return sig_key(nums) in STEP1_CONSEC


def class_rows() -> list[dict[str, Any]]:
    rows = []
    for k, c in SPACE.items():
        h = DRAWS.get(k, 0)
        rows.append(
            {
                "sig": k,
                "space": c,
                "p_space": round(c / C45_6, 8),
                "draws": h,
                "p_draws": round(h / AS_OF_DRAWS, 8),
                "null_e": round(AS_OF_DRAWS * c / C45_6, 4),
                "step1": k in STEP1_CONSEC,
            }
        )
    return rows


def summarize() -> dict[str, Any]:
    return {
        "c45_6": C45_6,
        "as_of_draws": AS_OF_DRAWS,
        "step1": sorted(STEP1_CONSEC),
        "gear": "neutral",
        "pass_wire": bool(REVIEW_CONSEC_PASS_WIRE),
        "rows": class_rows(),
    }


def summarize_before(draws: list[dict]) -> dict[str, Any]:
    """예측 전 읽기. as_of=draws 마지막(타깃 이전). 가중 불변."""
    global _LAST_READ
    if not draws:
        _LAST_READ = {"n": 0, "as_of": None, "gear": "neutral"}
        return _LAST_READ
    hist: Counter[str] = Counter()
    for d in draws:
        hist[sig_key(sorted_nums(d))] += 1
    _LAST_READ = {
        "n": len(draws),
        "as_of": int(draws[-1]["draw_no"]),
        "gear": "neutral",
        "pass_wire": bool(REVIEW_CONSEC_PASS_WIRE),
        "sig_hist": dict(hist),
        "step1": sorted(STEP1_CONSEC),
        "classes": {r["sig"]: {"space": r["space"], "draws": r["draws"]} for r in class_rows()},
    }
    return _LAST_READ


def last_read() -> dict[str, Any] | None:
    return _LAST_READ
