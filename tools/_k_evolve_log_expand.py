# -*- coding: utf-8 -*-
"""K-EVOLVE-LOG-EXPAND — evolve_log 53~1234 확장.

- 캐시 있는 회차: any_schema 백필
- miss: 순차 WF로 evolve_log만 (pool cache 미저장 · λ OFF)
- weight_applied=0 유지

Usage:
  python tools/_k_evolve_log_expand.py
  python tools/_k_evolve_log_expand.py --start 53 --end 1234
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KEVOLVE_LOG_EXPAND.json"
OUT_MD = ROOT / "reports" / "20260804_KEVOLVE_LOG_EXPAND.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=53)
    ap.add_argument("--end", type=int, default=1234)
    args = ap.parse_args()

    from app.testlotto.evolve_log import WEIGHT_APPLIED, backfill_expand_wf, get_evolve_log
    from app.testlotto.feature_lambda import FEATURE_LAMBDA_BY_BRAIN
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE

    init_testlotto_db()
    print(f"K-EVOLVE-LOG-EXPAND {args.start}~{args.end} ...", flush=True)
    result = backfill_expand_wf(args.start, args.end)

    conn = get_lotto_db()
    n_rows = conn.execute(
        "SELECT COUNT(*) FROM testlotto_evolve_log WHERE draw_no BETWEEN ? AND ?",
        (args.start, args.end),
    ).fetchone()[0]
    n_draws = conn.execute(
        "SELECT COUNT(DISTINCT draw_no) FROM testlotto_evolve_log "
        "WHERE draw_no BETWEEN ? AND ?",
        (args.start, args.end),
    ).fetchone()[0]
    mn_mx = conn.execute(
        "SELECT MIN(draw_no), MAX(draw_no) FROM testlotto_evolve_log"
    ).fetchone()
    conn.close()

    sample = get_evolve_log(100)
    sample2 = get_evolve_log(1200)
    summary = result["summary"]
    expected = args.end - args.start + 1
    passed = (
        int(n_draws) >= expected
        and WEIGHT_APPLIED == 0.0
        and result["filled_draws"] > 0
        and FEATURE_LAMBDA_WIRE is True
    )

    payload = {
        "id": "K-EVOLVE-LOG-EXPAND",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "draw_range": [args.start, args.end],
        "expected_draws": expected,
        "n_draws_logged": int(n_draws),
        "n_rows": int(n_rows),
        "log_min_max": [mn_mx[0], mn_mx[1]],
        "filled_from_cache": result["filled_from_cache"],
        "filled_from_wf": result["filled_from_wf"],
        "miss_draw": result["miss_draw"],
        "weight_applied": WEIGHT_APPLIED,
        "wire_to_predict": False,
        "feature_lambda_live": FEATURE_LAMBDA_WIRE,
        "feature_lambda_by_brain": dict(FEATURE_LAMBDA_BY_BRAIN),
        "summary": summary,
        "sample_100_ok": bool(sample and sample.get("ok")),
        "sample_1200_ok": bool(sample2 and sample2.get("ok")),
        "note": "miss구간 pool_cache 미저장 · 순차WF λ OFF · live λ/schema3 유지",
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-EVOLVE-LOG-EXPAND — evolve_log 53~1234",
        "",
        f"📅 {payload['ts'][:10]} · **{payload['verdict']}**",
        "",
        "## 결과",
        "",
        f"- range **{args.start}~{args.end}** · logged draws **{n_draws}** / expected {expected}",
        f"- from_cache **{result['filled_from_cache']}** · from_wf **{result['filled_from_wf']}** · miss **{result['miss_draw']}**",
        f"- weight_applied=**{WEIGHT_APPLIED}** · live FEATURE_LAMBDA_WIRE=**{FEATURE_LAMBDA_WIRE}**",
        f"- sample 100 ok={payload['sample_100_ok']} · 1200 ok={payload['sample_1200_ok']}",
        "",
        "## 뇌별 (발권 best 참고 · 학습입력 금지)",
        "",
        "| 뇌 | n | ge3_rate | avg_best | avg_mean |",
        "|----|---|---------:|---------:|---------:|",
    ]
    for tag, s in (summary.get("by_brain") or {}).items():
        lines.append(
            f"| {tag} | {s['n']} | **{s['ge3_rate']:.4f}** | {s['avg_best_hits']} | {s['avg_mean_hits']} |"
        )
    lines.extend(
        [
            "",
            "## 비고",
            "",
            "- miss 구간: 순차 WF · evolve_log만 · pool_view_cache **미저장**",
            "- 확장 중 λ OFF · 종료 후 live λ(review 0.3) 복원",
            "- 기존 n200 JSON 유지: `20260804_KEVOLVE_LOG.json`",
            "",
            f"근거: `{OUT_JSON.name}`",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({
        "pass": passed,
        "n_draws": int(n_draws),
        "from_cache": result["filled_from_cache"],
        "from_wf": result["filled_from_wf"],
    }, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
