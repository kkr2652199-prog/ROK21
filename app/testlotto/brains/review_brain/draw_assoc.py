# -*- coding: utf-8 -*-
"""회차 당첨 6+보너스 번호 연관 — 로또조회 1..지정회 저장.

비슷한 조합 = 당첨 본번호 6개 중 겹침(순서 무관).
보너스는 라벨·별칸(bonus_links)만. 예측 재료로 쓰지 않음.
타깃 회 당첨 미입력. load/summarize는 as_of=이미 지난 회만.
가중치·거절·몰아주기 변경 없음(읽기만). 자동화 시동 아님.
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

from app.lotto4.combinadic import combo_to_no
from app.testlotto.features.draw_features import sorted_nums
from app.testlotto.models import get_lotto_db, init_testlotto_db

# K-REVIEW-DRAW-ASSOC (20260823) — 예측 전 읽기만. 롤백: False
REVIEW_ASSOC_KB_READ: bool = True
# 안 A: 예측 경로에서 bonus_links 사용 금지. 채점 라벨 전용.
PREDICT_USE_BONUS_LINKS: bool = False

TABLE = "testlotto_draw_assoc"
_LAST_READ: dict[str, Any] | None = None


def main_pairs(nums: list[int]) -> list[list[int]]:
    s = sorted(int(n) for n in nums)
    return [[s[i], s[j]] for i in range(len(s)) for j in range(i + 1, len(s))]


def bonus_links(nums: list[int], bonus: int) -> list[list[int]]:
    b = int(bonus or 0)
    s = sorted(int(n) for n in nums)
    if b < 1 or b > 45 or b in s:
        return []
    return [[min(n, b), max(n, b)] for n in s]


def consec_pairs(nums: list[int]) -> list[list[int]]:
    s = sorted(int(n) for n in nums)
    return [[s[i], s[i + 1]] for i in range(len(s) - 1) if s[i + 1] - s[i] == 1]


def analyze_one(draw: dict, prev: dict | None) -> dict[str, Any]:
    nums = sorted_nums(draw)
    bonus = int(draw.get("bonus") or 0)
    carry: list[int] = []
    if prev:
        prev_set = set(sorted_nums(prev))
        carry = [n for n in nums if n in prev_set]
    return {
        "draw_no": int(draw["draw_no"]),
        "draw_date": str(draw.get("draw_date") or ""),
        "nums": nums,
        "bonus": bonus,
        "combo_rank_814": int(combo_to_no(nums)),
        "pairs": main_pairs(nums),
        "bonus_links": bonus_links(nums, bonus),
        "consec_pairs": consec_pairs(nums),
        "carry": carry,
        "similar4": [],
        "similar5": [],
        "share3_count": 0,
    }


def attach_similar(rows: list[dict[str, Any]]) -> None:
    """같은 구간 안 당첨 6개 겹침. 순서 무관. 본번호만(보너스 제외)."""
    items = [(int(r["draw_no"]), frozenset(int(x) for x in r["nums"])) for r in rows]
    by_no = {int(r["draw_no"]): r for r in rows}
    n = len(items)
    for i in range(n):
        ni, si = items[i]
        for j in range(i + 1, n):
            nj, sj = items[j]
            k = len(si & sj)
            if k == 3:
                by_no[ni]["share3_count"] = int(by_no[ni]["share3_count"]) + 1
                by_no[nj]["share3_count"] = int(by_no[nj]["share3_count"]) + 1
            if k >= 4:
                rec = {"draw_no": nj, "share": k, "overlap": sorted(si & sj)}
                rec_i = {"draw_no": ni, "share": k, "overlap": sorted(si & sj)}
                by_no[ni]["similar4"].append(rec)
                by_no[nj]["similar4"].append(rec_i)
            if k >= 5:
                rec = {"draw_no": nj, "share": k, "overlap": sorted(si & sj)}
                rec_i = {"draw_no": ni, "share": k, "overlap": sorted(si & sj)}
                by_no[ni]["similar5"].append(rec)
                by_no[nj]["similar5"].append(rec_i)


def _upsert_sql() -> str:
    return f"""
            INSERT INTO {TABLE} (
                draw_no, draw_date, nums_json, bonus, combo_rank_814,
                pairs_json, bonus_links_json, consec_pairs_json,
                carry_json, similar4_json, similar5_json, share3_count,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(draw_no) DO UPDATE SET
                draw_date=excluded.draw_date,
                nums_json=excluded.nums_json,
                bonus=excluded.bonus,
                combo_rank_814=excluded.combo_rank_814,
                pairs_json=excluded.pairs_json,
                bonus_links_json=excluded.bonus_links_json,
                consec_pairs_json=excluded.consec_pairs_json,
                carry_json=excluded.carry_json,
                similar4_json=excluded.similar4_json,
                similar5_json=excluded.similar5_json,
                share3_count=excluded.share3_count,
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
                json.dumps(row["pairs"], ensure_ascii=False),
                json.dumps(row["bonus_links"], ensure_ascii=False),
                json.dumps(row["consec_pairs"], ensure_ascii=False),
                json.dumps(row["carry"], ensure_ascii=False),
                json.dumps(row["similar4"], ensure_ascii=False),
                json.dumps(row["similar5"], ensure_ascii=False),
                int(row.get("share3_count") or 0),
            ),
        )
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()


