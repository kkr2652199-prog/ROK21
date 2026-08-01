# -*- coding: utf-8 -*-
"""K-ENGINE-PHASE1 smoke — coordinator 1230~1234 (5 draws)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.coordinator import run_coordinated_prediction  # noqa: E402

ok = 0
for draw_no in range(1230, 1235):
    result = run_coordinated_prediction(draw_no)
    if result.get("error"):
        raise RuntimeError(f"draw {draw_no}: {result['error']}")
    preds = result.get("predictions") or []
    print(f"draw {draw_no}: OK preds={len(preds)}")
    ok += 1

print(f"SMOKE PASS {ok}/5 · draws 1230~1234")
