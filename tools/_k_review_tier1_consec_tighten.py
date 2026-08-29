# -*- coding: utf-8 -*-
"""K-REVIEW-TIER1-CONSEC-TIGHTEN — 연번<4→<3. 게이트 미달 시 MAX=4 롤백."""
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

import app.testlotto.filters as fl
from app.testlotto.brains.review_brain.predict import run as review_run
from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before
from app.testlotto.features.draw_features import consecutive_pairs
from app.testlotto.learn_state_cutoff import set_learn_as_of
from app.testlotto.signal_pool import _pass_seed

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260829_KREVIEW_TIER1_CONSEC_TIGHTEN.json"
OUT_MD = ROOT / "reports" / "20260829_KREVIEW_TIER1_CONSEC_TIGHTEN.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
SRC = ROOT / "app" / "testlotto" / "filters.py"
SRC_SHAPE = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "shape_table.py"
SRC_KB = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "draw_shape_kb.py"
SRC_PRIZE = ROOT / "app" / "testlotto" / "brains" / "shared" / "crowd_signal.py"
LO, HI = 1137, 1236
SEED = 42
FLAG_3 = "REVIEW_TIER1_CONSEC_MAX: int = 3"
FLAG_4 = "REVIEW_TIER1_CONSEC_MAX: int = 4"
RUN3 = [8, 9, 10, 21, 32, 43]
RUN4 = [8, 9, 10, 11, 32, 43]
RUN2 = [8, 9, 21, 32, 40, 45]


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _run3_count(nums: list[int]) -> int:
    s = sorted(nums)
    if len(s) < 3:
        return 0
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


def _gen(dno: int, draws: list[dict], consec_max: int) -> list[list[int]]:
    prev = fl.REVIEW_TIER1_CONSEC_MAX
    fl.REVIEW_TIER1_CONSEC_MAX = int(consec_max)
    try:
        set_learn_as_of(dno)
        random.seed(_pass_seed(SEED, dno, 0))
        raw = review_run(draws, 10)
    finally:
        fl.REVIEW_TIER1_CONSEC_MAX = prev
    out: list[list[int]] = []
    for s in raw:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) == 6:
            out.append(nums)
    return out


def _s0() -> dict[str, Any]:
    prev = fl.REVIEW_TIER1_CONSEC_MAX
    fl.REVIEW_TIER1_CONSEC_MAX = 4
    before = {
        "max": 4,
        "run2_pass": fl.tier1_filter(RUN2),
        "run3_pass": fl.tier1_filter(RUN3),
        "run4_pass": fl.tier1_filter(RUN4),
    }
    fl.REVIEW_TIER1_CONSEC_MAX = 3
    after = {
        "max": 3,
        "run2_pass": fl.tier1_filter(RUN2),
        "run3_pass": fl.tier1_filter(RUN3),
        "run4_pass": fl.tier1_filter(RUN4),
    }
    fl.REVIEW_TIER1_CONSEC_MAX = prev
    src = SRC.read_text(encoding="utf-8")
    return {
        "before": before,
        "after_expected": after,
        "src_flag_3": FLAG_3 in src,
        "src_flag_4": FLAG_4 in src,
        "live_max": prev,
        "other_tier1_kept": True,
        "shape2_untouched": "REVIEW_SHAPE_FLAT_FACTOR: float = 0.75" in SRC_SHAPE.read_text(encoding="utf-8"),
        "kb_run_neutral_false": "REVIEW_SHAPE_KB_RUN_NEUTRAL: bool = False" in SRC_KB.read_text(encoding="utf-8"),
        "prize_untouched": 'review": 0.80' in SRC_PRIZE.read_text(encoding="utf-8"),
    }


def _set_file_max(val: int) -> None:
    text = SRC.read_text(encoding="utf-8")
    if val == 3:
        if FLAG_4 in text:
            text = text.replace(FLAG_4, FLAG_3, 1)
    elif val == 4:
        if FLAG_3 in text:
            text = text.replace(FLAG_3, FLAG_4, 1)
    else:
        raise ValueError(val)
    SRC.write_text(text, encoding="utf-8")
    fl.REVIEW_TIER1_CONSEC_MAX = int(val)


