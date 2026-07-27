# -*- coding: utf-8 -*-
"""K-AWAIT — 1235 발표 후 fetch·채점·feedback·1236 예측 루프.

기본: --readiness (READ-ONLY · API probe · 3DB · stage1 산출 확인)
실행: --execute (1235 API·DB 준비 시만 · lotto4 collect→fanout→testlotto 채점→1236 예측)

동결: random.choices / _get_draws_before / boost 상한 미수정.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260728_KAWAIT_readiness.json"
DRAW_TARGET = 1235
DRAW_PREDICT = 1236
DBS = {
    "lotto4": ROOT / "data" / "lotto4.db",
    "testlotto": ROOT / "data" / "lotto_testlotto.db",
    "hyodo": ROOT / "data" / "lotto_hyodo.db",
}


def _db_max(label: str, path: Path) -> int:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    row = con.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()
    con.close()
    return int(row[0] or 0)


def _probe_api(draw_no: int) -> dict[str, Any]:
    from app.lotto.data_service import fetch_single_draw

    draw = fetch_single_draw(draw_no)
    if not draw:
        return {"available": False, "draw_no": draw_no}
    nums = [draw.get(f"num{i}") for i in range(1, 7)] + [draw.get("bonus")]
    return {
        "available": True,
        "draw_no": draw_no,
        "draw_date": draw.get("draw_date"),
        "numbers": nums,
    }


def _pred_counts(draw_no: int) -> dict[str, int]:
    con = sqlite3.connect(f"file:{DBS['testlotto']}?mode=ro", uri=True)
    rows = con.execute(
        """
        SELECT brain_tag, COUNT(*) AS n
        FROM lotto_predictions
        WHERE target_draw_no = ?
          AND brain_tag IN ('stat','markov','review')
        GROUP BY brain_tag
        ORDER BY brain_tag
        """,
        (draw_no,),
    ).fetchall()
    con.close()
    return {str(r[0]): int(r[1]) for r in rows}


def _stage1_artifacts() -> dict[str, bool]:
    paths = {
        "stage1_script": ROOT / "tools" / "run_testlotto_stage1_bigdata.py",
        "atlas": ROOT / "tools" / "_testlotto_pattern_atlas_1234.json",
        "baseline": ROOT / "tools" / "_testlotto_stage1_baseline_1232_1234.json",
        "summary": ROOT / "tools" / "_testlotto_stage1_summary.json",
    }
    return {k: p.is_file() for k, p in paths.items()}


def _smoke_3db(expected_max: int) -> dict[str, Any]:
    num_key = ("num1", "num2", "num3", "num4", "num5", "num6", "bonus")

    def load_map(path: Path) -> dict[int, tuple]:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        q = f"SELECT draw_no,{','.join(num_key)} FROM lotto_draws"
        out = {int(r[0]): tuple(r[1:]) for r in con.execute(q)}
        con.close()
        return out

    stats = {k: _db_max(k, p) for k, p in DBS.items()}
    src = load_map(DBS["lotto4"])
    mism = {}
    for label in ("testlotto", "hyodo"):
        dst = load_map(DBS[label])
        mism[label] = sorted(n for n in set(src) & set(dst) if src[n] != dst[n])
    ok = all(v == expected_max for v in stats.values()) and all(len(v) == 0 for v in mism.values())
    return {"stats": stats, "mismatches": mism, "pass": ok, "expected_max": expected_max}


def readiness() -> dict[str, Any]:
    max_by_db = {k: _db_max(k, p) for k, p in DBS.items()}
    api = _probe_api(DRAW_TARGET)
    preds = _pred_counts(DRAW_TARGET)
    artifacts = _stage1_artifacts()

    ready_collect = api["available"] and max_by_db["lotto4"] < DRAW_TARGET
    ready_score = max_by_db["testlotto"] >= DRAW_TARGET
    prior_ok = sum(preds.values()) >= 15

    checks = {
        "3db_max_1234": all(v == 1234 for v in max_by_db.values()),
        "api_1235": api["available"],
        "stage1_artifacts": all(artifacts.values()),
        "predict_1235_saved": prior_ok,
        "ready_for_execute": ready_collect or (ready_score and prior_ok),
    }

    return {
        "task": "K-AWAIT",
        "mode": "readiness",
        "draw_target": DRAW_TARGET,
        "draw_predict": DRAW_PREDICT,
        "max_by_db": max_by_db,
        "api_probe": api,
        "predict_1235_counts": preds,
        "stage1_artifacts": artifacts,
        "checks": checks,
        "verify_pass": checks["stage1_artifacts"] and checks["predict_1235_saved"] and checks["3db_max_1234"],
        "next_when_api_yes": [
            "python tools/_kawait_1235_loop.py --execute",
            "python tools/_pin_3db_smoke.py",
            "python tools/_kpin_close_verify.py (선택)",
        ],
        "collab_doc": "My_Drive_Sync/SUMMARY/COLLAB_HANDOFF.md",
        "note": "READ-ONLY unless --execute and api_1235 available",
    }


def _collect_fanout() -> dict[str, Any]:
    from app.lotto.data_service import collect_latest_forward

    return collect_latest_forward(max_probe=5)


def _score_feedback_1235() -> dict[str, Any]:
    from app.testlotto.engine import refresh_prediction_scores_for_target_draw
    from app.testlotto.feedback import maybe_update_brain_weights_after_scoring
    from app.testlotto.learn_state import get_all_learn_states
    from app.testlotto.models import get_lotto_db
    from app.testlotto.walkforward import review_single_draw

    dn = DRAW_TARGET
    scored = refresh_prediction_scores_for_target_draw(dn)
    maybe_update_brain_weights_after_scoring(dn)
    review = review_single_draw(dn, store_features=True)

    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT brain_tag,
                   COUNT(*) AS n,
                   ROUND(AVG(matched_count), 4) AS avg_match
            FROM lotto_predictions
            WHERE target_draw_no = ?
              AND brain_tag IN ('stat','markov','review')
            GROUP BY brain_tag
            ORDER BY brain_tag
            """,
            (dn,),
        ).fetchall()
        stats = [dict(r) for r in rows]
    finally:
        conn.close()

    states = get_all_learn_states()
    return {
        "draw_no": dn,
        "scores_refreshed": bool(scored),
        "review_skipped": review.get("skipped"),
        "brain_stats": stats,
        "learn_states": {
            tag: {
                "review_count": s.get("review_count"),
                "last_draw_no": s.get("last_draw_no"),
                "recent_avg_match": s.get("recent_avg_match"),
            }
            for tag, s in states.items()
        },
    }


