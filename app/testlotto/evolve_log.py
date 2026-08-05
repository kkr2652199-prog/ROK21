# -*- coding: utf-8 -*-
"""K-EVOLVE-LOG — 회차×뇌 예측→채점→패턴 로그 (가중 0 · 학습 wire 없음).

Phase1: DB 축적만. apply_feedback / W_* / quota / coordinator 미수정.
as_of = draw_no (해당 회차 채점 기록; 다음 예측 입력으로 쓰일 때는 draw_no 미만만).
"""
from __future__ import annotations

import json
from statistics import mean
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db

BRAIN_TAGS = ("stat", "markov", "review")
EVOLVE_SCHEMA_VERSION = 1
WEIGHT_APPLIED = 0.0  # Phase1 고정


def ensure_evolve_log_table(conn=None) -> None:
    own = conn is None
    if own:
        init_testlotto_db()
        conn = get_lotto_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS testlotto_evolve_log (
            draw_no            INTEGER NOT NULL,
            brain_tag          TEXT NOT NULL,
            as_of              INTEGER NOT NULL,
            schema_version     INTEGER NOT NULL DEFAULT 1,
            weight_applied     REAL NOT NULL DEFAULT 0,
            actual_nums_json   TEXT NOT NULL,
            pool_json          TEXT NOT NULL,
            repack_json        TEXT NOT NULL,
            pool_hits_json     TEXT NOT NULL,
            repack_hits_json   TEXT NOT NULL,
            best_hits          INTEGER NOT NULL DEFAULT 0,
            mean_hits          REAL NOT NULL DEFAULT 0,
            best_set_kind      TEXT,
            best_set_no        INTEGER,
            features_json      TEXT NOT NULL,
            miss_tags_json     TEXT NOT NULL,
            assemble_mode      TEXT,
            note               TEXT DEFAULT '',
            created_at         TEXT DEFAULT (datetime('now','localtime')),
            updated_at         TEXT DEFAULT (datetime('now','localtime')),
            PRIMARY KEY (draw_no, brain_tag)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_evolve_log_draw ON testlotto_evolve_log(draw_no)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_evolve_log_brain ON testlotto_evolve_log(brain_tag)"
    )
    if own:
        conn.commit()
        conn.close()


def _max_run(nums: list[int]) -> int:
    s = sorted(int(x) for x in nums)
    if not s:
        return 0
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def set_features(nums: list[int]) -> dict[str, Any]:
    """1D 구조 특징 (가중 0 로그용 · I3 B1 흡수)."""
    ns = sorted(int(x) for x in nums)
    odd = sum(1 for n in ns if n % 2 == 1)
    low = sum(1 for n in ns if 1 <= n <= 15)
    mid = sum(1 for n in ns if 16 <= n <= 30)
    high = sum(1 for n in ns if 31 <= n <= 45)
    return {
        "sum": sum(ns),
        "odd": odd,
        "even": 6 - odd,
        "zone_low": low,
        "zone_mid": mid,
        "zone_high": high,
        "max_run": _max_run(ns),
        "span": (ns[-1] - ns[0]) if len(ns) == 6 else 0,
    }


def _hits(nums: list[int], actual: set[int]) -> int:
    return len(set(int(x) for x in nums) & actual)


def _score_sets(sets: list[dict], actual: set[int]) -> list[dict]:
    out = []
    for s in sets:
        nums = [int(x) for x in s.get("nums") or []]
        out.append(
            {
                "set_no": int(s.get("set_no") or 0),
                "nums": nums,
                "hits": _hits(nums, actual),
                "kind": s.get("kind") or "unknown",
                "assemble": s.get("assemble"),
                "source": s.get("source"),
                "source_set_no": s.get("source_set_no"),
                "features": set_features(nums) if len(nums) == 6 else {},
            }
        )
    return out


