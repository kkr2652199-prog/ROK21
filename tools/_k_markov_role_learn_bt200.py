# -*- coding: utf-8 -*-
"""K-MARKOV-ROLE-LEARN-BT200 — 리셋 후 markov만 역할숙제 200회.

1~5 ON==OFF HARD. 6~8/9~10 ON vs 구경로.
walk: 예측 → 채점 → 원장+역할숙제 → 다음 소비.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KMARKOV_ROLE_LEARN_BT200.json"
OUT_MD = ROOT / "reports" / "20260814_KMARKOV_ROLE_LEARN_BT200.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SMOKE_LO, SMOKE_HI = 1234, 1236
BT_LO, BT_HI = 1037, 1236
SEED = 42
TAG = "markov"
ROLES = ("skill_native", "cover_r3", "shape_r2", "focus_r1")
LABEL = {1: "1등", 2: "2등", 3: "3등", 4: "4등", 5: "5등", 0: "미적중"}
NOTE = "markov_role_bt200"


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


def _expand(draws, dno: int, *, on: bool) -> tuple[list[dict], list[dict]]:
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


def _score_role(sets: list[dict], actual: set[int], bonus: int) -> dict[str, Any]:
    from app.testlotto.tier_utils import score_predicted_set

    hits: list[int] = []
    best = -1
    for s in sets:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) != 6:
            continue
        sc = score_predicted_set(nums, sorted(actual), bonus)
        h = int(sc["matched_count"])
        hits.append(h)
        best = max(best, h)
    return {
        "n": len(hits),
        "mean": round(mean(hits), 6) if hits else 0.0,
        "best": max(0, best),
    }


def _flags() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.role_homework import COVER_MIN_HITS

    return {
        "ROLE_TIER_LEARN_WIRE": bool(sp.ROLE_TIER_LEARN_WIRE),
        "ROLE_TIER_LEARN_BRAINS": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "COVER_MIN_HITS": int(COVER_MIN_HITS),
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
        f"{side}_{role}": {"means": [], "bests": []}
        for side in ("on", "off")
        for role in ROLES
    }
    skill_same = skill_diff = cover_diff = shape_diff = 0
    peek_fail = n_ok = size_bad = 0
    errors: list[str] = []
    hw_npos: list[int] = []
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
            pool_off, rep_off = _expand(draws, dno, on=False)
            pool_on, rep_on = _expand(draws, dno, on=True)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} expand {type(e).__name__}: {e}")
            continue
        if len(pool_on) != 10 or len(rep_on) != 5 or len(pool_off) != 10 or len(rep_off) != 5:
            size_bad += 1
            continue
        buckets = {"on": defaultdict(list), "off": defaultdict(list)}
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
                sc = _score_role(buckets[side][role], actual, bonus)
                acc[f"{side}_{role}"]["means"].append(sc["mean"])
                acc[f"{side}_{role}"]["bests"].append(sc["best"])
        for s in pool_on + rep_on:
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
        if write_db:
            try:
                payload = payload_from_wf_parts(dno, {TAG: pool_on}, rep_on, seed=MC_SEED)
                payload["tune_snapshot"] = tune_snapshot()
                save_pool_view_cache(dno, payload)
                wr = write_pool_hit_ledger(dno, note=NOTE, allow_compute=False)
                if not wr.get("ok"):
                    errors.append(f"{dno} ledger {wr}")
                hw = write_role_homework(dno, note=NOTE)
                npos = (
                    ((hw.get("brains") or {}).get(TAG) or {}).get("cover_r3") or {}
                ).get("n_pos", 0)
                hw_npos.append(int(npos or 0))
                if not hw.get("ok"):
                    errors.append(f"{dno} hw {hw}")
                write_skill_homework(dno, note=NOTE)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{dno} write {type(e).__name__}: {e}")
        n_ok += 1
        if (i + 1) % 20 == 0 or dno == hi:
            print(
                f"  [{label}] {i+1}/{len(rows)} d={dno} n_ok={n_ok} "
                f"skill_diff={skill_diff} cover_diff={cover_diff} shape_diff={shape_diff}",
                flush=True,
            )

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
    return {
        "label": label,
        "lo": lo,
        "hi": hi,
        "n_ok": n_ok,
        "n_target": hi - lo + 1,
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "n_errors": len(errors),
        "errors_head": errors[:12],
        "skill_1to5_same": skill_same,
        "skill_1to5_diff": skill_diff,
        "cover_nums_diff_draws": cover_diff,
        "shape_nums_diff_draws": shape_diff,
        "by_role": {k: _summ(v["means"], v["bests"]) for k, v in acc.items()},
        "hw_cover_npos_mean": round(mean(hw_npos), 3) if hw_npos else None,
        "hw_cover_npos_min": min(hw_npos) if hw_npos else None,
        "hw_cover_npos_max": max(hw_npos) if hw_npos else None,
        "unique_combo_tier": {LABEL[k]: int(uniq_c.get(k, 0)) for k in (1, 2, 3, 4, 5, 0)},
        "draw_best_tier": {LABEL[k]: int(best_c.get(k, 0)) for k in (1, 2, 3, 4, 5)},
        "draws_with_any_tier": sum(
            1 for v in draw_best_tier.values() if 1 <= (v if v != 99 else 0) <= 5
        ),
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
        }
    finally:
        conn.close()


def main() -> int:
    from tools._k_predict_reset import apply_reset, survey as reset_survey

    flags = _flags()
    print("FLAGS", json.dumps(flags, ensure_ascii=False), flush=True)
    if not (
        flags["ROLE_TIER_LEARN_WIRE"]
        and "markov" in flags["ROLE_TIER_LEARN_BRAINS"]
        and "stat" in flags["ROLE_TIER_LEARN_BRAINS"]
        and flags["COVER_MIN_HITS"] == 3
    ):
        print("FLAG FAIL — abort", flush=True)
        return 2

    rs = reset_survey()
    deleted = apply_reset(list(rs["to_delete"].keys()))
    print("RESET", {k: v for k, v in deleted.items() if v}, flush=True)

    print("== SMOKE ==", flush=True)
    smoke = _run_range(SMOKE_LO, SMOKE_HI, write_db=False, label="smoke")
    smoke_hard = (
        smoke["n_ok"] == 3
        and smoke["peek_fail"] == 0
        and smoke["size_bad"] == 0
        and smoke["n_errors"] == 0
        and smoke["skill_1to5_diff"] == 0
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
        and bt["size_bad"] == 0
        and bt["n_errors"] == 0
        and bt["skill_1to5_diff"] == 0
        and bt["skill_1to5_same"] == 200
        and census["pred_1237"] == 0
        and census["draws_max"] == 1236
    )
    out = {
        "id": "K-MARKOV-ROLE-LEARN-BT200",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "brain": TAG,
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
    print(json.dumps({
        "verdict": out["verdict"],
        "hard": hard,
        "census": census,
        "skill_same": (bt or {}).get("skill_1to5_same"),
        "cover_diff": (bt or {}).get("cover_nums_diff_draws"),
        "shape_diff": (bt or {}).get("shape_nums_diff_draws"),
        "hw_npos": (bt or {}).get("hw_cover_npos_mean"),
        "unique": (bt or {}).get("unique_combo_tier"),
    }, ensure_ascii=False, indent=2))
    return 0 if hard else 1


def _md(o: dict[str, Any]) -> str:
    bt = o.get("bt200") or {}
    br = bt.get("by_role") or {}
    u = bt.get("unique_combo_tier") or {}
    d = bt.get("draw_best_tier") or {}
    names = [
        ("on_skill_native", "ON 1~5"),
        ("off_skill_native", "OFF 1~5"),
        ("on_cover_r3", "ON 6~8"),
        ("off_cover_r3", "OFF 6~8"),
        ("on_shape_r2", "ON 9~10"),
        ("off_shape_r2", "OFF 9~10"),
        ("on_focus_r1", "ON 몰아주기"),
        ("off_focus_r1", "OFF 몰아주기"),
    ]
    lines = [
        "# K-MARKOV-ROLE-LEARN-BT200 — markov만 역할숙제 리셋+200회",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · ge3미클레임 · 1237아님",
        "창 1037~1236 · 뇌=markov만 · 1~5 ON==OFF HARD",
        "",
        "## 0) 한 줄",
        "",
        "예측을 지운 뒤 markov만 6~8/9~10 원장복습을 200회 돌렸다. "
        f"HARD={'통과' if o.get('hard_ok') else '실패'}. 1~5는 같아야 한다. 등수·평균은 모니터만.",
        "",
        "## 1) 플래그",
        "",
        f"`{json.dumps(o.get('flags') or {}, ensure_ascii=False)}`",
        "",
        "## 2) HARD",
        "",
        f"- n_ok={bt.get('n_ok')} · peek={bt.get('peek_fail')} · size_bad={bt.get('size_bad')} · err={bt.get('n_errors')}",
        f"- 1~5 동일 {bt.get('skill_1to5_same')} / 다름 {bt.get('skill_1to5_diff')}",
        f"- cover 번호 다른 회차 {bt.get('cover_nums_diff_draws')} · shape {bt.get('shape_nums_diff_draws')}",
        f"- cover 숙제 n_pos 평균 {bt.get('hw_cover_npos_mean')} (min {bt.get('hw_cover_npos_min')} max {bt.get('hw_cover_npos_max')})",
        "",
        "## 3) 칸별 모니터 (이론 1장 0.80 · 클레임금지)",
        "",
        "| 경로 | mean_all | mean_best | 회차최고≥3(모니터) |",
        "|------|----------|-----------|-------------------|",
    ]
    for k, lab in names:
        v = br.get(k) or {}
        lines.append(
            f"| {lab} | {v.get('mean_all')} | {v.get('mean_best')} | {v.get('ge3_best_count')} |"
        )
    lines += [
        "",
        "## 4) 등수 (고유조합 / 회차최고 · 모니터)",
        "",
        "| 등수 | 고유조합 | 회차최고 |",
        "|------|----------|----------|",
    ]
    for lab in ("1등", "2등", "3등", "4등", "5등"):
        lines.append(f"| {lab} | **{u.get(lab, 0)}** | {d.get(lab, 0)} |")
    lines += [
        f"| 등수 있는 회차 | — | {bt.get('draws_with_any_tier')} / 200 |",
        "",
        f"- census `{json.dumps(o.get('census') or {}, ensure_ascii=False)}`",
        "",
        "## 5) 금지",
        "",
        "- ge3/등수/mean으로 성적 향상 클레임 금지. 발권 0. DB 파일 커밋 금지.",
        "",
        "## 6) 다음",
        "",
        "형 1건. markov S1~S5 복사는 지시 시. 1237아님.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
