# -*- coding: utf-8 -*-
"""K-FUTURE-WIRE — V2 quota + aux_hint_native bucket · n=100."""
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
    BUCKET_SELECT_MODE,
    PREDICT_TAGS,
    QUOTA_ADAPTIVE_MIN_EACH,
    QUOTA_DOMINANCE_FLOOR,
    SOLO_GE3_PRIORS,
    _compute_dynamic_quota,
    _get_quota_weights,
    run_coordinated_prediction,
)
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from tools.bench_quick_gate import MC_SEED, NULL_GE3, enrich_metrics  # noqa: E402

DRAW_START = 1135
DRAW_END = 1234
SEED = MC_SEED
PASS_GE3 = 0.0900
REF_V2_GE3 = 0.0900
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260803_KFUTURE_WIRE_N100.json"
OUT_REPORT = ROOT / "reports" / "20260803_KFUTURE_WIRE_N100.md"
OUT_DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_REPORT.name

PERIODS = {"early": (1135, 1159), "mid": (1160, 1184), "late": (1185, 1234)}


def _apply_production_flags() -> None:
    stat_predict.HINT_WEIGHT = 0.15
    markov_predict.HINT_WEIGHT = 0.15
    review_predict.HINT_WEIGHT = 0.15
    markov_learn.LEARN_WIRED = True
    coord_mod.AUX_1TO1_ENABLED = True
    coord_mod.MARKOV_WIRE_ENABLED = True
    coord_mod.BUCKET_SELECT_MODE = "aux_hint_native"
    coord_mod.BENCH_FIXED_QUOTA = None


def reset_backtest_tables() -> None:
    init_lotto_db()
    conn = get_lotto_db()
    try:
        conn.execute("DELETE FROM lotto_predictions")
        conn.execute("DELETE FROM testlotto_brain_learn_state")
        conn.execute("DELETE FROM testlotto_brain_review")
        conn.execute(
            "UPDATE testlotto_brain_weights SET current_weight=1.0, recent_avg_match=0, "
            "total_predictions=0, total_matches=0, last_updated_draw=0"
        )
        conn.commit()
    finally:
        conn.close()


def _cleanup_predictions(lo: int, hi: int) -> None:
    conn = get_lotto_db()
    try:
        conn.execute(
            "DELETE FROM lotto_predictions WHERE target_draw_no BETWEEN ? AND ?", (lo, hi)
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
    return {
        **enrich_metrics(ge3_c, n, mean_match, gate_mode="full"),
        "mean_match": round(mean_match, 6),
        "n_eval": n,
    }


def _period_for(draw_no: int) -> str | None:
    for name, (lo, hi) in PERIODS.items():
        if lo <= draw_no <= hi:
            return name
    return None


def _issued_best(conn, draw_no: int, actual: set[int]) -> int:
    rows = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,matched_count FROM lotto_predictions "
        "WHERE target_draw_no=?",
        (draw_no,),
    ).fetchall()
    best = 0
    for r in rows:
        row = dict(r)
        if row.get("matched_count") is not None and int(row["matched_count"]) >= 0:
            mc = int(row["matched_count"])
        else:
            mc = _match_count(_pred_row_nums(row), actual)
        best = max(best, mc)
    return best


