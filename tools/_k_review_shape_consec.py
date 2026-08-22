# -*- coding: utf-8 -*-
"""K-REVIEW-SHAPE-CONSEC — 1~1237 당첨 연번 vs 금액뇌 벡터. 첫 패치=3연속 능선평탄.

널 E[연번쌍]=0.6667. 당첨 미입력. 표는 draws_before만. 게이트 1137–1236.
1237 신규예측 없음.
"""
from __future__ import annotations

import json
import random
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.review_brain.shape_table import (  # noqa: E402
    max_run,
    summarize,
)
from app.testlotto.features.draw_features import consecutive_pairs  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260822_KREVIEW_SHAPE_CONSEC.json"
OUT_MD = ROOT / "reports" / "20260822_KREVIEW_SHAPE_CONSEC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
SHAPE_SRC = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "shape_table.py"
DB = ROOT / "data" / "lotto_testlotto.db"
ISO = 0.005
SEED = 42
GATE_LO, GATE_HI = 1137, 1236
NULL_E_PAIRS = 0.6667


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _m(xs: list[float]) -> float | None:
    return round(mean(xs), 6) if xs else None


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


def _combo_stats(sets: list[list[int]]) -> dict[str, Any]:
    if not sets:
        return {}
    pairs = [consecutive_pairs(s) for s in sets]
    runs = [max_run(s) for s in sets]
    return {
        "n": len(sets),
        "mean_pairs": round(mean(pairs), 6),
        "p_pair": round(sum(1 for p in pairs if p >= 1) / len(sets), 6),
        "p_run3": round(sum(1 for r in runs if r >= 3) / len(sets), 6),
        "p_run4": round(sum(1 for r in runs if r >= 4) / len(sets), 6),
        "p_run6": round(sum(1 for r in runs if r >= 6) / len(sets), 6),
        "max_run_max": max(runs),
    }


def _draws_actual() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT draw_no, num1,num2,num3,num4,num5,num6 FROM lotto_draws "
            "WHERE draw_no BETWEEN 1 AND 1237 ORDER BY draw_no"
        ).fetchall()
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
        n_cache = int(
            conn.execute(
                "SELECT COUNT(*) FROM testlotto_pool_view_cache WHERE brain='review' "
                "AND draw_no BETWEEN 1037 AND 1236"
            ).fetchone()[0]
        )
        cache_rows = conn.execute(
            "SELECT draw_no, pool_json FROM testlotto_pool_view_cache "
            "WHERE brain='review' AND draw_no BETWEEN 1037 AND 1236"
        ).fetchall()
    finally:
        conn.close()
    sets = [
        sorted(int(r[f"num{i}"]) for i in range(1, 7)) for r in rows
    ]
    draws = [
        {
            "draw_no": int(r["draw_no"]),
            **{f"num{i}": int(r[f"num{i}"]) for i in range(1, 7)},
        }
        for r in rows
    ]
    skill: list[list[int]] = []
    all10: list[list[int]] = []
    for cr in cache_rows:
        pool = json.loads(cr["pool_json"] or "[]")
        psets = [_nums(s) for s in sorted(pool, key=lambda x: int(x.get("set_no") or 0))]
        if len(psets) >= 5:
            skill.extend(psets[:5])
        all10.extend(psets)
    return {
        "dmax": dmax,
        "pred_1237": pred_1237,
        "n_draws": len(sets),
        "n_cache": n_cache,
        "actual": _combo_stats(sets),
        "actual_table": summarize(draws),
        "review_skill5": _combo_stats(skill),
        "review_pool10": _combo_stats(all10),
    }


def _set_wire(on: bool) -> None:
    text = SHAPE_SRC.read_text(encoding="utf-8")
    text2, n = re.subn(
        r"REVIEW_SHAPE_WIRE: bool = (True|False)",
        f"REVIEW_SHAPE_WIRE: bool = {on}",
        text,
        count=1,
    )
    if n != 1:
        raise RuntimeError(f"wire replace n={n}")
    SHAPE_SRC.write_text(text2, encoding="utf-8")


