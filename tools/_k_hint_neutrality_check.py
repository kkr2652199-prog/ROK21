# -*- coding: utf-8 -*-
"""hint 축 개방이 **성적 무변화**인지 확인 (READ-ONLY).

`HINT_SPEC_BY_BRAIN` 값이 3뇌 동일이면 뇌별 hint 를 넘겨도 결과가 같아야 한다.
같지 않으면 「값은 그대로 두고 구조만 열었다」는 주장이 거짓이 된다.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _rows(dno: int, seed: int, *, per_brain: bool) -> list[tuple]:
    import app.testlotto.signal_pool as sp

    learner = sp.RollingSignalLearner()
    sp.warm_learner_to_draw(learner, max(1, dno - 200), dno, seed=seed)
    num_all, pos_all = learner.snapshot()
    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    random.seed(seed)
    pool_br = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))
    hint = sp._build_hint(draws, dno)
    hbb = sp.build_hint_by_brain(draws, dno) if per_brain else None
    rows = sp.repack_by_brain(
        pool_br, hint, num_all, pos_all, target_draw_no=dno, hint_by_brain=hbb
    )
    return [
        (str(r.get("brain_tag")), int(r.get("pred_set_no") or 0), tuple(sorted(r["nums"])))
        for r in rows
    ]


def main() -> None:
    import app.testlotto.signal_pool as sp

    print(f"HINT_SPEC_BY_BRAIN = {dict(sp.HINT_SPEC_BY_BRAIN)}")
    print(f"hint_shared_across_brains() = {sp.hint_shared_across_brains()}")
    ok = True
    for dno in (1233, 1234, 1235):
        a = _rows(dno, sp.MC_SEED, per_brain=False)
        b = _rows(dno, sp.MC_SEED, per_brain=True)
        same = a == b
        ok = ok and same
        print(f"  {dno} 공용hint vs 뇌별hint 동일: {same}")
    print("\n" + ("NEUTRAL — 성적 무변화 확인" if ok else "CHANGED — 무변화 주장 거짓"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
