# -*- coding: utf-8 -*-
"""K-EV-POP — V2 뇌쿼터 고정 · 발권 슬롯을 비인기(EV)로 재선택 (READ-ONLY).

가설: V2(m3+s1+r1) 쿼터·풀(뇌당 5세트)은 고정하고,
set_no 오름 대신 저인기도(1/pop) 순으로 슬롯을 고르면
(1) ge3가 의미있게 오르거나 (2) ge3 손실 없이 인기도만 유의미히 낮출 수 있다.

직교: 뇌 믹스·파라미터·생성 로직 불변 · 발권 선택 기준만.
DB mode=ro · coordinator 미수정.
산출: docs/benchmarks/20260729_KEV_pop.json
"""
from __future__ import annotations

import json
import math
import sqlite3
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest, spearmanr

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KEV_pop.json"

BRAINS = ("stat", "markov", "review")
QUOTA = {"markov": 3, "stat": 1, "review": 1}
D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
V2_GE3 = 0.1447
V2_MEAN = 1.7504
ALPHA = 0.05
DELTA_GE3_HIT = 0.005
# EV-preserve: ge3 손실 허용폭 · pop 감소 최소비율
GE3_FLOOR_DELTA = -0.002
POP_DROP_MIN = 0.05  # mean_pop 상대 감소 ≥5%


def birthday_factor(n: int) -> float:
    return 1.3 if n <= 31 else 0.7


def count_consecutive(nums: list[int]) -> int:
    s = sorted(nums)
    best = run = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best if best >= 2 else 0


def popularity_score(nums: list[int], last_n: set[int], prev_n: set[int]) -> float:
    """ev_brain.popularity_score 와 동일 식 · history는 호출측이 draw_no 이전만 주입."""
    st = sorted({int(x) for x in nums if 1 <= int(x) <= 45})
    if len(st) != 6:
        return 1.0
    pop = 1.0
    for n in st:
        pop *= birthday_factor(n)
        if n % 7 == 0:
            pop *= 1.4
        if n in last_n:
            pop *= 1.5
        elif n in prev_n:
            pop *= 1.2
    c = count_consecutive(st)
    if c >= 3:
        pop *= 1.5
    elif c >= 2:
        pop *= 1.2
    odds = sum(1 for n in st if n % 2 == 1)
    if odds in (0, 6):
        pop *= 1.3
    return max(pop, 1e-9)


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


def load_draws(con: sqlite3.Connection) -> list[tuple[int, list[int]]]:
    rows = con.execute(
        "SELECT draw_no, num1, num2, num3, num4, num5, num6 "
        "FROM lotto_draws ORDER BY draw_no ASC"
    ).fetchall()
    out: list[tuple[int, list[int]]] = []
    for r in rows:
        out.append((int(r[0]), [int(r[i]) for i in range(1, 7)]))
    return out


def history_sets(all_draws: list[tuple[int, list[int]]], draw_no: int) -> tuple[set[int], set[int]]:
    before = [nums for dn, nums in all_draws if dn < draw_no]
    last_n: set[int] = set(before[-1]) if before else set()
    prev_n: set[int] = set()
    if len(before) >= 3:
        for nums in before[-3:-1]:
            prev_n.update(nums)
    return last_n, prev_n


def load_pool(con: sqlite3.Connection) -> dict[int, dict[str, list[dict[str, Any]]]]:
    """draw -> brain -> list of {set_no, nums, matched_count, confidence}."""
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
                    "confidence": float(s.get("confidence") or 0.0),
                }
            )
        if len(slots) >= 5:
            by_dn[dn][tag] = slots[:5]
    return {dn: dict(v) for dn, v in by_dn.items()}


