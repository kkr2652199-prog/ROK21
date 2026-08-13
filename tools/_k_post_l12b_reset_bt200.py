# -*- coding: utf-8 -*-
"""K-POST-L12B-RESET-BT200 — 리셋 후 스모크(1234~1236) → 200회(1037~1236).

순서: 숙제테이블 포함 리셋(별도 APPLY) → 본 도구 스모크 → 통과 시 200회.
경로 분리: 발권 quota5(coordinator) ≠ pool10+repack5.
뇌별 solo는 메모리 채점(DB 발권 덮어쓰기 금지).
ge3/등수 = 모니터만 · 1237아님 · 컨닝=_get_draws_before.
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260813_KPOST_L12B_RESET_BT200.json"
OUT_MD = ROOT / "reports" / "20260813_KPOST_L12B_RESET_BT200.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SMOKE_LO, SMOKE_HI = 1234, 1236
BT_LO, BT_HI = 1037, 1236
SEED = 42
BRAINS = ("stat", "markov", "review")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums: list) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def _actual_row(conn, dno: int) -> tuple[set[int], int] | None:
    row = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=?",
        (dno,),
    ).fetchone()
    if not row:
        return None
    actual = {int(row[f"num{k}"]) for k in range(1, 7)}
    return actual, int(row["bonus"] or 0)


def _peek_ok(draws: list[dict], dno: int) -> tuple[bool, int]:
    max_mat = max((int(d["draw_no"]) for d in draws), default=0)
    return max_mat < dno, max_mat


def _score_sets(sets: list[dict], actual: set[int], bonus: int) -> dict[str, Any]:
    from app.testlotto.tier_utils import score_predicted_set

    hits: list[int] = []
    best_h, best_t = -1, 0
    for s in sets:
        nums = [int(x) for x in (s.get("nums") or [])]
        sc = score_predicted_set(nums, sorted(actual), bonus)
        h = int(sc["matched_count"])
        t = int(sc["tier_rank"] or 0)
        hits.append(h)
        if h > best_h or (h == best_h and t and (not best_t or t < best_t)):
            best_h, best_t = h, t
    return {
        "n": len(hits),
        "mean": round(mean(hits), 6) if hits else 0.0,
        "best": max(0, best_h),
        "best_tier": best_t,
        "ge3_best": int(best_h >= 3),
    }


def _run_range(lo: int, hi: int, *, write_db: bool, label: str) -> dict[str, Any]:
    from app.testlotto.brains.coordinator import (
        PREDICT_MODULES,
        _seed_independent_brain,
        dynamic_brain_quota,
        run_coordinated_prediction,
        _apply_aux_scoring,
    )
    from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN
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
    from app.testlotto.pool_view_cache import payload_from_wf_parts

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT draw_no FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (lo, hi),
        ).fetchall()
    finally:
        conn.close()

    learner = RollingSignalLearner()
    warm_from = max(1, lo - 80)
    wconn = get_lotto_db()
    try:
        warm_rows = wconn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
            "WHERE draw_no>=? AND draw_no<? ORDER BY draw_no",
            (warm_from, lo),
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
        learner.update_from_pool(_pool_by_brain(pool), {int(wrow[f"num{k}"]) for k in range(1, 7)})

    bugs: list[dict[str, Any]] = []
    ticket_best: list[int] = []
    ticket_mean: list[float] = []
    solo_best: dict[str, list[int]] = {t: [] for t in BRAINS}
    solo_mean: dict[str, list[float]] = {t: [] for t in BRAINS}
    pool_best: list[int] = []
    issued_ok = 0
    min_each_ok = 0
    peek_fail = 0
    errors: list[str] = []
    n_ok = 0
    t0 = time.perf_counter()

    for i, r in enumerate(rows):
        dno = int(r["draw_no"])
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        ok_peek, max_mat = _peek_ok(draws, dno)
        if not ok_peek:
            peek_fail += 1
            bugs.append({"draw": dno, "kind": "PEEK", "max_material": max_mat})
            continue
        aconn = get_lotto_db()
        try:
            act = _actual_row(aconn, dno)
        finally:
            aconn.close()
        if not act:
            errors.append(f"{dno}: no actual")
            continue
        actual, bonus = act

        # solo (memory)
        try:
            for tag in BRAINS:
                _seed_independent_brain(dno)
                sets = PREDICT_MODULES[tag].predict_sets(draws, SETS_PER_PREDICT_BRAIN)
                sc = _score_sets(sets, actual, bonus)
                solo_best[tag].append(sc["best"])
                solo_mean[tag].append(sc["mean"])
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{dno} solo: {type(exc).__name__}: {exc}")
            bugs.append({"draw": dno, "kind": "SOLO_EXC", "err": str(exc)})

        # joint ticket
        try:
            if write_db:
                out = run_coordinated_prediction(dno)
                if out.get("error"):
                    errors.append(f"{dno} ticket: {out['error']}")
                    bugs.append({"draw": dno, "kind": "TICKET_ERR", "err": out["error"]})
                    continue
                tconn = get_lotto_db()
                try:
                    preds = [
                        dict(x)
                        for x in tconn.execute(
                            "SELECT brain_tag,num1,num2,num3,num4,num5,num6 "
                            "FROM lotto_predictions WHERE target_draw_no=?",
                            (dno,),
                        ).fetchall()
                    ]
                finally:
                    tconn.close()
            else:
                cands = []
                for tag in BRAINS:
                    _seed_independent_brain(dno)
                    sets = PREDICT_MODULES[tag].predict_sets(draws, SETS_PER_PREDICT_BRAIN)
                    for j, s in enumerate(sets):
                        cands.append({**s, "brain_tag": tag, "set_no": j + 1, "pred_set_no": j + 1})
                scored = _apply_aux_scoring(cands, draws, dno)
                picked = dynamic_brain_quota(scored)
                preds = []
                for p in picked:
                    nums = [int(x) for x in p["nums"]]
                    preds.append(
                        {
                            "brain_tag": p.get("brain_tag"),
                            "num1": nums[0],
                            "num2": nums[1],
                            "num3": nums[2],
                            "num4": nums[3],
                            "num5": nums[4],
                            "num6": nums[5],
                        }
                    )
            n_iss = len(preds)
            by = Counter(str(p.get("brain_tag")) for p in preds)
            if n_iss == 5:
                issued_ok += 1
            else:
                bugs.append({"draw": dno, "kind": "ISSUED_NE_5", "n": n_iss, "by": dict(by)})
            if set(BRAINS) <= set(by) and all(by[t] >= 1 for t in BRAINS):
                min_each_ok += 1
            else:
                bugs.append({"draw": dno, "kind": "MIN_EACH", "by": dict(by)})
            tsets = [
                {
                    "nums": [
                        int(p["num1"]),
                        int(p["num2"]),
                        int(p["num3"]),
                        int(p["num4"]),
                        int(p["num5"]),
                        int(p["num6"]),
                    ]
                }
                for p in preds
            ]
            sc = _score_sets(tsets, actual, bonus)
            ticket_best.append(sc["best"])
            ticket_mean.append(sc["mean"])
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{dno} ticket: {type(exc).__name__}: {exc}")
            bugs.append({"draw": dno, "kind": "TICKET_EXC", "err": str(exc)})
            continue

        # pool
        try:
            random.seed(MC_SEED)
            pool = expand_pool(draws, dno, seed=MC_SEED)
            pool_br = _pool_by_brain(pool)
            n_pool = {t: len(pool_br.get(t) or []) for t in BRAINS}
            if any(v != 10 for v in n_pool.values()):
                bugs.append({"draw": dno, "kind": "POOL_NE_10", "sizes": n_pool})
            num_ema, pos_ema = learner.snapshot()
            repacked = repack_by_brain(
                pool_br,
                _build_hint(draws, dno),
                num_ema,
                pos_ema,
                target_draw_no=dno,
                hint_by_brain=build_hint_by_brain(draws, dno),
            )
            n_re = Counter(str(x.get("brain_tag")) for x in repacked)
            if any(n_re.get(t, 0) != 5 for t in BRAINS):
                bugs.append({"draw": dno, "kind": "REPACK_NE_5", "sizes": dict(n_re)})
            payload = payload_from_wf_parts(dno, pool_br, repacked, seed=MC_SEED)
            payload["tune_snapshot"] = tune_snapshot()
            if write_db:
                save_pool_view_cache(dno, payload)
            pall = []
            for t in BRAINS:
                pall.extend(payload.get("pool_by_brain", {}).get(t) or [])
                pall.extend(payload.get("repack_by_brain", {}).get(t) or [])
            scp = _score_sets(pall, actual, bonus)
            pool_best.append(scp["best"])
            learner.update_from_pool(pool_br, actual)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{dno} pool: {type(exc).__name__}: {exc}")
            bugs.append({"draw": dno, "kind": "POOL_EXC", "err": str(exc)})
            continue

        n_ok += 1
        if (i + 1) % 10 == 0 or dno == hi:
            print(
                f"  [{label}] {i+1}/{len(rows)} draw={dno} "
                f"ticket_best={ticket_best[-1] if ticket_best else '-'} "
                f"bugs={len(bugs)}",
                flush=True,
            )

    def _summ(bests: list[int], means: list[float] | None, eval_mode: str) -> dict[str, Any]:
        from tools.bench_quick_gate import enrich_metrics, null_for_eval_mode

        n = len(bests)
        g = sum(1 for x in bests if x >= 3)
        mm = mean(bests) if bests else 0.0
        nu = null_for_eval_mode(eval_mode)
        return {
            "n": n,
            "mean_best": round(mm, 4),
            "mean_all": round(mean(means), 4) if means else None,
            "ge3_count": g,
            "ge3_rate": round(g / n, 4) if n else 0.0,
            "eval_mode": eval_mode,
            "null_ge3": nu["null_ge3"],
            "null_mean": nu["null_mean"],
            "monitor_only": True,
            **{k: v for k, v in enrich_metrics(g, n, mm, eval_mode=eval_mode).items() if k in ("p_value",)},
        }

    elapsed = round(time.perf_counter() - t0, 1)
    kind_counts = Counter(b["kind"] for b in bugs)
    return {
        "label": label,
        "lo": lo,
        "hi": hi,
        "n_ok": n_ok,
        "n_target": hi - lo + 1,
        "elapsed_s": elapsed,
        "peek_fail": peek_fail,
        "issued_eq_5": issued_ok,
        "min_each_ok": min_each_ok,
        "ticket": _summ(ticket_best, ticket_mean, "best_of_5"),
        "solo": {t: _summ(solo_best[t], solo_mean[t], "best_of_5") for t in BRAINS},
        "pool_best_of_many": _summ(pool_best, None, "best_of_15"),
        "bug_kinds": dict(kind_counts),
        "bugs_head": bugs[:30],
        "n_bugs": len(bugs),
        "errors_head": errors[:20],
        "n_errors": len(errors),
    }


def _post_db_census() -> dict[str, Any]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        def n(sql: str, *a) -> int:
            return int(conn.execute(sql, a).fetchone()[0])

        return {
            "lotto_draws_max": n("SELECT MAX(draw_no) FROM lotto_draws"),
            "predictions": n("SELECT COUNT(*) FROM lotto_predictions"),
            "pred_draws": n("SELECT COUNT(DISTINCT target_draw_no) FROM lotto_predictions"),
            "pool_cache": n("SELECT COUNT(*) FROM testlotto_pool_view_cache"),
            "pool_draws": n("SELECT COUNT(DISTINCT draw_no) FROM testlotto_pool_view_cache"),
            "ledger": n("SELECT COUNT(*) FROM testlotto_pool_hit_ledger"),
            "homework": n("SELECT COUNT(*) FROM testlotto_skill_homework"),
            "review": n("SELECT COUNT(*) FROM testlotto_brain_review"),
            "pred_1237": n("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"),
        }
    finally:
        conn.close()


def main() -> int:
    from tools._k_predict_reset import survey as reset_survey

    phase = "all"
    if len(sys.argv) > 1:
        phase = sys.argv[1].strip().lower()

    rs = reset_survey()
    hw_in_delete = "testlotto_skill_homework" in rs["to_delete"]
    hw_unknown = "testlotto_skill_homework" in (rs.get("unknown_tables") or [])
    draws_max = rs["counts_before"].get("lotto_draws", 0)

    print("RESET_SURVEY homework_in_delete=", hw_in_delete, "unknown=", hw_unknown, flush=True)
    print("draws_max_from_counts is table rows; see census after", flush=True)

    smoke = None
    bt = None
    if phase in ("smoke", "all"):
        print("== SMOKE 1234-1236 (no DB write) ==", flush=True)
        smoke = _run_range(SMOKE_LO, SMOKE_HI, write_db=False, label="smoke")
        print(json.dumps({"smoke_n_ok": smoke["n_ok"], "bugs": smoke["bug_kinds"]}, ensure_ascii=False), flush=True)

    smoke_hard = False
    if smoke:
        smoke_hard = (
            smoke["n_ok"] == 3
            and smoke["peek_fail"] == 0
            and smoke["issued_eq_5"] == 3
            and smoke["min_each_ok"] == 3
            and smoke["n_errors"] == 0
            and smoke["bug_kinds"].get("POOL_NE_10", 0) == 0
            and smoke["bug_kinds"].get("REPACK_NE_5", 0) == 0
        )

    if phase == "all" and not smoke_hard:
        print("SMOKE FAIL — skip 200", flush=True)
    elif phase in ("bt200", "all") and (phase == "bt200" or smoke_hard):
        print("== BT200 1037-1236 (DB write) ==", flush=True)
        bt = _run_range(BT_LO, BT_HI, write_db=True, label="bt200")

    census = _post_db_census()
    improves: list[str] = []
    if not hw_in_delete:
        improves.append("리셋 목록에 skill_homework 누락이었음 → 도구에 추가 필요")
    if smoke and smoke["ticket"]["mean_best"] < smoke["ticket"]["null_mean"]:
        improves.append("발권5 mean_best가 best_of_5 null(1.73) 아래 · 모니터(서열금지)")
    if bt and bt["n_bugs"]:
        improves.append(f"200회 버그 {bt['n_bugs']}건 · kinds={bt['bug_kinds']}")
    if bt and bt["pool_best_of_many"]["ge3_rate"] and bt["ticket"]["ge3_rate"]:
        if bt["pool_best_of_many"]["ge3_rate"] > bt["ticket"]["ge3_rate"] + 0.05:
            improves.append("풀 경로 ge3가 발권보다 큼 · 장수효과 가능 · 발권실력로 쓰지 말 것")
    improves.append("L10~L11c HOLD 손잡이는 이번 200회로 자동 재스윕하지 않음")
    improves.append("클릭 L12b 동기 경로는 BT에 안 탐 · 화면 확인은 별도")

    hard_ok = bool(hw_in_delete) and (smoke_hard if smoke else True) and census["pred_1237"] == 0
    if bt:
        hard_ok = hard_ok and bt["peek_fail"] == 0 and bt["n_ok"] >= 190
    verdict = "PASS" if hard_ok else "FAIL"

    payload = {
        "id": "K-POST-L12B-RESET-BT200",
        "ts": _now(),
        "verdict": verdict,
        "phase": phase,
        "wire": False,
        "ge3_used_as_claim": False,
        "force_bt": True,
        "window_smoke": [SMOKE_LO, SMOKE_HI],
        "window_bt": [BT_LO, BT_HI],
        "reset_homework_in_delete": hw_in_delete,
        "reset_unknown": rs.get("unknown_tables"),
        "smoke": smoke,
        "smoke_hard": smoke_hard,
        "bt200": bt,
        "census": census,
        "improves": improves,
        "note": "1237아님 · draws보존 · ge3모니터 · 발권≠풀",
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-POST-L12B-RESET-BT200 — 리셋 후 스모크·200회",
        "",
        f"시각: {payload['ts']} · **{verdict}** · 1237아님 · ge3미클레임",
        "",
        "## 범위",
        "",
        "- DB: `data/lotto_testlotto.db` 만 · `lotto_draws` 보존",
        "- 스모크: 1234~1236 (DB 미기록)",
        "- 200회: 1037~1236 (발권+풀 기록)",
        "",
        f"- skill_homework 리셋포함: **{hw_in_delete}**",
        f"- smoke_hard: **{smoke_hard}**",
        f"- census: {census}",
        "",
    ]
    if smoke:
        lines += ["## 스모크", "", f"- n_ok={smoke['n_ok']} issued5={smoke['issued_eq_5']} min_each={smoke['min_each_ok']} peek_fail={smoke['peek_fail']}", f"- ticket {smoke['ticket']}", f"- solo {smoke['solo']}", f"- bugs {smoke['bug_kinds']}", ""]
    if bt:
        lines += ["## 200회 (모니터)", "", f"- n_ok={bt['n_ok']}/{bt['n_target']} elapsed={bt['elapsed_s']}s peek_fail={bt['peek_fail']}", f"- 발권5 ticket {bt['ticket']}", f"- 뇌별 solo {bt['solo']}", f"- 풀(장수많음·발권아님) {bt['pool_best_of_many']}", f"- bugs {bt['bug_kinds']}", ""]
    lines += ["## 버그·개선 (고치기 전 목록)", ""]
    for x in improves:
        lines.append(f"- {x}")
    if smoke and smoke["bugs_head"]:
        lines += ["", "### 스모크 버그 헤드", "", "```", json.dumps(smoke["bugs_head"], ensure_ascii=False, indent=2), "```"]
    if bt and bt["bugs_head"]:
        lines += ["", "### 200회 버그 헤드", "", "```", json.dumps(bt["bugs_head"], ensure_ascii=False, indent=2), "```"]
    lines += ["", f"벤치: `{OUT_JSON.relative_to(ROOT).as_posix()}`", "도구: `tools/_k_post_l12b_reset_bt200.py`", ""]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "smoke_hard": smoke_hard, "census": census}, ensure_ascii=False, indent=2), flush=True)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
