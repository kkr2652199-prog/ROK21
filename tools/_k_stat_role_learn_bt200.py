# -*- coding: utf-8 -*-
"""K-STAT-ROLE-LEARN-BT200 — 리셋 후 stat만 패치 엔진 200회.

1~5 불변 검증(ON==OFF). 6~8/9~10 ON vs Jaccard OFF.
walk-forward: 예측 → 채점 → 원장+역할숙제 기록 → 다음 회차 소비.
ge3/등수 = 모니터만. 1237아님. DB 파일 커밋 금지.
"""
from __future__ import annotations

import json
import os
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KSTAT_ROLE_LEARN_BT200.json"
OUT_MD = ROOT / "reports" / "20260814_KSTAT_ROLE_LEARN_BT200.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SMOKE_LO, SMOKE_HI = 1234, 1236
BT_LO, BT_HI = 1037, 1236
SEED = 42
TAG = "stat"
ROLES = ("skill_native", "cover_r3", "shape_r2", "focus_r1")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _actual_row(conn, dno: int) -> tuple[set[int], int] | None:
    row = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=?",
        (dno,),
    ).fetchone()
    if not row:
        return None
    return {int(row[f"num{k}"]) for k in range(1, 7)}, int(row["bonus"] or 0)


def _peek_ok(draws: list[dict], dno: int) -> tuple[bool, int]:
    max_mat = max((int(d["draw_no"]) for d in draws), default=0)
    return max_mat < dno, max_mat


def _role_of(s: dict) -> str:
    r = str(s.get("role") or "")
    if r:
        return r
    sn = int(s.get("set_no") or s.get("pred_set_no") or 0)
    if 1 <= sn <= 5:
        return "skill_native"
    if 6 <= sn <= 8:
        return "cover_r3"
    if 9 <= sn <= 10:
        return "shape_r2"
    return "focus_r1"


def _score_sets(sets: list[dict], actual: set[int], bonus: int) -> dict[str, Any]:
    from app.testlotto.tier_utils import score_predicted_set

    hits: list[int] = []
    best_h = -1
    ge3 = ge4 = ge5 = r3 = r2 = 0
    for s in sets:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) != 6:
            continue
        sc = score_predicted_set(nums, sorted(actual), bonus)
        h = int(sc["matched_count"])
        bm = int(sc.get("bonus_matched") or 0)
        hits.append(h)
        best_h = max(best_h, h)
        if h >= 3:
            ge3 += 1
        if h >= 4:
            ge4 += 1
        if h >= 5:
            ge5 += 1
        if h == 5 and bm:
            r2 += 1
        if h == 5 and not bm:
            r3 += 1
    return {
        "n": len(hits),
        "mean": round(mean(hits), 6) if hits else 0.0,
        "best": max(0, best_h),
        "ge3": ge3,
        "ge4": ge4,
        "ge5": ge5,
        "r3": r3,
        "r2": r2,
    }


def _expand_stat(draws, dno: int, *, on: bool) -> tuple[list[dict], list[dict]]:
    import app.testlotto.signal_pool as sp

    old = bool(sp.ROLE_TIER_LEARN_WIRE)
    sp.ROLE_TIER_LEARN_WIRE = bool(on)
    try:
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED, brains=[TAG])
        pool_br = sp._pool_by_brain(pool)
        learner = sp.RollingSignalLearner()
        num_ema, pos_ema = learner.snapshot()
        repacked = sp.repack_by_brain(
            pool_br,
            sp._build_hint(draws, dno),
            num_ema,
            pos_ema,
            target_draw_no=dno,
            hint_by_brain=sp.build_hint_by_brain(draws, dno),
        )
        return pool_br.get(TAG) or [], [x for x in repacked if str(x.get("brain_tag")) == TAG]
    finally:
        sp.ROLE_TIER_LEARN_WIRE = old


