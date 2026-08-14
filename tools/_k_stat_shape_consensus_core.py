# -*- coding: utf-8 -*-
"""K-STAT-SHAPE-CONSENSUS-CORE — S2 게이트.

stat shape 9~10: set1 1칸변형 vs 1~5 합의 core5.
1~5·cover 불변 HARD. 게이트=prefer/prize 비악화.
모니터=shape vs set1 Jaccard↓. T-NB1. 1237아님. DB쓰기 없음.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KSTAT_SHAPE_CONSENSUS_CORE.json"
OUT_MD = ROOT / "reports" / "20260814_KSTAT_SHAPE_CONSENSUS_CORE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SMOKE_LO, SMOKE_HI = 1234, 1236
GATE_LO, GATE_HI = 1137, 1236
SEED = 42
TAG = "stat"
ISO = 0.005


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _role(s: dict) -> str:
    return str(s.get("role") or "")


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _jaccard(a, b) -> float:
    sa, sb = set(a), set(b)
    u = sa | sb
    return (len(sa & sb) / len(u)) if u else 0.0


def _expand(draws, dno: int, *, mode: str) -> list[dict]:
    import app.testlotto.role_slots as rs
    import app.testlotto.signal_pool as sp

    old = rs.SHAPE_CORE_MODE
    rs.SHAPE_CORE_MODE = mode
    try:
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED, brains=[TAG])
        return sp._pool_by_brain(pool).get(TAG) or []
    finally:
        rs.SHAPE_CORE_MODE = old


def _geom(pool: list[dict]) -> dict[str, float]:
    by = {}
    for s in pool:
        sn = int(s.get("set_no") or 0)
        by[sn] = _nums(s)
    set1 = by.get(1) or []
    shape = [by[i] for i in (9, 10) if i in by]
    jacs = [_jaccard(sh, set1) for sh in shape if set1]
    return {"jac_shape_set1": float(mean(jacs)) if jacs else 0.0}


def _axis(table: dict[int, float], sets: list[dict]) -> float | None:
    if not table or not sets:
        return None
    uni = mean(table[i] for i in range(1, 46))
    vals = []
    for s in sets:
        nums = _nums(s)
        if len(nums) != 6:
            continue
        vals.append(mean(table[n] for n in nums) - uni)
    return round(mean(vals), 6) if vals else None


def _run(lo: int, hi: int, label: str) -> dict[str, Any]:
    from app.testlotto.brains.shared import crowd_signal as cs
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.role_slots import assert_shape_no_bonus_in_signature

    tnb = assert_shape_no_bonus_in_signature()
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT draw_no FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (lo, hi),
        ).fetchall()
    finally:
        conn.close()

    t0 = time.perf_counter()
    n_ok = peek_fail = size_bad = skill_same = cover_same = shape_diff = 0
    errors: list[str] = []
    src_on: dict[str, int] = {}
    g_off: list[dict] = []
    g_on: list[dict] = []
    pref_off: list[float] = []
    pref_on: list[float] = []
    prize_off: list[float] = []
    prize_on: list[float] = []

    for i, r in enumerate(rows):
        dno = int(r["draw_no"])
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        max_mat = max((int(d["draw_no"]) for d in draws), default=0)
        if max_mat >= dno:
            peek_fail += 1
            continue
        try:
            off = _expand(draws, dno, mode="set1")
            on = _expand(draws, dno, mode="consensus")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} {type(e).__name__}: {e}")
            continue
        if len(off) != 10 or len(on) != 10:
            size_bad += 1
            continue
        if [_key(_nums(s)) for s in off if _role(s) == "skill_native"] == [
            _key(_nums(s)) for s in on if _role(s) == "skill_native"
        ]:
            skill_same += 1
        if [_key(_nums(s)) for s in off if _role(s) == "cover_r3"] == [
            _key(_nums(s)) for s in on if _role(s) == "cover_r3"
        ]:
            cover_same += 1
        sh_off = [_key(_nums(s)) for s in off if _role(s) == "shape_r2"]
        sh_on = [_key(_nums(s)) for s in on if _role(s) == "shape_r2"]
        if sh_off != sh_on:
            shape_diff += 1
        for s in on:
            if _role(s) == "shape_r2":
                k = str(s.get("source") or "")
                src_on[k] = src_on.get(k, 0) + 1
        g_off.append(_geom(off))
        g_on.append(_geom(on))
        pref_t = cs.prefer_table(draws, brain="markov")
        prize_t = cs.prize_table(draws, brain="review")
        so = [s for s in off if _role(s) == "shape_r2"]
        sn = [s for s in on if _role(s) == "shape_r2"]
        po, pn = _axis(pref_t, so), _axis(pref_t, sn)
        zo, zn = _axis(prize_t, so), _axis(prize_t, sn)
        if po is not None:
            pref_off.append(po)
        if pn is not None:
            pref_on.append(pn)
        if zo is not None:
            prize_off.append(zo)
        if zn is not None:
            prize_on.append(zn)
        n_ok += 1
        if (i + 1) % 20 == 0 or dno == hi:
            print(f"  [{label}] {i+1}/{len(rows)} d={dno} n_ok={n_ok} shape_diff={shape_diff}", flush=True)

    def _m(xs: list[float]) -> float | None:
        return round(mean(xs), 6) if xs else None

    def _gm(key: str, rows: list[dict]) -> float | None:
        vs = [float(r[key]) for r in rows]
        return round(mean(vs), 4) if vs else None

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
        "errors_head": errors[:8],
        "tnb1_ok": bool(tnb.get("ok")),
        "skill_same": skill_same,
        "cover_same": cover_same,
        "shape_diff": shape_diff,
        "src_on": src_on,
        "jac_off": _gm("jac_shape_set1", g_off),
        "jac_on": _gm("jac_shape_set1", g_on),
        "prefer_off": _m(pref_off),
        "prefer_on": _m(pref_on),
        "prize_off": _m(prize_off),
        "prize_on": _m(prize_on),
    }


def main() -> int:
    import app.testlotto.role_slots as rs

    print("== SMOKE ==", flush=True)
    smoke = _run(SMOKE_LO, SMOKE_HI, "smoke")
    smoke_hard = (
        smoke["n_ok"] == 3
        and smoke["peek_fail"] == 0
        and smoke["size_bad"] == 0
        and smoke["n_errors"] == 0
        and smoke["skill_same"] == 3
        and smoke["cover_same"] == 3
        and smoke["tnb1_ok"]
    )
    print("smoke_hard", smoke_hard, "shape_diff", smoke["shape_diff"], flush=True)
    gate = None
    if smoke_hard:
        print("== GATE n100 ==", flush=True)
        gate = _run(GATE_LO, GATE_HI, "gate100")

    hard = bool(
        smoke_hard
        and gate
        and gate["n_ok"] == 100
        and gate["peek_fail"] == 0
        and gate["size_bad"] == 0
        and gate["n_errors"] == 0
        and gate["skill_same"] == 100
        and gate["cover_same"] == 100
        and gate["tnb1_ok"]
    )
    d_pref = d_prize = None
    prefer_not_worse = prize_not_worse = iso = design = False
    if gate and gate["prefer_off"] is not None and gate["prefer_on"] is not None:
        d_pref = round(gate["prefer_on"] - gate["prefer_off"], 6)
        d_prize = round(gate["prize_on"] - gate["prize_off"], 6)
        prefer_not_worse = d_pref < ISO
        prize_not_worse = d_prize < ISO
        iso = prefer_not_worse and prize_not_worse
        design = (gate["jac_on"] or 9) < (gate["jac_off"] or 9)
    wire_alive = bool(gate and gate["shape_diff"] > 0)
    apply = bool(hard and wire_alive and iso and design)
    if apply:
        verdict = "APPLY"
        rs.SHAPE_CORE_MODE = "consensus"
    elif hard and wire_alive and not iso:
        verdict = "HOLD_ISO_FAIL"
        rs.SHAPE_CORE_MODE = "set1"
    elif hard and not wire_alive:
        verdict = "DEAD_WIRE"
        rs.SHAPE_CORE_MODE = "set1"
    elif hard and wire_alive and iso and not design:
        verdict = "HOLD_NO_DESIGN"
        rs.SHAPE_CORE_MODE = "set1"
    else:
        verdict = "FAIL"
        rs.SHAPE_CORE_MODE = "set1"

    out = {
        "id": "K-STAT-SHAPE-CONSENSUS-CORE",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "iso_thr": ISO,
        "live_mode_after": rs.SHAPE_CORE_MODE,
        "smoke": smoke,
        "smoke_hard": smoke_hard,
        "gate100": gate,
        "hard_ok": hard,
        "wire_alive": wire_alive,
        "design_moved": design,
        "prefer_not_worse": prefer_not_worse,
        "prize_not_worse": prize_not_worse,
        "delta": {"prefer": d_pref, "prize": d_prize},
        "apply": apply,
        "verdict": verdict,
        "rollback": "SHAPE_CORE_MODE='set1'",
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "apply": apply,
        "hard": hard,
        "wire_alive": wire_alive,
        "iso": iso,
        "design": design,
        "delta": out["delta"],
        "live_mode_after": rs.SHAPE_CORE_MODE,
        "jac_off": (gate or {}).get("jac_off"),
        "jac_on": (gate or {}).get("jac_on"),
        "shape_diff": (gate or {}).get("shape_diff"),
        "src_on": (gate or {}).get("src_on"),
    }, ensure_ascii=False, indent=2))
    return 0 if hard else 1


def _md(o: dict[str, Any]) -> str:
    g = o.get("gate100") or {}
    d = o.get("delta") or {}
    return "\n".join([
        "# K-STAT-SHAPE-CONSENSUS-CORE — S2 stat shape 코어",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · APPLY={o.get('apply')} · ge3미클레임 · 1237아님",
        "창 게이트 1137~1236 n100 · 스모크 1234~1236 · 뇌=stat · 1~5·cover 불변 · T-NB1",
        "",
        "## 0) 한 줄",
        "",
        "9~10 shape 코어를 1번 세트 복제가 아니라 **1~5에서 2회 이상 나온 번호**로 잡았다. "
        f"HARD={'통과' if o.get('hard_ok') else '실패'} · 배선={('살아있음' if o.get('wire_alive') else '무반응')} · "
        f"비악화={o.get('prefer_not_worse') and o.get('prize_not_worse')} · 설계(J↓)={o.get('design_moved')}. "
        f"라이브 모드=`{o.get('live_mode_after')}` (롤백 `{o.get('rollback')}`).",
        "",
        "## 1) 게이트",
        "",
        "| 축 | OFF(set1) | ON(consensus) | Δ |",
        "|----|-----------|---------------|---|",
        f"| prefer (shape2) | {g.get('prefer_off')} | {g.get('prefer_on')} | {d.get('prefer')} |",
        f"| prize (shape2) | {g.get('prize_off')} | {g.get('prize_on')} | {d.get('prize')} |",
        f"| shape vs set1 Jaccard | {g.get('jac_off')} | {g.get('jac_on')} | 모니터 |",
        "",
        f"- skill동일 {g.get('skill_same')}/{g.get('n_ok')} · cover동일 {g.get('cover_same')} · shape변경 {g.get('shape_diff')}",
        f"- peek={g.get('peek_fail')} err={g.get('n_errors')} T-NB1={g.get('tnb1_ok')}",
        f"- ON source `{json.dumps(g.get('src_on') or {}, ensure_ascii=False)}`",
        "",
        "## 2) 판정",
        "",
        "- APPLY: HARD + shape변경>0 + prefer/prize 비악화 + Jaccard↓",
        "- 등수·적중 mean으로 성공 금지.",
        "",
        "## 3) 다음",
        "",
        "S3 몰아주기 역할쿼터 (APPLY일 때). 1237아님.",
        "",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
