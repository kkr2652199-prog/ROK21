# -*- coding: utf-8 -*-
"""K-WIRE-SELECT-FULL-SURVEY — wire/selection strategy FULL revalidation (READ-ONLY).

Production stack:
  HINT_WEIGHT=0.15 · LEARN_WIRED=True · AUX_1TO1_ENABLED=True
  quota markov=3 stat=1 review=1 (total 5)

Strategies (selection functions in this tool only — coordinator.py unchanged):
  set_no_asc · conf_quota · conf_global_top5 · aux_hint_quota · oracle_best15 (ref)

FULL n=1182 · draw 53~1234 · seed=42
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import coordinator as coord_mod  # noqa: E402
from app.testlotto.brains.coordinator import (  # noqa: E402
    BRAIN_DEDICATED_AUX,
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
HINT_WEIGHT = 0.15
TARGET_N = 5
OUT = ROOT / "docs" / "benchmarks" / "20260801_KWIRE_SELECT_FULL_survey.json"
QUICK_REF = ROOT / "docs" / "benchmarks" / "20260801_KQUOTA_GAP_survey.json"
LIVE_BASELINE_GE3 = 0.1218

QUOTA: dict[str, int] = {"markov": 3, "stat": 1, "review": 1}
REF_V2_PIN_GE3 = WIRE_PIN_GE3
REF_ARCH_NOTE_GAP = 0.436


def _apply_production_flags() -> None:
    stat_predict.HINT_WEIGHT = HINT_WEIGHT
    markov_predict.HINT_WEIGHT = HINT_WEIGHT
    review_predict.HINT_WEIGHT = HINT_WEIGHT
    markov_learn.LEARN_WIRED = True
    coord_mod.AUX_1TO1_ENABLED = True


def _aux_hint_score(c: dict, draws: list[dict], draw_no: int) -> float:
    if "aux_hint_score" in c and c["aux_hint_score"] is not None:
        return float(c["aux_hint_score"])
    tag = str(c.get("brain_tag") or "")
    dedicated = BRAIN_DEDICATED_AUX.get(tag)
    if dedicated is None:
        return float(c.get("confidence") or 0)
    try:
        return float(
            dedicated.score_set(c["nums"], draws, draw_no, brain_tag=tag)
        )
    except Exception:
        return float(c.get("confidence") or 0)


def _enrich_aux_hint(scored: list[dict], draws: list[dict], draw_no: int) -> list[dict]:
    out: list[dict] = []
    for c in scored:
        ah = _aux_hint_score(c, draws, draw_no)
        out.append({**c, "aux_hint_score": round(ah, 4)})
    return out


def _select_set_no_asc(candidates: list[dict]) -> list[dict]:
    return apply_markov_wire_quota(candidates)


def _select_conf_quota(candidates: list[dict]) -> list[dict]:
    brain_buckets: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        tag = str(c.get("brain_tag", "") or "")
        if tag in QUOTA:
            brain_buckets[tag].append(c)

    selected: list[dict] = []
    for tag, cap in QUOTA.items():
        bucket = sorted(
            brain_buckets.get(tag) or [],
            key=lambda x: float(x.get("confidence") or 0),
            reverse=True,
        )
        selected.extend(bucket[:cap])

    if len(selected) < TARGET_N:
        used = {id(c) for c in selected}
        remainder = sorted(
            [c for c in candidates if id(c) not in used],
            key=lambda x: float(x.get("confidence") or 0),
            reverse=True,
        )
        for c in remainder:
            selected.append(c)
            if len(selected) >= TARGET_N:
                break
    return selected[:TARGET_N]


def _select_conf_global_top5(candidates: list[dict]) -> list[dict]:
    return sorted(
        candidates, key=lambda x: float(x.get("confidence") or 0), reverse=True
    )[:TARGET_N]


def _select_aux_hint_quota(candidates: list[dict]) -> list[dict]:
    brain_buckets: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        tag = str(c.get("brain_tag", "") or "")
        if tag in QUOTA:
            brain_buckets[tag].append(c)

    selected: list[dict] = []
    for tag, cap in QUOTA.items():
        bucket = sorted(
            brain_buckets.get(tag) or [],
            key=lambda x: (
                float(x.get("aux_hint_score") or 0),
                float(x.get("confidence") or 0),
            ),
            reverse=True,
        )
        selected.extend(bucket[:cap])

    if len(selected) < TARGET_N:
        used = {id(c) for c in selected}
        remainder = sorted(
            [c for c in candidates if id(c) not in used],
            key=lambda x: (
                float(x.get("aux_hint_score") or 0),
                float(x.get("confidence") or 0),
            ),
            reverse=True,
        )
        for c in remainder:
            selected.append(c)
            if len(selected) >= TARGET_N:
                break
    return selected[:TARGET_N]


SELECTORS: dict[str, Callable[[list[dict]], list[dict]]] = {
    "set_no_asc": _select_set_no_asc,
    "conf_quota": _select_conf_quota,
    "conf_global_top5": _select_conf_global_top5,
    "aux_hint_quota": _select_aux_hint_quota,
}


def _best_match(candidates: list[dict], actual: set[int]) -> int:
    best = 0
    for c in candidates:
        mc = len(set(int(x) for x in c["nums"]) & actual)
        best = max(best, mc)
    return best


def _generate_scored(draw_no: int) -> tuple[list[dict], list[dict]]:
    set_learn_as_of(draw_no)
    draws = _get_draws_before(draw_no)
    if not draws:
        return [], draws

    candidates: list[dict] = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(SEED)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            candidates.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})

    if not candidates:
        return [], draws

    scored = _apply_aux_scoring(candidates, draws, draw_no)
    scored = _enrich_aux_hint(scored, draws, draw_no)
    return scored, draws


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

    strategy_bests: dict[str, list[int]] = {k: [] for k in SELECTORS}
    strategy_bests["oracle_best15"] = []
    quota_gap_draws = 0

    for row in rows:
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}

        scored, _ = _generate_scored(draw_no)
        if not scored:
            for k in strategy_bests:
                strategy_bests[k].append(0)
            continue

        oracle_best = _best_match(scored, actual)
        strategy_bests["oracle_best15"].append(oracle_best)

        baseline_selected = SELECTORS["set_no_asc"](scored)
        baseline_best = _best_match(baseline_selected, actual)
        if oracle_best > baseline_best:
            quota_gap_draws += 1

        for sid, fn in SELECTORS.items():
            selected = fn(scored)
            strategy_bests[sid].append(_best_match(selected, actual))

    n = len(strategy_bests["set_no_asc"])
    strategies: dict[str, dict[str, Any]] = {}
    for sid, bests in strategy_bests.items():
        ge3_c = sum(1 for x in bests if x >= 3)
        mean_match = sum(bests) / n if n else 0.0
        gate = enrich_metrics(ge3_c, n, mean_match, gate_mode="full")
        strategies[sid] = {
            **gate,
            "mean_match": round(mean_match, 6),
            "n_eval": n,
        }

    quota_gap_rate = quota_gap_draws / n if n else 0.0
    return {
        "strategies": strategies,
        "quota_gap": {
            "draws_oracle_gt_set_no_asc": quota_gap_draws,
            "quota_gap_rate": round(quota_gap_rate, 6),
            "baseline_strategy": "set_no_asc",
            "ref_arch_note_rate": REF_ARCH_NOTE_GAP,
            "ref_note": "architecture note ~43.6% from K-BENCH-01 n=1182",
        },
        "n_eval": n,
    }


def _load_quick_ref() -> dict[str, Any] | None:
    if not QUICK_REF.is_file():
        return None
    return json.loads(QUICK_REF.read_text(encoding="utf-8"))


def _quick_full_compare(
    full_strategies: dict[str, dict[str, Any]],
    quick_ref: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    quick_strategies = (quick_ref or {}).get("strategies") or {}
    for sid in ("set_no_asc", "conf_quota", "conf_global_top5", "aux_hint_quota", "oracle_best15"):
        full_g = full_strategies.get(sid, {}).get("ge3_rate", 0.0)
        quick_g = quick_strategies.get(sid, {}).get("ge3_rate", 0.0)
        out[sid] = {
            "quick_ge3": quick_g,
            "full_ge3": full_g,
            "delta_full_minus_quick": round(full_g - quick_g, 6),
            "collapse": quick_g > 0 and full_g < quick_g - 0.005,
        }
    return out


def _wire_go_verdict(strategies: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """PASS for wire GO: conf_global_top5 ge3 > set_no_asc AND p<0.05 vs null."""
    baseline = strategies["set_no_asc"]
    baseline_ge3 = baseline["ge3_rate"]
    top5 = strategies["conf_global_top5"]
    aux = strategies["aux_hint_quota"]

    top5_beats_baseline = top5["ge3_rate"] > baseline_ge3
    top5_p_sig = top5.get("p_value", 1.0) < 0.05
    top5_beats_live = top5["ge3_rate"] > LIVE_BASELINE_GE3

    aux_beats_baseline = aux["ge3_rate"] > baseline_ge3
    aux_p_sig = aux.get("p_value", 1.0) < 0.05

    wire_pass = top5_beats_baseline and top5_p_sig

    if wire_pass:
        wire_go = "yes"
        recommendation = "K-WIRE-SELECT-GO-WAIT"
        note = (
            "conf_global_top5 beats set_no_asc on FULL with p<0.05 vs null — "
            "형 GO for wire A/B only (no auto-patch)"
        )
    elif top5_beats_baseline or aux_beats_baseline:
        wire_go = "wait"
        recommendation = "K-WIRE-SELECT-GO-WAIT"
        note = (
            "Candidate beats set_no_asc on FULL but FAILS p<0.05 or collapse vs QUICK — HOLD wire"
        )
    else:
        wire_go = "no"
        recommendation = "K-ATTACK-HOLD"
        note = "No wire candidate beats set_no_asc on FULL ge3 — hold current wire"

    beats: list[str] = []
    for sid in ("conf_quota", "conf_global_top5", "aux_hint_quota"):
        if strategies[sid]["ge3_rate"] > baseline_ge3:
            beats.append(sid)

    return {
        "baseline_ge3": baseline_ge3,
        "conf_global_top5_ge3": top5["ge3_rate"],
        "conf_global_top5_p": top5.get("p_value"),
        "beats_set_no_asc": beats,
        "pass_criteria": {
            "conf_global_top5_gt_set_no_asc": top5_beats_baseline,
            "conf_global_top5_gt_live_baseline_0.1218": top5_beats_live,
            "conf_global_top5_p_lt_0.05": top5_p_sig,
            "aux_hint_beats_baseline": aux_beats_baseline,
            "aux_hint_p_lt_0.05": aux_p_sig,
            "wire_pass": wire_pass,
        },
        "wire_go": wire_go,
        "recommendation": recommendation,
        "note": note,
        "auto_wire": False,
    }


def run_survey() -> dict[str, Any]:
    random.seed(SEED)
    wf = _walkforward()
    strategies = wf["strategies"]
    quick_ref = _load_quick_ref()
    compare = _quick_full_compare(strategies, quick_ref)
    verdict = _wire_go_verdict(strategies)

    baseline = strategies["set_no_asc"]
    comparison: dict[str, dict[str, float]] = {}
    for sid, m in strategies.items():
        if sid == "oracle_best15":
            comparison[sid] = {
                "delta_ge3_vs_set_no_asc": round(m["ge3_rate"] - baseline["ge3_rate"], 6),
                "oracle_ceiling_uplift": round(m["ge3_rate"] - baseline["ge3_rate"], 6),
            }
        else:
            comparison[sid] = {
                "delta_ge3_vs_set_no_asc": round(m["ge3_rate"] - baseline["ge3_rate"], 6),
                "delta_ge3_vs_v2_pin": round(m["ge3_rate"] - REF_V2_PIN_GE3, 6),
                "delta_ge3_vs_null": round(m["ge3_rate"] - NULL_GE3, 6),
            }

    return {
        "id": "K-WIRE-SELECT-FULL-SURVEY",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "n_eval": wf["n_eval"],
        "path": "coordinator_full (C package · 3brain pool + aux scoring + wire alt)",
        "production_stack": {
            "hint_weight": HINT_WEIGHT,
            "learn_wired": True,
            "aux_1to1_enabled": True,
            "wire_baseline": "set_no_asc",
            "quota": dict(QUOTA),
        },
        "gate": gate_criteria_doc()["full"],
        "strategies": strategies,
        "quota_gap": wf["quota_gap"],
        "quick_vs_full": compare,
        "comparison": comparison,
        "references": {
            "v2_pin_ge3": REF_V2_PIN_GE3,
            "live_baseline_ge3": LIVE_BASELINE_GE3,
            "quick_survey_id": "K-QUOTA-GAP-SURVEY",
            "arch_note_quota_gap_rate": REF_ARCH_NOTE_GAP,
        },
        "verdict": verdict,
        "note": "READ-ONLY · coordinator.py unchanged · no auto-wire",
    }


def main() -> int:
    result = run_survey()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
