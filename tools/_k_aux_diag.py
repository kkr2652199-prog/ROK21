# -*- coding: utf-8 -*-
"""K-AUX-DIAG — per-aux ablation diagnostic (READ-ONLY bench).

Purpose: identify which of 4 aux brains causes most markov set dropouts from final top 5.
draw 1135~1234 · n=100 walk-forward · production quota 25/60/15 · AUX_1TO1_ENABLED=True.
Bench-only overrides — coordinator.py permanent logic unchanged.
"""
from __future__ import annotations

import json
import random
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import coordinator as coord_mod  # noqa: E402
from app.testlotto.brains.coordinator import (  # noqa: E402
    PREDICT_BRAINS,
    PREDICT_MODULES,
    _apply_aux_scoring,
    run_coordinated_prediction,
)
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from tools.bench_quick_gate import MC_SEED, NULL_GE3, enrich_metrics  # noqa: E402

DRAW_START = 1135
DRAW_END = 1234
SEED = MC_SEED
REF_BASELINE_GE3 = 0.0800
NEUTRAL_AUX = 0.5
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KAUX_DIAG.json"
OUT_REPORT = ROOT / "reports" / "20260801_KAUX_DIAG.md"
OUT_DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_REPORT.name

SCENARIOS: list[dict[str, Any]] = [
    {"id": "baseline", "label": "all aux ON", "disabled": []},
    {"id": "aux_miss_off", "label": "miss_detective weight=0", "disabled": ["miss"]},
    {"id": "aux_spotlight_off", "label": "pattern_spotlight weight=0", "disabled": ["spotlight"]},
    {"id": "aux_balance_off", "label": "balance_keeper weight=0", "disabled": ["balance"]},
    {"id": "aux_referee_off", "label": "referee weight=0", "disabled": ["referee"]},
    {"id": "all_aux_off", "label": "all 4 aux OFF (quota only)", "disabled": ["miss", "spotlight", "balance", "referee"]},
]

AUX_TO_BRAIN = {
    "miss": "review",
    "spotlight": "markov",
    "balance": "stat",
}


def _apply_production_flags() -> None:
    stat_predict.HINT_WEIGHT = 0.15
    markov_predict.HINT_WEIGHT = 0.15
    review_predict.HINT_WEIGHT = 0.15
    markov_learn.LEARN_WIRED = True
    coord_mod.AUX_1TO1_ENABLED = True
    coord_mod.MARKOV_WIRE_ENABLED = True
    coord_mod.BENCH_FIXED_QUOTA = None


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
        "SELECT num1,num2,num3,num4,num5,num6,matched_count FROM lotto_predictions WHERE target_draw_no = ?",
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


def _markov_survival_on_draw(draw_no: int, apply_scoring: Callable) -> float:
    """Markov sets in global top5 after aux scoring (pre-quota)."""
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

    scored = apply_scoring(candidates, draws, draw_no)
    scored.sort(key=lambda x: float(x.get("confidence") or 0), reverse=True)

    markov_generated = sum(1 for c in candidates if c.get("brain_tag") == "markov")
    markov_in_top5 = sum(1 for c in scored[:5] if c.get("brain_tag") == "markov")
    return markov_in_top5 / markov_generated if markov_generated else 0.0


