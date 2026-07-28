# -*- coding: utf-8 -*-
"""K-UI-SSOT — 메인 brain_review 우선·상세 미래회차 폴백 검증."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260728_KUI_ssot_fix.json"


def _stat_first_set(body: dict) -> list[int] | None:
    for b in body.get("brains") or []:
        if b.get("brain_tag") != "stat":
            continue
        sets = b.get("predicted_sets") or []
        if sets and sets[0].get("nums"):
            return list(sets[0]["nums"])
        nums = b.get("predicted_nums") or []
        return list(nums) if nums else None
    return None


def _legacy_stat_first_set(preds: list[dict]) -> list[int] | None:
    stat = [p for p in preds if p.get("brain_tag") == "stat"]
    if not stat:
        return None
    r = stat[0]
    return [r[f"num{i}"] for i in range(1, 7)]


def main() -> int:
    from fastapi.testclient import TestClient

    from app.main_v13 import app

    client = TestClient(app)
    checks: dict[str, bool] = {}
    samples: dict[str, object] = {}

    r_detail = client.get("/api/testlotto/detail/draw/1234")
    r_legacy = client.get("/api/testlotto/predictions/draw/1234")
    r_pred_list = client.get("/api/testlotto/predictions?limit=20000")
    r_draws = client.get("/api/testlotto/draws?limit=10000")

    checks["detail_1234_200"] = r_detail.status_code == 200
    checks["legacy_1234_200"] = r_legacy.status_code == 200
    checks["predictions_list_200"] = r_pred_list.status_code == 200
    checks["draws_list_200"] = r_draws.status_code == 200

    detail = r_detail.json() if checks["detail_1234_200"] else {}
    legacy_rows = (r_legacy.json().get("predictions") or []) if checks["legacy_1234_200"] else []

    detail_stat = _stat_first_set(detail)
    legacy_stat = _legacy_stat_first_set(legacy_rows)
    checks["detail_1234_has_stat_sets"] = detail_stat is not None and len(detail_stat) == 6
    checks["legacy_1234_has_stat_sets"] = legacy_stat is not None and len(legacy_stat) == 6
    # K-00 SSOT: 당첨 회차는 detail ≠ legacy (동기화 가정 금지 · 패치 후 메인=detail)
    checks["detail_legacy_stat_differ_1234"] = (
        detail_stat is not None and legacy_stat is not None and detail_stat != legacy_stat
    )

    pred_draws = {
        int(p["target_draw_no"])
        for p in (r_pred_list.json().get("predictions") or [])
        if p.get("target_draw_no") is not None
    }
    draw_draws = {
        int(d["draw_no"])
        for d in (r_draws.json().get("draws") or [])
        if d.get("draw_no") is not None
    }
    merged = pred_draws | draw_draws
    checks["merged_list_has_1234"] = 1234 in merged
    checks["predictions_only_1235"] = 1235 in pred_draws and 1235 not in draw_draws
    checks["merged_list_has_1235"] = 1235 in merged

    r_pred_1235 = client.get("/api/testlotto/predictions/draw/1235")
    checks["legacy_1235_has_rows"] = r_pred_1235.status_code == 200 and len(r_pred_1235.json().get("predictions") or []) > 0
    r_detail_1235 = client.get("/api/testlotto/detail/draw/1235")
    body_1235 = r_detail_1235.json() if r_detail_1235.status_code == 200 else {}
    checks["detail_1235_error_body"] = bool(body_1235.get("error"))

    samples["1234"] = {
        "detail_stat_set1": detail_stat,
        "legacy_stat_set1": legacy_stat,
        "detail_stat_matched": next(
            (b.get("matched_count") for b in (detail.get("brains") or []) if b.get("brain_tag") == "stat"),
            None,
        ),
    }
    samples["draw_lists"] = {
        "draws_max": max(draw_draws) if draw_draws else None,
        "predictions_max": max(pred_draws) if pred_draws else None,
        "merged_max": max(merged) if merged else None,
    }
    samples["1235"] = {
        "detail_error": body_1235.get("error"),
        "legacy_n": len(r_pred_1235.json().get("predictions") or []) if checks["legacy_1235_has_rows"] else 0,
    }

    verify_pass = all(checks.values())
    payload = {
        "task": "K-UI-SSOT",
        "fix": "main brain_review priority; select sync; detail future draw fallback",
        "checks": checks,
        "samples": samples,
        "verify_pass": verify_pass,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
