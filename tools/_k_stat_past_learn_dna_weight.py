# -*- coding: utf-8 -*-
"""K-STAT-PAST-LEARN-DNA-WEIGHT — stat만. prize/prefer/review 미접촉. 게이트 미달 롤백."""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.testlotto.brains.stat_brain.past_learn as pl
from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.brains.stat_brain import engine as st_eng
from app.testlotto.brains.stat_brain import learn as st_learn
from app.testlotto.brains.stat_brain import transition_v1
from app.testlotto.data_service import _get_draws_before
from app.testlotto.learn_state_cutoff import set_learn_as_of

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260829_KSTAT_PAST_LEARN_DNA_WEIGHT.json"
OUT_MD = ROOT / "reports" / "20260829_KSTAT_PAST_LEARN_DNA_WEIGHT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
SRC = ROOT / "app" / "testlotto" / "brains" / "stat_brain" / "past_learn.py"
SRC_PRIZE = ROOT / "app" / "testlotto" / "brains" / "shared" / "crowd_signal.py"
SRC_REV = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "engine.py"
LO, HI = 1137, 1236
SEED = 42
FLAG_T = "STAT_PAST_LEARN_WEIGHT_WIRE: bool = True"
FLAG_F = "STAT_PAST_LEARN_WEIGHT_WIRE: bool = False"
NULL_RATE = 6 / 45


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None

    def _rank(a: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: a[i])
        r = [0.0] * n
        for k, i in enumerate(order):
            r[i] = float(k + 1)
        return r

    rx, ry = _rank(xs), _rank(ys)
    mx, my = mean(rx), mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((ry[i] - my) ** 2 for i in range(n)))
    if dx <= 0 or dy <= 0:
        return None
    return round(num / (dx * dy), 4)


def _axis(table: dict[int, float], sets: list[list[int]]) -> float | None:
    if not table or not sets:
        return None
    uni = mean(table[i] for i in range(1, 46))
    vals = [mean(table[n] for n in nums) - uni for nums in sets if len(nums) == 6]
    return round(mean(vals), 6) if vals else None


def _dna_sets(profile: dict[str, Any], sets: list[list[int]]) -> dict[str, float | None]:
    if not sets:
        return {"overdue": None, "hot1y": None, "rate1y": None, "gap": None}
    r1 = profile.get("rate_1y") or {}
    gap = profile.get("gap") or {}
    ov, ht, rt, gp = [], [], [], []
    for s in sets:
        ov.append(sum(1 for n in s if float(gap.get(n, 0) or 0) >= 30))
        ht.append(sum(1 for n in s if float(r1.get(n, 0) or 0) > NULL_RATE * 1.15))
        rt.append(mean(float(r1.get(n, 0) or 0) for n in s))
        gp.append(mean(float(gap.get(n, 0) or 0) for n in s))
    return {
        "overdue": round(mean(ov), 6),
        "hot1y": round(mean(ht), 6),
        "rate1y": round(mean(rt), 6),
        "gap": round(mean(gp), 6),
    }


def _pool(dno: int, draws: list[dict], wire: bool) -> list[list[int]]:
    import app.testlotto.signal_pool as sp

    prev = bool(pl.STAT_PAST_LEARN_WEIGHT_WIRE)
    pl.STAT_PAST_LEARN_WEIGHT_WIRE = bool(wire)
    try:
        set_learn_as_of(dno)
        random.seed(SEED)
        raw = sp.expand_pool(draws, dno, seed=SEED, brains=["stat"])
    finally:
        pl.STAT_PAST_LEARN_WEIGHT_WIRE = prev
    out: list[list[int]] = []
    for s in raw:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) == 6:
            out.append(nums)
    return out


def _s0() -> dict[str, Any]:
    draws = _get_draws_before(1236)
    set_learn_as_of(1236)
    adj = (st_learn.get_adjustments().get("adjustments") or {})
    prev = bool(pl.STAT_PAST_LEARN_WEIGHT_WIRE)
    pl.STAT_PAST_LEARN_WEIGHT_WIRE = False
    try:
        w_off, *_ = st_eng.build_weights(draws)
    finally:
        pl.STAT_PAST_LEARN_WEIGHT_WIRE = True
        w_on, *_ = st_eng.build_weights(draws)
        pl.STAT_PAST_LEARN_WEIGHT_WIRE = prev
    prof = pl.build_past_profiles(draws)
    r1 = [float((prof.get("rate_1y") or {}).get(n, 0) or 0) for n in range(1, 46)]
    gp = [float((prof.get("gap") or {}).get(n, 0) or 0) for n in range(1, 46)]
    wo = [float(w_off.get(n, 0)) for n in range(1, 46)]
    wn = [float(w_on.get(n, 0)) for n in range(1, 46)]
    src_p = SRC_PRIZE.read_text(encoding="utf-8")
    src_r = SRC_REV.read_text(encoding="utf-8")
    return {
        "pipe": "transition(OFF) → engine(v2) → aux → past_learn soft → weight_mix → diversity",
        "PAST_LEARN_WIRE": pl.wire_on(),
        "ENGINE_V2": pl.use_engine_v2(),
        "ASSOC": pl.assoc_hint_on(),
        "TRANSITION_V1": bool(transition_v1.TRANSITION_V1_WIRE),
        "WEIGHT_WIRE_file": FLAG_T in SRC.read_text(encoding="utf-8"),
        "WEIGHT_ALPHA": pl.weight_alpha(),
        "learn_adj": {k: float(adj.get(k, 0) or 0) for k in ("carry_over_boost", "ending_digit_boost", "overdue_boost")},
        "as_of_weights": 1236,
        "rho_w_off_vs_rate1y": _spearman(wo, r1),
        "rho_w_off_vs_gap": _spearman(wo, gp),
        "rho_w_on_vs_rate1y": _spearman(wn, r1),
        "rho_w_on_vs_gap": _spearman(wn, gp),
        "prize_table_untouched": 'review": 0.80' in src_p,
        "review_rank_mix_untouched": "REVIEW_PRIZE_RANK_MIX: bool = True" in src_r,
        "peek1236": max((int(d["draw_no"]) for d in draws), default=0) < 1236,
    }


