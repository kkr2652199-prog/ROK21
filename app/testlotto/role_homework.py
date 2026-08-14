# -*- coding: utf-8 -*-
"""6~8(cover_r3)·9~10(shape_r2) 역할 숙제 — 원장 복습.

1~5 skill_native 불변. 타깃 회차 보너스/당첨 미사용 (as_of < target).
등수P 게이트 아님. 한 뇌만 ROLE_TIER_LEARN_BRAINS 로 소비.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db

logger = logging.getLogger(__name__)

TABLE = "testlotto_role_homework"
SCHEMA_VERSION = 1
WINDOW_DRAWS = 50
COVER_MIN_HITS = 3  # 4맞만 쓰면 표가 거의 빔(BT200 n_pos평균1). 3맞=5등 근사 복습.
BRAIN_TAGS = ("stat", "markov", "review")
ROLES = ("cover_r3", "shape_r2")


def _empty() -> dict[int, float]:
    return {i: 0.0 for i in range(1, 46)}


def _hint_to_payload(hint: dict[int, float]) -> dict[str, float]:
    return {str(i): float(hint.get(i, 0.0) or 0.0) for i in range(1, 46)}


def _payload_to_hint(payload: dict[str, Any]) -> dict[int, float]:
    out = _empty()
    for i in range(1, 46):
        out[i] = float(payload.get(str(i), payload.get(i, 0.0)) or 0.0)
    return out


def _parse_int_list(raw: Any) -> list[int]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, list):
        return []
    return [int(x) for x in raw if str(x).lstrip("-").isdigit()]


def ensure_role_homework_table(conn=None) -> None:
    own = conn is None
    if own:
        init_testlotto_db()
        conn = get_lotto_db()
    try:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE} (
                as_of_draw      INTEGER NOT NULL,
                brain_tag       TEXT NOT NULL,
                role            TEXT NOT NULL,
                window_draws    INTEGER,
                payload_json    TEXT NOT NULL,
                schema_version  INTEGER DEFAULT 1,
                note            TEXT,
                created_at      TEXT DEFAULT (datetime('now','localtime')),
                PRIMARY KEY (as_of_draw, brain_tag, role)
            )
            """
        )
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_role_hw_asof ON {TABLE}(as_of_draw)"
        )
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()


def brain_consumes_role_learn(brain_tag: str) -> bool:
    from app.testlotto.signal_pool import ROLE_TIER_LEARN_BRAINS, ROLE_TIER_LEARN_WIRE

    return bool(ROLE_TIER_LEARN_WIRE) and str(brain_tag) in ROLE_TIER_LEARN_BRAINS


def compute_role_tables(brain_tag: str, as_of_draw: int) -> dict[str, dict[int, float]]:
    """as_of=N 확정 후 표 = draw_no <= N (다음 예측 N+1 용). 타깃 N+1 미사용."""
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.pool_hit_ledger import read_ledger_before

    tag = str(brain_tag)
    as_of = int(as_of_draw)
    target_next = as_of + 1
    cover = _empty()
    shape = _empty()

    rows = read_ledger_before(target_next, brain_tag=tag, kind="pool", limit=None)
    draw_nos = sorted({int(r["draw_no"]) for r in rows})
    if len(draw_nos) > WINDOW_DRAWS:
        keep = set(draw_nos[-WINDOW_DRAWS:])
        rows = [r for r in rows if int(r["draw_no"]) in keep]

    for r in rows:
        hits = int(r.get("hits") or 0)
        bonus_hit = int(r.get("bonus_hit") or 0)
        hit_nums = _parse_int_list(r.get("hit_nums_json"))
        nums = _parse_int_list(r.get("nums_json"))
        if hits >= COVER_MIN_HITS:
            credit = hits / 6.0
            for n in hit_nums:
                if 1 <= n <= 45:
                    cover[n] += credit
            if hits >= 4:
                for n in hit_nums:
                    if 1 <= n <= 45:
                        cover[n] += 0.5
            if hits >= 5:
                for n in hit_nums:
                    if 1 <= n <= 45:
                        cover[n] += 0.5
        if hits == 5:
            for n in hit_nums:
                if 1 <= n <= 45:
                    shape[n] += 0.3
            if bonus_hit and nums:
                for n in nums:
                    if 1 <= n <= 45:
                        shape[n] += 1.0

    draws = _get_draws_before(target_next)
    if len(draws) > WINDOW_DRAWS:
        draws = draws[-WINDOW_DRAWS:]
    for d in draws:
        b = int(d.get("bonus") or 0)
        if 1 <= b <= 45:
            shape[b] += 1.0

    return {"cover_r3": cover, "shape_r2": shape}