def build_evolve_row(
    draw_no: int,
    brain_tag: str,
    actual_nums: list[int],
    pool: list[dict],
    repack: list[dict],
    *,
    draws_before: list[dict] | None = None,
) -> dict[str, Any]:
    from app.testlotto.brains.coordinator import _detect_missed_patterns

    actual = set(int(x) for x in actual_nums)
    pool_scored = _score_sets(pool, actual)
    repack_scored = _score_sets(repack, actual)
    all_scored = pool_scored + repack_scored
    best_hits = max((x["hits"] for x in repack_scored), default=0)
    # Phase1 지표: 발권(repack) 5장 mean · best는 참고만 (학습 입력 금지 명시)
    mean_hits = mean(x["hits"] for x in repack_scored) if repack_scored else 0.0
    best_row = max(
        repack_scored,
        key=lambda x: (x["hits"], -int(x["set_no"])),
        default=None,
    )
    miss_tags: list[str] = []
    if best_row and best_row["nums"]:
        miss_tags = _detect_missed_patterns(
            best_row["nums"], list(actual_nums), draws_before
        )

    # 뇌 요약 특징 = 발권 5장 feature 평균
    feat_keys = ["sum", "odd", "zone_low", "zone_mid", "zone_high", "max_run", "span"]
    agg: dict[str, Any] = {"weight_applied": WEIGHT_APPLIED, "n_repack": len(repack_scored)}
    for k in feat_keys:
        vals = [float(r["features"].get(k, 0)) for r in repack_scored if r.get("features")]
        agg[f"repack_avg_{k}"] = round(mean(vals), 4) if vals else 0.0
    if best_row:
        agg["best_features"] = best_row.get("features") or {}

    assemble_modes = {
        str(r.get("assemble") or "") for r in repack if r.get("assemble")
    }
    assemble_mode = ",".join(sorted(m for m in assemble_modes if m)) or "unknown"

    base_note = "K-EVOLVE-LOG Phase1 · weight=0 · best는 참고(학습입력 금지)"
    # HIT-WARRANT: 설명 문자열만 부착 · weight_applied 불변 · 발권 미접촉
    try:
        from app.testlotto.hit_warrant import attach_summary_for_evolve_note

        note = attach_summary_for_evolve_note(int(draw_no), base_note)
    except Exception:
        note = base_note

    return {
        "draw_no": int(draw_no),
        "brain_tag": brain_tag,
        "as_of": int(draw_no),
        "schema_version": EVOLVE_SCHEMA_VERSION,
        "weight_applied": WEIGHT_APPLIED,
        "actual_nums": [int(x) for x in actual_nums],
        "pool": pool_scored,
        "repack": repack_scored,
        "best_hits": int(best_hits),
        "mean_hits": round(float(mean_hits), 4),
        "best_set_kind": "repack" if best_row else None,
        "best_set_no": int(best_row["set_no"]) if best_row else None,
        "features": agg,
        "miss_tags": miss_tags,
        "assemble_mode": assemble_mode,
        "note": note,
    }


