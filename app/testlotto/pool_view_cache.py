"""pool-view SQLite 캐시 — walk-forward 계산 1회 저장, 이후 즉시 서빙."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db
from app.testlotto.signal_pool import MC_SEED, build_pool_and_repack

BRAIN_TAGS = ("stat", "markov", "review")
CACHE_SCHEMA_VERSION = 1


def _row_to_brain_payload(pool_json: str, repack_json: str) -> tuple[list[dict], list[dict]]:
    pool = json.loads(pool_json) if pool_json else []
    repack = json.loads(repack_json) if repack_json else []
    return pool, repack


def get_cached_pool_view(draw_no: int) -> dict[str, Any] | None:
    """캐시 hit 시 pool-view 응답 dict, miss 시 None."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT brain, pool_json, repack_json, computed_at, seed
            FROM testlotto_pool_view_cache
            WHERE draw_no = ?
            ORDER BY brain
            """,
            (draw_no,),
        ).fetchall()
    finally:
        conn.close()

    if len(rows) != len(BRAIN_TAGS):
        return None

    pool_by_brain: dict[str, list[dict]] = {}
    repack_by_brain: dict[str, list[dict]] = {}
    computed_at = None
    seed = MC_SEED
    for row in rows:
        row = dict(row)
        tag = str(row["brain"])
        if tag not in BRAIN_TAGS:
            return None
        if int(row.get("seed") or MC_SEED) != MC_SEED:
            return None
        pool, repack = _row_to_brain_payload(row["pool_json"], row["repack_json"])
        pool_by_brain[tag] = pool
        repack_by_brain[tag] = repack
        computed_at = row.get("computed_at") or computed_at

    return {
        "ok": True,
        "target_draw_no": draw_no,
        "no_peek": True,
        "pool_sets_per_brain": 10,
        "repack_sets_per_brain": 5,
        "seed": seed,
        "pool_by_brain": pool_by_brain,
        "repack_by_brain": repack_by_brain,
        "cached": True,
        "computed_at": computed_at,
    }


def payload_from_wf_parts(
    draw_no: int,
    pool_by_brain: dict[str, list[dict]],
    repacked: list[dict],
    *,
    seed: int = MC_SEED,
) -> dict[str, Any]:
    """build_pool_and_repack과 동일 pool-view dict (백테스트 WF 중 캐시 저장용)."""
    from app.testlotto.signal_pool import POOL_SETS_PER_BRAIN, REPACK_SETS_PER_BRAIN

    by_brain_pool: dict[str, list[dict]] = {}
    for tag in BRAIN_TAGS:
        sets = sorted(pool_by_brain.get(tag, []), key=lambda x: int(x.get("pred_set_no") or x.get("set_no") or 1))
        by_brain_pool[tag] = [
            {
                "set_no": int(c.get("pred_set_no") or c.get("set_no") or 1),
                "nums": [int(x) for x in c["nums"]],
                "brain_tag": tag,
                "kind": "pool",
            }
            for c in sets
        ]

    by_brain_repack: dict[str, list[dict]] = {t: [] for t in BRAIN_TAGS}
    for c in repacked:
        tag = str(c["brain_tag"])
        if tag not in BRAIN_TAGS:
            continue
        by_brain_repack.setdefault(tag, []).append(
            {
                "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
                "nums": [int(x) for x in c["nums"]],
                "brain_tag": tag,
                "kind": "repack",
            }
        )

    return {
        "ok": True,
        "target_draw_no": draw_no,
        "no_peek": True,
        "pool_sets_per_brain": POOL_SETS_PER_BRAIN,
        "repack_sets_per_brain": REPACK_SETS_PER_BRAIN,
        "seed": seed,
        "pool_by_brain": by_brain_pool,
        "repack_by_brain": by_brain_repack,
    }


def save_pool_view_cache(draw_no: int, payload: dict[str, Any]) -> None:
    """build_pool_and_repack 결과를 뇌별 행으로 저장."""
    init_testlotto_db()
    pool_by = payload.get("pool_by_brain") or {}
    repack_by = payload.get("repack_by_brain") or {}
    seed = int(payload.get("seed") or MC_SEED)
    conn = get_lotto_db()
    try:
        for tag in BRAIN_TAGS:
            conn.execute(
                """
                INSERT INTO testlotto_pool_view_cache
                    (draw_no, brain, pool_json, repack_json, seed, schema_version, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(draw_no, brain) DO UPDATE SET
                    pool_json = excluded.pool_json,
                    repack_json = excluded.repack_json,
                    seed = excluded.seed,
                    schema_version = excluded.schema_version,
                    computed_at = excluded.computed_at
                """,
                (
                    draw_no,
                    tag,
                    json.dumps(pool_by.get(tag, []), ensure_ascii=False),
                    json.dumps(repack_by.get(tag, []), ensure_ascii=False),
                    seed,
                    CACHE_SCHEMA_VERSION,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def get_or_build_pool_view(
    target_draw_no: int,
    *,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """캐시 우선 · miss 시 WF 계산 후 저장."""
    t0 = time.perf_counter()
    if not force_refresh:
        cached = get_cached_pool_view(target_draw_no)
        if cached:
            cached["cache_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            return cached

    built = build_pool_and_repack(target_draw_no)
    if not built.get("ok"):
        built["cached"] = False
        built["cache_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return built

    save_pool_view_cache(target_draw_no, built)
    out = get_cached_pool_view(target_draw_no) or built
    out["cached"] = False
    out["cache_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    out["compute_ms"] = out["cache_ms"]
    return out


def resolve_pool_view_for_ui(
    target_draw_no: int,
    *,
    force_refresh: bool = False,
    allow_compute: bool = False,
) -> dict[str, Any]:
    """UI GET용 — 캐시 hit 즉시 · 백테 DB면 요약 즉시 · 계산은 compute/refresh만.

    K-UI-BT-INSTANT: 브라우즈 GET에서 백테 회차 자동 WF 금지 (회차당 수십 초 hang 제거).
    pool 10+5 상세 계산은 ``compute=1`` / ``refresh=1`` / 「3뇌 예측」만.
    """
    from app.testlotto.backtest_store import get_backtest_summaries_for_draw, is_draw_backtested

    t0 = time.perf_counter()
    if not force_refresh:
        cached = get_cached_pool_view(target_draw_no)
        if cached:
            cached["cache_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            return cached

    # 명시 계산만 무거운 WF 허용
    if force_refresh or allow_compute:
        out = get_or_build_pool_view(target_draw_no, force_refresh=force_refresh)
        if out.get("ok"):
            return out
        if is_draw_backtested(target_draw_no):
            summaries = get_backtest_summaries_for_draw(target_draw_no)
            if summaries:
                return {
                    "ok": False,
                    "backtest_only": True,
                    "target_draw_no": target_draw_no,
                    "backtest_summaries": summaries,
                    "message": "pool 계산 실패 · 백테스트 요약만 표시",
                    "cache_ms": round((time.perf_counter() - t0) * 1000, 1),
                }
        return out

    # 수동 브라우즈: DB에 백테 기록이 있으면 즉시 요약 (자동 WF 없음)
    if is_draw_backtested(target_draw_no):
        summaries = get_backtest_summaries_for_draw(target_draw_no)
        if summaries:
            return {
                "ok": False,
                "backtest_only": True,
                "target_draw_no": target_draw_no,
                "backtest_summaries": summaries,
                "message": "백테스트 DB 저장됨 · 즉시 표시 (pool은 예측 버튼)",
                "cache_ms": round((time.perf_counter() - t0) * 1000, 1),
            }

    return {
        "ok": False,
        "cache_miss": True,
        "target_draw_no": target_draw_no,
        "message": "캐시 없음 — 예측 버튼을 눌러 계산하세요",
    }


def prewarm_pool_view_cache(
    draw_start: int,
    draw_end: int,
    *,
    skip_existing: bool = True,
) -> dict[str, Any]:
    """회차 범위 pool-view 캐시 프리워arm (draw_start..draw_end 포함)."""
    if draw_end < draw_start:
        draw_start, draw_end = draw_end, draw_start
    warmed = 0
    skipped = 0
    errors: list[str] = []
    for dno in range(draw_start, draw_end + 1):
        if skip_existing and get_cached_pool_view(dno):
            skipped += 1
            continue
        try:
            result = get_or_build_pool_view(dno, force_refresh=not skip_existing)
            if result.get("ok"):
                warmed += 1
            else:
                errors.append(f"{dno}: {result.get('error', 'unknown')}")
        except Exception as exc:  # noqa: BLE001 — prewarm batch must continue
            errors.append(f"{dno}: {exc}")
    return {
        "draw_start": draw_start,
        "draw_end": draw_end,
        "warmed": warmed,
        "skipped": skipped,
        "errors": errors[:20],
    }


def latest_draw_no(conn: sqlite3.Connection | None = None) -> int:
    own = conn is None
    if own:
        conn = get_lotto_db()
    try:
        row = conn.execute("SELECT MAX(draw_no) AS m FROM lotto_draws").fetchone()
        return int(row["m"] or 0) if row else 0
    finally:
        if own:
            conn.close()


def clear_pool_view_cache(draw_no: int = 0) -> int:
    """pool-view 캐시 삭제. draw_no>0 이면 해당 회차만, 0 이면 전체."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        if draw_no > 0:
            cur = conn.execute(
                "DELETE FROM testlotto_pool_view_cache WHERE draw_no = ?",
                (draw_no,),
            )
        else:
            cur = conn.execute("DELETE FROM testlotto_pool_view_cache")
        conn.commit()
        return int(cur.rowcount or 0)
    finally:
        conn.close()


def prewarm_visible_range(*, window: int = 30) -> dict[str, Any]:
    """최신 회차 기준 ±window 프리워arm."""
    init_testlotto_db()
    latest = latest_draw_no()
    if latest <= 0:
        return {"warmed": 0, "skipped": 0, "errors": ["no draws"]}
    start = max(1, latest - window)
    return prewarm_pool_view_cache(start, latest + 1, skip_existing=True)
