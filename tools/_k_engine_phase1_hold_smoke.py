# -*- coding: utf-8 -*-
"""K-ENGINE-PHASE1-HOLD STEP1 smoke — markov solo draws 1230~1234 · 5 predictions."""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.markov_brain import engine  # noqa: E402
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402

SEED = 42
N_SETS = 5


def _uses_full_draws() -> bool:
    """build_transition_matrix must NOT slice draws[-100:]."""
    import inspect

    src = inspect.getsource(engine.build_transition_matrix)
    return "draws[-100:]" not in src


def main() -> int:
    markov_predict.HINT_WEIGHT = 0.15
    markov_learn.LEARN_WIRED = True

    if not _uses_full_draws():
        print("FAIL: build_transition_matrix still has draws[-100:] slice")
        return 1

    ok = True
    for draw_no in range(1230, 1235):
        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            print(f"draw {draw_no}: FAIL no draws")
            ok = False
            continue
        random.seed(SEED)
        sets = markov_predict.run(draws, N_SETS)
        n = len(sets)
        status = "OK" if n == N_SETS else "FAIL"
        if n != N_SETS:
            ok = False
        print(f"draw {draw_no}: {status} n_sets={n} draws_in={len(draws)}")

    if ok:
        print("SMOKE PASS 1230~1234 · full draws · 5/5 each")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
