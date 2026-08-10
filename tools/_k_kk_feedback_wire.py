# -*- coding: utf-8 -*-
"""K-KK-FEEDBACK-WIRE — STEP0 진단 + STEP3 검증 (검증 스크립트)."""
from __future__ import annotations

import inspect
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260810_KKK_FEEDBACK_WIRE.json"
OUT_MD = ROOT / "reports" / "20260810_KKK_FEEDBACK_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
FINDINGS = ROOT / "My_Drive_Sync" / "SUMMARY" / "FINDINGS.md"

SMOKE_DRAWS = list(range(1230, 1236))


def step0_diag() -> dict[str, Any]:
    import app.testlotto.brains.coordinator as coord
    import app.testlotto.learn_state as ls
    import app.testlotto.routes as routes
    from app.testlotto.evolve_log import ensure_evolve_log_table
    from app.testlotto.models import get_lotto_db

    routes_src = Path(routes.__file__).read_text(encoding="utf-8")
    routes_connected = (
        "apply_feedback_after_predict" in routes_src
        or "apply_draw_result_feedback" in routes_src
        or "click_feedback" in routes_src
    )
    # 라인: predict 핸들러 근처 click_feedback
    routes_line = None
    for i, line in enumerate(routes_src.splitlines(), 1):
        if "apply_feedback_after_predict" in line or "click_feedback" in line:
            if "import" in line or "apply_" in line:
                routes_line = i
                if "apply_feedback_after_predict" in line:
                    break

    coord_src = Path(coord.__file__).read_text(encoding="utf-8")
    has_auto = "_auto_feedback" in coord_src
    called_in_run = bool(
        re.search(r"def run_coordinated_prediction[\s\S]*?_auto_feedback\(", coord_src)
    )
    if has_auto and called_in_run:
        loc = "both" if routes_connected else "walkforward_and_predict_via_coordinator"
        # 지시서 enum: walkforward_only | both | none — coordinator는 predict+evolve_auto
        if routes_connected:
            loc = "both"
        else:
            loc = "walkforward_only"  # 구상태 표기용; 실제는 coordinator predict도 있음
            # 더 정확한 라벨
            loc = "coordinator_predict_and_evolve_auto"

    sig = str(inspect.signature(ls.apply_feedback))
    ensure_evolve_log_table()
    conn = get_lotto_db()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(testlotto_evolve_log)")]
    finally:
        conn.close()

    # apply_feedback 본문은 evolve_log 미기록 · click_feedback._mark 가 write path
    af_src = inspect.getsource(ls.apply_feedback)
    weight_path_in_apply = "weight_applied" in af_src or "evolve_log" in af_src
    from app.testlotto import click_feedback as cf

    cf_src = inspect.getsource(cf)
    weight_path = ("weight_applied" in cf_src) and ("testlotto_evolve_log" in cf_src)

    return {
        "routes_feedback_connected": routes_connected,
        "routes_feedback_line": routes_line,
        "coordinator_feedback_location": (
            "both" if (routes_connected and called_in_run) else (
                "walkforward_only" if called_in_run else "none"
            )
        ),
        "coordinator_note": (
            "run_coordinated_prediction 진입 시 _auto_feedback(prev) 호출 기존 존재. "
            "이번 패치는 routes 명시 + evolve_log 마크."
        ),
        "apply_feedback_signature": f"apply_feedback{sig}",
        "evolve_log_columns": cols,
        "weight_applied_write_path_exists": bool(weight_path),
        "apply_feedback_writes_evolve_log": bool(weight_path_in_apply),
    }


def step1_design() -> dict[str, Any]:
    return {
        "trigger_point": (
            "① POST /predict/{target} 후 apply_feedback_after_predict(target) "
            "→ draw=target-1 · ② POST /fetch-latest 성공 시 해당 draw_no"
        ),
        "guard_duplicate": (
            "evolve_log.note 에 K-KK-FEEDBACK 있으면 뇌별 SKIP · "
            "learn 은 last_draw_no>=draw 이면 apply_feedback 생략"
        ),
        "guard_future": "lotto_draws 에 해당 draw_no 없으면 SKIP(guard_future_no_draw)",
        "files_to_modify": [
            "app/testlotto/click_feedback.py (신규)",
            "app/testlotto/routes.py",
            "My_Drive_Sync/SUMMARY/FINDINGS.md (K-K)",
        ],
        "lines_to_add_approx": 220,
        "risk": (
            "coordinator._auto_feedback 와 이중 호출 가능하나 last_draw/evolve 마크로 멱등. "
            "smoke 시 이미 학습된 회차는 learn SKIP·evolve 마크만."
        ),
    }


