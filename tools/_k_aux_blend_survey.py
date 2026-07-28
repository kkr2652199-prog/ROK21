# -*- coding: utf-8 -*-
"""K-AUX-BLEND — AUX_WEIGHTS / aux_score*40 점수 레버 관측 (READ-ONLY).

가설: V2(set_no_asc · m3+s1+r1) 발권 고정 시, 발권전 AUX 합성점수
(live 0.25×4 또는 warrant 편향 재가중)가 matched_count와 유의 상관이면
`coordinator.AUX_WEIGHTS` / `aux_score*40` 이 실재 레버.

직교: 슬롯재선택 없음 · diversify/Jaccard 없음 · 뇌쿼터·set_no 불변.
재탕금지와 구분: BAND의 K-AUX-THRESH=문턱으로 슬롯픽 · conf-quota=conf정렬발권
· 본축=점수↔적중 상관·오분위만 (픽 변경 0).

DB mode=ro · coordinator 미수정.
산출: docs/benchmarks/20260729_KAUX_BLEND_survey.json
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import (  # noqa: E402
    aux_balance_keeper,
    aux_miss_detective,
    aux_pattern_spotlight,
    aux_referee,
)
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KAUX_BLEND_survey.json"

BRAINS = ("stat", "markov", "review")
QUOTA = {"markov": 3, "stat": 1, "review": 1}
AUX_MODS = [
    aux_miss_detective,
    aux_pattern_spotlight,
    aux_balance_keeper,
    aux_referee,
]
AUX_NAMES = ("miss", "pattern", "balance", "referee")

LIVE_WEIGHTS = [0.25, 0.25, 0.25, 0.25]
LIVE_SCALE = 40.0

BLENDS: dict[str, list[float]] = {
    "live_025": [0.25, 0.25, 0.25, 0.25],
    # warrant: pattern/balance=실증 · miss=기각 · referee=미정의
    "warrant_emp": [0.05, 0.40, 0.40, 0.15],
    "pattern_heavy": [0.10, 0.55, 0.25, 0.10],
    "balance_heavy": [0.10, 0.25, 0.55, 0.10],
    "miss_off": [0.0, 1 / 3, 1 / 3, 1 / 3],
    "equal_emp3": [0.0, 0.5, 0.5, 0.0],
}

D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
V2_GE3 = 0.1447
V2_MEAN = 1.7504
ALPHA = 0.05
CORR_HIT = 0.03
DELTA_GE3_HIT = 0.005


def summarize(ms: list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3": 0, "ge3_rate": 0.0, "ge4": 0, "ge4_rate": 0.0}
    ge3 = sum(1 for x in ms if x >= 3)
    ge4 = sum(1 for x in ms if x >= 4)
    return {
        "n": n,
        "mean": round(sum(ms) / n, 4),
        "ge3": ge3,
        "ge3_rate": round(ge3 / n, 4),
        "ge4": ge4,
        "ge4_rate": round(ge4 / n, 4),
    }


def pick_v2(by_brain: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tag, cap in QUOTA.items():
        slots = sorted(by_brain.get(tag) or [], key=lambda x: x["set_no"])
        out.extend(slots[:cap])
    return out


def load_draws(con: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1 AND ? ORDER BY draw_no",
        (D_HI,),
    ).fetchall()
    return [
        {
            "draw_no": int(r[0]),
            "num1": int(r[1]),
            "num2": int(r[2]),
            "num3": int(r[3]),
            "num4": int(r[4]),
            "num5": int(r[5]),
            "num6": int(r[6]),
        }
        for r in rows
    ]


def load_pool(con: sqlite3.Connection) -> dict[int, dict[str, list[dict[str, Any]]]]:
    by_dn: dict[int, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: {b: [] for b in BRAINS}
    )
    for r in con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE brain_tag IN (?,?,?) AND draw_no BETWEEN ? AND ?",
        (*BRAINS, D_LO, D_HI),
    ):
        dn, tag = int(r[0]), str(r[1])
        if tag not in BRAINS:
            continue
        try:
            raw = json.loads(r[2] or "[]")
        except json.JSONDecodeError:
            continue
        slots: list[dict[str, Any]] = []
        for i, s in enumerate(raw[:5]):
            nums = [int(x) for x in (s.get("nums") or []) if 1 <= int(x) <= 45]
            if len(nums) != 6:
                continue
            mc = s.get("matched_count")
            if mc is None:
                continue
            slots.append(
                {
                    "set_no": int(s.get("set_no") or (i + 1)),
                    "nums": sorted(nums),
                    "matched_count": int(mc),
                    "confidence": float(s.get("confidence") or 0),
                }
            )
        if len(slots) >= 5:
            by_dn[dn][tag] = sorted(slots, key=lambda x: x["set_no"])[:5]
    return {dn: dict(v) for dn, v in by_dn.items() if all(len(v[b]) >= 5 for b in BRAINS)}


def component_scores(
    nums: list[int],
    draws: list[dict],
    target: int,
    brain_tag: str,
) -> list[float]:
    return [
        float(m.score_set(nums, draws, target, brain_tag=brain_tag)) for m in AUX_MODS
    ]


def blend(comps: list[float], weights: list[float]) -> float:
    return sum(w * c for w, c in zip(weights, comps))


def corr_block(xs: list[float], ys: list[float]) -> dict[str, Any]:
    if len(xs) < 30:
        return {"n": len(xs), "r": None, "p": None, "pass": False, "constant": False}
    if max(xs) - min(xs) < 1e-12:
        return {"n": len(xs), "r": 0.0, "p": 1.0, "pass": False, "constant": True}
    r, p = spearmanr(xs, ys)
    rf = float(r) if r == r else 0.0
    pf = float(p) if p == p else 1.0
    return {
        "n": len(xs),
        "r": round(rf, 4),
        "p": round(pf, 6),
        "pass": bool(abs(rf) >= CORR_HIT and pf < ALPHA and rf > 0),
        "constant": False,
    }


def quintile_pack(
    pack_scores: list[float], pack_bests: list[int]
) -> dict[str, Any]:
    """회차 단위: V2팩 mean_aux 오분위 → best matched ge3."""
    n = len(pack_scores)
    if n < 50:
        return {"n": n, "quintiles": []}
    order = sorted(range(n), key=lambda i: pack_scores[i])
    qs: list[dict[str, Any]] = []
    for q in range(5):
        lo = q * n // 5
        hi = (q + 1) * n // 5
        idx = order[lo:hi]
        ms = [pack_bests[i] for i in idx]
        sc = [pack_scores[i] for i in idx]
        sm = summarize(ms)
        qs.append(
            {
                "Q": q + 1,
                "n": len(idx),
                "mean_aux": round(sum(sc) / len(sc), 4),
                **{k: sm[k] for k in ("mean", "ge3_rate", "ge4_rate")},
                "delta_ge3_vs_v2": round(sm["ge3_rate"] - V2_GE3, 4),
            }
        )
    q5 = qs[4]["ge3_rate"]
    q1 = qs[0]["ge3_rate"]
    return {
        "n": n,
        "quintiles": qs,
        "Q5_minus_Q1_ge3": round(q5 - q1, 4),
        "Q5_beats_v2": bool(q5 > V2_GE3 + DELTA_GE3_HIT),
    }


def main() -> None:
    t0 = time.perf_counter()
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    draws_all = load_draws(con)
    pool = load_pool(con)
    con.close()

    draw_nos = [d["draw_no"] for d in draws_all]
    dns = sorted(dn for dn in pool if dn > 1)

    pool_matched: list[int] = []
    pool_comps: list[list[float]] = []
    pool_live: list[float] = []
    pool_blends: dict[str, list[float]] = {k: [] for k in BLENDS}
    pool_scale40: list[float] = []
    pool_conf: list[float] = []

    v2_bests: list[int] = []
    v2_means_aux: dict[str, list[float]] = {k: [] for k in BLENDS}
    v2_ticket_matched: list[int] = []
    v2_ticket_live: list[float] = []

    for dn in dns:
        set_learn_as_of(int(dn))
        # draws before target (prefix of sorted draws_all)
        hi = 0
        while hi < len(draw_nos) and draw_nos[hi] < dn:
            hi += 1
        before = draws_all[:hi]
        if not before:
            continue
        by_b = pool[dn]
        scored: dict[tuple[str, int], tuple[list[float], float]] = {}
        for tag in BRAINS:
            for s in by_b[tag]:
                comps = component_scores(s["nums"], before, dn, tag)
                live = blend(comps, LIVE_WEIGHTS)
                scored[(tag, s["set_no"])] = (comps, live)
                pool_matched.append(s["matched_count"])
                pool_comps.append(comps)
                pool_live.append(live)
                pool_scale40.append(live * LIVE_SCALE)
                pool_conf.append(s["confidence"])
                for name, w in BLENDS.items():
                    pool_blends[name].append(blend(comps, w))

        owned: list[tuple[str, dict[str, Any]]] = []
        for tag, cap in QUOTA.items():
            slots = sorted(by_b[tag], key=lambda x: x["set_no"])[:cap]
            for s in slots:
                owned.append((tag, s))
        if len(owned) != 5:
            continue
        best = max(s["matched_count"] for _, s in owned)
        v2_bests.append(best)
        auxs_by_blend: dict[str, list[float]] = {k: [] for k in BLENDS}
        for tag, s in owned:
            comps, live = scored[(tag, s["set_no"])]
            for name, w in BLENDS.items():
                auxs_by_blend[name].append(blend(comps, w))
            v2_ticket_matched.append(s["matched_count"])
            v2_ticket_live.append(live)
        for name in BLENDS:
            v2_means_aux[name].append(sum(auxs_by_blend[name]) / 5.0)

    v2_sm = summarize(v2_bests)

    # component corrs
    comp_corrs = {}
    for i, name in enumerate(AUX_NAMES):
        xs = [c[i] for c in pool_comps]
        comp_corrs[name] = corr_block(xs, pool_matched)

    blend_corrs = {name: corr_block(pool_blends[name], pool_matched) for name in BLENDS}
    live_corr = corr_block(pool_live, pool_matched)
    scale_corr = corr_block(pool_scale40, pool_matched)
    conf_corr = corr_block(pool_conf, pool_matched)
    v2_ticket_corr = corr_block(v2_ticket_live, v2_ticket_matched)

    # pack-level: mean live aux vs best
    pack_q = {
        name: quintile_pack(v2_means_aux[name], v2_bests) for name in BLENDS
    }

    any_corr_pass = any(v["pass"] for v in blend_corrs.values()) or any(
        v["pass"] for v in comp_corrs.values()
    )
    # Q5 high-aux packs beat V2 (observational; not reselect)
    any_q5 = any(pack_q[n].get("Q5_beats_v2") for n in BLENDS)

    # best blend by r
    best_name = max(BLENDS.keys(), key=lambda n: (blend_corrs[n]["r"] or -1))
    best_r = blend_corrs[best_name]

    gates = {
        "any_positive_corr_pass": any_corr_pass,
        "live_corr_pass": live_corr["pass"],
        "best_blend": best_name,
        "best_blend_corr_pass": best_r["pass"],
        "any_Q5_high_aux_beats_v2": any_q5,
        "PASS_to_WIRE": bool(any_corr_pass and (live_corr["pass"] or best_r["pass"])),
        "note": "PASS=점수↔적중 상관 게이트. V2 set_no 발권은 관측 중 불변·슬롯재선택0. "
        "WIRE=AUX_WEIGHTS/scale 후보(형 GO 전 금지). V2경로에서 발권조합 자체는 set_no라 "
        "WEIGHTS만 바꿔도 티켓 불변 — conf경로·잔여채움에만 영향.",
    }

    elapsed = round(time.perf_counter() - t0, 3)
    out = {
        "id": "K-AUX-BLEND",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "db_code_write": False,
        "not_slot_reselect": True,
        "not_gendiv_jaccard": True,
        "v2_pin": {"ge3": V2_GE3, "mean": V2_MEAN, "quota": QUOTA, "mode": "set_no_asc"},
        "code_anchors": {
            "AUX_WEIGHTS": LIVE_WEIGHTS,
            "aux_score_scale": LIVE_SCALE,
            "file": "app/testlotto/brains/coordinator.py",
        },
        "protocol": {
            "draw_range": [D_LO, D_HI],
            "n_draws": len(v2_bests),
            "corr_hit": CORR_HIT,
            "alpha": ALPHA,
            "delta_ge3_hit": DELTA_GE3_HIT,
            "null_ge3": NULL_GE3,
            "PASS": "any blend/component spearman r>=0.03 & p<0.05 & r>0 "
            "(live or best blend). Q5는 보조관측.",
        },
        "hypothesis": (
            "발권전 AUX 합성점수(가중·*40)가 matched와 유의 양상관이면 "
            "AUX_WEIGHTS/scale이 실재 레버"
        ),
        "blends": BLENDS,
        "v2_baseline_check": {
            **v2_sm,
            "p_vs_null": round(
                float(binomtest(v2_sm["ge3"], v2_sm["n"], NULL_GE3, alternative="greater").pvalue),
                6,
            )
            if v2_sm["n"]
            else None,
        },
        "pool_n_sets": len(pool_matched),
        "correlations": {
            "components": comp_corrs,
            "blends": blend_corrs,
            "live_composite": live_corr,
            "live_times_40": scale_corr,
            "stored_confidence": conf_corr,
            "v2_tickets_live_aux": v2_ticket_corr,
        },
        "v2_pack_aux_quintiles": pack_q,
        "gates": gates,
        "recommended_next": (
            None
            if not gates["PASS_to_WIRE"]
            else "K-AUX-BLEND-WIRE (형 GO 전 금지 · V2 set_no 유지 시 티켓불변 명시)"
        ),
        "elapsed_s": elapsed,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"out": str(OUT), "gates": gates, "elapsed_s": elapsed, "n": len(v2_bests)},
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
