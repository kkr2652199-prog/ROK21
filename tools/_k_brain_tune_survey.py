# -*- coding: utf-8 -*-
"""K-BRAIN-TUNE-SURVEY — hint / look_back / wire selection FULL sweep (READ-ONLY).

Production defaults:
  HINT_WEIGHT=0.15 · LEARN_WIRED=True · AUX_1TO1_ENABLED=True · LOOK_BACK=52

P0 wire sweep (look_back=52, hint=0.15):
  set_no_asc · conf_top5 · aux_hint_top5 · conf_quota

P1 look_back sweep (wire=set_no_asc, hint=0.15):
  [30, 52, 80, 120, 200] + early/mid/late period ge3

P2 hint_weight sweep (wire=set_no_asc, look_back=52):
  [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]

best_combo: single-axis bests combined → one FULL walk-forward.

FULL n=1182 (draw 53~1234 when look_back=52) · seed=42 · READ-ONLY · no app/DB changes.
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
DEFAULT_LOOK_BACK = 52
DEFAULT_HINT_WEIGHT = 0.15
TARGET_N = 5
OUT = ROOT / "docs" / "benchmarks" / "20260801_KBRAIN_TUNE_SURVEY.json"

REF_BASELINE_GE3 = 0.1015
REF_LIVE_BASELINE_GE3 = 0.1218
REF_V2_PIN_GE3 = WIRE_PIN_GE3

QUOTA: dict[str, int] = {"markov": 3, "stat": 1, "review": 1}

PERIODS: dict[str, tuple[int, int]] = {
    "early": (53, 447),
    "mid": (448, 841),
    "late": (842, 1234),
}

P0_WIRES = ("set_no_asc", "conf_top5", "aux_hint_top5", "conf_quota")
P1_LOOK_BACKS = [30, 52, 80, 120, 200]
P2_HINT_WEIGHTS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]


def _apply_production_flags(hint_weight: float = DEFAULT_HINT_WEIGHT) -> None:
    stat_predict.HINT_WEIGHT = hint_weight
    markov_predict.HINT_WEIGHT = hint_weight
    review_predict.HINT_WEIGHT = hint_weight
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
        return float(dedicated.score_set(c["nums"], draws, draw_no, brain_tag=tag))
    except Exception:
        return float(c.get("confidence") or 0)


def _enrich_aux_hint(scored: list[dict], draws: list[dict], draw_no: int) -> list[dict]:
    return [{**c, "aux_hint_score": round(_aux_hint_score(c, draws, draw_no), 4)} for c in scored]


def _select_set_no_asc(candidates: list[dict]) -> list[dict]:
    return apply_markov_wire_quota(candidates)


def _select_conf_top5(candidates: list[dict]) -> list[dict]:
    return sorted(candidates, key=lambda x: float(x.get("confidence") or 0), reverse=True)[:TARGET_N]


def _select_aux_hint_top5(candidates: list[dict]) -> list[dict]:
    return sorted(
        candidates,
        key=lambda x: (
            float(x.get("aux_hint_score") or 0),
            float(x.get("confidence") or 0),
        ),
        reverse=True,
    )[:TARGET_N]


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


WIRE_SELECTORS: dict[str, Callable[[list[dict]], list[dict]]] = {
    "set_no_asc": _select_set_no_asc,
    "conf_top5": _select_conf_top5,
    "aux_hint_top5": _select_aux_hint_top5,
    "conf_quota": _select_conf_quota,
}


def _best_match(candidates: list[dict], actual: set[int]) -> int:
    best = 0
    for c in candidates:
        mc = len(set(int(x) for x in c["nums"]) & actual)
        best = max(best, mc)
    return best


def _period_for_draw(draw_no: int) -> str | None:
    for name, (lo, hi) in PERIODS.items():
        if lo <= draw_no <= hi:
            return name
    return None


def _slice_draws(draws: list[dict], look_back: int) -> list[dict] | None:
    if len(draws) < look_back:
        return None
    return draws[-look_back:]


def _generate_scored(
    draw_no: int,
    *,
    look_back: int = DEFAULT_LOOK_BACK,
    hint_weight: float = DEFAULT_HINT_WEIGHT,
) -> tuple[list[dict], list[dict]] | None:
    _apply_production_flags(hint_weight)
    set_learn_as_of(draw_no)
    raw_draws = _get_draws_before(draw_no)
    if not raw_draws:
        return None
    draws = _slice_draws(raw_draws, look_back)
    if draws is None:
        return None

    candidates: list[dict] = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(SEED)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            candidates.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})

    if not candidates:
        return None

    scored = _apply_aux_scoring(candidates, draws, draw_no)
    scored = _enrich_aux_hint(scored, draws, draw_no)
    return scored, draws


def _summarize_bests(bests: list[int]) -> dict[str, Any]:
    n = len(bests)
    ge3_c = sum(1 for x in bests if x >= 3)
    mean_match = sum(bests) / n if n else 0.0
    gate = enrich_metrics(ge3_c, n, mean_match, gate_mode="full")
    return {
        **gate,
        "mean_match": round(mean_match, 6),
        "n_eval": n,
    }


def _summarize_by_period(bests_by_period: dict[str, list[int]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, (lo, hi) in PERIODS.items():
        pb = bests_by_period.get(name, [])
        out[name] = {"draw_range": [lo, hi], **_summarize_bests(pb)}
    return out


def _load_rows() -> list[dict]:
    window = resolve_eval_window(n_eval=N_EVAL, sample_mode="full")
    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    return [dict(r) for r in filter_draw_rows(rows, window)]


def _walkforward(
    *,
    wire: str = "set_no_asc",
    look_back: int = DEFAULT_LOOK_BACK,
    hint_weight: float = DEFAULT_HINT_WEIGHT,
    label: str = "",
    track_periods: bool = False,
    multi_wire: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Single-axis walk-forward. multi_wire: generate once, score all wire selectors."""
    rows = _load_rows()
    selector = WIRE_SELECTORS[wire]
    wires = multi_wire or (wire,)

    overall_bests: dict[str, list[int]] = {w: [] for w in wires}
    period_bests: dict[str, list[int]] = {k: [] for k in PERIODS} if track_periods else {}
    processed = 0
    sweep_tag = label or f"wire={wire} lb={look_back} hint={hint_weight}"

    for row in rows:
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}

        gen = _generate_scored(draw_no, look_back=look_back, hint_weight=hint_weight)
        if gen is None:
            for w in wires:
                overall_bests[w].append(0)
            if track_periods:
                period = _period_for_draw(draw_no)
                if period:
                    period_bests[period].append(0)
            continue

        scored, _ = gen
        processed += 1
        if processed % 100 == 0:
            print(f"[{sweep_tag}] progress {processed} draws", flush=True)

        if len(wires) == 1:
            hit = _best_match(selector(scored), actual)
            overall_bests[wire].append(hit)
            if track_periods:
                period = _period_for_draw(draw_no)
                if period:
                    period_bests[period].append(hit)
        else:
            for w in wires:
                hit = _best_match(WIRE_SELECTORS[w](scored), actual)
                overall_bests[w].append(hit)

    if len(wires) == 1:
        overall = _summarize_bests(overall_bests[wire])
        result: dict[str, Any] = {
            "wire": wire,
            "look_back": look_back,
            "hint_weight": hint_weight,
            "overall": overall,
            "n_eval": overall["n_eval"],
        }
        if track_periods:
            result["by_period"] = _summarize_by_period(period_bests)
        return result

    strategies: dict[str, dict[str, Any]] = {}
    for w in wires:
        strategies[w] = _summarize_bests(overall_bests[w])
    n = next(iter(overall_bests.values()))
    return {
        "strategies": strategies,
        "n_eval": len(n),
        "look_back": look_back,
        "hint_weight": hint_weight,
    }


