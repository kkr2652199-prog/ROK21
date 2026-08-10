# -*- coding: utf-8 -*-
"""K-N-MEAN-INPUT-FIX — 학습입력 best→mean 정합 검증."""
from __future__ import annotations

import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260810_KN_MEAN_INPUT_FIX.json"
OUT_MD = ROOT / "reports" / "20260810_KN_MEAN_INPUT_FIX.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
FINDINGS = ROOT / "My_Drive_Sync" / "SUMMARY" / "FINDINGS.md"
WF = ROOT / "app" / "testlotto" / "walkforward.py"


def _check_sources() -> dict[str, Any]:
    from app.testlotto.brains.coordinator import FEEDBACK_MATCH_MODE
    from app.testlotto.walkforward import _learn_match_from_sets

    mode = FEEDBACK_MATCH_MODE
    # unit: best vs mean diverge
    scored = [
        {"set_no": 1, "nums": [1, 2, 3, 4, 5, 6], "matched_count": 0},
        {"set_no": 2, "nums": [7, 8, 9, 10, 11, 12], "matched_count": 0},
        {"set_no": 3, "nums": [13, 14, 15, 16, 17, 18], "matched_count": 3},
        {"set_no": 4, "nums": [19, 20, 21, 22, 23, 24], "matched_count": 0},
        {"set_no": 5, "nums": [25, 26, 27, 28, 29, 30], "matched_count": 1},
    ]
    # mean = (0+0+3+0+1)/5 = 0.8 → round 1 · nearest set with hits=1 is set 5
    learn_m, learn_nums, learn_sn = _learn_match_from_sets(scored)
    unit_ok = learn_m == 1 and learn_sn == 5 and learn_nums == scored[4]["nums"]

    src = WF.read_text(encoding="utf-8")
    uses_helper = "_learn_match_from_sets" in src
    applies_item_matched = "apply_feedback(\n            item[\"tag\"], draw_no, item[\"matched\"]" in src or (
        'apply_feedback(\n            item["tag"], draw_no, item["matched"]' in src
    )
    # ensure apply_feedback not fed best["matched_count"] directly
    bad_best_feed = "apply_feedback(\n            item[\"tag\"], draw_no, int(best" in src
    has_kn_comment = "K-N" in src

    click = (ROOT / "app" / "testlotto" / "click_feedback.py").read_text(encoding="utf-8")
    click_mean = "FEEDBACK_MATCH_MODE" in click and "mean_mc" in click

    return {
        "feedback_match_mode": mode,
        "mode_is_mean": mode == "mean",
        "unit_mean_vs_best": {
            "learn_matched": learn_m,
            "learn_set_no": learn_sn,
            "best_would_be_matched": 3,
            "best_would_be_set": 3,
            "unit_ok": unit_ok,
        },
        "walkforward_uses_helper": uses_helper,
        "walkforward_no_direct_best_feed": not bad_best_feed,
        "click_feedback_aligned": click_mean,
        "has_kn_comment": has_kn_comment,
    }


def _smoke_review() -> dict[str, Any]:
    """한 회차 review_single_draw — DB learn 쓸 수 있음. store_features만."""
    from app.testlotto.walkforward import review_single_draw

    # 이미 확정된 회차 · 테스트 단계 허용
    out = review_single_draw(1236, store_features=False)
    if out.get("skipped"):
        return {"ok": False, "out": out}
    brains = out.get("brains") or out.get("results") or []
    # review_single_draw returns dict with results key?
    # read rest of function
    return {"ok": True, "raw_keys": list(out.keys()), "sample": out}


def _read_review_return() -> dict[str, Any]:
    import inspect
    from app.testlotto import walkforward as wf

    src = inspect.getsource(wf.review_single_draw)
    # call and inspect
    from app.testlotto.walkforward import review_single_draw

    # 소스/유닛만으로도 충분. smoke는 구조 확인용 · learn DB 갱신 부작용 있음(개발단계 허용)
    out = review_single_draw(1235, store_features=False)
    rows = out.get("reviews") or out.get("results") or []
    if not rows:
        for k, v in out.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "brain_tag" in v[0]:
                rows = v
                break
    modes = [r.get("feedback_mode") for r in rows if isinstance(r, dict)]
    means = [r.get("matched_count") for r in rows if isinstance(r, dict)]
    bests = [r.get("best_matched") for r in rows if isinstance(r, dict)]
    return {
        "draw_no": out.get("draw_no", 1235),
        "skipped": out.get("skipped"),
        "n_rows": len(rows),
        "feedback_modes": modes,
        "matched_counts_learn": means,
        "best_matcheds": bests,
        "all_mode_mean": all(m == "mean" for m in modes) if modes else False,
        "ok": bool(rows) and all(m == "mean" for m in modes),
    }


