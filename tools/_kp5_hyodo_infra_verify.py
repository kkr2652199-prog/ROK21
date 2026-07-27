# -*- coding: utf-8 -*-
"""K-P5 verify: hyodo infra-dashboard API · READ-ONLY."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "benchmarks" / "20260727_KP5_hyodo_infra.json"


def main() -> int:
    from app.hyodo.infra_dashboard import build_infra_dashboard

    data = build_infra_dashboard()
    checks = {
        "has_draws_max": int((data.get("draws") or {}).get("max") or 0) == 1234,
        "lstm_block": "lstm" in data,
        "baseline_pin": data.get("baseline_pin") == "640cb67",
        "frozen_list": len(data.get("frozen_tokens") or []) >= 1,
    }
    verify_pass = all(checks.values())
    payload = {**data, "checks": checks, "verify_pass": verify_pass}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