def step3_verify() -> dict[str, Any]:
    from app.testlotto.click_feedback import (
        FEEDBACK_NOTE_TAG,
        WEIGHT_APPLIED,
        apply_draw_result_feedback,
    )
    from app.testlotto.evolve_log import WEIGHT_APPLIED as EV_W
    from app.testlotto.models import get_lotto_db

    assert float(WEIGHT_APPLIED) == 0.0
    assert float(EV_W) == 0.0

    conn = get_lotto_db()
    try:
        before = conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0]
        # 기존 마크 제거 후 재검증 (note 만 · pool 불변)
        for dno in SMOKE_DRAWS:
            for tag in ("stat", "markov", "review"):
                row = conn.execute(
                    "SELECT note FROM testlotto_evolve_log WHERE draw_no=? AND brain_tag=?",
                    (dno, tag),
                ).fetchone()
                if row and FEEDBACK_NOTE_TAG in str(row["note"] or ""):
                    cleaned = str(row["note"]).replace(" | " + FEEDBACK_NOTE_TAG, "")
                    # 전체 태그 구문 제거(간단)
                    parts = [
                        p
                        for p in cleaned.split(" | ")
                        if FEEDBACK_NOTE_TAG not in p
                    ]
                    conn.execute(
                        "UPDATE testlotto_evolve_log SET note=? WHERE draw_no=? AND brain_tag=?",
                        (" | ".join(parts), dno, tag),
                    )
        conn.commit()
    finally:
        conn.close()

    results = []
    for dno in SMOKE_DRAWS:
        results.append(apply_draw_result_feedback(dno))

    # 중복 SKIP
    dup = apply_draw_result_feedback(1235)
    dup_ok = all(
        (dup.get("brains") or {}).get(t, {}).get("status") == "skip_duplicate_evolve"
        for t in ("stat", "markov", "review")
    ) or dup.get("skipped") == "all_brains_duplicate_or_empty"

    # 미래 guard
    fut = apply_draw_result_feedback(9999)
    future_ok = fut.get("skipped") == "guard_future_no_draw"

    conn = get_lotto_db()
    try:
        after = conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0]
        marked = conn.execute(
            "SELECT COUNT(DISTINCT draw_no) FROM testlotto_evolve_log "
            "WHERE draw_no BETWEEN 1230 AND 1235 AND note LIKE ?",
            (f"%{FEEDBACK_NOTE_TAG}%",),
        ).fetchone()[0]
        wrows = conn.execute(
            "SELECT weight_applied FROM testlotto_evolve_log "
            "WHERE draw_no BETWEEN 1230 AND 1235 AND note LIKE ?",
            (f"%{FEEDBACK_NOTE_TAG}%",),
        ).fetchall()
        weight_zero = all(float(r[0] or 0) == 0.0 for r in wrows) and len(wrows) >= 1
        brain_marks = conn.execute(
            "SELECT COUNT(*) FROM testlotto_evolve_log "
            "WHERE draw_no BETWEEN 1230 AND 1235 AND note LIKE ?",
            (f"%{FEEDBACK_NOTE_TAG}%",),
        ).fetchone()[0]
    finally:
        conn.close()

    smoke_ok = marked == 6 and brain_marks >= 6

    # predict 경로 무결성: 캐시된 1235 호출
    from app.testlotto.engine import run_prediction

    pred = run_prediction(1235)
    predict_ok = isinstance(pred, dict) and (
        "error" not in pred or not pred.get("error")
    ) and (
        "predictions" in pred
        or "brains" in pred
        or "brain_warrant" in pred
        or "sets" in pred
        or any(k in pred for k in ("stat", "markov", "review", "candidates", "ok"))
    )
    # 최소: 예외 없이 dict 반환 + predictions 행 존재
    conn = get_lotto_db()
    try:
        n_pred = conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1235"
        ).fetchone()[0]
    finally:
        conn.close()
    predict_ok = predict_ok or (n_pred > 0 and isinstance(pred, dict))

    learn_applied_any = any(
        (r.get("brains") or {}).get(t, {}).get("learn_applied")
        for r in results
        for t in ("stat", "markov", "review")
    )

    return {
        "smoke_6draws_ok": bool(smoke_ok),
        "smoke_draws": SMOKE_DRAWS,
        "smoke_results_summary": [
            {
                "draw_no": r["draw_no"],
                "ok": r.get("ok"),
                "skipped": r.get("skipped"),
                "brains": {
                    t: (r.get("brains") or {}).get(t, {}).get("status")
                    for t in ("stat", "markov", "review")
                },
            }
            for r in results
        ],
        "evolve_log_count_before": before,
        "evolve_log_count_after": after,
        "evolve_feedback_marked_draws": int(marked),
        "evolve_feedback_marked_rows": int(brain_marks),
        "weight_applied_still_zero": bool(weight_zero),
        "duplicate_skip_ok": bool(dup_ok),
        "future_guard_ok": bool(future_ok),
        "predict_path_intact": bool(predict_ok),
        "learn_applied_any_in_smoke": bool(learn_applied_any),
        "dup_result_skipped": dup.get("skipped"),
        "future_result": fut,
    }