def _run_range(lo: int, hi: int, *, write_db: bool, label: str) -> dict[str, Any]:
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_hit_ledger import write_pool_hit_ledger
    from app.testlotto.pool_view_cache import payload_from_wf_parts, save_pool_view_cache
    from app.testlotto.role_homework import write_role_homework
    from app.testlotto.signal_pool import MC_SEED, tune_snapshot

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT draw_no FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (lo, hi),
        ).fetchall()
    finally:
        conn.close()

    acc: dict[str, dict[str, list]] = {
        f"{side}_{role}": {"means": [], "bests": []}
        for side in ("on", "off")
        for role in ROLES
    }
    skill_same = 0
    skill_diff = 0
    cover_diff = 0
    shape_diff = 0
    peek_fail = 0
    n_ok = 0
    errors: list[str] = []
    bugs: list[dict[str, Any]] = []
    hw_npos: list[int] = []
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

        try:
            pool_off, rep_off = _expand_stat(draws, dno, on=False)
            pool_on, rep_on = _expand_stat(draws, dno, on=True)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{dno} expand: {type(exc).__name__}: {exc}")
            bugs.append({"draw": dno, "kind": "EXPAND_EXC", "err": str(exc)})
            continue

        if len(pool_on) != 10 or len(rep_on) != 5:
            bugs.append(
                {
                    "draw": dno,
                    "kind": "SIZE",
                    "pool": len(pool_on),
                    "repack": len(rep_on),
                }
            )
        buckets = {
            "on": defaultdict(list),
            "off": defaultdict(list),
        }
        for s in pool_on:
            buckets["on"][_role_of(s)].append(s)
        for s in rep_on:
            buckets["on"]["focus_r1"].append(s)
        for s in pool_off:
            buckets["off"][_role_of(s)].append(s)
        for s in rep_off:
            buckets["off"]["focus_r1"].append(s)

        sk_on = {_key(s.get("nums")) for s in buckets["on"]["skill_native"]}
        sk_off = {_key(s.get("nums")) for s in buckets["off"]["skill_native"]}
        if sk_on == sk_off and len(sk_on) == 5:
            skill_same += 1
        else:
            skill_diff += 1
            bugs.append({"draw": dno, "kind": "SKILL_1TO5_DIFF"})

        if {_key(s.get("nums")) for s in buckets["on"]["cover_r3"]} != {
            _key(s.get("nums")) for s in buckets["off"]["cover_r3"]
        }:
            cover_diff += 1
        if {_key(s.get("nums")) for s in buckets["on"]["shape_r2"]} != {
            _key(s.get("nums")) for s in buckets["off"]["shape_r2"]
        }:
            shape_diff += 1

        for side in ("on", "off"):
            for role in ROLES:
                sc = _score_sets(buckets[side][role], actual, bonus)
                acc[f"{side}_{role}"]["means"].append(sc["mean"])
                acc[f"{side}_{role}"]["bests"].append(sc["best"])

        if write_db:
            try:
                pool_br = {TAG: pool_on}
                payload = payload_from_wf_parts(dno, pool_br, rep_on, seed=MC_SEED)
                payload["tune_snapshot"] = tune_snapshot()
                save_pool_view_cache(dno, payload)
                wr = write_pool_hit_ledger(dno, note="stat_role_bt200", allow_compute=False)
                if not wr.get("ok"):
                    bugs.append({"draw": dno, "kind": "LEDGER", "err": wr})
                hw = write_role_homework(dno, note="stat_role_bt200")
                npos = (
                    ((hw.get("brains") or {}).get(TAG) or {}).get("cover_r3") or {}
                ).get("n_pos", 0)
                hw_npos.append(int(npos or 0))
                if not hw.get("ok"):
                    bugs.append({"draw": dno, "kind": "HW", "err": hw})
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{dno} write: {type(exc).__name__}: {exc}")
                bugs.append({"draw": dno, "kind": "WRITE_EXC", "err": str(exc)})

        n_ok += 1
        if (i + 1) % 10 == 0 or dno == hi:
            print(
                f"  [{label}] {i+1}/{len(rows)} draw={dno} "
                f"skill_diff={skill_diff} cover_diff={cover_diff} "
                f"bugs={len(bugs)}",
                flush=True,
            )

    def _summ(means: list[float], bests: list[int]) -> dict[str, Any]:
        n = len(means)
        return {
            "n": n,
            "mean_all": round(mean(means), 4) if means else None,
            "mean_best": round(mean(bests), 4) if bests else None,
            "ge3_best_count": sum(1 for b in bests if b >= 3),
            "monitor_only": True,
        }

    by_role = {
        k: _summ(v["means"], v["bests"]) for k, v in acc.items()
    }
    elapsed = round(time.perf_counter() - t0, 1)
    return {
        "label": label,
        "lo": lo,
        "hi": hi,
        "n_ok": n_ok,
        "n_target": hi - lo + 1,
        "elapsed_s": elapsed,
        "peek_fail": peek_fail,
        "skill_1to5_same": skill_same,
        "skill_1to5_diff": skill_diff,
        "cover_nums_diff_draws": cover_diff,
        "shape_nums_diff_draws": shape_diff,
        "by_role": by_role,
        "hw_cover_npos_mean": round(mean(hw_npos), 3) if hw_npos else None,
        "hw_cover_npos_min": min(hw_npos) if hw_npos else None,
        "bug_kinds": dict(Counter(b["kind"] for b in bugs)),
        "bugs_head": bugs[:20],
        "n_bugs": len(bugs),
        "errors_head": errors[:15],
        "n_errors": len(errors),
    }