def _predict_1236() -> dict[str, Any]:
    from app.testlotto.brains.coordinator import run_coordinated_prediction
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.models import get_lotto_db

    prior = _get_draws_before(DRAW_PREDICT)
    max_prior = max(d["draw_no"] for d in prior) if prior else 0
    if max_prior != DRAW_TARGET:
        return {
            "ok": False,
            "error": f"_get_draws_before({DRAW_PREDICT}) max_prior={max_prior}, expected {DRAW_TARGET}",
            "prior_count": len(prior),
        }

    pred = run_coordinated_prediction(DRAW_PREDICT)
    conn = get_lotto_db()
    try:
        by = conn.execute(
            """
            SELECT brain_tag, COUNT(*) AS n
            FROM lotto_predictions
            WHERE target_draw_no = ?
              AND brain_tag IN ('stat','markov','review')
            GROUP BY brain_tag
            ORDER BY brain_tag
            """,
            (DRAW_PREDICT,),
        ).fetchall()
        counts = {r["brain_tag"]: int(r["n"]) for r in by}
    finally:
        conn.close()

    return {
        "ok": True,
        "max_prior_draw": max_prior,
        "prior_count": len(prior),
        "prediction_keys": list(pred.keys()) if isinstance(pred, dict) else [],
        "error": pred.get("error") if isinstance(pred, dict) else None,
        "saved_counts": counts,
        "total_saved": sum(counts.values()),
    }


def execute_loop() -> dict[str, Any]:
    api = _probe_api(DRAW_TARGET)
    if not api.get("available"):
        return {
            "task": "K-AWAIT",
            "mode": "execute",
            "ok": False,
            "error": f"API {DRAW_TARGET} not available — abort (no partial fetch)",
            "api_probe": api,
        }

    collect = _collect_fanout()
    max_tl = _db_max("testlotto", DBS["testlotto"])
    if max_tl < DRAW_TARGET:
        return {
            "task": "K-AWAIT",
            "mode": "execute",
            "ok": False,
            "error": f"testlotto MAX={max_tl} after collect, need {DRAW_TARGET}",
            "collect": collect,
        }

    score = _score_feedback_1235()
    predict = _predict_1236()
    smoke = _smoke_3db(DRAW_TARGET)
    smoke_path = ROOT / "docs" / "benchmarks" / f"20260728_KAWAIT_3db_{DRAW_TARGET}.json"
    smoke_path.write_text(json.dumps(smoke, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = (
        predict.get("ok")
        and predict.get("total_saved", 0) >= 15
        and score.get("scores_refreshed")
        and smoke.get("pass") is True
    )

    return {
        "task": "K-AWAIT",
        "mode": "execute",
        "ok": ok,
        "collect": collect,
        "score_1235": score,
        "predict_1236": predict,
        "3db_smoke": smoke,
        "3db_smoke_path": str(smoke_path),
        "max_by_db": {k: _db_max(k, p) for k, p in DBS.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="K-AWAIT 1235 loop")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run full loop when API 1235 available",
    )
    args = parser.parse_args()

    payload = execute_loop() if args.execute else readiness()
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), **{k: payload[k] for k in payload if k != "learn_states"}}, ensure_ascii=False))

    if args.execute:
        return 0 if payload.get("ok") else 1
    return 0 if payload.get("verify_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