def write_role_homework(as_of_draw: int, *, note: str = "") -> dict[str, Any]:
    """결과 확정 회차 as_of — 3뇌×2역할 스냅샷. 소비는 BRAINS 플래그."""
    ensure_role_homework_table()
    dno = int(as_of_draw)
    out: dict[str, Any] = {"ok": True, "as_of_draw": dno, "brains": {}, "note": note}
    computed: dict[str, dict[str, dict[int, float]]] = {}
    for tag in BRAIN_TAGS:
        try:
            computed[tag] = compute_role_tables(tag, dno)
        except Exception as e:
            logger.exception("[ROLE-HW] compute fail brain=%s", tag)
            out["brains"][tag] = {"error": str(e)}
            out["ok"] = False

    conn = get_lotto_db()
    try:
        for tag, tables in computed.items():
            out["brains"][tag] = {}
            for role in ROLES:
                payload = _hint_to_payload(tables[role])
                conn.execute(
                    f"""
                    INSERT INTO {TABLE} (
                        as_of_draw, brain_tag, role, window_draws,
                        payload_json, schema_version, note
                    ) VALUES (?,?,?,?,?,?,?)
                    ON CONFLICT(as_of_draw, brain_tag, role) DO UPDATE SET
                        window_draws=excluded.window_draws,
                        payload_json=excluded.payload_json,
                        schema_version=excluded.schema_version,
                        note=excluded.note,
                        created_at=datetime('now','localtime')
                    """,
                    (
                        dno,
                        tag,
                        role,
                        WINDOW_DRAWS,
                        json.dumps(payload, ensure_ascii=False),
                        SCHEMA_VERSION,
                        note or "",
                    ),
                )
                out["brains"][tag][role] = {
                    "sum": round(sum(payload.values()), 6),
                    "n_pos": sum(1 for v in payload.values() if v > 0),
                }
        conn.commit()
    finally:
        conn.close()
    logger.info("[ROLE-HW] write as_of=%s ok=%s note=%s", dno, out["ok"], note)
    return out


def load_role_homework_before(
    target_draw_no: int,
) -> dict[str, dict[str, dict[int, float]]]:
    """target 직전 as_of. {brain: {role: hint}}."""
    ensure_role_homework_table()
    t = int(target_draw_no)
    conn = get_lotto_db()
    try:
        as_of = conn.execute(
            f"SELECT MAX(as_of_draw) FROM {TABLE} WHERE as_of_draw < ?",
            (t,),
        ).fetchone()[0]
        if as_of is None or int(as_of) >= t:
            return {}
        rows = conn.execute(
            f"""
            SELECT brain_tag, role, payload_json
            FROM {TABLE}
            WHERE as_of_draw = ?
            """,
            (int(as_of),),
        ).fetchall()
    finally:
        conn.close()

    out: dict[str, dict[str, dict[int, float]]] = {}
    for r in rows:
        tag = str(r["brain_tag"])
        role = str(r["role"])
        out.setdefault(tag, {})[role] = _payload_to_hint(
            json.loads(r["payload_json"] or "{}")
        )
    return out


def load_role_hint_for_brain(
    target_draw_no: int, brain_tag: str, role: str
) -> dict[int, float]:
    if not brain_consumes_role_learn(brain_tag):
        return {}
    all_hw = load_role_homework_before(int(target_draw_no))
    return dict((all_hw.get(str(brain_tag)) or {}).get(str(role)) or {})
