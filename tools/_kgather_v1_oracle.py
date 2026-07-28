# -*- coding: utf-8 -*-
"""K-GATHER-V1 step1 — union6 oracle 분해 (READ-ONLY)."""
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KGATHER_v1_oracle.json"


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    actuals = {
        int(r[0]): sorted(int(r[i]) for i in range(1, 7))
        for r in con.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no BETWEEN 2 AND 1234"
        )
    }
    rows = con.execute(
        """
        SELECT draw_no, brain_tag, predicted_sets_json
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN 2 AND 1234 AND brain_tag='stat'
        """
    ).fetchall()
    con.close()

    cases = []
    for r in rows:
        d = int(r["draw_no"])
        act = set(actuals[d])
        sets = json.loads(r["predicted_sets_json"] or "[]")
        bases = [[int(n) for n in (s.get("nums") or [])] for s in sets]
        bases = [b for b in bases if len(b) == 6]
        if len(bases) < 5:
            continue
        union = {n for b in bases for n in b}
        if not act.issubset(union):
            continue
        # per winning num: which set indices contain it
        win_locs = {}
        for w in sorted(act):
            win_locs[w] = [i + 1 for i, b in enumerate(bases) if w in b]
        # can any single base get >=4?
        per = [len(set(b) & act) for b in bases]
        # pairwise: how many winning pairs appear together in some base set
        win_pairs = list(combinations(sorted(act), 2))
        pairs_covered = sum(
            1
            for p in win_pairs
            if any(p[0] in b and p[1] in b for b in bases)
        )
        # oracle: if we could pick exactly act as one gather set
        # blind upper with 5 tickets: greedy set cover style — max hits packing
        # simulate best possible best-of-5 from V without knowing act: impossible
        # instead: count minimal tickets needed to cover all win pairs (oracle wheel size)
        cases.append(
            {
                "draw": d,
                "actual": sorted(act),
                "V_size": len(union),
                "per_set_hits": per,
                "best": max(per),
                "win_locations": {str(k): v for k, v in win_locs.items()},
                "sets_touched_by_winners": len({i for locs in win_locs.values() for i in locs}),
                "winning_pairs_total": len(win_pairs),
                "winning_pairs_covered_in_some_base": pairs_covered,
                "pair_cover_rate": round(pairs_covered / len(win_pairs), 4),
                "singleton_winners": sum(1 for locs in win_locs.values() if len(locs) == 1),
            }
        )

    # summary
    n = len(cases)
    summary = {
        "n_union6_stat": n,
        "V_size_mean": round(sum(c["V_size"] for c in cases) / n, 2) if n else 0,
        "best_mean": round(sum(c["best"] for c in cases) / n, 4) if n else 0,
        "pair_cover_rate_mean": round(sum(c["pair_cover_rate"] for c in cases) / n, 4)
        if n
        else 0,
        "singleton_winners_mean": round(sum(c["singleton_winners"] for c in cases) / n, 2)
        if n
        else 0,
        "sets_touched_mean": round(
            sum(c["sets_touched_by_winners"] for c in cases) / n, 2
        )
        if n
        else 0,
        "draws": [c["draw"] for c in cases],
    }

    # insight: if pair_cover_rate high, winners often appear as pairs in bases →
    # gather should stitch pairs from different sets
    payload = {
        "id": "K-GATHER-V1-ORACLE",
        "brain": "stat",
        "summary": summary,
        "cases": cases,
        "design_hints": [
            "V_size typically ~20 → C(V,6) huge; 5 tickets cannot guarantee 6-if-6",
            "if pair_cover_rate high: stitch winning pairs across sets (graph matching)",
            "if singleton_winners high: need cross-set assembly of isolates",
            "v1 candidate: build graph of numbers co-appearing in same base set; find 6-cliques/dense subgraphs in complement (numbers that RARELY co-appear) — actually winners may rarely co-appear",
            "v1-oracle-ceiling test: inject one gather set = actual when act⊂V (cheat ceiling) to separate 'algorithm fail' vs '5-ticket limit'",
        ],
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for c in cases[:5]:
        print(c["draw"], "V", c["V_size"], "best", c["best"], "pairs", c["pair_cover_rate"], "single", c["singleton_winners"], c["per_set_hits"])


if __name__ == "__main__":
    main()
