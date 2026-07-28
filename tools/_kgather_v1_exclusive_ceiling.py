# -*- coding: utf-8 -*-
"""Exclusive-pool ceiling on union6 cases."""
import json
import sqlite3
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
oracle = json.loads((ROOT / "docs/benchmarks/20260729_KGATHER_v1_oracle.json").read_text(encoding="utf-8"))
draws = set(oracle["summary"]["draws"])
con = sqlite3.connect(ROOT / "data/lotto_testlotto.db")
con.row_factory = sqlite3.Row
actuals = {
    int(r[0]): set(int(r[i]) for i in range(1, 7))
    for r in con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no BETWEEN 2 AND 1234"
    )
}
rows = con.execute(
    "SELECT draw_no, predicted_sets_json FROM testlotto_brain_review "
    "WHERE brain_tag=? AND draw_no BETWEEN 2 AND 1234",
    ("stat",),
).fetchall()
con.close()


def excl_pool(bases):
    app = Counter()
    for b in bases:
        for n in set(b):
            app[n] += 1
    return {n for n, c in app.items() if c == 1}


rec5 = rec6 = act_in_E = 0
E_sizes = []
details = []
for r in rows:
    d = int(r["draw_no"])
    if d not in draws:
        continue
    act = actuals[d]
    sets = json.loads(r["predicted_sets_json"] or "[]")
    bases = [[int(x) for x in (s.get("nums") or [])] for s in sets]
    bases = [b for b in bases if len(b) == 6]
    E = excl_pool(bases)
    E_sizes.append(len(E))
    if act.issubset(E):
        act_in_E += 1
    best = 0
    if 6 <= len(E) <= 15:
        for comb in combinations(sorted(E), 6):
            best = max(best, len(set(comb) & act))
    elif len(E) > 15:
        # ceiling among exclusives: how many winners are exclusive
        best = len(act & E)  # not a ticket — upper if we could pick all winners from E
        # also best ticket via random greedy N/A — use actual ∩ E size as 'oracle exclusives'
        # For ticket ceiling when |E|>15: C too big; report winners_in_E
        details.append({"draw": d, "E": len(E), "winners_in_E": len(act & E), "mode": "largeE"})
        if len(act & E) >= 5:
            rec5 += 1
        if len(act & E) >= 6:
            rec6 += 1
        print(d, "|E|", len(E), "winners_in_E", len(act & E), "base", max(len(set(b) & act) for b in bases))
        continue
    details.append({"draw": d, "E": len(E), "brute_best": best, "winners_in_E": len(act & E)})
    if best >= 5:
        rec5 += 1
    if best >= 6:
        rec6 += 1
    print(d, "|E|", len(E), "brute_best", best, "winners_in_E", len(act & E), "base", max(len(set(b) & act) for b in bases))

print(
    "n",
    len(draws),
    "act_subset_E",
    act_in_E,
    "E_mean",
    round(sum(E_sizes) / len(E_sizes), 2),
    "rec5",
    rec5,
    "rec6",
    rec6,
)
out = {
    "act_subset_E": act_in_E,
    "E_mean": round(sum(E_sizes) / len(E_sizes), 2),
    "brute_or_oracle_rec5": rec5,
    "brute_or_oracle_rec6": rec6,
    "details": details,
}
(ROOT / "docs/benchmarks/20260729_KGATHER_v1_exclusive_ceiling.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
