# -*- coding: utf-8 -*-
"""K-SETNO-HITMAP — V2 뇌쿼터 고정 · 뇌내 set_no 히트맵 + 발권 슬롯 재배치 (READ-ONLY).

가설: V2는 markov3+stat1+review1 쿼터만 고정하고 set_no는 항상 오름(1..k).
PATTERN1 tier4에서 set3 편향(12/31) → 뇌×set_no 적중률이 균등하지 않으면
동일 쿼터 내 set_no 조합이 V2(ge3=0.1447)를 이길 수 있다.

DB mode=ro · coordinator WIRE 미수정.
산출: docs/benchmarks/20260729_KSETNO_hitmap.json
"""
from __future__ import annotations

import json
import sqlite3
import time
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KSETNO_hitmap.json"

BRAINS = ("stat", "markov", "review")
D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
V2_GE3 = 0.1447  # docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json
V2_MEAN = 1.7504
ALPHA = 0.05

# policy: brain -> tuple of set_no to issue (order irrelevant; best-of issued)
POLICIES: dict[str, dict[str, tuple[int, ...]]] = {
    "v2_asc": {"markov": (1, 2, 3), "stat": (1,), "review": (1,)},
    "markov_skip2": {"markov": (1, 3, 5), "stat": (1,), "review": (1,)},
    "markov_mid": {"markov": (2, 3, 4), "stat": (1,), "review": (1,)},
    "markov_hi": {"markov": (3, 4, 5), "stat": (1,), "review": (1,)},
    "slot_stat2": {"markov": (1, 2, 3), "stat": (2,), "review": (1,)},
    "slot_stat3": {"markov": (1, 2, 3), "stat": (3,), "review": (1,)},  # grid best
    "slot_rev2": {"markov": (1, 2, 3), "stat": (1,), "review": (2,)},
    "slot_both2": {"markov": (1, 2, 3), "stat": (2,), "review": (2,)},
    "slot_both3": {"markov": (1, 2, 3), "stat": (3,), "review": (3,)},  # PATTERN1 set3 hint
    "mix_m135_s3_r3": {"markov": (1, 3, 5), "stat": (3,), "review": (3,)},
}


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