def _gate() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.shape_table as st
    import app.testlotto.signal_pool as sp
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
    mets = {k: {x: [] for x in ("pref", "prize", "pairs", "run3")} for k in ("off", "on")}
    old = bool(st.REVIEW_SHAPE_WIRE)
    try:
        for i, r in enumerate(rows):
            dno = int(r["draw_no"])
            set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            if max((int(d["draw_no"]) for d in draws), default=0) >= dno:
                peek_fail += 1
                continue
            try:
                st.REVIEW_SHAPE_WIRE = False
                random.seed(SEED)
                p_off = [
                    c
                    for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
                    if str(c.get("brain_tag")) == "review"
                ]
                st.REVIEW_SHAPE_WIRE = True
                random.seed(SEED)
                p_on = [
                    c
                    for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
                    if str(c.get("brain_tag")) == "review"
                ]
            except Exception as e:  # noqa: BLE001
                errors.append(f"{dno} {type(e).__name__}: {e}")
                continue
            if len(p_off) != 10 or len(p_on) != 10:
                size_bad += 1
                continue
            if [tuple(_nums(s)) for s in p_off] != [tuple(_nums(s)) for s in p_on]:
                changed += 1
            pref_t = cs.prefer_table(draws, brain="markov")
            prize_t = cs.prize_table(draws, brain="review")
            for name, p in (("off", p_off), ("on", p_on)):
                skill = [
                    _nums(s)
                    for s in sorted(p, key=lambda x: int(x.get("pred_set_no") or x.get("set_no") or 0))[:5]
                ]
                cs_ = _combo_stats(skill)
                mets[name]["pref"].append(_axis(pref_t, p) or 0.0)
                mets[name]["prize"].append(_axis(prize_t, p) or 0.0)
                mets[name]["pairs"].append(float(cs_.get("mean_pairs") or 0))
                mets[name]["run3"].append(float(cs_.get("p_run3") or 0))
            n_ok += 1
            if (i + 1) % 20 == 0 or dno == GATE_HI:
                print(f"  [gate] {i+1}/{len(rows)} d={dno} n_ok={n_ok} ch={changed}", flush=True)
    finally:
        st.REVIEW_SHAPE_WIRE = old

    def pack(name: str) -> dict[str, Any]:
        m = mets[name]
        return {
            "prefer": _m(m["pref"]),
            "prize": _m(m["prize"]),
            "mean_pairs": _m(m["pairs"]),
            "p_run3": _m(m["run3"]),
        }

    off, on = pack("off"), pack("on")
    d_pref = None if off["prefer"] is None else round(on["prefer"] - off["prefer"], 6)
    d_prize = None if off["prize"] is None else round(on["prize"] - off["prize"], 6)
    hard = n_ok == 100 and peek_fail == 0 and size_bad == 0 and not errors
    iso = bool(d_pref is not None and d_pref < ISO and d_prize is not None and d_prize < ISO)
    design = bool(changed > 0)
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
        "apply": bool(hard and iso and design),
        "off": off,
        "on": on,
        "delta_prefer": d_pref,
        "delta_prize": d_prize,
        "delta_pairs": None
        if off["mean_pairs"] is None
        else round(on["mean_pairs"] - off["mean_pairs"], 6),
        "delta_run3": None if off["p_run3"] is None else round(on["p_run3"] - off["p_run3"], 6),
    }


def _refill() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.pool_view_cache import save_pool_view_cache_one

    ok = fail = 0
    for dno in range(1037, 1237):
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        try:
            random.seed(SEED)
            pool = sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
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
                    "brain_tag": "review",
                    "kind": "pool",
                    **({"role": c.get("role")} if c.get("role") else {}),
                    **({"source": c.get("source")} if c.get("source") else {}),
                }
                for c in (pool_br.get("review") or [])
            ]
            r = [
                {
                    "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
                    "nums": _nums(c),
                    "brain_tag": "review",
                    "kind": "repack",
                    "assemble": c.get("assemble") or "",
                }
                for c in rows
                if str(c.get("brain_tag")) == "review"
            ]
            save_pool_view_cache_one(
                dno,
                "review",
                {"pool_by_brain": {"review": p}, "repack_by_brain": {"review": r}, "seed": SEED},
            )
            ok += 1
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"  refill fail {dno} {type(e).__name__}: {e}", flush=True)
        if dno % 40 == 0 or dno == 1236:
            print(f"  [refill] {dno} ok={ok} fail={fail}", flush=True)
    return {"ok": ok, "fail": fail}


