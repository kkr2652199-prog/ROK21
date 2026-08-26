# -*- coding: utf-8 -*-
"""회차 당첨 형태 지식 — 로또조회 1..(MAX) 회차별 저장.

특징 계산은 본번호 6개만. 보너스는 라벨 칸(채점 2등)만 저장.
타깃 회 당첨 미입력. load/summarize는 as_of=이미 지난 회만.
전체조합 반영 없음. 몰아주기 미접촉. 자동화 시동 아님.
"""
from __future__ import annotations

import json
import math
import random
from collections import Counter
from statistics import mean, pstdev
from typing import Any

from app.lotto4.combinadic import combo_to_no
from app.testlotto.brains.review_brain.rare_slice import tags as rare_tags
from app.testlotto.features.draw_features import (
    ac_value,
    consecutive_pairs,
    ending_digits,
    sorted_nums,
)
from app.testlotto.models import get_lotto_db, init_testlotto_db

# K-REVIEW-DRAW-SHAPE-KB (20260823) — 예측 전 읽기. 롤백: False
REVIEW_SHAPE_KB_READ: bool = True
# K-REVIEW-SHAPE-KB-WIRE (20260826) — 저울(가점). 칼/거절 아님. 라이브 켜기=형 확인.
# 롤백: False
REVIEW_SHAPE_KB_WEIGHT_WIRE: bool = False

TABLE = "testlotto_draw_shape_kb"
_LAST_READ: dict[str, Any] | None = None


