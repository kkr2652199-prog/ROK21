# -*- coding: utf-8 -*-
"""K-EVOLVE-AUTO — 상태머신 + tick.

실행 wire 기본 OFF (`EVOLVE_AUTO` env != 1).
S1 dry-run · S2 --apply-score · S3 --apply-predict · S4 --ops(EVOLVE_AUTO=1 필수).
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


def _maybe_mean_feedback_after_score(draw_no: int) -> dict[str, Any]:
    """SCORE 후 기존 coordinator mean 피드백 (lotto_predictions 없으면 no-op)."""
    from app.testlotto.brains.coordinator import _auto_feedback

    conn = get_lotto_db()
    try:
        _auto_feedback(int(draw_no) + 1, conn)
        return {"ok": True, "draw_no": int(draw_no), "mode": "mean", "via": "_auto_feedback"}
    except Exception as e:
        return {"ok": False, "draw_no": int(draw_no), "error": str(e)[:200]}
    finally:
        conn.close()


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
            "would_apply": bool(
                evolve_auto_enabled()
                and not state.get("paused")
                and g2["g2_pass"]
            ),
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


def score_draw_from_cache(draw_no: int) -> dict[str, Any]:
    """S2: pool_view_cache(any_schema) → evolve_log 3뇌 upsert. 예측 재실행 없음."""
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.evolve_log import (
        BRAIN_TAGS,
        build_evolve_row,
        ensure_evolve_log_table,
        upsert_evolve_row,
    )
    from app.testlotto.pool_view_cache import get_cached_pool_view_any_schema

    ensure_evolve_log_table()
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        row = conn.execute(
            """
            SELECT draw_no, num1,num2,num3,num4,num5,num6
            FROM lotto_draws WHERE draw_no=?
            """,
            (int(draw_no),),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {"ok": False, "draw_no": draw_no, "error": "lotto_draws 없음"}
    d = dict(row)
    actual = [int(d[f"num{k}"]) for k in range(1, 7)]
    pv = get_cached_pool_view_any_schema(int(draw_no))
    if not pv or not pv.get("ok"):
        return {"ok": False, "draw_no": draw_no, "error": "pool_view_cache 없음"}

    draws_before = _get_draws_before(int(draw_no))
    written = []
    for tag in BRAIN_TAGS:
        pool = pv.get("pool_by_brain", {}).get(tag, [])
        repack = pv.get("repack_by_brain", {}).get(tag, [])
        if not pool or not repack:
            return {
                "ok": False,
                "draw_no": draw_no,
                "error": f"cache incomplete brain={tag}",
            }
        erow = build_evolve_row(
            int(draw_no), tag, actual, pool, repack, draws_before=draws_before
        )
        erow["note"] = "K-EVOLVE-AUTO SCORE · weight=0 · cache→log"
        upsert_evolve_row(erow)
        written.append(
            {
                "brain_tag": tag,
                "best_hits": erow["best_hits"],
                "mean_hits": erow["mean_hits"],
                "assemble_mode": erow.get("assemble_mode"),
            }
        )
    return {"ok": True, "draw_no": int(draw_no), "brains": written}


def predict_and_cache(draw_no: int) -> dict[str, Any]:
    """S3: build_pool_and_repack → pool_view_cache 저장 (현재 schema)."""
    from app.testlotto.pool_view_cache import save_pool_view_cache
    from app.testlotto.signal_pool import build_pool_and_repack

    built = build_pool_and_repack(int(draw_no))
    if not built.get("ok"):
        return {
            "ok": False,
            "draw_no": int(draw_no),
            "error": built.get("error") or "build_pool_and_repack 실패",
        }
    save_pool_view_cache(int(draw_no), built)
    return {
        "ok": True,
        "draw_no": int(draw_no),
        "cached": True,
        "seed": built.get("seed"),
        "hybrid": built.get("hybrid"),
        "feature_lambda": built.get("feature_lambda"),
    }


def predict_then_score(draw_no: int) -> dict[str, Any]:
    """S3: 예측·캐시 후, 확정번호 있으면 SCORE."""
    pred = predict_and_cache(draw_no)
    if not pred.get("ok"):
        return pred
    conn = get_lotto_db()
    try:
        has = conn.execute(
            "SELECT 1 FROM lotto_draws WHERE draw_no=?", (int(draw_no),)
        ).fetchone()
    finally:
        conn.close()
    if not has:
        return {
            "ok": True,
            "draw_no": int(draw_no),
            "predicted": True,
            "scored": False,
            "predict": pred,
            "note": "미추첨 · PREDICT_ONLY 완료",
        }
    scored = score_draw_from_cache(draw_no)
    return {
        "ok": bool(scored.get("ok")),
        "draw_no": int(draw_no),
        "predicted": True,
        "scored": bool(scored.get("ok")),
        "predict": pred,
        "score": scored,
    }


def _execute_score_predict_actions(
    plan: dict[str, Any],
    *,
    skip_cached_predict: bool = False,
    with_mean_feedback: bool = False,
) -> dict[str, Any]:
    """SCORE / PREDICT_THEN_SCORE / optional PREDICT_ONLY 실행 본체."""
    executed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    feedbacks: list[dict[str, Any]] = []

    for a in plan.get("mandatory_actions") or []:
        op = a.get("op")
        dno = int(a["draw_no"])
        if op == "SCORE":
            r = score_draw_from_cache(dno)
        elif op == "PREDICT_THEN_SCORE":
            r = predict_then_score(dno)
        else:
            skipped.append({"action": a, "reason": "unknown mandatory op"})
            continue
        if r.get("ok"):
            executed.append({"action": a, "result": r})
            scored = bool(r.get("scored")) or op == "SCORE"
            if with_mean_feedback and scored:
                feedbacks.append(_maybe_mean_feedback_after_score(dno))
        else:
            errors.append({"action": a, "result": r})

    for a in plan.get("actions") or []:
        if not a.get("optional"):
            continue
        if a.get("op") != "PREDICT_ONLY":
            skipped.append({"action": a, "reason": "optional non-predict skipped"})
            continue
        dno = int(a["draw_no"])
        if skip_cached_predict:
            conn = get_lotto_db()
            try:
                cached = _has_pool_cache_any(conn, dno)
            finally:
                conn.close()
            if cached:
                skipped.append(
                    {"action": a, "reason": "pool_view_cache already warm · skip"}
                )
                continue
        r = predict_and_cache(dno)
        if r.get("ok"):
            executed.append({"action": a, "result": {**r, "scored": False}})
        else:
            errors.append({"action": a, "result": r})

    return {
        "executed": executed,
        "skipped": skipped,
        "errors": errors,
        "feedbacks": feedbacks,
    }


def tick(
    *,
    dry_run: bool = True,
    lookback: int = DEFAULT_LOOKBACK,
    apply_score: bool = False,
    apply_predict: bool = False,
    apply_ops: bool = False,
) -> dict[str, Any]:
    """틱 1회.

    - dry_run=True (기본): 계획만
    - apply_score=True: SCORE만 (S2)
    - apply_predict=True: PREDICT(+SCORE) (S3) · feedback 없음
    - apply_ops=True: S4 운영 · EVOLVE_AUTO=1 필수 · mean feedback(기존경로)
    """
    plan = plan_tick(lookback=lookback)
    if not plan.get("ok"):
        save_auto_state(phase="error", last_error=plan.get("error") or "plan_failed", last_plan=plan)
        return plan

    if apply_ops:
        if not evolve_auto_enabled():
            out = {
                **plan,
                "ok": False,
                "dry_run": False,
                "apply_ops": True,
                "error": f"{AUTO_FLAG_ENV}!=1 · S4 ops 거부",
            }
            save_auto_state(phase="idle", last_error=out["error"], last_plan=out)
            return out
        if get_auto_state().get("paused"):
            out = {
                **plan,
                "ok": False,
                "dry_run": False,
                "apply_ops": True,
                "error": "paused=1 · S4 ops 중단",
            }
            save_auto_state(phase="paused", last_error=out["error"], last_plan=out)
            return out

        run = _execute_score_predict_actions(
            plan, skip_cached_predict=True, with_mean_feedback=True
        )
        executed = run["executed"]
        skipped = run["skipped"]
        errors = run["errors"]
        feedbacks = run["feedbacks"]
        mandatory = plan.get("mandatory_actions") or []
        healthy_idle = len(mandatory) == 0 and len(errors) == 0
        ok = len(errors) == 0 and (len(executed) > 0 or healthy_idle)
        scored_draws = [
            e["result"]["draw_no"]
            for e in executed
            if e.get("result", {}).get("scored")
            or e.get("action", {}).get("op") == "SCORE"
        ]
        last_done = max(scored_draws) if scored_draws else plan.get("evolve_log_max")
        plan_after = plan_tick(lookback=lookback)
        out = {
            **plan,
            "ok": ok,
            "dry_run": False,
            "apply_ops": True,
            "would_apply": True,
            "executed": executed,
            "skipped": skipped,
            "errors": errors,
            "feedbacks": feedbacks,
            "healthy_idle": healthy_idle,
            "plan_after": {
                "evolve_log_max": plan_after.get("evolve_log_max"),
                "g2_pass": (plan_after.get("g2") or {}).get("g2_pass"),
                "mandatory_left": len(plan_after.get("mandatory_actions") or []),
                "next_predict_draw": plan_after.get("next_predict_draw"),
                "would_apply": plan_after.get("would_apply"),
            },
            "note": "S4 ops · EVOLVE_AUTO=1 · mean feedback(기존) · λ/covering OFF · weight=0",
        }
        save_auto_state(
            phase="ops" if ok else "error",
            last_error="" if ok else json.dumps(errors, ensure_ascii=False)[:500],
            last_plan=out,
            last_completed_draw=last_done,
            paused=False,
        )
        out["state_saved"] = True
        out["status_after"] = get_auto_state()
        return out

    if apply_predict:
        if get_auto_state().get("paused"):
            out = {
                **plan,
                "ok": False,
                "dry_run": False,
                "apply_predict": True,
                "error": "paused=1 · PREDICT 중단",
            }
            save_auto_state(phase="paused", last_error=out["error"], last_plan=out)
            return out

        run = _execute_score_predict_actions(
            plan, skip_cached_predict=False, with_mean_feedback=False
        )
        executed = run["executed"]
        skipped = run["skipped"]
        errors = run["errors"]

        ok = len(errors) == 0 and len(executed) > 0
        scored_draws = [
            e["result"]["draw_no"]
            for e in executed
            if e.get("result", {}).get("scored") or e.get("action", {}).get("op") == "SCORE"
        ]
        last_done = max(scored_draws) if scored_draws else plan.get("evolve_log_max")
        plan_after = plan_tick(lookback=lookback)
        out = {
            **plan,
            "ok": ok,
            "dry_run": False,
            "apply_predict": True,
            "would_apply": True,
            "executed": executed,
            "skipped": skipped,
            "errors": errors,
            "plan_after": {
                "evolve_log_max": plan_after.get("evolve_log_max"),
                "g2_pass": (plan_after.get("g2") or {}).get("g2_pass"),
                "mandatory_left": len(plan_after.get("mandatory_actions") or []),
                "next_predict_draw": plan_after.get("next_predict_draw"),
            },
            "note": "S3 PREDICT+SCORE · feedback/λ/covering 미실행 · weight=0",
        }
        save_auto_state(
            phase="predicted" if ok else "error",
            last_error="" if ok else json.dumps(errors, ensure_ascii=False)[:500],
            last_plan=out,
            last_completed_draw=last_done,
        )
        out["state_saved"] = True
        out["status_after"] = get_auto_state()
        return out

    if apply_score:
        if plan.get("paused") or (get_auto_state().get("paused")):
            out = {
                **plan,
                "ok": False,
                "dry_run": False,
                "apply_score": True,
                "error": "paused=1 · SCORE 중단",
            }
            save_auto_state(phase="paused", last_error=out["error"], last_plan=out)
            return out

        executed = []
        skipped = []
        errors = []
        for a in plan.get("mandatory_actions") or []:
            op = a.get("op")
            dno = int(a["draw_no"])
            if op == "SCORE":
                r = score_draw_from_cache(dno)
                if r.get("ok"):
                    executed.append({"action": a, "result": r})
                else:
                    errors.append({"action": a, "result": r})
            elif op == "PREDICT_THEN_SCORE":
                skipped.append(
                    {
                        "action": a,
                        "reason": "S2는 SCORE-only · 캐시 없으면 스킵(S3 PREDICT)",
                    }
                )
            else:
                skipped.append({"action": a, "reason": "S2 not handling"})

        for a in plan.get("actions") or []:
            if a.get("optional"):
                skipped.append({"action": a, "reason": "optional PREDICT skipped in S2"})

        ok = len(errors) == 0 and len(executed) > 0
        # 성공 시 last_completed = 실행한 최대 draw
        done_draws = [e["result"]["draw_no"] for e in executed if e.get("result", {}).get("ok")]
        last_done = max(done_draws) if done_draws else plan.get("evolve_log_max")
        # 재계획으로 G2 확인
        plan_after = plan_tick(lookback=lookback)
        out = {
            **plan,
            "ok": ok,
            "dry_run": False,
            "apply_score": True,
            "would_apply": True,
            "executed": executed,
            "skipped": skipped,
            "errors": errors,
            "plan_after": {
                "evolve_log_max": plan_after.get("evolve_log_max"),
                "g2_pass": (plan_after.get("g2") or {}).get("g2_pass"),
                "mandatory_left": len(plan_after.get("mandatory_actions") or []),
            },
            "note": "S2 SCORE apply · PREDICT/feedback 미실행 · weight=0",
        }
        save_auto_state(
            phase="scored" if ok else "error",
            last_error="" if ok else json.dumps(errors, ensure_ascii=False)[:500],
            last_plan=out,
            last_completed_draw=last_done,
        )
        out["state_saved"] = True
        out["status_after"] = get_auto_state()
        return out

    if not dry_run:
        plan = {
            **plan,
            "ok": False,
            "dry_run": False,
            "would_apply": False,
            "error": "use --apply-score (S2) / --apply-predict (S3) / --ops (S4)",
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
