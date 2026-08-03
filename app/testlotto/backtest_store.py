"""K-SIGNAL 백테스트 DB 저장·조회."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.testlotto.models import get_lotto_db, init_testlotto_db
from app.testlotto.survey_labels import (
    eval_mode_label_ko,
    strategy_label_ko,
    survey_label_ko,
    tier_rank_label,
)


def insert_backtest_run(
    conn: sqlite3.Connection,
    *,
    survey_id: str,
    strategy_id: str,
    gate_mode: str,
    eval_mode: str,
    n_draws: int,
    seed: int,
    draw_start: int,
    draw_end: int,
    ge3_rate: float,
    mean_hits: float,
    ge3_count: int,
    tiers: dict[str, int],
    p_value: float | None = None,
    verdict: str = "",
    delta_ge3_vs_pin: float | None = None,
    source_json: str | None = None,
    note: str = "",
) -> int:
    cur = conn.execute(
        """
        INSERT INTO testlotto_backtest_runs (
            survey_id, survey_label_ko, strategy_id, strategy_label_ko,
            gate_mode, eval_mode, n_draws, seed, draw_start, draw_end,
            ge3_rate, mean_hits, ge3_count,
            tier_r1, tier_r2, tier_r3, tier_r4, tier_r5,
            p_value, verdict, delta_ge3_vs_pin, source_json, note
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            survey_id,
            survey_label_ko(survey_id),
            strategy_id,
            strategy_label_ko(strategy_id),
            gate_mode,
            eval_mode,
            n_draws,
            seed,
            draw_start,
            draw_end,
            ge3_rate,
            mean_hits,
            ge3_count,
            int(tiers.get("r1", 0)),
            int(tiers.get("r2", 0)),
            int(tiers.get("r3", 0)),
            int(tiers.get("r4", 0)),
            int(tiers.get("r5", 0)),
            p_value,
            verdict,
            delta_ge3_vs_pin,
            source_json,
            note,
        ),
    )
    return int(cur.lastrowid)


def insert_draw_results(
    conn: sqlite3.Connection,
    run_id: int,
    rows: list[dict[str, Any]],
) -> int:
    conn.executemany(
        """
        INSERT OR REPLACE INTO testlotto_backtest_draw_results
            (run_id, draw_no, best_hits, best_tier)
        VALUES (?,?,?,?)
        """,
        [(run_id, int(r["draw_no"]), int(r["best_hits"]), int(r.get("best_tier") or 0)) for r in rows],
    )
    return len(rows)


def delete_runs_for_survey_strategy(
    conn: sqlite3.Connection, survey_id: str, strategy_id: str
) -> None:
    old = conn.execute(
        "SELECT run_id FROM testlotto_backtest_runs WHERE survey_id=? AND strategy_id=?",
        (survey_id, strategy_id),
    ).fetchall()
    for r in old:
        conn.execute(
            "DELETE FROM testlotto_backtest_draw_results WHERE run_id=?",
            (int(r[0]),),
        )
    conn.execute(
        "DELETE FROM testlotto_backtest_runs WHERE survey_id=? AND strategy_id=?",
        (survey_id, strategy_id),
    )


def is_draw_backtested(draw_no: int) -> bool:
    """회차별 백테스트 draw_results 가 1건이라도 있으면 True."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM testlotto_backtest_draw_results WHERE draw_no=? LIMIT 1",
            (draw_no,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def get_backtest_summaries_for_draw(draw_no: int) -> list[dict[str, Any]]:
    """회차별 전략·run 백테스트 요약 (pool 캐시 miss 시 UI 폴백)."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT r.run_id, r.survey_id, r.strategy_id, r.strategy_label_ko,
                   d.best_hits, d.best_tier
            FROM testlotto_backtest_draw_results d
            JOIN testlotto_backtest_runs r ON r.run_id = d.run_id
            WHERE d.draw_no = ?
            ORDER BY r.run_id DESC
            """,
            (draw_no,),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            d = dict(row)
            out.append(
                {
                    "run_id": d["run_id"],
                    "survey_id": d["survey_id"],
                    "survey_label_ko": d.get("survey_label_ko") or survey_label_ko(d["survey_id"]),
                    "strategy_id": d["strategy_id"],
                    "strategy_label_ko": d.get("strategy_label_ko") or strategy_label_ko(d["strategy_id"]),
                    "best_hits": d["best_hits"],
                    "best_tier": d.get("best_tier") or 0,
                    "best_tier_label": tier_rank_label(int(d.get("best_tier") or 0)),
                }
            )
        return out
    finally:
        conn.close()


def list_backtest_draw_ranges() -> list[dict[str, Any]]:
    """등록된 백테스트 run 의 draw_start~draw_end 목록."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT run_id, survey_id, strategy_id, draw_start, draw_end
            FROM testlotto_backtest_runs
            ORDER BY run_id
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def build_backtest_draw_index() -> dict[str, Any]:
    """회차별 백테 요약 전체 — UI 프리로드(로딩 없이 즉시 표시)."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT d.draw_no, r.run_id, r.survey_id, r.strategy_id, r.strategy_label_ko,
                   d.best_hits, d.best_tier
            FROM testlotto_backtest_draw_results d
            JOIN testlotto_backtest_runs r ON r.run_id = d.run_id
            ORDER BY d.draw_no ASC, r.run_id DESC
            """
        ).fetchall()
        by_draw: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            d = dict(row)
            key = str(int(d["draw_no"]))
            by_draw.setdefault(key, []).append(
                {
                    "run_id": d["run_id"],
                    "survey_id": d["survey_id"],
                    "survey_label_ko": survey_label_ko(d["survey_id"]),
                    "strategy_id": d["strategy_id"],
                    "strategy_label_ko": d.get("strategy_label_ko")
                    or strategy_label_ko(d["strategy_id"]),
                    "best_hits": d["best_hits"],
                    "best_tier": d.get("best_tier") or 0,
                    "best_tier_label": tier_rank_label(int(d.get("best_tier") or 0)),
                }
            )
        draw_nos = sorted((int(k) for k in by_draw.keys()), reverse=True)
        return {
            "ok": True,
            "n_draws": len(by_draw),
            "n_rows": len(rows),
            "draw_range": [draw_nos[-1], draw_nos[0]] if draw_nos else [],
            "by_draw": by_draw,
        }
    finally:
        conn.close()


