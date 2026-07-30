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
NULL_GE3 = 0.1137
WIRE_PIN_GE3 = 0.1447
WIRE_PIN_MEAN = 1.7504
MC_SEED = 42

SampleMode = Literal["full", "tail", "stratified"]


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
) -> dict[str, Any]:
    """Add Δ vs null/pin, p-value, verdict for QUICK or FULL gate."""
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
        }
    ge3_rate = round(ge3_count / n, 4)
    p = float(binomtest(ge3_count, n, NULL_GE3, alternative="greater").pvalue)
    delta_null = round(ge3_rate - NULL_GE3, 4)
    delta_pin = round(ge3_rate - WIRE_PIN_GE3, 4)
    if gate_mode == "full":
        verdict = "PASS" if ge3_rate > WIRE_PIN_GE3 and p < 0.05 else "FAIL"
    else:
        verdict = "PASS" if p < 0.15 and ge3_rate > NULL_GE3 else "FAIL"
    return {
        "n": n,
        "mean": round(mean if mean is not None else 0.0, 4),
        "ge3_rate": ge3_rate,
        "ge3_count": ge3_count,
        "delta_ge3_vs_null": delta_null,
        "delta_ge3_vs_pin": delta_pin,
        "p_value": round(p, 6),
        "verdict": verdict,
    }


def gate_criteria_doc() -> dict[str, Any]:
    """JSON-serializable gate spec for survey outputs."""
    return {
        "quick": {
            "n_eval": QUICK_N_EVAL,
            "draw_range": [QUICK_TAIL_START, DRAW_END],
            "sample_mode": "tail",
            "seed": MC_SEED,
            "pass": "ge3>null(0.1137) AND p<0.15",
            "promising": "ge3>null+0.01 OR top variant clear",
        },
        "full": {
            "n_eval": FULL_N_EVAL,
            "draw_range": [DRAW_START, DRAW_END],
            "sample_mode": "full",
            "seed": MC_SEED,
            "pass": "ge3>pin(0.1447) AND p<0.05",
        },
    }