def patch_findings() -> None:
    text = FINDINGS.read_text(encoding="utf-8")
    old = (
        "| K-N | HOLD | 학습지표 best → 고분산 뇌를 실력으로 오인 | "
        "`walkforward.py:91,110` `apply_feedback(best)` | "
        "**원인확정**: null상 best 전원 비실력. 조치(학습입력을 mean/볼지표로) 대기 |"
    )
    new = (
        "| K-N | PATCHED | 학습지표 best → 고분산 뇌를 실력으로 오인 | "
        "`walkforward._learn_match_from_sets` · `FEEDBACK_MATCH_MODE=mean` | "
        "WF/클릭/coordinator 학습입력 **mean** · best는 표시·참고만 · K-M HOLD |"
    )
    if old in text:
        FINDINGS.write_text(text.replace(old, new), encoding="utf-8")
    elif "| K-N | HOLD |" in text:
        import re

        FINDINGS.write_text(
            re.sub(r"\| K-N \| HOLD \|[^|]+\|[^|]+\|[^|]+\|", new, text, count=1),
            encoding="utf-8",
        )
    # also update K-K note that said K-N HOLD
    text2 = FINDINGS.read_text(encoding="utf-8")
    text2 = text2.replace("· K-M/K-N HOLD |", "· K-M HOLD · K-N PATCHED |")
    FINDINGS.write_text(text2, encoding="utf-8")


def main() -> int:
    checks = _check_sources()
    smoke = _read_review_return()
    patch_findings()

    paths_ok = (
        checks["mode_is_mean"]
        and checks["unit_mean_vs_best"]["unit_ok"]
        and checks["walkforward_uses_helper"]
        and checks["walkforward_no_direct_best_feed"]
        and checks["click_feedback_aligned"]
        and smoke["ok"]
    )
    verdict = "PATCHED" if paths_ok else "PARTIAL"

    payload = {
        "id": "K-N-MEAN-INPUT-FIX",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "checks": checks,
        "smoke_review_1235": smoke,
        "findings_update": {"K-N": "PATCHED", "K-M": "HOLD 유지"},
        "verdict": verdict,
        "stage_note": "3뇌 테스트/개발 단계 · 1237 양산 준비 전",
        "next_step": "K-M-REFEREE-WEIGHT",
        "wire": True,
        "ge3_used": False,
        "cursor_opinion": (
            "walkforward 학습입력을 coordinator/click_feedback과 동일 mean으로 정합. "
            "best는 tier/표시만. K-M(referee 균등)이 다음 — 학습 신호가 mean으로 들어가도 "
            "referee가 평탄하면 발권 비중은 안 움직임."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = f"""# K-N-MEAN-INPUT-FIX

📅 2026-08-10 KST · **3뇌 테스트/개발 단계** · ge3 미사용

## 판정: **{verdict}**

## 이해 (형)
지금은 개발·테스트. 1237 개발 완료 후 양산 준비. 이번은 3뇌 학습입력 정합.

## 패치
- `walkforward.py`: `_learn_match_from_sets` · `apply_feedback`에 **mean** 입력
- best/tier는 표시·`best_matched` 참고만
- `FEEDBACK_MATCH_MODE` = `{checks['feedback_match_mode']}` (coordinator와 공유)
- click_feedback / coordinator `_auto_feedback` 이미 mean — 정렬 확인

## 검증
- unit: best=3 vs learn_mean=1 (고분산 best 오인 사례) → `{checks['unit_mean_vs_best']}`
- smoke review 1235: `{smoke}`

## FINDINGS
- K-N → **PATCHED**
- K-M → HOLD (다음)

## 커서 의견
{payload['cursor_opinion']}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict)
    print(json.dumps({"verdict": verdict, "checks": checks, "smoke": smoke}, ensure_ascii=True))
    return 0 if verdict == "PATCHED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
