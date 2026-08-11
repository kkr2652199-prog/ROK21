# -*- coding: utf-8 -*-
"""K-FORCE-POOL-BACKTEST-100 — 예측 리셋 후 최신 3뇌 knobs로 100회 WF 재적재.

형 지시: 강제 백테=리셋 → 패치된 3뇌로 재예측. 컨닝 금지(_get_draws_before).
구 캐시 재입력 금지(전체 리셋 후 덮어쓰기).

범위: 1137~1236 (n=100) · seed=MC_SEED
산출: pool_view_cache(schema4) + backtest_runs/draw_results
ge3는 모니터만(성적클레임 금지).
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KFORCE_POOL_BACKTEST_100_v5.json"
OUT_MD = ROOT / "reports" / "20260812_KFORCE_POOL_BACKTEST_100_v5.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SURVEY_ID = "K-FORCE-POOL-BT-100-V5"
STRATEGY_ID = "pool10_repack5_min1_ov5"


def _reset() -> dict[str, Any]:
    os.environ["K_RESET_APPLY"] = "1"
    from tools._k_predict_reset import apply_reset, survey

    s = survey()
    targets = list(s["to_delete"].keys())
    deleted = apply_reset(targets) if targets else {}
    return {"targets": targets, "deleted": deleted, "before": s["to_delete"]}


def _best_of_payload(payload: dict[str, Any], actual: set[int], bonus: int) -> tuple[int, int]:
    from app.testlotto.tier_utils import score_predicted_set

    best_hits = -1
    best_tier = 0
    for kind in ("pool_by_brain", "repack_by_brain"):
        by = payload.get(kind) or {}
        for tag, sets in by.items():
            for s in sets or []:
                nums = [int(x) for x in (s.get("nums") or [])]
                hits = len(set(nums) & actual)
                tr = score_predicted_set(nums, sorted(actual), bonus)
                tier = int(tr.get("tier_rank") or 0) if isinstance(tr, dict) else int(tr or 0)
                if hits > best_hits or (hits == best_hits and tier and (not best_tier or tier < best_tier)):
                    best_hits = hits
                    best_tier = tier
    return max(0, best_hits), best_tier


def _run_wf() -> dict[str, Any]:
    from app.testlotto.backtest_store import (
        delete_runs_for_survey_strategy,
        insert_backtest_run,
        insert_draw_results,
    )
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_view_cache import save_pool_view_cache
    from app.testlotto.signal_pool import (
        MC_SEED,
        RollingSignalLearner,
        _build_hint,
        _pool_by_brain,
        build_hint_by_brain,
        expand_pool,
        repack_by_brain,
        tune_snapshot,
    )

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (LO, HI),
    ).fetchall()
    conn.close()

    learner = RollingSignalLearner()
    # warm before LO (incremental · full rebuild_pool warm 회피)
    warm_from = max(1, LO - 80)
    wconn = get_lotto_db()
    try:
        warm_rows = wconn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
            "WHERE draw_no>=? AND draw_no<? ORDER BY draw_no",
            (warm_from, LO),
        ).fetchall()
    finally:
        wconn.close()
    for wrow in warm_rows:
        dno = int(wrow["draw_no"])
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        if len(draws) < 50:
            continue
        random.seed(MC_SEED)
        pool = expand_pool(draws, dno, seed=MC_SEED)
        pool_br = _pool_by_brain(pool)
        actual = {int(wrow[f"num{k}"]) for k in range(1, 7)}
        learner.update_from_pool(pool_br, actual)

    per_draw: list[dict[str, Any]] = []
    peek_checks: list[dict[str, Any]] = []
    t0 = time.perf_counter()

    for i, row in enumerate(rows):
        row = dict(row)
        dno = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        bonus = int(row.get("bonus") or 0)
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        # 컨닝 가드: 재료 max draw_no < target
        max_mat = max((int(d["draw_no"]) for d in draws), default=0)
        if max_mat >= dno:
            raise RuntimeError(f"PEEK_VIOLATION draw={dno} max_material={max_mat}")
        if i < 3 or i == len(rows) - 1:
            peek_checks.append({"draw": dno, "max_material": max_mat, "n_draws": len(draws)})

        num_ema, pos_ema = learner.snapshot()
        random.seed(MC_SEED)
        pool = expand_pool(draws, dno, seed=MC_SEED)
        pool_br = _pool_by_brain(pool)
        hint_by = build_hint_by_brain(draws, dno)
        fallback = _build_hint(draws, dno)
        repacked = repack_by_brain(
            pool_br,
            fallback,
            num_ema,
            pos_ema,
            target_draw_no=dno,
            hint_by_brain=hint_by,
        )

        by_brain_pool: dict[str, list[dict]] = {}
        for tag, sets in pool_br.items():
            by_brain_pool[tag] = [
                {
                    "set_no": int(c.get("pred_set_no") or c.get("set_no") or 1),
                    "nums": [int(x) for x in c["nums"]],
                    "brain_tag": tag,
                    "kind": "pool",
                }
                for c in sorted(sets, key=lambda x: int(x.get("pred_set_no") or 0))
            ]
        by_brain_repack: dict[str, list[dict]] = {"stat": [], "markov": [], "review": []}
        for c in repacked:
            tag = str(c["brain_tag"])
            entry = {
                "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
                "nums": [int(x) for x in c["nums"]],
                "brain_tag": tag,
                "kind": "repack",
                "assemble": c.get("assemble") or "signal_top",
            }
            if c.get("source"):
                entry["source"] = c["source"]
                entry["source_set_no"] = c.get("source_set_no")
            by_brain_repack.setdefault(tag, []).append(entry)

        payload = {
            "ok": True,
            "target_draw_no": dno,
            "no_peek": True,
            "pool_sets_per_brain": 10,
            "repack_sets_per_brain": 5,
            "seed": MC_SEED,
            "tune_snapshot": tune_snapshot(),
            "pool_by_brain": by_brain_pool,
            "repack_by_brain": by_brain_repack,
        }
        save_pool_view_cache(dno, payload)
        hits, tier = _best_of_payload(payload, actual, bonus)
        per_draw.append({"draw_no": dno, "best_hits": hits, "best_tier": tier})
        learner.update_from_pool(pool_br, actual)
        if (i + 1) % 10 == 0:
            print(f"  WF {i+1}/{len(rows)} draw={dno} best={hits}", flush=True)

    n = len(per_draw)
    ge3 = sum(1 for r in per_draw if r["best_hits"] >= 3)
    mean_h = sum(r["best_hits"] for r in per_draw) / n if n else 0.0
    tiers = {"r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0}
    for r in per_draw:
        t = int(r["best_tier"] or 0)
        if 1 <= t <= 5:
            tiers[f"r{t}"] += 1

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        delete_runs_for_survey_strategy(conn, SURVEY_ID, STRATEGY_ID)
        run_id = insert_backtest_run(
            conn,
            survey_id=SURVEY_ID,
            strategy_id=STRATEGY_ID,
            gate_mode="force100",
            eval_mode="best_of_pool10_repack5",
            n_draws=n,
            seed=MC_SEED,
            draw_start=LO,
            draw_end=HI,
            ge3_rate=ge3 / n if n else 0.0,
            mean_hits=mean_h,
            ge3_count=ge3,
            tiers=tiers,
            p_value=None,
            verdict="MONITOR_ONLY",
            delta_ge3_vs_pin=None,
            source_json=str(OUT_JSON.as_posix()),
            note="force reset+WF · tuned knobs · _get_draws_before · no peek · ge3 not claim",
        )
        insert_draw_results(conn, run_id, per_draw)
        conn.commit()
    finally:
        conn.close()

    # post counts
    conn = get_lotto_db()
    pool_n = conn.execute("SELECT COUNT(*) FROM testlotto_pool_view_cache").fetchone()[0]
    pool_draws = conn.execute(
        "SELECT COUNT(DISTINCT draw_no) FROM testlotto_pool_view_cache"
    ).fetchone()[0]
    bt_n = conn.execute("SELECT COUNT(*) FROM testlotto_backtest_draw_results").fetchone()[0]
    conn.close()

    return {
        "run_id": run_id,
        "n": n,
        "draw_range": [LO, HI],
        "mean_hits": round(mean_h, 6),
        "ge3_count": ge3,
        "ge3_rate": round(ge3 / n, 6) if n else 0.0,
        "tiers": tiers,
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "peek_checks": peek_checks,
        "tune_snapshot": tune_snapshot(),
        "post_counts": {
            "pool_view_cache_rows": pool_n,
            "pool_view_cache_draws": pool_draws,
            "backtest_draw_results": bt_n,
        },
        "note": "ge3/mean = monitor only · not performance claim",
    }


def main() -> int:
    print("== RESET ==")
    reset_info = _reset()
    print("deleted", reset_info["deleted"])
    print("== WF 1137-1236 ==")
    wf = _run_wf()
    print("WF done", {k: wf[k] for k in ("run_id", "n", "mean_hits", "ge3_rate", "post_counts", "elapsed_s")})

    payload = {
        "id": "K-FORCE-POOL-BACKTEST-100",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "reset": reset_info,
        "wf": wf,
        "verdict": "REBUILT_OK" if wf.get("post_counts", {}).get("pool_view_cache_draws") == 100 else "PARTIAL",
        "ge3_used_as_claim": False,
        "no_peek": True,
        # pool/repack best ≠ 발권5장. 병기 측정: tools/_k_bt_issue_path_metric.py
        "issue_path_note": "BT tiers are pool10+repack5 path · run _k_bt_issue_path_metric for issued-5 dual metric",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = f"""# K-FORCE-POOL-BACKTEST-100 v4

