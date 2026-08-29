# -*- coding: utf-8 -*-
"""K-REVIEW-CONSEC-ROOT-AND-PRIZE-ISOLATE — 진단 전용. APPLY 금지.

READ-ONLY: 엔진/플래그 파일·DB write 없음. 메모리 패치 후 복원.
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.testlotto.brains.review_brain.draw_shape_kb as kb
import app.testlotto.brains.review_brain.engine as eng
import app.testlotto.brains.review_brain.shape_table as shape_table
from app.testlotto.brains.review_brain.kb7_future import collect_before
from app.testlotto.brains.review_brain.predict import run as review_run
from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before
from app.testlotto.features.draw_features import consecutive_pairs
from app.testlotto.filters import tier1_filter as TIER1_LIVE
from app.testlotto.learn_state_cutoff import set_learn_as_of
from app.testlotto.signal_pool import _pass_seed

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260829_KREVIEW_CONSEC_ROOT_AND_PRIZE_ISOLATE.json"
OUT_MD = ROOT / "reports" / "20260829_KREVIEW_CONSEC_ROOT_AND_PRIZE_ISOLATE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1137, 1236
SEED = 42
PREV_BRANCHED = {"prize": -0.00192, "struct": -0.005521}
SRC_FILTER = ROOT / "app" / "testlotto" / "filters.py"
SRC_SHAPE = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "shape_table.py"
SRC_KB = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "draw_shape_kb.py"
SRC_PRIZE = ROOT / "app" / "testlotto" / "brains" / "shared" / "crowd_signal.py"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _max_consec(nums: list[int]) -> int:
    s = sorted(int(x) for x in nums)
    if not s:
        return 0
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def _tier1_reject_at(reject_at: int) -> Callable[[list[int]], bool]:
    def _f(nums: list[int]) -> bool:
        s = sum(nums)
        odd_count = sum(1 for n in nums if n % 2 == 1)
        ranges_hit = len({(n - 1) // 10 for n in nums})
        if s < 80 or s > 210:
            return False
        if odd_count == 0 or odd_count == 6:
            return False
        if ranges_hit <= 1:
            return False
        if _max_consec(nums) >= reject_at:
            return False
        return True

    return _f


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


def _shape(sets: list[list[int]]) -> dict[str, float | None]:
    if not sets:
        return {"run2": None, "run3": None, "n_sets": 0}
    return {
        "run2": round(mean(consecutive_pairs(s) for s in sets), 6),
        "run3": round(mean(_run3_count(s) for s in sets), 6),
        "n_sets": len(sets),
    }


def _keep_isolated(nums: list[int], hist: dict[str, Any] | None, rng: random.Random) -> bool:
    if not hist or not hist.get("n"):
        return True
    score = kb.set_shape_score(nums, hist)
    p = 0.45 + 0.55 * score
    return rng.random() <= p


def _metrics(prize, struct, sets: list[list[int]]) -> dict[str, Any]:
    sh = _shape(sets)
    return {
        "prize": _axis(prize, sets),
        "struct": _axis(struct, sets),
        "run2": sh["run2"],
        "run3": sh["run3"],
        "n_sets": sh["n_sets"],
    }


class _Patch:
    """메모리만. 파일 플래그 불변."""

    def __init__(self, reject_at: int = 4, flatten: float = 0.75, kb_wire: bool = True) -> None:
        self.reject_at = reject_at
        self.flatten = flatten
        self.kb_wire = kb_wire
        self._old: dict[str, Any] = {}

    def __enter__(self) -> "_Patch":
        orig_flat = shape_table.apply_consec_flatten
        fac = float(self.flatten)

        def _flat(weights, *, factor=fac):
            return orig_flat(weights, factor=factor)

        self._old = {
            "eng_t1": eng.tier1_filter,
            "flat": shape_table.apply_consec_flatten,
            "wire": bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE),
        }
        eng.tier1_filter = _tier1_reject_at(self.reject_at)
        shape_table.apply_consec_flatten = _flat
        kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = bool(self.kb_wire)
        return self

    def __exit__(self, *a: object) -> None:
        eng.tier1_filter = self._old["eng_t1"]
        shape_table.apply_consec_flatten = self._old["flat"]
        kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = self._old["wire"]


def _gen(draws: list[dict], dno: int, n_sets: int, **kw: Any) -> list[list[int]]:
    set_learn_as_of(dno)
    with _Patch(**kw):
        random.seed(_pass_seed(SEED, dno, 0))
        raw = review_run(draws, n_sets)
    out: list[list[int]] = []
    for s in raw:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) == 6:
            out.append(nums)
    return out


def _mean_acc(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0, "prize": None, "struct": None, "run2": None, "run3": None}
    out: dict[str, Any] = {"n": len(rows)}
    for k in ("prize", "struct", "run2", "run3"):
        vs = [float(r[k]) for r in rows if r.get(k) is not None]
        out[k] = round(mean(vs), 6) if vs else None
    return out


def _d(a: dict[str, Any], b: dict[str, Any], key: str) -> float | None:
    x, y = a.get(key), b.get(key)
    if x is None or y is None:
        return None
    return round(float(y) - float(x), 6)


def _s0() -> dict[str, Any]:
    live = TIER1_LIVE([8, 9, 10, 21, 32, 43])
    live_run4 = TIER1_LIVE([8, 9, 10, 11, 32, 43])
    src_f = SRC_FILTER.read_text(encoding="utf-8")
    src_s = SRC_SHAPE.read_text(encoding="utf-8")
    src_k = SRC_KB.read_text(encoding="utf-8")
    src_p = SRC_PRIZE.read_text(encoding="utf-8")
    return {
        "tier1_rule": "max_consec >= 4 탈락 → 연번<4 (3연속까지 허용)",
        "tier1_live_run3_pass": live is True,
        "tier1_live_run4_fail": live_run4 is False,
        "src_max_consec_ge4": "if max_consec >= 4:" in src_f,
        "shape2_factor": shape_table.REVIEW_SHAPE_FLAT_FACTOR,
        "shape2_wire": shape_table.REVIEW_SHAPE_WIRE,
        "src_flat_075": "REVIEW_SHAPE_FLAT_FACTOR: float = 0.75" in src_s,
        "kb4_wire": kb.REVIEW_SHAPE_KB_WEIGHT_WIRE,
        "rng_branch_points": [
            "keep_set_by_hist → random.random() (choices와 전역 RNG 공유)",
            "저울 거절 시 generate 루프 추가 → random.choices 추가 소비",
        ],
        "prize_table_untouched": (
            "W_CROWD_BY_BRAIN" in src_p
            and 'review": 0.80' in src_p
            and "W_STRUCT_BY_BRAIN" in src_p
        ),
        "run_neutral_false": "REVIEW_SHAPE_KB_RUN_NEUTRAL: bool = False" in src_k,
    }


def main() -> int:
    live_wire = bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE)
    live_t1 = eng.tier1_filter
    live_flat = shape_table.apply_consec_flatten
    s0 = _s0()

    peek = 0
    n_ok = 0
    acc: dict[str, list[dict[str, Any]]] = {
        "base": [],
        "t3": [],
        "t2": [],
        "f060": [],
        "f050": [],
        "off": [],
        "on_branch": [],
        "frozen_kept": [],
        "aligned_on": [],
    }
    frozen_skip = 0
    aligned_skip = 0
    frozen_keep_n: list[int] = []

    for dno in range(LO, HI + 1):
        draws = _get_draws_before(dno)
        mx = max((int(d["draw_no"]) for d in draws), default=0)
        if mx >= dno:
            peek += 1
            continue
        prize = cs.prize_table(draws, brain="review")
        struct = cs.structural_unpopular_prior()
        hist = (collect_before(draws) or {}).get("shape")

        base = _gen(draws, dno, 10, reject_at=4, flatten=0.75, kb_wire=True)
        t3 = _gen(draws, dno, 10, reject_at=3, flatten=0.75, kb_wire=True)
        t2 = _gen(draws, dno, 10, reject_at=2, flatten=0.75, kb_wire=True)
        f060 = _gen(draws, dno, 10, reject_at=4, flatten=0.60, kb_wire=True)
        f050 = _gen(draws, dno, 10, reject_at=4, flatten=0.50, kb_wire=True)
        off40 = _gen(draws, dno, 40, reject_at=4, flatten=0.75, kb_wire=False)
        if len(base) < 10 or len(t3) < 10 or len(t2) < 10 or len(f060) < 10 or len(f050) < 10:
            continue
        if len(off40) < 10:
            continue
        off10 = off40[:10]
        rng = random.Random(SEED * 100000 + dno)
        decisions = [(s, _keep_isolated(s, hist, rng)) for s in off40]
        frozen = [s for s, ok in decisions[:10] if ok]
        aligned = [s for s, ok in decisions if ok][:10]
        if not frozen:
            frozen_skip += 1
        else:
            frozen_keep_n.append(len(frozen))
            acc["frozen_kept"].append(_metrics(prize, struct, frozen))
        if len(aligned) < 10:
            aligned_skip += 1
        else:
            acc["aligned_on"].append(_metrics(prize, struct, aligned))

        acc["base"].append(_metrics(prize, struct, base))
        acc["t3"].append(_metrics(prize, struct, t3))
        acc["t2"].append(_metrics(prize, struct, t2))
        acc["f060"].append(_metrics(prize, struct, f060))
        acc["f050"].append(_metrics(prize, struct, f050))
        acc["off"].append(_metrics(prize, struct, off10))
        acc["on_branch"].append(_metrics(prize, struct, base))
        n_ok += 1
        if n_ok % 20 == 0:
            print(f"[ISO] {dno} n={n_ok} peek={peek}", flush=True)

    summ = {k: _mean_acc(v) for k, v in acc.items()}
    base, t3, t2 = summ["base"], summ["t3"], summ["t2"]
    f060, f050 = summ["f060"], summ["f050"]
    off, onb = summ["off"], summ["on_branch"]
    frz, aln = summ["frozen_kept"], summ["aligned_on"]

    a_s1 = {
        "lt4": base,
        "lt3": t3,
        "lt2": t2,
        "d_lt3_minus_lt4": {k: _d(base, t3, k) for k in ("run2", "run3", "prize", "struct")},
        "d_lt2_minus_lt4": {k: _d(base, t2, k) for k in ("run2", "run3", "prize", "struct")},
    }
    a_s2 = {
        "f075": base,
        "f060": f060,
        "f050": f050,
        "d_f060_minus_f075": {k: _d(base, f060, k) for k in ("run2", "run3", "prize", "struct")},
        "d_f050_minus_f075": {k: _d(base, f050, k) for k in ("run2", "run3", "prize", "struct")},
    }
    cut_map = {
        "tier1_<3": a_s1["d_lt3_minus_lt4"]["run2"],
        "tier1_<2": a_s1["d_lt2_minus_lt4"]["run2"],
        "shape2_0.60": a_s2["d_f060_minus_f075"]["run2"],
        "shape2_0.50": a_s2["d_f050_minus_f075"]["run2"],
    }
    valid_cuts = {k: v for k, v in cut_map.items() if v is not None}
    winner = min(valid_cuts, key=valid_cuts.get) if valid_cuts else None
    root_axis = "tier1" if winner and winner.startswith("tier1") else (
        "shape2" if winner and winner.startswith("shape2") else "미확인"
    )

    b_branch = {k: _d(off, onb, k) for k in ("prize", "struct", "run2", "run3")}
    b_frozen = {k: _d(off, frz, k) for k in ("prize", "struct", "run2", "run3")}
    b_align = {k: _d(off, aln, k) for k in ("prize", "struct", "run2", "run3")}

    def _culprit(key: str) -> str:
        br, al = b_branch.get(key), b_align.get(key)
        if br is None or al is None:
            return "미확인"
        if abs(al) + 1e-12 < 0.5 * abs(br):
            return "RNG_분기"
        if abs(al) > 0.75 * abs(br) and (br < 0 and al < 0):
            return "저울"
        return "혼합"

    culprit_prize = _culprit("prize")
    culprit_struct = _culprit("struct")
    if culprit_prize == culprit_struct:
        culprit = culprit_prize
    elif "RNG_분기" in (culprit_prize, culprit_struct) and "저울" not in (
        culprit_prize,
        culprit_struct,
    ):
        culprit = "RNG_분기"
    else:
        culprit = "혼합"

    restored = (
        bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE) == live_wire
        and eng.tier1_filter is live_t1
        and shape_table.apply_consec_flatten is live_flat
    )
    src_f = SRC_FILTER.read_text(encoding="utf-8")
    src_s = SRC_SHAPE.read_text(encoding="utf-8")
    src_p = SRC_PRIZE.read_text(encoding="utf-8")
    src_k = SRC_KB.read_text(encoding="utf-8")
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    pred_1237 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0])
    pred_1239 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0])
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    conn.close()

    hard = {
        "peek0": peek == 0,
        "n100": n_ok == 100,
        "restored": restored,
        "pred_1237_0": pred_1237 == 0,
        "pred_1239_0": pred_1239 == 0,
        "src_tier1_ge4": "if max_consec >= 4:" in src_f,
        "src_flat_075": "REVIEW_SHAPE_FLAT_FACTOR: float = 0.75" in src_s,
        "src_kb_wire_true": "REVIEW_SHAPE_KB_WEIGHT_WIRE: bool = True" in src_k,
        "src_prize_untouched": 'review": 0.80' in src_p and "W_STRUCT_BY_BRAIN" in src_p,
        "apply_false": True,
    }
    verdict = "SPEC_OK" if all(hard.values()) else "DISCUSS_OK"

    def _worse(dlt: float | None) -> bool:
        return bool(dlt is not None and dlt < 0)

    payload = {
        "id": "K-REVIEW-CONSEC-ROOT-AND-PRIZE-ISOLATE",
        "as_of": _now(),
        "verdict": verdict,
        "apply": False,
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "seed": SEED,
        "n": n_ok,
        "peek": peek,
        "s0": s0,
        "part_a": {
            "s1_tier1": a_s1,
            "s2_shape2": a_s2,
            "run2_cuts": cut_map,
            "largest_run2_cut": winner,
            "root_axis": root_axis,
            "prize_worse": {
                "tier1_<3": _worse(a_s1["d_lt3_minus_lt4"]["prize"]),
                "tier1_<2": _worse(a_s1["d_lt2_minus_lt4"]["prize"]),
                "shape2_0.60": _worse(a_s2["d_f060_minus_f075"]["prize"]),
                "shape2_0.50": _worse(a_s2["d_f050_minus_f075"]["prize"]),
            },
            "struct_worse": {
                "tier1_<3": _worse(a_s1["d_lt3_minus_lt4"]["struct"]),
                "tier1_<2": _worse(a_s1["d_lt2_minus_lt4"]["struct"]),
                "shape2_0.60": _worse(a_s2["d_f060_minus_f075"]["struct"]),
                "shape2_0.50": _worse(a_s2["d_f050_minus_f075"]["struct"]),
            },
        },
        "part_b": {
            "prev_branched": PREV_BRANCHED,
            "branched_this": b_branch,
            "frozen10_kept_vs_off": b_frozen,
            "aligned10_vs_off": b_align,
            "frozen_keep_mean": round(mean(frozen_keep_n), 4) if frozen_keep_n else None,
            "frozen_skip": frozen_skip,
            "aligned_skip": aligned_skip,
            "culprit_prize": culprit_prize,
            "culprit_struct": culprit_struct,
            "culprit": culprit,
        },
        "hard": hard,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "draws_max": dmax,
    }

    lines = [
        "# K-REVIEW-CONSEC-ROOT-AND-PRIZE-ISOLATE",
        "",
        f"시각: {payload['as_of']} · **{verdict}** · READ-ONLY · APPLY **금지** · 1237아님 · hits 클레임 금지",
        "목적=① 쌍번호 뿌리가 tier1 연번기준인지 2번 억제인지 ② 비인기 하락이 4번 저울인지 RNG 분기인지.",
        "",
        "## 파트 A · S0) 현재 노브",
        "",
        f"tier1 연번 기준: **연번<4** (`max_consec >= 4` 탈락). 라이브 3연속 통과={s0['tier1_live_run3_pass']} · 4연속 탈락={s0['tier1_live_run4_fail']}.",
        f"2번 억제강도: **×{s0['shape2_factor']}** · `REVIEW_SHAPE_WIRE`={s0['shape2_wire']}. 가운데(3연속 능선)만 깎음. 쌍 자체 가중은 아님.",
        f"4번 WIRE={s0['kb4_wire']} · RUN_NEUTRAL 파일 False={s0['run_neutral_false']}. prize표 미접촉={s0['prize_table_untouched']}.",
        f"게이트 {LO}–{HI} n={n_ok} peek={peek} seed={SEED}.",
        "",
        "## 파트 A · S1) tier1 연번기준 오프라인",
        "",
        "코드 미변경. `engine.tier1_filter`만 메모리 교체 후 복원. 라이브=4번 ON · 2번 ×0.75.",
        "",
        "| 기준 | run2 | run3 | prize | struct |",
        "|------|------|------|-------|--------|",
        f"| 연번<4 (현재) | {base['run2']} | {base['run3']} | {base['prize']} | {base['struct']} |",
        f"| 연번<3 | {t3['run2']} | {t3['run3']} | {t3['prize']} | {t3['struct']} |",
        f"| 연번<2 | {t2['run2']} | {t2['run3']} | {t2['prize']} | {t2['struct']} |",
        "",
        f"Δ(<3−<4) run2={a_s1['d_lt3_minus_lt4']['run2']} run3={a_s1['d_lt3_minus_lt4']['run3']} "
        f"prize={a_s1['d_lt3_minus_lt4']['prize']} struct={a_s1['d_lt3_minus_lt4']['struct']}.",
        f"Δ(<2−<4) run2={a_s1['d_lt2_minus_lt4']['run2']} run3={a_s1['d_lt2_minus_lt4']['run3']} "
        f"prize={a_s1['d_lt2_minus_lt4']['prize']} struct={a_s1['d_lt2_minus_lt4']['struct']}.",
        "",
        "## 파트 A · S2) 2번 억제강도 오프라인",
        "",
        "코드 미변경. `apply_consec_flatten(factor=…)`만 메모리 교체 후 복원. tier1 연번<4 · 4번 ON.",
        "",
        "| 강도 | run2 | run3 | prize | struct |",
        "|------|------|------|-------|--------|",
        f"| ×0.75 (현재) | {base['run2']} | {base['run3']} | {base['prize']} | {base['struct']} |",
        f"| ×0.60 | {f060['run2']} | {f060['run3']} | {f060['prize']} | {f060['struct']} |",
        f"| ×0.50 | {f050['run2']} | {f050['run3']} | {f050['prize']} | {f050['struct']} |",
        "",
        f"Δ(0.60−0.75) run2={a_s2['d_f060_minus_f075']['run2']} prize={a_s2['d_f060_minus_f075']['prize']} "
        f"struct={a_s2['d_f060_minus_f075']['struct']}.",
        f"Δ(0.50−0.75) run2={a_s2['d_f050_minus_f075']['run2']} prize={a_s2['d_f050_minus_f075']['prize']} "
        f"struct={a_s2['d_f050_minus_f075']['struct']}.",
        "",
        "## 파트 A · 판정",
        "",
        f"run2를 가장 크게 줄인 축: **{winner}** → 뿌리=**{root_axis}**.",
        f"cut map={cut_map}.",
        f"비인기 동반악화 prize={payload['part_a']['prize_worse']} · struct={payload['part_a']['struct_worse']}.",
        "",
        "## 파트 B · S0) RNG 분기 지점",
        "",
        "1. `keep_set_by_hist`가 `random.random()`을 씀 → `random.choices`와 **같은 전역 RNG**.",
        "2. 저울이 거절하면 generate가 한 바퀴 더 돌아 **choices를 더 소비**.",
        "3. 같은 seed로 OFF/ON을 따로 `generate(10)`하면 첫 저울 `random()` 이후 시퀀스가 갈라짐.",
        "",
        "## 파트 B · S1–S2) 시드 정렬 vs 분기",
        "",
        f"기존 분기 Δ(직전 BALANCE) prize={PREV_BRANCHED['prize']} struct={PREV_BRANCHED['struct']}.",
        f"이번 분기(OFF generate vs ON generate) Δprize={b_branch['prize']} Δstruct={b_branch['struct']} "
        f"Δrun2={b_branch['run2']}.",
        f"고정10장 후필터(시드 안 갈라짐, 장수 줄 수 있음) keep평균={payload['part_b']['frozen_keep_mean']} "
        f"skip={frozen_skip} · Δprize={b_frozen['prize']} Δstruct={b_frozen['struct']}.",
        f"공유후보 정렬 10vs10 Δprize={b_align['prize']} Δstruct={b_align['struct']} Δrun2={b_align['run2']} "
        f"skip={aligned_skip}.",
        "",
        f"비인기 하락 주범: prize=**{culprit_prize}** · struct=**{culprit_struct}** · 종합=**{culprit}**.",
        "정렬|Δ|이 분기의 절반 미만이면 RNG 분기. 정렬이 분기의 75% 이상을 같은 부호로 유지하면 저울.",
        "",
        "## 판정",
        "",
        f"**{verdict}**. APPLY **없음**. 파일 플래그/prize표/`random.choices`/몰아주기/kweon 미수정.",
        f"pred_1237={pred_1237} · pred_1239={pred_1239} · MAX={dmax} · restored={restored}.",
        "",
        "## 금지 확인",
        "",
        "코드/플래그/DB write 없음(산출물 md/json만). 1237/1239 예측 없음. hits 클레임 없음.",
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
                "root_axis": root_axis,
                "winner": winner,
                "cuts": cut_map,
                "culprit": culprit,
                "b_branch": b_branch,
                "b_align": b_align,
                "hard": hard,
                "n": n_ok,
                "peek": peek,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
