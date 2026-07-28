"""Quick post K-REVIEW-RUN sample checks."""
import hashlib
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "lotto_testlotto.db"

def main():
    c = sqlite3.connect(DB)
    for d in (100, 500, 1234):
        r = c.execute(
            "SELECT predicted_sets_json, matched_count, created_at FROM testlotto_brain_review "
            "WHERE draw_no=? AND brain_tag=?",
            (d, "stat"),
        ).fetchone()
        h = hashlib.md5((r[0] or "").encode()).hexdigest()[:12]
        has_pipe = "[보조4뇌:" in (r[0] or "")
        print(f"draw={d} matched={r[1]} created={r[2]} md5={h} pipe={has_pipe}")
    pipe = c.execute(
        "SELECT COUNT(*) FROM testlotto_brain_review WHERE predicted_sets_json LIKE ?",
        ("%[보조4뇌:%",),
    ).fetchone()[0]
    total = c.execute("SELECT COUNT(*) FROM testlotto_brain_review").fetchone()[0]
    print(f"pipe_markers={pipe}/{total}")
    c.close()

if __name__ == "__main__":
    main()
