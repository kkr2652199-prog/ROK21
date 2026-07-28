# -*- coding: utf-8 -*-
"""K-DETAIL-CUTOFF — detail/draw CUTOFF 회귀 검증 (1234·1235)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260728_KDETAIL_cutoff_fix.json"


def main() -> int:
    from fastapi.testclient import TestClient

    from app.main_v13 import app

    client = TestClient(app)
    checks: dict[str, bool] = {}
    samples: dict[str, object] = {}

    for draw_no in (1234, 1235):
        r = client.get(f"/api/testlotto/detail/draw/{draw_no}")
        ok = r.status_code == 200
        checks[f"detail_{draw_no}_200"] = ok
        if ok:
            body = r.json()
            samples[str(draw_no)] = {
                "draw_no": body.get("draw_no"),
                "actual_nums": body.get("actual_nums"),
                "brains_n": len(body.get("brains") or []),
                "aux_n": len(body.get("aux_brains") or []),
                "error": body.get("error"),
            }
            checks[f"detail_{draw_no}_has_actual"] = bool(body.get("actual_nums")) or draw_no == 1235
        else:
            samples[str(draw_no)] = {"status": r.status_code, "text": r.text[:200]}

    r_pred = client.get("/api/testlotto/predictions/draw/1234")
    checks["predictions_1234_200"] = r_pred.status_code == 200

    verify_pass = all(checks.values())
    payload = {
        "task": "K-DETAIL-CUTOFF",
        "fix": "get_draw_detail set_learn_as_of(draw_no) before aux/referee",
        "checks": checks,
        "samples": samples,
        "verify_pass": verify_pass,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