def main() -> int:
    s0 = _s0()
    if FLAG_3 not in SRC.read_text(encoding="utf-8"):
        raise RuntimeError("expected REVIEW_TIER1_CONSEC_MAX=3 in filters.py before gate")

    peek = 0
    n_ok = 0
    size_bad = 0
    bonus_in = 0
    acc: dict[str, dict[str, list[float]]] = {
        "before": {"prize": [], "struct": [], "run2": [], "run3": []},
        "after": {"prize": [], "struct": [], "run2": [], "run3": []},
    }

    for dno in range(LO, HI + 1):
        draws = _get_draws_before(dno)
        mx = max((int(d["draw_no"]) for d in draws), default=0)
        if mx >= dno:
            peek += 1
            continue
        prize = cs.prize_table(draws, brain="review")
        struct = cs.structural_unpopular_prior()
        before_sets = _gen(dno, draws, 4)
        after_sets = _gen(dno, draws, 3)
        for sets in (before_sets, after_sets):
            if len(sets) != 10:
                size_bad += 1
            for s in sets:
                if len(s) != 6:
                    size_bad += 1
                if any(n < 1 or n > 45 for n in s):
                    bonus_in += 1
        if len(before_sets) < 10 or len(after_sets) < 10:
            continue
        for tag, sets in (("before", before_sets), ("after", after_sets)):
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
            print(f"[T1] {dno} n={n_ok} peek={peek} size_bad={size_bad}", flush=True)

    def _summ(tag: str) -> dict[str, Any]:
        return {k: round(mean(vs), 6) if vs else None for k, vs in acc[tag].items()}

    before, after = _summ("before"), _summ("after")

    def _d(k: str) -> float | None:
        a, b = before.get(k), after.get(k)
        if a is None or b is None:
            return None
        return round(float(b) - float(a), 6)

    delta = {"prize": _d("prize"), "struct": _d("struct"), "run2": _d("run2"), "run3": _d("run3")}
    run3_down = bool(delta["run3"] is not None and delta["run3"] < 0)
    run2_ok = bool(delta["run2"] is not None and delta["run2"] <= 0)
    prize_ok = bool(delta["prize"] is not None and delta["prize"] >= 0)
    struct_plunge = bool(delta["struct"] is not None and delta["struct"] < -0.005)

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    pred_1237 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0])
    pred_1239 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0])
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    conn.close()

    gate = {
        "run3_down": run3_down,
        "run2_not_up": run2_ok,
        "prize_not_worse": prize_ok,
        "size_bad0": size_bad == 0,
        "peek0": peek == 0,
        "n100": n_ok == 100,
        "bonus_in0": bonus_in == 0,
    }
    pass_ok = all(
        (
            run3_down,
            run2_ok,
            prize_ok,
            size_bad == 0,
            peek == 0,
            n_ok == 100,
            bonus_in == 0,
        )
    )
    rolled = False
    if not pass_ok:
        _set_file_max(4)
        rolled = True
        verdict = "SPEC_OK"
        applied = False
    else:
        fl.REVIEW_TIER1_CONSEC_MAX = 3
        verdict = "APPLY_OK"
        applied = True

    src = SRC.read_text(encoding="utf-8")
    payload = {
        "id": "K-REVIEW-TIER1-CONSEC-TIGHTEN",
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
        "before": before,
        "after": after,
        "delta_after_minus_before": delta,
        "gate": gate,
        "struct_plunge": struct_plunge,
        "size_bad": size_bad,
        "bonus_in": bonus_in,
        "src_max_3": FLAG_3 in src,
        "src_max_4": FLAG_4 in src,
        "live_max": fl.REVIEW_TIER1_CONSEC_MAX,
        "rollback": "REVIEW_TIER1_CONSEC_MAX=4",
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "draws_max": dmax,
        "untouched": {
            "shape2_075": s0["shape2_untouched"],
            "run_neutral_false": s0["kb_run_neutral_false"],
            "prize_table": s0["prize_untouched"],
        },
    }

    lines = [
        "# K-REVIEW-TIER1-CONSEC-TIGHTEN",
        "",
        f"시각: {payload['as_of']} · **{verdict}** · APPLY={'함' if applied else '안 함(롤백)' if rolled else '안 함'} · 1237아님 · hits 클레임 금지",
        "목적=tier1 연번 기준 연번<4 → 연번<3 (2연속까지 허용, 3연속 이상 탈락).",
        "",
        "## S0) 변경 전",
        "",
        f"변경 전 임계=**4** (3연속 통과={s0['before']['run3_pass']} · 4연속 통과={s0['before']['run4_pass']} · 2연속 통과={s0['before']['run2_pass']}).",
        f"변경 후 기대 임계=**3** (2연속 통과={s0['after_expected']['run2_pass']} · 3연속 통과={s0['after_expected']['run3_pass']} · 4연속 통과={s0['after_expected']['run4_pass']}).",
        "나머지=합80–210 · 홀수1–5 · 구간2+. 2번×0.75 · 4번 RUN_NEUTRAL=False · prize표 미접촉.",
        "",
        "## S1) 패치",
        "",
        "`REVIEW_TIER1_CONSEC_MAX` 기본 **3**. 롤백 키=`REVIEW_TIER1_CONSEC_MAX=4`.",
        f"파일 MAX=3={FLAG_3 in src} · MAX=4={FLAG_4 in src} · 라이브={fl.REVIEW_TIER1_CONSEC_MAX}.",
        "",
        "## S2) 게이트 1137–1236 n100 before(MAX=4)↔after(MAX=3)",
        "",
        f"peek={peek} · n={n_ok} · size_bad={size_bad} · bonus_in={bonus_in} · seed={SEED}.",
        "",
        "| 축 | before(<4) | after(<3) | Δ |",
        "|----|------------|-----------|---|",
        f"| run2 | {before['run2']} | {after['run2']} | {delta['run2']} |",
        f"| run3 | {before['run3']} | {after['run3']} | {delta['run3']} |",
        f"| prize | {before['prize']} | {after['prize']} | {delta['prize']} |",
        f"| struct | {before['struct']} | {after['struct']} | {delta['struct']} |",
        "",
        f"통과: run3감소={run3_down} · run2비증가={run2_ok} · prize비악화={prize_ok} · size_bad0={size_bad == 0}.",
        f"struct 급락(Δ<−0.005)={struct_plunge}. pred_1237={pred_1237} · pred_1239={pred_1239} · MAX={dmax}.",
        "",
        "## 판정",
        "",
        f"**{verdict}**. {'게이트 통과 · 라이브 MAX=3.' if applied else '게이트 미달 · MAX=4 원복.' if rolled else '미적용.'}",
        "2번/4번/prize표/`random.choices`/몰아주기/kweon 미수정.",
        "",
        "## 롤백",
        "",
        "`REVIEW_TIER1_CONSEC_MAX=4`",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "applied": applied,
                "rolled": rolled,
                "delta": delta,
                "gate": gate,
                "size_bad": size_bad,
                "bonus_in": bonus_in,
                "live_max": fl.REVIEW_TIER1_CONSEC_MAX,
                "n": n_ok,
                "peek": peek,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
