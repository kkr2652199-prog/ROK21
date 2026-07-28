# -*- coding: utf-8 -*-
"""K-GENDIV — 생성15풀 다양성 강도 관측 (READ-ONLY · 슬롯재선택 금지).

가설: V2(m3+s1+r1 · set_no_asc) 발권 고정 시, 생성 풀/발권팩의
평균 pairwise Jaccard↓·union↑ 가 best-of-5 적중과 유의한 상관이면
`set_diversity.jaccard_penalty` / `oversample_factor` 강화 WIRE 후보.

직교: 발권 슬롯·뇌쿼터 불변 · 생성측 diversify_pick 레버 근거만 관측.
재탕금지와 구분: COVER=wheel 커버 · HISIM=고차구조 · SETNO/SUM/BAND=슬롯재선택
· 본축=고정 V2 팩의 Jaccard/unique ↔ 적중 (점수대체 픽 없음).

DB mode=ro · coordinator 미수정.
산출: docs/benchmarks/20260729_KGENDIV_survey.json
"""
from __future__ import annotations

import json
import sqlite3
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest, spearmanr

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KGENDIV_survey.json"

BRAINS = ("stat", "markov", "review")
QUOTA = {"markov": 3, "stat": 1, "review": 1}
D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
V2_GE3 = 0.1447
V2_MEAN = 1.7504
ALPHA = 0.05
DELTA_GE3_HIT = 0.005
CORR_HIT = 0.03  # |spearman| 게이트 (COVER와 동일 임계)

# live 레버 (set_diversity.py)
LIVE_JACCARD_PENALTY = 0.85
LIVE_OVERSAMPLE = "max(n_sets*3, n_sets+5)"


def jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def avg_pairwise_jaccard(sets: list[list[int]]) -> float:
    if len(sets) < 2:
        return 0.0
    ss = [set(s) for s in sets]
    tot = n = 0
    for i in range(len(ss)):
        for j in range(i + 1, len(ss)):
            tot += jaccard(ss[i], ss[j])
            n += 1
    return tot / max(1, n)


def union_size(sets: list[list[int]]) -> int:
    u: set[int] = set()
    for s in sets:
        u |= set(s)
    return len(u)


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
                }
            )
        if len(slots) >= 5:
            by_dn[dn][tag] = sorted(slots, key=lambda x: x["set_no"])[:5]
    return {dn: dict(v) for dn, v in by_dn.items()}


