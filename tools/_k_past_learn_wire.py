# -*- coding: utf-8 -*-
"""K-PAST-LEARN-WIRE — 과거학습 구조 패치 smoke + solo n50.

Usage:
  python tools/_k_past_learn_wire.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KPAST_LEARN_WIRE.json"
OUT_MD = ROOT / "reports" / "20260808_KPAST_LEARN_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def smoke() -> dict:
    from app.testlotto.brains.stat_brain import past_learn, transition_v1
    from app.testlotto.brains.stat_brain.predict import run
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    flags = past_learn.flags_snapshot()
    set_learn_as_of(1235)
    draws = _get_draws_before(1235)
    sets = run(draws, 5)
    methods = [s.get("method") for s in sets]
    has_pl = all(isinstance(s.get("past_learn"), dict) for s in sets)
    tags_ok = any(
        s.get("past_learn", {}).get("tags") or "[과거학습:" in str(s.get("reasoning", ""))
        for s in sets
    )
    return {
        "flags": flags,
        "TRANSITION_V1_WIRE": bool(transition_v1.TRANSITION_V1_WIRE),
        "n_sets": len(sets),
        "methods": methods,
        "has_past_learn_field": has_pl,
        "sample_reasoning": (sets[0].get("reasoning") if sets else "")[:180],
        "sample_nums": sets[0].get("nums") if sets else [],
        "smoke_ok": (
            len(sets) == 5
            and all(m == "과거학습" for m in methods)
            and has_pl
            and flags["PAST_LEARN_WIRE"]
            and flags["PAST_LEARN_ENGINE_V2"]
            and not flags["PAST_LEARN_ASSOC_HINT"]
            and not transition_v1.TRANSITION_V1_WIRE
        ),
        "tags_present": tags_ok,
    }


def solo_n50() -> dict:
    """과거학습 solo best-of-5 · 1035~1084 (빠른 튜닝 베이스)."""
    from app.testlotto.brains.stat_brain.predict import run
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    actuals = {}
    for r in conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1035 AND 1084"
    ):
        d = dict(r)
        actuals[int(d["draw_no"])] = {int(d[f"num{k}"]) for k in range(1, 7)}
    conn.close()
    bests = []
    for dno in range(1035, 1085):
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        sets = run(draws, 5)
        act = actuals[dno]
        best = max(len(set(s["nums"]) & act) for s in sets) if sets else 0
        bests.append(best)
    n = len(bests)
    ge3 = sum(1 for b in bests if b >= 3)
    return {
        "draw_range": [1035, 1084],
        "n": n,
        "mean_best": round(sum(bests) / n, 6) if n else 0,
        "ge3_rate": round(ge3 / n, 6) if n else 0,
        "ge3_count": ge3,
        "note": "튜닝 베이스라인(solo n50) · fusion n200은 별도",
    }


def main() -> int:
    # ensure clean env for default flags
    for k in ("K_PAST_LEARN", "K_STAT_ENGINE_V2", "K_PAST_LEARN_ASSOC", "K_STAT_TRANSITION_V1"):
        os.environ.pop(k, None)
    sm = smoke()
    n50 = solo_n50()
    ok = bool(sm["smoke_ok"])
    payload = {
        "id": "K-PAST-LEARN-WIRE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS" if ok else "FAIL",
        "wire": True,
        "pass": ok,
        "smoke": sm,
        "solo_n50": n50,
        "tuning_next": [
            "SOFT_WEIGHT / SOFT_CONF_CAP 스윕",
            "K_PAST_LEARN_ASSOC=1 A/B (전수 NOISE 주의)",
            "fusion n200 vs pin 0.135",
        ],
        "forbid": ["random.choices", "engine.py 로직 대치 아닌 플래그", "당첨P↑ 과장"],
        "tool": "tools/_k_past_learn_wire.py",
        "module": "app/testlotto/brains/stat_brain/past_learn.py",
        "prior": "docs/benchmarks/20260808_KSTAT_NUM_ASSOC_FULL.json",
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# K-PAST-LEARN-WIRE — 과거학습 구조 패치 (2026-08-08)",
        "",
        f"- **판정:** `{payload['verdict']}` · wire 구조 ON",
        f"- flags: `{sm['flags']}`",
        f"- TRANSITION_V1_WIRE=`{sm['TRANSITION_V1_WIRE']}` (OFF 유지)",
        f"- smoke_ok=`{sm['smoke_ok']}` · methods=`{sm['methods']}`",
        f"- solo n50: mean_best=**{n50['mean_best']}** · ge3=**{n50['ge3_rate']}**",
        f"- sample: `{sm['sample_reasoning']}`",
        "",
        "## 구조",
        "",
        "1. engine v2 (장·단 윈도우) via past_learn",
        "2. aux_hint",
        "3. past_learn soft(미출/1yHot·Cold) · ASSOC 기본 OFF",
        "4. diversity.pick · method=`과거학습`",
        "",
        "## 롤백",
        "",
        "- `K_PAST_LEARN=0` · `K_STAT_ENGINE_V2=0`",
        "",
        f"- tool: `{payload['tool']}`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"ok": ok, "ge3": n50["ge3_rate"], "mean": n50["mean_best"]}, ensure_ascii=False), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
