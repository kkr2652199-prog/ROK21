# -*- coding: utf-8 -*-
"""K-REPACK-HYENA-WIRE — 뇌별 몰아주기 H4/H2 단계 게이트.

S0 리스트 · S1 stat · S2 markov · S3 review · S4 합동스모크.
score5 실패 시 keep1. prefer/prize 비악화. pool 1~10 HARD 불변.
타깃 적중 미입력. 1237아님. 등수 게이트 아님.
통과 뇌만 라이브 플래그+해당뇌 캐시 1037~1236 재생성. 원장 미기록.
"""
from __future__ import annotations

import json
import random
import re
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KREPACK_HYENA_WIRE.json"
OUT_MD = ROOT / "reports" / "20260815_KREPACK_HYENA_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
SRC = ROOT / "app" / "testlotto" / "signal_pool.py"
DB = ROOT / "data" / "lotto_testlotto.db"

SMOKE_LO, SMOKE_HI = 1234, 1236
GATE_LO, GATE_HI = 1137, 1236
REFILL_LO, REFILL_HI = 1037, 1236
SEED = 42
ISO = 0.005
BRAINS = ("stat", "markov", "review")
CANDS = ("score5", "keep1")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


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


def _copy_n(pool: list[dict], rep: list[dict]) -> int:
    pset = {_key(_nums(s)) for s in pool}
    return sum(1 for s in rep if _key(_nums(s)) in pset)


def _union(sets: list[dict]) -> int:
    u: set[int] = set()
    for s in sets:
        u.update(_nums(s))
    return len(u)


def _repack(tag: str, pool_br: dict, draws, dno: int, mode: str) -> list[dict]:
    import app.testlotto.signal_pool as sp

    old = dict(sp.REPACK_HYENA_MODE_BY_BRAIN)
    try:
        for t in BRAINS:
            sp.REPACK_HYENA_MODE_BY_BRAIN[t] = mode if t == tag else ""
        learner = sp.RollingSignalLearner()
        num_ema, pos_ema = learner.snapshot()
        rows = sp.repack_by_brain(
            pool_br,
            sp._build_hint(draws, dno),
            num_ema,
            pos_ema,
            target_draw_no=dno,
            hint_by_brain=sp.build_hint_by_brain(draws, dno),
        )
        return [x for x in rows if str(x.get("brain_tag")) == tag]
    finally:
        sp.REPACK_HYENA_MODE_BY_BRAIN.clear()
        sp.REPACK_HYENA_MODE_BY_BRAIN.update(old)


def _expand_pool(tag: str, draws, dno: int) -> tuple[list[dict], dict]:
    import app.testlotto.signal_pool as sp

    random.seed(SEED)
    pool = sp.expand_pool(draws, dno, seed=SEED, brains=[tag])
    pool_br = sp._pool_by_brain(pool)
    return pool_br.get(tag) or [], pool_br


