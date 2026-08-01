# -*- coding: utf-8 -*-
"""K-BACKTEST-FULL-C — C package production stack FULL walk-forward (READ-ONLY DB).

Production stack (fixed):
  HINT_WEIGHT=0.15 · LEARN_WIRED=True · AUX_1TO1_ENABLED=True
  wire=set_no_asc (apply_markov_wire_quota unchanged)

FULL n=1182 · draw 53~1234 · seed=42 · LOOK_BACK=52
coordinator FULL path (3brain pool + aux scoring + wire quota → best of 5)

Also measures:
  by_brain — per brain_tag best match among that brain's 5 sets only
  by_period — early 53-447 · mid 448-841 · late 842-1234

Verdict:
  ge3 >= 0.1218 PASS (live baseline)
  ge3 >= 0.1447 STRONG PASS
  ge3 < 0.1218 FAIL
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import coordinator as coord_mod  # noqa: E402
from app.testlotto.brains.coordinator import (  # noqa: E402
    PREDICT_MODULES,
    _apply_aux_scoring,
    apply_markov_wire_quota,
)
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from tools.bench_quick_gate import (  # noqa: E402
    DRAW_END,
    DRAW_START,
    FULL_N_EVAL,
    MC_SEED,
    NULL_GE3,
    WIRE_PIN_GE3,
    enrich_metrics,
    filter_draw_rows,
    gate_criteria_doc,
    resolve_eval_window,
)

SEED = MC_SEED
N_EVAL = FULL_N_EVAL
LOOK_BACK = 52
HINT_WEIGHT = 0.15
OUT = ROOT / "docs" / "benchmarks" / "20260801_KBACKTEST_FULL_C.json"

REF_QUICK_GE3 = 0.125
REF_V2_PIN_GE3 = WIRE_PIN_GE3
REF_LIVE_BASELINE_GE3 = 0.1218

PERIODS: dict[str, tuple[int, int]] = {
    "early": (53, 447),
    "mid": (448, 841),
    "late": (842, 1234),
}


def _apply_production_flags() -> None:
    stat_predict.HINT_WEIGHT = HINT_WEIGHT
    markov_predict.HINT_WEIGHT = HINT_WEIGHT
    review_predict.HINT_WEIGHT = HINT_WEIGHT
    markov_learn.LEARN_WIRED = True
    coord_mod.AUX_1TO1_ENABLED = True


def _best_match(candidates: list[dict], actual: set[int]) -> int:
    best = 0
    for c in candidates:
        mc = len(set(int(x) for x in c["nums"]) & actual)
        best = max(best, mc)
    return best


def _generate_scored(draw_no: int) -> list[dict]:
    set_learn_as_of(draw_no)
    draws = _get_draws_before(draw_no)
    if not draws:
        return []

    candidates: list[dict] = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(SEED)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            candidates.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})

    if not candidates:
        return []

    return _apply_aux_scoring(candidates, draws, draw_no)


def _summarize(bests: list[int]) -> dict[str, Any]:
    n = len(bests)
    ge3_c = sum(1 for x in bests if x >= 3)
    mean_match = sum(bests) / n if n else 0.0
    gate = enrich_metrics(ge3_c, n, mean_match, gate_mode="full")
    return {
        **gate,
        "mean_match": round(mean_match, 6),
        "n_eval": n,
    }


def _period_for_draw(draw_no: int) -> str | None:
    for name, (lo, hi) in PERIODS.items():
        if lo <= draw_no <= hi:
            return name
    return None


def _verdict_label(ge3_rate: float) -> str:
    if ge3_rate >= REF_V2_PIN_GE3:
        return "STRONG PASS"
    if ge3_rate >= REF_LIVE_BASELINE_GE3:
        return "PASS"
    return "FAIL"


def _walkforward() -> dict[str, Any]:
    _apply_production_flags()
    window = resolve_eval_window(n_eval=N_EVAL, sample_mode="full")

    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    rows = filter_draw_rows(rows, window)

    overall_bests: list[int] = []
    brain_bests: dict[str, list[int]] = {tag: [] for tag in PREDICT_MODULES}
    period_bests: dict[str, list[int]] = {k: [] for k in PERIODS}
    draw_records: list[dict[str, Any]] = []

    for row in rows:
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}

        scored = _generate_scored(draw_no)
        if not scored:
            overall_bests.append(0)
            for tag in brain_bests:
                brain_bests[tag].append(0)
            period = _period_for_draw(draw_no)
            if period:
                period_bests[period].append(0)
            continue

        selected = apply_markov_wire_quota(scored)
        overall_hit = _best_match(selected, actual)
        overall_bests.append(overall_hit)

        per_brain: dict[str, int] = {}
        for tag in PREDICT_MODULES:
            tag_sets = [c for c in scored if str(c.get("brain_tag")) == tag]
            hit = _best_match(tag_sets, actual)
            brain_bests[tag].append(hit)
            per_brain[tag] = hit

        period = _period_for_draw(draw_no)
        if period:
            period_bests[period].append(overall_hit)

        draw_records.append({"draw_no": draw_no, "overall": overall_hit, "by_brain": per_brain})

    n = len(overall_bests)
    overall = _summarize(overall_bests)
    by_brain = {tag: _summarize(bests) for tag, bests in brain_bests.items()}
    by_period: dict[str, Any] = {}
    for name, (lo, hi) in PERIODS.items():
        pb = period_bests[name]
        by_period[name] = {
            "draw_range": [lo, hi],
            **_summarize(pb),
        }

    return {
        "overall": overall,
        "by_brain": by_brain,
        "by_period": by_period,
        "n_eval": n,
        "draw_records_count": len(draw_records),
    }


def run_bench() -> dict[str, Any]:
    random.seed(SEED)
    wf = _walkforward()
    overall = wf["overall"]
    ge3 = overall["ge3_rate"]
    verdict = _verdict_label(ge3)

    return {
        "id": "K-BACKTEST-FULL-C",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "look_back": LOOK_BACK,
        "n_eval": wf["n_eval"],
        "path": "coordinator_full (3brain pool + aux scoring + wire quota → best of 5)",
        "production_stack": {
            "hint_weight": HINT_WEIGHT,
            "learn_wired": True,
            "aux_1to1_enabled": True,
            "wire": "set_no_asc",
        },
        "gate": gate_criteria_doc()["full"],
        "overall": overall,
        "by_brain": wf["by_brain"],
        "by_period": wf["by_period"],
        "references": {
            "quick_ge3": REF_QUICK_GE3,
            "v2_pin_ge3": REF_V2_PIN_GE3,
            "live_baseline_ge3": REF_LIVE_BASELINE_GE3,
            "null_ge3": NULL_GE3,
            "source_files": {
                "quick_ge3": "docs/benchmarks/20260801_KBRAIN_PACKAGE_COMPLETE.json",
                "v2_pin_ge3": "STATUS_LATEST.md WIRE-V2 pin",
                "live_baseline_ge3": "K-10SET-DET-LAB-FULL pool10 ge3=0.1218",
            },
        },
        "comparison": {
            "ge3_vs_quick": round(ge3 - REF_QUICK_GE3, 6),
            "ge3_vs_live_baseline": round(ge3 - REF_LIVE_BASELINE_GE3, 6),
            "ge3_vs_v2_pin": round(ge3 - REF_V2_PIN_GE3, 6),
            "ge3_vs_null": round(ge3 - NULL_GE3, 6),
        },
        "verdict": verdict,
        "pass": verdict in ("PASS", "STRONG PASS"),
        "pass_criteria": {
            "live_baseline_ge3": REF_LIVE_BASELINE_GE3,
            "strong_pass_ge3": REF_V2_PIN_GE3,
            "overall_ge3": ge3,
            "meets_live_baseline": ge3 >= REF_LIVE_BASELINE_GE3,
            "meets_strong_pass": ge3 >= REF_V2_PIN_GE3,
        },
        "note": "READ-ONLY FULL n=1182 walk-forward · C package production stack · no app/DB changes",
    }


def main() -> int:
    result = run_bench()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
