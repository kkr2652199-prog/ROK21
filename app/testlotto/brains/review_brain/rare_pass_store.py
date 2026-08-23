# -*- coding: utf-8 -*-
"""814만 극소형태 조합 저장 — 예측 전 패스 목록.

개별 확률은 동일. 저장하는 것은 얇은 형태 조각의 조합 번호.
몰아주기 미접촉. 전체조합 탭·금액뇌가 같은 목록을 읽는다.
"""
from __future__ import annotations

import json
from itertools import combinations
from typing import Any, Iterable

from app.lotto4.combinadic import combo_to_no
from app.testlotto.brains.review_brain.rare_consec import is_step1_consec, sig_key
from app.testlotto.brains.review_brain.rare_slice import (
    STEP1_REJECT,
    is_step1_rare,
    max_run,
    pass_tags,
    tags,
)
from app.testlotto.models import get_lotto_db, init_testlotto_db

TABLE = "testlotto_rare_pass_combos"
_INDEX: set[tuple[int, ...]] | None = None


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
            if max_run(list(t)) >= 5:
                seen.add(t)
    for d in range(1, 10):
        for start in range(1, 46):
            seq = [start + i * d for i in range(6)]
            if seq[-1] > 45:
                break
            seen.add(tuple(seq))
    for y in combinations(range(1, 11), 6):
        x = tuple(y[i] + 7 * i for i in range(6))
        if 1 <= x[0] and x[5] <= 45:
            seen.add(x)
    for low in combinations(range(1, 11), 3):
        for high in combinations(range(36, 46), 3):
            seen.add(tuple(sorted(low + high)))
    for z in combinations(range(1, 16), 6):
        seen.add(z)
    seen.add((1, 2, 3, 43, 44, 45))
    return sorted(t for t in seen if is_step1_rare(list(t)))


def rebuild() -> dict[str, Any]:
    """극소 조합 목록을 다시 저장. 예측 생성 없음."""
    global _INDEX
    init_testlotto_db()
    rows = _enum_step1()
    conn = get_lotto_db()
    try:
        conn.execute(f"DELETE FROM {TABLE}")
        conn.executemany(
            f"""
            INSERT INTO {TABLE} (combo_no, nums_json, tags_json, updated_at)
            VALUES (?, ?, ?, datetime('now','localtime'))
            """,
            [
                (
                    combo_to_no(t),
                    json.dumps(list(t), ensure_ascii=False),
                    json.dumps(pass_tags(list(t)), ensure_ascii=False),
                )
                for t in rows
            ],
        )
        conn.commit()
        n = conn.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
    finally:
        conn.close()
    _INDEX = {t for t in rows}
    tag_c: dict[str, int] = {}
    for t in rows:
        for k in tags(list(t)):
            if k in STEP1_REJECT:
                tag_c[k] = tag_c.get(k, 0) + 1
    return {"ok": int(n), "unique": len(rows), "tag_counts": tag_c}


def load_index() -> set[tuple[int, ...]]:
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(f"SELECT nums_json FROM {TABLE}").fetchall()
    finally:
        conn.close()
    _INDEX = {tuple(json.loads(r[0])) for r in rows}
    return _INDEX


def in_pass_catalog(nums: Iterable[int]) -> bool:
    t = tuple(sorted(int(x) for x in nums))
    idx = load_index()
    if idx:
        return t in idx
    return is_step1_rare(list(t))


def should_pass(nums: list[int]) -> bool:
    """예측 전 패스(뽑지 않음). 표 또는 형태 규칙."""
    return is_step1_rare(nums) or in_pass_catalog(nums)


def catalog_count() -> int:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0])
    finally:
        conn.close()


def page_items(offset: int, limit: int) -> list[dict[str, Any]]:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            f"""
            SELECT combo_no, nums_json, tags_json
            FROM {TABLE}
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
                "rare_tags": [t for t in json.loads(r[2]) if t in STEP1_REJECT] or pass_tags(nums),
                "consec_sig": sig_key(nums),
                "consec_step1": is_step1_consec(nums),
            }
        )
    return out