def list_backtest_runs(limit: int = 50) -> list[dict[str, Any]]:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT * FROM testlotto_backtest_runs
            ORDER BY created_at DESC, run_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_run_row_to_dict(dict(r)) for r in rows]
    finally:
        conn.close()


def get_backtest_run(run_id: int, draw_limit: int = 500, draw_offset: int = 0) -> dict[str, Any] | None:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        row = conn.execute(
            "SELECT * FROM testlotto_backtest_runs WHERE run_id=?",
            (run_id,),
        ).fetchone()
        if not row:
            return None
        out = _run_row_to_dict(dict(row))
        total = conn.execute(
            "SELECT COUNT(*) FROM testlotto_backtest_draw_results WHERE run_id=?",
            (run_id,),
        ).fetchone()[0]
        draws = conn.execute(
            """
            SELECT draw_no, best_hits, best_tier
            FROM testlotto_backtest_draw_results
            WHERE run_id=?
            ORDER BY draw_no DESC
            LIMIT ? OFFSET ?
            """,
            (run_id, draw_limit, draw_offset),
        ).fetchall()
        out["draw_total"] = int(total)
        out["draws"] = [dict(d) for d in draws]
        return out
    finally:
        conn.close()


def _run_row_to_dict(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": d["run_id"],
        "survey_id": d["survey_id"],
        "survey_label_ko": d.get("survey_label_ko") or survey_label_ko(d["survey_id"]),
        "strategy_id": d["strategy_id"],
        "strategy_label_ko": d.get("strategy_label_ko") or strategy_label_ko(d["strategy_id"]),
        "gate_mode": d.get("gate_mode"),
        "gate_mode_ko": "빠른 검증" if d.get("gate_mode") == "quick" else "전체 검증",
        "eval_mode": d.get("eval_mode"),
        "eval_mode_ko": eval_mode_label_ko(str(d.get("eval_mode") or "")),
        "n_draws": d.get("n_draws"),
        "seed": d.get("seed"),
        "draw_range": [d.get("draw_start"), d.get("draw_end")],
        "ge3_rate": d.get("ge3_rate"),
        "ge3_rate_ko": "3개 이상 적중률",
        "mean_hits": d.get("mean_hits"),
        "mean_hits_ko": "평균 적중 개수",
        "ge3_count": d.get("ge3_count"),
        "tiers": {
            "r1": d.get("tier_r1", 0),
            "r2": d.get("tier_r2", 0),
            "r3": d.get("tier_r3", 0),
            "r4": d.get("tier_r4", 0),
            "r5": d.get("tier_r5", 0),
        },
        "p_value": d.get("p_value"),
        "verdict": d.get("verdict"),
        "delta_ge3_vs_pin": d.get("delta_ge3_vs_pin"),
        "note": d.get("note"),
        "created_at": d.get("created_at"),
        "source_json": d.get("source_json"),
    }


def import_run_from_json_summary(
    json_path: str,
    strategy_key: str,
    *,
    id_field: str = "strategy_id",
    list_field: str = "strategies",
) -> int | None:
    """JSON 요약만 DB에 적재 (per-draw 없음). draw 결과는 별도 WF 재실행."""
    from pathlib import Path

    p = Path(json_path)
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    survey_id = str(data.get("id") or "")
    gate_mode = str(data.get("gate_mode") or "quick")
    seed = int(data.get("mc_seed") or 42)
    dr = data.get("draw_range") or [0, 0]
    items = data.get(list_field) or []
    item = next((x for x in items if x.get(id_field) == strategy_key), None)
    if not item:
        return None

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        delete_runs_for_survey_strategy(conn, survey_id, strategy_key)
        run_id = insert_backtest_run(
            conn,
            survey_id=survey_id,
            strategy_id=strategy_key,
            gate_mode=gate_mode,
            eval_mode=str(item.get("eval_mode") or ""),
            n_draws=int(item.get("n") or data.get("n_eval") or 0),
            seed=seed,
            draw_start=int(dr[0]),
            draw_end=int(dr[1]),
            ge3_rate=float(item.get("ge3_rate") or 0),
            mean_hits=float(item.get("mean") or 0),
            ge3_count=int(item.get("ge3_count") or 0),
            tiers=item.get("tiers") or {},
            p_value=item.get("p_value"),
            verdict=str(item.get("verdict") or ""),
            delta_ge3_vs_pin=item.get("delta_ge3_vs_pin"),
            source_json=str(p.as_posix()),
            note="JSON 요약만 — per-draw는 import_k_signal_backtest.py",
        )
        conn.commit()
        return run_id
    finally:
        conn.close()