@contextmanager
def _scenario_patches(disabled: list[str]):
    """Bench-only aux ablation via monkey-patch (no permanent coordinator changes)."""
    from app.testlotto.brains import aux_balance_keeper, aux_miss_detective, aux_pattern_spotlight, aux_referee
    from app.testlotto.learn_state import get_referee_weights

    orig_apply = coord_mod._apply_aux_scoring
    disabled_set = set(disabled)
    all_off = disabled_set == {"miss", "spotlight", "balance", "referee"}

    def _neutral_score(*_a, **_kw) -> float:
        return NEUTRAL_AUX

    def _patched_composite(
        nums: list[int],
        draws: list[dict],
        target_draw_no: int,
        brain_tag: str | None = None,
    ) -> float:
        if all_off:
            return 0.0
        # Production AUX_1TO1: dedicated aux only (referee via brain_w in _apply_aux_scoring)
        if coord_mod.AUX_1TO1_ENABLED and brain_tag:
            if brain_tag == "review" and "miss" in disabled_set:
                return NEUTRAL_AUX
            if brain_tag == "markov" and "spotlight" in disabled_set:
                return NEUTRAL_AUX
            if brain_tag == "stat" and "balance" in disabled_set:
                return NEUTRAL_AUX
            dedicated = coord_mod.BRAIN_DEDICATED_AUX.get(brain_tag)
            if dedicated is not None:
                return dedicated.score_set(nums, draws, target_draw_no, brain_tag=brain_tag)
        # Fallback: global 4 aux with weight ablation
        modules = [aux_miss_detective, aux_pattern_spotlight, aux_balance_keeper, aux_referee]
        key_map = ["miss", "spotlight", "balance", "referee"]
        total = 0.0
        wsum = 0.0
        for mod, w, key in zip(modules, coord_mod.AUX_WEIGHTS, key_map):
            if key in disabled_set:
                continue
            total += w * mod.score_set(nums, draws, target_draw_no, brain_tag=brain_tag)
            wsum += w
        if wsum <= 0:
            return 0.0
        return total

    def _patched_apply(candidates: list[dict], draws: list[dict], target_draw_no: int) -> list[dict]:
        if all_off:
            ref_weights = get_referee_weights()
            out: list[dict] = []
            for c in candidates:
                base = float(c.get("confidence", 60))
                brain_w = ref_weights.get(c.get("brain_tag", ""), 1.0 / 3)
                final_conf = min(99.5, base * 0.5 * brain_w + base * 0.1)
                out.append({**c, "confidence": round(final_conf, 1)})
            return out

        if "referee" not in disabled_set:
            out: list[dict] = []
            ref_weights = get_referee_weights()
            for c in candidates:
                tag = c.get("brain_tag", "") or None
                aux_score = _patched_composite(c["nums"], draws, target_draw_no, brain_tag=tag)
                base = float(c.get("confidence", 60))
                brain_w = ref_weights.get(c.get("brain_tag", ""), 1.0 / 3)
                final_conf = min(99.5, base * 0.5 * brain_w + aux_score * 40 + base * 0.1)
                out.append({**c, "confidence": round(final_conf, 1)})
            return out

        flat_w = 1.0 / 3.0
        out = []
        for c in candidates:
            tag = c.get("brain_tag", "") or None
            aux_score = _patched_composite(c["nums"], draws, target_draw_no, brain_tag=tag)
            base = float(c.get("confidence", 60))
            final_conf = min(99.5, base * 0.5 * flat_w + aux_score * 40 + base * 0.1)
            out.append({**c, "confidence": round(final_conf, 1)})
        return out

    patches = [
        patch.object(coord_mod, "_aux_composite_score", _patched_composite),
        patch.object(coord_mod, "_apply_aux_scoring", _patched_apply),
    ]
    for p in patches:
        p.start()
    try:
        yield _patched_apply
    finally:
        for p in patches:
            p.stop()


def run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    _apply_production_flags()
    reset_backtest_tables()

    init_lotto_db()
    conn = get_lotto_db()
    draw_rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    overall_bests: list[int] = []
    survival_rates: list[float] = []
    total = len(draw_rows)

    with _scenario_patches(scenario["disabled"]) as apply_scoring:
        for idx, row in enumerate(draw_rows):
            row = dict(row)
            draw_no = int(row["draw_no"])
            actual = _actual_nums(row)

            surv = _markov_survival_on_draw(draw_no, apply_scoring)
            survival_rates.append(surv)

            random.seed(SEED + draw_no)
            result = run_coordinated_prediction(draw_no)
            if result.get("error"):
                print(f"  [WARN] {scenario['id']} draw={draw_no} error={result['error']}", flush=True)
                continue

            conn = get_lotto_db()
            try:
                issued_best = _issued_best_from_db(conn, draw_no, actual)
            finally:
                conn.close()

            overall_bests.append(issued_best)

            if (idx + 1) % 25 == 0 or idx + 1 == total:
                print(
                    f"  [{scenario['id']}] [{idx + 1}/{total}] draw={draw_no} "
                    f"best={issued_best} surv={surv:.2f}",
                    flush=True,
                )

    overall = _summarize(overall_bests)
    surv_avg = sum(survival_rates) / len(survival_rates) if survival_rates else 0.0
    ge3 = float(overall["ge3_rate"])

    return {
        "scenario_id": scenario["id"],
        "label": scenario["label"],
        "disabled_aux": scenario["disabled"],
        "overall": overall,
        "ge3_rate": ge3,
        "markov_survival_rate_avg": round(surv_avg, 4),
        "n_eval": len(overall_bests),
    }