def v2_issue(brains: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    issued: list[dict[str, Any]] = []
    for tag, k in QUOTA.items():
        slots = sorted(brains[tag], key=lambda s: s["set_no"])
        issued.extend(slots[:k])
    return issued


def sp_safe(xs: list[float], ys: list[float]) -> tuple[float | None, float | None]:
    if len(xs) < 30:
        return None, None
    r = spearmanr(xs, ys)
    corr = float(r.correlation) if r.correlation is not None else None
    p = float(r.pvalue) if r.pvalue is not None else None
    return corr, p


def quintile_edges(vals: list[float]) -> list[float]:
    """q0..q5 edges (inclusive bounds via ranks)."""
    if not vals:
        return [0.0] * 6
    s = sorted(vals)
    n = len(s)
    return [s[min(n - 1, max(0, int(round(i * (n - 1) / 5))))] for i in range(6)]


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    by_dn = load_pool(con)
    con.close()

    rows: list[dict[str, Any]] = []
    for dn in range(D_LO, D_HI + 1):
        brains = by_dn.get(dn) or {}
        if not all(len(brains.get(b) or []) >= 5 for b in BRAINS):
            continue
        pool15 = [s for b in BRAINS for s in brains[b]]
        issued = v2_issue(brains)
        if len(issued) != 5:
            continue
        pool_nums = [s["nums"] for s in pool15]
        iss_nums = [s["nums"] for s in issued]
        best = max(s["matched_count"] for s in issued)
        ge3 = 1 if best >= 3 else 0
        brain_jac: dict[str, float] = {}
        for b in BRAINS:
            brain_jac[b] = round(avg_pairwise_jaccard([s["nums"] for s in brains[b]]), 6)
        rows.append(
            {
                "dn": dn,
                "best": best,
                "ge3": ge3,
                "pool_jac": avg_pairwise_jaccard(pool_nums),
                "v2_jac": avg_pairwise_jaccard(iss_nums),
                "pool_union": union_size(pool_nums),
                "v2_union": union_size(iss_nums),
                "brain_jac": brain_jac,
            }
        )

    n = len(rows)
    bests = [r["best"] for r in rows]
    v2_sm = summarize(bests)
    p_null = (
        float(binomtest(v2_sm["ge3"], v2_sm["n"], NULL_GE3, alternative="greater").pvalue)
        if v2_sm["n"]
        else 1.0
    )

    # --- correlations (diversity ↑ = jac ↓) ---
    corr_block: dict[str, Any] = {}
    for key, xs_key, expect_sign in (
        ("v2_jac_vs_best", "v2_jac", "neg"),  # lower jac → higher best
        ("pool_jac_vs_best", "pool_jac", "neg"),
        ("v2_union_vs_best", "v2_union", "pos"),
        ("pool_union_vs_best", "pool_union", "pos"),
    ):
        xs = [float(r[xs_key]) for r in rows]
        ys = [float(r["best"]) for r in rows]
        sp, spp = sp_safe(xs, ys)
        corr_block[key] = {
            "spearman_r": None if sp is None else round(sp, 4),
            "spearman_p": None if spp is None else round(spp, 6),
            "expect_sign": expect_sign,
            "pass_corr_gate": bool(
                sp is not None
                and spp is not None
                and (
                    (expect_sign == "neg" and sp <= -CORR_HIT and spp < ALPHA)
                    or (expect_sign == "pos" and sp >= CORR_HIT and spp < ALPHA)
                )
            ),
        }

    # per-brain jac vs that brain's max matched in its 5 (solo diversity quality)
    brain_corr: dict[str, Any] = {}
    for b in BRAINS:
        xs = [float(r["brain_jac"][b]) for r in rows]
        # recompute brain max matched from pool — need reload; use issued only for markov? 
        # Use proxy: for each draw, max matched among that brain's 5 from by_dn
        ys: list[float] = []
        xs2: list[float] = []
        for r in rows:
            dn = r["dn"]
            slots = by_dn[dn][b]
            ys.append(float(max(s["matched_count"] for s in slots)))
            xs2.append(float(r["brain_jac"][b]))
        sp, spp = sp_safe(xs2, ys)
        brain_corr[b] = {
            "spearman_r": None if sp is None else round(sp, 4),
            "spearman_p": None if spp is None else round(spp, 6),
            "mean_within5_jac": round(sum(xs2) / len(xs2), 4) if xs2 else 0.0,
            "pass_neg_corr": bool(
                sp is not None and spp is not None and sp <= -CORR_HIT and spp < ALPHA
            ),
        }

    # --- quintiles on v2_jac (low = more diverse) ---
    v2_jacs = [r["v2_jac"] for r in rows]
    edges = quintile_edges(v2_jacs)
    # Q1 = lowest jac (most diverse), Q5 = highest jac
    quintiles: dict[str, Any] = {}
    for qi in range(1, 6):
        lo = edges[qi - 1]
        hi = edges[qi]
        if qi == 1:
            subset = [r for r in rows if r["v2_jac"] <= hi]
        elif qi == 5:
            subset = [r for r in rows if r["v2_jac"] >= lo]
        else:
            subset = [r for r in rows if lo <= r["v2_jac"] <= hi]
        # de-dup edge ties: use rank-based assignment instead
        quintiles[f"Q{qi}"] = {"n_raw_edge": len(subset), "lo": lo, "hi": hi}

    # rank-based quintiles (fairer)
    ranked = sorted(enumerate(rows), key=lambda x: x[1]["v2_jac"])
    q_assigns: list[int] = [0] * n
    for rank, (idx, _) in enumerate(ranked):
        q_assigns[idx] = min(5, rank * 5 // n + 1)

    q_stats: dict[str, Any] = {}
    for qi in range(1, 6):
        sub = [rows[i] for i in range(n) if q_assigns[i] == qi]
        sm = summarize([r["best"] for r in sub])
        p_vs_null = (
            float(binomtest(sm["ge3"], sm["n"], NULL_GE3, alternative="greater").pvalue)
            if sm["n"]
            else 1.0
        )
        mean_jac = sum(r["v2_jac"] for r in sub) / len(sub) if sub else 0.0
        q_stats[f"Q{qi}"] = {
            **sm,
            "mean_v2_jac": round(mean_jac, 4),
            "p_vs_null": round(p_vs_null, 6),
            "delta_ge3_vs_v2pin": round(sm["ge3_rate"] - V2_GE3, 4),
            "delta_mean_vs_v2pin": round(sm["mean"] - V2_MEAN, 4),
            "note": "Q1=lowest Jaccard(most diverse) · Q5=highest",
        }

    q1 = q_stats["Q1"]
    q5 = q_stats["Q5"]
    q1_beats = bool(
        q1["ge3_rate"] > V2_GE3
        and q1["delta_ge3_vs_v2pin"] >= DELTA_GE3_HIT
        and q1["p_vs_null"] < ALPHA
    )
    # also: Q1 ge3 meaningfully above Q5
    q1_vs_q5 = round(q1["ge3_rate"] - q5["ge3_rate"], 4)

    descriptive = {
        "mean_pool_jac": round(sum(r["pool_jac"] for r in rows) / n, 4),
        "mean_v2_jac": round(sum(r["v2_jac"] for r in rows) / n, 4),
        "mean_pool_union": round(sum(r["pool_union"] for r in rows) / n, 4),
        "mean_v2_union": round(sum(r["v2_union"] for r in rows) / n, 4),
        "mean_brain_jac": {
            b: round(sum(r["brain_jac"][b] for r in rows) / n, 4) for b in BRAINS
        },
    }

    any_corr_pass = any(v["pass_corr_gate"] for v in corr_block.values())
    any_brain_pass = any(v["pass_neg_corr"] for v in brain_corr.values())
    pass_wire = bool(q1_beats or any_corr_pass)

    gates = {
        "v2_baseline_ok": bool(
            abs(v2_sm["ge3_rate"] - V2_GE3) < 1e-9 or abs(v2_sm["ge3_rate"] - V2_GE3) < 0.00015
        ),
        "any_corr_pass": any_corr_pass,
        "any_brain_jac_pass": any_brain_pass,
        "q1_diverse_beats_v2": q1_beats,
        "q1_ge3_minus_q5": q1_vs_q5,
        "PASS": pass_wire,
    }

    # nearest "signal" for report even on FAIL
    nearest = {
        "best_corr": max(
            corr_block.items(),
            key=lambda kv: abs(kv[1]["spearman_r"] or 0.0),
        )[0],
        "best_corr_r": corr_block[
            max(corr_block.items(), key=lambda kv: abs(kv[1]["spearman_r"] or 0.0))[0]
        ]["spearman_r"],
        "q1_ge3": q1["ge3_rate"],
        "q1_delta": q1["delta_ge3_vs_v2pin"],
        "q1_vs_q5": q1_vs_q5,
    }

    payload = {
        "id": "K-GENDIV",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 3),
        "db_code_write": False,
        "axis": {
            "id": "K-GENDIV",
            "hypothesis": (
                "Fixed V2 set_no_asc pack: lower pairwise Jaccard / higher union "
                "of generate-15 or issued-5 → higher best-of-5 ge3 → justify raising "
                "set_diversity.jaccard_penalty or oversample_factor"
            ),
            "orthogonal_to_v2": True,
            "not_slot_reselect": True,
            "why_not_slot_reselect": (
                "발권은 V2 set_no_asc 고정·대체점수 픽 없음. "
                "관측만=생성풀/발권팩 Jaccard·union ↔ 적중 (diversify_pick 레버 근거)"
            ),
            "not_rehash_of": [
                "SUM-SELECT",
                "BAND-SELECT",
                "EV-POP",
                "SETNO-HITMAP",
                "SETPACK-TOP6",
                "MARKOV-TUNE",
                "conf-quota",
                "HISIM",
                "STRUCT",
                "COVER",
                "GATHER",
            ],
            "code_anchor": (
                "app/testlotto/set_diversity.py::diversify_pick"
                f"(jaccard_penalty={LIVE_JACCARD_PENALTY}) · oversample_factor={LIVE_OVERSAMPLE} · "
                "predict_{stat,flow_shaman,review_king}.predict_sets"
            ),
        },
        "protocol": {
            "draw_range": [D_LO, D_HI],
            "quota": QUOTA,
            "issuance": "v2_set_no_asc_fixed",
            "null_ge3": NULL_GE3,
            "v2_ge3_pin": V2_GE3,
            "v2_mean_pin": V2_MEAN,
            "corr_abs_min": CORR_HIT,
            "delta_ge3_min": DELTA_GE3_HIT,
            "pass_rule": (
                "PASS if (any diversity↔hit spearman gate) OR "
                "(Q1 lowest-jac ge3 > V2+0.005 & p_null<0.05)"
            ),
        },
        "v2_baseline": {
            **v2_sm,
            "p_vs_null": round(p_null, 6),
            "pin_ge3": V2_GE3,
            "pin_mean": V2_MEAN,
        },
        "descriptive": descriptive,
        "correlations": corr_block,
        "brain_within5_jac_vs_brain_best": brain_corr,
        "v2_jac_quintiles": q_stats,
        "nearest_signal": nearest,
        "gates": gates,
        "verdict": "PASS" if pass_wire else "FAIL",
        "recommended_next": (
            "K-GENDIV-WIRE-후보(형GO전 coordinator금지)"
            if pass_wire
            else "없음(HOLD·V2유지·GENDIV재탕금지)"
        ),
        "wire_forbidden_until_hyung_GO": True,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "verdict": payload["verdict"], "gates": gates, "nearest": nearest, "n": n}, ensure_ascii=False))


if __name__ == "__main__":
    main()
