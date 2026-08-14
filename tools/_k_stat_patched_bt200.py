# -*- coding: utf-8 -*-
"""K-STAT-PATCHED-BT200 — 리셋 후 패치 엔진(stat만) 200회.

켜짐: ROLE_SLOTS · ROLE_TIER_LEARN(stat) · COVER_MIN_HITS=3 · STAT_POOL_LEARN.
walk: 예측 → 채점 → 원장+역할숙제+skill숙제+brain_review → 다음 소비.
ge3/등수=모니터. 1237아님. DB파일 커밋 금지.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KSTAT_PATCHED_BT200.json"
OUT_MD = ROOT / "reports" / "20260814_KSTAT_PATCHED_BT200.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SMOKE_LO, SMOKE_HI = 1234, 1236
BT_LO, BT_HI = 1037, 1236
SEED = 42
TAG = "stat"
ROLES = ("skill_native", "cover_r3", "shape_r2", "focus_r1")
LABEL = {1: "1등", 2: "2등", 3: "3등", 4: "4등", 5: "5등", 0: "미적중"}


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _actual_row(conn, dno: int) -> tuple[set[int], int] | None:
    row = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=?",
        (dno,),
    ).fetchone()
    if not row:
        return None
    return {int(row[f"num{k}"]) for k in range(1, 7)}, int(row["bonus"] or 0)


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


def _expand_stat(draws, dno: int) -> tuple[list[dict], list[dict]]:
    import app.testlotto.signal_pool as sp

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


def _score_role(sets: list[dict], actual: set[int], bonus: int) -> dict[str, Any]:
    from app.testlotto.tier_utils import score_predicted_set

    hits: list[int] = []
    best = -1
    tiers: list[int] = []
    for s in sets:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) != 6:
            continue
        sc = score_predicted_set(nums, sorted(actual), bonus)
        h = int(sc["matched_count"])
        hits.append(h)
        best = max(best, h)
        tiers.append(int(sc.get("tier_rank") or 0))
    return {
        "n": len(hits),
        "mean": round(mean(hits), 6) if hits else 0.0,
        "best": max(0, best),
        "ge3_best": int(best >= 3),
        "tiers": tiers,
        "sets": sets,
    }


def _run_range(lo: int, hi: int, *, write_db: bool, label: str) -> dict[str, Any]:
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_hit_ledger import write_pool_hit_ledger
    from app.testlotto.pool_view_cache import payload_from_wf_parts, save_pool_view_cache
    from app.testlotto.role_homework import write_role_homework
    from app.testlotto.signal_pool import MC_SEED, tune_snapshot
    from app.testlotto.skill_homework import write_skill_homework
    from app.testlotto.stat_pool_learn import write_stat_pool_learn
    from app.testlotto.tier_utils import score_predicted_set

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
        r: {"means": [], "bests": []} for r in ROLES
    }
    peek_fail = n_ok = size_bad = 0
    errors: list[str] = []
    uniq: dict[tuple, int] = {}
    draw_best_tier: dict[int, int] = {}
    t0 = time.perf_counter()

    for i, r in enumerate(rows):
        dno = int(r["draw_no"])
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        max_mat = max((int(d["draw_no"]) for d in draws), default=0)
        if max_mat >= dno:
            peek_fail += 1
            errors.append(f"PEEK {dno}")
            continue
        aconn = get_lotto_db()
        try:
            act = _actual_row(aconn, dno)
        finally:
            aconn.close()
        if not act:
            errors.append(f"{dno} no actual")
            continue
        actual, bonus = act
        try:
            pool, rep = _expand_stat(draws, dno)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} expand {type(e).__name__}: {e}")
            continue
        if len(pool) != 10 or len(rep) != 5:
            size_bad += 1
            errors.append(f"{dno} size p{len(pool)} r{len(rep)}")
            continue
        buckets: dict[str, list] = defaultdict(list)
        for s in pool:
            buckets[_role_of(s)].append(s)
        for s in rep:
            buckets["focus_r1"].append(s)
        for role in ROLES:
            sc = _score_role(buckets[role], actual, bonus)
            acc[role]["means"].append(sc["mean"])
            acc[role]["bests"].append(sc["best"])
        for s in pool + rep:
            nums = tuple(sorted(int(x) for x in (s.get("nums") or [])))
            tr = int(score_predicted_set(list(nums), sorted(actual), bonus).get("tier_rank") or 0)
            uk = (dno, nums)
            prev = uniq.get(uk, 99)
            if tr and (not prev or prev == 99 or tr < prev):
                uniq[uk] = tr
            elif uk not in uniq:
                uniq[uk] = tr
            cur = draw_best_tier.get(dno, 99)
            score = tr if tr else 99
            if score < cur:
                draw_best_tier[dno] = score
        skill = buckets["skill_native"]
        if write_db:
            try:
                payload = payload_from_wf_parts(dno, {TAG: pool}, rep, seed=MC_SEED)
                payload["tune_snapshot"] = tune_snapshot()
                save_pool_view_cache(dno, payload)
                wr = write_pool_hit_ledger(dno, note="stat_patched_bt200", allow_compute=False)
                if not wr.get("ok"):
                    errors.append(f"{dno} ledger {wr}")
                write_role_homework(dno, note="stat_patched_bt200")
                write_skill_homework(dno, note="stat_patched_bt200")
                write_stat_pool_learn(
                    dno, skill, actual, bonus, draws, note="stat_patched_bt200"
                )
            except Exception as e:  # noqa: BLE001
                errors.append(f"{dno} write {type(e).__name__}: {e}")
        n_ok += 1
        if (i + 1) % 20 == 0 or dno == hi:
            print(f"  [{label}] {i+1}/{len(rows)} d={dno} n_ok={n_ok} err={len(errors)}", flush=True)

    def _summ(means: list[float], bests: list[int]) -> dict[str, Any]:
        return {
            "n": len(means),
            "mean_all": round(mean(means), 4) if means else None,
            "mean_best": round(mean(bests), 4) if bests else None,
            "ge3_best_count": sum(1 for b in bests if b >= 3),
            "monitor_only": True,
        }

    uniq_c = Counter(v if v != 99 else 0 for v in uniq.values())
    best_c = Counter((v if v != 99 else 0) for v in draw_best_tier.values())
    n_draws = hi - lo + 1
    elapsed = round(time.perf_counter() - t0, 1)
    return {
        "label": label,
        "lo": lo,
        "hi": hi,
        "n_ok": n_ok,
        "n_target": n_draws,
        "elapsed_s": elapsed,
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "n_errors": len(errors),
        "errors_head": errors[:12],
        "by_role": {r: _summ(acc[r]["means"], acc[r]["bests"]) for r in ROLES},
        "unique_combo_tier": {LABEL[k]: int(uniq_c.get(k, 0)) for k in (1, 2, 3, 4, 5, 0)},
        "draw_best_tier": {
            LABEL[k]: int(best_c.get(k, 0)) for k in (1, 2, 3, 4, 5)
        },
        "draws_with_any_tier": sum(1 for v in draw_best_tier.values() if 1 <= (v if v != 99 else 0) <= 5),
        "monitor_only": True,
    }


def _census() -> dict[str, Any]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        def n(sql: str) -> int:
            return int(conn.execute(sql).fetchone()[0])

        return {
            "draws_max": n("SELECT MAX(draw_no) FROM lotto_draws"),
            "pred": n("SELECT COUNT(*) FROM lotto_predictions"),
            "pred_1237": n("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"),
            "cache": n("SELECT COUNT(*) FROM testlotto_pool_view_cache"),
            "ledger": n("SELECT COUNT(*) FROM testlotto_pool_hit_ledger"),
            "role_hw": n("SELECT COUNT(*) FROM testlotto_role_homework"),
            "skill_hw": n("SELECT COUNT(*) FROM testlotto_skill_homework"),
            "brain_review": n("SELECT COUNT(*) FROM testlotto_brain_review"),
            "review_stat": n("SELECT COUNT(*) FROM testlotto_brain_review WHERE brain_tag='stat'"),
        }
    finally:
        conn.close()


def _flags() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.role_homework import COVER_MIN_HITS
    from app.testlotto.stat_pool_learn import STAT_POOL_LEARN_WIRE

    return {
        "ROLE_SLOTS_WIRE": bool(sp.ROLE_SLOTS_WIRE),
        "ROLE_TIER_LEARN_WIRE": bool(sp.ROLE_TIER_LEARN_WIRE),
        "ROLE_TIER_LEARN_BRAINS": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "COVER_MIN_HITS": int(COVER_MIN_HITS),
        "STAT_POOL_LEARN_WIRE": bool(STAT_POOL_LEARN_WIRE),
    }


def main() -> int:
    from tools._k_predict_reset import apply_reset, survey as reset_survey

    flags = _flags()
    print("FLAGS", json.dumps(flags, ensure_ascii=False), flush=True)
    if not (
        flags["ROLE_SLOTS_WIRE"]
        and flags["ROLE_TIER_LEARN_WIRE"]
        and flags["ROLE_TIER_LEARN_BRAINS"] == ["stat"]
        and flags["COVER_MIN_HITS"] == 3
        and flags["STAT_POOL_LEARN_WIRE"]
    ):
        print("FLAG FAIL — abort", flush=True)
        return 2

    rs = reset_survey()
    deleted = apply_reset(list(rs["to_delete"].keys()))
    print("RESET", deleted, flush=True)

    print("== SMOKE ==", flush=True)
    smoke = _run_range(SMOKE_LO, SMOKE_HI, write_db=False, label="smoke")
    smoke_hard = (
        smoke["n_ok"] == 3 and smoke["peek_fail"] == 0 and smoke["n_errors"] == 0 and smoke["size_bad"] == 0
    )
    print("smoke_hard", smoke_hard, flush=True)
    bt = None
    if smoke_hard:
        print("== BT200 write ==", flush=True)
        bt = _run_range(BT_LO, BT_HI, write_db=True, label="bt200")

    census = _census()
    hard = bool(
        smoke_hard
        and bt
        and bt["n_ok"] == 200
        and bt["peek_fail"] == 0
        and bt["n_errors"] == 0
        and bt["size_bad"] == 0
        and census["pred_1237"] == 0
        and census["review_stat"] == 200
    )
    out = {
        "id": "K-STAT-PATCHED-BT200",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "flags": flags,
        "reset_deleted": deleted,
        "smoke": smoke,
        "smoke_hard": smoke_hard,
        "bt200": bt,
        "census": census,
        "hard_ok": hard,
        "verdict": "PASS" if hard else "FAIL",
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({"verdict": out["verdict"], "hard": hard, "census": census}, ensure_ascii=False, indent=2))
    return 0 if hard else 1


def _md(o: dict[str, Any]) -> str:
    bt = o.get("bt200") or {}
    br = bt.get("by_role") or {}
    u = bt.get("unique_combo_tier") or {}
    d = bt.get("draw_best_tier") or {}
    lines = [
        "# K-STAT-PATCHED-BT200 — 패치 엔진 stat만 리셋+200회",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · ge3미클레임 · 1237아님",
        "창 1037~1236 · 뇌=stat만 · 역할복습+1~5 CUTOFF 학습 켜짐",
        "",
        "## 0) 한 줄",
        "",
        "예측을 지운 뒤 지금 패치로 과거학습만 200회 돌렸다. "
        f"HARD={'통과' if o.get('hard_ok') else '실패'}. 등수·평균은 모니터만.",
        "",
        "## 1) 플래그",
        "",
        f"`{json.dumps(o.get('flags') or {}, ensure_ascii=False)}`",
        "",
        "## 2) 칸별 모니터 (이론 1장 0.80)",
        "",
        "| 칸 | mean_all | mean_best | 회차최고≥3(모니터) |",
        "|----|----------|-----------|-------------------|",
    ]
    names = {
        "skill_native": "1~5 실력",
        "cover_r3": "6~8 덮기",
        "shape_r2": "9~10 모양",
        "focus_r1": "몰아주기5",
    }
    for k, lab in names.items():
        v = br.get(k) or {}
        lines.append(
            f"| {lab} | {v.get('mean_all')} | {v.get('mean_best')} | {v.get('ge3_best_count')} |"
        )
    lines += [
        "",
        "## 3) 등수 (고유조합 / 회차최고)",
        "",
        "| 등수 | 고유조합 | 회차최고 |",
        "|------|----------|----------|",
    ]
    for lab in ("1등", "2등", "3등", "4등", "5등"):
        lines.append(f"| {lab} | **{u.get(lab, 0)}** | {d.get(lab, 0)} |")
    lines += [
        f"| 등수 있는 회차 | — | {bt.get('draws_with_any_tier')} / 200 |",
        "",
        f"- peek={bt.get('peek_fail')} · err={bt.get('n_errors')} · size_bad={bt.get('size_bad')} · n_ok={bt.get('n_ok')}",
        f"- census `{json.dumps(o.get('census') or {}, ensure_ascii=False)}`",
        "",
        "## 4) 금지",
        "",
        "- ge3/등수로 성적 향상 클레임 금지. 발권 0.",
        "",
        "## 5) 다음",
        "",
        "형 1건(권고=markov 동일 소비). 1237아님.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
