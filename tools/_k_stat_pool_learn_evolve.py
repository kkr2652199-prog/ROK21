# -*- coding: utf-8 -*-
"""K-STAT-POOL-LEARN-EVOLVE — 리셋 후 stat 1~5 learn 미러 ON/OFF 200회.

문헌: 적중 mean 올리는 튜닝은 기각(초기하 0.80). 게이트=prize/prefer.
CUTOFF: brain_review(stat, skill 1~5 mean) → 다음 회차 apply_learn_boost.
동결: random.choices / _get_draws_before / boost 상한. 1237아님. ge3미클레임.
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KSTAT_POOL_LEARN_EVOLVE.json"
OUT_MD = ROOT / "reports" / "20260814_KSTAT_POOL_LEARN_EVOLVE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SMOKE_LO, SMOKE_HI = 1234, 1236
BT_LO, BT_HI = 1037, 1236
SEED = 42
TAG = "stat"
ISO = 0.005
PRIZE_THR = 0.005


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


def _skill(pool: list[dict]) -> list[dict]:
    out = []
    for s in pool:
        sn = int(s.get("set_no") or s.get("pred_set_no") or 0)
        role = str(s.get("role") or "")
        if role == "skill_native" or (not role and 1 <= sn <= 5):
            out.append(s)
    return out


def _axis(table: dict[int, float], sets: list[dict]) -> float | None:
    if not table or not sets:
        return None
    uni = mean(table[i] for i in range(1, 46))
    vals = []
    for s in sets:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) != 6:
            continue
        vals.append(mean(table[n] for n in nums) - uni)
    return round(mean(vals), 6) if vals else None


def _hits(sets: list[dict], actual: set[int]) -> tuple[float, int]:
    hs = []
    for s in sets:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) != 6:
            continue
        hs.append(len(set(nums) & actual))
    if not hs:
        return 0.0, 0
    return round(mean(hs), 6), max(hs)


def _expand_stat(draws, dno: int) -> list[dict]:
    import app.testlotto.signal_pool as sp

    random.seed(SEED)
    pool = sp.expand_pool(draws, dno, seed=SEED, brains=[TAG])
    return sp._pool_by_brain(pool).get(TAG) or []


def _run_walk(lo: int, hi: int, *, learn_on: bool, write_db: bool, label: str) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.shared import crowd_signal as cs
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.stat_pool_learn import STAT_POOL_LEARN_WIRE, write_stat_pool_learn

    saved = bool(STAT_POOL_LEARN_WIRE)
    import app.testlotto.stat_pool_learn as spl

    spl.STAT_POOL_LEARN_WIRE = bool(learn_on)
    init_testlotto_db()
    conn = get_lotto_db()
    t0 = time.perf_counter()
    n_ok = peek_fail = skill_n = 0
    prefer_s: list[float] = []
    prize_s: list[float] = []
    mean_s: list[float] = []
    best_s: list[int] = []
    keys: list[tuple] = []
    errors: list[str] = []
    n_learn_w = 0
    try:
        rows = list(
            conn.execute(
                "SELECT draw_no FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
                (lo, hi),
            )
        )
        for i, row in enumerate(rows):
            dno = int(row["draw_no"])
            act = _actual_row(conn, dno)
            if not act:
                errors.append(f"{dno} no actual")
                continue
            actual, bonus = act
            sp.set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            max_mat = max((int(d["draw_no"]) for d in draws), default=0)
            if max_mat >= dno:
                peek_fail += 1
                errors.append(f"PEEK {dno}")
                continue
            try:
                pool = _expand_stat(draws, dno)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{dno} expand {type(e).__name__}: {e}")
                continue
            skill = _skill(pool)
            if len(skill) != 5:
                errors.append(f"{dno} skill_n={len(skill)}")
                continue
            skill_n += 1
            keys.append(
                tuple(
                    _key(s.get("nums"))
                    for s in sorted(skill, key=lambda x: int(x.get("set_no") or 0))
                )
            )
            pref_t = cs.prefer_table(draws, brain="markov")
            prize_t = cs.prize_table(draws, brain="review")
            pv = _axis(pref_t, skill)
            zv = _axis(prize_t, skill)
            if pv is not None:
                prefer_s.append(pv)
            if zv is not None:
                prize_s.append(zv)
            m, b = _hits(skill, actual)
            mean_s.append(m)
            best_s.append(b)
            if learn_on:
                wr = write_stat_pool_learn(
                    dno, skill, actual, bonus, draws, note="stat_pool_learn_bt"
                )
                if wr.get("ok"):
                    n_learn_w += 1
                else:
                    errors.append(f"{dno} learn {wr}")
            if write_db:
                try:
                    from app.testlotto.pool_hit_ledger import write_pool_hit_ledger
                    from app.testlotto.pool_view_cache import (
                        payload_from_wf_parts,
                        save_pool_view_cache,
                    )
                    from app.testlotto.role_homework import write_role_homework
                    from app.testlotto.signal_pool import tune_snapshot
                    from app.testlotto.skill_homework import write_skill_homework

                    learner = sp.RollingSignalLearner()
                    num_ema, pos_ema = learner.snapshot()
                    hint = sp._build_hint(draws, dno)
                    repacked = sp.repack_by_brain(
                        {TAG: pool},
                        hint,
                        num_ema,
                        pos_ema,
                        target_draw_no=dno,
                        hint_by_brain=sp.build_hint_by_brain(draws, dno),
                    )
                    payload = payload_from_wf_parts(dno, {TAG: pool}, repacked, seed=SEED)
                    payload["tune_snapshot"] = tune_snapshot()
                    save_pool_view_cache(dno, payload)
                    write_pool_hit_ledger(dno, note="stat_pool_learn_bt", allow_compute=False)
                    write_role_homework(dno, note="stat_pool_learn_bt")
                    write_skill_homework(dno, note="stat_pool_learn_bt")
                except Exception as e:  # noqa: BLE001
                    errors.append(f"{dno} write {type(e).__name__}: {e}")
            n_ok += 1
            if (i + 1) % 20 == 0 or dno == hi:
                print(
                    f"  [{label}] {i+1}/{len(rows)} d={dno} n_ok={n_ok} learn_w={n_learn_w} err={len(errors)}",
                    flush=True,
                )
    finally:
        conn.close()
        spl.STAT_POOL_LEARN_WIRE = saved

    elapsed = round(time.perf_counter() - t0, 1)
    return {
        "label": label,
        "learn_on": bool(learn_on),
        "lo": lo,
        "hi": hi,
        "n_ok": n_ok,
        "n_target": hi - lo + 1,
        "elapsed_s": elapsed,
        "peek_fail": peek_fail,
        "skill5_ok": skill_n,
        "n_learn_write": n_learn_w,
        "n_errors": len(errors),
        "errors_head": errors[:12],
        "prefer_mean": round(mean(prefer_s), 6) if prefer_s else None,
        "prize_mean": round(mean(prize_s), 6) if prize_s else None,
        "hit_mean_all": round(mean(mean_s), 4) if mean_s else None,
        "hit_mean_best": round(mean(best_s), 4) if best_s else None,
        "ge3_best_count": sum(1 for x in best_s if x >= 3),
        "monitor_only": True,
        "skill_fingerprint": keys,
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
            "brain_review": n("SELECT COUNT(*) FROM testlotto_brain_review"),
            "review_stat": n("SELECT COUNT(*) FROM testlotto_brain_review WHERE brain_tag='stat'"),
            "learn_state": n("SELECT COUNT(*) FROM testlotto_brain_learn_state"),
            "skill_hw": n("SELECT COUNT(*) FROM testlotto_skill_homework"),
            "role_hw": n("SELECT COUNT(*) FROM testlotto_role_homework"),
            "ledger": n("SELECT COUNT(*) FROM testlotto_pool_hit_ledger"),
        }
    finally:
        conn.close()


def _boost_as_of(as_of: int) -> dict[str, Any]:
    from app.testlotto.learn_state_cutoff import rebuild_state_as_of

    st = rebuild_state_as_of("stat", as_of)
    adj = st.get("adjustments") or {}
    return {
        "review_count": st.get("review_count"),
        "last_draw_no": st.get("last_draw_no"),
        "recent_avg_match": st.get("recent_avg_match"),
        "adjustments": {k: float(adj.get(k, 0) or 0) for k in (
            "carry_over_boost", "ending_digit_boost", "overdue_boost"
        )},
        "miss_counts": st.get("miss_counts") or {},
    }


def main() -> int:
    from tools._k_predict_reset import apply_reset, survey as reset_survey

    rs = reset_survey()
    deleted = apply_reset(list(rs["to_delete"].keys()))
    print("RESET", deleted, flush=True)

    print("== SMOKE OFF ==", flush=True)
    smoke_off = _run_walk(SMOKE_LO, SMOKE_HI, learn_on=False, write_db=False, label="smoke_off")
    print("== SMOKE ON ==", flush=True)
    smoke_on = _run_walk(SMOKE_LO, SMOKE_HI, learn_on=True, write_db=False, label="smoke_on")
    smoke_hard = (
        smoke_off["n_ok"] == 3
        and smoke_on["n_ok"] == 3
        and smoke_off["peek_fail"] == 0
        and smoke_on["peek_fail"] == 0
        and smoke_off["n_errors"] == 0
        and smoke_on["n_errors"] == 0
    )
    print("smoke_hard", smoke_hard, flush=True)

    off = on = None
    if smoke_hard:
        from tools._k_predict_reset import apply_reset as ar

        print("== BT200 OFF (no learn write) ==", flush=True)
        ar(list(rs["to_delete"].keys()))
        off = _run_walk(BT_LO, BT_HI, learn_on=False, write_db=False, label="bt_off")
        print("== BT200 ON (review+cutoff) write DB ==", flush=True)
        ar(list(rs["to_delete"].keys()))
        on = _run_walk(BT_LO, BT_HI, learn_on=True, write_db=True, label="bt_on")

    census = _census()
    boost = _boost_as_of(1237) if on else {}
    fp_off = (off or {}).get("skill_fingerprint") or []
    fp_on = (on or {}).get("skill_fingerprint") or []
    n_cmp = min(len(fp_off), len(fp_on))
    skill_diff = sum(1 for i in range(n_cmp) if fp_off[i] != fp_on[i]) if n_cmp else 0

    d_pref = None
    d_prize = None
    if on and off and on.get("prefer_mean") is not None and off.get("prefer_mean") is not None:
        d_pref = round(on["prefer_mean"] - off["prefer_mean"], 6)
        d_prize = round(on["prize_mean"] - off["prize_mean"], 6)

    prize_ok = d_prize is not None and d_prize >= PRIZE_THR
    prefer_not_worse = d_pref is not None and d_pref <= ISO  # 인기↑는 EV에 불리 → 소량만 허용
    # prefer down (음수) is OK for EV. worse = large positive prefer delta
    wire_alive = skill_diff > 0
    hard = bool(
        smoke_hard
        and on
        and off
        and on["n_ok"] == 200
        and off["n_ok"] == 200
        and on["peek_fail"] == 0
        and off["peek_fail"] == 0
        and on["n_errors"] == 0
        and census["pred_1237"] == 0
    )
    if prize_ok and prefer_not_worse and wire_alive and hard:
        verdict = "APPLY"
    elif hard and wire_alive:
        verdict = "WIRE_OK_HOLD_KNOB"
    elif hard:
        verdict = "DEAD_WIRE"
    else:
        verdict = "FAIL"

    # APPLY only if prize gate. Else keep wire for record-fill if WIRE_OK_HOLD, or disable if DEAD.
    import app.testlotto.stat_pool_learn as spl

    if verdict == "APPLY":
        spl.STAT_POOL_LEARN_WIRE = True
        apply_flag = True
    elif verdict == "WIRE_OK_HOLD_KNOB":
        spl.STAT_POOL_LEARN_WIRE = True  # 기록 진화 유지 · 성적 클레임 금지
        apply_flag = True
    else:
        spl.STAT_POOL_LEARN_WIRE = False
        apply_flag = False

    out = {
        "id": "K-STAT-POOL-LEARN-EVOLVE",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "literature": {
            "hypergeometric_mean": 0.80,
            "hit_tune_rejected": True,
            "sources": [
                "Siegrist LibreTexts 13.7 hypergeometric E[U]=n*m/N → 6*6/45=0.80",
                "Clotfelter-Cook 1993 MS gambler fallacy lottery play",
                "Thaler-Ziemba 1988 JEP unpopular numbers EV not P(win)",
                "PINNED_TESTLOTTO_TUNING JackpotMath baseline",
            ],
        },
        "iso": ISO,
        "prize_thr": PRIZE_THR,
        "smoke_hard": smoke_hard,
        "smoke_off": {k: v for k, v in (smoke_off or {}).items() if k != "skill_fingerprint"},
        "smoke_on": {k: v for k, v in (smoke_on or {}).items() if k != "skill_fingerprint"},
        "bt_off": {k: v for k, v in (off or {}).items() if k != "skill_fingerprint"},
        "bt_on": {k: v for k, v in (on or {}).items() if k != "skill_fingerprint"},
        "skill_1to5_diff_draws": skill_diff,
        "n_compare": n_cmp,
        "delta": {"prefer": d_pref, "prize": d_prize, "hit_mean_all_monitor": (
            round(on["hit_mean_all"] - off["hit_mean_all"], 4)
            if on and off and on.get("hit_mean_all") is not None and off.get("hit_mean_all") is not None
            else None
        )},
        "boost_as_of_1237": boost,
        "census": census,
        "hard_ok": hard,
        "wire_alive": wire_alive,
        "prize_gate": prize_ok,
        "prefer_not_worse": prefer_not_worse,
        "STAT_POOL_LEARN_WIRE": bool(spl.STAT_POOL_LEARN_WIRE),
        "apply_flag": apply_flag,
        "verdict": verdict,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "diff": skill_diff, "delta": out["delta"], "hard": hard}, ensure_ascii=False, indent=2))
    return 0 if hard else 1


def _md(o: dict[str, Any]) -> str:
    on = o.get("bt_on") or {}
    off = o.get("bt_off") or {}
    d = o.get("delta") or {}
    return "\n".join([
        "# K-STAT-POOL-LEARN-EVOLVE — 과거학습 1~5 진화 배선",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · ge3미클레임 · 1237아님",
        "",
        "## 0) 한 줄",
        "",
        "논문·기존핀: **장당 적중 평균을 올리는 튜닝은 안 된다**(이론 0.80). "
        "이번엔 비어 있던 **1~5 학습 고리**(brain_review → CUTOFF → overdue/ending/carry)를 풀 확정 경로에 연결했다. "
        f"1~5 번호가 달라진 회차 **{o.get('skill_1to5_diff_draws')}**/200. "
        f"prize Δ={d.get('prize')} prefer Δ={d.get('prefer')} (게이트·모니터).",
        "",
        "## 1) 문헌 (배울 것 / 안 배울 것)",
        "",
        "- 초기하 E[맞힌개수]=6×6/45=**0.80**. 공정 추첨이면 과거로 이 값을 못 올린다.",
        "- Clotfelter–Cook 1993: 방금 나온 번호를 피하고 안 나온 번호를 쫓음 = **도박사의 오류**. 군중도 그렇게 한다.",
        "- Thaler–Ziemba 1988: 바꿀 수 있는 것은 **당첨금 분배(비인기 번호 EV)** 이지 P(당첨)이 아니다.",
        "- Wheeling/covering: 여러 장의 **최소 보장**이지 예측이 아니다.",
        "- 이미 HOLD: WIN_1Y · HINT_WEIGHT 0.15 · ASSOC OFF. 동결: boost 상한.",
        "",
        "## 2) 크로스체크 갭",
        "",
        "- skill_homework persist = 재계산과 동일 → 1~5를 바꾸지 않음.",
        "- 이번 200회는 발권 0 → brain_review 0 → learn boost 전부 0.",
        "- 어제 발권 경로 stat mean 0.828 은 learn이 쌓인 경로. 오늘은 그 고리가 꺼져 0.798.",
        "",
        "## 3) 배선",
        "",
        "`STAT_POOL_LEARN_WIRE` · `write_stat_pool_learn` · skill 1~5 **mean**(K-N) · as_of<target.",
        f"최종 플래그=**{o.get('STAT_POOL_LEARN_WIRE')}** · apply={o.get('apply_flag')}",
        "",
        "## 4) BT200 (1037~1236 · stat만)",
        "",
        "| | OFF | ON | Δ |",
        "|--|-----|----|---|",
        f"| n | {off.get('n_ok')} | {on.get('n_ok')} | |",
        f"| prefer (모니터·인기) | {off.get('prefer_mean')} | {on.get('prefer_mean')} | {d.get('prefer')} |",
        f"| prize (비인기 EV축) | {off.get('prize_mean')} | {on.get('prize_mean')} | {d.get('prize')} |",
        f"| hit mean_all (모니터) | {off.get('hit_mean_all')} | {on.get('hit_mean_all')} | {d.get('hit_mean_all_monitor')} |",
        f"| hit mean_best (모니터) | {off.get('hit_mean_best')} | {on.get('hit_mean_best')} | |",
        f"| peek | {off.get('peek_fail')} | {on.get('peek_fail')} | |",
        "",
        f"- 1~5 번호 다른 회차: **{o.get('skill_1to5_diff_draws')}**",
        f"- boost as_of<1237: `{json.dumps(o.get('boost_as_of_1237') or {}, ensure_ascii=False)}`",
        f"- census: `{json.dumps(o.get('census') or {}, ensure_ascii=False)}`",
        "",
        "## 5) 판정",
        "",
        f"- hard_ok={o.get('hard_ok')} · wire_alive={o.get('wire_alive')} · prize_gate={o.get('prize_gate')} · prefer_not_worse={o.get('prefer_not_worse')}",
        f"- verdict=**{o.get('verdict')}** · APPLY=prize≥+{o.get('prize_thr')} 이고 인기 폭증 아님.",
        "- ge3/등수 클레임 금지. 다음=형 1건(markov 또는 유지).",
        "",
    ]) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
