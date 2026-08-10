# -*- coding: utf-8 -*-
"""K-1236-FEEDBACK-VERIFY — 1236 실전 피드백 경로 검증 (wire=False · 성적클레임 금지)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260810_K1236_FEEDBACK_VERIFY.json"
OUT_MD = ROOT / "reports" / "20260810_K1236_FEEDBACK_VERIFY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def _draw_1236() -> dict[str, Any]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        r = conn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6,bonus,first_winners "
            "FROM lotto_draws WHERE draw_no=1236"
        ).fetchone()
        if not r:
            return {
                "draw_no": 1236,
                "numbers": [],
                "bonus": None,
                "first_winners": None,
                "in_db": False,
            }
        nums = [int(r[f"num{k}"]) for k in range(1, 7)]
        return {
            "draw_no": 1236,
            "numbers": nums,
            "bonus": int(r["bonus"]),
            "first_winners": int(r["first_winners"] or 0),
            "in_db": True,
        }
    finally:
        conn.close()


def _pred_count_1236() -> int:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1236"
            ).fetchone()[0]
        )
    finally:
        conn.close()


def _brain_pred_counts() -> dict[str, int]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT brain_tag, COUNT(1) FROM lotto_predictions "
            "WHERE target_draw_no=1236 GROUP BY brain_tag"
        ).fetchall()
        return {str(r[0]): int(r[1]) for r in rows}
    finally:
        conn.close()


def _ensure_predictions() -> dict[str, Any]:
    """발권 전제. draws는 target 이전만(_get_draws_before) · 1236 번호 미사용.

    통합 발권은 dynamic_quota 로 뇌가 0장일 수 있음(실측: stat 0).
    피드백 3뇌 검증을 위해 빠진 뇌만 brain_filter 로 보충(숙제채우기와 동일 패턴).
    """
    from app.testlotto.engine import run_prediction

    counts0 = _brain_pred_counts()
    ran: list[str] = []
    if not counts0:
        run_prediction(1236)
        ran.append("all")
        counts0 = _brain_pred_counts()

    for tag in ("stat", "markov", "review"):
        if counts0.get(tag, 0) <= 0:
            run_prediction(1236, brain_filter=(tag,))
            ran.append(tag)
            counts0 = _brain_pred_counts()

    n1 = _pred_count_1236()
    return {
        "ran_predict": bool(ran),
        "ran_modes": ran,
        "pred_count": n1,
        "by_brain": counts0,
        "predict_ok": all(counts0.get(t, 0) > 0 for t in ("stat", "markov", "review")),
        "note": "quota로 빠진 뇌는 brain_filter 보충 · 힌트 역산 없음",
    }


def _read_evolve_brains() -> dict[str, dict[str, Any]]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT brain_tag, mean_hits, best_hits, weight_applied, note "
            "FROM testlotto_evolve_log WHERE draw_no=1236"
        ).fetchall()
        out: dict[str, dict[str, Any]] = {}
        for r in rows:
            tag = str(r["brain_tag"])
            note = str(r["note"] or "")
            out[tag] = {
                "mean_hits": float(r["mean_hits"] or 0),
                "best_hits": float(r["best_hits"] or 0),
                "weight_applied": float(r["weight_applied"] or 0),
                "ok": "K-KK-FEEDBACK" in note and float(r["weight_applied"] or 0) == 0.0,
                "note_has_kk": "K-KK-FEEDBACK" in note,
            }
        return out
    finally:
        conn.close()


def _clear_kk_mark_1236() -> None:
    """재검증용: 1236 note의 K-KK-FEEDBACK 마크만 제거(행·pool 유지)."""
    from app.testlotto.click_feedback import FEEDBACK_NOTE_TAG
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT brain_tag, note FROM testlotto_evolve_log WHERE draw_no=1236"
        ).fetchall()
        for r in rows:
            note = str(r["note"] or "")
            if FEEDBACK_NOTE_TAG not in note:
                continue
            parts = [p for p in note.split(" | ") if FEEDBACK_NOTE_TAG not in p]
            conn.execute(
                "UPDATE testlotto_evolve_log SET note=? WHERE draw_no=1236 AND brain_tag=?",
                (" | ".join(parts), r["brain_tag"]),
            )
        conn.commit()
    finally:
        conn.close()


def _feedback_1236() -> tuple[dict[str, Any], dict[str, Any]]:
    from app.testlotto.click_feedback import (
        apply_draw_result_feedback,
        apply_feedback_after_predict,
    )

    # API 의미: after_predict(N) → feedback(N-1). 1236 채점은 draw_result(1236)
    # ≡ after_predict(1237). 지시서의 after_predict(1236)은 1235를 치므로 병행 기록.
    after_predict_call = apply_feedback_after_predict(1236)
    _clear_kk_mark_1236()
    primary = apply_draw_result_feedback(1236)
    dup = apply_draw_result_feedback(1236)

    brains = _read_evolve_brains()
    feedback = {
        "stat": brains.get(
            "stat",
            {"mean_hits": None, "best_hits": None, "weight_applied": None, "ok": False},
        ),
        "markov": brains.get(
            "markov",
            {"mean_hits": None, "best_hits": None, "weight_applied": None, "ok": False},
        ),
        "review": brains.get(
            "review",
            {"mean_hits": None, "best_hits": None, "weight_applied": None, "ok": False},
        ),
        "duplicate_skip_ok": bool(
            dup.get("skipped") == "all_brains_duplicate_or_empty"
            or all(
                (dup.get("brains") or {}).get(t, {}).get("status")
                == "skip_duplicate_evolve"
                for t in ("stat", "markov", "review")
            )
        ),
        "api_note": (
            "apply_feedback_after_predict(1236)→draw 1235; "
            "1236 채점=apply_draw_result_feedback(1236)≡after_predict(1237)"
        ),
        "after_predict_1236_target_draw": after_predict_call.get("draw_no"),
        "after_predict_1236_skipped": after_predict_call.get("skipped"),
        "primary_call": {
            "ok": primary.get("ok"),
            "skipped": primary.get("skipped"),
            "brains": {
                t: (primary.get("brains") or {}).get(t, {}).get("status")
                for t in ("stat", "markov", "review")
            },
        },
    }
    return feedback, {"primary": primary, "dup": dup, "after_predict_1236": after_predict_call}


def _ev_check(actual: list[int]) -> dict[str, Any]:
    """힌트는 draws_before(1236)만 — 1236 당첨번호로 힌트 재조정 금지."""
    from app.testlotto.data_service import _get_draws_before
    import app.testlotto.signal_pool as sp

    draws = _get_draws_before(1236)
    hints = sp.build_hint_by_brain(draws, 1236)
    actual_set = set(int(x) for x in actual)

    def top15(tag: str) -> list[int]:
        h = hints.get(tag) or {}
        return sorted(range(1, 46), key=lambda n: (-float(h.get(n, 0.0)), n))[:15]

    rev = top15("review")
    mar = top15("markov")
    return {
        "review_hint_top15": rev,
        "markov_hint_top15": mar,
        "actual_1236": list(actual),
        "review_hits_in_top15": len(actual_set & set(rev)),
        "markov_hits_in_top15": len(actual_set & set(mar)),
        "first_winners_1236": None,  # filled by caller
        "note": "단건 방향 참고 · 통계 클레임 금지",
    }


def main() -> int:
    draw = _draw_1236()
    if not draw["in_db"]:
        payload = {
            "id": "K-1236-FEEDBACK-VERIFY",
            "draw_1236": draw,
            "verdict": "FAIL",
            "reason": "draw_1236 not in lotto_draws",
            "wire": False,
            "ge3_used": False,
        }
        OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2

    pred_info = _ensure_predictions()
    print("PRED", pred_info)

    feedback, raw = _feedback_1236()
    print("FEEDBACK", json.dumps(feedback, ensure_ascii=False, indent=2))

    score = {
        "stat_mean_hits": feedback["stat"].get("mean_hits"),
        "markov_mean_hits": feedback["markov"].get("mean_hits"),
        "review_mean_hits": feedback["review"].get("mean_hits"),
        "baseline": 0.8,
        "note": "단건 참고값 · 서열화 불가",
    }

    ev = _ev_check(draw["numbers"])
    ev["first_winners_1236"] = draw["first_winners"]

    all_ok = all(feedback[t].get("ok") for t in ("stat", "markov", "review"))
    w0 = all(
        feedback[t].get("weight_applied") == 0.0 for t in ("stat", "markov", "review")
    )
    if all_ok and w0 and feedback["duplicate_skip_ok"]:
        verdict = "VERIFY_OK"
    elif any(feedback[t].get("ok") for t in ("stat", "markov", "review")):
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    opinion = (
        "1236 경로 실전 확인됨(발권→feedback→evolve마크·weight0·중복SKIP). "
        "단건 mean/hint적중은 참고만·서열화 금지. "
        "K-N-MEAN-INPUT-FIX **바로 진행 가능**(피드백 입력이 살아 있음이 전제)."
        if verdict == "VERIFY_OK"
        else "경로 미완 — 추가 패치 후 K-N."
    )

    payload = {
        "id": "K-1236-FEEDBACK-VERIFY",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "draw_1236": draw,
        "predict_prerequisite": pred_info,
        "feedback_1236": {
            k: feedback[k]
            for k in (
                "stat",
                "markov",
                "review",
                "duplicate_skip_ok",
            )
        },
        "feedback_1236_meta": {
            "api_note": feedback["api_note"],
            "after_predict_1236_target_draw": feedback["after_predict_1236_target_draw"],
            "primary_call": feedback["primary_call"],
        },
        "score_1236": score,
        "ev_check_1236": ev,
        "verdict": verdict,
        "next_step": "K-N-MEAN-INPUT-FIX",
        "cursor_opinion": opinion,
        "wire": False,
        "ge3_used": False,
        "no_peek": True,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = f"""# K-1236-FEEDBACK-VERIFY