def load_by_dn(con: sqlite3.Connection) -> dict[int, dict[str, dict[int, int]]]:
    """draw -> brain -> set_no -> matched_count (stored in JSON)."""
    by_dn: dict[int, dict[str, dict[int, int]]] = defaultdict(
        lambda: {b: {} for b in BRAINS}
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
        slot: dict[int, int] = {}
        for i, s in enumerate(raw[:5]):
            sn = int(s.get("set_no") or (i + 1))
            mc = s.get("matched_count")
            if mc is None:
                continue
            slot[sn] = int(mc)
        if len(slot) >= 5:
            by_dn[dn][tag] = slot
    return {dn: dict(v) for dn, v in by_dn.items()}


def eval_policy(
    by_dn: dict[int, dict[str, dict[int, int]]],
    policy: dict[str, tuple[int, ...]],
) -> dict[str, Any]:
    bests: list[int] = []
    for dn in range(D_LO, D_HI + 1):
        brains = by_dn.get(dn) or {}
        if not all(len(brains.get(b) or {}) >= 5 for b in BRAINS):
            continue
        hits: list[int] = []
        ok = True
        for b, sns in policy.items():
            slot = brains[b]
            for sn in sns:
                if sn not in slot:
                    ok = False
                    break
                hits.append(slot[sn])
            if not ok:
                break
        if not ok or not hits:
            continue
        bests.append(max(hits))
    sm = summarize(bests)
    p = (
        float(binomtest(sm["ge3"], sm["n"], NULL_GE3, alternative="greater").pvalue)
        if sm["n"]
        else 1.0
    )
    return {
        **sm,
        "p_vs_null": round(p, 6),
        "delta_ge3_vs_v2pin": round(sm["ge3_rate"] - V2_GE3, 4),
        "delta_mean_vs_v2pin": round(sm["mean"] - V2_MEAN, 4),
        "beats_v2_ge3": bool(sm["ge3_rate"] > V2_GE3),
        "pass_vs_null": bool(sm["ge3_rate"] >= V2_GE3 and p < ALPHA),
    }


def hitmap(
    by_dn: dict[int, dict[str, dict[int, int]]],
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[int]] = defaultdict(list)
    for dn in range(D_LO, D_HI + 1):
        brains = by_dn.get(dn) or {}
        if not all(len(brains.get(b) or {}) >= 5 for b in BRAINS):
            continue
        for b in BRAINS:
            for sn, mc in brains[b].items():
                buckets[f"{b}|{sn}"].append(mc)
    out: dict[str, dict[str, Any]] = {}
    for k, ms in sorted(buckets.items()):
        out[k] = summarize(ms)
    return out


def markov_combo_scan(
    by_dn: dict[int, dict[str, dict[int, int]]],
) -> list[dict[str, Any]]:
    """markov C(5,3) × stat1 × review1 소규모 격자 (set1 고정 슬롯)."""
    rows: list[dict[str, Any]] = []
    for mcombo in combinations((1, 2, 3, 4, 5), 3):
        for s_sn in (1, 2, 3):
            for r_sn in (1, 2, 3):
                pol = {
                    "markov": mcombo,
                    "stat": (s_sn,),
                    "review": (r_sn,),
                }
                ev = eval_policy(by_dn, pol)
                rows.append(
                    {
                        "markov": list(mcombo),
                        "stat": s_sn,
                        "review": r_sn,
                        **ev,
                    }
                )
    rows.sort(key=lambda r: (-r["ge3_rate"], -r["mean"]))
    return rows


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    by_dn = load_by_dn(con)
    con.close()

    hm = hitmap(by_dn)
    policy_results: dict[str, Any] = {}
    for name, pol in POLICIES.items():
        policy_results[name] = {
            "quota": {k: list(v) for k, v in pol.items()},
            **eval_policy(by_dn, pol),
        }

    grid = markov_combo_scan(by_dn)
    top10 = grid[:10]
    best = grid[0] if grid else None
    v2_row = next(
        (
            r
            for r in grid
            if r["markov"] == [1, 2, 3] and r["stat"] == 1 and r["review"] == 1
        ),
        None,
    )

    # PASS: grid best beats V2 ge3 and null skill
    gate_any_beats_v2 = bool(best and best["ge3_rate"] > V2_GE3)
    gate_best_null = bool(best and best["pass_vs_null"])
    # meaningful: +0.005 ge3 vs V2 pin (same cost 5 tickets)
    gate_meaningful = bool(best and (best["ge3_rate"] - V2_GE3) >= 0.005)
    passed = bool(gate_any_beats_v2 and gate_best_null and gate_meaningful)

    recommended = None
    if passed and best:
        recommended = {
            "markov": best["markov"],
            "stat": best["stat"],
            "review": best["review"],
            "ge3_rate": best["ge3_rate"],
            "mean": best["mean"],
            "p_vs_null": best["p_vs_null"],
        }

    # per-brain set_no ranking by ge3
    brain_rank: dict[str, list[dict[str, Any]]] = {}
    for b in BRAINS:
        rows = []
        for sn in range(1, 6):
            key = f"{b}|{sn}"
            if key in hm:
                rows.append({"set_no": sn, **hm[key]})
        rows.sort(key=lambda r: (-r["ge3_rate"], -r["mean"]))
        brain_rank[b] = rows

    out = {
        "id": "K-SETNO-HITMAP",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "draw_range": [D_LO, D_HI],
        "null_ge3": NULL_GE3,
        "v2_pin": {
            "source": "docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json",
            "ge3_rate": V2_GE3,
            "mean": V2_MEAN,
            "quota": {"markov": [1, 2, 3], "stat": [1], "review": [1]},
        },
        "hypothesis": (
            "V2 뇌쿼터 고정 상태에서 뇌내 set_no 적중 분포가 비균등하면 "
            "동일 5장 비용으로 set_no 재배치가 ge3를 개선할 수 있다."
        ),
        "orthogonal_to_v2": True,
        "hitmap_brain_setno": hm,
        "brain_setno_rank_by_ge3": brain_rank,
        "named_policies": policy_results,
        "grid_C53_markov_x_slot123": {
            "n_configs": len(grid),
            "top10": top10,
            "v2_row": v2_row,
            "best": best,
        },
        "gates": {
            "any_beats_v2_ge3": gate_any_beats_v2,
            "best_pass_vs_null": gate_best_null,
            "best_delta_ge3_ge_0_005": gate_meaningful,
            "PASS": passed,
        },
        "recommended_next": (
            "K-SETNO-WIRE" if passed else "없음(HOLD·V2유지)"
        ),
        "recommended_quota": recommended,
        "verdict": "PASS→WIRE검토" if passed else "FAIL·관측종료→V2유지",
        "db_code_write": False,
        "note": (
            "matched_count는 brain_review JSON 저장값(재예측 없음). "
            "WIRE/coordinator 미수정. SETPACK(번호몰아주기)과 직교."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "elapsed": out["elapsed_sec"],
        "v2_policy_ge3": policy_results["v2_asc"]["ge3_rate"],
        "best": best,
        "gates": out["gates"],
        "verdict": out["verdict"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
