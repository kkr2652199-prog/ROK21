# -*- coding: utf-8 -*-
"""BENCH_PROTOCOL §9 QUICK_GATE — eval window · gate criteria (survey reuse)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from scipy.stats import binomtest

FULL_N_EVAL = 1182
DRAW_START = 53
DRAW_END = 1234
QUICK_N_EVAL = 200
QUICK_TAIL_START = 1035  # tail-200: draw 1035~1234
# Default null = independent best-of-5 tickets (Hypergeometric 6/45).
# See BENCH_PROTOCOL §0.1 — never compare best_of_15 ge3 to this constant alone.
NULL_GE3 = 0.1137
NULL_GE3_SINGLE = 0.0238
NULL_GE3_BEST5 = 0.1137
NULL_GE3_BEST15 = 0.3036
NULL_MEAN_SINGLE = 0.8000
NULL_MEAN_BEST5 = 1.7289
NULL_MEAN_BEST15 = 2.2692
WIRE_PIN_GE3 = 0.1447
WIRE_PIN_MEAN = 1.7504
MC_SEED = 42

# eval_mode → theoretical null for max-hits over m independent 6/45 tickets
_NULL_BY_EVAL_MODE: dict[str, dict[str, float | str]] = {
    "single": {"m": 1, "null_ge3": NULL_GE3_SINGLE, "null_mean": NULL_MEAN_SINGLE},
    "single_ticket": {"m": 1, "null_ge3": NULL_GE3_SINGLE, "null_mean": NULL_MEAN_SINGLE},
    "best_of_5": {"m": 5, "null_ge3": NULL_GE3_BEST5, "null_mean": NULL_MEAN_BEST5},
    "best_of_5_from_30": {
        "m": 5,
        "null_ge3": NULL_GE3_BEST5,
        "null_mean": NULL_MEAN_BEST5,
        "note": "approx i.i.d. best-of-5; selection from 30 may change dependence",
    },
    "best_of_15": {"m": 15, "null_ge3": NULL_GE3_BEST15, "null_mean": NULL_MEAN_BEST15},
    "top5_from_15": {
        "m": 5,
        "null_ge3": NULL_GE3_BEST5,
        "null_mean": NULL_MEAN_BEST5,
        "note": "fair 5-ticket compare; do not use best_of_15 null",
    },
}

SampleMode = Literal["full", "tail", "stratified"]


def null_for_eval_mode(eval_mode: str | None = None) -> dict[str, Any]:
    """Return Hypergeometric null matched to eval_mode (BENCH_PROTOCOL §0.1)."""
    key = (eval_mode or "best_of_5").strip().lower()
    row = _NULL_BY_EVAL_MODE.get(key)
    if row is None:
        return {
            "eval_mode": key,
            "m": 5,
            "null_ge3": NULL_GE3,
            "null_mean": NULL_MEAN_BEST5,
            "known": False,
            "note": "unknown eval_mode → default best_of_5 null",
        }
    out: dict[str, Any] = {
        "eval_mode": key,
        "m": row["m"],
        "null_ge3": float(row["null_ge3"]),
        "null_mean": float(row["null_mean"]),
        "known": True,
    }
    if row.get("note"):
        out["note"] = row["note"]
    return out


@dataclass(frozen=True)
class EvalWindow:
    draw_start: int
    draw_end: int
    n_eval_target: int
    sample_mode: SampleMode
    quick_gate: bool
    tail_start: int | None = None


def resolve_eval_window(
    n_eval: int | None = None,
    draw_start: int = DRAW_START,
    draw_end: int = DRAW_END,
    sample_mode: SampleMode = "tail",
) -> EvalWindow:
    """Resolve eval subset. n_eval=None or >=1182 → full; else QUICK tail-last-N."""
    target = n_eval if n_eval is not None else FULL_N_EVAL
    if target >= FULL_N_EVAL or sample_mode == "full":
        return EvalWindow(
            draw_start=draw_start,
            draw_end=draw_end,
            n_eval_target=FULL_N_EVAL,
            sample_mode="full",
            quick_gate=False,
        )
    tail_start = max(draw_start, draw_end - target + 1)
    return EvalWindow(
        draw_start=tail_start,
        draw_end=draw_end,
        n_eval_target=target,
        sample_mode="tail",
        quick_gate=True,
        tail_start=tail_start,
    )


def filter_draw_rows(rows: list[Any], window: EvalWindow) -> list[Any]:
    """Keep rows whose draw_no lies in eval window (tail-last-N or full)."""
    out = [r for r in rows if window.draw_start <= int(dict(r)["draw_no"]) <= window.draw_end]
    if window.sample_mode == "tail" and window.quick_gate and len(out) > window.n_eval_target:
        out = out[-window.n_eval_target :]
    return out


def enrich_metrics(
    ge3_count: int,
    n: int,
    mean: float | None = None,
    *,
    gate_mode: str = "quick",
    eval_mode: str | None = None,
    null_ge3: float | None = None,
) -> dict[str, Any]:
    """Add Δ vs null/pin, p-value, verdict for QUICK or FULL gate.

    When ``eval_mode`` is set, null is resolved via ``null_for_eval_mode``
    (best_of_15 → 0.3036, best_of_5* → 0.1137). Explicit ``null_ge3`` wins.
    """
    null_meta = null_for_eval_mode(eval_mode)
    null = float(null_ge3) if null_ge3 is not None else float(null_meta["null_ge3"])
    if n <= 0:
        return {
            "n": 0,
            "mean": 0.0,
            "ge3_rate": 0.0,
            "ge3_count": 0,
            "delta_ge3_vs_null": 0.0,
            "delta_ge3_vs_pin": 0.0,
            "p_value": 1.0,
            "verdict": "FAIL",
            "eval_mode": null_meta["eval_mode"],
            "null_ge3": null,
            "null_mean": null_meta["null_mean"],
        }
    ge3_rate = round(ge3_count / n, 4)
    p = float(binomtest(ge3_count, n, null, alternative="greater").pvalue)
    delta_null = round(ge3_rate - null, 4)
    delta_pin = round(ge3_rate - WIRE_PIN_GE3, 4)
    if gate_mode == "full":
        # FULL pin gate stays on WIRE-V2 pin (best_of_5 comparable stacks only).
        verdict = "PASS" if ge3_rate > WIRE_PIN_GE3 and p < 0.05 else "FAIL"
    else:
        verdict = "PASS" if p < 0.15 and ge3_rate > null else "FAIL"
    out = {
        "n": n,
        "mean": round(mean if mean is not None else 0.0, 4),
        "ge3_rate": ge3_rate,
        "ge3_count": ge3_count,
        "delta_ge3_vs_null": delta_null,
        "delta_ge3_vs_pin": delta_pin,
        "p_value": round(p, 6),
        "verdict": verdict,
        "eval_mode": null_meta["eval_mode"],
        "null_ge3": null,
        "null_mean": float(null_meta["null_mean"]),
    }
    if null_meta.get("note"):
        out["null_note"] = null_meta["note"]
    return out


def gate_criteria_doc() -> dict[str, Any]:
    """JSON-serializable gate spec for survey outputs."""
    return {
        "quick": {
            "n_eval": QUICK_N_EVAL,
            "draw_range": [QUICK_TAIL_START, DRAW_END],
            "sample_mode": "tail",
            "seed": MC_SEED,
            "pass": "ge3>null(eval_mode-matched) AND p<0.15",
            "default_null_ge3_best_of_5": NULL_GE3,
            "null_by_eval_mode": {
                k: {"null_ge3": v["null_ge3"], "null_mean": v["null_mean"], "m": v["m"]}
                for k, v in _NULL_BY_EVAL_MODE.items()
            },
            "promising": "ge3>null+0.01 OR top variant clear",
        },
        "full": {
            "n_eval": FULL_N_EVAL,
            "draw_range": [DRAW_START, DRAW_END],
            "sample_mode": "full",
            "seed": MC_SEED,
            "pass": "ge3>pin(0.1447) AND p<0.05",
            "pin_applies_to": "best_of_5 comparable stacks",
        },
    }