def analyze_one(draw: dict, prev: dict | None) -> dict[str, Any]:
    nums = sorted_nums(draw)
    gaps = [nums[i + 1] - nums[i] for i in range(5)]
    d0 = nums[1] - nums[0]
    arith = bool(d0 > 0 and all(nums[i + 1] - nums[i] == d0 for i in range(5)))
    run = 1
    best = 1
    for i in range(1, 6):
        if nums[i] == nums[i - 1] + 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
    odd = sum(1 for n in nums if n % 2 == 1)
    zones = [
        sum(1 for n in nums if 1 <= n <= 15),
        sum(1 for n in nums if 16 <= n <= 30),
        sum(1 for n in nums if 31 <= n <= 45),
    ]
    decades = [0, 0, 0, 0, 0]
    for n in nums:
        decades[min(4, (n - 1) // 10)] += 1
    ends = ending_digits(nums)
    carry: list[int] = []
    if prev:
        prev_set = set(sorted_nums(prev))
        carry = [n for n in nums if n in prev_set]
    tgs = rare_tags(nums)
    feat = {
        "nums": nums,
        "sum": int(sum(nums)),
        "span": int(nums[5] - nums[0]),
        "ac": int(ac_value(nums)),
        "odd": int(odd),
        "even": int(6 - odd),
        "max_run": int(best),
        "consec_pairs": int(consecutive_pairs(nums)),
        "gaps": gaps,
        "gap_min": int(min(gaps)),
        "gap_max": int(max(gaps)),
        "gap_mean": round(sum(gaps) / 5, 4),
        "arith6": arith,
        "zones": zones,
        "decades": decades,
        "decades_hit": int(sum(1 for x in decades if x > 0)),
        "endings": ends,
        "ending_unique": int(len(set(ends))),
        "carry": carry,
        "carry_count": int(len(carry)),
        "high_ge32": int(sum(1 for n in nums if n >= 32)),
        "high_ge40": int(sum(1 for n in nums if n >= 40)),
        "mod3": [sum(1 for n in nums if n % 3 == r) for r in range(3)],
    }
    return {
        "draw_no": int(draw["draw_no"]),
        "draw_date": str(draw.get("draw_date") or ""),
        "nums": nums,
        "bonus": int(draw.get("bonus") or 0),
        "combo_rank_814": int(combo_to_no(nums)),
        "features": feat,
        "tags": tgs,
    }


def _upsert_sql() -> str:
    return f"""
            INSERT INTO {TABLE} (
                draw_no, draw_date, nums_json, bonus, combo_rank_814,
                features_json, tags_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(draw_no) DO UPDATE SET
                draw_date=excluded.draw_date,
                nums_json=excluded.nums_json,
                bonus=excluded.bonus,
                combo_rank_814=excluded.combo_rank_814,
                features_json=excluded.features_json,
                tags_json=excluded.tags_json,
                updated_at=excluded.updated_at
            """


def save_row(row: dict[str, Any], conn: Any | None = None) -> None:
    own = conn is None
    if own:
        init_testlotto_db()
        conn = get_lotto_db()
    try:
        conn.execute(
            _upsert_sql(),
            (
                row["draw_no"],
                row["draw_date"],
                json.dumps(row["nums"], ensure_ascii=False),
                row["bonus"],
                row["combo_rank_814"],
                json.dumps(row["features"], ensure_ascii=False),
                json.dumps(row["tags"], ensure_ascii=False),
            ),
        )
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()


def rebuild(*, lo: int = 1, hi: int | None = None) -> dict[str, Any]:
    """당첨 확정 회만. 예측 생성 없음."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        if hi is None:
            row = conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()
            hi = int(row[0] or 0)
        rows = conn.execute(
            """
            SELECT draw_no, draw_date, num1, num2, num3, num4, num5, num6, bonus
            FROM lotto_draws
            WHERE draw_no BETWEEN ? AND ?
            ORDER BY draw_no
            """,
            (lo, hi),
        ).fetchall()
        ok = fail = 0
        prev = None
        for r in rows:
            d = dict(r)
            try:
                rec = analyze_one(d, prev)
                save_row(rec, conn)
                ok += 1
            except Exception:  # noqa: BLE001
                fail += 1
            prev = d
        conn.commit()
    finally:
        conn.close()
    return {"ok": ok, "fail": fail, "lo": lo, "hi": hi, "n_src": len(rows)}


def load_upto(as_of: int) -> list[dict[str, Any]]:
    """draw_no <= as_of. 타깃 회 미포함이려면 as_of=target-1."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            f"""
            SELECT draw_no, draw_date, nums_json, bonus, combo_rank_814,
                   features_json, tags_json
            FROM {TABLE}
            WHERE draw_no <= ?
            ORDER BY draw_no
            """,
            (int(as_of),),
        ).fetchall()
    finally:
        conn.close()
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["nums"] = json.loads(d.pop("nums_json") or "[]")
        d["features"] = json.loads(d.pop("features_json") or "{}")
        d["tags"] = json.loads(d.pop("tags_json") or "[]")
        out.append(d)
    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    if not n:
        return {"n": 0, "as_of": None}
    tag_c: Counter[str] = Counter()
    odd_c: Counter[int] = Counter()
    run_c: Counter[int] = Counter()
    sums: list[int] = []
    spans: list[int] = []
    acs: list[int] = []
    for r in rows:
        for t in r.get("tags") or []:
            tag_c[str(t)] += 1
        feat = r.get("features") or {}
        odd_c[int(feat.get("odd") or 0)] += 1
        run_c[int(feat.get("max_run") or 1)] += 1
        if feat.get("sum") is not None:
            sums.append(int(feat["sum"]))
        if feat.get("span") is not None:
            spans.append(int(feat["span"]))
        if feat.get("ac") is not None:
            acs.append(int(feat["ac"]))
    return {
        "n": n,
        "as_of": int(rows[-1]["draw_no"]),
        "tag_hist": dict(tag_c),
        "odd_hist": {str(k): odd_c[k] for k in sorted(odd_c)},
        "run_hist": {str(k): run_c[k] for k in sorted(run_c)},
        "sum_mean": round(mean(sums), 4) if sums else None,
        "span_mean": round(mean(spans), 4) if spans else None,
        "ac_mean": round(mean(acs), 4) if acs else None,
        "sum_std": round(pstdev(sums), 4) if len(sums) >= 2 else 0.0,
        "span_std": round(pstdev(spans), 4) if len(spans) >= 2 else 0.0,
        "ac_std": round(pstdev(acs), 4) if len(acs) >= 2 else 0.0,
    }


def summarize_before(draws: list[dict]) -> dict[str, Any]:
    """예측 전 읽기. as_of=draws 마지막 회(타깃 이전)."""
    global _LAST_READ
    if not draws:
        _LAST_READ = {"n": 0, "as_of": None}
        return _LAST_READ
    as_of = int(draws[-1]["draw_no"])
    rows = load_upto(as_of)
    if not rows:
        built: list[dict[str, Any]] = []
        prev = None
        for d in draws:
            built.append(analyze_one(d, prev))
            prev = d
        _LAST_READ = summarize(built)
        return _LAST_READ
    _LAST_READ = summarize(rows)
    return _LAST_READ


def last_read() -> dict[str, Any] | None:
    return _LAST_READ


def six_shape_feat(nums: list[int]) -> dict[str, int]:
    """본번호 6개만. 보너스 금지."""
    s = sorted(int(x) for x in nums)
    if len(s) != 6:
        return {"odd": 0, "max_run": 0, "sum": 0, "span": 0, "ac": 0}
    run = 1
    best = 1
    for i in range(1, 6):
        if s[i] == s[i - 1] + 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return {
        "odd": int(sum(1 for n in s if n % 2 == 1)),
        "max_run": int(best),
        "sum": int(sum(s)),
        "span": int(s[5] - s[0]),
        "ac": int(ac_value(s)),
    }


def _gauss(x: float, mu: float | None, sd: float | None) -> float:
    if mu is None:
        return 1.0
    sig = float(sd or 0.0) or 1.0
    z = abs(float(x) - float(mu)) / sig
    return math.exp(-0.5 * min(z, 4.0) ** 2)


def set_shape_score(nums: list[int], hist: dict[str, Any] | None) -> float:
    """역사 분포에 가까울수록 1에 가깝다. 보너스 미사용. 거절 점수 아님."""
    if not hist or not hist.get("n"):
        return 1.0
    n = int(hist["n"])
    f = six_shape_feat(nums)
    oh = hist.get("odd_hist") or {}
    rh = hist.get("run_hist") or {}
    odd_p = float(oh.get(str(f["odd"]), 0)) / n
    run_p = float(rh.get(str(f["max_run"]), 0)) / n
    g = (
        _gauss(f["sum"], hist.get("sum_mean"), hist.get("sum_std"))
        * _gauss(f["span"], hist.get("span_mean"), hist.get("span_std"))
        * _gauss(f["ac"], hist.get("ac_mean"), hist.get("ac_std"))
    ) ** (1.0 / 3.0)
    raw = math.sqrt(odd_p + 1e-9) * math.sqrt(run_p + 1e-9) * g
    ref_odd = float(oh.get("3", n / 6)) / n
    ref_run = float(rh.get("1", n / 2)) / n
    ref = math.sqrt(ref_odd + 1e-9) * math.sqrt(ref_run + 1e-9)
    return max(0.0, min(1.0, raw / max(ref, 1e-9)))


def keep_set_by_hist(nums: list[int], hist: dict[str, Any] | None) -> bool:
    """저울: 흔한 모양은 거의 통과, 드문 모양은 가끔만 다시 뽑음. 칼 아님.

    3번(rare_slice/tier1)이 이미 극단을 거절한 뒤에만 호출할 것.
    """
    if not REVIEW_SHAPE_KB_WEIGHT_WIRE:
        return True
    if not hist or not hist.get("n"):
        return True
    score = set_shape_score(nums, hist)
    p = 0.45 + 0.55 * score
    return random.random() <= p
