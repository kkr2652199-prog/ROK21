# -*- coding: utf-8 -*-
"""K-EVOLVE-AUTO S1 — tick CLI (기본 dry-run).

Usage:
  python tools/_k_evolve_auto_tick.py
  python tools/_k_evolve_auto_tick.py --lookback 5
  python tools/_k_evolve_auto_tick.py --apply-score   # S2 SCORE only
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback", type=int, default=5)
    ap.add_argument(
        "--apply-score",
        action="store_true",
        help="S2: SCORE 액션만 실행 (PREDICT 없음)",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="전체 apply — S3+ 전 거부",
    )
    args = ap.parse_args()

    from app.testlotto.evolve_auto import (
        AUTO_FLAG_ENV,
        evolve_auto_enabled,
        get_auto_state,
        tick,
    )

    if args.apply_score:
        step = "S2"
        out_json = ROOT / "docs" / "benchmarks" / "20260805_KEVOLVE_AUTO_S2.json"
        out_md = ROOT / "reports" / "20260805_KEVOLVE_AUTO_S2.md"
        print(
            f"K-EVOLVE-AUTO S2 apply-score {AUTO_FLAG_ENV}={evolve_auto_enabled()}",
            flush=True,
        )
        result = tick(dry_run=False, lookback=args.lookback, apply_score=True)
        passed = bool(result.get("ok")) and bool(result.get("executed"))
    else:
        step = "S1"
        out_json = ROOT / "docs" / "benchmarks" / "20260805_KEVOLVE_AUTO_S1.json"
        out_md = ROOT / "reports" / "20260805_KEVOLVE_AUTO_S1.md"
        dry = not args.apply
        print(
            f"K-EVOLVE-AUTO S1 tick dry_run={dry} {AUTO_FLAG_ENV}={evolve_auto_enabled()}",
            flush=True,
        )
        result = tick(dry_run=dry, lookback=args.lookback, apply_score=False)
        passed = bool(result.get("ok")) and dry and result.get("dry_run") is True

    state = get_auto_state()
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / out_md.name
    payload = {
        "id": f"K-EVOLVE-AUTO-{step}",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "step": step,
        "dry_run": result.get("dry_run"),
        "apply_score": bool(args.apply_score),
        "EVOLVE_AUTO": evolve_auto_enabled(),
        "tick": result,
        "state": state,
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
        "wire": False,
        "note": (
            "S2 SCORE apply · PREDICT/feedback 없음 · weight=0"
            if args.apply_score
            else "S1=plan+state only"
        ),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.apply_score:
        lines = [
            "# K-EVOLVE-AUTO S2 — SCORE apply",
            "",
            f"📅 {payload['ts'][:10]} · **{payload['verdict']}** · apply_score=**True**",
            "",
            "## 실행",
            "",
        ]
        for e in result.get("executed") or []:
            r = e.get("result") or {}
            lines.append(
                f"- SCORE draw=**{r.get('draw_no')}** ok · brains={r.get('brains')}"
            )
        if result.get("errors"):
            lines.append("")
            lines.append("## errors")
            lines.append(f"```json\n{json.dumps(result['errors'], ensure_ascii=False, indent=2)}\n```")
        lines.extend(
            [
                "",
                "## after",
                "",
                f"- evolve_log_max = **{(result.get('plan_after') or {}).get('evolve_log_max')}**",
                f"- G2 pass = **{(result.get('plan_after') or {}).get('g2_pass')}**",
                f"- phase = `{state.get('phase')}`",
                "",
                "## 다음",
                "",
                "- S3: PREDICT+SCORE 통합 · 형 GO",
                "- feedback/λ/covering wire 금지 유지",
                "",
                f"근거: `{out_json.name}`",
                "",
            ]
        )
    else:
        actions = result.get("mandatory_actions") or result.get("actions") or []
        lines = [
            "# K-EVOLVE-AUTO S1 — dry-run tick",
            "",
            f"📅 {payload['ts'][:10]} · **{payload['verdict']}** · dry_run=**{result.get('dry_run')}**",
            "",
            "## 계획 액션",
            "",
        ]
        for a in actions:
            lines.append(f"- `{a.get('op')}` draw={a.get('draw_no')} · {a.get('reason')}")
        lines.extend(
            [
                "",
                f"phase=`{state.get('phase')}` · 근거 `{out_json.name}`",
                "",
            ]
        )

    text = "\n".join(lines)
    out_md.write_text(text, encoding="utf-8")
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "pass": passed,
                "step": step,
                "evolve_max_after": (result.get("plan_after") or {}).get("evolve_log_max")
                or result.get("evolve_log_max"),
                "executed": len(result.get("executed") or []),
                "phase": state.get("phase"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
