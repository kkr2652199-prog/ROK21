# -*- coding: utf-8 -*-
"""K-BRAIN-SIGNAL-B1-BACKTEST-100 — B1 virtual draws stack walk-forward n=100.

draw 1135~1234 · run_coordinated_prediction (B1 live stack · code frozen).
DB reset · predictions retained · UI draw max+1 issued after run.
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
    PREDICT_MODULES,
    _apply_aux_scoring,
    run_coordinated_prediction,
)
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.brains.shared.pattern_signal import get_pattern_signal, make_signal_draws  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from tools.bench_quick_gate import MC_SEED, NULL_GE3, enrich_metrics  # noqa: E402

DRAW_START = 1135
DRAW_END = 1234
SEED = MC_SEED
REF_DIR1_GE3 = 0.0600
REF_BASELINE_GE3 = 0.1015
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KBRAIN_SIGNAL_B1_BACKTEST_100.json"
OUT_REPORT = ROOT / "reports" / "20260801_KBRAIN_SIGNAL_B1_BACKTEST_100.md"

PERIODS: dict[str, tuple[int, int]] = {
    "early": (1135, 1159),
    "mid": (1160, 1184),
    "late": (1185, 1234),
}


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


def _draws_with_signal(draw_no: int) -> tuple[list[dict], list[dict], bool]:
    """Real draws + B1 virtual prefix (coordinator 동일)."""
    draws = _get_draws_before(draw_no)
    if not draws:
        return [], draws, False
    sig = get_pattern_signal(draws)
    vd = make_signal_draws(sig, int(draws[-1]["draw_no"]))
    active = bool(vd)
    dws = vd + draws if vd else draws
    return vd, dws, active


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


def _period_for_draw(draw_no: int) -> str | None:
    for name, (lo, hi) in PERIODS.items():
        if lo <= draw_no <= hi:
            return name
    return None


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


def _by_brain_best(draw_no: int, actual: set[int]) -> dict[str, int]:
    set_learn_as_of(draw_no)
    real_draws = _get_draws_before(draw_no)
    _, dws, _ = _draws_with_signal(draw_no)
    out: dict[str, int] = {}
    for tag, mod in PREDICT_MODULES.items():
        random.seed(SEED + draw_no)
        sets = mod.predict_sets(dws, SETS_PER_PREDICT_BRAIN)
        scored = _apply_aux_scoring(sets, real_draws, draw_no)
        best = 0
        for s in scored:
            best = max(best, _match_count(s["nums"], actual))
        out[tag] = best
    return out


def _verdict(ge3: float) -> str:
    if ge3 > REF_DIR1_GE3:
        return "PASS"
    return "FAIL"


def run_backtest() -> dict[str, Any]:
    _apply_production_flags()
    reset_backtest_tables()

    init_lotto_db()
    conn = get_lotto_db()
    draw_rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    max_draw = int(
        conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0] or DRAW_END
    )
    conn.close()

    overall_bests: list[int] = []
    brain_bests: dict[str, list[int]] = {t: [] for t in PREDICT_MODULES}
    period_bests: dict[str, list[int]] = {k: [] for k in PERIODS}
    virtual_active_flags: list[bool] = []

    total = len(draw_rows)
    for idx, row in enumerate(draw_rows):
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = _actual_nums(row)

        set_learn_as_of(draw_no)
        _, _, vactive = _draws_with_signal(draw_no)
        virtual_active_flags.append(vactive)

        random.seed(SEED + draw_no)
        result = run_coordinated_prediction(draw_no)
        if result.get("error"):
            print(f"[WARN] draw={draw_no} error={result['error']}", flush=True)
            continue

        conn = get_lotto_db()
        try:
            issued_best = _issued_best_from_db(conn, draw_no, actual)
        finally:
            conn.close()

        overall_bests.append(issued_best)
        bb = _by_brain_best(draw_no, actual)
        for tag, mc in bb.items():
            brain_bests[tag].append(mc)

        period = _period_for_draw(draw_no)
        if period:
            period_bests[period].append(issued_best)

        if (idx + 1) % 10 == 0 or idx + 1 == total:
            print(f"  [{idx + 1}/{total}] draw={draw_no} best={issued_best} virtual={vactive}", flush=True)

    next_draw = max_draw + 1
    print(f"Issuing UI prediction for draw {next_draw} ...", flush=True)
    random.seed(SEED + next_draw)
    ui_result = run_coordinated_prediction(next_draw)
    if ui_result.get("error"):
        print(f"[WARN] UI draw={next_draw} error={ui_result['error']}", flush=True)

    conn = get_lotto_db()
    try:
        pred_rows = conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0]
        ui_rows = conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no = ?",
            (next_draw,),
        ).fetchone()[0]
    finally:
        conn.close()

    overall = _summarize(overall_bests)
    by_brain = {tag: _summarize(vals) for tag, vals in brain_bests.items()}
    by_period = {p: _summarize(vals) for p, vals in period_bests.items()}
    ge3 = float(overall["ge3_rate"])
    virtual_n = sum(1 for x in virtual_active_flags if x)
    virtual_pct = round(100.0 * virtual_n / len(virtual_active_flags), 2) if virtual_active_flags else 0.0
    verdict = _verdict(ge3)

    return {
        "id": "K-BRAIN-SIGNAL-B1-BACKTEST-100",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "n_eval": len(overall_bests),
        "pipeline": "run_coordinated_prediction (B1 virtual draws + PHASE1 · code frozen)",
        "baseline_ref": {
            "direction1_fail": {"id": "K-BRAIN-SIGNAL-BACKTEST-100", "ge3_rate": REF_DIR1_GE3},
            "highway_fail": {"id": "K-HIGHWAY-BACKTEST-100", "ge3_rate": REF_DIR1_GE3},
            "full_c": {"id": "K-BACKTEST-FULL-C", "ge3_rate": REF_BASELINE_GE3},
        },
        "overall": overall,
        "by_brain": by_brain,
        "by_period": by_period,
        "by_period_note": "draw-range SSOT: early 1135-1159 · mid 1160-1184 · late 1185-1234 (n=25 each)",
        "signal_stats": {
            "virtual_draws_active_count": virtual_n,
            "total": len(virtual_active_flags),
            "virtual_active_rate_pct": virtual_pct,
        },
        "comparison": {
            "delta_ge3_vs_direction1": round(ge3 - REF_DIR1_GE3, 6),
            "delta_ge3_vs_baseline": round(ge3 - REF_BASELINE_GE3, 6),
        },
        "ui_state": {
            "db_reset": True,
            "predictions_kept": True,
            "total_prediction_rows": int(pred_rows),
            "next_draw_ui": next_draw,
            "next_draw_prediction_rows": int(ui_rows),
        },
        "verdict": verdict,
        "pass": verdict == "PASS",
        "next_on_fail": "K-BRAIN-SIGNAL-TUNE (_MIN_MAX_SIM) or B1 rollback — **형 GO 대기**",
    }


def write_report(payload: dict[str, Any]) -> None:
    o = payload["overall"]
    sig = payload["signal_stats"]
    ui = payload["ui_state"]
    ge3 = float(o["ge3_rate"])
    lines = [
        "# K-BRAIN-SIGNAL-B1-BACKTEST-100 — B1 virtual draws n=100",
        "",
        f"📅 2026-08-01 · **{payload['verdict']}** · draw {DRAW_START}~{DRAW_END}",
        "",
        f"근거: `{OUT_JSON.name}`",
        "",
        "## SUMMARY",
        "",
        "| 지표 | 값 |",
        "|------|-----|",
        f"| overall ge3_rate | **{o['ge3_rate']:.4f}** ({o['ge3_count']}/{o['n']}) |",
        f"| mean_match | **{o['mean_match']:.4f}** |",
        f"| virtual_active_rate | **{sig['virtual_active_rate_pct']:.2f}%** ({sig['virtual_draws_active_count']}/{sig['total']}) |",
        f"| vs direction1/highway 0.0600 | **{payload['comparison']['delta_ge3_vs_direction1']:+.4f}** |",
        f"| vs baseline 0.1015 | **{payload['comparison']['delta_ge3_vs_baseline']:+.4f}** |",
        f"| verdict | **{payload['verdict']}** |",
        "",
        "## PASS/FAIL (지시서)",
        "",
        "- PASS: ge3 **>** 0.0600",
        f"- FAIL: ge3 ≤ 0.0600 (현재 **{ge3:.4f}**)",
        "",
        "## by_brain (solo · draws_with_signal + aux on real draws)",
        "",
        "| brain | ge3_rate | ge3_count | mean_match |",
        "|-------|----------|-----------|------------|",
    ]
    for tag, m in payload["by_brain"].items():
        lines.append(
            f"| {tag} | {m['ge3_rate']:.4f} | {m['ge3_count']} | {m['mean_match']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## by_period (draw-range SSOT · n=25 each)",
            "",
            "| period | draw_range | ge3_rate | n |",
            "|--------|------------|----------|---|",
        ]
    )
    ranges = {"early": "1135-1159", "mid": "1160-1184", "late": "1185-1234"}
    for p, m in payload["by_period"].items():
        lines.append(f"| {p} | {ranges.get(p, '?')} | {m['ge3_rate']:.4f} | {m['n_eval']} |")
    lines.extend(
        [
            "",
            "## UI / DB",
            "",
            f"- prediction rows: **{ui['total_prediction_rows']}** · UI draw **{ui['next_draw_ui']}** ({ui['next_draw_prediction_rows']}장)",
            "",
            "## NEXT",
            "",
            f"- {payload['next_on_fail']}",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print(f"K-BRAIN-SIGNAL-B1-BACKTEST-100 draw {DRAW_START}~{DRAW_END} ...", flush=True)
    payload = run_backtest()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(payload)
    drive_copy = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_REPORT.name
    drive_copy.write_text(OUT_REPORT.read_text(encoding="utf-8"), encoding="utf-8")
    print(
        f"DONE verdict={payload['verdict']} ge3={payload['overall']['ge3_rate']:.4f} "
        f"virtual={payload['signal_stats']['virtual_active_rate_pct']:.1f}%",
        flush=True,
    )


if __name__ == "__main__":
    main()
