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


def load_sets_for_draw(draw_no: int, *, allow_compute: bool = True) -> dict[str, Any]:
    """pool/repack 소스: 캐시 우선.

    allow_compute=False: 캐시 없으면 생성하지 않음 (BT auto_feedback이 창밖 회차를
    get_or_build 해서 pool 캐시가 1건 늘어나던 SOFT 부작용 방지).
    """
    from app.testlotto.pool_view_cache import get_cached_pool_view, get_or_build_pool_view

    dno = int(draw_no)
    payload = get_cached_pool_view(dno)
    if payload is None and allow_compute:
        payload = get_or_build_pool_view(dno, force_refresh=False)
    if not payload or not payload.get("ok"):
        return {
            "ok": False,
            "error": (payload or {}).get("error") or "pool_cache_miss",
            "payload": payload,
        }
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
    allow_compute: bool = True,
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

    src = load_sets_for_draw(dno, allow_compute=allow_compute)
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


def read_scatter_before(
    target_draw_no: int,
    *,
    brain_tag: str | None = None,
    kind: str | None = "pool",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """no_peek 읽기: scatter draw_no < target 만."""
    init_testlotto_db()
    target = int(target_draw_no)
    sql = f"SELECT * FROM {SCATTER_TABLE} WHERE draw_no < ?"
    args: list[Any] = [target]
    if brain_tag:
        sql += " AND brain_tag=?"
        args.append(brain_tag)
    if kind:
        sql += " AND kind=?"
        args.append(kind)
    sql += " ORDER BY draw_no DESC, brain_tag"
    if limit is not None:
        sql += " LIMIT ?"
        args.append(int(limit))
    conn = get_lotto_db()
    try:
        rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()
    return [r for r in rows if int(r["draw_no"]) < target]


def _empty_num() -> dict[int, float]:
    return dict.fromkeys(range(1, 46), 0.0)


def _empty_pos() -> dict[int, float]:
    return dict.fromkeys(range(1, 11), 0.0)


def ledger_signal_tables(
    target_draw_no: int,
    *,
    kind: str = "pool",
    window_draws: int = 50,
    alpha: float = 0.15,
) -> dict[str, Any]:
    """원장 → 뇌별 num/pos 신호표 (draw_no < target · EMA와 동일 credit=hits/6).

    RollingSignalLearner.update_from_pool 과 같은 갱신식.
    scatter num_set_count 는 번호축 소량 보강(중복 출현 신호).
    """
    target = int(target_draw_no)
    peek = assert_no_peek_read(target)
    rows = read_ledger_before(target, kind=kind, limit=None)
    # 오래된 회차부터 적용
    draw_nos = sorted({int(r["draw_no"]) for r in rows})
    if window_draws > 0 and len(draw_nos) > window_draws:
        draw_nos = draw_nos[-int(window_draws) :]
    keep = set(draw_nos)

    num: dict[str, dict[int, float]] = {t: _empty_num() for t in BRAIN_TAGS}
    pos: dict[str, dict[int, float]] = {t: _empty_pos() for t in BRAIN_TAGS}
    n_sets_used = 0
    a = float(alpha)

    by_draw: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        d = int(r["draw_no"])
        if d not in keep:
            continue
        by_draw.setdefault(d, []).append(r)

    for dno in draw_nos:
        for r in by_draw.get(dno, []):
            tag = str(r.get("brain_tag") or "")
            if tag not in num:
                continue
            hits = int(r.get("hits") or 0)
            if hits <= 0:
                continue
            credit = hits / 6.0
            sn = int(r.get("set_no") or 0)
            if 1 <= sn <= 10:
                pos[tag][sn] = (1 - a) * pos[tag].get(sn, 0.0) + a * credit
            hit_nums = r.get("hit_nums_json")
            if isinstance(hit_nums, str):
                try:
                    hit_nums = json.loads(hit_nums)
                except json.JSONDecodeError:
                    hit_nums = []
            for n in hit_nums or []:
                ni = int(n)
                if 1 <= ni <= 45:
                    num[tag][ni] = (1 - a) * num[tag].get(ni, 0.0) + a * credit
            n_sets_used += 1

    # scatter 보강: 최근 회차 union/중복 번호
    sca_rows = read_scatter_before(target, kind=kind, limit=window_draws * 3)
    sca_by_draw = sorted({int(r["draw_no"]) for r in sca_rows})
    if window_draws > 0 and len(sca_by_draw) > window_draws:
        sca_keep = set(sca_by_draw[-int(window_draws) :])
    else:
        sca_keep = set(sca_by_draw)
    n_scatter = 0
    for r in sca_rows:
        if int(r["draw_no"]) not in sca_keep:
            continue
        tag = str(r.get("brain_tag") or "")
        if tag not in num:
            continue
        try:
            cnt = json.loads(r.get("num_set_count_json") or "{}")
        except json.JSONDecodeError:
            cnt = {}
        for ks, cv in cnt.items():
            ni = int(ks)
            c = int(cv)
            if 1 <= ni <= 45 and c >= 1:
                # 세트수 정규화 소량 credit
                boost = min(1.0, c / 10.0) * a * 0.5
                num[tag][ni] = num[tag].get(ni, 0.0) + boost
        n_scatter += 1

    return {
        "ok": True,
        "target": target,
        "kind": kind,
        "n_draws": len(draw_nos),
        "draw_range": [draw_nos[0], draw_nos[-1]] if draw_nos else [],
        "n_sets_with_hits": n_sets_used,
        "n_scatter_rows": n_scatter,
        "alpha": a,
        "window_draws": int(window_draws),
        "no_peek": peek,
        "num": num,
        "pos": pos,
        "ema_solo_exit": bool(draw_nos),  # 원장 회차≥1이면 EMA 단독 탈피
    }


def blend_signal_tables(
    ema_table: dict[str, dict[int, float]],
    led_table: dict[str, dict[int, float]],
    beta: float,
) -> dict[str, dict[int, float]]:
    """(1-β)*EMA + β*ledger. 키 합집합."""
    b = max(0.0, min(1.0, float(beta)))
    out: dict[str, dict[int, float]] = {}
    tags = set(ema_table) | set(led_table)
    for tag in tags:
        e = ema_table.get(tag) or {}
        l = led_table.get(tag) or {}
        keys = set(e) | set(l)
        out[tag] = {
            k: (1.0 - b) * float(e.get(k, 0.0)) + b * float(l.get(k, 0.0)) for k in keys
        }
    return out


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
