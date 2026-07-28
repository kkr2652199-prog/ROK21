# -*- coding: utf-8 -*-
"""Brief tier 1-4 hits — fast (no full JSON scan)."""
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "lotto_testlotto.db"


def tier_rank(matched: int, bonus: int) -> int:
    bm = 1 if bonus else 0
    if matched >= 6:
        return 1
    if matched == 5 and bm:
        return 2
    if matched == 5:
        return 3
    if matched == 4:
        return 4
    return 0


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    # counts only — no JSON
    counts = con.execute(
        """
        SELECT
          SUM(CASE WHEN matched_count>=6 THEN 1 ELSE 0 END) AS t1,
          SUM(CASE WHEN matched_count=5 AND bonus_matched=1 THEN 1 ELSE 0 END) AS t2,
          SUM(CASE WHEN matched_count=5 AND IFNULL(bonus_matched,0)=0 THEN 1 ELSE 0 END) AS t3,
          SUM(CASE WHEN matched_count=4 THEN 1 ELSE 0 END) AS t4,
          COUNT(*) AS total
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN 2 AND 1234
        """
    ).fetchone()

    hits = con.execute(
        """
        SELECT r.draw_no, r.brain_tag, r.matched_count, r.bonus_matched,
               r.predicted_sets_json, r.best_set_no, d.draw_date,
               d.num1, d.num2, d.num3, d.num4, d.num5, d.num6, d.bonus
        FROM testlotto_brain_review r
        JOIN lotto_draws d ON d.draw_no = r.draw_no
        WHERE r.draw_no BETWEEN 2 AND 1234
          AND r.matched_count >= 4
        ORDER BY r.draw_no, r.brain_tag
        """
    ).fetchall()

    print("SUMMARY")
    print(f"window: draw 2-1234 (3 brains x 1233 draws = {counts['total']} rows)")
    print(f"  1등: {counts['t1']}")
    print(f"  2등: {counts['t2']}")
    print(f"  3등: {counts['t3']}")
    print(f"  4등: {counts['t4']}")

    by_brain = defaultdict(list)
    detail = []
    for r in hits:
        tr = tier_rank(int(r["matched_count"]), int(r["bonus_matched"] or 0))
        if tr not in (1, 2, 3, 4):
            continue
        actual = sorted(int(r[f"num{i}"]) for i in range(1, 7))
        pred, hit_nums = [], []
        try:
            sets = json.loads(r["predicted_sets_json"] or "[]")
            best = next(
                (s for s in sets if int(s.get("set_no") or 0) == int(r["best_set_no"])),
                sets[int(r["best_set_no"]) - 1] if sets else {},
            )
            pred = list(best.get("nums") or [])
            hit_nums = sorted(set(pred) & set(actual))
        except Exception:
            pass
        entry = {
            "draw": int(r["draw_no"]),
            "date": r["draw_date"] or "",
            "tier": tr,
            "brain": r["brain_tag"],
            "set_no": int(r["best_set_no"]),
            "hit_nums": hit_nums,
            "actual": actual,
            "bonus": int(r["bonus"]),
            "pred": pred,
        }
        detail.append(entry)
        by_brain[r["brain_tag"]].append(int(r["draw_no"]))

    unique_draws = sorted({d["draw"] for d in detail})
    print(f"  unique draws (1-4등): {len(unique_draws)}")
    print("\nBY_BRAIN")
    for tag in ("markov", "review", "stat"):
        ds = sorted(by_brain.get(tag, []))
        print(f"  {tag}: {len(ds)} | {ds}")

    by_draw = defaultdict(list)
    for d in detail:
        by_draw[d["draw"]].append(d["brain"])
    multi = {k: v for k, v in by_draw.items() if len(v) > 1}
    print(f"\nMULTI_BRAIN ({len(multi)} draws)")
    for d in sorted(multi):
        print(f"  {d}: {multi[d]}")

    print("\nDETAIL")
    for d in sorted(detail, key=lambda x: (x["draw"], x["brain"])):
        print(
            f"{d['draw']:4d} {d['date']:10s} T{d['tier']} {d['brain']:6s} set{d['set_no']} "
            f"hit={d['hit_nums']} actual={d['actual']} b={d['bonus']}"
        )

    con.close()


if __name__ == "__main__":
    main()
