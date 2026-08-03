# -*- coding: utf-8 -*-
"""K-FUTURE-WIRE revalidate — reset walk-forward · QUICK200 / FULL1182.

Usage:
  python tools/_k_future_wire_revalidate.py --mode quick   # n=200 · 1035~1234
  python tools/_k_future_wire_revalidate.py --mode full    # n=1182 · 53~1234
"""
from __future__ import annotations

import argparse
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
    run_coordinated_prediction,
)
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from tools.bench_quick_gate import (  # noqa: E402
    DRAW_END,
    DRAW_START,
    FULL_N_EVAL,
    MC_SEED,
    NULL_GE3,
    QUICK_N_EVAL,
    QUICK_TAIL_START,
    WIRE_PIN_GE3,
    enrich_metrics,
    filter_draw_rows,
    resolve_eval_window,
)

SEED = MC_SEED
REF_N100_GE3 = 0.1500
# patch gate (n=100 era) — QUICK/FULL는 pin·null도 병기
PASS_GE3_PATCH = 0.0900


def _paths(mode: str) -> tuple[Path, Path, Path]:
    tag = "QUICK200" if mode == "quick" else "FULL"
    name = f"20260803_KFUTURE_WIRE_{tag}"
    js = ROOT / "docs" / "benchmarks" / f"{name}.json"
    md = ROOT / "reports" / f"{name}.md"
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / md.name
    return js, md, drive


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
    """당첨 lotto_draws 유지 · pred/learn/review/weights 리셋 후 재기입."""
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
        try:
            conn.execute("DELETE FROM testlotto_pool_view_cache")
        except Exception:
            pass
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


def _summarize(bests: list[int], gate_mode: str) -> dict[str, Any]:
    n = len(bests)
    ge3_c = sum(1 for x in bests if x >= 3)
    mean_match = sum(bests) / n if n else 0.0
    return {
        **enrich_metrics(ge3_c, n, mean_match, gate_mode=gate_mode),
        "mean_match": round(mean_match, 6),
        "n_eval": n,
    }


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


def run_backtest(mode: str) -> dict[str, Any]:
    _apply_production_flags()
    reset_backtest_tables()

    if mode == "quick":
        window = resolve_eval_window(n_eval=QUICK_N_EVAL, sample_mode="tail")
        gate_mode = "quick"
        periods = {
            "early": (QUICK_TAIL_START, QUICK_TAIL_START + 49),
            "mid": (QUICK_TAIL_START + 50, QUICK_TAIL_START + 99),
            "late": (QUICK_TAIL_START + 100, DRAW_END),
        }
    else:
        window = resolve_eval_window(n_eval=FULL_N_EVAL, sample_mode="full")
        gate_mode = "full"
        # FULL thirds by draw index in 53~1234
        span = DRAW_END - DRAW_START + 1
        t1 = DRAW_START + span // 3 - 1
        t2 = DRAW_START + 2 * span // 3 - 1
        periods = {
            "early": (DRAW_START, t1),
            "mid": (t1 + 1, t2),
            "late": (t2 + 1, DRAW_END),
        }

    conn = get_lotto_db()
    draw_rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    draw_rows = filter_draw_rows(draw_rows, window)

    overall: list[int] = []
    period_bests: dict[str, list[int]] = {k: [] for k in periods}
    quota_counter: Counter[str] = Counter()
    lo = int(dict(draw_rows[0])["draw_no"]) if draw_rows else window.draw_start
    hi = int(dict(draw_rows[-1])["draw_no"]) if draw_rows else window.draw_end

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
        for pname, (plo, phi) in periods.items():
            if plo <= draw_no <= phi:
                period_bests[pname].append(best)
                break
        step = 25 if mode == "quick" else 100
        if (idx + 1) % step == 0 or idx + 1 == total:
            print(f"  [{idx + 1}/{total}] draw={draw_no} best={best}", flush=True)

    _cleanup_predictions(lo, hi)
    o = _summarize(overall, gate_mode)
    ge3 = float(o["ge3_rate"])
    qt = sum(quota_counter.values()) or 1
    avg_pct = {t: round(100 * quota_counter[t] / qt, 2) for t in PREDICT_TAGS}

    # 판정: enrich_metrics verdict + patch gate(>0.09) + vs n100
    patch_pass = ge3 > PASS_GE3_PATCH
    pin_delta = round(ge3 - WIRE_PIN_GE3, 4)
    n100_delta = round(ge3 - REF_N100_GE3, 4)

    return {
        "id": f"K-FUTURE-WIRE-{'QUICK200' if mode == 'quick' else 'FULL'}",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "mode": mode,
        "draw_range": [lo, hi],
        "n_eval": len(overall),
        "pipeline": "reset→walkforward · V2 solo×ref + aux_hint_native + per-brain RNG",
        "reset": {
            "lotto_predictions": True,
            "learn_state": True,
            "brain_review": True,
            "brain_weights": True,
            "pool_view_cache": True,
            "lotto_draws": False,
        },
        "config": {
            "BUCKET_SELECT_MODE": BUCKET_SELECT_MODE,
            "BRAIN_RNG_SEED_BASE": coord_mod.BRAIN_RNG_SEED_BASE,
            "SOLO_GE3_PRIORS": SOLO_GE3_PRIORS,
            "QUOTA_ADAPTIVE_MIN_EACH": QUOTA_ADAPTIVE_MIN_EACH,
            "QUOTA_DOMINANCE_FLOOR": QUOTA_DOMINANCE_FLOOR,
        },
        "references": {
            "n100_ge3": REF_N100_GE3,
            "v2_baseline_ge3": 0.09,
            "pass_threshold_patch": PASS_GE3_PATCH,
            "null_ge3": NULL_GE3,
            "wire_pin_ge3": WIRE_PIN_GE3,
        },
        "overall": o,
        "by_period": {p: _summarize(v, gate_mode) for p, v in period_bests.items()},
        "quota_stats": {"counts": dict(quota_counter), "avg_pct": avg_pct},
        "delta_ge3_vs_n100": n100_delta,
        "delta_ge3_vs_pin": pin_delta,
        "patch_gate_pass": patch_pass,
        "verdict": "PASS" if patch_pass else "FAIL",
        "pass": patch_pass,
        "gate": {"null_ge3": NULL_GE3, "wire_pin_ge3": WIRE_PIN_GE3, "enrich_verdict": o.get("verdict")},
    }


