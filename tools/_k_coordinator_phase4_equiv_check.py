# -*- coding: utf-8 -*-
"""K-COORDINATOR-PHASE4-EQUIV — deprecated predict vs brain package 동치 검증 (READ-ONLY).

Per brain (stat, markov, review):
  A = predict_stat_fairy / predict_flow_shaman / predict_review_king .predict_sets
  B = stat_brain / markov_brain / review_brain .predict.run (predict_sets alias)
seed=42 · n_eval=200 · draw 1035~1234 walk-forward
PASS each: ge3 diff < 0.002 · mean diff < 0.01 · nums match rate 100%
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import predict_flow_shaman, predict_review_king, predict_stat_fairy  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from app.testlotto.tier_utils import pick_best_set_index, score_predicted_set  # noqa: E402

SEED = 42
N_EVAL = 200
DRAW_START = 1035
DRAW_END = 1234
N_SETS = 5
OUT = ROOT / "docs" / "benchmarks" / "20260801_KCOORDINATOR_PHASE4_EQUIV.json"

GE3_DIFF_MAX = 0.002
MEAN_DIFF_MAX = 0.01
NUMS_MATCH_MIN = 1.0

BRAINS: list[tuple[str, Callable, Callable, str, str]] = [
    (
        "stat",
        predict_stat_fairy.predict_sets,
        stat_predict.run,
        "app.testlotto.brains.predict_stat_fairy.predict_sets",
        "app.testlotto.brains.stat_brain.predict.run",
    ),
    (
        "markov",
        predict_flow_shaman.predict_sets,
        markov_predict.run,
        "app.testlotto.brains.predict_flow_shaman.predict_sets",
        "app.testlotto.brains.markov_brain.predict.run",
    ),
    (
        "review",
        predict_review_king.predict_sets,
        review_predict.run,
        "app.testlotto.brains.predict_review_king.predict_sets",
        "app.testlotto.brains.review_brain.predict.run",
    ),
]


def _best_match(sets: list[dict], actual_nums: list[int], bonus: int) -> int:
    if not sets:
        return 0
    scored = []
    for s in sets:
        tier = score_predicted_set(s.get("nums") or [], actual_nums, bonus)
        scored.append(tier)
    best_idx = pick_best_set_index(scored)
    return int(scored[best_idx]["matched_count"])


def _sets_equal(a: list[dict], b: list[dict]) -> bool:
    if len(a) != len(b):
        return False
    for sa, sb in zip(a, b):
        na = sorted(int(x) for x in sa.get("nums") or [])
        nb = sorted(int(x) for x in sb.get("nums") or [])
        if na != nb:
            return False
        if abs(float(sa.get("confidence", 0)) - float(sb.get("confidence", 0))) > 1e-9:
            return False
        if sa.get("reasoning") != sb.get("reasoning"):
            return False
        if sa.get("method") != sb.get("method"):
            return False
        if sa.get("brain_tag") != sb.get("brain_tag"):
            return False
        if sa.get("rank") != sb.get("rank"):
            return False
    return True


def run_brain_equiv(
    brain_id: str,
    fn_a: Callable,
    fn_b: Callable,
    path_a: str,
    path_b: str,
    rows: list[dict],
) -> dict[str, Any]:
    a_ge3 = b_ge3 = 0
    a_matches: list[int] = []
    b_matches: list[int] = []
    nums_match_count = 0
    mismatches: list[dict[str, Any]] = []

    for row in rows:
        draw_no = int(row["draw_no"])
        actual_nums = sorted(int(row[f"num{k}"]) for k in range(1, 7))
        bonus = int(row.get("bonus") or 0)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        random.seed(SEED)
        sets_a = fn_a(draws, N_SETS)

        random.seed(SEED)
        sets_b = fn_b(draws, N_SETS)

        if _sets_equal(sets_a, sets_b):
            nums_match_count += 1
        else:
            mismatches.append(
                {
                    "draw_no": draw_no,
                    "a_nums": [s.get("nums") for s in sets_a],
                    "b_nums": [s.get("nums") for s in sets_b],
                }
            )

        ma = _best_match(sets_a, actual_nums, bonus)
        mb = _best_match(sets_b, actual_nums, bonus)
        a_matches.append(ma)
        b_matches.append(mb)
        if ma >= 3:
            a_ge3 += 1
        if mb >= 3:
            b_ge3 += 1

    n = len(a_matches)
    a_ge3_rate = a_ge3 / n if n else 0.0
    b_ge3_rate = b_ge3 / n if n else 0.0
    a_mean = sum(a_matches) / n if n else 0.0
    b_mean = sum(b_matches) / n if n else 0.0
    ge3_diff = abs(a_ge3_rate - b_ge3_rate)
    mean_diff = abs(a_mean - b_mean)
    nums_match_rate = nums_match_count / n if n else 0.0

    passed = (
        ge3_diff < GE3_DIFF_MAX
        and mean_diff < MEAN_DIFF_MAX
        and nums_match_rate >= NUMS_MATCH_MIN
    )

    return {
        "brain": brain_id,
        "path_a": path_a,
        "path_b": path_b,
        "metrics": {
            "a_ge3_rate": round(a_ge3_rate, 6),
            "b_ge3_rate": round(b_ge3_rate, 6),
            "ge3_diff": round(ge3_diff, 6),
            "a_mean_match": round(a_mean, 6),
            "b_mean_match": round(b_mean, 6),
            "mean_diff": round(mean_diff, 6),
            "nums_match_rate": round(nums_match_rate, 6),
            "nums_match_count": nums_match_count,
        },
        "mismatch_samples": mismatches[:5],
        "verdict": "PASS" if passed else "FAIL",
        "pass": passed,
    }


def run_equiv() -> dict[str, Any]:
    init_lotto_db()
    conn = get_lotto_db()
    db_rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    rows = [dict(r) for r in db_rows]
    if len(rows) > N_EVAL:
        rows = rows[-N_EVAL:]

    brain_results = []
    for brain_id, fn_a, fn_b, path_a, path_b in BRAINS:
        brain_results.append(run_brain_equiv(brain_id, fn_a, fn_b, path_a, path_b, rows))

    all_pass = all(r["pass"] for r in brain_results)

    return {
        "id": "K-COORDINATOR-PHASE4-EQUIV",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "n_eval": len(rows),
        "draw_range": [DRAW_START, DRAW_END],
        "n_sets": N_SETS,
        "thresholds": {
            "ge3_diff_max": GE3_DIFF_MAX,
            "mean_diff_max": MEAN_DIFF_MAX,
            "nums_match_min": NUMS_MATCH_MIN,
        },
        "brains": brain_results,
        "verdict": "PASS" if all_pass else "FAIL",
        "pass": all_pass,
    }


def main() -> int:
    result = run_equiv()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
