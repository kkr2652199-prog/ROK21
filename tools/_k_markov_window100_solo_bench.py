# -*- coding: utf-8 -*-
"""K-MARKOV-WINDOW100-SOLO — markov brain solo walk-forward n=200 (READ-ONLY).

window=100 in build_transition_matrix · markov_brain.predict.run solo (n_sets=5)
draw 1035~1234 · seed=42 · set_learn_as_of + _get_draws_before

PASS: ge3_rate > 0.1300 (K-HIGHWAY solo markov reference)
FAIL: ge3_rate <= 0.1300 (no auto-tune on FAIL)
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

from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from app.testlotto.tier_utils import pick_best_set_index, score_predicted_set  # noqa: E402
from tools.bench_quick_gate import NULL_GE3, enrich_metrics  # noqa: E402

SEED = 42
N_EVAL = 200
DRAW_START = 1035
DRAW_END = 1234
N_SETS = 5
REF_HIGHWAY_SOLO_GE3 = 0.1300
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KMARKOV_WINDOW100_SOLO_N200.json"
OUT_REPORT = ROOT / "reports" / "20260801_KMARKOV_WINDOW100_SOLO_N200.md"
OUT_DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / "20260801_KMARKOV_WINDOW100_SOLO_N200.md"

PERIODS: dict[str, tuple[int, int]] = {
    "early": (1035, 1101),
    "mid": (1102, 1168),
    "late": (1169, 1234),
}


def _period_for_draw(draw_no: int) -> str | None:
    for name, (lo, hi) in PERIODS.items():
        if lo <= draw_no <= hi:
            return name
    return None


def _best_match(sets: list[dict], actual_nums: list[int], bonus: int) -> int:
    if not sets:
        return 0
    scored = [score_predicted_set(s.get("nums") or [], actual_nums, bonus) for s in sets]
    best_idx = pick_best_set_index(scored)
    return int(scored[best_idx]["matched_count"])


def _summarize(matches: list[int]) -> dict[str, Any]:
    n = len(matches)
    ge3_c = sum(1 for x in matches if x >= 3)
    mean_match = sum(matches) / n if n else 0.0
    gate = enrich_metrics(ge3_c, n, mean_match, gate_mode="full")
    return {
        **gate,
        "mean_match": round(mean_match, 6),
        "n": n,
    }


def run_bench() -> dict[str, Any]:
    markov_predict.HINT_WEIGHT = 0.15
    markov_learn.LEARN_WIRED = True

    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    if len(rows) > N_EVAL:
        rows = rows[-N_EVAL:]

    overall: list[int] = []
    period_bests: dict[str, list[int]] = {k: [] for k in PERIODS}

    for row in rows:
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual_nums = sorted(int(row[f"num{k}"]) for k in range(1, 7))
        bonus = int(row.get("bonus") or 0)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        random.seed(SEED)
        sets = markov_predict.run(draws, N_SETS)
        mc = _best_match(sets, actual_nums, bonus)
        overall.append(mc)

        period = _period_for_draw(draw_no)
        if period:
            period_bests[period].append(mc)

    summary = _summarize(overall)
    by_period = {p: _summarize(vals) for p, vals in period_bests.items()}
    ge3_rate = float(summary["ge3_rate"])
    delta = round(ge3_rate - REF_HIGHWAY_SOLO_GE3, 6)
    passed = ge3_rate > REF_HIGHWAY_SOLO_GE3

    return {
        "id": "K-MARKOV-WINDOW100-SOLO-N200",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "n_eval": summary["n"],
        "path": "markov_brain.predict.run solo (window=100 in build_transition_matrix)",
        "window": 100,
        "reference": {
            "id": "K-HIGHWAY solo markov",
            "ge3_rate": REF_HIGHWAY_SOLO_GE3,
        },
        "overall": summary,
        "by_period": by_period,
        "comparison": {
            "delta_ge3_vs_highway_solo": delta,
            "ref_ge3": REF_HIGHWAY_SOLO_GE3,
        },
        "gate": {
            "rule": "ge3_rate > 0.1300",
            "null_ge3": NULL_GE3,
        },
        "verdict": "PASS" if passed else "FAIL",
        "pass": passed,
    }


def write_report(payload: dict[str, Any]) -> None:
    o = payload["overall"]
    lines = [
        "# K-MARKOV-WINDOW100-SOLO-N200 — markov solo window=100",
        "",
        f"📅 2026-08-01 · **{payload['verdict']}** · draw {DRAW_START}~{DRAW_END} · n={payload['n_eval']}",
        "",
        f"근거: `{OUT_JSON.name}`",
        "",
        "## SUMMARY",
        "",
        "| 지표 | 값 |",
        "|------|-----|",
        f"| solo ge3_rate | **{o['ge3_rate']:.4f}** ({o['ge3_count']}/{o['n']}) |",
        f"| mean_match | **{o['mean_match']:.4f}** |",
        f"| vs K-HIGHWAY solo 0.1300 | **{payload['comparison']['delta_ge3_vs_highway_solo']:+.4f}** |",
        f"| p vs null ({NULL_GE3}) | {o.get('p_vs_null', '미확인')} |",
        f"| verdict | **{payload['verdict']}** |",
        "",
        "## by_period (draw-range · n≈67 each)",
        "",
        "| period | draw_range | ge3_rate | ge3_count | mean_match |",
        "|--------|------------|----------|-----------|------------|",
    ]
    for p, m in payload["by_period"].items():
        dr = PERIODS[p]
        lines.append(
            f"| {p} | {dr[0]}~{dr[1]} | {m['ge3_rate']:.4f} | {m['ge3_count']}/{m['n']} | {m['mean_match']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## gate",
            "",
            f"- rule: ge3 > {REF_HIGHWAY_SOLO_GE3}",
            f"- result: **{payload['verdict']}**",
            "",
        ]
    )
    text = "\n".join(lines) + "\n"
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(text, encoding="utf-8")
    OUT_DRIVE.parent.mkdir(parents=True, exist_ok=True)
    OUT_DRIVE.write_text(text, encoding="utf-8")


def main() -> int:
    payload = run_bench()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
