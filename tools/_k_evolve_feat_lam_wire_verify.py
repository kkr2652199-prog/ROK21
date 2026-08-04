# -*- coding: utf-8 -*-
"""K-EVOLVE-FEAT-LAM-WIRE — review λ=0.3 검증.

1) evolve_log as_of 재현 → review ge3 == SIGNAL survey 0.145
2) smoke: build_pool_and_repack review assemble=feat_lam_0.3
3) schema=3

Usage:
  python tools/_k_evolve_feat_lam_wire_verify.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KEVOLVE_FEAT_LAM_WIRE.json"
OUT_MD = ROOT / "reports" / "20260804_KEVOLVE_FEAT_LAM_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

REF_REVIEW_GE3 = 0.145
REF_BASELINE = 0.135
NULL5 = 0.1137
PIN = 0.1447
LO, HI = 1035, 1234


def main() -> int:
    from app.testlotto.feature_lambda import (
        FEATURE_LAMBDA_BY_BRAIN,
        apply_feature_lambda,
        load_bucket_stats_from_evolve,
        select_top5,
        candidates_from_pool_repack,
    )
    from app.testlotto.pool_view_cache import CACHE_SCHEMA_VERSION
    from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE, build_pool_and_repack
    from tools._k_evolve_signal_survey import _load_all_logs

    assert FEATURE_LAMBDA_WIRE is True
    assert FEATURE_LAMBDA_BY_BRAIN.get("review") == 0.3
    assert "stat" not in FEATURE_LAMBDA_BY_BRAIN
    assert "markov" not in FEATURE_LAMBDA_BY_BRAIN
    assert CACHE_SCHEMA_VERSION >= 3

    print("load evolve_log...", flush=True)
    logs = _load_all_logs(LO, HI)
    draw_nos = sorted(logs.keys())
    lam = 0.3
    bests = []
    for dno in draw_nos:
        row = logs[dno].get("review")
        if not row:
            continue
        buckets, gmean = load_bucket_stats_from_evolve("review", dno)
        cands = candidates_from_pool_repack(row["pool"], row["repack"])
        picked = select_top5(cands, buckets, lam, gmean)
        if not picked:
            continue
        bests.append(max(int(s.get("hits") or 0) for s in picked))

    n = len(bests)
    ge3 = sum(1 for x in bests if x >= 3)
    rate = round(ge3 / n, 4) if n else 0.0
    match = rate == REF_REVIEW_GE3
    print(
        f"offline review λ={lam} ge3={rate} ({ge3}/{n}) ref={REF_REVIEW_GE3} match={match}",
        flush=True,
    )

    # smoke live path
    smoke_dno = 1230
    print(f"smoke build_pool_and_repack({smoke_dno})...", flush=True)
    built = build_pool_and_repack(smoke_dno)
    rev = (built.get("repack_by_brain") or {}).get("review") or []
    modes = sorted({str(x.get("assemble") or "") for x in rev})
    smoke_ok = any(m.startswith("feat_lam_") for m in modes) and len(rev) == 5
    print(f"  review assemble={modes} n={len(rev)} ok={smoke_ok}", flush=True)

    # apply_feature_lambda unit on logged draw
    unit_ok = True
    sample = logs.get(1200, {}).get("review")
    if sample:
        lam_rows = apply_feature_lambda(
            "review", sample["pool"], sample["repack"], 1200
        )
        unit_ok = bool(lam_rows) and all(
            str(x.get("assemble", "")).startswith("feat_lam_") for x in lam_rows
        )
        print(f"  apply_feature_lambda(1200) ok={unit_ok} n={len(lam_rows or [])}", flush=True)

    passed = match and smoke_ok and unit_ok
    payload = {
        "id": "K-EVOLVE-FEAT-LAM-WIRE",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "brain": "review",
        "lambda": lam,
        "draw_range": [LO, HI],
        "n_eval": n,
        "ge3_rate": rate,
        "ge3_count": ge3,
        "mean_best": round(mean(bests), 4) if bests else 0.0,
        "ref_survey_ge3": REF_REVIEW_GE3,
        "ref_baseline_ge3": REF_BASELINE,
        "delta_vs_baseline": round(rate - REF_BASELINE, 4),
        "delta_vs_null": round(rate - NULL5, 4),
        "delta_vs_pin": round(rate - PIN, 4),
        "match_survey": match,
        "smoke": {"draw": smoke_dno, "assemble_modes": modes, "ok": smoke_ok},
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "FEATURE_LAMBDA_BY_BRAIN": dict(FEATURE_LAMBDA_BY_BRAIN),
        "stat_markov": "HOLD (not wired)",
        "verdict": "PASS" if passed else "FAIL",
        "pass": passed,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-EVOLVE-FEAT-LAM-WIRE — review λ=0.3",
        "",
        f"📅 {payload['ts'][:10]} · **{payload['verdict']}**",
        "",
        "## 결과",
        "",
        f"- review λ=**{lam}** ge3=**{rate}** ({ge3}/{n})",
        f"- vs SIGNAL survey ref **{REF_REVIEW_GE3}**: {'MATCH' if match else 'MISMATCH'}",
        f"- vs hybrid baseline **{REF_BASELINE}**: Δ={payload['delta_vs_baseline']:+.4f}",
        f"- CACHE_SCHEMA_VERSION=**{CACHE_SCHEMA_VERSION}**",
        f"- smoke {smoke_dno}: assemble={modes}",
        f"- stat/markov: **HOLD** (미배선)",
        "",
        f"근거: `{OUT_JSON.name}`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"pass": passed, "ge3": rate, "match": match}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
