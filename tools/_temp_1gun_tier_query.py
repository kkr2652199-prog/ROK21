"""READ-ONLY tier win survey for 1군 lotto.db — temp, delete after use."""
import sqlite3
from pathlib import Path

DB = Path(r"D:\MONEY lol\My_Library\data\lotto.db")
EXCLUDE = "brain_tag NOT IN ('miss_analysis','snake')"

conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== lotto_predictions schema ===")
for c in cur.execute("PRAGMA table_info(lotto_predictions)"):
    print(dict(c))

print("\n=== total rows (1군 brain_tags) ===")
row = cur.execute(
    f"""
    SELECT COUNT(*) AS n FROM lotto_predictions
    WHERE {EXCLUDE}
      AND brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')
    """
).fetchone()
print("1군6뇌 rows:", row["n"])

print("\n=== tier counts (prediction rows) ===")
tier_sql = f"""
SELECT
  SUM(CASE WHEN matched_count=6 THEN 1 ELSE 0 END) AS tier1_rows,
  SUM(CASE WHEN matched_count=5 AND bonus_matched=1 THEN 1 ELSE 0 END) AS tier2_rows,
  SUM(CASE WHEN matched_count=5 AND (bonus_matched=0 OR bonus_matched IS NULL) THEN 1 ELSE 0 END) AS tier3_rows,
  SUM(CASE WHEN matched_count=4 THEN 1 ELSE 0 END) AS tier4_rows,
  SUM(CASE WHEN matched_count=3 THEN 1 ELSE 0 END) AS tier5_rows,
  SUM(CASE WHEN matched_count>=0 THEN 1 ELSE 0 END) AS scored_rows,
  SUM(CASE WHEN matched_count<0 THEN 1 ELSE 0 END) AS unscored_rows
FROM lotto_predictions
WHERE {EXCLUDE}
  AND brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')
"""
for k, v in dict(cur.execute(tier_sql).fetchone()).items():
    print(f"  {k}: {v}")

print("\n=== tier counts (distinct draw_no with at least one hit) ===")
draw_tier = f"""
SELECT tier, COUNT(*) AS draw_count FROM (
  SELECT target_draw_no,
    CASE
      WHEN MAX(matched_count)=6 THEN '1'
      WHEN MAX(matched_count)=5 AND MAX(bonus_matched)=1 THEN '2'
      WHEN MAX(matched_count)=5 THEN '3'
      WHEN MAX(matched_count)=4 THEN '4'
      WHEN MAX(matched_count)=3 THEN '5'
      ELSE '0'
    END AS tier
  FROM lotto_predictions
  WHERE {EXCLUDE}
    AND brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')
    AND matched_count >= 0
  GROUP BY target_draw_no
) GROUP BY tier ORDER BY tier
"""
for r in cur.execute(draw_tier):
    print(f"  tier{r['tier']}: {r['draw_count']} draws")

print("\n=== tier by brain_tag (rows) ===")
for r in cur.execute(
    f"""
    SELECT brain_tag,
      SUM(CASE WHEN matched_count=6 THEN 1 ELSE 0 END) AS t1,
      SUM(CASE WHEN matched_count=5 AND bonus_matched=1 THEN 1 ELSE 0 END) AS t2,
      SUM(CASE WHEN matched_count=5 AND (bonus_matched=0 OR bonus_matched IS NULL) THEN 1 ELSE 0 END) AS t3,
      SUM(CASE WHEN matched_count=4 THEN 1 ELSE 0 END) AS t4,
      SUM(CASE WHEN matched_count=3 THEN 1 ELSE 0 END) AS t5
    FROM lotto_predictions
    WHERE {EXCLUDE} AND matched_count >= 0
      AND brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')
    GROUP BY brain_tag ORDER BY brain_tag
    """
):
    print(dict(r))

