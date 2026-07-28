# -*- coding: utf-8 -*-
"""K-REVIEW-RUN — walk-forward 재복습 (brain_review · learn_state · brain_page).

Usage:
  python tools/_kreview_rerun.py              # READ-ONLY before snapshot
  python tools/_kreview_rerun.py --execute    # backup + reset + loop + bench
  python tools/_kreview_rerun.py --execute --start 1132 --end 1234  # window only
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "lotto_testlotto.db"
BEFORE_REF = ROOT / "docs" / "benchmarks" / "20260728_K00_homework_expand.json"
OUT_DIR = ROOT / "docs" / "benchmarks"
LOG_PATH = ROOT / "backups" / "20260728_KREVIEW_progress.log"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)


def _brain_stats(con: sqlite3.Connection, lo: int, hi: int) -> dict[str, Any]:
    rows = con.execute(
        """
        SELECT brain_tag,
               COUNT(*) AS n,
               ROUND(AVG(matched_count), 4) AS avg_m,
               SUM(CASE WHEN matched_count >= 3 THEN 1 ELSE 0 END) AS ge3
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN ? AND ?
        GROUP BY brain_tag
        ORDER BY brain_tag
        """,
        (lo, hi),
    ).fetchall()
    return {
        str(r[0]): {"n": int(r[1]), "avg_m": float(r[2] or 0), "ge3": int(r[3] or 0)}
        for r in rows
    }


def _pipe_marker_count(con: sqlite3.Connection, lo: int, hi: int) -> int:
    return int(
        con.execute(
            """
            SELECT COUNT(*) FROM testlotto_brain_review
            WHERE draw_no BETWEEN ? AND ?
              AND predicted_sets_json LIKE '%[보조4뇌%'
            """,
            (lo, hi),
        ).fetchone()[0]
    )


def snapshot(label: str, lo: int, hi: int) -> dict[str, Any]:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        mx = con.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0]
        review_rows = con.execute("SELECT COUNT(*) FROM testlotto_brain_review").fetchone()[0]
        learn = [
            {k: r[k] for k in r.keys()}
            for r in con.execute(
                "SELECT brain_tag, last_draw_no, review_count FROM testlotto_brain_learn_state"
            ).fetchall()
        ]
        return {
            "label": label,
            "draw_range": [lo, hi],
            "draws_max": int(mx or 0),
            "brain_review_rows": int(review_rows or 0),
            "brain_stats": _brain_stats(con, lo, hi),
            "pipe_marker_rows": _pipe_marker_count(con, lo, hi),
            "learn_states": learn,
        }
    finally:
        con.close()


def backup_db() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = ROOT / "backups" / f"{stamp}_KREVIEW전"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "lotto_testlotto.db"
    shutil.copy2(DB, dest)
    logger.info("backup -> %s", dest)
    return dest


def run_loop(start: int, end: int, *, reset: bool) -> dict[str, Any]:
    from app.testlotto.learn_state import reset_learn_states
    from app.testlotto.models import init_testlotto_db
    from app.testlotto.walkforward import run_review_loop

    init_testlotto_db()
    if reset:
        reset_learn_states()
        logger.info("learn_state reset OK")

    t0 = time.perf_counter()
    summary = run_review_loop(start, end, progress_every=25)
    elapsed = round(time.perf_counter() - t0, 1)
    summary["elapsed_sec"] = elapsed
    summary["start_draw"] = start
    summary["end_draw"] = end
    logger.info("loop done reviewed=%s skipped=%s elapsed=%ss", summary.get("reviewed"), summary.get("skipped"), elapsed)
    return summary


def verify(after: dict[str, Any], before: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    lo, hi = after["draw_range"]
    pipe = after.get("pipe_marker_rows", 0)
    expected_min = after["brain_stats"].get("stat", {}).get("n", 0)
    checks["pipe_markers_gt0"] = pipe > 0
    checks["pipe_markers_ge_stat_n"] = pipe >= expected_min * 0.9 if expected_min else pipe > 0
    checks["review_rows_positive"] = after.get("brain_review_rows", 0) > 3000

    before_ref = {}
    if BEFORE_REF.is_file():
        ref = json.loads(BEFORE_REF.read_text(encoding="utf-8"))
        before_ref = (ref.get("brain_review") or {}).get("full_2_to_max") or {}

    drift: list[str] = []
    for tag, v in after.get("brain_stats", {}).items():
        old = before_ref.get(tag, {}).get("avg_m")
        if old is not None and abs(v["avg_m"] - float(old)) > 0.15:
            drift.append(f"{tag}: was={old} now={v['avg_m']}")
    checks["avg_drift_within_015"] = len(drift) == 0
    checks["drift_notes"] = drift

    checks["verify_pass"] = all(
        checks[k] for k in ("pipe_markers_gt0", "review_rows_positive")
    )
    return checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--start", type=int, default=2)
    ap.add_argument("--end", type=int, default=1234)
    ap.add_argument("--no-reset", action="store_true", help="learn_state 유지 (비권장)")
    args = ap.parse_args()

    if not DB.is_file():
        logger.error("DB missing: %s", DB)
        return 1

    lo, hi = args.start, args.end
    before = snapshot("before", lo, hi)
    print(json.dumps({"phase": "before", **before}, ensure_ascii=False, indent=2))

    if not args.execute:
        print("\n[DRY-RUN] --execute 없음. backup+reset+loop 미실행.")
        return 0

    backup_path = backup_db()
    before_run = snapshot("before_run", lo, hi)

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(fh)

    loop_summary = run_loop(lo, hi, reset=not args.no_reset)
    after = snapshot("after", lo, hi)
    checks = verify(after, before_run)

    out = {
        "id": "K-REVIEW-RUN",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "backup": str(backup_path),
        "window": [lo, hi],
        "before": before_run,
        "after": after,
        "loop": {
            "reviewed": loop_summary.get("reviewed"),
            "skipped": loop_summary.get("skipped"),
            "elapsed_sec": loop_summary.get("elapsed_sec"),
        },
        "checks": checks,
        "verify_pass": checks.get("verify_pass", False),
    }

    tag = "pilot" if lo >= 1132 else "full"
    out_path = OUT_DIR / f"20260728_KREVIEW_{tag}_{lo}_{hi}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\nWrote {out_path}")
    print(f"verify_pass={out['verify_pass']}")
    return 0 if out["verify_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
