# -*- coding: utf-8 -*-
"""K-EVOLVE-AUTO S1 — 상태머신 + dry-run 계획.

실행 wire 기본 OFF (`EVOLVE_AUTO` env != 1).
S1: plan만 · SCORE/PREDICT 실적용은 S2+ (apply 호출 시 명시 차단 또는 stub).
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db

BRAIN_TAGS = ("stat", "markov", "review")
AUTO_FLAG_ENV = "EVOLVE_AUTO"
DEFAULT_LOOKBACK = 5  # G2: 직전 N회 로그 완비 검사


def evolve_auto_enabled() -> bool:
    return os.environ.get(AUTO_FLAG_ENV, "0").strip() == "1"


def ensure_auto_state_table(conn=None) -> None:
    own = conn is None
    if own:
        init_testlotto_db()
        conn = get_lotto_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS testlotto_evolve_auto_state (
            id                   INTEGER PRIMARY KEY CHECK (id = 1),
            last_completed_draw  INTEGER,
            phase                TEXT NOT NULL DEFAULT 'idle',
            last_error           TEXT DEFAULT '',
            last_plan_json       TEXT DEFAULT '',
            paused               INTEGER NOT NULL DEFAULT 0,
            updated_at           TEXT DEFAULT (datetime('now','localtime'))
        )
        """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO testlotto_evolve_auto_state (id, phase, paused)
        VALUES (1, 'idle', 0)
        """
    )
    if own:
        conn.commit()
        conn.close()


def get_auto_state() -> dict[str, Any]:
    ensure_auto_state_table()
    conn = get_lotto_db()
    try:
        row = conn.execute(
            "SELECT * FROM testlotto_evolve_auto_state WHERE id=1"
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {
            "ok": True,
            "last_completed_draw": None,
            "phase": "idle",
            "last_error": "",
            "paused": False,
            "evolve_auto_env": evolve_auto_enabled(),
        }
    d = dict(row)
    plan = None
    if d.get("last_plan_json"):
        try:
            plan = json.loads(d["last_plan_json"])
        except Exception:
            plan = None
    return {
        "ok": True,
        "last_completed_draw": d.get("last_completed_draw"),
        "phase": d.get("phase") or "idle",
        "last_error": d.get("last_error") or "",
        "paused": bool(d.get("paused")),
        "last_plan": plan,
        "updated_at": d.get("updated_at"),
        "evolve_auto_env": evolve_auto_enabled(),
    }


def save_auto_state(
    *,
    last_completed_draw: int | None = None,
    phase: str | None = None,
    last_error: str | None = None,
    last_plan: dict | None = None,
    paused: bool | None = None,
) -> None:
    ensure_auto_state_table()
    cur = get_auto_state()
    conn = get_lotto_db()
    try:
        conn.execute(
            """
            UPDATE testlotto_evolve_auto_state SET
                last_completed_draw = ?,
                phase = ?,
                last_error = ?,
                last_plan_json = ?,
                paused = ?,
                updated_at = datetime('now','localtime')
            WHERE id = 1
            """,
            (
                last_completed_draw
                if last_completed_draw is not None
                else cur.get("last_completed_draw"),
                phase if phase is not None else cur.get("phase"),
                last_error if last_error is not None else cur.get("last_error") or "",
                json.dumps(last_plan if last_plan is not None else cur.get("last_plan") or {}, ensure_ascii=False),
                int(cur.get("paused") if paused is None else paused),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _max_draw(conn) -> int | None:
    r = conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()
    return int(r[0]) if r and r[0] is not None else None


def _evolve_brain_count(conn, draw_no: int) -> int:
    r = conn.execute(
        "SELECT COUNT(*) FROM testlotto_evolve_log WHERE draw_no=?",
        (int(draw_no),),
    ).fetchone()
    return int(r[0] or 0)


def _has_pool_cache_any(conn, draw_no: int) -> bool:
    r = conn.execute(
        """
        SELECT COUNT(DISTINCT brain) FROM testlotto_pool_view_cache
        WHERE draw_no=?
        """,
        (int(draw_no),),
    ).fetchone()
    return int(r[0] or 0) >= 3


def _log_gap_report(conn, max_draw: int, lookback: int) -> dict[str, Any]:
    """직전 lookback 회차 중 3뇌 미완 목록."""
    missing = []
    checked = []
    for dno in range(max(1, max_draw - lookback + 1), max_draw + 1):
        n = _evolve_brain_count(conn, dno)
        checked.append({"draw_no": dno, "brains": n})
        if n < 3:
            missing.append(dno)
    return {
        "lookback": lookback,
        "checked": checked,
        "missing_or_incomplete": missing,
        "g2_pass": len(missing) == 0,
    }


def plan_tick(*, lookback: int = DEFAULT_LOOKBACK) -> dict[str, Any]:
    """S1 dry-run 계획 — DB 읽기만으로 다음 액션 결정 (쓰기 없는 계획 본체)."""
    init_testlotto_db()
    ensure_auto_state_table()
    from app.testlotto.evolve_log import ensure_evolve_log_table

    ensure_evolve_log_table()
    conn = get_lotto_db()
    try:
        max_draw = _max_draw(conn)
        state = get_auto_state()
        if max_draw is None:
            plan = {
                "ok": False,
                "error": "lotto_draws 비어 있음",
                "actions": [],
                "dry_run": True,
            }
            return plan

        g2 = _log_gap_report(conn, max_draw, lookback)
        # 로그가 있는 최대 회차
        r = conn.execute("SELECT MAX(draw_no) FROM testlotto_evolve_log").fetchone()
        evolve_max = int(r[0]) if r and r[0] is not None else None

        actions: list[dict[str, Any]] = []
        # 미로그 확정회차: evolve_max+1 .. max_draw
        start_score = (evolve_max + 1) if evolve_max is not None else 1
        for dno in range(start_score, max_draw + 1):
            has_cache = _has_pool_cache_any(conn, dno)
            n_br = _evolve_brain_count(conn, dno)
            if n_br >= 3:
                continue
            if has_cache:
                actions.append(
                    {
                        "op": "SCORE",
                        "draw_no": dno,
                        "reason": "draws확정·pool캐시있음·evolve_log미완",
                        "source": "pool_cache",
                    }
                )
            else:
                actions.append(
                    {
                        "op": "PREDICT_THEN_SCORE",
                        "draw_no": dno,
                        "reason": "draws확정·캐시없음·evolve_log미완",
                        "source": "build_pool_and_repack",
                    }
                )

        # 다음 미추첨 예측 후보
        next_predict = max_draw + 1
        actions.append(
            {
                "op": "PREDICT_ONLY",
                "draw_no": next_predict,
                "reason": "미추첨 회차 사전 예측(캐시 워밍)",
                "source": "build_pool_and_repack",
                "optional": True,
            }
        )

        # pause / flag
        blocked = []
        if state.get("paused"):
            blocked.append("paused=1")
        if not evolve_auto_enabled():
            blocked.append(f"{AUTO_FLAG_ENV}!=1")
        if not g2["g2_pass"] and evolve_max is not None and evolve_max < max_draw - lookback:
            # 오래된 갭은 경고만 (최근 lookback 기준은 g2에 포함)
            pass
        if not g2["g2_pass"]:
            blocked.append("G2_incomplete_recent_logs")

        plan = {
            "ok": True,
            "dry_run": True,
            "ts_local": datetime.now().isoformat(timespec="seconds"),
            "max_lotto_draw": max_draw,
            "evolve_log_max": evolve_max,
            "next_predict_draw": next_predict,
            "g2": g2,
            "actions": actions,
            "action_count": len(actions),
            "mandatory_actions": [a for a in actions if not a.get("optional")],
            "blocked_for_apply": blocked,
            "would_apply": False,  # S1 항상 False
            "gates": {
                "G0_hyung_go": "required_for_S2+",
                "G1_EVOLVE_AUTO": evolve_auto_enabled(),
                "G2_recent_log": g2["g2_pass"],
                "paused": bool(state.get("paused")),
            },
            "forbid": [
                "FEATURE_LAMBDA_WIRE",
                "STRUCTURE_COVER_WIRE",
                "PAIR_COVER_WIRE",
                "best_as_learn_input",
                "W_HINT_auto_tune",
            ],
            "note": "S1 dry-run · SCORE/PREDICT 실적용 없음",
        }
        return plan
    finally:
        conn.close()


def tick(*, dry_run: bool = True, lookback: int = DEFAULT_LOOKBACK) -> dict[str, Any]:
    """틱 1회. S1: dry_run=True만 지원. dry_run=False면 거부(S2 미구현)."""
    plan = plan_tick(lookback=lookback)
    if not plan.get("ok"):
        save_auto_state(phase="error", last_error=plan.get("error") or "plan_failed", last_plan=plan)
        return plan

    if not dry_run:
        plan = {
            **plan,
            "ok": False,
            "dry_run": False,
            "would_apply": False,
            "error": "S1: apply 미구현 · S2 SCORE 자동 전 dry-run만 허용",
            "actions_not_executed": plan.get("actions"),
        }
        save_auto_state(phase="error", last_error=plan["error"], last_plan=plan)
        return plan

    # dry-run: 상태만 기록
    phase = "idle"
    if plan.get("mandatory_actions"):
        phase = "planned"
    save_auto_state(
        phase=phase,
        last_error="",
        last_plan=plan,
        last_completed_draw=plan.get("evolve_log_max"),
    )
    plan["state_saved"] = True
    plan["status_after"] = get_auto_state()
    return plan
