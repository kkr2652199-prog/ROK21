# -*- coding: utf-8 -*-
"""K-EVOLVE-AUTO tick CLI.

Usage:
  python tools/_k_evolve_auto_tick.py                 # S1 dry-run
  python tools/_k_evolve_auto_tick.py --apply-score   # S2 SCORE
  python tools/_k_evolve_auto_tick.py --apply-predict # S3 PREDICT(+SCORE)
  EVOLVE_AUTO=1 python tools/_k_evolve_auto_tick.py --ops  # S4 운영
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
    ap.add_argument("--apply-score", action="store_true", help="S2 SCORE only")
    ap.add_argument(
        "--apply-predict",
        action="store_true",
        help="S3 PREDICT + SCORE(if drawn) + optional next PREDICT",
    )
    ap.add_argument(
        "--ops",
        action="store_true",
        help="S4 ops — requires EVOLVE_AUTO=1 · SCORE/PREDICT + mean feedback",
    )
    args = ap.parse_args()

    from app.testlotto.evolve_auto import (
        AUTO_FLAG_ENV,
        evolve_auto_enabled,
        get_auto_state,
        tick,
    )

    modes = sum([bool(args.apply_predict), bool(args.apply_score), bool(args.ops)])
    if modes > 1:
        print("use only one of --apply-score / --apply-predict / --ops", flush=True)
        return 2

    if args.ops:
        step = "S4"
        out_json = ROOT / "docs" / "benchmarks" / "20260805_KEVOLVE_AUTO_S4.json"
        out_md = ROOT / "reports" / "20260805_KEVOLVE_AUTO_S4.md"
        print(
            f"K-EVOLVE-AUTO S4 ops {AUTO_FLAG_ENV}={evolve_auto_enabled()}",
            flush=True,
        )
        result = tick(dry_run=False, lookback=args.lookback, apply_ops=True)
        passed = bool(result.get("ok")) and bool(result.get("apply_ops"))
        note = "S4 ops · EVOLVE_AUTO=1 · mean feedback(기존) · λ/covering OFF · weight=0"
    elif args.apply_predict:
        step = "S3"
        out_json = ROOT / "docs" / "benchmarks" / "20260805_KEVOLVE_AUTO_S3.json"
        out_md = ROOT / "reports" / "20260805_KEVOLVE_AUTO_S3.md"
        print(
            f"K-EVOLVE-AUTO S3 apply-predict {AUTO_FLAG_ENV}={evolve_auto_enabled()}",
            flush=True,
        )
        result = tick(
            dry_run=False, lookback=args.lookback, apply_predict=True
        )
        passed = bool(result.get("ok")) and bool(result.get("executed"))
        note = "S3 PREDICT+SCORE · feedback/λ/covering 없음 · weight=0"
    elif args.apply_score:
        step = "S2"
        out_json = ROOT / "docs" / "benchmarks" / "20260805_KEVOLVE_AUTO_S2.json"
        out_md = ROOT / "reports" / "20260805_KEVOLVE_AUTO_S2.md"
        print(
            f"K-EVOLVE-AUTO S2 apply-score {AUTO_FLAG_ENV}={evolve_auto_enabled()}",
            flush=True,
        )
        result = tick(dry_run=False, lookback=args.lookback, apply_score=True)
        passed = bool(result.get("ok")) and bool(result.get("executed"))
        note = "S2 SCORE apply · PREDICT/feedback 없음 · weight=0"
    else:
        step = "S1"
        out_json = ROOT / "docs" / "benchmarks" / "20260805_KEVOLVE_AUTO_S1.json"
        out_md = ROOT / "reports" / "20260805_KEVOLVE_AUTO_S1.md"
        print(
            f"K-EVOLVE-AUTO S1 dry-run {AUTO_FLAG_ENV}={evolve_auto_enabled()}",
            flush=True,
        )
        result = tick(dry_run=True, lookback=args.lookback)
        passed = bool(result.get("ok")) and result.get("dry_run") is True
        note = "S1=plan+state only"

    state = get_auto_state()
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / out_md.name
    payload = {
        "id": f"K-EVOLVE-AUTO-{step}",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "step": step,
        "dry_run": result.get("dry_run"),
        "apply_score": bool(args.apply_score),
        "apply_predict": bool(args.apply_predict),
        "apply_ops": bool(args.ops),
        "EVOLVE_AUTO": evolve_auto_enabled(),
        "tick": result,
        "state": state,
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
        "wire": bool(args.ops) and evolve_auto_enabled(),
        "note": note,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# K-EVOLVE-AUTO {step}",
        "",
        f"📅 {payload['ts'][:10]} · **{payload['verdict']}** · {note}",
        "",
        f"- {AUTO_FLAG_ENV} = **{evolve_auto_enabled()}**",
        f"- healthy_idle = {result.get('healthy_idle')}",
        "",
        "## 실행/계획",
        "",
    ]
    for e in result.get("executed") or []:
        a = e.get("action") or {}
        r = e.get("result") or {}
        lines.append(
            f"- `{a.get('op')}` draw=**{r.get('draw_no', a.get('draw_no'))}** "
            f"ok={r.get('ok')} scored={r.get('scored', a.get('op')=='SCORE')}"
        )
    for s in result.get("skipped") or []:
        a = s.get("action") or {}
        lines.append(
            f"- skip `{a.get('op')}` draw={a.get('draw_no')} · {s.get('reason')}"
        )
    if not (result.get("executed") or result.get("skipped") or result.get("mandatory_actions")):
        for a in result.get("actions") or []:
            lines.append(f"- plan `{a.get('op')}` draw={a.get('draw_no')}")
    if result.get("errors"):
        lines.extend(
            [
                "",
                "## errors",
                f"```json\n{json.dumps(result['errors'], ensure_ascii=False, indent=2)}\n```",
            ]
        )
    if result.get("error"):
        lines.extend(["", f"- error: `{result.get('error')}`"])
    pa = result.get("plan_after") or {}
    lines.extend(
        [
            "",
            "## after",
            "",
            f"- evolve_log_max = **{pa.get('evolve_log_max', result.get('evolve_log_max'))}**",
            f"- G2 = **{pa.get('g2_pass', (result.get('gates') or {}).get('G2_recent_log'))}**",
            f"- phase = `{state.get('phase')}`",
            f"- next_predict = {pa.get('next_predict_draw', result.get('next_predict_draw'))}",
            "",
            f"근거: `{out_json.name}`",
            "",
            "운영: `$env:EVOLVE_AUTO=1; python tools/_k_evolve_auto_tick.py --ops` (PowerShell)",
            "롤백: `EVOLVE_AUTO=0` 또는 미설정 · DB 로그 삭제 없음",
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
                "EVOLVE_AUTO": evolve_auto_enabled(),
                "executed": len(result.get("executed") or []),
                "skipped": len(result.get("skipped") or []),
                "phase": state.get("phase"),
                "healthy_idle": result.get("healthy_idle"),
                "evolve_max": pa.get("evolve_log_max", result.get("evolve_log_max")),
                "error": result.get("error"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
