# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.coordinator import AUX_WEIGHTS, run_coordinated_prediction
from app.testlotto.models import get_lotto_db, init_lotto_db

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
        "SELECT brain_tag, confidence FROM lotto_predictions WHERE target_draw_no=? ORDER BY confidence DESC",
        (d,),
    ).fetchall()
    conn.close()
    if n != 5 or r.get("error"):
        ok = False
        print(f"FAIL draw {d} n={n} err={r.get('error')}")
    else:
        tags = [dict(x) for x in rows]
        print(
            f"OK draw {d} n=5 tags={[t['brain_tag'] for t in tags]} "
            f"conf_top={float(tags[0]['confidence']):.1f}"
        )
print("AUX_WEIGHTS", AUX_WEIGHTS)
print("SMOKE", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
