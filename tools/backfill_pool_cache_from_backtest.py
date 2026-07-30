# -*- coding: utf-8 -*-
"""백테스트 draw_results 가 있는 회차의 pool-view 캐시 백필 (WF · 컨닝 없음)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.models import get_lotto_db, init_testlotto_db  # noqa: E402
from app.testlotto.pool_view_cache import (  # noqa: E402
    get_cached_pool_view,
    get_or_build_pool_view,
)


def _draws_needing_cache(draw_start: int = 0, draw_end: int = 0) -> list[int]:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        if draw_start > 0 and draw_end >= draw_start:
            rows = conn.execute(
                """
                SELECT DISTINCT d.draw_no
                FROM testlotto_backtest_draw_results d
                WHERE d.draw_no BETWEEN ? AND ?
                ORDER BY d.draw_no
                """,
                (draw_start, draw_end),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT DISTINCT draw_no
                FROM testlotto_backtest_draw_results
                ORDER BY draw_no
                """
            ).fetchall()
    finally:
        conn.close()

    out: list[int] = []
    for (dno,) in rows:
        dno = int(dno)
        if get_cached_pool_view(dno):
            continue
        out.append(dno)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Backfill pool-view cache from backtest draws")
    ap.add_argument("--draw-start", type=int, default=0)
    ap.add_argument("--draw-end", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pending = _draws_needing_cache(args.draw_start, args.draw_end)
    summary = {
        "pending": len(pending),
        "draw_start": args.draw_start or None,
        "draw_end": args.draw_end or None,
        "warmed": 0,
        "errors": [],
    }

    if args.dry_run:
        summary["sample"] = pending[:10]
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    for i, dno in enumerate(pending):
        if i % 20 == 0:
            print(f"  backfill {i}/{len(pending)} draw={dno}", flush=True)
        try:
            result = get_or_build_pool_view(dno)
            if result.get("ok"):
                summary["warmed"] += 1
            else:
                summary["errors"].append(f"{dno}: {result.get('error', result.get('message', 'unknown'))}")
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append(f"{dno}: {exc}")

    summary["errors"] = summary["errors"][:20]
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
