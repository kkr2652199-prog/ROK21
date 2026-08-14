# -*- coding: utf-8 -*-
"""K-STAT-REPACK-ROLE-QUOTA — S3 게이트.

stat 몰아주기 cap4: cover≥1 · shape≤1 · skill≥1.
pool 1~10 불변 HARD. 게이트=prefer/prize 비악화.
모니터=copy_by_role. 1237아님. DB쓰기 없음.
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KSTAT_REPACK_ROLE_QUOTA.json"
OUT_MD = ROOT / "reports" / "20260814_KSTAT_REPACK_ROLE_QUOTA.md"
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


def _sn_role(sn: int) -> str:
    if 1 <= sn <= 5:
        return "skill"
    if 6 <= sn <= 8:
        return "cover"
    if 9 <= sn <= 10:
        return "shape"
    return "other"


def _expand(draws, dno: int, *, quota: bool) -> tuple[list[dict], list[dict]]:
    import app.testlotto.signal_pool as sp

    old = bool(sp.REPACK_ROLE_QUOTA_WIRE)
    sp.REPACK_ROLE_QUOTA_WIRE = bool(quota)
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
        sp.REPACK_ROLE_QUOTA_WIRE = old


def _copy_roles(pool: list[dict], rep: list[dict]) -> Counter:
    pmap = {_key(_nums(s)): int(s.get("set_no") or 0) for s in pool}
    c: Counter = Counter()
    for s in rep:
        sn = pmap.get(_key(_nums(s)))
        if sn:
            c[_sn_role(sn)] += 1
        else:
            c["recombine"] += 1
    return c


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
    n_ok = peek_fail = size_bad = pool_same = rep_diff = 0
    miss_cover_off = miss_cover_on = 0
    errors: list[str] = []
    copy_off: Counter = Counter()
    copy_on: Counter = Counter()
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
            p_off, r_off = _expand(draws, dno, quota=False)
            p_on, r_on = _expand(draws, dno, quota=True)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} {type(e).__name__}: {e}")
            continue
        if len(p_off) != 10 or len(p_on) != 10 or len(r_off) != 5 or len(r_on) != 5:
            size_bad += 1
            continue
        if [_key(_nums(s)) for s in p_off] == [_key(_nums(s)) for s in p_on]:
            pool_same += 1
        if [_key(_nums(s)) for s in r_off] != [_key(_nums(s)) for s in r_on]:
            rep_diff += 1
        co = _copy_roles(p_off, r_off)
        cn = _copy_roles(p_on, r_on)
        copy_off.update(co)
        copy_on.update(cn)
        if co.get("cover", 0) < 1:
            miss_cover_off += 1
        if cn.get("cover", 0) < 1:
            miss_cover_on += 1
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
            print(f"  [{label}] {i+1}/{len(rows)} d={dno} n_ok={n_ok} rep_diff={rep_diff}", flush=True)

    def _m(xs: list[float]) -> float | None:
        return round(mean(xs), 6) if xs else None

    n_rep = max(1, n_ok * 5)
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
        "repack_diff": rep_diff,
        "miss_cover_off": miss_cover_off,
        "miss_cover_on": miss_cover_on,
        "copy_off": dict(copy_off),
        "copy_on": dict(copy_on),
        "cover_share_off": round(copy_off.get("cover", 0) / n_rep, 4),
        "cover_share_on": round(copy_on.get("cover", 0) / n_rep, 4),
        "shape_share_off": round(copy_off.get("shape", 0) / n_rep, 4),
        "shape_share_on": round(copy_on.get("shape", 0) / n_rep, 4),
        "prefer_off": _m(pref_off),
        "prefer_on": _m(pref_on),
        "prize_off": _m(prize_off),
        "prize_on": _m(prize_on),
    }


def main() -> int:
    import app.testlotto.signal_pool as sp

    print("== SMOKE ==", flush=True)
    smoke = _run(SMOKE_LO, SMOKE_HI, "smoke")
    smoke_hard = (
        smoke["n_ok"] == 3
        and smoke["peek_fail"] == 0
        and smoke["size_bad"] == 0
        and smoke["n_errors"] == 0
        and smoke["pool_same"] == 3
    )
    print("smoke_hard", smoke_hard, "rep_diff", smoke["repack_diff"], flush=True)
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
        and gate["miss_cover_on"] == 0
    )
    d_pref = d_prize = None
    prefer_not_worse = prize_not_worse = iso = design = False
    if gate and gate["prefer_off"] is not None and gate["prefer_on"] is not None:
        d_pref = round(gate["prefer_on"] - gate["prefer_off"], 6)
        d_prize = round(gate["prize_on"] - gate["prize_off"], 6)
        prefer_not_worse = d_pref < ISO
        prize_not_worse = d_prize < ISO
        iso = prefer_not_worse and prize_not_worse
        design = bool(
            (gate["cover_share_on"] or 0) > (gate["cover_share_off"] or 0)
            or (gate["shape_share_on"] or 9) < (gate["shape_share_off"] or 9)
        )
    wire_alive = bool(gate and gate["repack_diff"] > 0)
    apply = bool(hard and wire_alive and iso and design)
    if apply:
        verdict = "APPLY"
        sp.REPACK_ROLE_QUOTA_WIRE = True
    elif hard and wire_alive and not iso:
        verdict = "HOLD_ISO_FAIL"
        sp.REPACK_ROLE_QUOTA_WIRE = False
    elif hard and not wire_alive:
        verdict = "DEAD_WIRE"
        sp.REPACK_ROLE_QUOTA_WIRE = False
    elif hard and wire_alive and iso and not design:
        verdict = "HOLD_NO_DESIGN"
        sp.REPACK_ROLE_QUOTA_WIRE = False
    else:
        verdict = "FAIL"
        sp.REPACK_ROLE_QUOTA_WIRE = False

    out = {
        "id": "K-STAT-REPACK-ROLE-QUOTA",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "iso_thr": ISO,
        "live_wire_after": bool(sp.REPACK_ROLE_QUOTA_WIRE),
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
        "rollback": "REPACK_ROLE_QUOTA_WIRE=False",
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
        "live_wire_after": bool(sp.REPACK_ROLE_QUOTA_WIRE),
        "cover_share": {"off": (gate or {}).get("cover_share_off"), "on": (gate or {}).get("cover_share_on")},
        "shape_share": {"off": (gate or {}).get("shape_share_off"), "on": (gate or {}).get("shape_share_on")},
        "miss_cover": {"off": (gate or {}).get("miss_cover_off"), "on": (gate or {}).get("miss_cover_on")},
        "repack_diff": (gate or {}).get("repack_diff"),
        "copy_off": (gate or {}).get("copy_off"),
        "copy_on": (gate or {}).get("copy_on"),
    }, ensure_ascii=False, indent=2))
    return 0 if hard else 1


def _md(o: dict[str, Any]) -> str:
    g = o.get("gate100") or {}
    d = o.get("delta") or {}
    return "\n".join([
        "# K-STAT-REPACK-ROLE-QUOTA — S3 stat 몰아주기 역할쿼터",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · APPLY={o.get('apply')} · ge3미클레임 · 1237아님",
        "창 게이트 1137~1236 n100 · 스모크 1234~1236 · 뇌=stat · pool 1~10 불변",
        "",
        "## 0) 한 줄",
        "",
        "몰아주기 4장 복사에 **cover 최소 1 · shape 최대 1 · skill 최소 1**을 넣었다. "
        f"HARD={'통과' if o.get('hard_ok') else '실패'} · 배선={('살아있음' if o.get('wire_alive') else '무반응')} · "
        f"비악화={o.get('prefer_not_worse') and o.get('prize_not_worse')} · 설계={o.get('design_moved')}. "
        f"라이브 WIRE=`{o.get('live_wire_after')}` (롤백 `{o.get('rollback')}`).",
        "",
        "## 1) 게이트",
        "",
        "| 축 | OFF | ON | Δ |",
        "|----|-----|----|---|",
        f"| prefer (repack5) | {g.get('prefer_off')} | {g.get('prefer_on')} | {d.get('prefer')} |",
        f"| prize (repack5) | {g.get('prize_off')} | {g.get('prize_on')} | {d.get('prize')} |",
        f"| cover 복사 비율 | {g.get('cover_share_off')} | {g.get('cover_share_on')} | 모니터 |",
        f"| shape 복사 비율 | {g.get('shape_share_off')} | {g.get('shape_share_on')} | 모니터 |",
        "",
        f"- pool동일 {g.get('pool_same')}/{g.get('n_ok')} · 몰아주기변경 {g.get('repack_diff')} · cover0장회 OFF {g.get('miss_cover_off')} ON {g.get('miss_cover_on')}",
        f"- copy OFF `{json.dumps(g.get('copy_off') or {}, ensure_ascii=False)}`",
        f"- copy ON `{json.dumps(g.get('copy_on') or {}, ensure_ascii=False)}`",
        f"- peek={g.get('peek_fail')} err={g.get('n_errors')}",
        "",
        "## 2) 판정",
        "",
        "- APPLY: HARD + 몰아주기변경>0 + cover 0장회=0 + prefer/prize 비악화 + cover비율↑또는 shape비율↓",
        "- 등수·적중 mean으로 성공 금지.",
        "",
        "## 3) 다음",
        "",
        "S4 몰아주기 5번째 장 보완조합 (APPLY일 때). HOLD면 플래그 False. 1237아님.",
        "",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
