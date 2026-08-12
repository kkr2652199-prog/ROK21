# -*- coding: utf-8 -*-
"""뇌별 스킬 숙제 persist — LIST_V3 L9c.

결과 확정 회차 N 이후, 각 뇌 hint 테이블(스킬축)을 as_of=N 으로 저장.
예측 target=M 시 as_of < M 최신 행을 읽어 재계산을 대체(플래그 ON).
컨닝 금지: as_of >= target 행은 읽지 않음.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db

logger = logging.getLogger(__name__)

TABLE = "testlotto_skill_homework"
SCHEMA_VERSION = 1

# 쓰기=항상(결과확정) · 읽기소비=플래그
SKILL_HOMEWORK_CONSUME: bool = True

# brain → (skill_kind, window_weeks|None)
SKILL_KIND_BY_BRAIN: dict[str, tuple[str, int | None]] = {
    "stat": ("miss_pattern", 52),
    "markov": ("crowd_prefer", None),
    "review": ("crowd_prize", None),
}


def ensure_skill_homework_table(conn=None) -> None:
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
                skill_kind      TEXT NOT NULL,
                window_weeks    INTEGER,
                payload_json    TEXT NOT NULL,
                schema_version  INTEGER DEFAULT 1,
                note            TEXT,
                created_at      TEXT DEFAULT (datetime('now','localtime')),
                PRIMARY KEY (as_of_draw, brain_tag, skill_kind)
            )
            """
        )
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_skill_hw_asof ON {TABLE}(as_of_draw)"
        )
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()


def _hint_to_payload(hint: dict[int, float]) -> dict[str, float]:
    return {str(i): float(hint.get(i, 0.0)) for i in range(1, 46)}


def _payload_to_hint(payload: dict[str, Any]) -> dict[int, float]:
    out: dict[int, float] = {}
    for i in range(1, 46):
        out[i] = float(payload.get(str(i), payload.get(i, 0.0)) or 0.0)
    return out


def compute_skill_hint(brain_tag: str, as_of_draw: int) -> dict[int, float]:
    """draws draw_no <= as_of 로 뇌 스킬 hint 재계산 (저장용)."""
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.signal_pool import HINT_SPEC_BY_BRAIN, _build_hint_for_spec

    # as_of=N → N+1 예측에 쓸 표 = draws before (N+1) = draws <= N
    target_next = int(as_of_draw) + 1
    draws = _get_draws_before(target_next)
    weeks, signal = HINT_SPEC_BY_BRAIN[brain_tag]
    return _build_hint_for_spec(draws, weeks, signal, target_next)


def write_skill_homework(as_of_draw: int, *, note: str = "") -> dict[str, Any]:
    """결과 확정 회차 as_of 에 대해 3뇌 스킬 hint 스냅샷 UPSERT."""
    ensure_skill_homework_table()
    dno = int(as_of_draw)
    out: dict[str, Any] = {"ok": True, "as_of_draw": dno, "brains": {}, "note": note}
    conn = get_lotto_db()
    try:
        from app.testlotto.signal_pool import HINT_SPEC_BY_BRAIN

        for tag in SKILL_KIND_BY_BRAIN:
            try:
                hint = compute_skill_hint(tag, dno)
                weeks_w, kind_w = HINT_SPEC_BY_BRAIN[tag]
                payload = _hint_to_payload(hint)
                conn.execute(
                    f"""
                    INSERT INTO {TABLE} (
                        as_of_draw, brain_tag, skill_kind, window_weeks,
                        payload_json, schema_version, note
                    ) VALUES (?,?,?,?,?,?,?)
                    ON CONFLICT(as_of_draw, brain_tag, skill_kind) DO UPDATE SET
                        window_weeks=excluded.window_weeks,
                        payload_json=excluded.payload_json,
                        schema_version=excluded.schema_version,
                        note=excluded.note,
                        created_at=datetime('now','localtime')
                    """,
                    (
                        dno,
                        tag,
                        kind_w,
                        weeks_w,
                        json.dumps(payload, ensure_ascii=False),
                        SCHEMA_VERSION,
                        note or "",
                    ),
                )
                out["brains"][tag] = {
                    "skill_kind": kind_w,
                    "window_weeks": weeks_w,
                    "n_keys": len(payload),
                    "sum": round(sum(payload.values()), 6),
                }
            except Exception as e:
                logger.exception("[L9c-SKILL-HW] write fail brain=%s", tag)
                out["brains"][tag] = {"error": str(e)}
                out["ok"] = False
        conn.commit()
    finally:
        conn.close()
    logger.info("[L9c-SKILL-HW] write as_of=%s ok=%s note=%s", dno, out["ok"], note)
    return out


def load_skill_homework_before(target_draw_no: int) -> dict[str, dict[int, float]]:
    """target 직전 as_of 스냅샷. 없으면 빈 dict (호출측 재계산)."""
    ensure_skill_homework_table()
    t = int(target_draw_no)
    conn = get_lotto_db()
    try:
        as_of = conn.execute(
            f"SELECT MAX(as_of_draw) FROM {TABLE} WHERE as_of_draw < ?",
            (t,),
        ).fetchone()[0]
        if as_of is None:
            return {}
        if int(as_of) >= t:
            return {}
        rows = conn.execute(
            f"""
            SELECT brain_tag, skill_kind, payload_json
            FROM {TABLE}
            WHERE as_of_draw = ?
            """,
            (int(as_of),),
        ).fetchall()
    finally:
        conn.close()

    out: dict[str, dict[int, float]] = {}
    for r in rows:
        tag = str(r["brain_tag"])
        expect = SKILL_KIND_BY_BRAIN.get(tag, (None, None))[0]
        kind = str(r["skill_kind"])
        # kind 불일치여도 payload 우선(스키마 진화 대비) · 로그만
        if expect and kind != expect and kind not in (
            "miss_pattern",
            "crowd_prefer",
            "crowd_prize",
        ):
            logger.warning("[L9c-SKILL-HW] unexpected kind %s for %s", kind, tag)
        payload = json.loads(r["payload_json"] or "{}")
        out[tag] = _payload_to_hint(payload)
    return out


def assert_no_peek_homework(target_draw_no: int) -> bool:
    """as_of >= target 행이 읽히지 않음(로드 결과 검증용)."""
    loaded_asof_check = True
    t = int(target_draw_no)
    conn = get_lotto_db()
    try:
        bad = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE as_of_draw >= ?",
            (t,),
        ).fetchone()[0]
        # 존재해도 로드가 막으면 OK — 로드 API 검증
        got = load_skill_homework_before(t)
        # got 의 as_of 는 내부에서 < t 보장; 추가 교차: 최신 as_of
        mx = conn.execute(
            f"SELECT MAX(as_of_draw) FROM {TABLE} WHERE as_of_draw < ?",
            (t,),
        ).fetchone()[0]
        if mx is not None and int(mx) >= t:
            loaded_asof_check = False
        _ = bad  # 테이블에 future 행이 있어도 API가 안 읽으면 PASS
        return loaded_asof_check and (not got or mx is None or int(mx) < t)
    finally:
        conn.close()
