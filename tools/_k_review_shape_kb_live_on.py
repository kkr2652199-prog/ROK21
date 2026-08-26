# -*- coding: utf-8 -*-
"""K-REVIEW-SHAPE-KB-LIVE-ON — 4번 저울 라이브 ON 재검증.

형 GO. review만. 1237예측 없음. 몰아주기 없음. 자동화 없음.
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

from tools._k_review_shape_kb_wire import (  # noqa: E402
    GATE_HI,
    GATE_LO,
    ISO,
    SEED,
    _axis,
    _combo_ext,
    _m,
    _nums,
)

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260827_KREVIEW_SHAPE_KB_LIVE_ON.json"
OUT_MD = ROOT / "reports" / "20260827_KREVIEW_SHAPE_KB_LIVE_ON.md"
DB = ROOT / "data" / "lotto_testlotto.db"
SRC = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "draw_shape_kb.py"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _hard_db() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
        pred_1239 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239"
            ).fetchone()[0]
        )
    finally:
        conn.close()
    src = SRC.read_text(encoding="utf-8")
    return {
        "dmax": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "src_wire_true": "REVIEW_SHAPE_KB_WEIGHT_WIRE: bool = True" in src,
        "src_wire_false": "REVIEW_SHAPE_KB_WEIGHT_WIRE: bool = False" in src,
    }


def _smoke_1236() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.draw_shape_kb as kb
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    dno = 1236
    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    peek = max((int(d["draw_no"]) for d in draws), default=0) >= dno
    live = bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE)
    random.seed(SEED)
    pool = [
        c
        for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
        if str(c.get("brain_tag")) == "review"
    ]
    sets = [_nums(c) for c in pool]
    bonus_in = sum(1 for s in sets if len(s) != 6)
    bad_range = sum(1 for s in sets if any(n < 1 or n > 45 for n in s))
    return {
        "dno": dno,
        "live": live,
        "peek": peek,
        "n": len(sets),
        "bonus_in": bonus_in,
        "bad_range": bad_range,
        "sample1": sets[0] if sets else None,
        "ok": bool(live and not peek and len(sets) == 10 and bonus_in == 0 and bad_range == 0),
    }


def _gate_live() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.draw_shape_kb as kb
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.review_brain.draw_shape_kb import set_shape_score
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
    n_ok = peek_fail = size_bad = bonus_in = 0
    errors: list[str] = []
    changed = 0
    mets = {
        k: {x: [] for x in ("pref", "prize", "score", "rare", "run4")}
        for k in ("off", "on")
    }
    old = bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE)
    try:
        for i, r in enumerate(rows):
            dno = int(r["draw_no"])
            set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            if max((int(d["draw_no"]) for d in draws), default=0) >= dno:
                peek_fail += 1
                continue
            try:
                kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = False
                random.seed(SEED)
                p_off = [
                    c
                    for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
                    if str(c.get("brain_tag")) == "review"
                ]
                kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = True
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
            off_t = [tuple(_nums(s)) for s in p_off]
            on_t = [tuple(_nums(s)) for s in p_on]
            if off_t != on_t:
                changed += 1
            for t in off_t + on_t:
                if len(t) != 6:
                    bonus_in += 1
            pref_t = cs.prefer_table(draws, brain="markov")
            prize_t = cs.prize_table(draws, brain="review")
            hist = kb.summarize_before(draws)
            for name, p in (("off", p_off), ("on", p_on)):
                skill = [
                    _nums(s)
                    for s in sorted(
                        p, key=lambda x: int(x.get("pred_set_no") or x.get("set_no") or 0)
                    )[:5]
                ]
                ext = _combo_ext(skill)
                sc = [set_shape_score(s, hist) for s in skill if len(s) == 6]
                mets[name]["pref"].append(_axis(pref_t, p) or 0.0)
                mets[name]["prize"].append(_axis(prize_t, p) or 0.0)
                mets[name]["score"].append(mean(sc) if sc else 0.0)
                mets[name]["rare"].append(float(ext.get("p_rare_pass") or 0))
                mets[name]["run4"].append(float(ext.get("p_run4") or 0))
            n_ok += 1
            if (i + 1) % 20 == 0 or dno == GATE_HI:
                print(f"  [gate] {i+1}/{len(rows)} d={dno} n_ok={n_ok} ch={changed}", flush=True)
    finally:
        kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = old

    def pack(name: str) -> dict[str, Any]:
        m = mets[name]
        return {
            "prefer": _m(m["pref"]),
            "prize": _m(m["prize"]),
            "shape_score": _m(m["score"]),
            "p_rare_pass": _m(m["rare"]),
            "p_run4": _m(m["run4"]),
        }

    off, on = pack("off"), pack("on")
    d_pref = None if off["prefer"] is None else round(on["prefer"] - off["prefer"], 6)
    d_prize = None if off["prize"] is None else round(on["prize"] - off["prize"], 6)
    hard = (
        n_ok == 100
        and peek_fail == 0
        and size_bad == 0
        and not errors
        and bonus_in == 0
        and old is True
    )
    iso = bool(d_pref is not None and d_pref < ISO and d_prize is not None and d_prize < ISO)
    extreme_ok = bool(
        (on["p_rare_pass"] or 0) <= (off["p_rare_pass"] or 0) + 1e-12
        and (on["p_run4"] or 0) <= (off["p_run4"] or 0) + 1e-12
        and (off["p_rare_pass"] or 0) == (on["p_rare_pass"] or 0)
        and (off["p_run4"] or 0) == (on["p_run4"] or 0)
    )
    return {
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "n_ok": n_ok,
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "bonus_in_sets": bonus_in,
        "n_errors": len(errors),
        "errors_head": errors[:6],
        "changed": changed,
        "hard_ok": hard,
        "iso_ok": iso,
        "extreme_ok": extreme_ok,
        "off": off,
        "on": on,
        "delta_prefer": d_pref,
        "delta_prize": d_prize,
        "restored_live": bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE),
    }


def _write_md(doc: dict[str, Any]) -> str:
    g = doc["gate"]
    s = doc["smoke"]
    h = doc["hard"]
    return "\n".join(
        [
            "# K-REVIEW-SHAPE-KB-LIVE-ON (2026-08-27)",
            "",
            f"- **판정:** `{doc['verdict']}` · 4번 저울 라이브 ON · 몰아주기 미접촉",
            f"- 시각: {doc['ts']}",
            "- 형 GO: `REVIEW_SHAPE_KB_WEIGHT_WIRE=True`. review만. 자동화 아님.",
            f"- 근거: `{OUT_JSON.name}`",
            "",
            "## 라이브 플래그",
            "",
            f"- 소스 True `{h['src_wire_true']}` · 소스 False잔존 `{h['src_wire_false']}`",
            f"- 재검증 후 모듈 복원 `{g['restored_live']}`",
            "",
            "## 재검증 게이트 1137–1236 n100 (라이브 기본 ON 상태에서 OFF↔ON)",
            "",
            f"- HARD peek `{g['peek_fail']}` n_ok `{g['n_ok']}` size_bad `{g['size_bad']}` bonus_in `{g['bonus_in_sets']}` hard `{g['hard_ok']}`",
            f"- Δprefer `{g['delta_prefer']}` Δprize `{g['delta_prize']}` iso `{g['iso_ok']}`",
            f"- changed `{g['changed']}` · rare OFF `{g['off']['p_rare_pass']}` ON `{g['on']['p_rare_pass']}` · run4 OFF `{g['off']['p_run4']}` ON `{g['on']['p_run4']}` · extreme `{g['extreme_ok']}`",
            f"- elapsed `{g['elapsed_s']}`s",
            "",
            "## 1236 발권",
            "",
            f"- live `{s['live']}` n `{s['n']}` peek `{s['peek']}` bonus_in `{s['bonus_in']}` ok `{s['ok']}`",
            f"- sample1 `{s['sample1']}`",
            "",
            f"- pred_1237 `{h['pred_1237']}` · pred_1239 `{h['pred_1239']}` · MAX `{h['dmax']}`",
            "",
            "## 롤백",
            "",
            "- `REVIEW_SHAPE_KB_WEIGHT_WIRE=False`",
            "",
            "## 파일",
            "",
            "- `draw_shape_kb.py`",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )


def main() -> None:
    import app.testlotto.brains.review_brain.draw_shape_kb as kb

    if not kb.REVIEW_SHAPE_KB_WEIGHT_WIRE:
        raise SystemExit("live flag is False — set True before this tool")
    print("smoke 1236", flush=True)
    smoke = _smoke_1236()
    print(smoke, flush=True)
    print("gate", flush=True)
    gate = _gate_live()
    hard = _hard_db()
    live_after = bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE)
    verdict = (
        "APPLY_OK"
        if hard["src_wire_true"]
        and not hard["src_wire_false"]
        and live_after
        and gate["hard_ok"]
        and gate["iso_ok"]
        and gate["extreme_ok"]
        and smoke["ok"]
        and hard["pred_1237"] == 0
        and gate["restored_live"]
        else "HOLD"
    )
    doc = {
        "id": "K-REVIEW-SHAPE-KB-LIVE-ON",
        "ts": _now(),
        "verdict": verdict,
        "smoke": smoke,
        "gate": gate,
        "hard": hard,
        "repack": "untouched",
        "all_combos": "untouched",
        "automation": False,
        "predict": False,
        "live_wire": True,
        "rollback": "REVIEW_SHAPE_KB_WEIGHT_WIRE=False",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(verdict, "iso", gate["iso_ok"], "dpref", gate["delta_prefer"], flush=True)


if __name__ == "__main__":
    main()
