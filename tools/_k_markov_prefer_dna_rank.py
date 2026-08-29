# -*- coding: utf-8 -*-
"""K-MARKOV-PREFER-DNA-RANK — markov만. prize/stat 미접촉. 게이트 미달 롤백."""
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

import app.testlotto.brains.markov_brain.engine as mk
from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before
from app.testlotto.learn_state_cutoff import set_learn_as_of

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260829_KMARKOV_PREFER_DNA_RANK.json"
OUT_MD = ROOT / "reports" / "20260829_KMARKOV_PREFER_DNA_RANK.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
SRC = ROOT / "app" / "testlotto" / "brains" / "markov_brain" / "engine.py"
SRC_STAT = ROOT / "app" / "testlotto" / "brains" / "stat_brain" / "past_learn.py"
SRC_REV = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "engine.py"
SRC_PRIZE = ROOT / "app" / "testlotto" / "brains" / "shared" / "crowd_signal.py"
LO, HI = 1137, 1236
SEED = 42
FLAG_T = "MARKOV_PREFER_RANK_MIX: bool = True"
FLAG_F = "MARKOV_PREFER_RANK_MIX: bool = False"
BDAY_MAX = 31


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


def _pool(dno: int, draws: list[dict], mix: bool) -> list[list[int]]:
    import app.testlotto.signal_pool as sp

    prev = bool(mk.MARKOV_PREFER_RANK_MIX)
    mk.MARKOV_PREFER_RANK_MIX = bool(mix)
    try:
        set_learn_as_of(dno)
        random.seed(SEED)
        raw = sp.expand_pool(draws, dno, seed=SEED, brains=["markov"])
    finally:
        mk.MARKOV_PREFER_RANK_MIX = prev
    out: list[list[int]] = []
    for s in raw:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) == 6:
            out.append(nums)
    return out


def _s0() -> dict[str, Any]:
    draws = _get_draws_before(1236)
    set_learn_as_of(1236)
    pref = cs.prefer_table(draws, brain="markov")
    pv = [float(pref[n]) for n in range(1, 46)]
    prev = bool(mk.MARKOV_PREFER_RANK_MIX)
    random.seed(SEED)
    mk.MARKOV_PREFER_RANK_MIX = False
    w_off = mk.build_weights(draws)
    random.seed(SEED)
    mk.MARKOV_PREFER_RANK_MIX = True
    w_on = mk.build_weights(draws)
    mk.MARKOV_PREFER_RANK_MIX = prev
    wo = [float(w_off.get(n, 0)) for n in range(1, 46)]
    wn = [float(w_on.get(n, 0)) for n in range(1, 46)]
    src_p = SRC_PRIZE.read_text(encoding="utf-8")
    src_s = SRC_STAT.read_text(encoding="utf-8")
    src_r = SRC_REV.read_text(encoding="utf-8")
    return {
        "pipe": "transition walk → learn → prefer mix → top25 choices → aux → diversity",
        "PREFER_WIRE": cs.prefer_on(),
        "LEARN_WIRED": True,
        "W_CROWD_markov": cs.W_CROWD_BY_BRAIN.get("markov"),
        "W_STRUCT_markov": cs.W_STRUCT_BY_BRAIN.get("markov"),
        "BLEND_markov": cs.BLEND_STRENGTH_BY_BRAIN.get("markov"),
        "RANK_ALPHA": mk.MARKOV_PREFER_RANK_ALPHA,
        "as_of_weights": 1236,
        "peek1236": max((int(d["draw_no"]) for d in draws), default=0) < 1236,
        "rho_w_off_vs_prefer": _spearman(wo, pv),
        "rho_w_on_vs_prefer": _spearman(wn, pv),
        "prize_table_untouched": 'review": 0.80' in src_p and 'markov": 0.90' in src_p,
        "stat_weight_untouched": "STAT_PAST_LEARN_WEIGHT_WIRE: bool = True" in src_s,
        "review_rank_untouched": "REVIEW_PRIZE_RANK_MIX: bool = True" in src_r,
    }


def _set_file_mix(on: bool) -> None:
    text = SRC.read_text(encoding="utf-8")
    if on:
        if FLAG_F in text:
            text = text.replace(FLAG_F, FLAG_T, 1)
    else:
        if FLAG_T in text:
            text = text.replace(FLAG_T, FLAG_F, 1)
    SRC.write_text(text, encoding="utf-8")
    mk.MARKOV_PREFER_RANK_MIX = bool(on)