def _run_brain(tag: str, mode: str, lo: int, hi: int, label: str) -> dict[str, Any]:
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
    n_ok = peek_fail = size_bad = pool_same = changed = 0
    errors: list[str] = []
    copy_off: list[int] = []
    copy_on: list[int] = []
    u_off: list[int] = []
    u_on: list[int] = []
    pref_off: list[float] = []
    pref_on: list[float] = []
    prize_off: list[float] = []
    prize_on: list[float] = []
    assemble_on: Counter[str] = Counter()

    for i, r in enumerate(rows):
        dno = int(r["draw_no"])
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        max_mat = max((int(d["draw_no"]) for d in draws), default=0)
        if max_mat >= dno:
            peek_fail += 1
            continue
        try:
            p, pool_br = _expand_pool(tag, draws, dno)
            r_off = _repack(tag, pool_br, draws, dno, "")
            r_on = _repack(tag, pool_br, draws, dno, mode)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} {type(e).__name__}: {e}")
            continue
        if len(p) != 10 or len(r_off) != 5 or len(r_on) != 5:
            size_bad += 1
            continue
        pool_same += 1
        if [_key(_nums(s)) for s in r_off] != [_key(_nums(s)) for s in r_on]:
            changed += 1
        copy_off.append(_copy_n(p, r_off))
        copy_on.append(_copy_n(p, r_on))
        u_off.append(_union(r_off))
        u_on.append(_union(r_on))
        for s in r_on:
            assemble_on[str(s.get("assemble") or "")] += 1
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
                f"  [{label}] {i+1}/{len(rows)} d={dno} n_ok={n_ok} ch={changed}",
                flush=True,
            )

    def _m(xs: list[float]) -> float | None:
        return round(mean(xs), 6) if xs else None

    d_pref = d_prize = None
    if pref_off and pref_on:
        d_pref = round(mean(pref_on) - mean(pref_off), 6)
        d_prize = round(mean(prize_on) - mean(prize_off), 6)
    hard = (
        n_ok == (hi - lo + 1)
        and peek_fail == 0
        and size_bad == 0
        and len(errors) == 0
        and pool_same == n_ok
    )
    iso = bool(d_pref is not None and d_pref < ISO and d_prize is not None and d_prize < ISO)
    # 점수 상위6이 pool 1장과 우연히 같아도 source는 score_repack.
    # 세트일치 copy_on으로 H4를 탈락시키지 않는다.
    hyena_lbl = sum(assemble_on.get(k, 0) for k in assemble_on if "hyena" in k)
    design = bool(changed > 0 and (hyena_lbl >= n_ok or changed >= n_ok // 2))
    apply = bool(hard and iso and design)
    return {
        "tag": tag,
        "mode": mode,
        "label": label,
        "n_ok": n_ok,
        "n_target": hi - lo + 1,
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "n_errors": len(errors),
        "errors_head": errors[:6],
        "pool_same": pool_same,
        "changed": changed,
        "copy_off": _m(copy_off),
        "copy_on": _m(copy_on),
        "union_off": _m(u_off),
        "union_on": _m(u_on),
        "prefer_off": _m(pref_off),
        "prefer_on": _m(pref_on),
        "prize_off": _m(prize_off),
        "prize_on": _m(prize_on),
        "delta_prefer": d_pref,
        "delta_prize": d_prize,
        "assemble_on": dict(assemble_on),
        "hard_ok": hard,
        "iso_ok": iso,
        "design_ok": design,
        "apply": apply,
        "verdict": "APPLY" if apply else ("HOLD_ISO_FAIL" if hard and not iso else ("HOLD_NO_DESIGN" if hard else "FAIL")),
    }


def _joint_smoke(modes: dict[str, str]) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    old = dict(sp.REPACK_HYENA_MODE_BY_BRAIN)
    out: dict[str, Any] = {"modes": dict(modes), "draws": []}
    try:
        sp.REPACK_HYENA_MODE_BY_BRAIN.clear()
        sp.REPACK_HYENA_MODE_BY_BRAIN.update(modes)
        peek = 0
        for dno in range(SMOKE_LO, SMOKE_HI + 1):
            set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            if max((int(d["draw_no"]) for d in draws), default=0) >= dno:
                peek += 1
            random.seed(SEED)
            pool = sp.expand_pool(draws, dno, seed=SEED)
            pool_br = sp._pool_by_brain(pool)
            learner = sp.RollingSignalLearner()
            rows = sp.repack_by_brain(
                pool_br,
                sp._build_hint(draws, dno),
                learner.snapshot()[0],
                learner.snapshot()[1],
                target_draw_no=dno,
                hint_by_brain=sp.build_hint_by_brain(draws, dno),
            )
            rec: dict[str, Any] = {"draw_no": dno}
            for tag in BRAINS:
                p = pool_br.get(tag) or []
                r = [x for x in rows if str(x.get("brain_tag")) == tag]
                rec[tag] = {
                    "pool": len(p),
                    "repack": len(r),
                    "copy": _copy_n(p, r),
                    "assemble": [str(x.get("assemble") or "") for x in r],
                }
            out["draws"].append(rec)
        out["peek_fail"] = peek
        out["ok"] = peek == 0 and all(
            d[t]["pool"] == 10 and d[t]["repack"] == 5 for d in out["draws"] for t in BRAINS
        )
    finally:
        sp.REPACK_HYENA_MODE_BY_BRAIN.clear()
        sp.REPACK_HYENA_MODE_BY_BRAIN.update(old)
    return out


def _write_live_modes(modes: dict[str, str]) -> None:
    text = SRC.read_text(encoding="utf-8")
    block = (
        "REPACK_HYENA_MODE_BY_BRAIN: dict[str, str] = {\n"
        f'    "stat": "{modes["stat"]}",\n'
        f'    "markov": "{modes["markov"]}",\n'
        f'    "review": "{modes["review"]}",\n'
        "}"
    )
    new, n = re.subn(
        r"REPACK_HYENA_MODE_BY_BRAIN: dict\[str, str\] = \{[^}]+\}",
        block,
        text,
        count=1,
    )
    if n != 1:
        raise RuntimeError(f"hyena dict replace failed n={n}")
    SRC.write_text(new, encoding="utf-8")


def _refill(modes: dict[str, str]) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.pool_view_cache import save_pool_view_cache_one

    applied = [t for t in BRAINS if modes[t]]
    if not applied:
        return {"skipped": True, "applied": []}
    old = dict(sp.REPACK_HYENA_MODE_BY_BRAIN)
    ok = 0
    fail = 0
    try:
        sp.REPACK_HYENA_MODE_BY_BRAIN.clear()
        sp.REPACK_HYENA_MODE_BY_BRAIN.update(modes)
        for dno in range(REFILL_LO, REFILL_HI + 1):
            set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            for tag in applied:
                try:
                    random.seed(SEED)
                    pool = sp.expand_pool(draws, dno, seed=SEED, brains=[tag])
                    pool_br = sp._pool_by_brain(pool)
                    learner = sp.RollingSignalLearner()
                    rows = sp.repack_by_brain(
                        pool_br,
                        sp._build_hint(draws, dno),
                        learner.snapshot()[0],
                        learner.snapshot()[1],
                        target_draw_no=dno,
                        hint_by_brain=sp.build_hint_by_brain(draws, dno),
                    )
                    p = [
                        {
                            "set_no": int(c.get("pred_set_no") or c.get("set_no") or 1),
                            "nums": _nums(c),
                            "brain_tag": tag,
                            "kind": "pool",
                            **({"role": c.get("role")} if c.get("role") else {}),
                        }
                        for c in (pool_br.get(tag) or [])
                    ]
                    r = [
                        {
                            "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
                            "nums": _nums(c),
                            "brain_tag": tag,
                            "kind": "repack",
                            "assemble": c.get("assemble") or "",
                            **({"source": c.get("source"), "source_set_no": c.get("source_set_no")} if c.get("source") else {}),
                        }
                        for c in rows
                        if str(c.get("brain_tag")) == tag
                    ]
                    save_pool_view_cache_one(
                        dno,
                        tag,
                        {"pool_by_brain": {tag: p}, "repack_by_brain": {tag: r}, "seed": SEED},
                    )
                    ok += 1
                except Exception as e:  # noqa: BLE001
                    fail += 1
                    print(f"  refill fail {tag} {dno} {type(e).__name__}: {e}", flush=True)
            if dno % 20 == 0 or dno == REFILL_HI:
                print(f"  [refill] {dno} ok={ok} fail={fail}", flush=True)
    finally:
        sp.REPACK_HYENA_MODE_BY_BRAIN.clear()
        sp.REPACK_HYENA_MODE_BY_BRAIN.update(old)
    return {"skipped": False, "applied": applied, "ok": ok, "fail": fail}


def _hard_db() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    led = {
        str(r[0]): int(r[1])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
        )
    }
    conn.close()
    return {"draws_max": dmax, "pred_1237": pred_1237, "ledger": led}


def _md(o: dict[str, Any]) -> str:
    live = o.get("live_modes") or {}
    lines = [
        "# K-REPACK-HYENA-WIRE",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · APPLY={o.get('apply')} · 1237아님 · 등수 게이트 아님",
        "단계: S0리스트 → S1 stat → S2 markov → S3 review → S4 합동스모크 → 통과뇌 캐시재생.",
        "",
        "## 0) 한 줄",
        "",
        "몰아주기를 뇌별 점수로 **새 5장**을 짜는 하이에나로 바꿨다. "
        f"라이브 stat=`{live.get('stat') or 'union'}` · markov=`{live.get('markov') or 'union'}` · "
        f"review=`{live.get('review') or 'union'}`. "
        "점수축은 기존 그대로(stat 과거/원장 · markov prefer · review prize). 타깃 적중 미입력.",
        "",
        "## 1) 단계 리스트",
        "",
        "| 단계 | 뇌 | 1순위 | 실패시 | 게이트 |",
        "|------|----|--------|--------|--------|",
        "| S0 | — | 플래그 신설 | — | 코드 |",
        "| S1 | stat | score5 | keep1 | prefer/prize · pool불변 |",
        "| S2 | markov | score5 | keep1 | 동상 · 타뇌 플래그OFF |",
        "| S3 | review | score5 | keep1 | 동상 · 타뇌 플래그OFF |",
        "| S4 | 3뇌 | 합동 스모크 1234–1236 | — | peek0 · 10+5 |",
        "",
        "## 2) 게이트 결과",
        "",
        "| 단계 | 뇌 | 모드 | HARD | iso | design | Δprefer | Δprize | copy off→on | union off→on | 변경 | 판정 |",
        "|------|----|------|------|-----|--------|---------|--------|-------------|--------------|------|------|",
    ]
    for st in o.get("stages") or []:
        lines.append(
            f"| {st.get('step')} | {st.get('tag')} | {st.get('mode')} | {st.get('hard_ok')} | "
            f"{st.get('iso_ok')} | {st.get('design_ok')} | {st.get('delta_prefer')} | {st.get('delta_prize')} | "
            f"{st.get('copy_off')}→{st.get('copy_on')} | {st.get('union_off')}→{st.get('union_on')} | "
            f"{st.get('changed')} | {st.get('verdict')} |"
        )
    js = o.get("joint_smoke") or {}
    lines += [
        "",
        "## 3) S4 합동 스모크",
        "",
        f"ok={js.get('ok')} · peek={js.get('peek_fail')} · modes={js.get('modes')}",
        "",
        "## 4) 캐시 재생성",
        "",
        json.dumps(o.get("refill") or {}, ensure_ascii=False),
        "",
        "## 5) HARD DB",
        "",
        json.dumps(o.get("db") or {}, ensure_ascii=False),
        "",
        "## 6) 롤백",
        "",
        '`REPACK_HYENA_MODE_BY_BRAIN` 세 뇌를 `""` 로.',
        "",
        "## 7) 금지 확인",
        "",
        "타깃 적중 미입력. 원장 미기록. 1237 아님. 동결 토큰 미수정. hits/등수 클레임 금지.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    import app.testlotto.signal_pool as sp

    db = _hard_db()
    print("db", db, flush=True)
    stages: list[dict[str, Any]] = []
    live = {t: "" for t in BRAINS}

    for i, tag in enumerate(BRAINS, start=1):
        step = f"S{i}"
        chosen = ""
        for mode in CANDS:
            print(f"== {step} {tag} {mode} smoke ==", flush=True)
            smoke = _run_brain(tag, mode, SMOKE_LO, SMOKE_HI, f"{step}-{tag}-{mode}-sm")
            print("smoke", smoke["verdict"], smoke["delta_prefer"], smoke["delta_prize"], flush=True)
            if not (
                smoke["n_ok"] == 3
                and smoke["peek_fail"] == 0
                and smoke["size_bad"] == 0
                and smoke["n_errors"] == 0
            ):
                smoke["step"] = step
                stages.append(smoke)
                continue
            print(f"== {step} {tag} {mode} gate100 ==", flush=True)
            gate = _run_brain(tag, mode, GATE_LO, GATE_HI, f"{step}-{tag}-{mode}-g")
            gate["step"] = step
            stages.append(gate)
            print("gate", gate["verdict"], gate["delta_prefer"], gate["delta_prize"], flush=True)
            if gate["apply"]:
                chosen = mode
                break
        live[tag] = chosen
        print(f"LIVE {tag}={chosen or 'union'}", flush=True)

    print("== S4 joint smoke ==", flush=True)
    joint = _joint_smoke(live)
    print("joint", joint.get("ok"), joint.get("peek_fail"), flush=True)

    apply_any = any(live[t] for t in BRAINS)
    if apply_any and joint.get("ok"):
        _write_live_modes(live)
        # re-import not needed; source updated for process restart
        sp.REPACK_HYENA_MODE_BY_BRAIN.clear()
        sp.REPACK_HYENA_MODE_BY_BRAIN.update(live)
        print("== refill applied brains ==", flush=True)
        refill = _refill(live)
    else:
        refill = {"skipped": True, "reason": "no_apply_or_joint_fail"}

    db2 = _hard_db()
    verdict = "APPLY_OK" if apply_any and joint.get("ok") and (refill.get("fail") in (None, 0)) else (
        "HOLD_ALL" if not apply_any else "PARTIAL_OR_FAIL"
    )
    payload = {
        "id": "K-REPACK-HYENA-WIRE",
        "as_of": _now(),
        "apply": apply_any and joint.get("ok") is True,
        "verdict": verdict,
        "iso_thr": ISO,
        "live_modes": live,
        "stages": stages,
        "joint_smoke": joint,
        "refill": refill,
        "db": db,
        "db_after": db2,
        "rollback": 'REPACK_HYENA_MODE_BY_BRAIN 전부 ""',
        "pred_1237": db2["pred_1237"],
        "draws_max": db2["draws_max"],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    text = _md(payload)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "live": live,
                "joint_ok": joint.get("ok"),
                "refill": refill,
                "pred_1237": db2["pred_1237"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if db2["pred_1237"] == 0 and db2["draws_max"] == 1236 else 2


if __name__ == "__main__":
    raise SystemExit(main())
