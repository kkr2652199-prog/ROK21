# -*- coding: utf-8 -*-
"""K-REVIEW-SHAPE-KB-CONSEC-NEUTRAL — 4번 저울 run 성분만 중립. 게이트 미달 시 롤백."""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.testlotto.brains.review_brain.draw_shape_kb as kb
from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before
from app.testlotto.features.draw_features import consecutive_pairs
from app.testlotto.learn_state_cutoff import set_learn_as_of

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260829_KREVIEW_SHAPE_KB_CONSEC_NEUTRAL.json"
OUT_MD = ROOT / "reports" / "20260829_KREVIEW_SHAPE_KB_CONSEC_NEUTRAL.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
SRC = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "draw_shape_kb.py"
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1137, 1236
SEED = 42
HI32 = frozenset(range(32, 46))
PREV_D_PRIZE = -0.00192
PREV_D_STRUCT = -0.005521
RUN2_MAX = 0.001
FLAG_TRUE = "REVIEW_SHAPE_KB_RUN_NEUTRAL: bool = True"
FLAG_FALSE = "REVIEW_SHAPE_KB_RUN_NEUTRAL: bool = False"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _run3_count(nums: list[int]) -> int:
    s = sorted(nums)
    n = 0
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[j] + 1:
            j += 1
        if j - i + 1 >= 3:
            n += 1
        i = j + 1
    return n


def _axis(table: dict[int, float], sets: list[list[int]]) -> float | None:
    if not table or not sets:
        return None
    uni = mean(table[i] for i in range(1, 46))
    vals = [mean(table[n] for n in nums) - uni for nums in sets if len(nums) == 6]
    return round(mean(vals), 6) if vals else None


def _pool_sets(dno: int, draws: list[dict], wire: bool) -> list[list[int]]:
    import app.testlotto.signal_pool as sp

    prev = bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE)
    kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = bool(wire)
    try:
        set_learn_as_of(dno)
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
    finally:
        kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = prev
    return [_nums(s) for s in pool if len(_nums(s)) == 6]


def _rollback() -> None:
    text = SRC.read_text(encoding="utf-8")
    if FLAG_TRUE not in text:
        raise RuntimeError("rollback flag missing")
    SRC.write_text(text.replace(FLAG_TRUE, FLAG_FALSE, 1), encoding="utf-8")
    kb.REVIEW_SHAPE_KB_RUN_NEUTRAL = False