def pick_by_set_no(slots: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    ordered = sorted(slots, key=lambda s: s["set_no"])
    return ordered[:k]


def pick_by_pop(
    slots: list[dict[str, Any]],
    k: int,
    *,
    mode: str,
) -> list[dict[str, Any]]:
    """mode: low | high | mid."""
    scored = sorted(slots, key=lambda s: (s["pop"], s["set_no"]))
    if mode == "low":
        return scored[:k]
    if mode == "high":
        return list(reversed(scored))[:k]
    # mid: take around median
    n = len(scored)
    if k >= n:
        return scored
    start = max(0, (n - k) // 2)
    return scored[start : start + k]


def pick_hybrid(
    slots: list[dict[str, Any]],
    k: int,
    *,
    brain: str,
    markov_mode: str,
    other_mode: str,
) -> list[dict[str, Any]]:
    mode = markov_mode if brain == "markov" else other_mode
    if mode == "asc":
        return pick_by_set_no(slots, k)
    return pick_by_pop(slots, k, mode=mode)


POLICIES = {
    "v2_asc": {"markov": "asc", "stat": "asc", "review": "asc"},
    "all_low_pop": {"markov": "low", "stat": "low", "review": "low"},
    "all_high_pop": {"markov": "high", "stat": "high", "review": "high"},
    "all_mid_pop": {"markov": "mid", "stat": "mid", "review": "mid"},
    "markov_asc_others_low": {"markov": "asc", "stat": "low", "review": "low"},
    "markov_low_others_asc": {"markov": "low", "stat": "asc", "review": "asc"},
}


def eval_policy(
    by_dn: dict[int, dict[str, list[dict[str, Any]]]],
    all_draws: list[tuple[int, list[int]]],
    modes: dict[str, str],
) -> dict[str, Any]:
    bests: list[int] = []
    issued_pops: list[float] = []
    issued_mcs: list[int] = []
    issued_logpops: list[float] = []

    for dn in range(D_LO, D_HI + 1):
        brains = by_dn.get(dn) or {}
        if not all(len(brains.get(b) or []) >= 5 for b in BRAINS):
            continue
        last_n, prev_n = history_sets(all_draws, dn)
        # annotate pop once per slot
        annotated: dict[str, list[dict[str, Any]]] = {}
        for b in BRAINS:
            rows = []
            for s in brains[b]:
                pop = popularity_score(s["nums"], last_n, prev_n)
                rows.append({**s, "pop": pop})
            annotated[b] = rows

        issued: list[dict[str, Any]] = []
        for b, k in QUOTA.items():
            mode = modes[b]
            if mode == "asc":
                picked = pick_by_set_no(annotated[b], k)
            else:
                picked = pick_by_pop(annotated[b], k, mode=mode)
            issued.extend(picked)

        if len(issued) != 5:
            continue
        mcs = [s["matched_count"] for s in issued]
        bests.append(max(mcs))
        for s in issued:
            issued_pops.append(s["pop"])
            issued_mcs.append(s["matched_count"])
            issued_logpops.append(math.log(s["pop"]))

    sm = summarize(bests)
    p_null = (
        float(binomtest(sm["ge3"], sm["n"], NULL_GE3, alternative="greater").pvalue)
        if sm["n"]
        else 1.0
    )
    mean_pop = sum(issued_pops) / len(issued_pops) if issued_pops else 0.0
    mean_log_pop = sum(issued_logpops) / len(issued_logpops) if issued_logpops else 0.0
    sp = None
    sp_p = None
    if len(issued_pops) >= 30:
        sp_res = spearmanr(issued_pops, issued_mcs)
        sp = float(sp_res.correlation) if sp_res.correlation is not None else None
        sp_p = float(sp_res.pvalue) if sp_res.pvalue is not None else None

    return {
        **sm,
        "p_vs_null": round(p_null, 6),
        "delta_ge3_vs_v2pin": round(sm["ge3_rate"] - V2_GE3, 4),
        "delta_mean_vs_v2pin": round(sm["mean"] - V2_MEAN, 4),
        "mean_pop": round(mean_pop, 4),
        "mean_log_pop": round(mean_log_pop, 4),
        "spearman_pop_vs_matched": None if sp is None else round(sp, 4),
        "spearman_p": None if sp_p is None else round(sp_p, 6),
        "n_issued_sets": len(issued_pops),
        "beats_v2_ge3": bool(sm["ge3_rate"] > V2_GE3),
    }


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    all_draws = load_draws(con)
    by_dn = load_pool(con)
    con.close()

    results: dict[str, Any] = {}
    for name, modes in POLICIES.items():
        results[name] = {"modes": modes, "quota": QUOTA, **eval_policy(by_dn, all_draws, modes)}

    v2 = results["v2_asc"]
    # hit-rate candidates among non-baseline
    hit_cands = [
        (name, row)
        for name, row in results.items()
        if name != "v2_asc" and row["ge3_rate"] > V2_GE3
    ]
    hit_cands.sort(key=lambda x: (-x[1]["ge3_rate"], -x[1]["mean"]))
    best_hit = hit_cands[0] if hit_cands else None

    gate_hit_beats = bool(best_hit and best_hit[1]["ge3_rate"] > V2_GE3)
    gate_hit_delta = bool(
        best_hit and (best_hit[1]["ge3_rate"] - V2_GE3) >= DELTA_GE3_HIT
    )
    gate_hit_null = bool(
        best_hit and best_hit[1]["p_vs_null"] < ALPHA and best_hit[1]["ge3_rate"] >= V2_GE3
    )
    pass_hit = bool(gate_hit_beats and gate_hit_delta and gate_hit_null)

    # EV-preserve: ge3 유지 + pop↓
    ev_cands = []
    for name, row in results.items():
        if name == "v2_asc":
            continue
        dge3 = row["ge3_rate"] - v2["ge3_rate"]
        if dge3 < GE3_FLOOR_DELTA:
            continue
        if v2["mean_pop"] <= 0:
            continue
        pop_drop = (v2["mean_pop"] - row["mean_pop"]) / v2["mean_pop"]
        if pop_drop < POP_DROP_MIN:
            continue
        ev_cands.append((name, row, round(pop_drop, 4), round(dge3, 4)))
    ev_cands.sort(key=lambda x: (-x[2], -x[1]["ge3_rate"]))
    best_ev = ev_cands[0] if ev_cands else None
    pass_ev = bool(best_ev is not None)

    passed = pass_hit or pass_ev
    recommended = None
    if pass_hit and best_hit:
        recommended = {
            "axis": "hit",
            "policy": best_hit[0],
            "ge3_rate": best_hit[1]["ge3_rate"],
            "mean": best_hit[1]["mean"],
            "mean_pop": best_hit[1]["mean_pop"],
            "delta_ge3": best_hit[1]["delta_ge3_vs_v2pin"],
            "p_vs_null": best_hit[1]["p_vs_null"],
        }
    elif pass_ev and best_ev:
        recommended = {
            "axis": "ev_preserve",
            "policy": best_ev[0],
            "ge3_rate": best_ev[1]["ge3_rate"],
            "mean": best_ev[1]["mean"],
            "mean_pop": best_ev[1]["mean_pop"],
            "pop_drop_vs_v2": best_ev[2],
            "delta_ge3_vs_v2_policy": best_ev[3],
            "p_vs_null": best_ev[1]["p_vs_null"],
        }

    out = {
        "id": "K-EV-POP",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "draw_range": [D_LO, D_HI],
        "null_ge3": NULL_GE3,
        "v2_pin": {
            "source": "docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json",
            "ge3_rate": V2_GE3,
            "mean": V2_MEAN,
            "quota": QUOTA,
        },
        "hypothesis": (
            "V2 쿼터 고정 시 발권 슬롯을 저인기도(EV)로 고르면 "
            "ge3 개선 또는 ge3 유지+인기도 유의미 감소가 가능하다."
        ),
        "orthogonal_to_v2": True,
        "popularity_model": (
            "ev_brain.popularity_score 동일 휴리스틱 "
            "(birthday·7배수·직전/최근이월·연속·홀짝) · "
            "history=draw_no 미만 only (LAST_CUT 미사용·컨닝금지)"
        ),
        "protocol": {
            "hit_WIRE": {
                "delta_ge3_min": DELTA_GE3_HIT,
                "p_vs_null_max": ALPHA,
                "beats_v2": True,
            },
            "ev_preserve_WIRE": {
                "ge3_floor_delta_vs_v2_policy": GE3_FLOOR_DELTA,
                "pop_drop_min_rel": POP_DROP_MIN,
                "note": "적중↑ 아님 · 당첨 시 실수령(공유↓) 후보. hit_WIRE와 OR.",
            },
        },
        "policies": results,
        "best_hit_policy": (
            None
            if not best_hit
            else {
                "name": best_hit[0],
                "ge3_rate": best_hit[1]["ge3_rate"],
                "mean": best_hit[1]["mean"],
                "delta_ge3_vs_v2pin": best_hit[1]["delta_ge3_vs_v2pin"],
                "p_vs_null": best_hit[1]["p_vs_null"],
                "mean_pop": best_hit[1]["mean_pop"],
            }
        ),
        "best_ev_preserve_policy": (
            None
            if not best_ev
            else {
                "name": best_ev[0],
                "ge3_rate": best_ev[1]["ge3_rate"],
                "mean": best_ev[1]["mean"],
                "mean_pop": best_ev[1]["mean_pop"],
                "pop_drop_vs_v2": best_ev[2],
                "delta_ge3_vs_v2_policy": best_ev[3],
                "p_vs_null": best_ev[1]["p_vs_null"],
            }
        ),
        "gates": {
            "hit_beats_v2_ge3": gate_hit_beats,
            "hit_delta_ge3_ge_0_005": gate_hit_delta,
            "hit_pass_vs_null": gate_hit_null,
            "PASS_hit_WIRE": pass_hit,
            "PASS_ev_preserve_WIRE": pass_ev,
            "PASS": passed,
        },
        "recommended_next": (
            "K-EV-POP-WIRE" if passed else "없음(HOLD·V2유지)"
        ),
        "recommended": recommended,
        "verdict": (
            "PASS→WIRE검토" if passed else "FAIL·관측종료→V2유지·EV-POP재탕금지"
        ),
        "db_code_write": False,
        "note": (
            "matched_count=brain_review JSON · 재예측 없음. "
            "SETNO(히트맵 set_no)·SETPACK(번호몰아)·COVER(휠)과 직교."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "elapsed": out["elapsed_sec"],
                "v2": {
                    "ge3": v2["ge3_rate"],
                    "mean": v2["mean"],
                    "mean_pop": v2["mean_pop"],
                },
                "best_hit": out["best_hit_policy"],
                "best_ev": out["best_ev_preserve_policy"],
                "gates": out["gates"],
                "verdict": out["verdict"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
