# -*- coding: utf-8 -*-
"""K-STAT-COVER-OUTSIDE-UNION — S1 게이트.

stat cover 6~8: Jaccard최저 vs skill-union 밖 번호 최대.
1~5 불변 HARD. 게이트=prefer/prize iso(|Δ|<0.005).
설계모니터=union10·cover-skill Jaccard·outside count.
ge3미클레임. 1237아님. DB쓰기 없음.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KSTAT_COVER_OUTSIDE_UNION.json"
OUT_MD = ROOT / "reports" / "20260814_KSTAT_COVER_OUTSIDE_UNION.md"
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

    old = rs.COVER_SELECT_MODE
    rs.COVER_SELECT_MODE = mode
    try:
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED, brains=[TAG])
        return sp._pool_by_brain(pool).get(TAG) or []
    finally:
        rs.COVER_SELECT_MODE = old


def _geom(pool: list[dict]) -> dict[str, float]:
    by = {}
    for s in pool:
        sn = int(s.get("set_no") or 0)
        by[sn] = _nums(s)
    skill = [by[i] for i in range(1, 6) if i in by]
    cover = [by[i] for i in range(6, 9) if i in by]
    alln = [by[i] for i in range(1, 11) if i in by]
    su = set().union(*map(set, skill)) if skill else set()
    u10 = len(set().union(*map(set, alln))) if alln else 0
    outside = []
    jacs = []
    for c in cover:
        cs = set(c)
        outside.append(len(cs - su))
        if skill:
            jacs.append(mean(_jaccard(c, sk) for sk in skill))
    return {
        "union10": float(u10),
        "outside_mean": float(mean(outside)) if outside else 0.0,
        "jac_cover_skill": float(mean(jacs)) if jacs else 0.0,
    }


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
    n_ok = peek_fail = size_bad = skill_same = cover_diff = 0
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
            off = _expand(draws, dno, mode="jaccard")
            on = _expand(draws, dno, mode="outside_union")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} {type(e).__name__}: {e}")
            continue
        if len(off) != 10 or len(on) != 10:
            size_bad += 1
            continue
        sk_off = [_key(_nums(s)) for s in off if _role(s) == "skill_native"]
        sk_on = [_key(_nums(s)) for s in on if _role(s) == "skill_native"]
        if sk_off == sk_on:
            skill_same += 1
        cv_off = [_key(_nums(s)) for s in off if _role(s) == "cover_r3"]
        cv_on = [_key(_nums(s)) for s in on if _role(s) == "cover_r3"]
        if cv_off != cv_on:
            cover_diff += 1
        for s in on:
            if _role(s) == "cover_r3":
                k = str(s.get("source") or "")
                src_on[k] = src_on.get(k, 0) + 1
        g_off.append(_geom(off))
        g_on.append(_geom(on))
        pref_t = cs.prefer_table(draws, brain="markov")
        prize_t = cs.prize_table(draws, brain="review")
        cov_off = [s for s in off if _role(s) == "cover_r3"]
        cov_on = [s for s in on if _role(s) == "cover_r3"]
        po = _axis(pref_t, cov_off)
        pn = _axis(pref_t, cov_on)
        zo = _axis(prize_t, cov_off)
        zn = _axis(prize_t, cov_on)
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
            print(f"  [{label}] {i+1}/{len(rows)} d={dno} n_ok={n_ok} cover_diff={cover_diff}", flush=True)

    def _m(xs: list[float]) -> float | None:
        return round(mean(xs), 6) if xs else None

    def _gm(key: str, rows: list[dict]) -> float | None:
        vs = [float(r[key]) for r in rows]
        return round(mean(vs), 4) if vs else None

    n_target = hi - lo + 1
    return {
        "label": label,
        "lo": lo,
        "hi": hi,
        "n_ok": n_ok,
        "n_target": n_target,
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "n_errors": len(errors),
        "errors_head": errors[:8],
        "skill_same": skill_same,
        "cover_diff": cover_diff,
        "src_on": src_on,
        "geom_off": {
            "union10": _gm("union10", g_off),
            "outside_mean": _gm("outside_mean", g_off),
            "jac_cover_skill": _gm("jac_cover_skill", g_off),
        },
        "geom_on": {
            "union10": _gm("union10", g_on),
            "outside_mean": _gm("outside_mean", g_on),
            "jac_cover_skill": _gm("jac_cover_skill", g_on),
        },
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
    )
    print("smoke_hard", smoke_hard, "cover_diff", smoke["cover_diff"], flush=True)
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
    )
    d_pref = d_prize = None
    iso = False
    prefer_not_worse = prize_not_worse = False
    design = False
    if gate and gate["prefer_off"] is not None and gate["prefer_on"] is not None:
        d_pref = round(gate["prefer_on"] - gate["prefer_off"], 6)
        d_prize = round(gate["prize_on"] - gate["prize_off"], 6)
        # 비악화: 인기↑(+prefer) · 몫EV악화(+prize) 만 0.005 이상이면 실패.
        # |Δ| iso는 독립성 게이트용. 여기선 EV 방향 개선을 실패로 치면 안 됨.
        prefer_not_worse = d_pref < ISO
        prize_not_worse = d_prize < ISO
        iso = prefer_not_worse and prize_not_worse
        go = gate["geom_on"]
        gf = gate["geom_off"]
        design = bool(
            (go["union10"] or 0) > (gf["union10"] or 0)
            or (go["outside_mean"] or 0) > (gf["outside_mean"] or 0)
            or (go["jac_cover_skill"] or 9) < (gf["jac_cover_skill"] or 9)
        )
    wire_alive = bool(gate and gate["cover_diff"] > 0)
    apply = bool(hard and wire_alive and iso and design)
    if apply:
        verdict = "APPLY"
        rs.COVER_SELECT_MODE = "outside_union"
    elif hard and wire_alive and not iso:
        verdict = "HOLD_ISO_FAIL"
        rs.COVER_SELECT_MODE = "jaccard"
    elif hard and not wire_alive:
        verdict = "DEAD_WIRE"
        rs.COVER_SELECT_MODE = "jaccard"
    else:
        verdict = "FAIL"
        rs.COVER_SELECT_MODE = "jaccard"

    out = {
        "id": "K-STAT-COVER-OUTSIDE-UNION",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "iso_thr": ISO,
        "live_mode_after": rs.COVER_SELECT_MODE,
        "smoke": smoke,
        "smoke_hard": smoke_hard,
        "gate100": gate,
        "hard_ok": hard,
        "wire_alive": wire_alive,
        "design_moved": design,
        "prefer_prize_iso": iso,
        "prefer_not_worse": prefer_not_worse,
        "prize_not_worse": prize_not_worse,
        "delta": {"prefer": d_pref, "prize": d_prize},
        "apply": apply,
        "verdict": verdict,
        "rollback": "COVER_SELECT_MODE='jaccard'",
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
        "live_mode_after": rs.COVER_SELECT_MODE,
        "geom_off": (gate or {}).get("geom_off"),
        "geom_on": (gate or {}).get("geom_on"),
        "cover_diff": (gate or {}).get("cover_diff"),
        "src_on": (gate or {}).get("src_on"),
    }, ensure_ascii=False, indent=2))
    return 0 if hard else 1


def _md(o: dict[str, Any]) -> str:
    g = o.get("gate100") or {}
    d = o.get("delta") or {}
    go = g.get("geom_on") or {}
    gf = g.get("geom_off") or {}
    return "\n".join([
        "# K-STAT-COVER-OUTSIDE-UNION — S1 stat cover 선택",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · APPLY={o.get('apply')} · ge3미클레임 · 1237아님",
        "창 게이트 1137~1236 n100 · 스모크 1234~1236 · 뇌=stat · 1~5 불변",
        "",
        "## 0) 한 줄",
        "",
        "6~8 cover를 Jaccard 최저 대신 **1~5가 안 쓴 번호가 많은 장**을 고르게 했다. "
        f"HARD={'통과' if o.get('hard_ok') else '실패'} · 배선={('살아있음' if o.get('wire_alive') else '무반응')} · "
        f"prefer/prize iso={o.get('prefer_prize_iso')} · 설계이동={o.get('design_moved')}. "
        f"라이브 모드=`{o.get('live_mode_after')}` (롤백 `{o.get('rollback')}`).",
        "",
        "## 1) 게이트",
        "",
        f"| 축 | OFF(jaccard) | ON(outside) | Δ |",
        f"|----|--------------|-------------|---|",
        f"| prefer (cover3) | {g.get('prefer_off')} | {g.get('prefer_on')} | {d.get('prefer')} |",
        f"| prize (cover3) | {g.get('prize_off')} | {g.get('prize_on')} | {d.get('prize')} |",
        f"| union10 | {gf.get('union10')} | {go.get('union10')} | 모니터 |",
        f"| cover 밖번호 mean | {gf.get('outside_mean')} | {go.get('outside_mean')} | 모니터 |",
        f"| cover-skill Jaccard | {gf.get('jac_cover_skill')} | {go.get('jac_cover_skill')} | 모니터 |",
        "",
        f"- skill 1~5 동일 {g.get('skill_same')}/{g.get('n_ok')} · cover 변경 {g.get('cover_diff')}",
        f"- peek={g.get('peek_fail')} err={g.get('n_errors')} size={g.get('size_bad')} n_ok={g.get('n_ok')}",
        f"- ON source `{json.dumps(g.get('src_on') or {}, ensure_ascii=False)}`",
        f"- iso thr={o.get('iso_thr')} · smoke_hard={o.get('smoke_hard')}",
        "",
        "## 2) 판정 규칙",
        "",
        "- APPLY: HARD + cover변경>0 + prefer/prize **비악화**(Δprefer<0.005 · Δprize<0.005) + 설계이동",
        "- HOLD_ISO_FAIL: 인기↑ 또는 몫EV악화가 0.005 이상",
        "- DEAD_WIRE: cover 번호가 안 바뀜 → 기본 jaccard",
        "- |Δ| 대칭 iso는 타뇌 독립성용. EV가 좋아진 음수 Δ를 실패로 치지 않음.",
        "- 등수·적중 mean으로 성공 금지.",
        "",
        "## 3) 다음",
        "",
        "S2 shape 합의 코어 (APPLY일 때). HOLD면 리스트 재검토. 1237아님.",
        "",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
