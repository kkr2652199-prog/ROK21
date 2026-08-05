# -*- coding: utf-8 -*-
"""K-TRANSITION-FUSION-N200 — transition_v1 배선 상태 fusion n200 (DB 미기록).

Usage:
  python tools/_k_transition_fusion_n200.py
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KTRANSITION_FUSION_N200.json"
OUT_MD = ROOT / "reports" / "20260805_KTRANSITION_FUSION_N200.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1035, 1234
BASELINE_GE3 = 0.135
RANDOM_GE3_TOP15 = 0.311  # 참고(티켓 ge3와 지표 다름)
STEP3_NOPEEK_GE3 = 0.274
PERIODS = {
    "early": (1035, 1101),
    "mid": (1102, 1167),
    "late": (1168, 1234),
}
SEED = 42


def env_check() -> dict[str, Any]:
    from app.testlotto.brains.stat_brain import transition_v1
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    # 검증 중 플래그 변경 금지 — 현재값만 확인
    wire = bool(transition_v1.TRANSITION_V1_WIRE)
    use = transition_v1._use_transition_v1()
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        n_log = int(
            conn.execute(
                "SELECT COUNT(*) AS c FROM transition_log WHERE sim_k=2"
            ).fetchone()["c"]
        )
    finally:
        conn.close()
    brains = ["markov", "review", "stat(transition_v1 if wired)"]
    env_ok = wire and use and n_log == 1134
    return {
        "env_ok": env_ok,
        "TRANSITION_V1_WIRE": wire,
        "use_transition_v1": use,
        "transition_log_rows": n_log,
        "brains": brains,
        "env_K_STAT_TRANSITION_V1": os.environ.get("K_STAT_TRANSITION_V1"),
    }


def load_actuals() -> dict[int, set[int]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT draw_no,num1,num2,num3,num4,num5,num6
        FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no
        """,
        (LO, HI),
    ).fetchall()
    conn.close()
    return {
        int(dict(r)["draw_no"]): {int(dict(r)[f"num{k}"]) for k in range(1, 7)}
        for r in rows
    }


def fuse_one(dno: int, actual: set[int]) -> int:
    """live coordinator 경로 in-memory · lotto_predictions 미기록."""
    import app.testlotto.brains.coordinator as coord
    from app.testlotto.brains.coordinator import (
        PREDICT_BRAINS,
        PREDICT_MODULES,
        SETS_PER_PREDICT_BRAIN,
        _apply_aux_scoring,
        _seed_independent_brain,
        dynamic_brain_quota,
    )
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.ticket_dedup import dedup_enabled, dedup_ticket_list

    # production quota
    coord.BENCH_FIXED_QUOTA = None
    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    if not draws:
        return 0

    candidates: list[dict] = []
    for brain in PREDICT_BRAINS:
        tag = brain["tag"]
        mod = PREDICT_MODULES[tag]
        _seed_independent_brain(dno)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            conf = float(s.get("confidence", 60))
            candidates.append({**s, "confidence": conf, "pred_set_no": sn, "set_no": sn})

    scored = _apply_aux_scoring(candidates, draws, dno)
    scored.sort(key=lambda x: x["confidence"], reverse=True)

    if dedup_enabled():

        def _regen(brain_tag: str, seen: set[tuple[int, ...]], replace_of: dict | None = None):
            mod = PREDICT_MODULES.get(brain_tag)
            if mod is None:
                return None
            _seed_independent_brain(dno)
            raw = mod.predict_sets(draws, 1)
            if not raw:
                return None
            return _apply_aux_scoring(raw, draws, dno)[0]

        scored, _ = dedup_ticket_list(scored, regenerate=_regen)
        scored.sort(key=lambda x: x["confidence"], reverse=True)

    issued = dynamic_brain_quota(scored)
    best = 0
    for pred in issued:
        nums = [int(x) for x in pred["nums"]]
        best = max(best, len(set(nums) & actual))
    return best


def run_fusion_n200(actuals: dict[int, set[int]]) -> tuple[dict[str, Any], list[tuple[int, int]]]:
    bests: list[tuple[int, int]] = []
    t0 = time.time()
    total = HI - LO + 1
    for i, dno in enumerate(range(LO, HI + 1), 1):
        random.seed(SEED + dno)
        best = fuse_one(dno, actuals[dno])
        bests.append((dno, best))
        if i % 25 == 0 or i == total:
            print(
                f"  [fusion {i}/{total}] draw={dno} best={best} "
                f"elapsed={time.time()-t0:.0f}s",
                flush=True,
            )
    hits = [b for _, b in bests]
    dist = Counter(hits)
    n = len(hits)
    ge3_count = sum(1 for h in hits if h >= 3)
    ge3_rate = ge3_count / n if n else 0.0
    mean_hit = sum(hits) / n if n else 0.0
    fusion = {
        "draw_range": [LO, HI],
        "n": n,
        "mean_hit": round(mean_hit, 6),
        "ge3_rate": round(ge3_rate, 6),
        "ge3_count": ge3_count,
        "hit_dist": {str(k): int(dist.get(k, 0)) for k in range(7)},
        "baseline_ge3": BASELINE_GE3,
        "delta_vs_baseline": round(ge3_rate - BASELINE_GE3, 6),
        "random_ge3_top15_ref": RANDOM_GE3_TOP15,
        "step3_nopeek_ge3_ref": STEP3_NOPEEK_GE3,
        "seed": SEED,
        "path": "in-memory coordinator fuse · no lotto_predictions write",
    }
    return fusion, bests