print("\n=== sample tier1-3 rows ===")
for tier_name, cond in [
    ("1등", "matched_count=6"),
    ("2등", "matched_count=5 AND bonus_matched=1"),
    ("3등", "matched_count=5 AND (bonus_matched=0 OR bonus_matched IS NULL)"),
]:
    print(f"\n--- {tier_name} (top 5) ---")
    rows = cur.execute(
        f"""
        SELECT target_draw_no, brain_tag, method, matched_count, bonus_matched,
               confidence, created_at,
               num1,num2,num3,num4,num5,num6
        FROM lotto_predictions
        WHERE {EXCLUDE} AND {cond}
          AND brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')
        ORDER BY target_draw_no DESC, confidence DESC
        LIMIT 5
        """
    ).fetchall()
    if not rows:
        print("  (none)")
    for r in rows:
        d = dict(r)
        nums = [d[f"num{i}"] for i in range(1, 7)]
        print(
            f"  draw={d['target_draw_no']} tag={d['brain_tag']} mc={d['matched_count']} "
            f"bonus={d['bonus_matched']} conf={d['confidence']} at={d.get('created_at')} nums={nums}"
        )

print("\n=== draw range ===")
r = cur.execute(
    f"""
    SELECT MIN(target_draw_no) mn, MAX(target_draw_no) mx, COUNT(DISTINCT target_draw_no) draws
    FROM lotto_predictions
    WHERE brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')
    """
).fetchone()
print(dict(r))

print("\n=== max draw in lotto_draws ===")
r = cur.execute("SELECT MAX(draw_no) mx, COUNT(*) n FROM lotto_draws").fetchone()
print(dict(r))

print("\n=== distinct draw_no per tier (≥1 set hit) ===")
for name, cond in [
    ("1등", "matched_count=6"),
    ("2등", "matched_count=5 AND bonus_matched=1"),
    ("3등", "matched_count=5 AND (bonus_matched=0 OR bonus_matched IS NULL)"),
    ("4등", "matched_count=4"),
    ("5등", "matched_count=3"),
]:
    n = cur.execute(
        f"""
        SELECT COUNT(DISTINCT target_draw_no) FROM lotto_predictions
        WHERE {EXCLUDE}
          AND brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')
          AND matched_count >= 0 AND ({cond})
        """
    ).fetchone()[0]
    print(f"  {name}: {n} draws")

print("\n=== best hit per draw distribution ===")
for r in cur.execute(
    f"""
    SELECT
      SUM(CASE WHEN best_mc=6 THEN 1 ELSE 0 END) AS best_is_1,
      SUM(CASE WHEN best_mc=5 AND best_bm=1 THEN 1 ELSE 0 END) AS best_is_2,
      SUM(CASE WHEN best_mc=5 AND best_bm=0 THEN 1 ELSE 0 END) AS best_is_3,
      SUM(CASE WHEN best_mc=4 THEN 1 ELSE 0 END) AS best_is_4,
      SUM(CASE WHEN best_mc=3 THEN 1 ELSE 0 END) AS best_is_5,
      SUM(CASE WHEN best_mc<3 THEN 1 ELSE 0 END) AS best_lt_5,
      COUNT(*) AS scored_draws
    FROM (
      SELECT target_draw_no,
             MAX(matched_count) AS best_mc,
             MAX(CASE WHEN matched_count=5 THEN bonus_matched ELSE 0 END) AS best_bm
      FROM lotto_predictions
      WHERE {EXCLUDE}
        AND brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')
        AND matched_count >= 0
      GROUP BY target_draw_no
    )
    """
):
    print(dict(r))

print("\n=== 1등 distinct draws ===")
rows = cur.execute(
    f"""
    SELECT DISTINCT target_draw_no FROM lotto_predictions
    WHERE {EXCLUDE} AND matched_count=6
      AND brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')
    ORDER BY target_draw_no
    """
).fetchall()
print([r[0] for r in rows])

conn.close()
