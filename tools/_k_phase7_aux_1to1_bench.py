# -*- coding: utf-8 -*-
"""K-PHASE7-AUX-1TO1-BENCH — coordinator aux 1:1 A/B 성능 비교 (READ-ONLY DB).

A: AUX_1TO1_ENABLED=False (PHASE6 baseline — 4 aux global)
B: AUX_1TO1_ENABLED=True (PHASE7 — 1:1 dedicated aux)
draw 1035~1234 (n=200) · seed=42 · HINT_WEIGHT=0.15 · LEARN_WIRED=True
coordinator 전체 경로 (3뇌 pool · aux scoring · wire quota)

PASS: ge3_B >= ge3_A (후퇴 없음)
FAIL: revert AUX_1TO1_ENABLED=False · record HOLD
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.coordinator import (  # noqa: E402
    PREDICT_MODULES,
    _apply_aux_scoring,
    apply_markov_wire_quota,
)
from app.testlotto.brains import coordinator as coord_mod  # noqa: E402
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

SEED = 42
N_EVAL = 200
DRAW_START = 1035
DRAW_END = 1234
HINT_WEIGHT = 0.15
OUT = ROOT / "docs" / "benchmarks" / "20260801_KPHASE7_AUX_1TO1_BENCH.json"
V2_PIN_GE3 = 0.1447
PHASE6_BASELINE_GE3 = 0.125


def _set_hint_weights(weight: float) -> None:
    stat_predict.HINT_WEIGHT = weight
    markov_predict.HINT_WEIGHT = weight
    review_predict.HINT_WEIGHT = weight


def _set_aux_1to1(enabled: bool) -> None:
    coord_mod.AUX_1TO1_ENABLED = enabled


def _run_coordinator_path(draw_no: int, actual: set[int]) -> int:
    """3뇌 predict → aux scoring → wire quota → best matched count."""
    set_learn_as_of(draw_no)
    draws = _get_draws_before(draw_no)
    if not draws:
        return 0

    candidates: list[dict] = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(SEED)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            candidates.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})

    if not candidates:
        return 0

    scored = _apply_aux_scoring(candidates, draws, draw_no)
    selected = apply_markov_wire_quota(scored)

    best_hit = 0
    for c in selected:
        mc = len(set(int(x) for x in c["nums"]) & actual)
        best_hit = max(best_hit, mc)
    return best_hit


def _walkforward(aux_1to1: bool) -> dict[str, Any]:
    _set_hint_weights(HINT_WEIGHT)
    markov_learn.LEARN_WIRED = True
    _set_aux_1to1(aux_1to1)

    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    if len(rows) > N_EVAL:
        rows = rows[-N_EVAL:]

    bests: list[int] = []
    for row in rows:
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        bests.append(_run_coordinator_path(draw_no, actual))

    n = len(bests)
    ge3_c = sum(1 for x in bests if x >= 3)
    ge3_rate = ge3_c / n if n else 0.0
    mean_match = sum(bests) / n if n else 0.0
    return {
        "aux_1to1_enabled": aux_1to1,
        "hint_weight": HINT_WEIGHT,
        "learn_wired": True,
        "n_eval": n,
        "ge3_count": ge3_c,
        "ge3_rate": round(ge3_rate, 6),
        "mean_match": round(mean_match, 6),
    }


def run_bench() -> dict[str, Any]:
    random.seed(SEED)

    a = _walkforward(False)
    b = _walkforward(True)

    ge3_diff = round(b["ge3_rate"] - a["ge3_rate"], 6)
    mean_diff = round(b["mean_match"] - a["mean_match"], 6)
    passed = b["ge3_rate"] >= a["ge3_rate"]
    verdict = "PASS" if passed else "HOLD"
    final_aux_1to1 = True if passed else False

    if not passed:
        _set_aux_1to1(False)

    return {
        "id": "K-PHASE7-AUX-1TO1-BENCH",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "path": "coordinator_full (3brain pool + aux scoring + wire quota)",
        "hint_weight": HINT_WEIGHT,
        "learn_wired": True,
        "v2_pin_ge3": V2_PIN_GE3,
        "phase6_baseline_ge3": PHASE6_BASELINE_GE3,
        "metrics_a": a,
        "metrics_b": b,
        "ge3_diff": ge3_diff,
        "mean_diff": mean_diff,
        "pass_criterion": "ge3_B >= ge3_A",
        "final_aux_1to1_enabled": final_aux_1to1,
        "verdict": verdict,
        "pass": passed,
    }


def main() -> int:
    result = run_bench()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