def write_report(
    payload: dict[str, Any], out_json: Path, out_report: Path, out_drive: Path
) -> None:
    o = payload["overall"]
    qs = payload["quota_stats"]
    mode = payload["mode"]
    title = "QUICK n=200" if mode == "quick" else "FULL n=1182"
    lines = [
        f"# K-FUTURE-WIRE — {title} 재검증 (리셋 후 재기입)",
        "",
        f"📅 2026-08-03 · **{payload['verdict']}** · draw {payload['draw_range'][0]}~{payload['draw_range'][1]}",
        "",
        f"근거: `{out_json.name}`",
        "",
        "## SUMMARY",
        "",
        f"| ge3_rate | **{o['ge3_rate']:.4f}** ({o['ge3_count']}/{o['n']}) |",
        f"| mean_match | **{o['mean_match']:.4f}** |",
        f"| vs n100 0.1500 | **{payload['delta_ge3_vs_n100']:+.4f}** |",
        f"| vs wire pin 0.1447 | **{payload['delta_ge3_vs_pin']:+.4f}** |",
        f"| patch gate (>0.09) | **{payload['verdict']}** |",
        f"| enrich_verdict | {payload['gate'].get('enrich_verdict')} |",
        f"| BUCKET_SELECT_MODE | **{payload['config']['BUCKET_SELECT_MODE']}** |",
        "",
        "## reset",
        "",
        "- lotto_predictions / learn_state / brain_review / weights / pool cache **삭제 후 재기입**",
        "- lotto_draws(당첨) **유지**",
        "",
        "## quota avg %",
        "",
    ]
    for t in PREDICT_TAGS:
        lines.append(f"- {t}: **{qs['avg_pct'].get(t, 0):.1f}%**")
    lines.extend(["", "## by_period", ""])
    for p, m in payload["by_period"].items():
        lines.append(f"- {p}: ge3={m['ge3_rate']:.4f} n={m['n_eval']}")
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_drive.parent.mkdir(parents=True, exist_ok=True)
    out_drive.write_text(out_report.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("quick", "full"), required=True)
    args = ap.parse_args()
    mode = args.mode
    out_json, out_report, out_drive = _paths(mode)
    print(f"K-FUTURE-WIRE revalidate mode={mode} reset+WF ...", flush=True)
    print(
        f"BUCKET={BUCKET_SELECT_MODE} RNG_BASE={coord_mod.BRAIN_RNG_SEED_BASE}",
        flush=True,
    )
    payload = run_backtest(mode)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(payload, out_json, out_report, out_drive)
    print(
        f"DONE mode={mode} ge3={payload['overall']['ge3_rate']:.4f} "
        f"vs_n100={payload['delta_ge3_vs_n100']:+.4f} "
        f"verdict={payload['verdict']} → {out_json.name}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