def _census() -> dict[str, Any]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        def n(sql: str, *a) -> int:
            return int(conn.execute(sql, a).fetchone()[0])

        return {
            "lotto_draws_max": n("SELECT MAX(draw_no) FROM lotto_draws"),
            "predictions": n("SELECT COUNT(*) FROM lotto_predictions"),
            "pool_cache": n("SELECT COUNT(*) FROM testlotto_pool_view_cache"),
            "ledger": n("SELECT COUNT(*) FROM testlotto_pool_hit_ledger"),
            "role_homework": n("SELECT COUNT(*) FROM testlotto_role_homework"),
            "skill_homework": n("SELECT COUNT(*) FROM testlotto_skill_homework"),
            "pred_1237": n("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"),
        }
    finally:
        conn.close()


def main() -> int:
    from tools._k_predict_reset import apply_reset, survey as reset_survey

    rs = reset_survey()
    targets = [t for t in rs["to_delete"] if rs["to_delete"][t] >= 0]
    print("RESET survey tables", list(rs["to_delete"].keys()), flush=True)
    print("role_hw in delete", "testlotto_role_homework" in rs["to_delete"], flush=True)
    deleted = apply_reset(list(rs["to_delete"].keys()))
    print("RESET deleted", deleted, flush=True)

    print("== SMOKE 1234-1236 ==", flush=True)
    smoke = _run_range(SMOKE_LO, SMOKE_HI, write_db=False, label="smoke")
    print(json.dumps({"smoke_n_ok": smoke["n_ok"], "bugs": smoke["bug_kinds"]}, ensure_ascii=False), flush=True)
    smoke_hard = (
        smoke["n_ok"] == 3
        and smoke["peek_fail"] == 0
        and smoke["skill_1to5_diff"] == 0
        and smoke["n_errors"] == 0
        and smoke["bug_kinds"].get("SIZE", 0) == 0
        and smoke["bug_kinds"].get("PEEK", 0) == 0
    )
    bt = None
    if not smoke_hard:
        print("SMOKE FAIL — skip 200", flush=True)
    else:
        print("== BT200 1037-1236 write cache/ledger/role_hw ==", flush=True)
        bt = _run_range(BT_LO, BT_HI, write_db=True, label="bt200")

    census = _census()
    hard = bool(smoke_hard and bt and bt["n_ok"] == 200 and bt["peek_fail"] == 0 and bt["skill_1to5_diff"] == 0 and bt["n_errors"] == 0)
    payload: dict[str, Any] = {
        "id": "K-STAT-ROLE-LEARN-BT200",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "brain": TAG,
        "reset_deleted": deleted,
        "smoke": smoke,
        "smoke_hard": smoke_hard,
        "bt200": bt,
        "census": census,
        "hard_ok": hard,
        "cover_min_hits": 3,
        "v1_sparse": "docs/benchmarks/20260814_KSTAT_ROLE_LEARN_BT200_v1_hitsge4.json",
        "baseline_src": "docs/benchmarks/20260813_KPOST_L12B_RESET_BT200.json",
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    br = (bt or {}).get("by_role") or {}
    md = f"""# K-STAT-ROLE-LEARN-BT200 — stat만 패치 엔진 200회

시각: {payload['as_of']} · **{'PASS' if hard else 'FAIL'}** · ge3미클레임 · 1237아님

## 0) 한 줄

리셋 후 **과거학습만** 6~8/9~10 원장복습 ON vs 구 Jaccard OFF. 1~5는 같아야 한다.

## 1) 리셋

`{json.dumps(deleted, ensure_ascii=False)}`

## 2) 스모크 1234~1236

hard={smoke_hard} n_ok={smoke['n_ok']} peek={smoke['peek_fail']} skill_diff={smoke['skill_1to5_diff']}

## 3) 200회 모니터 (성적 아님)

n_ok={None if not bt else bt['n_ok']} elapsed={None if not bt else bt.get('elapsed_s')}s
skill 1~5 동일 회차={None if not bt else bt.get('skill_1to5_same')} / 다름={None if not bt else bt.get('skill_1to5_diff')}
cover 번호 다른 회차={None if not bt else bt.get('cover_nums_diff_draws')}
shape 번호 다른 회차={None if not bt else bt.get('shape_nums_diff_draws')}
숙제 cover n_pos 평균={None if not bt else bt.get('hw_cover_npos_mean')}

| 경로 | mean_all | mean_best | ge3_best(모니터) |
|------|----------|-----------|------------------|
| ON skill | {(br.get('on_skill_native') or {}).get('mean_all')} | {(br.get('on_skill_native') or {}).get('mean_best')} | {(br.get('on_skill_native') or {}).get('ge3_best_count')} |
| OFF skill | {(br.get('off_skill_native') or {}).get('mean_all')} | {(br.get('off_skill_native') or {}).get('mean_best')} | {(br.get('off_skill_native') or {}).get('ge3_best_count')} |
| ON cover | {(br.get('on_cover_r3') or {}).get('mean_all')} | {(br.get('on_cover_r3') or {}).get('mean_best')} | {(br.get('on_cover_r3') or {}).get('ge3_best_count')} |
| OFF cover | {(br.get('off_cover_r3') or {}).get('mean_all')} | {(br.get('off_cover_r3') or {}).get('mean_best')} | {(br.get('off_cover_r3') or {}).get('ge3_best_count')} |
| ON shape | {(br.get('on_shape_r2') or {}).get('mean_all')} | {(br.get('on_shape_r2') or {}).get('mean_best')} | {(br.get('on_shape_r2') or {}).get('ge3_best_count')} |
| OFF shape | {(br.get('off_shape_r2') or {}).get('mean_all')} | {(br.get('off_shape_r2') or {}).get('mean_best')} | {(br.get('off_shape_r2') or {}).get('ge3_best_count')} |
| ON 몰아주기 | {(br.get('on_focus_r1') or {}).get('mean_all')} | {(br.get('on_focus_r1') or {}).get('mean_best')} | {(br.get('on_focus_r1') or {}).get('ge3_best_count')} |
| OFF 몰아주기 | {(br.get('off_focus_r1') or {}).get('mean_all')} | {(br.get('off_focus_r1') or {}).get('mean_best')} | {(br.get('off_focus_r1') or {}).get('ge3_best_count')} |

이전 3뇌 BT200 stat solo mean_all **0.828** (1~5 경로 · 비교 참고).

census: {json.dumps(census, ensure_ascii=False)}
bugs: {json.dumps((bt or smoke).get('bug_kinds'), ensure_ascii=False)}

## 4) 판정

hard_ok={hard}. 등수P 클레임 없음. DB 커밋 안 함.
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({"hard_ok": hard, "smoke_hard": smoke_hard, "census": census}, ensure_ascii=False, indent=2))
    return 0 if hard else 1


if __name__ == "__main__":
    raise SystemExit(main())