def rebuild(*, lo: int = 1, hi: int = 1237) -> dict[str, Any]:
    """당첨 확정 회만. 기본 1–1237(형 구간). 예측 생성 없음."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT draw_no, draw_date, num1, num2, num3, num4, num5, num6, bonus
            FROM lotto_draws
            WHERE draw_no BETWEEN ? AND ?
            ORDER BY draw_no
            """,
            (lo, hi),
        ).fetchall()
        built: list[dict[str, Any]] = []
        prev = None
        fail = 0
        for r in rows:
            d = dict(r)
            try:
                built.append(analyze_one(d, prev))
            except Exception:  # noqa: BLE001
                fail += 1
            prev = d
        attach_similar(built)
        ok = 0
        for rec in built:
            try:
                save_row(rec, conn)
                ok += 1
            except Exception:  # noqa: BLE001
                fail += 1
        conn.commit()
    finally:
        conn.close()
    return {
        "ok": ok,
        "fail": fail,
        "lo": lo,
        "hi": hi,
        "n_src": len(rows),
        "n_similar4_draws": sum(1 for r in built if r["similar4"]),
        "n_similar5_draws": sum(1 for r in built if r["similar5"]),
        "n_similar4_undirected": sum(len(r["similar4"]) for r in built) // 2,
        "n_similar5_undirected": sum(len(r["similar5"]) for r in built) // 2,
    }


def _parse_row(r: Any) -> dict[str, Any]:
    d = dict(r)
    d["nums"] = json.loads(d.pop("nums_json") or "[]")
    d["pairs"] = json.loads(d.pop("pairs_json") or "[]")
    d["bonus_links"] = json.loads(d.pop("bonus_links_json") or "[]")
    d["consec_pairs"] = json.loads(d.pop("consec_pairs_json") or "[]")
    d["carry"] = json.loads(d.pop("carry_json") or "[]")
    d["similar4"] = json.loads(d.pop("similar4_json") or "[]")
    d["similar5"] = json.loads(d.pop("similar5_json") or "[]")
    return d


def load_upto(as_of: int) -> list[dict[str, Any]]:
    """draw_no <= as_of. 타깃 회 미포함이려면 as_of=target-1."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            f"""
            SELECT draw_no, draw_date, nums_json, bonus, combo_rank_814,
                   pairs_json, bonus_links_json, consec_pairs_json,
                   carry_json, similar4_json, similar5_json, share3_count
            FROM {TABLE}
            WHERE draw_no <= ?
            ORDER BY draw_no
            """,
            (int(as_of),),
        ).fetchall()
    finally:
        conn.close()
    return [_parse_row(r) for r in rows]


def _filter_similar(items: list[dict[str, Any]], as_of: int) -> list[dict[str, Any]]:
    out = []
    for it in items or []:
        try:
            if int(it.get("draw_no") or 0) <= as_of:
                out.append(it)
        except (TypeError, ValueError):
            continue
    return out


def summarize(rows: list[dict[str, Any]], *, as_of: int | None = None) -> dict[str, Any]:
    n = len(rows)
    if not n:
        return {"n": 0, "as_of": None}
    if as_of is None:
        as_of = int(rows[-1]["draw_no"])
    pair_c: Counter[tuple[int, int]] = Counter()
    bonus_c: Counter[tuple[int, int]] = Counter()
    n_sim4 = 0
    n_sim5 = 0
    sim4_u = 0
    sim5_u = 0
    consec_n = 0
    carry_n = 0
    share3_sum = 0
    examples5: list[dict[str, Any]] = []
    for r in rows:
        dno = int(r["draw_no"])
        for p in r.get("pairs") or []:
            if len(p) == 2:
                a, b = int(p[0]), int(p[1])
                pair_c[(min(a, b), max(a, b))] += 1
        for p in r.get("bonus_links") or []:
            if len(p) == 2:
                a, b = int(p[0]), int(p[1])
                bonus_c[(min(a, b), max(a, b))] += 1
        s4 = _filter_similar(r.get("similar4") or [], as_of)
        s5 = _filter_similar(r.get("similar5") or [], as_of)
        if s4:
            n_sim4 += 1
            sim4_u += len(s4)
        if s5:
            n_sim5 += 1
            sim5_u += len(s5)
            for it in s5:
                if int(it["draw_no"]) > dno:
                    examples5.append(
                        {
                            "a": dno,
                            "b": int(it["draw_no"]),
                            "share": int(it.get("share") or 0),
                            "overlap": it.get("overlap") or [],
                        }
                    )
        consec_n += len(r.get("consec_pairs") or [])
        carry_n += len(r.get("carry") or [])
        share3_sum += int(r.get("share3_count") or 0)
    top_pairs = [
        {"pair": [a, b], "n": c} for (a, b), c in pair_c.most_common(10)
    ]
    top_bonus = [
        {"pair": [a, b], "n": c} for (a, b), c in bonus_c.most_common(10)
    ]
    return {
        "n": n,
        "as_of": as_of,
        "pair_kinds": len(pair_c),
        "bonus_link_kinds": len(bonus_c),
        "top_pairs": top_pairs,
        "top_bonus_links": top_bonus,
        "n_draws_similar4": n_sim4,
        "n_draws_similar5": n_sim5,
        "n_similar4_undirected": sim4_u // 2,
        "n_similar5_undirected": sim5_u // 2,
        "similar5_examples": examples5[:20],
        "consec_pair_mean": round(consec_n / n, 4),
        "carry_mean": round(carry_n / n, 4),
        "share3_mean": round(share3_sum / n, 4),
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
        attach_similar(built)
        _LAST_READ = summarize(built, as_of=as_of)
        return _LAST_READ
    _LAST_READ = summarize(rows, as_of=as_of)
    return _LAST_READ