def _pick_best(items: dict[str, dict[str, Any]], key: str = "overall") -> tuple[str, dict[str, Any]]:
    best_id = ""
    best_m: dict[str, Any] = {}
    best_ge3 = -1.0
    best_p = 2.0
    for sid, data in items.items():
        m = data if key == "overall" and "ge3_rate" in data else data.get(key, data)
        if not isinstance(m, dict) or "ge3_rate" not in m:
            continue
        ge3 = float(m["ge3_rate"])
        p = float(m.get("p_value", 1.0))
        if ge3 > best_ge3 or (ge3 == best_ge3 and p < best_p):
            best_ge3 = ge3
            best_p = p
            best_id = sid
            best_m = m
    return best_id, best_m


def _apply_recommendation(
    p0: dict[str, Any],
    p1: dict[str, Any],
    p2: dict[str, Any],
    best_combo: dict[str, Any],
) -> dict[str, Any]:
    combo_ge3 = float(best_combo["overall"]["ge3_rate"])
    baseline_ge3 = REF_BASELINE_GE3
    live_ge3 = REF_LIVE_BASELINE_GE3

    beats_baseline = combo_ge3 > baseline_ge3
    meets_live = combo_ge3 >= live_ge3
    combo_p = float(best_combo["overall"].get("p_value", 1.0))
    p_sig = combo_p < 0.05

    if meets_live and p_sig:
        action = "GO-APPLY"
        note = "best_combo meets live_baseline ge3>=0.1218 with p<0.05 — 형 GO for K-BRAIN-TUNE-APPLY"
    elif beats_baseline and combo_ge3 >= NULL_GE3:
        action = "GO-WAIT"
        note = "best_combo improves over baseline but below live_baseline or p — 형 GO 대기"
    else:
        action = "HOLD"
        note = "best_combo does not beat baseline meaningfully — HOLD production stack"

    return {
        "action": action,
        "note": note,
        "baseline_ge3": baseline_ge3,
        "live_baseline_ge3": live_ge3,
        "best_combo_ge3": combo_ge3,
        "delta_vs_baseline": round(combo_ge3 - baseline_ge3, 6),
        "delta_vs_live": round(combo_ge3 - live_ge3, 6),
        "meets_live_baseline": meets_live,
        "p_lt_0_05": p_sig,
        "auto_apply": False,
    }


