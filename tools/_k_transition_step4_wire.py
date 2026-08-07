# -*- coding: utf-8 -*-
"""K-TRANSITION-STEP4-WIRE — transition_v1 stat 슬롯 배선 검증 (형 GO).

Usage:
  python tools/_k_transition_step4_wire.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KTRANSITION_STEP4_WIRE.json"
OUT_MD = ROOT / "reports" / "20260805_KTRANSITION_STEP4_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def load_draws_upto(max_no: int) -> list[dict]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT draw_no,num1,num2,num3,num4,num5,num6
        FROM lotto_draws WHERE draw_no <= ? ORDER BY draw_no
        """,
        (max_no,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def smoke_predict() -> dict:
    from app.testlotto.brains.stat_brain import predict, transition_v1
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    draws = load_draws_upto(1234)
    set_learn_as_of(1235)
    os.environ["K_STAT_TRANSITION_V1"] = "1"
    # force module flag read
    transition_v1.TRANSITION_V1_WIRE = True
    sets_on = predict.run(draws, n_sets=5)
    methods_on = [s.get("method") for s in sets_on]

    os.environ["K_STAT_TRANSITION_V1"] = "0"
    sets_off = predict.run(draws, n_sets=5)
    methods_off = [s.get("method") for s in sets_off]

    # restore GO default
    os.environ.pop("K_STAT_TRANSITION_V1", None)
    transition_v1.TRANSITION_V1_WIRE = True

    ok = (
        len(sets_on) == 5
        and len(sets_off) == 5
        and all(len(s["nums"]) == 6 for s in sets_on)
        and any(str(m).startswith("전이") for m in methods_on)
        and all(
            str(m) in ("과거학습", "통계요정") or "과거" in str(m) or "통계" in str(m)
            for m in methods_off
        )
    )
    return {
        "smoke_ok": ok,
        "wire_default": transition_v1.TRANSITION_V1_WIRE,
        "on_methods": methods_on,
        "off_methods": methods_off,
        "on_sample": sets_on[0]["nums"] if sets_on else [],
        "rollback_env": "K_STAT_TRANSITION_V1=0",
    }


def mini_wf(n: int = 50) -> dict:
    """Live stat_brain.predict only · best-of-5 ge3 on last n draws ending 1234."""
    from app.testlotto.brains.stat_brain import predict, transition_v1
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    transition_v1.TRANSITION_V1_WIRE = True
    os.environ.pop("K_STAT_TRANSITION_V1", None)

    hi = 1234
    lo = hi - n + 1
    hits_ge3 = 0
    hit_counts: list[int] = []
    all_draws = load_draws_upto(hi)
    by_no = {int(d["draw_no"]): d for d in all_draws}

    for t in range(lo, hi + 1):
        hist = [d for d in all_draws if int(d["draw_no"]) < t]
        if len(hist) < 3:
            continue
        set_learn_as_of(t)
        actual = by_no[t]
        act = {int(actual[f"num{k}"]) for k in range(1, 7)}
        sets = predict.run(hist, n_sets=5)
        best = max(len(act & set(s["nums"])) for s in sets) if sets else 0
        hit_counts.append(best)
        if best >= 3:
            hits_ge3 += 1

    nn = len(hit_counts)
    ge3_rate = hits_ge3 / nn if nn else 0.0
    mean_best = sum(hit_counts) / nn if nn else 0.0
    return {
        "draw_range": [lo, hi],
        "n": nn,
        "ge3_count": hits_ge3,
        "ge3_rate": round(ge3_rate, 6),
        "mean_best_of_5": round(mean_best, 6),
        "baseline_fusion_ge3_ref": 0.135,
        "note": "stat solo best-of-5 · fusion 전체 아님 · n50 smoke",
    }


def main() -> int:
    print("[smoke]", flush=True)
    smoke = smoke_predict()
    print(json.dumps(smoke, ensure_ascii=False), flush=True)
    print("[mini_wf n50]", flush=True)
    wf = mini_wf(50)
    print(json.dumps(wf, ensure_ascii=False), flush=True)

    verdict = "PASS" if smoke["smoke_ok"] else "FAIL"
    # wire is on by design (형 GO) — note HOLD prior
    payload = {
        "id": "K-TRANSITION-STEP4-WIRE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "wire": True,
        "flag": {
            "TRANSITION_V1_WIRE": True,
            "env_off": "K_STAT_TRANSITION_V1=0",
            "module": "app/testlotto/brains/stat_brain/transition_v1.py",
            "entry": "app/testlotto/brains/stat_brain/predict.py",
        },
        "smoke": smoke,
        "mini_wf_n50": wf,
        "prior_hold_note": (
            "STEP3 DESIGN_HOLD(nopeek≈2.007) 상태에서 형 A=STEP4 GO. "
            "solo n50는 참고 · fusion n200 재검증 권고."
        ),
        "forbid_kept": [
            "random.choices",
            "engine.py 미수정",
            "auto-tune",
        ],
        "pass": verdict == "PASS",
        "tool": "tools/_k_transition_step4_wire.py",
        "prior": "docs/benchmarks/20260805_KTRANSITION_STEP3_DESIGN.json",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    md = "\n".join(
        [
            "# K-TRANSITION-STEP4-WIRE — transition_v1 배선 (2026-08-05)",
            "",
            f"- **판정:** `{verdict}` · wire=`True` (형 A GO)",
            f"- flag ON 기본 · 롤백: `K_STAT_TRANSITION_V1=0` 또는 `TRANSITION_V1_WIRE=False`",
            f"- smoke: `{smoke}`",
            f"- mini_wf n50: ge3_rate=**{wf['ge3_rate']}** mean_best=**{wf['mean_best_of_5']}**",
            f"- prior HOLD note: {payload['prior_hold_note']}",
            "",
            f"- tool: `{payload['tool']}`",
            "",
        ]
    )
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({"ok": True, "verdict": verdict, "wf": wf}, ensure_ascii=False))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
