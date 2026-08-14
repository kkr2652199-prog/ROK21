# -*- coding: utf-8 -*-
"""K-STAT-REPACK-MIX-RECOMBINE — S4 게이트.

stat 몰아주기 5번째 장: 복사4 번호합을 빼고 남은 고점수 6개.
pool 1~10·복사4 HARD 불변. 게이트=prefer/prize 비악화.
모니터=재조합 vs 복사4 Jaccard · union_repack.
1237아님. DB쓰기 없음.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KSTAT_REPACK_MIX_RECOMBINE.json"
OUT_MD = ROOT / "reports" / "20260814_KSTAT_REPACK_MIX_RECOMBINE.md"
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


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _split(rep: list[dict]) -> tuple[list[dict], list[dict]]:
    copied = [s for s in rep if str(s.get("source") or "") == "pool"]
    rec = [s for s in rep if str(s.get("source") or "") != "pool"]
    return copied, rec


def _expand(draws, dno: int, *, mode: str) -> tuple[list[dict], list[dict]]:
    import app.testlotto.signal_pool as sp

    old = str(sp.REPACK_RECOMBINE_MODE)
    sp.REPACK_RECOMBINE_MODE = str(mode)
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
        p = pool_br.get(TAG) or []
        r = [x for x in repacked if str(x.get("brain_tag")) == TAG]
        return p, r
    finally:
        sp.REPACK_RECOMBINE_MODE = old


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


def _geom(rep: list[dict]) -> tuple[float, int, int]:
    copied, rec = _split(rep)
    cu: set[int] = set()
    for s in copied:
        cu.update(_nums(s))
    rec_u: set[int] = set()
    for s in rec:
        rec_u.update(_nums(s))
    all_u: set[int] = set()
    for s in rep:
        all_u.update(_nums(s))
    return _jaccard(rec_u, cu), len(all_u), len(rec_u & cu)


def _self_check() -> dict[str, Any]:
    from app.testlotto.signal_pool import recombine_complement_ticket

    scores = {n: float(46 - n) for n in range(1, 46)}
    copied = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12],
              [13, 14, 15, 16, 17, 18], [19, 20, 21, 22, 23, 24]]
    got = recombine_complement_ticket(scores, copied)
    ok = got == [25, 26, 27, 28, 29, 30]
    tiny = recombine_complement_ticket(scores, [list(range(1, 41))])
    fb_ok = tiny == [1, 2, 3, 4, 5, 6]
    return {"ok": bool(ok and fb_ok), "complement": got, "fallback": tiny}


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
    n_ok = peek_fail = size_bad = pool_same = copies_same = rec_diff = 0
    errors: list[str] = []
    j_off: list[float] = []
    j_on: list[float] = []
    u_off: list[int] = []
    u_on: list[int] = []
    inter_on: list[int] = []
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
            p_off, r_off = _expand(draws, dno, mode="top6")
            p_on, r_on = _expand(draws, dno, mode="complement")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} {type(e).__name__}: {e}")
            continue
        if len(p_off) != 10 or len(p_on) != 10 or len(r_off) != 5 or len(r_on) != 5:
            size_bad += 1
            continue
        if [_key(_nums(s)) for s in p_off] == [_key(_nums(s)) for s in p_on]:
            pool_same += 1
        c_off, rec_off = _split(r_off)
        c_on, rec_on = _split(r_on)
        if [_key(_nums(s)) for s in c_off] == [_key(_nums(s)) for s in c_on]:
            copies_same += 1
        if [_key(_nums(s)) for s in rec_off] != [_key(_nums(s)) for s in rec_on]:
            rec_diff += 1
        jo, uo, _ = _geom(r_off)
        jn, un, ion = _geom(r_on)
        j_off.append(jo)
        j_on.append(jn)
        u_off.append(uo)
        u_on.append(un)
        inter_on.append(ion)
        pref_t = cs.prefer_table(draws, brain="markov")
        prize_t = cs.prize_table(draws, brain="review")
        po, pn = _axis(pref_t, r_off), _axis(pref_t, r_on)
        zo, zn = _axis(prize_t, r_off), _axis(prize_t, r_on)
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
            print(
                f"  [{label}] {i+1}/{len(rows)} d={dno} n_ok={n_ok} rec_diff={rec_diff}",
                flush=True,
            )

    def _m(xs: list[float]) -> float | None:
        return round(mean(xs), 6) if xs else None

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
        "pool_same": pool_same,
        "copies_same": copies_same,
        "recombine_diff": rec_diff,
        "jaccard_off": _m(j_off),
        "jaccard_on": _m(j_on),
        "union_repack_off": _m(u_off),
        "union_repack_on": _m(u_on),
        "inter_on_mean": _m(inter_on),
        "prefer_off": _m(pref_off),
        "prefer_on": _m(pref_on),
        "prize_off": _m(prize_off),
        "prize_on": _m(prize_on),
    }


def main() -> int:
    import app.testlotto.signal_pool as sp

    selfc = _self_check()
    print("self_check", selfc, flush=True)
    print("== SMOKE ==", flush=True)
    smoke = _run(SMOKE_LO, SMOKE_HI, "smoke")
    smoke_hard = (
        selfc["ok"]
        and smoke["n_ok"] == 3
        and smoke["peek_fail"] == 0
        and smoke["size_bad"] == 0
        and smoke["n_errors"] == 0
        and smoke["pool_same"] == 3
        and smoke["copies_same"] == 3
    )
    print("smoke_hard", smoke_hard, "rec_diff", smoke["recombine_diff"], flush=True)
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
        and gate["pool_same"] == 100
        and gate["copies_same"] == 100
    )
    d_pref = d_prize = None
    prefer_not_worse = prize_not_worse = iso = design = False
    if gate and gate["prefer_off"] is not None and gate["prefer_on"] is not None:
        d_pref = round(gate["prefer_on"] - gate["prefer_off"], 6)
        d_prize = round(gate["prize_on"] - gate["prize_off"], 6)
        prefer_not_worse = d_pref < ISO
        prize_not_worse = d_prize < ISO
        iso = prefer_not_worse and prize_not_worse
        j_off = gate.get("jaccard_off") or 0.0
        j_on = gate.get("jaccard_on") or 0.0
        u_off = gate.get("union_repack_off") or 0.0
        u_on = gate.get("union_repack_on") or 0.0
        design = bool(j_on < j_off or u_on > u_off)
    wire_alive = bool(gate and gate["recombine_diff"] > 0)
    apply = bool(hard and wire_alive and iso and design)
    if apply:
        verdict = "APPLY"
        sp.REPACK_RECOMBINE_MODE = "complement"
    elif hard and wire_alive and not iso:
        verdict = "HOLD_ISO_FAIL"
        sp.REPACK_RECOMBINE_MODE = "top6"
    elif hard and not wire_alive:
        verdict = "DEAD_WIRE"
        sp.REPACK_RECOMBINE_MODE = "top6"
    elif hard and wire_alive and iso and not design:
        verdict = "HOLD_NO_DESIGN"
        sp.REPACK_RECOMBINE_MODE = "top6"
    else:
        verdict = "FAIL"
        sp.REPACK_RECOMBINE_MODE = "top6"

    out = {
        "id": "K-STAT-REPACK-MIX-RECOMBINE",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "iso_thr": ISO,
        "self_check": selfc,
        "live_mode_after": str(sp.REPACK_RECOMBINE_MODE),
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
        "rollback": 'REPACK_RECOMBINE_MODE="top6"',
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
        "live_mode_after": str(sp.REPACK_RECOMBINE_MODE),
        "jaccard": {"off": (gate or {}).get("jaccard_off"), "on": (gate or {}).get("jaccard_on")},
        "union_repack": {
            "off": (gate or {}).get("union_repack_off"),
            "on": (gate or {}).get("union_repack_on"),
        },
        "inter_on_mean": (gate or {}).get("inter_on_mean"),
        "recombine_diff": (gate or {}).get("recombine_diff"),
        "copies_same": (gate or {}).get("copies_same"),
    }, ensure_ascii=False, indent=2))
    return 0 if hard else 1


def _md(o: dict[str, Any]) -> str:
    g = o.get("gate100") or {}
    d = o.get("delta") or {}
    return "\n".join([
        "# K-STAT-REPACK-MIX-RECOMBINE — S4 stat 몰아주기 보완조합",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · APPLY={o.get('apply')} · ge3미클레임 · 1237아님",
        "창 게이트 1137~1236 n100 · 스모크 1234~1236 · 뇌=stat · pool 1~10·복사4 불변",
        "",
        "## 0) 한 줄",
        "",
        "몰아주기 5번째 장을 **복사 4장에 없는 고점수 6개**로 바꿨다. "
        f"HARD={'통과' if o.get('hard_ok') else '실패'} · 배선={('살아있음' if o.get('wire_alive') else '무반응')} · "
        f"비악화={o.get('prefer_not_worse') and o.get('prize_not_worse')} · 설계={o.get('design_moved')}. "
        f"라이브 MODE=`{o.get('live_mode_after')}` (롤백 `{o.get('rollback')}`).",
        "",
        "## 1) 게이트",
        "",
        "| 축 | OFF(top6) | ON(complement) | Δ |",
        "|----|-----------|----------------|---|",
        f"| prefer (repack5) | {g.get('prefer_off')} | {g.get('prefer_on')} | {d.get('prefer')} |",
        f"| prize (repack5) | {g.get('prize_off')} | {g.get('prize_on')} | {d.get('prize')} |",
        f"| 재조합 vs 복사4 Jaccard | {g.get('jaccard_off')} | {g.get('jaccard_on')} | 모니터 |",
        f"| union_repack | {g.get('union_repack_off')} | {g.get('union_repack_on')} | 모니터 |",
        "",
        f"- pool동일 {g.get('pool_same')}/{g.get('n_ok')} · 복사4동일 {g.get('copies_same')} · 5장변경 {g.get('recombine_diff')}",
        f"- 보완∩복사 mean {g.get('inter_on_mean')} (설계상 0에 가까움)",
        f"- peek={g.get('peek_fail')} err={g.get('n_errors')} · self_check={o.get('self_check', {}).get('ok')}",
        "",
        "## 2) 판정",
        "",
        "- APPLY: HARD + 5장변경>0 + prefer/prize 비악화 + Jaccard↓또는 union_repack↑",
        "- 등수·적중 mean으로 성공 금지.",
        "- |Δ| 대칭 iso는 타뇌 독립성용. EV가 좋아진 음수 Δ를 실패로 치지 않음.",
        "",
        "## 3) 다음",
        "",
        "S5 리셋+stat 200회 (APPLY일 때). HOLD면 MODE=top6. 1237아님.",
        "",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
