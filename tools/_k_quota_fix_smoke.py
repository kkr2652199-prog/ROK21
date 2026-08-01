# -*- coding: utf-8 -*-
"""K-FUSION-QUOTA-FIX smoke — draws 1230~1234 · 5 predictions each."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import coordinator as coord_mod  # noqa: E402
from app.testlotto.brains.coordinator import run_coordinated_prediction  # noqa: E402
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

SMOKE_DRAWS = range(1230, 1235)


def main() -> None:
    stat_predict.HINT_WEIGHT = 0.15
    markov_predict.HINT_WEIGHT = 0.15
    review_predict.HINT_WEIGHT = 0.15
    markov_learn.LEARN_WIRED = True
    coord_mod.AUX_1TO1_ENABLED = True
    coord_mod.MARKOV_WIRE_ENABLED = True
    coord_mod.BENCH_FIXED_QUOTA = None

    init_lotto_db()
    ok = 0
    for draw_no in SMOKE_DRAWS:
        result = run_coordinated_prediction(draw_no)
        if result.get("error"):
            raise RuntimeError(f"draw {draw_no}: {result['error']}")
        conn = get_lotto_db()
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no = ?",
                (draw_no,),
            ).fetchone()[0]
        finally:
            conn.close()
        if int(n) != 5:
            raise RuntimeError(f"draw {draw_no}: expected 5 predictions, got {n}")
        tags = {}
        conn = get_lotto_db()
        try:
            rows = conn.execute(
                "SELECT brain_tag FROM lotto_predictions WHERE target_draw_no = ?",
                (draw_no,),
            ).fetchall()
            for r in rows:
                t = str(dict(r).get("brain_tag") or "")
                tags[t] = tags.get(t, 0) + 1
        finally:
            conn.close()
        print(f"draw {draw_no}: OK n=5 quota={tags}")
        ok += 1
    print(f"SMOKE PASS {SMOKE_DRAWS.start}~{SMOKE_DRAWS.stop - 1} ({ok}/5)")


if __name__ == "__main__":
    main()