def by_period(bests: list[tuple[int, int]]) -> dict[str, Any]:
    rates: dict[str, float] = {}
    for name, (lo, hi) in PERIODS.items():
        hs = [b for d, b in bests if lo <= d <= hi]
        ge3 = sum(1 for h in hs if h >= 3)
        rates[name] = round(ge3 / len(hs), 6) if hs else 0.0
    vals = list(rates.values())
    gap = max(vals) - min(vals) if vals else 0.0
    return {
        "early": rates["early"],
        "mid": rates["mid"],
        "late": rates["late"],
        "max_gap": round(gap, 6),
        "stable": gap < 0.05,
        "ranges": {k: list(v) for k, v in PERIODS.items()},
    }


def final_verdict(fusion: dict[str, Any]) -> str:
    ge3 = float(fusion["ge3_rate"])
    mean = float(fusion["mean_hit"])
    if ge3 < 0.100 or mean < 1.8:
        return "ROLLBACK"
    if ge3 >= 0.135 and mean >= 2.0:
        return "KEEP"
    if 0.100 <= ge3 < 0.135:
        return "MARGINAL"
    # ge3 >= 0.135 but mean < 2.0 → not KEEP; treat as MARGINAL if ge3 ok
    if ge3 >= 0.135:
        return "MARGINAL"
    return "ROLLBACK"


def maybe_apply_rollback(verdict: str) -> dict[str, Any]:
    """ROLLBACK이면 코드 플래그 OFF (검증 종료 후)."""
    from app.testlotto.brains.stat_brain import transition_v1

    applied = False
    if verdict == "ROLLBACK":
        path = ROOT / "app" / "testlotto" / "brains" / "stat_brain" / "transition_v1.py"
        text = path.read_text(encoding="utf-8")
        if "TRANSITION_V1_WIRE: bool = True" in text:
            path.write_text(
                text.replace(
                    "TRANSITION_V1_WIRE: bool = True",
                    "TRANSITION_V1_WIRE: bool = False",
                ),
                encoding="utf-8",
            )
            applied = True
        transition_v1.TRANSITION_V1_WIRE = False
    return {
        "applied": applied,
        "TRANSITION_V1_WIRE_now": bool(transition_v1.TRANSITION_V1_WIRE),
        "cmd": "K_STAT_TRANSITION_V1=0 또는 TRANSITION_V1_WIRE=False",
    }


def write_artifacts(
    env: dict, fusion: dict, period: dict, verdict: str, rb: dict
) -> dict[str, Any]:
    payload = {
        "id": "K-TRANSITION-FUSION-N200",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "wire": True,
        "env_ok": env["env_ok"],
        "env": env,
        "fusion_n200": fusion,
        "by_period": period,
        "final_verdict": verdict,
        "rollback_cmd": "K_STAT_TRANSITION_V1=0",
        "rollback_applied": rb,
        "pass": True,
        "tool": "tools/_k_transition_fusion_n200.py",
        "prior": "docs/benchmarks/20260805_KTRANSITION_STEP4_WIRE.json",
        "forbid": [
            "engine.py 수정",
            "auto-tune",
            "random.choices",
            "발권 테이블 INSERT/UPDATE",
            "coordinator 수정",
            "신호 과장",
            "검증 중 TRANSITION_V1_WIRE 변경",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# K-TRANSITION-FUSION-N200 — fusion n200 (2026-08-05)",
        "",
        f"- **판정:** `{verdict}` · env_ok=`{env['env_ok']}`",
        f"- range {fusion['draw_range']} n={fusion['n']}",
        f"- mean_hit=**{fusion['mean_hit']}** · ge3_rate=**{fusion['ge3_rate']}** "
        f"(count={fusion['ge3_count']}) · Δvs baseline={fusion['delta_vs_baseline']}",
        f"- hit_dist={fusion['hit_dist']}",
        f"- by_period={period}",
        f"- rollback_cmd=`K_STAT_TRANSITION_V1=0` · applied={rb}",
        "",
        f"- tool: `{payload['tool']}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(OUT_MD.read_text(encoding="utf-8"), encoding="utf-8")
    return payload


def main() -> int:
    print("[1] env", flush=True)
    env = env_check()
    print(json.dumps(env, ensure_ascii=False), flush=True)
    if not env["env_ok"]:
        print("[abort] env_ok=false", flush=True)
        return 1

    print("[2] fusion n200", flush=True)
    actuals = load_actuals()
    assert len(actuals) == 200, len(actuals)
    fusion, bests = run_fusion_n200(actuals)
    print(json.dumps(fusion, ensure_ascii=False), flush=True)

    print("[3] by_period", flush=True)
    period = by_period(bests)
    print(json.dumps(period, ensure_ascii=False), flush=True)

    print("[4] verdict", flush=True)
    verdict = final_verdict(fusion)
    rb = maybe_apply_rollback(verdict)
    payload = write_artifacts(env, fusion, period, verdict, rb)
    print(
        json.dumps(
            {
                "ok": True,
                "verdict": verdict,
                "ge3": fusion["ge3_rate"],
                "mean": fusion["mean_hit"],
                "rollback_applied": rb["applied"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