def _set_file_wire(on: bool) -> None:
    text = SRC.read_text(encoding="utf-8")
    if on:
        if FLAG_F in text:
            text = text.replace(FLAG_F, FLAG_T, 1)
    else:
        if FLAG_T in text:
            text = text.replace(FLAG_T, FLAG_F, 1)
    SRC.write_text(text, encoding="utf-8")
    pl.STAT_PAST_LEARN_WEIGHT_WIRE = bool(on)


def main() -> int:
    s0 = _s0()
    peek = 0
    n_ok = 0
    size_bad = 0
    bonus_in = 0
    acc: dict[str, dict[str, list[float]]] = {
        "off": {"prize": [], "prefer": [], "overdue": [], "hot1y": [], "rate1y": [], "gap": []},
        "on": {"prize": [], "prefer": [], "overdue": [], "hot1y": [], "rate1y": [], "gap": []},
    }
    for dno in range(LO, HI + 1):
        draws = _get_draws_before(dno)
        mx = max((int(d["draw_no"]) for d in draws), default=0)
        if mx >= dno:
            peek += 1
            continue
        prize = cs.prize_table(draws, brain="review")
        prefer = cs.prefer_table(draws, brain="markov")
        prof = pl.build_past_profiles(draws)
        off_sets = _pool(dno, draws, False)
        on_sets = _pool(dno, draws, True)
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
            pr = _axis(prefer, sets)
            dna = _dna_sets(prof, sets)
            if pa is not None:
                acc[tag]["prize"].append(pa)
            if pr is not None:
                acc[tag]["prefer"].append(pr)
            for k in ("overdue", "hot1y", "rate1y", "gap"):
                if dna[k] is not None:
                    acc[tag][k].append(float(dna[k]))
        n_ok += 1
        if n_ok % 20 == 0:
            print(f"[STATDNA] {dno} n={n_ok} peek={peek} size_bad={size_bad}", flush=True)

    def _summ(tag: str) -> dict[str, Any]:
        return {k: round(mean(vs), 6) if vs else None for k, vs in acc[tag].items()}

    off, on = _summ("off"), _summ("on")

    def _d(k: str) -> float | None:
        a, b = off.get(k), on.get(k)
        if a is None or b is None:
            return None
        return round(float(b) - float(a), 6)

    delta = {k: _d(k) for k in ("prize", "prefer", "overdue", "hot1y", "rate1y", "gap")}
    dna_up = bool(
        (delta["overdue"] is not None and delta["overdue"] > 0)
        or (delta["hot1y"] is not None and delta["hot1y"] > 0)
        or (delta["rate1y"] is not None and delta["rate1y"] > 0)
    )
    prize_ok = bool(delta["prize"] is not None and delta["prize"] >= -0.005)
    prefer_ok = bool(delta["prefer"] is not None and delta["prefer"] <= 0.005)

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    pred_1237 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0])
    pred_1239 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0])
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    conn.close()

    gate = {
        "dna_up": dna_up,
        "prize_iso": prize_ok,
        "prefer_iso": prefer_ok,
        "size_bad0": size_bad == 0,
        "bonus_in0": bonus_in == 0,
        "peek0": peek == 0,
        "n100": n_ok == 100,
    }
    pass_ok = all(gate.values())
    rolled = False
    if not pass_ok:
        _set_file_wire(False)
        rolled = True
        verdict = "SPEC_OK"
        applied = False
    else:
        pl.STAT_PAST_LEARN_WEIGHT_WIRE = True
        verdict = "APPLY_OK"
        applied = True

    src = SRC.read_text(encoding="utf-8")
    payload = {
        "id": "K-STAT-PAST-LEARN-DNA-WEIGHT",
        "as_of": _now(),
        "verdict": verdict,
        "applied": applied,
        "rolled_back": rolled,
        "apply": applied,
        "ge3_claim": False,
        "draw_1237": False,
        "brain": "stat",
        "window": [LO, HI],
        "seed": SEED,
        "n": n_ok,
        "peek": peek,
        "s0": s0,
        "off": off,
        "on": on,
        "delta_on_minus_off": delta,
        "gate": gate,
        "size_bad": size_bad,
        "bonus_in": bonus_in,
        "src_wire_true": FLAG_T in src,
        "src_wire_false": FLAG_F in src,
        "live_wire": bool(pl.STAT_PAST_LEARN_WEIGHT_WIRE),
        "rollback": "STAT_PAST_LEARN_WEIGHT_WIRE=False",
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "draws_max": dmax,
        "untouched": {
            "prize_table": s0["prize_table_untouched"],
            "review_rank_mix": s0["review_rank_mix_untouched"],
        },
    }
    lines = [
        "# K-STAT-PAST-LEARN-DNA-WEIGHT",
        "",
        f"시각: {payload['as_of']} · **{verdict}** · APPLY={'함' if applied else '안 함(롤백)' if rolled else '안 함'} · stat만 · 1237아님 · hits 클레임 금지",
        "목적=과거학습 DNA(1y빈도·미출30+)를 발권 가중 순위에 살림. 금액표·선호표·타뇌 미사용.",
        "",
        "## S0) 프로세스·DNA 실측",
        "",
        f"파이프: `{s0['pipe']}`.",
        f"WIRE past_learn={s0['PAST_LEARN_WIRE']} · v2={s0['ENGINE_V2']} · ASSOC={s0['ASSOC']} · transition={s0['TRANSITION_V1']}.",
        f"learn adj 이월={s0['learn_adj']['carry_over_boost']} 끝수={s0['learn_adj']['ending_digit_boost']} 미출={s0['learn_adj']['overdue_boost']} (0이면 boost 고리 비어 있음).",
        f"as_of1236 peekOK={s0['peek1236']}.",
        f"ρ 가중OFF↔1y률={s0['rho_w_off_vs_rate1y']} · ↔gap={s0['rho_w_off_vs_gap']}.",
        f"ρ 가중ON↔1y률={s0['rho_w_on_vs_rate1y']} · ↔gap={s0['rho_w_on_vs_gap']}.",
        "OFF에서 1y ρ가 낮으면 DNA는 soft 스티커에만 있고 뽑기 가중의 주인이 아님.",
        "",
        "## S1) 패치",
        "",
        "`STAT_PAST_LEARN_WEIGHT_WIRE` 기본 True · α=0.70 · 표=0.65×1y률+0.35×미출30+.",
        "순위혼합은 `past_learn._mix_by_rank`(로컬). `prize_table`/`prefer_table` 호출 없음. `random.choices` 불변.",
        f"파일 WIRE True={FLAG_T in src} · False={FLAG_F in src} · 라이브={pl.STAT_PAST_LEARN_WEIGHT_WIRE}.",
        "",
        "## S2) 게이트 1137–1236 n100 OFF↔ON (stat pool10)",
        "",
        f"peek={peek} · n={n_ok} · size_bad={size_bad} · bonus_in={bonus_in} · seed={SEED}.",
        "",
        "| 축 | OFF | ON | Δ |",
        "|----|-----|-----|---|",
        f"| overdue(미출30+ 개수) | {off['overdue']} | {on['overdue']} | {delta['overdue']} |",
        f"| hot1y 개수 | {off['hot1y']} | {on['hot1y']} | {delta['hot1y']} |",
        f"| rate1y 평균 | {off['rate1y']} | {on['rate1y']} | {delta['rate1y']} |",
        f"| gap 평균 | {off['gap']} | {on['gap']} | {delta['gap']} |",
        f"| prize(모니터) | {off['prize']} | {on['prize']} | {delta['prize']} |",
        f"| prefer(모니터) | {off['prefer']} | {on['prefer']} | {delta['prefer']} |",
        "",
        f"통과: DNA상승={dna_up} · prize ISO(≥−0.005)={prize_ok} · prefer ISO(≤+0.005)={prefer_ok} · size_bad0={size_bad == 0}.",
        f"pred_1237={pred_1237} · pred_1239={pred_1239} · MAX={dmax}.",
        "",
        "## 판정",
        "",
        f"**{verdict}**. {'게이트 통과 · 라이브 WIRE True.' if applied else '게이트 미달 · WIRE False 원복.' if rolled else '미적용.'}",
        "review/markov/prize표/choices/몰아주기/kweon 미수정. 엔진 독립 유지.",
        "",
        "## 롤백",
        "",
        "`STAT_PAST_LEARN_WEIGHT_WIRE=False`",
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
                "s0_rho": {
                    "off_1y": s0["rho_w_off_vs_rate1y"],
                    "on_1y": s0["rho_w_on_vs_rate1y"],
                },
                "delta": delta,
                "gate": gate,
                "live_wire": pl.STAT_PAST_LEARN_WEIGHT_WIRE,
                "n": n_ok,
                "peek": peek,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
