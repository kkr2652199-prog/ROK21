# -*- coding: utf-8 -*-
"""K-FUTURE-WIRE smoke — 5 draws · bucket=aux_hint_native · n=5 issued."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import coordinator as coord_mod
from app.testlotto.brains.coordinator import BUCKET_SELECT_MODE, run_coordinated_prediction
from app.testlotto.models import get_lotto_db, init_lotto_db

assert BUCKET_SELECT_MODE == "aux_hint_native", BUCKET_SELECT_MODE
coord_mod.MARKOV_WIRE_ENABLED = True
coord_mod.AUX_1TO1_ENABLED = True
coord_mod.BENCH_FIXED_QUOTA = None

init_lotto_db()
conn = get_lotto_db()
conn.execute("DELETE FROM lotto_predictions WHERE target_draw_no BETWEEN 1230 AND 1234")
conn.commit()
conn.close()

ok = True
for d in range(1230, 1235):
    r = run_coordinated_prediction(d)
    conn = get_lotto_db()
    n = conn.execute(
        "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=?", (d,)
    ).fetchone()[0]
    rows = conn.execute(
        "SELECT brain_tag, confidence FROM lotto_predictions WHERE target_draw_no=? "
        "ORDER BY confidence DESC",
        (d,),
    ).fetchall()
    conn.close()
    dedup = r.get("dedup") or {}
    mode = dedup.get("bucket_select_mode")
    if n != 5 or r.get("error") or mode != "aux_hint_native":
        ok = False
        print(
            f"FAIL draw {d} n={n} err={r.get('error')} mode={mode}",
            flush=True,
        )
    else:
        tags = [dict(x)["brain_tag"] for x in rows]
        print(f"OK draw {d} n=5 tags={tags} mode={mode}", flush=True)

print("BUCKET_SELECT_MODE", BUCKET_SELECT_MODE)
print("SMOKE", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