def run_backtest() -> dict[str, Any]:
    _apply_production_flags()
    reset_backtest_tables()
    conn = get_lotto_db()
    draw_rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    overall: list[int] = []
    period_bests: dict[str, list[int]] = {k: [] for k in PERIODS}
    quota_counter: Counter[str] = Counter()

    for idx, row in enumerate(draw_rows):
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = _actual_nums(row)
        random.seed(SEED + draw_no)
        result = run_coordinated_prediction(draw_no)
        if result.get("error"):
            continue
        set_learn_as_of(draw_no)
        conn = get_lotto_db()
        try:
            best = _issued_best(conn, draw_no, actual)
            for r in conn.execute(
                "SELECT brain_tag FROM lotto_predictions WHERE target_draw_no=?",
                (draw_no,),
            ).fetchall():
                quota_counter[str(dict(r).get("brain_tag") or "")] += 1
        finally:
            conn.close()
        overall.append(best)
        p = _period_for(draw_no)
        if p:
            period_bests[p].append(best)
        if (idx + 1) % 25 == 0:
            print(f"  [{idx + 1}/{len(draw_rows)}] draw={draw_no} best={best}", flush=True)

    _cleanup_predictions(DRAW_START, DRAW_END)
    o = _summarize(overall)
    ge3 = float(o["ge3_rate"])
    qt = sum(quota_counter.values()) or 1
    avg_pct = {t: round(100 * quota_counter[t] / qt, 2) for t in PREDICT_TAGS}
    delta = round(ge3 - REF_V2_GE3, 4)
    passed = ge3 > PASS_GE3

    return {
        "id": "K-FUTURE-WIRE",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "pipeline": "V2 solo×ref + aux_hint_native + per-brain RNG isolate",
        "config": {
            "BUCKET_SELECT_MODE": BUCKET_SELECT_MODE,
            "BRAIN_RNG_SEED_BASE": coord_mod.BRAIN_RNG_SEED_BASE,
            "SOLO_GE3_PRIORS": SOLO_GE3_PRIORS,
            "QUOTA_ADAPTIVE_MIN_EACH": QUOTA_ADAPTIVE_MIN_EACH,
            "QUOTA_DOMINANCE_FLOOR": QUOTA_DOMINANCE_FLOOR,
        },
        "references": {
            "v2_baseline_ge3": REF_V2_GE3,
            "pass_threshold": PASS_GE3,
            "full_survey_aux_hint_quota": 0.1134,
        },
        "overall": o,
        "by_period": {p: _summarize(v) for p, v in period_bests.items()},
        "quota_stats": {"counts": dict(quota_counter), "avg_pct": avg_pct},
        "verdict": "PASS" if passed else "FAIL",
        "pass": passed,
        "delta_ge3_vs_v2": delta,
        "gate": {"null_ge3": NULL_GE3},
    }


def write_report(payload: dict[str, Any]) -> None:
    o = payload["overall"]
    qs = payload["quota_stats"]
    lines = [
        "# K-FUTURE-WIRE — aux_hint_native bucket n=100",
        "",
        f"📅 2026-08-03 · **{payload['verdict']}** · draw {DRAW_START}~{DRAW_END}",
        "",
        f"근거: `{OUT_JSON.name}`",
        "",
        "## SUMMARY",
        "",
        f"| ge3_rate | **{o['ge3_rate']:.4f}** ({o['ge3_count']}/{o['n']}) |",
        f"| mean_match | **{o['mean_match']:.4f}** |",
        f"| vs V2 baseline 0.09 | **{payload['delta_ge3_vs_v2']:+.4f}** |",
        f"| BUCKET_SELECT_MODE | **{payload['config']['BUCKET_SELECT_MODE']}** |",
        f"| verdict | **{payload['verdict']}** (gate > {PASS_GE3}) |",
        "",
        "## quota avg %",
        "",
    ]
    for t in PREDICT_TAGS:
        lines.append(f"- {t}: **{qs['avg_pct'].get(t, 0):.1f}%**")
    lines.extend(["", "## by_period", ""])
    for p, m in payload["by_period"].items():
        lines.append(f"- {p}: ge3={m['ge3_rate']:.4f} n={m['n_eval']}")
    lines.extend(
        [
            "",
            "## design",
            "",
            "- 독립 3뇌 predict → 뇌전용 aux_hint 보존 → V2 quota 배분",
            "- 뇌내 선별: set_no_asc 폐기 → aux_hint_score + native_confidence",
            "- 표시용 coordinator confidence 재작성은 발권 키와 분리",
            "",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_DRIVE.parent.mkdir(parents=True, exist_ok=True)
    OUT_DRIVE.write_text(OUT_REPORT.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    print("K-FUTURE-WIRE n=100 ...", flush=True)
    print(f"BUCKET_SELECT_MODE={BUCKET_SELECT_MODE}", flush=True)
    payload = run_backtest()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(payload)
    print(
        f"DONE ge3={payload['overall']['ge3_rate']:.4f} "
        f"delta_v2={payload['delta_ge3_vs_v2']:+.4f} "
        f"verdict={payload['verdict']} quota={payload['quota_stats']['avg_pct']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