def run_survey() -> dict[str, Any]:
    random.seed(SEED)
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    print("=== P0 wire sweep (look_back=52, hint=0.15) ===", flush=True)
    p0_wf = _walkforward(
        look_back=DEFAULT_LOOK_BACK,
        hint_weight=DEFAULT_HINT_WEIGHT,
        label="P0-wire",
        multi_wire=P0_WIRES,
    )
    p0_strategies = p0_wf["strategies"]
    p0_best_id, p0_best_m = _pick_best(p0_strategies)

    print("=== P1 look_back sweep (wire=set_no_asc, hint=0.15) ===", flush=True)
    p1_results: dict[str, dict[str, Any]] = {}
    for lb in P1_LOOK_BACKS:
        print(f"--- P1 look_back={lb} ---", flush=True)
        p1_results[str(lb)] = _walkforward(
            wire="set_no_asc",
            look_back=lb,
            hint_weight=DEFAULT_HINT_WEIGHT,
            label=f"P1-lb={lb}",
            track_periods=True,
        )
    p1_best_id, p1_best_m = _pick_best(p1_results)

    print("=== P2 hint_weight sweep (wire=set_no_asc, look_back=52) ===", flush=True)
    p2_results: dict[str, dict[str, Any]] = {}
    for hw in P2_HINT_WEIGHTS:
        print(f"--- P2 hint_weight={hw} ---", flush=True)
        p2_results[str(hw)] = _walkforward(
            wire="set_no_asc",
            look_back=DEFAULT_LOOK_BACK,
            hint_weight=hw,
            label=f"P2-hint={hw}",
        )
    p2_best_id, p2_best_m = _pick_best(p2_results)

    best_wire = p0_best_id
    best_lb = int(p1_best_id)
    best_hint = float(p2_best_id)

    print(
        f"=== best_combo: wire={best_wire} look_back={best_lb} hint={best_hint} ===",
        flush=True,
    )
    best_combo = _walkforward(
        wire=best_wire,
        look_back=best_lb,
        hint_weight=best_hint,
        label="best_combo",
        track_periods=True,
    )
    best_combo["선정_근거"] = {
        "P0_best_wire": {"id": p0_best_id, "ge3_rate": p0_best_m.get("ge3_rate")},
        "P1_best_look_back": {"id": p1_best_id, "ge3_rate": p1_best_m.get("ge3_rate")},
        "P2_best_hint_weight": {"id": p2_best_id, "ge3_rate": p2_best_m.get("ge3_rate")},
        "method": "single-axis best ge3_rate per sweep (tie-break: lower p_value)",
    }

    apply_rec = _apply_recommendation(
        p0_strategies, p1_results, p2_results, best_combo
    )

    return {
        "id": "K-BRAIN-TUNE-SURVEY",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "n_eval_target": N_EVAL,
        "path": "coordinator_full (3brain pool + aux scoring + in-tool wire/params)",
        "production_stack": {
            "hint_weight_default": DEFAULT_HINT_WEIGHT,
            "look_back_default": DEFAULT_LOOK_BACK,
            "learn_wired": True,
            "aux_1to1_enabled": True,
            "wire_baseline": "set_no_asc",
        },
        "gate": gate_criteria_doc()["full"],
        "references": {
            "baseline_ge3": REF_BASELINE_GE3,
            "live_baseline_ge3": REF_LIVE_BASELINE_GE3,
            "v2_pin_ge3": REF_V2_PIN_GE3,
            "null_ge3": NULL_GE3,
            "pass_target_ge3": REF_LIVE_BASELINE_GE3,
        },
        "P0_wire_sweep": {
            "look_back": DEFAULT_LOOK_BACK,
            "hint_weight": DEFAULT_HINT_WEIGHT,
            "strategies": p0_strategies,
            "best": {"id": p0_best_id, **p0_best_m},
        },
        "P1_look_back_sweep": {
            "wire": "set_no_asc",
            "hint_weight": DEFAULT_HINT_WEIGHT,
            "values": P1_LOOK_BACKS,
            "results": p1_results,
            "best": {"look_back": int(p1_best_id), **p1_best_m},
        },
        "P2_hint_weight_sweep": {
            "wire": "set_no_asc",
            "look_back": DEFAULT_LOOK_BACK,
            "values": P2_HINT_WEIGHTS,
            "results": p2_results,
            "best": {"hint_weight": float(p2_best_id), **p2_best_m},
        },
        "best_combo": best_combo,
        "apply_recommendation": apply_rec,
        "note": "READ-ONLY FULL sweep · coordinator unchanged · no auto-apply · no DB write",
    }


def main() -> int:
    result = run_survey()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
