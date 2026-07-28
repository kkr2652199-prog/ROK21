# -*- coding: utf-8 -*-
"""K-SCATTER-1 — 뇌별 5세트 당첨공 흩어짐 (READ-ONLY).

질문: 한 뇌 5세트에 당첨 번호가 몇 장에 갈렸는가? 합치면 몇 개?
산출: docs/benchmarks/20260729_KSCATTER_brain5.json
"""
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KSCATTER_brain5.json"


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    actuals = {
        int(r[0]): set(int(r[i]) for i in range(1, 7))
        for r in con.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no BETWEEN 2 AND 1234"
        )
    }
    bonuses = {
        int(r[0]): int(r[1])
        for r in con.execute(
            "SELECT draw_no, bonus FROM lotto_draws WHERE draw_no BETWEEN 2 AND 1234"
        )
    }
    rows = con.execute(
        """
        SELECT draw_no, brain_tag, predicted_sets_json, matched_count
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN 2 AND 1234
        """
    ).fetchall()
    con.close()

    by_brain: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for r in rows:
        d = int(r["draw_no"])
        act = actuals.get(d)
        if not act:
            continue
        try:
            sets = json.loads(r["predicted_sets_json"] or "[]")
        except Exception:
            continue
        per_set_hits = []
        union_hit = set()
        sets_with_hit = 0
        for s in sets:
            nums = set(int(n) for n in (s.get("nums") or []))
            hit = nums & act
            per_set_hits.append(len(hit))
            if hit:
                sets_with_hit += 1
            union_hit |= hit
        bonus = bonuses.get(d, 0)
        bonus_in_any = any(bonus in set(s.get("nums") or []) for s in sets)
        best = max(per_set_hits) if per_set_hits else 0
        union_n = len(union_hit)
        # scatter waste: union has more hits than best single set
        waste = union_n - best
        by_brain[r["brain_tag"]].append(
            {
                "draw": d,
                "best": best,
                "union_hit": union_n,
                "waste": waste,
                "sets_with_any_hit": sets_with_hit,
                "bonus_in_pool": bonus_in_any,
                "stored_best_matched": int(r["matched_count"]),
            }
        )

    summary = {}
    for tag, items in sorted(by_brain.items()):
        n = len(items)
        if not n:
            continue
        summary[tag] = {
            "n": n,
            "best_mean": round(sum(i["best"] for i in items) / n, 4),
            "union_hit_mean": round(sum(i["union_hit"] for i in items) / n, 4),
            "waste_mean": round(sum(i["waste"] for i in items) / n, 4),
            "waste_ge1_rate": round(sum(1 for i in items if i["waste"] >= 1) / n, 4),
            "waste_ge2_rate": round(sum(1 for i in items if i["waste"] >= 2) / n, 4),
            "union_ge4_rate": round(sum(1 for i in items if i["union_hit"] >= 4) / n, 4),
            "union_ge5_rate": round(sum(1 for i in items if i["union_hit"] >= 5) / n, 4),
            "union_ge6_rate": round(sum(1 for i in items if i["union_hit"] >= 6) / n, 4),
            "union_ge6_count": sum(1 for i in items if i["union_hit"] >= 6),
            "best_ge4_rate": round(sum(1 for i in items if i["best"] >= 4) / n, 4),
            "gather_opportunity_rate": round(
                sum(1 for i in items if i["union_hit"] > i["best"]) / n, 4
            ),
            "bonus_in_5set_pool_rate": round(
                sum(1 for i in items if i["bonus_in_pool"]) / n, 4
            ),
            "sets_with_hit_mean": round(
                sum(i["sets_with_any_hit"] for i in items) / n, 3
            ),
        }

    # examples: largest waste
    examples = []
    for tag, items in by_brain.items():
        top = sorted(items, key=lambda x: (-x["waste"], -x["union_hit"]))[:5]
        for i in top:
            if i["waste"] >= 2:
                examples.append({"brain": tag, **i})

    payload = {
        "id": "K-SCATTER-1",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "definition": {
            "scope": "per brain × 5 sets (NOT cross-brain 15)",
            "union_hit": "distinct winning nums appearing in any of 5 sets",
            "best": "max hit count in a single set",
            "waste": "union_hit - best (≥1 ⇒ gather could help retrospectively)",
            "gather_opportunity": "waste >= 1",
        },
        "by_brain": summary,
        "examples_high_waste": examples[:15],
        "interpretation": [
            "gather_opportunity_rate 높으면 뇌내 몰아주기 사후 이득 공간 큼",
            "union_ge6 > best_ge6 이면 '공은 풀에 있었는데 한 장에 못 모음'",
            "사전 몰아주기는 V 선별이 핵심 — 본 지표는 동기(왜 +5세트) 제공",
        ],
        "next": "K-GATHER-DESIGN",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    for tag, s in summary.items():
        print(tag, s)


if __name__ == "__main__":
    main()
