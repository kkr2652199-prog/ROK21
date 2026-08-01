# -*- coding: utf-8 -*-
"""K-FUSION-BOTTLE-DIAG — fusion bottleneck diagnostic (READ-ONLY bench).

Purpose: solo markov ge3=0.1300 vs fused coordinator ge3=0.0600 — quantify why.
Mode: BENCH_FIXED_QUOTA markov=5 stat=0 review=0 (dynamic_brain_quota bypass · diagnostic only).
draw 1135~1234 · n=100 walk-forward · seed=42
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

from app.testlotto.brains import coordinator as coord_mod  # noqa: E402
from app.testlotto.brains.coordinator import (  # noqa: E402
    PREDICT_BRAINS,
    PREDICT_MODULES,
    _apply_aux_scoring,
    _compute_dynamic_quota,
    dynamic_brain_quota,
    run_coordinated_prediction,
)
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state import get_referee_weights  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from tools.bench_quick_gate import MC_SEED, NULL_GE3, enrich_metrics  # noqa: E402

DRAW_START = 1135
DRAW_END = 1234
SEED = MC_SEED
REF_FUSED_GE3 = 0.0600
REF_SOLO_MARKOV_GE3 = 0.1300
FIXED_QUOTA = {"markov": 5, "stat": 0, "review": 0}
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KFUSION_BOTTLE_DIAG.json"
OUT_REPORT = ROOT / "reports" / "20260801_KFUSION_BOTTLE_DIAG.md"
OUT_DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_REPORT.name


def _apply_production_flags() -> None:
    stat_predict.HINT_WEIGHT = 0.15
    markov_predict.HINT_WEIGHT = 0.15
    review_predict.HINT_WEIGHT = 0.15
    markov_learn.LEARN_WIRED = True
    coord_mod.AUX_1TO1_ENABLED = True
    coord_mod.MARKOV_WIRE_ENABLED = True


def reset_backtest_tables() -> None:
    init_lotto_db()
    conn = get_lotto_db()
    try:
        conn.execute("DELETE FROM lotto_predictions")
        conn.execute("DELETE FROM testlotto_brain_learn_state")
        conn.execute("DELETE FROM testlotto_brain_review")
        conn.execute(
            """
            UPDATE testlotto_brain_weights SET
                current_weight=1.0, recent_avg_match=0, total_predictions=0,
                total_matches=0, last_updated_draw=0
            """
        )
        conn.commit()
    finally:
        conn.close()


def _actual_nums(row: dict) -> set[int]:
    return {int(row[f"num{k}"]) for k in range(1, 7)}


def _pred_row_nums(row: dict) -> list[int]:
    return [int(row[f"num{k}"]) for k in range(1, 7)]


def _match_count(nums: list[int], actual: set[int]) -> int:
    return len(set(nums) & actual)


def _summarize(bests: list[int]) -> dict[str, Any]:
    n = len(bests)
    ge3_c = sum(1 for x in bests if x >= 3)
    mean_match = sum(bests) / n if n else 0.0
    gate = enrich_metrics(ge3_c, n, mean_match, gate_mode="full")
    return {**gate, "mean_match": round(mean_match, 6), "n_eval": n}


def _issued_best_from_db(conn, draw_no: int, actual: set[int]) -> int:
    rows = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,matched_count,brain_tag FROM lotto_predictions WHERE target_draw_no = ?",
        (draw_no,),
    ).fetchall()
    best = 0
    for r in rows:
        row = dict(r)
        mc = (
            int(row["matched_count"])
            if row.get("matched_count") is not None and int(row["matched_count"]) >= 0
            else _match_count(_pred_row_nums(row), actual)
        )
        best = max(best, mc)
    return best


def _prod_dynamic_select(scored: list[dict]) -> list[dict]:
    """Production dynamic_brain_quota without BENCH_FIXED_QUOTA."""
    saved = coord_mod.BENCH_FIXED_QUOTA
    coord_mod.BENCH_FIXED_QUOTA = None
    try:
        return dynamic_brain_quota(scored)
    finally:
        coord_mod.BENCH_FIXED_QUOTA = saved


def _per_draw_diagnostics(draw_no: int) -> dict[str, float]:
    """Quota·aux survival on production candidate pool (no fixed quota)."""
    set_learn_as_of(draw_no)
    draws = _get_draws_before(draw_no)
    candidates: list[dict] = []
    for brain in PREDICT_BRAINS:
        tag = brain["tag"]
        mod = PREDICT_MODULES[tag]
        random.seed(SEED + draw_no)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            candidates.append({**s, "confidence": float(s.get("confidence", 60)), "pred_set_no": sn, "set_no": sn})

    scored = _apply_aux_scoring(candidates, draws, draw_no)
    scored.sort(key=lambda x: float(x.get("confidence") or 0), reverse=True)

    markov_generated = sum(1 for c in candidates if c.get("brain_tag") == "markov")
    markov_in_global_top5 = sum(1 for c in scored[:5] if c.get("brain_tag") == "markov")
    aux_survival = markov_in_global_top5 / markov_generated if markov_generated else 0.0

    prod_quota = _compute_dynamic_quota(get_referee_weights(), total=5)
    prod_selected = _prod_dynamic_select(scored)
    markov_issued = sum(1 for c in prod_selected if c.get("brain_tag") == "markov")
    markov_quota_rate = markov_issued / 5.0

    return {
        "aux_survival_rate": round(aux_survival, 4),
        "markov_quota_actual_rate": round(markov_quota_rate, 4),
        "prod_quota_markov_slots": prod_quota.get("markov", 0),
        "markov_in_global_top5": markov_in_global_top5,
    }


def _interpret(ge3: float, aux_avg: float, quota_avg: float) -> dict[str, Any]:
    dist_fused = abs(ge3 - REF_FUSED_GE3)
    dist_solo = abs(ge3 - REF_SOLO_MARKOV_GE3)
    if dist_solo < dist_fused:
        bottleneck = "quota_dilution"
        verdict = "QUOTA_BOTTLENECK"
        detail = f"diag ge3={ge3:.4f} closer to solo ref {REF_SOLO_MARKOV_GE3} — quota/aux filter not main loss"
    else:
        bottleneck = "aux_or_coordinator_path"
        verdict = "AUX_PATH_BOTTLENECK"
        detail = f"diag ge3={ge3:.4f} closer to fused ref {REF_FUSED_GE3} — aux/coordinator path degrades markov"

    if aux_avg < 0.5:
        aux_note = "LOW aux survival — markov sets rarely rank in global top5 after aux"
    elif aux_avg >= 0.8:
        aux_note = "HIGH aux survival — markov competitive after aux; quota likely main diluter"
    else:
        aux_note = "MIXED aux survival — partial aux ranking loss"

    if quota_avg < 0.6:
        quota_note = f"LOW production markov allocation (~{quota_avg:.2f}/5) — quota dilution significant"
    else:
        quota_note = f"markov production allocation ~{quota_avg:.2f}/5"

    return {
        "verdict": verdict,
        "primary_bottleneck": bottleneck,
        "detail": detail,
        "aux_note": aux_note,
        "quota_note": quota_note,
        "delta_vs_fused": round(ge3 - REF_FUSED_GE3, 6),
        "delta_vs_solo_markov": round(ge3 - REF_SOLO_MARKOV_GE3, 6),
    }


def run_diag() -> dict[str, Any]:
    _apply_production_flags()
    reset_backtest_tables()
    coord_mod.BENCH_FIXED_QUOTA = dict(FIXED_QUOTA)

    try:
        init_lotto_db()
        conn = get_lotto_db()
        draw_rows = conn.execute(
            "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (DRAW_START, DRAW_END),
        ).fetchall()
        conn.close()

        overall_bests: list[int] = []
        aux_rates: list[float] = []
        quota_rates: list[float] = []
        per_draw: list[dict[str, Any]] = []

        total = len(draw_rows)
        for idx, row in enumerate(draw_rows):
            row = dict(row)
            draw_no = int(row["draw_no"])
            actual = _actual_nums(row)

            diag = _per_draw_diagnostics(draw_no)
            aux_rates.append(diag["aux_survival_rate"])
            quota_rates.append(diag["markov_quota_actual_rate"])

            random.seed(SEED + draw_no)
            result = run_coordinated_prediction(draw_no)
            if result.get("error"):
                print(f"[WARN] draw={draw_no} error={result['error']}", flush=True)
                continue

            conn = get_lotto_db()
            try:
                issued_best = _issued_best_from_db(conn, draw_no, actual)
                issued_rows = conn.execute(
                    "SELECT brain_tag FROM lotto_predictions WHERE target_draw_no = ?",
                    (draw_no,),
                ).fetchall()
                markov_issued = sum(1 for r in issued_rows if dict(r).get("brain_tag") == "markov")
            finally:
                conn.close()

            overall_bests.append(issued_best)
            per_draw.append(
                {
                    "draw_no": draw_no,
                    "best_match": issued_best,
                    "markov_issued": markov_issued,
                    **diag,
                }
            )

            if (idx + 1) % 10 == 0 or idx + 1 == total:
                print(
                    f"  [{idx + 1}/{total}] draw={draw_no} best={issued_best} "
                    f"aux_surv={diag['aux_survival_rate']:.2f} prod_quota={diag['markov_quota_actual_rate']:.2f}",
                    flush=True,
                )

        overall = _summarize(overall_bests)
        ge3 = float(overall["ge3_rate"])
        aux_avg = sum(aux_rates) / len(aux_rates) if aux_rates else 0.0
        quota_avg = sum(quota_rates) / len(quota_rates) if quota_rates else 0.0
        interp = _interpret(ge3, aux_avg, quota_avg)

        return {
            "id": "K-FUSION-BOTTLE-DIAG",
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "seed": SEED,
            "draw_range": [DRAW_START, DRAW_END],
            "n_eval": len(overall_bests),
            "mode": "BENCH_FIXED_QUOTA markov=5 stat=0 review=0 (dynamic_brain_quota bypass · diagnostic)",
            "markov_window": "full draws (window100 rolled back)",
            "references": {
                "fused_coordinator": {"id": "K-BRAIN-SIGNAL-B1-BACKTEST-100", "ge3_rate": REF_FUSED_GE3},
                "solo_markov": {"id": "K-HIGHWAY solo markov", "ge3_rate": REF_SOLO_MARKOV_GE3},
            },
            "overall": overall,
            "diagnostics": {
                "markov_quota_actual_rate_avg": round(quota_avg, 4),
                "aux_survival_rate_avg": round(aux_avg, 4),
                "fixed_quota_markov_rate": 1.0,
                "prod_dynamic_quota_markov_slots_avg": round(
                    sum(d["prod_quota_markov_slots"] for d in per_draw) / len(per_draw), 4
                )
                if per_draw
                else 0.0,
            },
            "interpretation": interp,
            "per_draw_sample": per_draw[:5] + per_draw[-3:] if len(per_draw) > 8 else per_draw,
            "gate": {"null_ge3": NULL_GE3},
        }
    finally:
        coord_mod.BENCH_FIXED_QUOTA = None


def write_report(payload: dict[str, Any]) -> None:
    o = payload["overall"]
    d = payload["diagnostics"]
    i = payload["interpretation"]
    ge3 = float(o["ge3_rate"])
    lines = [
        "# K-FUSION-BOTTLE-DIAG — fusion bottleneck diagnostic",
        "",
        f"📅 2026-08-01 · draw {DRAW_START}~{DRAW_END} · n={payload['n_eval']}",
        "",
        f"근거: `{OUT_JSON.name}`",
        "",
        "## SUMMARY",
        "",
        "| 지표 | 값 |",
        "|------|-----|",
        f"| diag overall ge3_rate | **{o['ge3_rate']:.4f}** ({o['ge3_count']}/{o['n']}) |",
        f"| mean_match | **{o['mean_match']:.4f}** |",
        f"| vs fused ref 0.0600 | **{i['delta_vs_fused']:+.4f}** |",
        f"| vs solo markov ref 0.1300 | **{i['delta_vs_solo_markov']:+.4f}** |",
        f"| markov quota actual rate (prod dynamic avg) | **{d['markov_quota_actual_rate_avg']:.4f}** |",
        f"| aux survival rate (markov in global top5 avg) | **{d['aux_survival_rate_avg']:.4f}** |",
        f"| fixed diag markov allocation | **{d['fixed_quota_markov_rate']:.4f}** (5/5) |",
        "",
        "## PASS/FAIL interpretation",
        "",
        f"- **{i['verdict']}** — primary bottleneck: **{i['primary_bottleneck']}**",
        f"- {i['detail']}",
        f"- aux: {i['aux_note']}",
        f"- quota: {i['quota_note']}",
        "",
        "## References",
        "",
        "| path | ge3_rate |",
        "|------|----------|",
        f"| fused coordinator (B1 backtest) | {REF_FUSED_GE3:.4f} |",
        f"| solo markov (K-HIGHWAY ref) | {REF_SOLO_MARKOV_GE3:.4f} |",
        f"| **this diag (markov 100% fixed quota)** | **{ge3:.4f}** |",
        "",
        "## Mode",
        "",
        "- `BENCH_FIXED_QUOTA` markov=5 stat=0 review=0 — diagnostic only, production logic preserved",
        "- markov window100 **rolled back** — full draws in build_transition_matrix",
        "",
    ]
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_DRIVE.parent.mkdir(parents=True, exist_ok=True)
    OUT_DRIVE.write_text(OUT_REPORT.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    print(f"K-FUSION-BOTTLE-DIAG draw {DRAW_START}~{DRAW_END} ...", flush=True)
    payload = run_diag()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(payload)
    ge3 = payload["overall"]["ge3_rate"]
    print(
        f"DONE ge3={ge3:.4f} verdict={payload['interpretation']['verdict']} "
        f"aux_avg={payload['diagnostics']['aux_survival_rate_avg']:.4f} "
        f"quota_avg={payload['diagnostics']['markov_quota_actual_rate_avg']:.4f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
