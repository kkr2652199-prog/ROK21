# -*- coding: utf-8 -*-
"""FULL 스냅샷 — hybrid/mean 피드백 이후 fusion 회귀 기준.

기존 20260803_KFUTURE_WIRE_FULL.json 은 덮지 않음.
Usage:
  python tools/_k_full_snapshot_post_evolve.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KFUTURE_FULL_POST_EVOLVE.json"
OUT_MD = ROOT / "reports" / "20260804_KFUTURE_FULL_POST_EVOLVE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
BASE_JSON = ROOT / "docs" / "benchmarks" / "20260803_KFUTURE_WIRE_FULL.json"


def main() -> int:
    from app.testlotto.brains import coordinator as coord_mod
    from tools._k_future_wire_revalidate import run_backtest, write_report

    print(
        f"FULL snapshot post-evolve · FEEDBACK_MATCH_MODE={getattr(coord_mod, 'FEEDBACK_MATCH_MODE', '?')}",
        flush=True,
    )
    payload = run_backtest("full")
    payload["id"] = "K-FUTURE-FULL-POST-EVOLVE"
    payload["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload["snapshot_note"] = (
        "After K-REPACK-HYBRID-WIRE + K-EVOLVE-SIGNAL(mean). "
        "signal_pool hybrid는 fusion 경로와 별개 · 본 스냅샷은 coordinator WF."
    )
    payload["live_flags"] = {
        "FEEDBACK_MATCH_MODE": getattr(coord_mod, "FEEDBACK_MATCH_MODE", None),
        "BUCKET_SELECT_MODE": getattr(coord_mod, "BUCKET_SELECT_MODE", None),
    }

    base = None
    if BASE_JSON.exists():
        base = json.loads(BASE_JSON.read_text(encoding="utf-8"))
        payload["vs_prev_full"] = {
            "prev_id": base.get("id"),
            "prev_ge3": base["overall"]["ge3_rate"],
            "new_ge3": payload["overall"]["ge3_rate"],
            "delta_ge3": round(
                float(payload["overall"]["ge3_rate"]) - float(base["overall"]["ge3_rate"]),
                4,
            ),
            "prev_by_period": {
                k: v.get("ge3_rate") for k, v in (base.get("by_period") or {}).items()
            },
            "new_by_period": {
                k: v.get("ge3_rate") for k, v in (payload.get("by_period") or {}).items()
            },
        }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(payload, OUT_JSON, OUT_MD, DRIVE)

    # prepend comparison section
    extra = [
        "",
        "## POST-EVOLVE 비교",
        "",
        f"- FEEDBACK_MATCH_MODE = `{payload['live_flags']['FEEDBACK_MATCH_MODE']}`",
        f"- 구 FULL ge3 = **{(base or {}).get('overall', {}).get('ge3_rate', '미확인')}**",
        f"- 신 FULL ge3 = **{payload['overall']['ge3_rate']}**",
        f"- Δ = **{payload.get('vs_prev_full', {}).get('delta_ge3', '미확인')}**",
        "",
        "구 FULL JSON은 유지: `docs/benchmarks/20260803_KFUTURE_WIRE_FULL.json`",
        "",
    ]
    text = OUT_MD.read_text(encoding="utf-8")
    # insert after title block
    parts = text.split("\n", 3)
    if len(parts) >= 4:
        text = "\n".join(parts[:3]) + "\n" + "\n".join(extra) + parts[3]
    else:
        text = text + "\n".join(extra)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.write_text(text, encoding="utf-8")

    print(
        f"DONE ge3={payload['overall']['ge3_rate']:.4f} "
        f"vs_prev={payload.get('vs_prev_full', {}).get('delta_ge3')} → {OUT_JSON.name}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