def main() -> int:
    s0 = _s0()
    peek = 0
    n_ok = 0
    size_bad = 0
    bonus_in = 0
    acc: dict[str, dict[str, list[float]]] = {
        "off": {"prefer": [], "prize": [], "bday": [], "hi32": []},
        "on": {"prefer": [], "prize": [], "bday": [], "hi32": []},
    }
    for dno in range(LO, HI + 1):
        draws = _get_draws_before(dno)
        mx = max((int(d["draw_no"]) for d in draws), default=0)
        if mx >= dno:
            peek += 1
            continue
        prize = cs.prize_table(draws, brain="review")
        prefer = cs.prefer_table(draws, brain="markov")
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
            if pa is not None:
                acc[tag]["prize"].append(pa)
            if pr is not None:
                acc[tag]["prefer"].append(pr)
            acc[tag]["bday"].append(mean(sum(1 for n in s if n <= BDAY_MAX) for s in sets))
            acc[tag]["hi32"].append(mean(sum(1 for n in s if n >= 32) for s in sets))
        n_ok += 1
        if n_ok % 20 == 0:
            print(f"[MKDNA] {dno} n={n_ok} peek={peek} size_bad={size_bad}", flush=True)

    def _summ(tag: str) -> dict[str, Any]:
        return {k: round(mean(vs), 6) if vs else None for k, vs in acc[tag].items()}

    off, on = _summ("off"), _summ("on")

    def _d(k: str) -> float | None:
        a, b = off.get(k), on.get(k)
        if a is None or b is None:
            return None
        return round(float(b) - float(a), 6)

    delta = {k: _d(k) for k in ("prefer", "prize", "bday", "hi32")}
    dna_up = bool(delta["prefer"] is not None and delta["prefer"] > 0)
    prize_ok = bool(delta["prize"] is not None and delta["prize"] >= -0.005)
    gate = {
        "dna_up": dna_up,
        "prize_iso": prize_ok,
        "size_bad0": size_bad == 0,
        "bonus_in0": bonus_in == 0,
        "peek0": peek == 0,
        "n100": n_ok == 100,
    }
    pass_ok = all(gate.values())
    rolled = False
    if not pass_ok:
        _set_file_mix(False)
        rolled = True
        verdict = "SPEC_OK"
        applied = False
    else:
        mk.MARKOV_PREFER_RANK_MIX = True
        verdict = "APPLY_OK"
        applied = True

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    pred_1237 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0])
    pred_1239 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0])
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    conn.close()
    src = SRC.read_text(encoding="utf-8")
    payload = {
        "id": "K-MARKOV-PREFER-DNA-RANK",
        "as_of": _now(),
        "verdict": verdict,
        "applied": applied,
        "rolled_back": rolled,
        "apply": applied,
        "ge3_claim": False,
        "draw_1237": False,
        "brain": "markov",
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
        "src_mix_true": FLAG_T in src,
        "src_mix_false": FLAG_F in src,
        "live_mix": bool(mk.MARKOV_PREFER_RANK_MIX),
        "rollback": "MARKOV_PREFER_RANK_MIX=False",
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "draws_max": dmax,
        "untouched": {
            "prize_w_crowd": s0["prize_table_untouched"],
            "stat_weight": s0["stat_weight_untouched"],
            "review_rank": s0["review_rank_untouched"],
        },
    }
    lines = [
        "# K-MARKOV-PREFER-DNA-RANK",
        "",
        f"시각: {payload['as_of']} · **{verdict}** · APPLY={'함' if applied else '안 함(롤백)' if rolled else '안 함'} · markov만 · 1237아님 · hits 클레임 금지",
        "목적=선호번호 DNA(prefer_table=인기회+생일대)를 발권 순위에 살림. 금액표·1y표 미사용.",
        "",
        "## S0) 프로세스·DNA 실측",
        "",
        f"파이프: `{s0['pipe']}`.",
        f"PREFER_WIRE={s0['PREFER_WIRE']} · W_CROWD markov={s0['W_CROWD_markov']} · W_STRUCT={s0['W_STRUCT_markov']} · BLEND={s0['BLEND_markov']}.",
        f"as_of1236 peekOK={s0['peek1236']}.",
        f"ρ 가중OFF(곱셈블렌드)↔prefer={s0['rho_w_off_vs_prefer']} · ON(순위혼합)↔prefer={s0['rho_w_on_vs_prefer']}.",
        "OFF ρ가 낮으면 전이 방문횟수가 선호표를 눌러 DNA가 순위 주인이 아님.",
        "",
        "## S1) 패치",
        "",
        "`MARKOV_PREFER_RANK_MIX` 기본 True · α=0.70 · `mix_by_rank(visit, prefer_table)`.",
        "`random.choices` 불변. prize_table/stat 1y 미호출. markov W_CROWD/W_STRUCT 불변.",
        f"파일 MIX True={FLAG_T in src} · False={FLAG_F in src} · 라이브={mk.MARKOV_PREFER_RANK_MIX}.",
        "",
        "## S2) 게이트 1137–1236 n100 OFF↔ON (markov pool10)",
        "",
        f"peek={peek} · n={n_ok} · size_bad={size_bad} · bonus_in={bonus_in} · seed={SEED}.",
        "",
        "| 축 | OFF(곱셈) | ON(순위) | Δ |",
        "|----|-----------|----------|---|",
        f"| prefer | {off['prefer']} | {on['prefer']} | {delta['prefer']} |",
        f"| bday(≤31 개수) | {off['bday']} | {on['bday']} | {delta['bday']} |",
        f"| hi32 모니터 | {off['hi32']} | {on['hi32']} | {delta['hi32']} |",
        f"| prize 모니터 | {off['prize']} | {on['prize']} | {delta['prize']} |",
        "",
        f"통과: prefer상승={dna_up} · prize ISO(≥−0.005)={prize_ok} · size_bad0={size_bad == 0}.",
        f"pred_1237={pred_1237} · pred_1239={pred_1239} · MAX={dmax}.",
        "",
        "## 판정",
        "",
        f"**{verdict}**. {'게이트 통과 · 라이브 MIX True.' if applied else '게이트 미달 · MIX False 원복.' if rolled else '미적용.'}",
        "review/stat/prize표/choices/몰아주기/kweon 미수정. 엔진 독립 유지.",
        "",
        "## 롤백",
        "",
        "`MARKOV_PREFER_RANK_MIX=False`",
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
                "s0_rho": {"off": s0["rho_w_off_vs_prefer"], "on": s0["rho_w_on_vs_prefer"]},
                "delta": delta,
                "gate": gate,
                "live_mix": mk.MARKOV_PREFER_RANK_MIX,
                "n": n_ok,
                "peek": peek,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