📅 2026-08-12 KST · **단계⑫** · 강제 리셋 + live knobs WF 재적재  
(min_each=1 · oversample m5 · cand_B · union · ⑪발권 VERIFY_OK 후)

## 실행
1. `_k_predict_reset` APPLY — 예측·pool캐시·백테·evolve 삭제 (draws 보존)
2. 1137~1236 n100 · `_get_draws_before` · `expand_pool`+`build_hint_by_brain`+`repack_by_brain`
3. 매회 `save_pool_view_cache` (schema4 · tune_snapshot 포함)
4. `backtest_runs` / `draw_results` 적재

## 결과
- run_id={wf['run_id']} · n={wf['n']} · range={wf['draw_range']}
- pool_draws={wf['post_counts']['pool_view_cache_draws']} · bt_rows={wf['post_counts']['backtest_draw_results']}
- mean_hits={wf['mean_hits']} · ge3_rate={wf['ge3_rate']} (**모니터만 · 클레임금지**)
- tiers={wf['tiers']}
- elapsed={wf['elapsed_s']}s
- knobs={wf['tune_snapshot']}
- peek_checks={wf['peek_checks']}

## 판정
- **verdict** = **{payload['verdict']}** · ge3미클레임 · 1237아님
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", payload["verdict"])
    print("WROTE", OUT_JSON)
    return 0 if payload["verdict"] == "REBUILT_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
