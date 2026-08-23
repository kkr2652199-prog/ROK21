# -*- coding: utf-8 -*-
"""K-REVIEW-RARE-SLICE — 814만 극소형태 선별·표·금액뇌 1단계 거절.

당첨미입력. random.choices 라인 동결. 1237 신규예측 없음.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260823_KREVIEW_RARE_SLICE.json"
OUT_MD = ROOT / "reports" / "20260823_KREVIEW_RARE_SLICE.md"
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


def _pool(tag: str, draws, dno: int) -> list[dict]:
    import app.testlotto.signal_pool as sp

    random.seed(SEED)
    pool = sp.expand_pool(draws, dno, seed=SEED, brains=[tag])
    return [c for c in pool if str(c.get("brain_tag")) == tag]


def _gate() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.rare_slice as rs
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
    rare_off: list[float] = []
    rare_on: list[float] = []
    mets = {k: {x: [] for x in ("pref", "prize")} for k in ("off", "on")}
    old = bool(rs.REVIEW_RARE_SLICE_WIRE)
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
                rs.REVIEW_RARE_SLICE_WIRE = False
                p_off = _pool(TAG, draws, dno)
                rs.REVIEW_RARE_SLICE_WIRE = True
                p_on = _pool(TAG, draws, dno)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{dno} {type(e).__name__}: {e}")
                continue
            if len(p_off) != 10 or len(p_on) != 10:
                size_bad += 1
                continue
            if [_key(_nums(s)) for s in p_off] != [_key(_nums(s)) for s in p_on]:
                changed += 1
            pref_t = cs.prefer_table(draws, brain="markov")
            prize_t = cs.prize_table(draws, brain="review")
            for name, p in (("off", p_off), ("on", p_on)):
                mets[name]["pref"].append(_axis(pref_t, p) or 0.0)
                mets[name]["prize"].append(_axis(prize_t, p) or 0.0)
            rare_off.append(sum(1 for s in p_off if rs.is_step1_rare(_nums(s))))
            rare_on.append(sum(1 for s in p_on if rs.is_step1_rare(_nums(s))))
            n_ok += 1
            if (i + 1) % 20 == 0 or dno == GATE_HI:
                print(f"  [gate] {i+1}/{len(rows)} d={dno} n_ok={n_ok}", flush=True)
    finally:
        rs.REVIEW_RARE_SLICE_WIRE = old

    off = {"prefer": _m(mets["off"]["pref"]), "prize": _m(mets["off"]["prize"])}
    on = {"prefer": _m(mets["on"]["pref"]), "prize": _m(mets["on"]["prize"])}
    d_pref = None if off["prefer"] is None else round(on["prefer"] - off["prefer"], 6)
    d_prize = None if off["prize"] is None else round(on["prize"] - off["prize"], 6)
    hard = n_ok == (GATE_HI - GATE_LO + 1) and peek_fail == 0 and size_bad == 0 and not errors
    iso = bool(d_pref is not None and d_pref < ISO and d_prize is not None and d_prize < ISO)
    design = bool(changed >= 0 and _m(rare_on) is not None and _m(rare_off) is not None and _m(rare_on) <= _m(rare_off))
    apply = bool(hard and iso and design)
    return {
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "n_ok": n_ok,
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "n_errors": len(errors),
        "errors_head": errors[:6],
        "changed": changed,
        "rare_off": _m(rare_off),
        "rare_on": _m(rare_on),
        "hard_ok": hard,
        "iso_ok": iso,
        "design_ok": design,
        "apply": apply,
        "off": off,
        "on": on,
        "delta_prefer": d_pref,
        "delta_prize": d_prize,
    }


def _refill_review() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.rare_slice as rs
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.pool_view_cache import save_pool_view_cache_one

    rs.REVIEW_RARE_SLICE_WIRE = True
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
    return {"ok": ok, "fail": fail, "lo": REFILL_LO, "hi": REFILL_HI}


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


def _write_md(doc: dict[str, Any]) -> str:
    g = doc["gate"]
    rows = doc["table"]["rows"]
    lines = [
        "# K-REVIEW-RARE-SLICE (2026-08-23)",
        "",
        f"- **판정:** `{doc['verdict']}` · 금액뇌만 · 당첨미입력 · 1237 신규예측 없음",
        f"- 시각: {doc['ts']}",
        "- 형: 814만 전체조합에서 극소형태 선별저장. 로또조회 1–1237과 대조. 예측 전 사용.",
        f"- 근거: `{OUT_JSON.name}`",
        "",
        "## 조사 자료 (사람이 원한 것)",
        "",
        "개별 조합 확률은 모두 1/8,145,060. 갈라내는 것은 **얇은 형태 조각**.",
        "표=`rare_slice.summarize()` · 814만 전수 + 당첨 1237.",
        "",
        "| 형태 | 814만 개수 | 공간비 | 당첨1–1237 | 널E | 1단계거절 |",
        "|------|-----------:|-------:|-----------:|-----:|:----------:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['key']} | {r['space']} | {r['p_space']:.6f} | {r['draws']} | {r['null_e']} | {'Y' if r['step1_reject'] else ''} |"
        )
    lines.extend(
        [
            "",
            "## 1단계 거절",
            "",
            "- arith6(180) · gap8(210) · split_l3h3(14400) · zone_1_15(5005) · run5/6 · exact 1-2-3-43-44-45",
            "- 1237에서 **0회**. run4·전홀짝은 당첨이 있어서 이번엔 안 자름(tier1이 일부 담당)",
            "- split_l3h3 널E **2.187** · 0회는 가능(포아송). 우열 아님",
            "",
            "## 게이트 1137–1236 n100",
            "",
            f"- HARD `{g['hard_ok']}` peek **{g['peek_fail']}** size {g['size_bad']} err {g['n_errors']} {g['elapsed_s']}s · 변경 {g['changed']}",
            f"- off prefer/prize `{g['off']['prefer']}` / `{g['off']['prize']}` rare장 `{g['rare_off']}`",
            f"- on  `{g['on']['prefer']}` / `{g['on']['prize']}` rare장 `{g['rare_on']}`",
            f"- Δprefer `{g['delta_prefer']}` Δprize `{g['delta_prize']}`",
            f"- iso `{g['iso_ok']}` design `{g['design_ok']}` apply `{g['apply']}`",
            "",
            f"- WIRE `{doc['wire']}` · refill `{doc.get('refill')}` · catalog `{doc.get('catalog')}`",
            "- 롤백=`REVIEW_RARE_SLICE_WIRE=False`",
            "- 우열금지 · 다음단계는 형 1건",
            "",
            "## 파일",
            "",
            "- `app/testlotto/brains/review_brain/rare_slice.py` · `engine.py`",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    from app.testlotto.brains.review_brain.rare_slice import summarize
    from app.testlotto.rare_bundle_store import run_full_survey

    print("refresh rare_bundle catalog+hits 1-1237", flush=True)
    catalog = run_full_survey()
    print(catalog.get("summary"), flush=True)

    print("gate 1137-1236 n100", flush=True)
    gate = _gate()
    print(
        json.dumps(
            {k: gate[k] for k in ("n_ok", "peek_fail", "iso_ok", "design_ok", "apply", "changed", "delta_prefer", "delta_prize", "rare_off", "rare_on")},
            ensure_ascii=False,
        ),
        flush=True,
    )

    import app.testlotto.brains.review_brain.rare_slice as rs

    refill = None
    if gate["apply"]:
        print("refill review 1037-1236", flush=True)
        refill = _refill_review()
    rs.REVIEW_RARE_SLICE_WIRE = True

    hard = _hard_db()
    verdict = (
        "APPLY_OK"
        if gate["apply"] and refill and refill.get("fail") == 0
        else ("HOLD_ISO" if gate["hard_ok"] and not gate["iso_ok"] else "HOLD")
    )
    doc = {
        "id": "K-REVIEW-RARE-SLICE",
        "ts": _now(),
        "verdict": verdict,
        "wire": bool(rs.REVIEW_RARE_SLICE_WIRE),
        "table": summarize(),
        "gate": gate,
        "refill": refill,
        "catalog": catalog.get("summary"),
        "catalog_n": catalog.get("catalog_saved"),
        "hits_n": catalog.get("hits_saved"),
        "hard_db": hard,
        "pred_1237": hard["pred_1237"],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(verdict, "pred_1237", hard["pred_1237"], flush=True)


if __name__ == "__main__":
    main()
