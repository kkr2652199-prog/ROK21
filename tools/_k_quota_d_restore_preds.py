# -*- coding: utf-8 -*-
"""롤백 후 fusion 예측 재발권 (dynamic quota)."""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from app.testlotto.brains import coordinator as c
    from app.testlotto.brains.coordinator import run_coordinated_prediction
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    print("BENCH_FIXED_QUOTA", c.BENCH_FIXED_QUOTA)
    assert c.BENCH_FIXED_QUOTA is None
    c.BRAIN_RNG_SEED_BASE = 42
    init_testlotto_db()
    conn = get_lotto_db()
    conn.execute(
        "DELETE FROM lotto_predictions WHERE target_draw_no BETWEEN 1036 AND 1235"
    )
    conn.commit()
    conn.close()

    t0 = time.time()
    for i, dno in enumerate(range(1036, 1236), 1):
        random.seed(42 + dno)
        run_coordinated_prediction(dno)
        if i % 40 == 0:
            print(i, "elapsed", round(time.time() - t0), flush=True)

    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT brain_tag, COUNT(*) AS c FROM lotto_predictions "
        "WHERE target_draw_no BETWEEN 1036 AND 1235 GROUP BY brain_tag"
    ).fetchall()
    print("quota", [dict(r) for r in rows])
    bests = []
    for dno in range(1036, 1236):
        preds = conn.execute(
            "SELECT matched_count,num1,num2,num3,num4,num5,num6 "
            "FROM lotto_predictions WHERE target_draw_no=?",
            (dno,),
        ).fetchall()
        act = conn.execute(
            "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?",
            (dno,),
        ).fetchone()
        actual = {int(dict(act)[f"num{k}"]) for k in range(1, 7)}
        best = 0
        for p in preds:
            pd = dict(p)
            if pd.get("matched_count") is not None:
                mc = int(pd["matched_count"])
            else:
                mc = len({int(pd[f"num{k}"]) for k in range(1, 7)} & actual)
            best = max(best, mc)
        bests.append(best)
    ge3 = sum(1 for b in bests if b >= 3) / len(bests)
    print("restored_ge3", round(ge3, 6), "elapsed", round(time.time() - t0))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
