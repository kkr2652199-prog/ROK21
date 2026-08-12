# -*- coding: utf-8 -*-
"""K-LIVE-FEEDBACK-REVIEW-MIRROR — LIST_V3 L9b 검증.

live/click 경로가 testlotto_brain_review 를 UPSERT 하는지,
CUTOFF 캐시 무효화가 되는지, no_peek(learn as_of) 전제와 충돌 없는지 확인.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SAMPLE_DRAW = 1236
BENCH = ROOT / "docs" / "benchmarks" / "20260812_KLIVE_FEEDBACK_REVIEW_MIRROR.json"
REPORT = ROOT / "reports" / "20260812_KLIVE_FEEDBACK_REVIEW_MIRROR.md"


def main() -> int:
    from app.testlotto.brain_review_mirror import (
        invalidate_learn_cutoff_cache,
        upsert_brain_review_feedback,
    )
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto import learn_state_cutoff as cut
    from app.testlotto.click_feedback import apply_draw_result_feedback

    init_testlotto_db()
    dno = SAMPLE_DRAW
    checks: dict[str, bool] = {}
    detail: dict = {}

    # 1) 미러 유닛: UPSERT + 캐시 무효화 (원행 백업→프로브→복원)
    conn = get_lotto_db()
    try:
        bak = conn.execute(
            "SELECT * FROM testlotto_brain_review WHERE draw_no=? AND brain_tag=?",
            (dno, "stat"),
        ).fetchone()
        bak_d = dict(bak) if bak else None
    finally:
        conn.close()

    cut._history_cache = {"probe": True}
    st = upsert_brain_review_feedback(
        dno,
        "stat",
        predicted_nums=[1, 2, 3, 4, 5, 6],
        matched_count=0,
        missed=["unit_probe"],
        best_set_no=1,
        source="L9b_unit_probe",
    )
    checks["unit_upsert"] = st == "upserted"
    checks["cache_invalidated"] = cut._history_cache is None

    conn = get_lotto_db()
    try:
        row = conn.execute(
            """
            SELECT matched_count, missed_patterns, feedback_json
            FROM testlotto_brain_review
            WHERE draw_no=? AND brain_tag=?
            """,
            (dno, "stat"),
        ).fetchone()
        fb = json.loads(row["feedback_json"] or "{}") if row else {}
        checks["unit_row_source"] = fb.get("source") == "L9b_unit_probe"
        if bak_d:
            cols = [
                "draw_no",
                "brain_tag",
                "predicted_nums",
                "predicted_sets_json",
                "best_set_no",
                "matched_count",
                "bonus_matched",
                "missed_patterns",
                "feedback_json",
                "weight_snapshot",
            ]
            conn.execute(
                """
                INSERT INTO testlotto_brain_review (
                    draw_no, brain_tag, predicted_nums, predicted_sets_json, best_set_no,
                    matched_count, bonus_matched, missed_patterns, feedback_json, weight_snapshot
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(draw_no, brain_tag) DO UPDATE SET
                    predicted_nums=excluded.predicted_nums,
                    predicted_sets_json=excluded.predicted_sets_json,
                    best_set_no=excluded.best_set_no,
                    matched_count=excluded.matched_count,
                    bonus_matched=excluded.bonus_matched,
                    missed_patterns=excluded.missed_patterns,
                    feedback_json=excluded.feedback_json,
                    weight_snapshot=excluded.weight_snapshot
                """,
                tuple(bak_d.get(c) for c in cols),
            )
            conn.commit()
            checks["unit_restored"] = True
        else:
            conn.execute(
                "DELETE FROM testlotto_brain_review WHERE draw_no=? AND brain_tag=? AND feedback_json LIKE ?",
                (dno, "stat", "%L9b_unit_probe%"),
            )
            conn.commit()
            checks["unit_restored"] = True
    finally:
        conn.close()
    invalidate_learn_cutoff_cache()

    # 2) click 경로 (예측 없으면 skip · 있으면 3뇌 미러)
    fb = apply_draw_result_feedback(dno)
    detail["click_feedback"] = {
        "ok": fb.get("ok"),
        "skipped": fb.get("skipped"),
        "brains": {
            k: {
                "status": v.get("status"),
                "brain_review": v.get("brain_review"),
                "matched_count": v.get("matched_count"),
            }
            for k, v in (fb.get("brains") or {}).items()
        },
    }
    brains = fb.get("brains") or {}
    if fb.get("skipped") == "no_predictions":
        checks["click_path_ran"] = True
        checks["click_has_preds"] = False
    else:
        checks["click_path_ran"] = bool(fb.get("ok") or fb.get("skipped"))
        checks["click_has_preds"] = bool(brains)
        # 예측이 있으면 각 뇌에 brain_review 키
        if brains:
            checks["click_mirror_keys"] = all(
                "brain_review" in v or v.get("status") == "no_brain_preds"
                for v in brains.values()
            )

    # 3) census
    conn = get_lotto_db()
    try:
        n_review = conn.execute("SELECT COUNT(*) FROM testlotto_brain_review").fetchone()[0]
        by_tag = dict(
            conn.execute(
                "SELECT brain_tag, COUNT(*) FROM testlotto_brain_review GROUP BY brain_tag"
            ).fetchall()
        )
        n_pred = conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0]
        max_pred = conn.execute(
            "SELECT MAX(target_draw_no) FROM lotto_predictions"
        ).fetchone()[0]
        # 모듈 import 경로
        import inspect
        from app.testlotto import click_feedback as cf
        from app.testlotto.brains import coordinator as coord

        checks["wired_click"] = "upsert_brain_review_feedback" in inspect.getsource(
            cf.apply_draw_result_feedback
        )
        checks["wired_auto"] = "upsert_brain_review_feedback" in inspect.getsource(
            coord._auto_feedback
        )
    finally:
        conn.close()

    detail["census"] = {
        "brain_review_n": n_review,
        "brain_review_by_tag": by_tag,
        "predictions_n": n_pred,
        "predictions_max_target": max_pred,
    }

    conn = get_lotto_db()
    try:
        row = conn.execute(
            "SELECT feedback_json FROM testlotto_brain_review WHERE draw_no=? AND brain_tag=?",
            (dno, "stat"),
        ).fetchone()
        src = json.loads(row["feedback_json"] or "{}").get("source") if row else None
        detail["stat_1236_source_after"] = src
        checks["no_unit_probe_residue"] = src != "L9b_unit_probe"
    finally:
        conn.close()

    hard = [
        "unit_upsert",
        "cache_invalidated",
        "unit_restored",
        "no_unit_probe_residue",
        "wired_click",
        "wired_auto",
        "click_path_ran",
    ]
    if checks.get("click_has_preds"):
        hard.append("click_mirror_keys")
    hard_ok = all(checks.get(k) for k in hard)
    verdict = "WIRE_OK" if hard_ok else "FAIL"

    payload = {
        "id": "K-LIVE-FEEDBACK-REVIEW-MIRROR",
        "list": "LIST_V3 L9b",
        "verdict": verdict,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "sample_draw": dno,
        "checks": checks,
        "hard_keys": hard,
        "detail": detail,
        "notes": [
            "learn_state last_draw guard 와 무관하게 brain_review UPSERT",
            "CUTOFF 재생 SSOT = testlotto_brain_review",
            "ge3 미클레임 · 1237 아님 · 강제BT 보류",
        ],
    }
    BENCH.parent.mkdir(parents=True, exist_ok=True)
    BENCH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# K-LIVE-FEEDBACK-REVIEW-MIRROR — LIST_V3 L9b",
        "",
        f"판정: **{verdict}** · sample={dno}",
        "",
        "## HARD checks",
        "",
    ]
    for k in hard:
        lines.append(f"- `{k}`: **{checks.get(k)}**")
    lines += [
        "",
        "## 기타",
        "",
        f"- unit_row_source: {checks.get('unit_row_source')}",
        f"- no_unit_probe_residue: {checks.get('no_unit_probe_residue')}",
        f"- census: `{json.dumps(detail.get('census'), ensure_ascii=False)}`",
        f"- click: `{json.dumps(detail.get('click_feedback'), ensure_ascii=False)}`",
        "",
        "## 배선",
        "",
        "- `app/testlotto/brain_review_mirror.py`",
        "- `click_feedback.apply_draw_result_feedback`",
        "- `coordinator._auto_feedback`",
        "",
        f"벤치: `{BENCH.relative_to(ROOT).as_posix()}`",
        "",
        "다음: **L9c** K-SKILL-HOMEWORK-PERSIST (스킬별 숙제 테이블 persist)",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
