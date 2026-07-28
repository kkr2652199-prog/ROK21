# -*- coding: utf-8 -*-
"""K-ANALOG-1 verify — API gate 재현 (READ-ONLY)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from app.testlotto.analog_service import build_analog_report

    draw_no = int(sys.argv[1]) if len(sys.argv) > 1 else 1234
    report = build_analog_report(draw_no)
    if report.get("error"):
        print(json.dumps(report, ensure_ascii=False))
        return 1

    top = report.get("top_k") or []
    top1 = report.get("top1_summary") or {}
    gate = report.get("patch_gate", {})
    ok = (
        gate.get("conditional_go") is True
        and len(top) >= 5
        and top1.get("overlap", 0) >= 2
        and report.get("ui_disclaimer")
        and report.get("bench_verdict")
    )
    out = {
        "draw_no": draw_no,
        "verify": "PASS" if ok else "FAIL",
        "candidate_total": report["candidate_total"],
        "top1": top1,
        "conditional_hint": report.get("conditional_hint"),
        "top3": [
            {
                "draw_no": c["draw_no"],
                "overlap": c["overlap"],
                "next_draw": c["next_draw"]["draw_no"],
            }
            for c in top[:3]
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