def main() -> int:
    s0 = {
        "score_parts": ["odd_hist", "run_hist(max_run)", "sum_gauss", "span_gauss", "ac_gauss"],
        "consec_part": "run_hist keyed by max_run (1=무연속, 2=run2포함, 3+=run3)",
        "kept_after_patch": ["odd_hist", "sum", "span", "ac"],
        "neutralized": "run_hist / max_run",
        "WIRE": kb.REVIEW_SHAPE_KB_WEIGHT_WIRE,
        "RUN_NEUTRAL": kb.REVIEW_SHAPE_KB_RUN_NEUTRAL,
        "prize_table_untouched": True,
    }
    if not kb.REVIEW_SHAPE_KB_RUN_NEUTRAL or not kb.REVIEW_SHAPE_KB_WEIGHT_WIRE:
        raise RuntimeError("expected WIRE True and RUN_NEUTRAL True before gate")

    peek = 0
    n_ok = 0
    size_bad = 0
    bonus_in = 0
    acc: dict[str, dict[str, list[float]]] = {
        "off": {"prize": [], "struct": [], "run2": [], "run3": []},
        "on": {"prize": [], "struct": [], "run2": [], "run3": []},
    }
    for dno in range(LO, HI + 1):
        draws = _get_draws_before(dno)
        mx = max((int(d["draw_no"]) for d in draws), default=0)
        if mx >= dno:
            peek += 1
            continue
        prize = cs.prize_table(draws, brain="review")
        struct = cs.structural_unpopular_prior()
        off_sets = _pool_sets(dno, draws, False)
        on_sets = _pool_sets(dno, draws, True)
        for sets in (off_sets, on_sets):
            if len(sets) != 10:
                size_bad += 1
            for s in sets:
                if len(s) != 6:
                    size_bad += 1
                if any(n < 1 or n > 45 for n in s):
                    bonus_in += 1
        if len(off_sets) < 10 or len(on_sets) < 10:
            continue
        for tag, sets in (("off", off_sets), ("on", on_sets)):
            pa = _axis(prize, sets)
            st = _axis(struct, sets)
            if pa is not None:
                acc[tag]["prize"].append(pa)
            if st is not None:
                acc[tag]["struct"].append(st)
            acc[tag]["run2"].append(mean(consecutive_pairs(s) for s in sets))
            acc[tag]["run3"].append(mean(_run3_count(s) for s in sets))
        n_ok += 1
        if n_ok % 20 == 0:
            print(f"[NEUT] {dno} n={n_ok}", flush=True)

    def _summ(tag: str) -> dict[str, Any]:
        return {k: round(mean(vs), 6) if vs else None for k, vs in acc[tag].items()}

    off, on = _summ("off"), _summ("on")

    def _d(k: str) -> float | None:
        a, b = off.get(k), on.get(k)
        if a is None or b is None:
            return None
        return round(float(b) - float(a), 6)

    delta = {"prize": _d("prize"), "struct": _d("struct"), "run2": _d("run2"), "run3": _d("run3")}
    run2_ok = bool(delta["run2"] is not None and delta["run2"] <= RUN2_MAX)
    prize_ok = bool(delta["prize"] is not None and delta["prize"] >= PREV_D_PRIZE)
    struct_ok = bool(delta["struct"] is not None and delta["struct"] >= PREV_D_STRUCT)
    hard = {
        "peek0": peek == 0,
        "n100": n_ok == 100,
        "size_bad0": size_bad == 0,
        "bonus_in0": bonus_in == 0,
        "run2_le_001": run2_ok,
        "prize_not_worse": prize_ok,
        "struct_not_worse": struct_ok,
        "wire_true": kb.REVIEW_SHAPE_KB_WEIGHT_WIRE is True,
    }
    pass_ok = all(hard.values())
    rolled = False
    if pass_ok:
        verdict = "APPLY_OK"
        applied = True
    else:
        _rollback()
        rolled = True
        verdict = "SPEC_OK"
        applied = False

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    pred_1237 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0])
    pred_1239 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0])
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    conn.close()
    src = SRC.read_text(encoding="utf-8")

    payload = {
        "id": "K-REVIEW-SHAPE-KB-CONSEC-NEUTRAL",
        "as_of": _now(),
        "verdict": verdict,
        "applied": applied,
        "rolled_back": rolled,
        "apply": applied,
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "seed": SEED,
        "n": n_ok,
        "peek": peek,
        "s0": s0,
        "off": off,
        "on": on,
        "delta_on_minus_off": delta,
        "prev_delta": {"prize": PREV_D_PRIZE, "struct": PREV_D_STRUCT, "run2": 0.008},
        "hard": hard,
        "size_bad": size_bad,
        "bonus_in": bonus_in,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "draws_max": dmax,
        "src_run_neutral_true": FLAG_TRUE in src,
        "rollback": "REVIEW_SHAPE_KB_RUN_NEUTRAL=False",
    }
    lines = [
        "# K-REVIEW-SHAPE-KB-CONSEC-NEUTRAL",
        "",
        f"시각: {payload['as_of']} · **{verdict}** · 4번 WIRE True 유지 · prize표 미접촉 · 1237아님 · hits 금지",
        "목적=저울의 run_hist(연속) 가점만 중립. 합/폭/홀짝/AC 유지.",
        "",
        "## S0) 저울 성분",
        "",
        f"점수 부품: {s0['score_parts']}.",
        f"연속 성분=**{s0['consec_part']}**.",
        f"패치 후 유지={s0['kept_after_patch']} · 중립={s0['neutralized']}.",
        "롤백=`REVIEW_SHAPE_KB_RUN_NEUTRAL=False`.",
        "",
        "## S1) 패치",
        "",
        f"APPLY={'함' if applied else '안 함(롤백)' if rolled else '안 함'}. WIRE={kb.REVIEW_SHAPE_KB_WEIGHT_WIRE} · RUN_NEUTRAL 파일={FLAG_TRUE in src}.",
        "",
        "## S2) 게이트 1137–1236 n100 (4번 OFF↔ON, run중립 적용 상태)",
        "",
        "| 항 | OFF | ON | Δ(ON−OFF) | 기준 |",
        "|----|-----|-----|-----------|------|",
        f"| run2 | {off['run2']} | {on['run2']} | {delta['run2']} | ≤0.001 → {run2_ok} |",
        f"| run3 | {off['run3']} | {on['run3']} | {delta['run3']} | 모니터 |",
        f"| prize | {off['prize']} | {on['prize']} | {delta['prize']} | ≥{PREV_D_PRIZE} → {prize_ok} |",
        f"| struct | {off['struct']} | {on['struct']} | {delta['struct']} | ≥{PREV_D_STRUCT} → {struct_ok} |",
        "",
        f"peek={peek} · n={n_ok} · size_bad={size_bad} · bonus_in={bonus_in} · pred_1237={pred_1237} · MAX={dmax}.",
        "",
        "## 판정",
        "",
        f"**{verdict}**. 롤백실행={rolled}. 몰아주기/prize표/choices 미수정.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "delta": delta, "hard": hard, "rolled": rolled}, ensure_ascii=False))
    return 0 if verdict in ("APPLY_OK", "SPEC_OK") else 2


if __name__ == "__main__":
    raise SystemExit(main())
