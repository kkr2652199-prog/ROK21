# -*- coding: utf-8 -*-
"""극소 연속 조합 저장 — 예측 전 엔진이 읽는 목록.

기어 중립: 생성 거절은 rare_pass/tier1이 이미 담당. 이 표는 연속 세분화.
"""
from __future__ import annotations

import json
from typing import Any

from app.lotto4.combinadic import combo_to_no
from app.testlotto.brains.review_brain.rare_consec import (
    STEP1_CONSEC,
    class_rows,
    is_step1_consec,
    sig_key,
)
from app.testlotto.models import get_lotto_db, init_testlotto_db

CLASS_TABLE = "testlotto_rare_consec_classes"
COMBO_TABLE = "testlotto_rare_consec_combos"


def _enum_step1() -> list[tuple[int, ...]]:
    seen: set[tuple[int, ...]] = set()
    for start in range(1, 41):
        seen.add(tuple(range(start, start + 6)))
    for start in range(1, 42):
        block = list(range(start, start + 5))
        for x in range(1, 46):
            if x in block:
                continue
            t = tuple(sorted(block + [x]))
            if is_step1_consec(list(t)):
                seen.add(t)
    return sorted(t for t in seen if is_step1_consec(list(t)))


def rebuild() -> dict[str, Any]:
    """연속 클래스표 + STEP1 조합. 예측 생성 없음."""
    init_testlotto_db()
    combos = _enum_step1()
    conn = get_lotto_db()
    try:
        conn.execute(f"DELETE FROM {CLASS_TABLE}")
        conn.executemany(
            f"""
            INSERT INTO {CLASS_TABLE}
                (sig, space, draws, null_e, step1, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))
            """,
            [
                (
                    r["sig"],
                    int(r["space"]),
                    int(r["draws"]),
                    float(r["null_e"]),
                    1 if r["step1"] else 0,
                )
                for r in class_rows()
            ],
        )
        conn.execute(f"DELETE FROM {COMBO_TABLE}")
        conn.executemany(
            f"""
            INSERT INTO {COMBO_TABLE} (combo_no, nums_json, sig, updated_at)
            VALUES (?, ?, ?, datetime('now','localtime'))
            """,
            [
                (combo_to_no(t), json.dumps(list(t), ensure_ascii=False), sig_key(t))
                for t in combos
            ],
        )
        conn.commit()
        n_cls = conn.execute(f"SELECT COUNT(*) FROM {CLASS_TABLE}").fetchone()[0]
        n_cmb = conn.execute(f"SELECT COUNT(*) FROM {COMBO_TABLE}").fetchone()[0]
    finally:
        conn.close()
    tag_c: dict[str, int] = {}
    for t in combos:
        k = sig_key(t)
        tag_c[k] = tag_c.get(k, 0) + 1
    return {
        "classes": int(n_cls),
        "combos": int(n_cmb),
        "unique": len(combos),
        "sig_counts": tag_c,
        "step1": sorted(STEP1_CONSEC),
    }


def catalog_count() -> int:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {COMBO_TABLE}").fetchone()[0])
    finally:
        conn.close()


def page_items(offset: int, limit: int) -> list[dict[str, Any]]:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            f"""
            SELECT combo_no, nums_json, sig
            FROM {COMBO_TABLE}
            ORDER BY combo_no
            LIMIT ? OFFSET ?
            """,
            (int(limit), int(offset)),
        ).fetchall()
    finally:
        conn.close()
    out = []
    for r in rows:
        nums = json.loads(r[1])
        out.append(
            {
                "combo_no": int(r[0]),
                "numbers": nums,
                "total": int(sum(nums)),
                "is_winner": False,
                "win_draw_no": None,
                "win_date": None,
                "rare_pass": True,
                "rare_tags": [],
                "consec_sig": str(r[2]),
                "consec_step1": True,
            }
        )
    return out
