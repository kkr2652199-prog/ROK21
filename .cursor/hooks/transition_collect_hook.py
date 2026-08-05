#!/usr/bin/env python3
"""stop 훅 — transition_log 자동 수집 (발권·coordinator 미접촉).

매 에이전트 stop 시 collect_latest(sim_k=2) 호출.
이미 적재된 (draw_no, sim_k) 는 SKIP.
결과는 logs/transition_collect.log 에 append.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "logs" / "transition_collect.log"


def main() -> int:
    sys.path.insert(0, str(ROOT))
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    try:
        from tools._k_transition_collect import collect_latest

        result = collect_latest(sim_k=2)
        line = json.dumps({"ts": ts, "ok": True, "result": result}, ensure_ascii=False)
    except Exception as e:
        line = json.dumps(
            {"ts": ts, "ok": False, "error": repr(e)}, ensure_ascii=False
        )
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    # Cursor hook: 항상 성공 종료 (수집 실패해도 에이전트 stop 차단 금지)
    print(json.dumps({"continue": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
