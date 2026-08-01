# -*- coding: utf-8 -*-
"""K-BRAIN-SIGNAL-BACKTEST-100 — pattern_signal + coordinator walk-forward n=100.

draw 1135~1234 · full coordinator (pattern_signal blend + PHASE1 stack).
Resets predictions/learn before run · **predictions retained** for UI (no cleanup).
After backtest: issues prediction for draw max+1 (next UI target).
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
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
from app.testlotto.brains.shared.pattern_signal import get_pattern_signal  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from tools.bench_quick_gate import MC_SEED, NULL_GE3, enrich_metrics  # noqa: E402

DRAW_START = 1135
DRAW_END = 1234
N_EVAL = DRAW_END - DRAW_START + 1
SEED = MC_SEED
REF_HIGHWAY_GE3 = 0.0600
REF_BASELINE_GE3 = 0.1015
SIGNAL_SKIP_MAX = (1.0 / 45.0) * 1.5
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KBRAIN_SIGNAL_BACKTEST_100.json"
OUT_REPORT = ROOT / "reports" / "20260801_KBRAIN_SIGNAL_BACKTEST_100.md"

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
    """예측·학습 기록만 초기화 (lotto_draws 보존)."""
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


def _is_signal_active(draws: list[dict]) -> bool:
    sig = get_pattern_signal(draws)
    return max(sig.values()) >= SIGNAL_SKIP_MAX


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
    draws = _get_draws_before(draw_no)
    out: dict[str, int] = {}
    for tag, mod in PREDICT_MODULES.items():
        random.seed(SEED + draw_no)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        scored = _apply_aux_scoring(sets, draws, draw_no)
        best = 0
        for s in scored:
            best = max(best, _match_count(s["nums"], actual))
        out[tag] = best
    return out


def _verdict(ge3: float, signal_active_pct: float) -> str:
    if ge3 <= REF_HIGHWAY_GE3 or signal_active_pct <= 5.0:
        return "FAIL"
    if ge3 > REF_HIGHWAY_GE3 and signal_active_pct > 20.0:
        return "PASS"
    return "HOLD"


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
    signal_active_flags: list[bool] = []

    total = len(draw_rows)
    for idx, row in enumerate(draw_rows):
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = _actual_nums(row)

        set_learn_as_of(draw_no)
        pre_draws = _get_draws_before(draw_no)
        signal_active_flags.append(_is_signal_active(pre_draws))

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
            print(f"  [{idx + 1}/{total}] draw={draw_no} best={issued_best}", flush=True)

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
    signal_active_n = sum(1 for x in signal_active_flags if x)
    signal_active_pct = round(100.0 * signal_active_n / len(signal_active_flags), 2) if signal_active_flags else 0.0
    verdict = _verdict(ge3, signal_active_pct)

    return {
        "id": "K-BRAIN-SIGNAL-BACKTEST-100",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "n_eval": len(overall_bests),
        "pipeline": "run_coordinated_prediction (pattern_signal blend + PHASE1)",
        "baseline_ref": {
            "highway_fail": {"id": "K-HIGHWAY-BACKTEST-100", "ge3_rate": REF_HIGHWAY_GE3},
            "full_c": {"id": "K-BACKTEST-FULL-C", "ge3_rate": REF_BASELINE_GE3},
        },
        "overall": overall,
        "by_brain": by_brain,
        "by_period": by_period,
        "signal_stats": {
            "active_count": signal_active_n,
            "total": len(signal_active_flags),
            "active_rate_pct": signal_active_pct,
            "skip_threshold_max": SIGNAL_SKIP_MAX,
        },
        "comparison": {
            "delta_ge3_vs_highway": round(ge3 - REF_HIGHWAY_GE3, 6),
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
    }


def write_report(payload: dict[str, Any]) -> None:
    o = payload["overall"]
    sig = payload["signal_stats"]
    ui = payload["ui_state"]
    lines = [
        "# K-BRAIN-SIGNAL-BACKTEST-100 — pattern_signal stack n=100",
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
        f"| p vs null ({NULL_GE3}) | {o.get('p_vs_null', '미확인')} |",
        f"| signal_active_rate | **{sig['active_rate_pct']:.2f}%** ({sig['active_count']}/{sig['total']}) |",
        f"| vs highway 0.0600 | **{payload['comparison']['delta_ge3_vs_highway']:+.4f}** |",
        f"| vs baseline 0.1015 | **{payload['comparison']['delta_ge3_vs_baseline']:+.4f}** |",
        f"| verdict | **{payload['verdict']}** |",
        "",
        "## PASS/FAIL 기준",
        "",
        "- PASS: ge3 > 0.0600 **AND** signal_active > 20%",
        "- FAIL: ge3 ≤ 0.0600 **OR** signal_active ≤ 5%",
        "",
        "## by_brain (solo best-of-5)",
        "",
        "| brain | ge3_rate | ge3_count | mean_match |",
        "|-------|----------|-----------|------------|",
    ]
    for tag, m in payload["by_brain"].items():
        lines.append(
            f"| {tag} | {m['ge3_rate']:.4f} | {m['ge3_count']} | {m['mean_match']:.4f} |"
        )
    lines.extend(["", "## by_period", "", "| period | ge3_rate | n |", "|--------|----------|---|"])
    for p, m in payload["by_period"].items():
        lines.append(f"| {p} | {m['ge3_rate']:.4f} | {m['n_eval']} |")
    lines.extend(
        [
            "",
            "## UI / DB 상태",
            "",
            f"- DB reset: **{ui['db_reset']}** (lotto_draws 보존)",
            f"- walk-forward 예측 **유지** (cleanup 없음)",
            f"- 총 prediction 행: **{ui['total_prediction_rows']}**",
            f"- UI 다음 회차: **{ui['next_draw_ui']}** ({ui['next_draw_prediction_rows']}장)",
            "",
            "## NEXT",
            "",
            "- **K-BRAIN-SIGNAL-TUNE** — _MIN_MAX_SIM·k 조정 · **형 GO 대기**",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print(f"K-BRAIN-SIGNAL-BACKTEST-100 draw {DRAW_START}~{DRAW_END} ...", flush=True)
    payload = run_backtest()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(payload)
    drive_copy = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_REPORT.name
    drive_copy.write_text(OUT_REPORT.read_text(encoding="utf-8"), encoding="utf-8")
    print(
        f"DONE verdict={payload['verdict']} ge3={payload['overall']['ge3_rate']:.4f} "
        f"signal_active={payload['signal_stats']['active_rate_pct']:.1f}% "
        f"ui_draw={payload['ui_state']['next_draw_ui']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
