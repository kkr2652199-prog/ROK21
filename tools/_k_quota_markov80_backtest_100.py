# -*- coding: utf-8 -*-
"""K-QUOTA-MARKOV80-REV2 — walk-forward n=100 · markov floor 4/5.

draw 1135~1234 · production dynamic (BENCH_FIXED_QUOTA=None).
PASS if overall ge3 > 0.0900.
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
    DEFAULT_QUOTA_WEIGHTS,
    PREDICT_MODULES,
    PREDICT_TAGS,
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
REF_FUSED_GE3 = 0.0600
REF_QUOTA60_GE3 = 0.0800
PASS_GE3 = 0.0900
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KQUOTA_MARKOV80_N100.json"
OUT_REPORT = ROOT / "reports" / "20260801_KQUOTA_MARKOV80_N100.md"
OUT_DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_REPORT.name

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


def _cleanup_predictions(draw_lo: int, draw_hi: int) -> None:
    conn = get_lotto_db()
    try:
        conn.execute(
            "DELETE FROM lotto_predictions WHERE target_draw_no BETWEEN ? AND ?",
            (draw_lo, draw_hi),
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


def _period_for_draw(draw_no: int) -> str | None:
    for name, (lo, hi) in PERIODS.items():
        if lo <= draw_no <= hi:
            return name
    return None


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


def run_backtest() -> dict[str, Any]:
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
    brain_bests: dict[str, list[int]] = {t: [] for t in PREDICT_MODULES}
    period_bests: dict[str, list[int]] = {k: [] for k in PERIODS}
    quota_counter: Counter[str] = Counter()

    total = len(draw_rows)
    for idx, row in enumerate(draw_rows):
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = _actual_nums(row)

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
            for r in issued_rows:
                quota_counter[str(dict(r).get("brain_tag") or "")] += 1
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

    _cleanup_predictions(DRAW_START, DRAW_END)

    overall = _summarize(overall_bests)
    by_brain = {tag: _summarize(vals) for tag, vals in brain_bests.items()}
    by_period = {p: _summarize(vals) for p, vals in period_bests.items()}
    ge3 = float(overall["ge3_rate"])
    verdict = "PASS" if ge3 > PASS_GE3 else "FAIL"

    quota_total = sum(quota_counter.values()) or 1
    quota_avg_pct = {
        tag: round(100.0 * quota_counter[tag] / quota_total, 2) for tag in PREDICT_TAGS
    }

    return {
        "id": "K-QUOTA-MARKOV80-REV2",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "n_eval": len(overall_bests),
        "pipeline": "run_coordinated_prediction · markov floor 4/5 · DEFAULT 80/10/10",
        "quota_defaults": dict(DEFAULT_QUOTA_WEIGHTS),
        "references": {
            "fused_highway": {"ge3_rate": REF_FUSED_GE3},
            "quota60_fix": {"ge3_rate": REF_QUOTA60_GE3},
            "pass_threshold": PASS_GE3,
        },
        "overall": overall,
        "by_brain": by_brain,
        "by_period": by_period,
        "quota_stats": {
            "counts": dict(quota_counter),
            "avg_pct": quota_avg_pct,
            "prev_avg_pct": {"stat": 20.0, "markov": 60.0, "review": 20.0},
        },
        "comparison": {
            "delta_ge3_vs_fused_ref": round(ge3 - REF_FUSED_GE3, 6),
            "delta_ge3_vs_quota60": round(ge3 - REF_QUOTA60_GE3, 6),
        },
        "verdict": verdict,
        "pass": verdict == "PASS",
        "next_on_fail": "rollback DEFAULT 25/60/15 + floor logic · **형 GO 대기**",
        "gate": {"null_ge3": NULL_GE3},
    }


def write_report(payload: dict[str, Any]) -> None:
    o = payload["overall"]
    qs = payload["quota_stats"]
    ge3 = float(o["ge3_rate"])
    lines = [
        "# K-QUOTA-MARKOV80-REV2 — markov floor 4/5 n=100",
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
        f"| vs fused ref 0.0600 | **{payload['comparison']['delta_ge3_vs_fused_ref']:+.4f}** |",
        f"| vs quota60 0.0800 | **{payload['comparison']['delta_ge3_vs_quota60']:+.4f}** |",
        f"| pass threshold | ge3 **>** {PASS_GE3:.4f} |",
        f"| verdict | **{payload['verdict']}** |",
        "",
        "## quota",
        "",
        f"- DEFAULT: stat **10%** · markov **80%** · review **10%** · floor **4/5**",
        "",
        "| brain | quota60 % | markov80 % |",
        "|-------|-----------|--------------|",
    ]
    for tag in PREDICT_TAGS:
        prev = qs["prev_avg_pct"].get(tag, 0)
        after = qs["avg_pct"].get(tag, 0)
        lines.append(f"| {tag} | {prev:.1f} | **{after:.1f}** |")
    lines.extend(
        [
            "",
            "## by_period",
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
            "## PASS/FAIL",
            "",
            f"- PASS: ge3 **>** {PASS_GE3:.4f}",
            f"- FAIL: ge3 ≤ {PASS_GE3:.4f} · rollback 25/60/15 + floor · no auto-tune",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_DRIVE.parent.mkdir(parents=True, exist_ok=True)
    OUT_DRIVE.write_text(OUT_REPORT.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    print(f"K-QUOTA-MARKOV80 draw {DRAW_START}~{DRAW_END} ...", flush=True)
    payload = run_backtest()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(payload)
    print(
        f"DONE verdict={payload['verdict']} ge3={payload['overall']['ge3_rate']:.4f} "
        f"quota={payload['quota_stats']['avg_pct']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