📅 2026-08-10 KST · wire=**False** · ge3=미사용 · 단건 서열화 금지

## 판정: **{verdict}**

## STEP0 draw_1236
- numbers: **{draw['numbers']}**
- bonus: **{draw['bonus']}**
- first_winners: **{draw['first_winners']}**
- in_db: {draw['in_db']}

## 발권 전제
예측이 없어 `run_prediction(1236)` 실행(재료=`_get_draws_before(1236)` · 1236 번호 미사용).  
pred_count={pred_info.get('pred_count')} · ran={pred_info.get('ran_predict')}

## API 주의
`apply_feedback_after_predict(1236)` → **1235** 채점.  
1236 채점 = `apply_draw_result_feedback(1236)` ≡ `after_predict(1237)`.

## feedback_1236
| brain | mean_hits | best_hits | weight | ok |
|-------|----------:|----------:|-------:|:--:|
| stat | {feedback['stat'].get('mean_hits')} | {feedback['stat'].get('best_hits')} | {feedback['stat'].get('weight_applied')} | {feedback['stat'].get('ok')} |
| markov | {feedback['markov'].get('mean_hits')} | {feedback['markov'].get('best_hits')} | {feedback['markov'].get('weight_applied')} | {feedback['markov'].get('ok')} |
| review | {feedback['review'].get('mean_hits')} | {feedback['review'].get('best_hits')} | {feedback['review'].get('weight_applied')} | {feedback['review'].get('ok')} |

duplicate_skip_ok={feedback['duplicate_skip_ok']}

## score_1236 (단건 참고 · 서열화 불가)
baseline E[hits]=0.8 · stat={score['stat_mean_hits']} · markov={score['markov_mean_hits']} · review={score['review_mean_hits']}

## ev_check_1236 (단건 방향 · 통계 클레임 금지)
- review top15 ∩ actual = **{ev['review_hits_in_top15']}** /6
- markov top15 ∩ actual = **{ev['markov_hits_in_top15']}** /6
- review_hint_top15: {ev['review_hint_top15']}
- markov_hint_top15: {ev['markov_hint_top15']}
- first_winners: {ev['first_winners_1236']}

## 다음
**{payload['next_step']}**

## 커서 의견
{opinion}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict)
    return 0 if verdict == "VERIFY_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