def upsert_evolve_row(row: dict[str, Any]) -> None:
    ensure_evolve_log_table()
    conn = get_lotto_db()
    try:
        conn.execute(
            """
            INSERT INTO testlotto_evolve_log (
                draw_no, brain_tag, as_of, schema_version, weight_applied,
                actual_nums_json, pool_json, repack_json,
                pool_hits_json, repack_hits_json,
                best_hits, mean_hits, best_set_kind, best_set_no,
                features_json, miss_tags_json, assemble_mode, note,
                updated_at
            ) VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
                datetime('now','localtime')
            )
            ON CONFLICT(draw_no, brain_tag) DO UPDATE SET
                as_of=excluded.as_of,
                schema_version=excluded.schema_version,
                weight_applied=excluded.weight_applied,
                actual_nums_json=excluded.actual_nums_json,
                pool_json=excluded.pool_json,
                repack_json=excluded.repack_json,
                pool_hits_json=excluded.pool_hits_json,
                repack_hits_json=excluded.repack_hits_json,
                best_hits=excluded.best_hits,
                mean_hits=excluded.mean_hits,
                best_set_kind=excluded.best_set_kind,
                best_set_no=excluded.best_set_no,
                features_json=excluded.features_json,
                miss_tags_json=excluded.miss_tags_json,
                assemble_mode=excluded.assemble_mode,
                note=excluded.note,
                updated_at=datetime('now','localtime')
            """,
            (
                row["draw_no"],
                row["brain_tag"],
                row["as_of"],
                row["schema_version"],
                row["weight_applied"],
                json.dumps(row["actual_nums"], ensure_ascii=False),
                json.dumps(
                    [{"set_no": p["set_no"], "nums": p["nums"], "kind": p["kind"]} for p in row["pool"]],
                    ensure_ascii=False,
                ),
                json.dumps(
                    [
                        {
                            "set_no": r["set_no"],
                            "nums": r["nums"],
                            "kind": r["kind"],
                            "assemble": r.get("assemble"),
                            "source": r.get("source"),
                            "source_set_no": r.get("source_set_no"),
                        }
                        for r in row["repack"]
                    ],
                    ensure_ascii=False,
                ),
                json.dumps(
                    [{"set_no": p["set_no"], "hits": p["hits"]} for p in row["pool"]],
                    ensure_ascii=False,
                ),
                json.dumps(
                    [
                        {
                            "set_no": r["set_no"],
                            "hits": r["hits"],
                            "features": r.get("features"),
                        }
                        for r in row["repack"]
                    ],
                    ensure_ascii=False,
                ),
                row["best_hits"],
                row["mean_hits"],
                row.get("best_set_kind"),
                row.get("best_set_no"),
                json.dumps(row["features"], ensure_ascii=False),
                json.dumps(row["miss_tags"], ensure_ascii=False),
                row.get("assemble_mode") or "",
                row.get("note") or "",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_evolve_log(draw_no: int) -> dict[str, Any] | None:
    ensure_evolve_log_table()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT * FROM testlotto_evolve_log WHERE draw_no=? ORDER BY brain_tag",
            (int(draw_no),),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return None
    brains = {}
    for r in rows:
        d = dict(r)
        brains[d["brain_tag"]] = {
            "draw_no": d["draw_no"],
            "brain_tag": d["brain_tag"],
            "as_of": d["as_of"],
            "weight_applied": d["weight_applied"],
            "actual_nums": json.loads(d["actual_nums_json"] or "[]"),
            "pool": json.loads(d["pool_json"] or "[]"),
            "repack": json.loads(d["repack_json"] or "[]"),
            "pool_hits": json.loads(d["pool_hits_json"] or "[]"),
            "repack_hits": json.loads(d["repack_hits_json"] or "[]"),
            "best_hits": d["best_hits"],
            "mean_hits": d["mean_hits"],
            "best_set_no": d["best_set_no"],
            "features": json.loads(d["features_json"] or "{}"),
            "miss_tags": json.loads(d["miss_tags_json"] or "[]"),
            "assemble_mode": d["assemble_mode"],
            "note": d["note"],
            "updated_at": d["updated_at"],
        }
    return {
        "ok": True,
        "draw_no": int(draw_no),
        "weight_applied": WEIGHT_APPLIED,
        "phase": "K-EVOLVE-LOG",
        "brains": brains,
    }


def evolve_summary(draw_start: int, draw_end: int) -> dict[str, Any]:
    ensure_evolve_log_table()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT brain_tag, COUNT(*) AS n,
                   AVG(best_hits) AS avg_best, AVG(mean_hits) AS avg_mean,
                   SUM(CASE WHEN best_hits>=3 THEN 1 ELSE 0 END) AS ge3
            FROM testlotto_evolve_log
            WHERE draw_no BETWEEN ? AND ?
            GROUP BY brain_tag
            """,
            (draw_start, draw_end),
        ).fetchall()
        n_draws = conn.execute(
            "SELECT COUNT(DISTINCT draw_no) FROM testlotto_evolve_log WHERE draw_no BETWEEN ? AND ?",
            (draw_start, draw_end),
        ).fetchone()[0]
    finally:
        conn.close()
    by_brain = {}
    for r in rows:
        d = dict(r)
        n = int(d["n"])
        by_brain[d["brain_tag"]] = {
            "n": n,
            "avg_best_hits": round(float(d["avg_best"] or 0), 4),
            "avg_mean_hits": round(float(d["avg_mean"] or 0), 4),
            "ge3_count": int(d["ge3"] or 0),
            "ge3_rate": round(int(d["ge3"] or 0) / n, 4) if n else 0.0,
        }
    return {
        "ok": True,
        "draw_range": [draw_start, draw_end],
        "n_draws": int(n_draws or 0),
        "weight_applied": WEIGHT_APPLIED,
        "by_brain": by_brain,
    }


def backfill_from_pool_cache(
    draw_start: int,
    draw_end: int,
    *,
    any_schema: bool = False,
) -> dict[str, Any]:
    """pool_view_cache + lotto_draws로 로그 백필 (예측 재실행 없음 · 가중 0).

    any_schema=True: UI schema 핀 무시(확장 백필용). False면 현재 CACHE_SCHEMA만.
    """
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.pool_view_cache import (
        get_cached_pool_view,
        get_cached_pool_view_any_schema,
    )

    ensure_evolve_log_table()
    init_testlotto_db()
    conn = get_lotto_db()
    draw_rows = conn.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6
        FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no
        """,
        (draw_start, draw_end),
    ).fetchall()
    conn.close()

    getter = get_cached_pool_view_any_schema if any_schema else get_cached_pool_view
    ok = 0
    miss_cache = 0
    for r in draw_rows:
        d = dict(r)
        dno = int(d["draw_no"])
        actual = [int(d[f"num{k}"]) for k in range(1, 7)]
        pv = getter(dno)
        if not pv or not pv.get("ok"):
            miss_cache += 1
            continue
        draws_before = _get_draws_before(dno)
        for tag in BRAIN_TAGS:
            pool = pv.get("pool_by_brain", {}).get(tag, [])
            repack = pv.get("repack_by_brain", {}).get(tag, [])
            if not pool or not repack:
                continue
            row = build_evolve_row(
                dno, tag, actual, pool, repack, draws_before=draws_before
            )
            upsert_evolve_row(row)
        ok += 1

    summary = evolve_summary(draw_start, draw_end)
    return {
        "ok": True,
        "filled_draws": ok,
        "missing_cache": miss_cache,
        "summary": summary,
    }


def backfill_expand_wf(
    draw_start: int,
    draw_end: int,
    *,
    seed: int = 42,
    progress_every: int = 50,
) -> dict[str, Any]:
    """캐시 있는 회차 any_schema 백필 + miss는 순차 WF로 evolve_log만 채움.

    pool_view_cache는 miss 구간에 쓰지 않음(UI schema=3/λ와 혼동 방지).
    순차 빌드 중 FEATURE_LAMBDA_WIRE 일시 OFF (O(n²) 버킷스캔·조기희소 회피).
    weight_applied=0 유지.
    """
    import random

    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.pool_view_cache import get_cached_pool_view_any_schema
    from app.testlotto import signal_pool as sp

    ensure_evolve_log_table()
    init_testlotto_db()
    conn = get_lotto_db()
    draw_rows = conn.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6
        FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no
        """,
        (draw_start, draw_end),
    ).fetchall()
    conn.close()

    prev_lam = bool(getattr(sp, "FEATURE_LAMBDA_WIRE", False))
    sp.FEATURE_LAMBDA_WIRE = False
    learner = sp.RollingSignalLearner()
    from_cache = 0
    from_wf = 0
    miss_draw = 0
    try:
        for i, r in enumerate(draw_rows):
            d = dict(r)
            dno = int(d["draw_no"])
            actual_list = [int(d[f"num{k}"]) for k in range(1, 7)]
            actual = set(actual_list)
            draws_before = _get_draws_before(dno)

            pv = get_cached_pool_view_any_schema(dno)
            if pv and pv.get("ok"):
                pool_by = pv.get("pool_by_brain") or {}
                repack_by = pv.get("repack_by_brain") or {}
                # learner 동기: 캐시 pool로 EMA 갱신
                pool_br = {
                    t: [
                        {
                            "nums": s["nums"],
                            "pred_set_no": s.get("set_no"),
                            "set_no": s.get("set_no"),
                            "brain_tag": t,
                        }
                        for s in (pool_by.get(t) or [])
                    ]
                    for t in BRAIN_TAGS
                }
                learner.update_from_pool(pool_br, actual)
                for tag in BRAIN_TAGS:
                    pool = pool_by.get(tag) or []
                    repack = repack_by.get(tag) or []
                    if not pool or not repack:
                        continue
                    row = build_evolve_row(
                        dno, tag, actual_list, pool, repack, draws_before=draws_before
                    )
                    upsert_evolve_row(row)
                from_cache += 1
            else:
                set_learn_as_of(dno)
                draws = draws_before
                if not draws:
                    miss_draw += 1
                    continue
                random.seed(seed)
                pool = sp.expand_pool(draws, dno, seed=seed)
                pool_br = sp._pool_by_brain(pool)
                hint = sp._build_hint(draws, dno)
                num_ema, pos_ema = learner.snapshot()
                repacked = sp.repack_by_brain(
                    pool_br, hint, num_ema, pos_ema, target_draw_no=None
                )
                by_pool: dict[str, list] = {t: [] for t in BRAIN_TAGS}
                for tag in BRAIN_TAGS:
                    sets = sorted(
                        pool_br.get(tag, []),
                        key=lambda x: int(x.get("pred_set_no") or 0),
                    )
                    by_pool[tag] = [
                        {
                            "set_no": int(c.get("pred_set_no") or c.get("set_no") or 1),
                            "nums": [int(x) for x in c["nums"]],
                            "brain_tag": tag,
                            "kind": "pool",
                        }
                        for c in sets
                    ]
                by_repack: dict[str, list] = {t: [] for t in BRAIN_TAGS}
                for c in repacked:
                    tag = str(c["brain_tag"])
                    entry = {
                        "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
                        "nums": [int(x) for x in c["nums"]],
                        "brain_tag": tag,
                        "kind": "repack",
                        "assemble": c.get("assemble") or "baseline_repack",
                    }
                    if c.get("source"):
                        entry["source"] = c["source"]
                        entry["source_set_no"] = c.get("source_set_no")
                    by_repack.setdefault(tag, []).append(entry)

                for tag in BRAIN_TAGS:
                    pool = by_pool.get(tag) or []
                    repack = by_repack.get(tag) or []
                    if not pool or not repack:
                        continue
                    row = build_evolve_row(
                        dno, tag, actual_list, pool, repack, draws_before=draws_before
                    )
                    row["note"] = (
                        "K-EVOLVE-LOG expand WF · weight=0 · cache미저장 · lam OFF"
                    )
                    upsert_evolve_row(row)
                learner.update_from_pool(pool_br, actual)
                from_wf += 1

            if progress_every and (i + 1) % progress_every == 0:
                print(
                    f"  [{i+1}/{len(draw_rows)}] draw={dno} "
                    f"cache={from_cache} wf={from_wf}",
                    flush=True,
                )
    finally:
        sp.FEATURE_LAMBDA_WIRE = prev_lam

    summary = evolve_summary(draw_start, draw_end)
    return {
        "ok": True,
        "filled_from_cache": from_cache,
        "filled_from_wf": from_wf,
        "miss_draw": miss_draw,
        "filled_draws": from_cache + from_wf,
        "summary": summary,
        "feature_lambda_restored": prev_lam,
    }
