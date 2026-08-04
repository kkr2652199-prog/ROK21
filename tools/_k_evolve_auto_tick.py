# -*- coding: utf-8 -*-
"""K-EVOLVE-AUTO S1 — tick CLI (기본 dry-run).

Usage:
  python tools/_k_evolve_auto_tick.py
  python tools/_k_evolve_auto_tick.py --lookback 5
  python tools/_k_evolve_auto_tick.py --apply   # S1에서는 거부됨
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KEVOLVE_AUTO_S1.json"
OUT_MD = ROOT / "reports" / "20260805_KEVOLVE_AUTO_S1.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback", type=int, default=5)
    ap.add_argument(
        "--apply",
        action="store_true",
        help="S1에서 거부됨 · S2+ 전용",
    )
    args = ap.parse_args()

    from app.testlotto.evolve_auto import (
        AUTO_FLAG_ENV,
        evolve_auto_enabled,
        get_auto_state,
        tick,
    )

    dry = not args.apply
    print(
        f"K-EVOLVE-AUTO S1 tick dry_run={dry} {AUTO_FLAG_ENV}={evolve_auto_enabled()}",
        flush=True,
    )
    result = tick(dry_run=dry, lookback=args.lookback)
    state = get_auto_state()

    passed = bool(result.get("ok")) and dry and result.get("dry_run") is True
    payload = {
        "id": "K-EVOLVE-AUTO-S1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "step": "S1",
        "dry_run": dry,
        "EVOLVE_AUTO": evolve_auto_enabled(),
        "tick": result,
        "state": state,
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
        "wire": False,
        "note": "S1=plan+state only · SCORE/PREDICT apply 없음",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    actions = result.get("mandatory_actions") or result.get("actions") or []
    lines = [
        "# K-EVOLVE-AUTO S1 — dry-run tick",
        "",
        f"📅 {payload['ts'][:10]} · **{payload['verdict']}** · dry_run=**{dry}** · wire=**False**",
        "",
        "## 0) 한 줄",
        "",
        "AUTO 상태테이블 + tick 계획만 수행. 예측/채점 **미실행**.",
        "",
        "## 1) 관측",
        "",
        f"- max lotto_draws = **{result.get('max_lotto_draw')}**",
        f"- evolve_log max = **{result.get('evolve_log_max')}**",
        f"- next_predict = **{result.get('next_predict_draw')}**",
        f"- G1 EVOLVE_AUTO = **{evolve_auto_enabled()}**",
        f"- G2 recent log = **{(result.get('gates') or {}).get('G2_recent_log')}**",
        f"- blocked_for_apply = {result.get('blocked_for_apply')}",
        "",
        "## 2) 계획 액션 (미실행)",
        "",
    ]
    for a in actions:
        lines.append(
            f"- `{a.get('op')}` draw={a.get('draw_no')} · {a.get('reason')}"
        )
    if not actions:
        lines.append("- (mandatory 없음)")
    opt = [a for a in (result.get("actions") or []) if a.get("optional")]
    if opt:
        lines.append("")
        lines.append("optional:")
        for a in opt:
            lines.append(f"- `{a.get('op')}` draw={a.get('draw_no')}")
    lines.extend(
        [
            "",
            "## 3) 상태",
            "",
            f"- phase = `{state.get('phase')}`",
            f"- last_completed_draw = {state.get('last_completed_draw')}",
            "",
            "## 4) 다음",
            "",
            "- S2: SCORE 자동(캐시 있는 미로그 회차) · 형 GO + 별도 승인",
            "- `EVOLVE_AUTO=1` 없이는 apply 금지 유지",
            "",
            f"근거: `{OUT_JSON.name}` · 설계 `20260805_KEVOLVE_AUTO_DESIGN.md`",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({
        "pass": passed,
        "max_draw": result.get("max_lotto_draw"),
        "evolve_max": result.get("evolve_log_max"),
        "mandatory": len(result.get("mandatory_actions") or []),
        "blocked": result.get("blocked_for_apply"),
        "phase": state.get("phase"),
    }, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