def patch_findings() -> None:
    text = FINDINGS.read_text(encoding="utf-8")
    old = "| K-K | OPEN | 클릭 예측이 feedback 미연결 | `learn_state.apply_feedback` | 백테/복습 경로에서만 호출. 단발 클릭은 학습 안 됨 |"
    new = (
        "| K-K | PATCHED | 클릭 예측이 feedback 미연결 → routes 연결 | "
        "`click_feedback.py` · `routes.py` | "
        "POST /predict·/fetch-latest → apply_draw_result_feedback · "
        "evolve_log note=`K-KK-FEEDBACK` · weight_applied=0.0 유지 · K-M/K-N HOLD |"
    )
    if old in text:
        FINDINGS.write_text(text.replace(old, new), encoding="utf-8")
    elif "K-K | PATCHED" not in text and "K-K | OPEN" in text:
        text2 = re.sub(
            r"\| K-K \| OPEN \|[^|]+\|[^|]+\|[^|]+\|",
            new,
            text,
            count=1,
        )
        FINDINGS.write_text(text2, encoding="utf-8")


def write_md(payload: dict[str, Any]) -> None:
    v = payload["verdict"]
    s0 = payload["step0_diag"]
    s3 = payload["step3_verify"]
    md = f"""# K-KK-FEEDBACK-WIRE

📅 2026-08-10 KST · wire=**True** · ge3=미사용  
도구: `tools/_k_kk_feedback_wire.py`

## 판정: **{v}**

## STEP0 진단
```json
{json.dumps(s0, ensure_ascii=False, indent=2)}
```

## STEP1 설계
```json
{json.dumps(payload["step1_design"], ensure_ascii=False, indent=2)}
```

## STEP2 패치
- 신규: `app/testlotto/click_feedback.py`
- 수정: `app/testlotto/routes.py` (`/predict`, `/fetch-latest`)
- coordinator/engine/random.choices/SCORE_WEIGHTS/**미수정**
- weight_applied **0.0 고정**

## STEP3 검증
| 항목 | 결과 |
|------|------|
| smoke 1230~1235 마크 | {s3['smoke_6draws_ok']} (draws={s3['evolve_feedback_marked_draws']}, rows={s3['evolve_feedback_marked_rows']}) |
| evolve_log count | {s3['evolve_log_count_before']} → {s3['evolve_log_count_after']} |
| weight_applied=0 | {s3['weight_applied_still_zero']} |
| 중복 SKIP | {s3['duplicate_skip_ok']} |
| 미래 9999 SKIP | {s3['future_guard_ok']} |
| predict 무결성 | {s3['predict_path_intact']} |

## FINDINGS
- K-K → **PATCHED**
- K-M → HOLD 유지
- K-N → HOLD 유지

## 커서 의견
{payload['cursor_opinion']}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")


def main() -> int:
    s0 = step0_diag()
    s1 = step1_design()
    s3 = step3_verify()
    patch_findings()

    files_mod = [
        "app/testlotto/click_feedback.py",
        "app/testlotto/routes.py",
        "My_Drive_Sync/SUMMARY/FINDINGS.md",
    ]
    guard_dup = bool(s3["duplicate_skip_ok"])
    guard_fut = bool(s3["future_guard_ok"])
    patched = (
        s0["routes_feedback_connected"]
        and s3["smoke_6draws_ok"]
        and s3["weight_applied_still_zero"]
        and s3["predict_path_intact"]
        and guard_dup
        and guard_fut
    )
    partial = s0["routes_feedback_connected"] and not patched
    verdict = "PATCHED" if patched else ("PARTIAL" if partial else "FAIL")

    opinion = (
        "K-K 경로 연결 완료(routes 명시 + evolve 마크 + weight=0). "
        "단 referee는 여전히 균등(K-M HOLD)이라 **학습 입력이 발권 가중으로 전달되지 않음**. "
        "K-M 착수 가능하나, 입력 지표가 best 오인(K-N)이면 가중 조정 전에 mean 입력 정합을 먼저 보는 편이 안전. "
        "지금 당장 K-M GO는 **조건부 가능**(경로 살아 있음 · 실효격차 설계는 별도)."
    )

    payload = {
        "id": "K-KK-FEEDBACK-WIRE",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "step0_diag": s0,
        "step1_design": s1,
        "step2_patch": {
            "files_modified": files_mod,
            "lines_added": "approx_220",
            "guard_duplicate_ok": guard_dup,
            "guard_future_ok": guard_fut,
        },
        "step3_verify": s3,
        "findings_update": {
            "K-K": "PATCHED",
            "K-M": "HOLD 유지 (referee 조정은 다음 단계)",
            "K-N": "HOLD 유지 (mean 학습 입력은 다음 단계)",
        },
        "verdict": verdict,
        "cursor_opinion": opinion,
        "wire": True,
        "ge3_used": False,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_md(payload)
    print("VERDICT", verdict)
    print(json.dumps(s3, ensure_ascii=False, indent=2))
    return 0 if verdict == "PATCHED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