def _write_md(doc: dict[str, Any]) -> str:
    a = doc["census"]
    g = doc["gate"]
    return "\n".join(
        [
            "# K-REVIEW-SHAPE-CONSEC (2026-08-22)",
            "",
            f"- **판정:** `{doc['verdict']}` · 금액뇌만 · 당첨미입력 · 1237 신규예측 없음",
            f"- 시각: {doc['ts']}",
            "- 형: 붙는 번호(1-2-3-4-5-6류)가 814만 중 극소. 1~1237 당첨 패턴을 뇌가 예측 전 읽게.",
            f"- 근거: `{OUT_JSON.name}`",
            "",
            "## 당첨 1~1237 (실측)",
            "",
            f"- n **{a['n_draws']}** · MAX `{a['dmax']}` · pred_1237 **{a['pred_1237']}** · 금액뇌캐시1037-1236 `{a['n_cache']}`",
            f"- 널 E[연번쌍] **{NULL_E_PAIRS}** (44×C(43,4)/C(45,6))",
            "",
            "| | n | 연번쌍평균 | 연번≥1 | run≥3 | run≥4 | run=6 |",
            "|--|---|------------|--------|-------|-------|-------|",
            f"| 당첨 1–1237 | {a['actual'].get('n')} | {a['actual'].get('mean_pairs')} | {a['actual'].get('p_pair')} | {a['actual'].get('p_run3')} | {a['actual'].get('p_run4')} | {a['actual'].get('p_run6')} |",
            f"| 금액뇌 skill1–5 | {a['review_skill5'].get('n')} | {a['review_skill5'].get('mean_pairs')} | {a['review_skill5'].get('p_pair')} | {a['review_skill5'].get('p_run3')} | {a['review_skill5'].get('p_run4')} | {a['review_skill5'].get('p_run6')} |",
            f"| 금액뇌 pool10 | {a['review_pool10'].get('n')} | {a['review_pool10'].get('mean_pairs')} | {a['review_pool10'].get('p_pair')} | {a['review_pool10'].get('p_run3')} | {a['review_pool10'].get('p_run4')} | {a['review_pool10'].get('p_run6')} |",
            "",
            f"- 당첨표 as_of `{a['actual_table'].get('as_of')}` hist `{a['actual_table'].get('max_run_hist')}`",
            "- 6연속(1–6류)은 당첨·예측 모두 극소/0이 정상. tier1이 이미 run≥4 탈락.",
            "",
            "## 첫 패치",
            "",
            "`shape_table.summarize(draws_before)` 를 예측 전 읽고,",
            "가중치에서 3연속 고질량 구간의 가운데를 ×0.75 (random.choices 전).",
            "",
            "## 게이트 1137–1236 n100",
            "",
            f"- HARD `{g['hard_ok']}` peek **{g['peek_fail']}** size {g['size_bad']} err {g['n_errors']} {g['elapsed_s']}s · 변경 {g['changed']}",
            f"- off prefer/prize `{g['off']['prefer']}` / `{g['off']['prize']}` pairs `{g['off']['mean_pairs']}` run3 `{g['off']['p_run3']}`",
            f"- on  `{g['on']['prefer']}` / `{g['on']['prize']}` pairs `{g['on']['mean_pairs']}` run3 `{g['on']['p_run3']}`",
            f"- Δprefer `{g['delta_prefer']}` Δprize `{g['delta_prize']}` Δpairs `{g['delta_pairs']}` Δrun3 `{g['delta_run3']}`",
            f"- iso `{g['iso_ok']}` design `{g['design_ok']}` apply `{g['apply']}`",
            "",
            f"- WIRE `{doc['wire']}` · refill `{doc.get('refill')}`",
            "- 롤백=`REVIEW_SHAPE_WIRE=False`",
            "- 우열금지 · 다음 패치(간격/홀짝/구간)는 형 확인 후 1건",
            "",
            "## 파일",
            "",
            "- `app/testlotto/brains/review_brain/shape_table.py` · `engine.py`",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
            "",
        ]
    )


def main() -> None:
    print("census draws+review cache...", flush=True)
    census = _draws_actual()
    print(
        f"  actual pairs={census['actual'].get('mean_pairs')} run3={census['actual'].get('p_run3')} "
        f"review5 pairs={census['review_skill5'].get('mean_pairs')} run3={census['review_skill5'].get('p_run3')}",
        flush=True,
    )
    print("gate...", flush=True)
    gate = _gate()
    print(f"  apply={gate['apply']} ch={gate['changed']}", flush=True)
    refill = {"skipped": True}
    wire = False
    if gate["apply"]:
        _set_wire(True)
        wire = True
        print("APPLY refill 1037-1236...", flush=True)
        refill = _refill()
    else:
        _set_wire(False)
    verdict = (
        "APPLY_OK"
        if gate["apply"]
        else (
            "HOLD_ISO_FAIL"
            if gate["hard_ok"] and not gate["iso_ok"]
            else ("HOLD_NO_DESIGN" if gate["hard_ok"] else "FAIL")
        )
    )
    doc = {
        "id": "K-REVIEW-SHAPE-CONSEC",
        "ts": _now(),
        "verdict": verdict,
        "census": census,
        "gate": gate,
        "wire": wire,
        "refill": refill,
        "null_e_pairs": NULL_E_PAIRS,
        "pred_1237_new": False,
    }
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _write_md(doc)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(verdict, flush=True)


if __name__ == "__main__":
    main()
