# -*- coding: utf-8 -*-
"""K-REVIEW-REASONABLE-SET — 장마다 합리한 장. 소진·Jaccard멀리 없음.

기준=현 소진(SEQ). 신=장마다 1~45 리셋+tier1. #1=먼저 완성.
random.choices 라인 동결. 1237 신규예측 없음.
게이트 1137–1236 n100 peek0 · Δprefer/Δprize <0.005(증가실패).
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.set_diversity import avg_pairwise_jaccard  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260822_KREVIEW_REASONABLE_SET.json"
OUT_MD = ROOT / "reports" / "20260822_KREVIEW_REASONABLE_SET.md"
DB = ROOT / "data" / "lotto_testlotto.db"
TAG = "review"
GATE_LO, GATE_HI = 1137, 1236
REFILL_LO, REFILL_HI = 1037, 1236
ISO = 0.005
SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _axis(table: dict[int, float], sets: list[dict]) -> float | None:
    if not table or not sets:
        return None
    uni = mean(table[i] for i in range(1, 46))
    vals = []
    for s in sets:
        nums = _nums(s)
        if len(nums) == 6:
            vals.append(mean(table[n] for n in nums) - uni)
    return round(mean(vals), 6) if vals else None


def _m(xs: list[float]) -> float | None:
    return round(mean(xs), 6) if xs else None


def _geom(sets: list[list[int]]) -> dict[str, Any]:
    if len(sets) < 2:
        return {"union5": 0, "union10": 0, "jaccard5": 0.0, "s1_s2": 0, "multi5": 0, "wrap": 0.0}
    uni: set[int] = set()
    for s in sets:
        uni.update(s)
    skill = sets[:5] if len(sets) >= 5 else sets
    skill_u: set[int] = set()
    for s in skill:
        skill_u.update(s)
    cnt: dict[int, int] = {}
    for s in skill:
        for n in set(s):
            cnt[n] = cnt.get(n, 0) + 1
    wrap = 0.0
    if len(sets) >= 10:
        front = set()
        for s in sets[:7]:
            front.update(s)
        wrap = mean(len(set(s) & front) for s in sets[7:10])
    return {
        "union10": len(uni),
        "union5": len(skill_u),
        "jaccard5": round(avg_pairwise_jaccard(skill), 6),
        "s1_s2": len(set(sets[0]) & set(sets[1])) if len(sets) > 1 else 0,
        "multi5": sum(1 for v in cnt.values() if v >= 2),
        "wrap": round(wrap, 6),
    }


def _set_mode(eng: Any, mode: str) -> None:
    if mode == "seq":
        eng.REVIEW_SEQ_DISTRIBUTE = True
        eng.REVIEW_REASONABLE_SET = False
    elif mode == "reasonable":
        eng.REVIEW_SEQ_DISTRIBUTE = False
        eng.REVIEW_REASONABLE_SET = True
    else:
        eng.REVIEW_SEQ_DISTRIBUTE = False
        eng.REVIEW_REASONABLE_SET = False


def _pool(tag: str, draws, dno: int) -> list[dict]:
    import app.testlotto.signal_pool as sp

    random.seed(SEED)
    pool = sp.expand_pool(draws, dno, seed=SEED, brains=[tag])
    return [c for c in pool if str(c.get("brain_tag")) == tag]


def _gate() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.engine as eng
    from app.testlotto.brains.shared import crowd_signal as cs
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT draw_no FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (GATE_LO, GATE_HI),
        ).fetchall()
    finally:
        conn.close()

    t0 = time.perf_counter()
    n_ok = peek_fail = size_bad = 0
    errors: list[str] = []
    changed = 0
    mets = {
        k: {x: [] for x in ("pref", "prize", "u5", "u10", "jac", "s12", "mul", "wrap")}
        for k in ("off", "on")
    }
    src_on: list[str] = []

    old_seq = bool(eng.REVIEW_SEQ_DISTRIBUTE)
    old_rsn = bool(eng.REVIEW_REASONABLE_SET)
    try:
        for i, r in enumerate(rows):
            dno = int(r["draw_no"])
            set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            max_mat = max((int(d["draw_no"]) for d in draws), default=0)
            if max_mat >= dno:
                peek_fail += 1
                continue
            try:
                _set_mode(eng, "seq")
                p_off = _pool(TAG, draws, dno)
                _set_mode(eng, "reasonable")
                p_on = _pool(TAG, draws, dno)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{dno} {type(e).__name__}: {e}")
                continue
            if len(p_off) != 10 or len(p_on) != 10:
                size_bad += 1
                continue
            if [_key(_nums(s)) for s in p_off] != [_key(_nums(s)) for s in p_on]:
                changed += 1
            src_on.append(str(p_on[0].get("source") or ""))
            pref_t = cs.prefer_table(draws, brain="markov")
            prize_t = cs.prize_table(draws, brain="review")
            for name, p in (("off", p_off), ("on", p_on)):
                g = _geom([_nums(s) for s in p])
                mets[name]["pref"].append(_axis(pref_t, p) or 0.0)
                mets[name]["prize"].append(_axis(prize_t, p) or 0.0)
                mets[name]["u5"].append(float(g["union5"]))
                mets[name]["u10"].append(float(g["union10"]))
                mets[name]["jac"].append(float(g["jaccard5"]))
                mets[name]["s12"].append(float(g["s1_s2"]))
                mets[name]["mul"].append(float(g["multi5"]))
                mets[name]["wrap"].append(float(g["wrap"]))
            n_ok += 1
            if (i + 1) % 20 == 0 or dno == GATE_HI:
                print(f"  [gate] {i+1}/{len(rows)} d={dno} n_ok={n_ok}", flush=True)
    finally:
        eng.REVIEW_SEQ_DISTRIBUTE = old_seq
        eng.REVIEW_REASONABLE_SET = old_rsn

    def pack(name: str) -> dict[str, Any]:
        m = mets[name]
        return {
            "prefer": _m(m["pref"]),
            "prize": _m(m["prize"]),
            "union5": _m(m["u5"]),
            "union10": _m(m["u10"]),
            "jaccard5": _m(m["jac"]),
            "s1_s2": _m(m["s12"]),
            "multi5": _m(m["mul"]),
            "wrap": _m(m["wrap"]),
        }

    off, on = pack("off"), pack("on")
    d_pref = None if off["prefer"] is None else round(on["prefer"] - off["prefer"], 6)
    d_prize = None if off["prize"] is None else round(on["prize"] - off["prize"], 6)
    hard = n_ok == (GATE_HI - GATE_LO + 1) and peek_fail == 0 and size_bad == 0 and not errors
    iso = bool(d_pref is not None and d_pref < ISO and d_prize is not None and d_prize < ISO)
    design = bool(
        changed > 0
        and on["s1_s2"] is not None
        and off["s1_s2"] is not None
        and on["s1_s2"] > off["s1_s2"]
        and on["union5"] is not None
        and off["union5"] is not None
        and on["union5"] < off["union5"]
    )
    apply = bool(hard and iso and design)
    return {
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "n_ok": n_ok,
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "n_errors": len(errors),
        "errors_head": errors[:6],
        "changed": changed,
        "hard_ok": hard,
        "iso_ok": iso,
        "design_ok": design,
        "apply": apply,
        "off": off,
        "on": on,
        "delta_prefer": d_pref,
        "delta_prize": d_prize,
        "delta_union5": None if off["union5"] is None else round(on["union5"] - off["union5"], 6),
        "delta_jaccard5": None
        if off["jaccard5"] is None
        else round(on["jaccard5"] - off["jaccard5"], 6),
        "delta_s1_s2": None if off["s1_s2"] is None else round(on["s1_s2"] - off["s1_s2"], 6),
        "delta_multi5": None if off["multi5"] is None else round(on["multi5"] - off["multi5"], 6),
        "delta_wrap": None if off["wrap"] is None else round(on["wrap"] - off["wrap"], 6),
        "on_source_head": src_on[:3],
    }


def _refill_review() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.engine as eng
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.pool_view_cache import save_pool_view_cache_one

    _set_mode(eng, "reasonable")
    ok = fail = 0
    for dno in range(REFILL_LO, REFILL_HI + 1):
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        try:
            random.seed(SEED)
            pool = sp.expand_pool(draws, dno, seed=SEED, brains=[TAG])
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
                    "brain_tag": TAG,
                    "kind": "pool",
                    **({"role": c.get("role")} if c.get("role") else {}),
                    **({"source": c.get("source")} if c.get("source") else {}),
                }
                for c in (pool_br.get(TAG) or [])
            ]
            r = [
                {
                    "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
                    "nums": _nums(c),
                    "brain_tag": TAG,
                    "kind": "repack",
                    "assemble": c.get("assemble") or "",
                }
                for c in rows
                if str(c.get("brain_tag")) == TAG
            ]
            save_pool_view_cache_one(
                dno,
                TAG,
                {"pool_by_brain": {TAG: p}, "repack_by_brain": {TAG: r}, "seed": SEED},
            )
            ok += 1
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"  refill fail {dno} {type(e).__name__}: {e}", flush=True)
        if dno % 40 == 0 or dno == REFILL_HI:
            print(f"  [refill] {dno} ok={ok} fail={fail}", flush=True)
    return {"ok": ok, "fail": fail, "lo": REFILL_LO, "hi": REFILL_HI, "mode": eng.review_compose_mode()}


def _hard_db() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
        ledger = int(
            conn.execute(
                "SELECT COUNT(*) FROM testlotto_pool_hit_ledger WHERE brain_tag='stat'"
            ).fetchone()[0]
        )
    finally:
        conn.close()
    return {"draws_max": dmax, "pred_1237": pred_1237, "ledger_stat": ledger}


def _sample(dno: int) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT pool_json FROM testlotto_pool_view_cache WHERE brain=? AND draw_no=?",
            (TAG, dno),
        ).fetchone()
        draw = conn.execute(
            "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?",
            (dno,),
        ).fetchone()
    finally:
        conn.close()
    pool = json.loads(row["pool_json"]) if row else []
    actual = [int(draw[k]) for k in range(6)] if draw else []
    sets = []
    for s in pool:
        nums = _nums(s)
        sets.append(
            {
                "set_no": s.get("set_no"),
                "nums": nums,
                "source": s.get("source"),
                "overlap_s1": sorted(set(nums) & set(_nums(pool[0]))) if pool else [],
            }
        )
    return {"dno": dno, "actual": actual, "sets": sets}


def _write_md(doc: dict[str, Any]) -> str:
    g = doc["gate"]
    return "\n".join(
        [
            "# K-REVIEW-REASONABLE-SET (2026-08-22)",
            "",
            f"- **판정:** `{doc['verdict']}` · 금액뇌만 · 당첨미입력 · 1237 신규예측 없음",
            f"- 시각: {doc['ts']}",
            "- 형: 소진=찌꺼기. 장마다 합리한 장. Jaccard멀리 없음. 장겹침 허용.",
            f"- 근거: `{OUT_JSON.name}`",
            "",
            "## 재구성",
            "",
            "- OFF(소진): 45소진 · #2~#7 찌꺼기 · #1∩#2=0",
            "- ON: 장마다 1–45 리셋 · tier1(합/홀짝/구간/연번<4) · Jaccard·cover멀리·소진 없음",
            "- #1=엔진이 먼저 완성한 한 장. `random.choices` 라인 동결",
            "",
            "## 게이트 1137–1236 n100",
            "",
            f"- HARD `{g['hard_ok']}` peek **{g['peek_fail']}** size {g['size_bad']} err {g['n_errors']} {g['elapsed_s']}s · 변경 {g['changed']}",
            "",
            "| | prefer | prize | skill5합 | Jaccard5 | #1∩#2 | 2장이상 | wrap8-10 |",
            "|--|--------|-------|----------|----------|-------|---------|----------|",
            f"| 소진 | {g['off']['prefer']} | {g['off']['prize']} | {g['off']['union5']} | {g['off']['jaccard5']} | {g['off']['s1_s2']} | {g['off']['multi5']} | {g['off']['wrap']} |",
            f"| 합리장 | {g['on']['prefer']} | {g['on']['prize']} | {g['on']['union5']} | {g['on']['jaccard5']} | {g['on']['s1_s2']} | {g['on']['multi5']} | {g['on']['wrap']} |",
            f"| Δ | {g['delta_prefer']} | {g['delta_prize']} | {g['delta_union5']} | {g['delta_jaccard5']} | {g['delta_s1_s2']} | {g['delta_multi5']} | {g['delta_wrap']} |",
            "",
            f"- iso `{g['iso_ok']}` design `{g['design_ok']}` apply `{g['apply']}`",
            "",
            f"- WIRE SEQ=`{doc['seq']}` REASONABLE=`{doc['reasonable']}` · refill `{doc.get('refill')}`",
            "- 롤백=`REVIEW_REASONABLE_SET=False` (소진 재켜려면 SEQ True)",
            "- 우열금지 · 1237 신규예측 없음",
            "",
            "## 파일",
            "",
            "- `app/testlotto/brains/review_brain/engine.py` · `predict.py` · `signal_pool.py`",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )


def main() -> None:
    print("gate 1137-1236 n100 (seq vs reasonable)", flush=True)
    gate = _gate()
    print(json.dumps({k: gate[k] for k in ("n_ok", "peek_fail", "iso_ok", "design_ok", "apply", "delta_prefer", "delta_prize", "delta_s1_s2", "delta_union5")}, ensure_ascii=False), flush=True)

    import app.testlotto.brains.review_brain.engine as eng

    refill = None
    sample = None
    if gate["apply"]:
        _set_mode(eng, "reasonable")
        print("refill review 1037-1236", flush=True)
        refill = _refill_review()
        sample = _sample(1236)
    else:
        _set_mode(eng, "reasonable")

    hard = _hard_db()
    verdict = "APPLY_OK" if gate["apply"] and refill and refill.get("fail") == 0 else (
        "HOLD_ISO" if gate["hard_ok"] and not gate["iso_ok"] else (
            "HOLD_DESIGN" if gate["hard_ok"] and not gate["design_ok"] else "HOLD"
        )
    )
    doc = {
        "id": "K-REVIEW-REASONABLE-SET",
        "ts": _now(),
        "verdict": verdict,
        "seq": bool(eng.REVIEW_SEQ_DISTRIBUTE),
        "reasonable": bool(eng.REVIEW_REASONABLE_SET),
        "mode": eng.review_compose_mode(),
        "gate": gate,
        "refill": refill,
        "sample_1236": sample,
        "hard_db": hard,
        "pred_1237": hard["pred_1237"],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _write_md(doc)
    OUT_MD.write_text(md + "\n", encoding="utf-8")
    print(verdict, "pred_1237", hard["pred_1237"], flush=True)


if __name__ == "__main__":
    main()
