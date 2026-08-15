# -*- coding: utf-8 -*-
"""K-REVIEW-ROLE-TIER-LEARN-WIRE — review도 6~8/9~10 원장복습 소비.

stat·markov 소비 유지. review 1~5 불변. 타뇌 pool 불변 HARD.
게이트=prefer/prize 비악화. 1237아님. DB쓰기 없음.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KREVIEW_ROLE_TIER_LEARN_WIRE.json"
OUT_MD = ROOT / "reports" / "20260815_KREVIEW_ROLE_TIER_LEARN_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SMOKE_LO, SMOKE_HI = 1234, 1236
GATE_LO, GATE_HI = 1137, 1236
SEED = 42
ISO = 0.005
OFF_BRAINS = frozenset({"stat", "markov"})
ON_BRAINS = frozenset({"stat", "markov", "review"})


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _by_brain(pool: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"stat": [], "markov": [], "review": []}
    for s in pool:
        t = str(s.get("brain_tag") or "")
        if t in out:
            out[t].append(s)
    for t in out:
        out[t] = sorted(out[t], key=lambda x: int(x.get("set_no") or 0))
    return out


def _slot(rows: list[dict], lo: int, hi: int) -> list[dict]:
    return [s for s in rows if lo <= int(s.get("set_no") or 0) <= hi]


def _keys(rows: list[dict]) -> list[tuple[int, ...]]:
    return [_key(_nums(s)) for s in rows]


def _expand(draws, dno: int, *, brains: frozenset[str]) -> dict[str, list[dict]]:
    import app.testlotto.signal_pool as sp

    old = sp.ROLE_TIER_LEARN_BRAINS
    sp.ROLE_TIER_LEARN_BRAINS = frozenset(brains)
    try:
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED)
        return _by_brain(pool)
    finally:
        sp.ROLE_TIER_LEARN_BRAINS = old


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

    tnb1 = assert_shape_no_bonus_in_signature()
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
    n_ok = peek_fail = size_bad = 0
    stat_same = markov_same = r_skill_same = 0
    r_cover_diff = r_shape_diff = 0
    errors: list[str] = []
    src_cover: dict[str, int] = {}
    src_shape: dict[str, int] = {}
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
            off = _expand(draws, dno, brains=OFF_BRAINS)
            on = _expand(draws, dno, brains=ON_BRAINS)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} {type(e).__name__}: {e}")
            continue
        sizes_ok = all(len(off[t]) == 10 and len(on[t]) == 10 for t in off)
        if not sizes_ok:
            size_bad += 1
            continue
        if _keys(off["stat"]) == _keys(on["stat"]):
            stat_same += 1
        if _keys(off["markov"]) == _keys(on["markov"]):
            markov_same += 1
        r_off, r_on = off["review"], on["review"]
        if _keys(_slot(r_off, 1, 5)) == _keys(_slot(r_on, 1, 5)):
            r_skill_same += 1
        if _keys(_slot(r_off, 6, 8)) != _keys(_slot(r_on, 6, 8)):
            r_cover_diff += 1
        if _keys(_slot(r_off, 9, 10)) != _keys(_slot(r_on, 9, 10)):
            r_shape_diff += 1
        for s in _slot(r_on, 6, 8):
            k = str(s.get("source") or "")
            src_cover[k] = src_cover.get(k, 0) + 1
        for s in _slot(r_on, 9, 10):
            k = str(s.get("source") or "")
            src_shape[k] = src_shape.get(k, 0) + 1
        pref_t = cs.prefer_table(draws, brain="markov")
        prize_t = cs.prize_table(draws, brain="review")
        changed_off = _slot(r_off, 6, 10)
        changed_on = _slot(r_on, 6, 10)
        po, pn = _axis(pref_t, changed_off), _axis(pref_t, changed_on)
        zo, zn = _axis(prize_t, changed_off), _axis(prize_t, changed_on)
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
                f"  [{label}] {i+1}/{len(rows)} d={dno} n_ok={n_ok} "
                f"shape_diff={r_shape_diff} cover_diff={r_cover_diff}",
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
        "tnb1": bool(tnb1.get("ok")),
        "stat_same": stat_same,
        "markov_same": markov_same,
        "review_skill_same": r_skill_same,
        "review_cover_diff": r_cover_diff,
        "review_shape_diff": r_shape_diff,
        "src_cover_on": src_cover,
        "src_shape_on": src_shape,
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
        and smoke["tnb1"]
        and smoke["stat_same"] == 3
        and smoke["markov_same"] == 3
        and smoke["review_skill_same"] == 3
    )
    print("smoke_hard", smoke_hard, "shape_diff", smoke["review_shape_diff"], flush=True)
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
        and gate["tnb1"]
        and gate["stat_same"] == 100
        and gate["markov_same"] == 100
        and gate["review_skill_same"] == 100
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
            (gate["review_cover_diff"] or 0) > 0
            or (gate["review_shape_diff"] or 0) > 0
        )
    wire_alive = design
    apply = bool(hard and wire_alive and iso)
    if apply:
        verdict = "WIRE_OK"
        sp.ROLE_TIER_LEARN_BRAINS = ON_BRAINS
    elif hard and wire_alive and not iso:
        verdict = "HOLD_ISO_FAIL"
        sp.ROLE_TIER_LEARN_BRAINS = OFF_BRAINS
    elif hard and not wire_alive:
        verdict = "DEAD_WIRE"
        sp.ROLE_TIER_LEARN_BRAINS = OFF_BRAINS
    else:
        verdict = "FAIL"
        sp.ROLE_TIER_LEARN_BRAINS = OFF_BRAINS

    out = {
        "id": "K-REVIEW-ROLE-TIER-LEARN-WIRE",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "iso_thr": ISO,
        "live_brains_after": sorted(sp.ROLE_TIER_LEARN_BRAINS),
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
        "rollback": 'ROLE_TIER_LEARN_BRAINS=frozenset({"stat","markov"})',
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
        "delta": out["delta"],
        "live_brains_after": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "stat_same": (gate or {}).get("stat_same"),
        "markov_same": (gate or {}).get("markov_same"),
        "review_skill_same": (gate or {}).get("review_skill_same"),
        "cover_diff": (gate or {}).get("review_cover_diff"),
        "shape_diff": (gate or {}).get("review_shape_diff"),
        "src_cover": (gate or {}).get("src_cover_on"),
        "src_shape": (gate or {}).get("src_shape_on"),
    }, ensure_ascii=False, indent=2))
    return 0 if hard else 1


def _md(o: dict[str, Any]) -> str:
    g = o.get("gate100") or {}
    d = o.get("delta") or {}
    return "\n".join([
        "# K-REVIEW-ROLE-TIER-LEARN-WIRE — review 6~8/9~10 원장복습 소비",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · APPLY={o.get('apply')} · ge3미클레임 · 1237아님",
        "창 게이트 1137~1236 n100 · 스모크 1234~1236 · stat·markov 소비 유지",
        "",
        "## 0) 한 줄",
        "",
        "review도 stat·markov와 같이 **6~8/9~10 원장 숙제표**를 읽게 했다. 1~5는 그대로. "
        f"HARD={'통과' if o.get('hard_ok') else '실패'} · 배선={('살아있음' if o.get('wire_alive') else '무반응')} · "
        f"비악화={o.get('prefer_not_worse') and o.get('prize_not_worse')}. "
        f"라이브 BRAINS=`{o.get('live_brains_after')}` (롤백 `{o.get('rollback')}`).",
        "",
        "## 1) 게이트",
        "",
        "| 축 | OFF(stat+markov) | ON(+review) | Δ |",
        "|----|------------------|-------------|---|",
        f"| prefer (review 6~10) | {g.get('prefer_off')} | {g.get('prefer_on')} | {d.get('prefer')} |",
        f"| prize (review 6~10) | {g.get('prize_off')} | {g.get('prize_on')} | {d.get('prize')} |",
        f"| review cover 변경 | 0 | {g.get('review_cover_diff')} | 모니터 |",
        f"| review shape 변경 | 0 | {g.get('review_shape_diff')} | 모니터 |",
        "",
        f"- stat pool동일 {g.get('stat_same')}/{g.get('n_ok')} · markov동일 {g.get('markov_same')} · review 1~5동일 {g.get('review_skill_same')}",
        f"- cover source `{json.dumps(g.get('src_cover_on') or {}, ensure_ascii=False)}`",
        f"- shape source `{json.dumps(g.get('src_shape_on') or {}, ensure_ascii=False)}`",
        f"- peek={g.get('peek_fail')} err={g.get('n_errors')} T-NB1={g.get('tnb1')}",
        "",
        "## 2) 판정",
        "",
        "- WIRE_OK: HARD + review 6~10 변경>0 + prefer/prize 비악화 + 타뇌·1~5 불변",
        "- COVER_SELECT/몰아주기 S1~S4를 review에 복사하지 않음.",
        "- 등수·적중 mean으로 성공 금지.",
        "",
        "## 3) 다음",
        "",
        "WIRE_OK면 review만 리셋+200회 소비 누적. HOLD면 BRAINS={stat,markov}. 1237아님.",
        "",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