def _rank_scenarios(baseline: dict[str, Any], ablations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank aux by dropout contribution: turning OFF improves survival/ge3 most = worst aux."""
    base_ge3 = float(baseline["ge3_rate"])
    base_surv = float(baseline["markov_survival_rate_avg"])
    ranking: list[dict[str, Any]] = []

    aux_map = {
        "aux_miss_off": "miss_detective",
        "aux_spotlight_off": "pattern_spotlight",
        "aux_balance_off": "balance_keeper",
        "aux_referee_off": "referee",
    }

    for s in ablations:
        sid = s["scenario_id"]
        if sid == "all_aux_off":
            continue
        ge3_delta = round(float(s["ge3_rate"]) - base_ge3, 6)
        surv_delta = round(float(s["markov_survival_rate_avg"]) - base_surv, 6)
        dropout_contrib = round(base_surv - float(s["markov_survival_rate_avg"]), 6)
        ranking.append(
            {
                "aux": aux_map.get(sid, sid),
                "scenario_id": sid,
                "ge3_when_off": float(s["ge3_rate"]),
                "ge3_delta_vs_baseline": ge3_delta,
                "markov_survival_when_off": float(s["markov_survival_rate_avg"]),
                "survival_delta_vs_baseline": surv_delta,
                "dropout_contribution": dropout_contrib,
            }
        )

    ranking.sort(
        key=lambda x: (x["dropout_contribution"], -x["ge3_delta_vs_baseline"]),
        reverse=True,
    )
    for i, r in enumerate(ranking, 1):
        r["rank"] = i
    return ranking


def run_diag() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        print(f"\n=== {scenario['id']}: {scenario['label']} ===", flush=True)
        results.append(run_scenario(scenario))

    baseline = next(r for r in results if r["scenario_id"] == "baseline")
    ablations = [r for r in results if r["scenario_id"] != "baseline"]
    ranking = _rank_scenarios(baseline, ablations)

    for r in results:
        r["ge3_delta_vs_baseline"] = round(float(r["ge3_rate"]) - float(baseline["ge3_rate"]), 6)
        r["survival_delta_vs_baseline"] = round(
            float(r["markov_survival_rate_avg"]) - float(baseline["markov_survival_rate_avg"]), 6
        )

    return {
        "id": "K-AUX-DIAG",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "mode": "production AUX_1TO1 + dynamic quota 25/60/15 · bench-only aux ablation",
        "reference_baseline_ge3": REF_BASELINE_GE3,
        "scenarios": results,
        "dropout_ranking": ranking,
        "worst_aux": ranking[0]["aux"] if ranking else "unknown",
        "gate": {"null_ge3": NULL_GE3},
    }


def write_report(payload: dict[str, Any]) -> None:
    baseline = next(s for s in payload["scenarios"] if s["scenario_id"] == "baseline")
    lines = [
        "# K-AUX-DIAG — per-aux ablation diagnostic",
        "",
        f"📅 2026-08-01 · draw {DRAW_START}~{DRAW_END} · n=100 walk-forward",
        "",
        f"근거: `{OUT_JSON.name}`",
        "",
        "## SUMMARY",
        "",
        f"- baseline ge3 (expect ~{REF_BASELINE_GE3:.4f}): **{baseline['ge3_rate']:.4f}**",
        f"- worst aux (most markov dropout): **{payload['worst_aux']}**",
        "",
        "## scenarios",
        "",
        "| scenario | disabled | ge3_rate | ge3 Δ | markov survival | survival Δ |",
        "|----------|----------|----------|-------|-----------------|------------|",
    ]
    for s in payload["scenarios"]:
        off = s.get("disabled_aux") or s.get("disabled") or []
        disabled = ",".join(off) if off else "—"
        lines.append(
            f"| {s['scenario_id']} | {disabled} | **{s['ge3_rate']:.4f}** | "
            f"{s['ge3_delta_vs_baseline']:+.4f} | {s['markov_survival_rate_avg']:.4f} | "
            f"{s['survival_delta_vs_baseline']:+.4f} |"
        )

    lines.extend(
        [
            "",
            "## dropout contribution ranking",
            "",
            "Higher rank = aux causes more markov dropout when ON (baseline survival − survival when OFF).",
            "",
            "| rank | aux | dropout contrib | ge3 when OFF | ge3 Δ | survival when OFF |",
            "|------|-----|-----------------|--------------|-------|-------------------|",
        ]
    )
    for r in payload["dropout_ranking"]:
        lines.append(
            f"| {r['rank']} | **{r['aux']}** | {r['dropout_contribution']:.4f} | "
            f"{r['ge3_when_off']:.4f} | {r['ge3_delta_vs_baseline']:+.4f} | "
            f"{r['markov_survival_when_off']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Mode",
            "",
            "- production: AUX_1TO1_ENABLED=True · DEFAULT_QUOTA_WEIGHTS 25/60/15",
            "- bench-only monkey-patch on `_aux_composite_score` / `_apply_aux_scoring`",
            "- coordinator.py permanent logic **unchanged**",
            "",
            "## NEXT",
            "",
            "- no auto next steps · **형 GO 대기**",
        ]
    )

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_DRIVE.parent.mkdir(parents=True, exist_ok=True)
    OUT_DRIVE.write_text(OUT_REPORT.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    print(f"K-AUX-DIAG draw {DRAW_START}~{DRAW_END} · 6 scenarios ...", flush=True)
    payload = run_diag()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        write_report(payload)
    except Exception as exc:
        print(f"[WARN] write_report failed: {exc}", flush=True)
        raise

    print("\n=== RESULTS ===", flush=True)
    for s in payload["scenarios"]:
        print(
            f"  {s['scenario_id']:20s} ge3={s['ge3_rate']:.4f} "
            f"surv={s['markov_survival_rate_avg']:.4f} Δge3={s['ge3_delta_vs_baseline']:+.4f}",
            flush=True,
        )
    print(f"worst_aux={payload['worst_aux']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
