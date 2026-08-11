# -*- coding: utf-8 -*-
"""K-QUOTA-MIN-EACH-GATE — 3뇌 최소1장 게이트.

base=min_each0 dominance → m4/r1/s0
cand=min_each1 → 전뇌≥1 · Σ=5
live referee 가중으로 실측. ge3미사용.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KQUOTA_MIN_EACH_GATE.json"
OUT_MD = ROOT / "reports" / "20260812_KQUOTA_MIN_EACH_GATE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> None:
    from app.testlotto.brains import coordinator as coord
    from app.testlotto.learn_state import get_referee_weights
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    set_learn_as_of(1237)
    live = get_referee_weights()
    qw = coord._get_quota_weights()

    saved = int(coord.QUOTA_ADAPTIVE_MIN_EACH)
    try:
        coord.QUOTA_ADAPTIVE_MIN_EACH = 0
        q0 = coord._compute_dynamic_quota(qw, total=5)
        coord.QUOTA_ADAPTIVE_MIN_EACH = 1
        q1 = coord._compute_dynamic_quota(qw, total=5)
    finally:
        coord.QUOTA_ADAPTIVE_MIN_EACH = saved

    # 합성 케이스: 균등 / 강한 dominance
    cases = {
        "live": qw,
        "flat": {"stat": 1 / 3, "markov": 1 / 3, "review": 1 / 3},
        "dom_markov": {"stat": 0.20, "markov": 0.50, "review": 0.30},
    }
    case_out: dict[str, Any] = {}
    for name, w in cases.items():
        coord.QUOTA_ADAPTIVE_MIN_EACH = 0
        a = coord._compute_dynamic_quota(w, total=5)
        coord.QUOTA_ADAPTIVE_MIN_EACH = 1
        b = coord._compute_dynamic_quota(w, total=5)
        case_out[name] = {
            "weights": {k: round(float(v), 6) for k, v in w.items()},
            "min0": a,
            "min1": b,
            "min1_all_ge1": all(v >= 1 for v in b.values()),
            "min1_sum5": sum(b.values()) == 5,
        }
    coord.QUOTA_ADAPTIVE_MIN_EACH = saved

    detail = {
        "live_min0_has_zero": any(v == 0 for v in q0.values()),
        "live_min1_all_ge1": all(v >= 1 for v in q1.values()),
        "live_min1_sum5": sum(q1.values()) == 5,
        "cases_all_ge1": all(c["min1_all_ge1"] and c["min1_sum5"] for c in case_out.values()),
        "code_live_min_each": int(coord.QUOTA_ADAPTIVE_MIN_EACH),
    }
    # APPLY already in code (=1). Gate confirms behavior.
    ok = (
        detail["live_min1_all_ge1"]
        and detail["live_min1_sum5"]
        and detail["cases_all_ge1"]
        and detail["code_live_min_each"] == 1
    )
    verdict = "APPLY_OK" if ok else "GATE_FAIL"

    out = {
        "id": "K-QUOTA-MIN-EACH-GATE",
        "ts": _now(),
        "live_referee": {k: round(float(v), 6) for k, v in live.items()},
        "quota_weights": {k: round(float(v), 6) for k, v in qw.items()},
        "quota_min0": q0,
        "quota_min1": q1,
        "cases": case_out,
        "gate_detail": detail,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "note": "단계⑧ · 1237아님 · dominance 보정+min_each=1",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = f"""# K-QUOTA-MIN-EACH-GATE

시각: {out['ts']} · 단계⑧

## 판정 **{verdict}**

| | min_each=0 | min_each=1 (live) |
|--|------------|-------------------|
| quota | `{q0}` | `{q1}` |

### 케이스
| name | min0 | min1 | all≥1 |
|------|------|------|-------|
"""
    for name, c in case_out.items():
        md += f"| {name} | `{c['min0']}` | `{c['min1']}` | {c['min1_all_ge1']} |\n"
    md += f"""
## 코드
- `QUOTA_ADAPTIVE_MIN_EACH=1`
- dominance 분기에서도 min_each 이체 보정
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict, "q0", q0, "q1", q1)
    print("WROTE", OUT_JSON)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
