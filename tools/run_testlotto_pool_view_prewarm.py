#!/usr/bin/env python3
"""pool-view 캐시 프리워arm CLI — import/배치용."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.models import init_testlotto_db  # noqa: E402
from app.testlotto.pool_view_cache import (  # noqa: E402
    get_or_build_pool_view,
    prewarm_pool_view_cache,
    prewarm_visible_range,
)


def main() -> int:
    p = argparse.ArgumentParser(description="testlotto pool-view cache prewarm")
    p.add_argument("--start", type=int, default=0, help="시작 회차 (0=visible range)")
    p.add_argument("--end", type=int, default=0, help="끝 회차")
    p.add_argument("--window", type=int, default=40, help="visible range window")
    p.add_argument("--draw", type=int, action="append", dest="draws", help="단일 회차 (반복 가능)")
    args = p.parse_args()

    init_testlotto_db()

    if args.draws:
        for dno in args.draws:
            r = get_or_build_pool_view(dno)
            print(f"{dno}: ok={r.get('ok')} cached={r.get('cached')} ms={r.get('cache_ms')}")
        return 0

    if args.start > 0 and args.end > 0:
        summary = prewarm_pool_view_cache(args.start, args.end)
    else:
        summary = prewarm_visible_range(window=args.window)

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
