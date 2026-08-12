# -*- coding: utf-8 -*-
"""K-POOL-HIT-LEDGER — 세트별 적중 원장 (LIST_V3 L3).

쓰기: 결과 확정 후 draw_no=N · pool/repack 을 actual[N]으로 채점.
읽기: draw_no < target 만 (no_peek).
역할슬롯 생성은 L4b · 본 모듈은 role 컬럼을 있으면 저장만.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db
from app.testlotto.signal_pool import MC_SEED
from app.testlotto.tier_utils import score_predicted_set

logger = logging.getLogger(__name__)

BRAIN_TAGS = ("stat", "markov", "review")
SCHEMA_VERSION = 1
LEDGER_TABLE = "testlotto_pool_hit_ledger"
SCATTER_TABLE = "testlotto_pool_hit_scatter"


def _draw_actual(conn, draw_no: int) -> tuple[list[int], int] | None:
    row = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=?",
        (int(draw_no),),
    ).fetchone()
    if not row:
        return None
    nums = [int(row[f"num{k}"]) for k in range(1, 7)]
    bonus = int(row["bonus"] or 0)
    return nums, bonus


def _score_set(
    nums: list[int], actual: list[int], bonus: int
) -> dict[str, Any]:
    nums_s = sorted(int(x) for x in nums)
    actual_set = set(actual)
    hit_nums = sorted(n for n in nums_s if n in actual_set)
    miss_nums = sorted(n for n in nums_s if n not in actual_set)
    sc = score_predicted_set(nums_s, actual, bonus)
    return {
        "nums": nums_s,
        "hits": int(sc["matched_count"]),
        "hit_nums": hit_nums,
        "miss_nums": miss_nums,
        "bonus_hit": int(sc["bonus_matched"]),
        "tier_rank": int(sc["tier_rank"] or 0),
    }


def _scatter_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    union: set[int] = set()
    cnt: Counter[int] = Counter()
    sets_with = 0
    max_h = 0
    sum_h = 0
    bonus_sets = 0
    for r in rows:
        h = int(r["hits"])
        sum_h += h
        max_h = max(max_h, h)
        if h >= 1:
            sets_with += 1
        if int(r.get("bonus_hit") or 0):
            bonus_sets += 1
        for n in r.get("hit_nums") or []:
            ni = int(n)
            union.add(ni)
            cnt[ni] += 1
    dup = sorted(n for n, c in cnt.items() if c >= 2)
    return {
        "union_hit_nums": sorted(union),
        "num_set_count": {str(k): int(v) for k, v in sorted(cnt.items())},
        "dup_hit_nums": dup,
        "sets_with_hits": sets_with,
        "max_hits_in_set": max_h,
        "sum_hits": sum_h,
        "bonus_hit_set_count": bonus_sets,
    }


def load_sets_for_draw(draw_no: int) -> dict[str, Any]:
    """pool/repack 소스: 캐시 우선 · 없으면 WF 빌드(캐시 저장)."""
    from app.testlotto.pool_view_cache import get_or_build_pool_view

    payload = get_or_build_pool_view(int(draw_no), force_refresh=False)
    if not payload.get("ok"):
        return {"ok": False, "error": payload.get("error") or "pool_build_failed", "payload": payload}
    return {
        "ok": True,
        "pool_by_brain": payload.get("pool_by_brain") or {},
        "repack_by_brain": payload.get("repack_by_brain") or {},
        "seed": int(payload.get("seed") or MC_SEED),
    }


def write_pool_hit_ledger(
    draw_no: int,
    *,
    include_repack: bool = True,
    note: str = "L3",
) -> dict[str, Any]:
    """결과 확정 회차 draw_no 의 pool(+repack) 원장·scatter 기록.

    no_peek: 이 함수는 actual[draw_no]로 **채점만** 한다. 예측 생성은 target=draw_no
    의 이전 draws만 사용(기존 build_pool_and_repack).
    """
    init_testlotto_db()
    dno = int(draw_no)
    conn = get_lotto_db()
    try:
        actual_pack = _draw_actual(conn, dno)
        if actual_pack is None:
            return {"ok": False, "draw_no": dno, "skipped": "no_draw"}
        actual, bonus = actual_pack
    finally:
        conn.close()

    src = load_sets_for_draw(dno)
    if not src.get("ok"):
        return {"ok": False, "draw_no": dno, "skipped": "no_pool", "error": src.get("error")}

    seed = int(src["seed"])
    rows_out: list[dict[str, Any]] = []
    scatter_out: list[dict[str, Any]] = []

    conn = get_lotto_db()
    try:
        conn.execute(
            f"DELETE FROM {LEDGER_TABLE} WHERE draw_no=?",
            (dno,),
        )
        conn.execute(
            f"DELETE FROM {SCATTER_TABLE} WHERE draw_no=?",
            (dno,),
        )

        for tag in BRAIN_TAGS:
            for kind, by in (
                ("pool", src["pool_by_brain"]),
                ("repack", src["repack_by_brain"] if include_repack else {}),
            ):
                sets = by.get(tag) or []
                kind_rows: list[dict[str, Any]] = []
                for s in sets:
                    nums = [int(x) for x in (s.get("nums") or [])]
                    if len(nums) != 6:
                        continue
                    sc = _score_set(nums, actual, bonus)
                    set_no = int(
                        s.get("set_no")
                        or s.get("pred_set_no")
                        or s.get("repack_rank")
                        or 0
                    )
                    role = s.get("role")
                    role_s = str(role) if role else None
                    row = {
                        "draw_no": dno,
                        "brain_tag": tag,
                        "kind": kind,
                        "set_no": set_no,
                        "nums": sc["nums"],
                        "hits": sc["hits"],
                        "hit_nums": sc["hit_nums"],
                        "miss_nums": sc["miss_nums"],
                        "bonus": bonus,
                        "bonus_hit": sc["bonus_hit"],
                        "tier_rank": sc["tier_rank"],
                        "role": role_s,
                        "seed": seed,
                        "schema_version": SCHEMA_VERSION,
                    }
                    conn.execute(
                        f"""
                        INSERT INTO {LEDGER_TABLE} (
                            draw_no, brain_tag, kind, set_no, nums_json,
                            hits, hit_nums_json, miss_nums_json,
                            bonus, bonus_hit, tier_rank, role, seed,
                            schema_version, note
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            dno,
                            tag,
                            kind,
                            set_no,
                            json.dumps(sc["nums"]),
                            sc["hits"],
                            json.dumps(sc["hit_nums"]),
                            json.dumps(sc["miss_nums"]),
                            bonus,
                            sc["bonus_hit"],
                            sc["tier_rank"],
                            role_s,
                            seed,
                            SCHEMA_VERSION,
                            note,
                        ),
                    )
                    kind_rows.append(row)
                    rows_out.append(row)

                if kind_rows:
                    sca = _scatter_from_rows(kind_rows)
                    scatter_row = {"draw_no": dno, "brain_tag": tag, "kind": kind, **sca}
                    conn.execute(
                        f"""
                        INSERT INTO {SCATTER_TABLE} (
                            draw_no, brain_tag, kind,
                            union_hit_nums_json, num_set_count_json, dup_hit_nums_json,
                            sets_with_hits, max_hits_in_set, sum_hits, bonus_hit_set_count,
                            schema_version
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            dno,
                            tag,
                            kind,
                            json.dumps(sca["union_hit_nums"]),
                            json.dumps(sca["num_set_count"], ensure_ascii=False),
                            json.dumps(sca["dup_hit_nums"]),
                            sca["sets_with_hits"],
                            sca["max_hits_in_set"],
                            sca["sum_hits"],
                            sca["bonus_hit_set_count"],
                            SCHEMA_VERSION,
                        ),
                    )
                    scatter_out.append(scatter_row)

        conn.commit()
    finally:
        conn.close()

    return {
        "ok": True,
        "draw_no": dno,
        "n_ledger": len(rows_out),
        "n_scatter": len(scatter_out),
        "bonus": bonus,
        "actual": actual,
        "seed": seed,
        "schema_version": SCHEMA_VERSION,
    }


def read_ledger_before(
    target_draw_no: int,
    *,
    brain_tag: str | None = None,
    kind: str | None = "pool",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """no_peek 읽기: draw_no < target 만."""
    init_testlotto_db()
    target = int(target_draw_no)
    sql = f"SELECT * FROM {LEDGER_TABLE} WHERE draw_no < ?"
    args: list[Any] = [target]
    if brain_tag:
        sql += " AND brain_tag=?"
        args.append(brain_tag)
    if kind:
        sql += " AND kind=?"
        args.append(kind)
    sql += " ORDER BY draw_no DESC, brain_tag, set_no"
    if limit is not None:
        sql += " LIMIT ?"
        args.append(int(limit))
    conn = get_lotto_db()
    try:
        rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()
    # 방어: 혹시라도 target 이상 섞이면 컷
    return [r for r in rows if int(r["draw_no"]) < target]


def assert_no_peek_read(target_draw_no: int) -> dict[str, Any]:
    """읽기 결과가 draw_no < target 인지 검증."""
    target = int(target_draw_no)
    rows = read_ledger_before(target, kind=None, limit=5000)
    bad = [int(r["draw_no"]) for r in rows if int(r["draw_no"]) >= target]
    return {
        "ok": len(bad) == 0,
        "target": target,
        "n_rows": len(rows),
        "bad_draws": sorted(set(bad)),
    }


def ledger_counts() -> dict[str, int]:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        n_l = conn.execute(f"SELECT COUNT(*) FROM {LEDGER_TABLE}").fetchone()[0]
        n_s = conn.execute(f"SELECT COUNT(*) FROM {SCATTER_TABLE}").fetchone()[0]
        n_d = conn.execute(
            f"SELECT COUNT(DISTINCT draw_no) FROM {LEDGER_TABLE}"
        ).fetchone()[0]
    finally:
        conn.close()
    return {"ledger_rows": int(n_l), "scatter_rows": int(n_s), "draws": int(n_d)}
