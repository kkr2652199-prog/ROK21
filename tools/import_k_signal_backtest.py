# -*- coding: utf-8 -*-
"""K-SIGNAL QUICK 백테스트 per-draw DB 적재 (walk-forward · 컨닝 없음).

기존 JSON은 회차별 결과 없음 → 본 스크립트가 WF 재실행 후 DB 저장.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.bench_quick_gate import (  # noqa: E402
    MC_SEED,
    QUICK_N_EVAL,
    filter_draw_rows,
    resolve_eval_window,
)

REPACK_JSON = ROOT / "docs" / "benchmarks" / "20260730_KSIGNAL_REPACK_survey.json"
SELECT_JSON = ROOT / "docs" / "benchmarks" / "20260730_KSIGNAL_SELECT_survey.json"


def _run_repack_per_draw(
    eval_window,
    *,
    survey_id: str = "K-SIGNAL-REPACK-01",
    gate_mode: str = "quick",
    source_json: str | None = None,
) -> dict:
    import random

    from app.testlotto.backtest_store import delete_runs_for_survey_strategy, insert_backtest_run, insert_draw_results
    from app.testlotto.models import get_lotto_db, init_lotto_db
    from app.testlotto.signal_pool import (
        RollingSignalLearner,
        _build_hint,
        _pool_by_brain,
        expand_pool,
        repack_by_brain,
    )
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import clear_history_cache, set_learn_as_of
    from app.testlotto.tier_utils import score_predicted_set
    from tools._k_signal_repack_survey import _best_match, _best_tier, _reset_predictions_for_eval

    strategy_id = "signal_repack"
    if source_json is None:
        source_json = str(REPACK_JSON.as_posix())

    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (eval_window.draw_start, eval_window.draw_end),
    ).fetchall()
    conn.close()
    rows = filter_draw_rows(rows, eval_window)

    learner = RollingSignalLearner()
    per_draw: list[dict] = []
    hits_list: list[int] = []
    tier_acc = {"r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0}

    for ri, row in enumerate(rows):
        if ri % 50 == 0:
            print(f"  REPACK {ri}/{len(rows)} draw={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        actual_list = sorted(actual)
        bonus = int(row.get("bonus") or 0)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        num_ema, pos_ema = learner.snapshot()
        random.seed(MC_SEED)
        pool = expand_pool(draws, draw_no)
        pool_br = _pool_by_brain(pool)
        hint = _build_hint(draws, draw_no)
        repacked = repack_by_brain(pool_br, hint, num_ema, pos_ema)

        best = _best_match(repacked, actual)
        best_tr, _ = _best_tier(repacked, actual_list, bonus)
        hits_list.append(best)
        per_draw.append({"draw_no": draw_no, "best_hits": best, "best_tier": best_tr})
        if best_tr == 1:
            tier_acc["r1"] += 1
        elif best_tr == 2:
            tier_acc["r2"] += 1
        elif best_tr == 3:
            tier_acc["r3"] += 1
        elif best_tr == 4:
            tier_acc["r4"] += 1
        elif best_tr == 5:
            tier_acc["r5"] += 1

        learner.update_from_pool(pool_br, actual)

    n = len(hits_list)
    ge3_c = sum(1 for x in hits_list if x >= 3)
    mean_h = sum(hits_list) / n if n else 0.0

    init_lotto_db()
    conn = get_lotto_db()
    try:
        delete_runs_for_survey_strategy(conn, survey_id, strategy_id)
        run_id = insert_backtest_run(
            conn,
            survey_id=survey_id,
            strategy_id=strategy_id,
            gate_mode=gate_mode,
            eval_mode="best_of_15",
            n_draws=n,
            seed=MC_SEED,
            draw_start=eval_window.draw_start,
            draw_end=eval_window.draw_end,
            ge3_rate=round(ge3_c / n, 4) if n else 0.0,
            mean_hits=round(mean_h, 4),
            ge3_count=ge3_c,
            tiers=tier_acc,
            source_json=source_json,
            note="WF live per-draw · signal_repack · no future leak",
        )
        insert_draw_results(conn, run_id, per_draw)
        conn.commit()
    finally:
        conn.close()

    from tools.bench_quick_gate import enrich_metrics

    metrics = enrich_metrics(ge3_c, n, mean_h, gate_mode=gate_mode if gate_mode != "tail100" else "quick")
    metrics["tiers"] = tier_acc
    return {
        "run_id": run_id,
        "survey_id": survey_id,
        "strategy_id": strategy_id,
        "n": n,
        "draw_range": [eval_window.draw_start, eval_window.draw_end],
        "metrics": metrics,
        "per_draw_count": len(per_draw),
    }


def _run_select_per_draw(
    eval_window,
    *,
    survey_id: str = "K-SIGNAL-SELECT-01",
    gate_mode: str = "quick",
    source_json: str | None = None,
) -> dict:
    import random

    from app.testlotto.backtest_store import delete_runs_for_survey_strategy, insert_backtest_run, insert_draw_results
    from app.testlotto.models import get_lotto_db, init_lotto_db
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.tier_utils import score_predicted_set
    from tools._k_signal_select_survey import (
        WINDOW_WEEKS,
        WINDOW_SIGNAL,
        _best_match,
        _bin_match_score,
        _build_hint,
        _expected_bins,
        _expand_pool,
        _hint_overlap_score,
        _live_candidates,
        _pick_top_greedy,
    )

    strategy_id = "combined"
    if source_json is None:
        source_json = str(SELECT_JSON.as_posix())

    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (eval_window.draw_start, eval_window.draw_end),
    ).fetchall()
    conn.close()
    rows = filter_draw_rows(rows, eval_window)

    per_draw: list[dict] = []
    hits_list: list[int] = []
    tier_acc = {"r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0}

    for ri, row in enumerate(rows):
        if ri % 50 == 0:
            print(f"  SELECT {ri}/{len(rows)} draw={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        actual_list = sorted(actual)
        bonus = int(row.get("bonus") or 0)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        random.seed(MC_SEED)
        pool = _expand_pool(draws, draw_no)
        hint = _build_hint(draws, WINDOW_WEEKS, WINDOW_SIGNAL, draw_no)
        expected_bins = _expected_bins(draws)
        selected = _pick_top_greedy(
            pool,
            lambda nums: (
                0.5 * _hint_overlap_score(nums, hint)
                + 0.35 * _bin_match_score(nums, expected_bins)
            ),
            diversity_weight=0.15,
        )

        best = _best_match(selected, actual)
        best_tr = 0
        for c in selected:
            scored = score_predicted_set(c["nums"], actual_list, bonus)
            tr = int(scored["tier_rank"])
            if tr > 0 and (best_tr == 0 or tr < best_tr):
                best_tr = tr

        hits_list.append(best)
        per_draw.append({"draw_no": draw_no, "best_hits": best, "best_tier": best_tr})
        if best_tr == 1:
            tier_acc["r1"] += 1
        elif best_tr == 2:
            tier_acc["r2"] += 1
        elif best_tr == 3:
            tier_acc["r3"] += 1
        elif best_tr == 4:
            tier_acc["r4"] += 1
        elif best_tr == 5:
            tier_acc["r5"] += 1

    n = len(hits_list)
    ge3_c = sum(1 for x in hits_list if x >= 3)
    mean_h = sum(hits_list) / n if n else 0.0

    init_lotto_db()
    conn = get_lotto_db()
    try:
        delete_runs_for_survey_strategy(conn, survey_id, strategy_id)
        run_id = insert_backtest_run(
            conn,
            survey_id=survey_id,
            strategy_id=strategy_id,
            gate_mode=gate_mode,
            eval_mode="best_of_5_from_30",
            n_draws=n,
            seed=MC_SEED,
            draw_start=eval_window.draw_start,
            draw_end=eval_window.draw_end,
            ge3_rate=round(ge3_c / n, 4) if n else 0.0,
            mean_hits=round(mean_h, 4),
            ge3_count=ge3_c,
            tiers=tier_acc,
            source_json=source_json,
            note="WF live per-draw · combined selector · no future leak",
        )
        insert_draw_results(conn, run_id, per_draw)
        conn.commit()
    finally:
        conn.close()

    from tools.bench_quick_gate import enrich_metrics

    metrics = enrich_metrics(ge3_c, n, mean_h, gate_mode=gate_mode if gate_mode != "tail100" else "quick")
    metrics["tiers"] = tier_acc
    return {
        "run_id": run_id,
        "survey_id": survey_id,
        "strategy_id": strategy_id,
        "n": n,
        "draw_range": [eval_window.draw_start, eval_window.draw_end],
        "metrics": metrics,
        "per_draw_count": len(per_draw),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Import K-SIGNAL backtest per-draw to DB")
    ap.add_argument("--which", choices=["repack", "select", "both"], default="both")
    ap.add_argument("--n-eval", type=int, default=QUICK_N_EVAL)
    args = ap.parse_args()

    from tools._k_signal_repack_survey import _reset_predictions_for_eval  # noqa: E402

    eval_window = resolve_eval_window(args.n_eval, sample_mode="tail")
    t0 = time.time()
    out: dict = {"eval_window": [eval_window.draw_start, eval_window.draw_end], "runs": []}

    if args.which in ("repack", "both"):
        _reset_predictions_for_eval(eval_window.draw_start, eval_window.draw_end)

    if args.which in ("repack", "both"):
        print("K-SIGNAL-REPACK-01 signal_repack WF import...", flush=True)
        out["runs"].append(_run_repack_per_draw(eval_window))

    if args.which in ("select", "both"):
        print("K-SIGNAL-SELECT-01 combined WF import...", flush=True)
        out["runs"].append(_run_select_per_draw(eval_window))

    out["elapsed_sec"] = round(time.time() - t0, 1)
    print(json.dumps(out, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
