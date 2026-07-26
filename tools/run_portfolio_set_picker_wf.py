# -*- coding: utf-8 -*-
"""포트폴리오 장선택 — 한 장이 아니라 서로 덜 겹치는 K장을 고른다.

동기: 뇌 best-of-15이 랜덤 best-of-15보다 약간 낮음(상관·겹침).
평균 장은 랜덤과 유사(~0.80) → '패턴 농축'이 최고장 행운을 깎음.
해결 시도: aux 상위 후보 중 Jaccard 낮게 K장 골라, 그 중 best / union cover 측정.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402
from tools.run_meta_hybrid_wf import _load_traps, fast_aux_composite  # noqa: E402
from tools.run_meta_vote2_wf import _best_single_match, _draws_before, _load_draws  # noqa: E402
from tools.run_set_picker_wf import _load_tagged_sets  # noqa: E402

OUT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_신뢰_odd_even_순위장선택"
    / "portfolio_wf_summary.json"
)


def jaccard(a: set[int], b: set[int]) -> float:
    return len(a & b) / max(1, len(a | b))


def pick_portfolio(
    entries: list[dict],
    draws_before: list[dict],
    target: int,
    traps: set[int],
    k: int = 3,
) -> list[list[int]]:
    scored = [
        (fast_aux_composite(list(e["nums"]), draws_before, target, traps), e["nums"])
        for e in entries
    ]
    scored.sort(key=lambda x: -x[0])
    # take top 8 then greedy diversity
    cand = scored[: max(8, k)]
    picked: list[list[int]] = []
    for sc, nums in cand:
        s = set(nums)
        if not picked:
            picked.append(sorted(nums))
            continue
        # penalty = avg jaccard to already picked
        pen = sum(jaccard(s, set(p)) for p in picked) / len(picked)
        # accept if diversity ok or we still need slots — score by aux - 0.5*pen
        # greedy: among remaining, pick max aux - 0.8*avg_jac
        pass
    # proper greedy from cand
    picked = []
    remaining = list(cand)
    while len(picked) < k and remaining:
        def key(item: tuple) -> float:
            sc, nums = item
            if not picked:
                return sc
            pen = sum(jaccard(set(nums), set(p)) for p in picked) / len(picked)
            return sc - 0.8 * pen

        best = max(remaining, key=key)
        remaining.remove(best)
        picked.append(sorted(best[1]))
    return picked


def main() -> int:
    init_testlotto_db()
    traps = _load_traps()
    all_draws = _load_draws()
    tagged = _load_tagged_sets()
    rng = random.Random(123)

    rows = []
    for d in all_draws:
        td = int(d["draw_no"])
        entries = tagged.get(td) or []
        if len(entries) < 5:
            continue
        before = _draws_before(all_draws, td)
        if not before:
            continue
        actual = sorted_nums(d)
        bonus = int(d["bonus"])
        sets = [e["nums"] for e in entries]
        oracle1 = _best_single_match(sets, actual, bonus)["matched_count"]

        port = pick_portfolio(entries, before, td, traps, k=3)
        port_best = max(
            score_predicted_set(s, actual, bonus)["matched_count"] for s in port
        )
        port_union = len(set(actual) & set().union(*[set(s) for s in port]))

        # aux single
        aux = max(
            entries,
            key=lambda e: fast_aux_composite(list(e["nums"]), before, td, traps),
        )
        aux_m = score_predicted_set(aux["nums"], actual, bonus)["matched_count"]

        # random portfolio of 3
        rsets = [sorted(rng.sample(range(1, 46), 6)) for _ in range(3)]
        rand_best = max(
            score_predicted_set(s, actual, bonus)["matched_count"] for s in rsets
        )

        rows.append(
            {
                "oracle1": oracle1,
                "aux1": aux_m,
                "port3_best": port_best,
                "port3_union": port_union,
                "rand3_best": rand_best,
                "delta_port_vs_aux": port_best - aux_m,
                "delta_port_vs_rand3": port_best - rand_best,
            }
        )

    n = len(rows)

    def avg(k: str) -> float:
        return round(sum(r[k] for r in rows) / n, 4)

    summary = {
        "ok": True,
        "n": n,
        "k": 3,
        "avg_oracle_best1": avg("oracle1"),
        "avg_aux1": avg("aux1"),
        "avg_portfolio3_best": avg("port3_best"),
        "avg_portfolio3_union_cover": avg("port3_union"),
        "avg_random3_best": avg("rand3_best"),
        "mean_delta_port_vs_aux": avg("delta_port_vs_aux"),
        "mean_delta_port_vs_rand3": avg("delta_port_vs_rand3"),
        "adopt_portfolio": avg("port3_best") >= avg("aux1") + 0.05,
        "note": (
            "포트폴리오=aux상위 후보에서 Jaccard 패널티로 K=3 선택. "
            "평가=3장 중 best match 및 union cover."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
