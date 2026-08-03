# -*- coding: utf-8 -*-
"""극소 번들 catalog · 당첨 적중 DB 저장."""
from __future__ import annotations

import json
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db
from app.testlotto.rare_bundle import (
    PATTERN_META,
    detect_patterns,
    enumerate_ultra_rare_catalog,
    max_consecutive_run,
    refs_json,
    sorted_nums,
)
from app.lotto4.combinadic import combo_to_no


def save_catalog(entries: list[dict[str, Any]], *, historical: dict[tuple[int, ...], int]) -> int:
    """catalog → testlotto_rare_bundle_catalog."""
    init_testlotto_db()
    conn = get_lotto_db()
    conn.execute("DELETE FROM testlotto_rare_bundle_catalog")
    n = 0
    for e in entries:
        nums = tuple(e["nums"])
        hist_draw = historical.get(nums)
        meta = PATTERN_META.get(e["primary_pattern"], {})
        conn.execute(
            """
            INSERT INTO testlotto_rare_bundle_catalog (
                pattern_key, pattern_label, nums_json, combo_rank_814,
                theoretical_count, theoretical_prob, rarity_score,
                historical_draw_no, is_ultra_rare, refs_json, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                e["primary_pattern"],
                meta.get("label", e["primary_pattern"]),
                json.dumps(e["nums"], ensure_ascii=False),
                e["combo_rank_814"],
                meta.get("theoretical_count"),
                e["theoretical_prob"],
                e["rarity_score"],
                hist_draw,
                1 if e["is_ultra_rare"] else 0,
                refs_json(),
                meta.get("note", ""),
            ),
        )
        n += 1
    conn.commit()
    conn.close()
    return n


def save_draw_hits(draws: list[dict]) -> int:
    """당첨 회차별 패턴 적중 → testlotto_rare_bundle_hits."""
    init_testlotto_db()
    conn = get_lotto_db()
    conn.execute("DELETE FROM testlotto_rare_bundle_hits")
    n = 0
    for d in draws:
        nums = sorted_nums([d[f"num{k}"] for k in range(1, 7)])
        patterns = detect_patterns(nums)
        rank = combo_to_no(nums)
        ultra = any(p in ("consec_6", "split_exact_123_434445", "arithmetic_6") for p in patterns)
        mrun = max_consecutive_run(nums)
        conn.execute(
            """
            INSERT INTO testlotto_rare_bundle_hits (
                draw_no, draw_date, nums_json, combo_rank_814,
                pattern_keys_json, max_consecutive_run, is_ultra_rare_hit
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(d["draw_no"]),
                d.get("draw_date", ""),
                json.dumps(nums, ensure_ascii=False),
                rank,
                json.dumps(patterns, ensure_ascii=False),
                mrun,
                1 if ultra or len(patterns) >= 3 else 0,
            ),
        )
        n += 1
    conn.commit()
    conn.close()
    return n


def load_draws() -> list[dict]:
    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT draw_no, draw_date, num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def build_historical_map(draws: list[dict]) -> dict[tuple[int, ...], int]:
    out: dict[tuple[int, ...], int] = {}
    for d in draws:
        nums = tuple(sorted_nums([d[f"num{k}"] for k in range(1, 7)]))
        out[nums] = int(d["draw_no"])
    return out


def get_ultra_rare_catalog(limit: int = 50) -> list[dict]:
    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT * FROM testlotto_rare_bundle_catalog
        WHERE is_ultra_rare=1
        ORDER BY rarity_score DESC, combo_rank_814 ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pattern_summary() -> dict[str, Any]:
    init_testlotto_db()
    conn = get_lotto_db()
    total_catalog = conn.execute("SELECT COUNT(*) FROM testlotto_rare_bundle_catalog").fetchone()[0]
    ultra = conn.execute(
        "SELECT COUNT(*) FROM testlotto_rare_bundle_catalog WHERE is_ultra_rare=1"
    ).fetchone()[0]
    hits_ultra = conn.execute(
        "SELECT COUNT(*) FROM testlotto_rare_bundle_hits WHERE is_ultra_rare_hit=1"
    ).fetchone()[0]
    hits_consec6 = conn.execute(
        "SELECT COUNT(*) FROM testlotto_rare_bundle_hits WHERE max_consecutive_run>=6"
    ).fetchone()[0]
    never_drawn = conn.execute(
        "SELECT COUNT(*) FROM testlotto_rare_bundle_catalog WHERE historical_draw_no IS NULL AND is_ultra_rare=1"
    ).fetchone()[0]
    conn.close()
    return {
        "catalog_total": total_catalog,
        "catalog_ultra_rare": ultra,
        "historical_ultra_hits": hits_ultra,
        "historical_consec_6": hits_consec6,
        "ultra_never_drawn": never_drawn,
    }


def run_full_survey() -> dict[str, Any]:
    draws = load_draws()
    hist = build_historical_map(draws)
    catalog = enumerate_ultra_rare_catalog()
    n_cat = save_catalog(catalog, historical=hist)
    n_hits = save_draw_hits(draws)
    summary = get_pattern_summary()
    return {
        "n_draws": len(draws),
        "catalog_saved": n_cat,
        "hits_saved": n_hits,
        "summary": summary,
        "top_ultra": get_ultra_rare_catalog(15),
    }
