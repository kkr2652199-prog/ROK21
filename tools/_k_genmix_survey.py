# -*- coding: utf-8 -*-
"""K-GENMIX — 뇌별 생성 개수(15풀 구성) 관측 (READ-ONLY · 발권 V2 고정).

가설: markov/stat/review 생성 티켓 수(n_sets) 비율을 바꾸면
diversify_pick 결과가 달라져 V2(set_no_asc · m3+s1+r1) 발권 후 ge3가 오른다.

코드 레버: registry.SETS_PER_PREDICT_BRAIN (현재 균등 5 · 뇌별 dict 없음).
발권 불변: MARKOV_WIRE_BRAIN_QUOTA + set_no_asc.
건드리지 않음: AUX_WEIGHTS · 슬롯재픽 · diversify 파라미터.

Part A — brain_review trunc 프록시: fillable이면 티켓 동일(구조적 null).
Part B — live regen: n_sets별 predict_sets (diversify 때문에 trunc≠regen).

DB mode=ro · coordinator 미수정.
산출: docs/benchmarks/20260729_KGENMIX_survey.json
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

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import (  # noqa: E402
    predict_flow_shaman,
    predict_review_king,
    predict_stat_fairy,
)
from app.testlotto.brains.coordinator import apply_markov_wire_quota  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KGENMIX_survey.json"

BRAINS = ("markov", "stat", "review")  # quota 키 순서와 맞춤
MODS = {
    "markov": predict_flow_shaman,
    "stat": predict_stat_fairy,
    "review": predict_review_king,
}
QUOTA = {"markov": 3, "stat": 1, "review": 1}
D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
V2_GE3 = 0.1447
V2_MEAN = 1.7504
ALPHA = 0.05
DELTA_GE3_HIT = 0.005

# Part B live mixes (m,s,r) — 발권 쿼터는 전부 V2
LIVE_MIXES: dict[str, tuple[int, int, int]] = {
    "baseline_5_5_5": (5, 5, 5),
    "m7_s5_r3": (7, 5, 3),
    "m9_s3_r3": (9, 3, 3),
    "m3_s7_r5": (3, 7, 5),
    "m3_s5_r7": (3, 5, 7),
    "m7_s4_r4": (7, 4, 4),
    "equal_3_3_3": (3, 3, 3),
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


def ticket_fp(issued: list[dict[str, Any]]) -> tuple[tuple[str, tuple[int, ...]], ...]:
    rows = []
    for c in issued:
        nums = tuple(sorted(int(x) for x in c["nums"]))
        rows.append((str(c.get("brain_tag") or ""), nums))
    return tuple(sorted(rows))


def fillable(gen: dict[str, int]) -> bool:
    return all(gen.get(t, 0) >= QUOTA[t] for t in QUOTA)


def issue_v2(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return apply_markov_wire_quota(candidates)


def load_stored(con: sqlite3.Connection) -> tuple[
    dict[int, set[int]],
    dict[int, dict[str, list[dict[str, Any]]]],
]:
    actuals: dict[int, set[int]] = {}
    for r in con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1 AND ?",
        (D_HI,),
    ):
        actuals[int(r[0])] = {int(r[i]) for i in range(1, 7)}

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
            sn = int(s.get("set_no") or (i + 1))
            slots.append(
                {
                    "nums": sorted(nums),
                    "brain_tag": tag,
                    "confidence": float(s.get("confidence") or 50),
                    "set_no": sn,
                    "pred_set_no": sn,
                    "matched_count": s.get("matched_count"),
                }
            )
        if len(slots) >= 5:
            by_dn[dn][tag] = sorted(slots, key=lambda x: x["set_no"])[:5]
    return actuals, {dn: dict(v) for dn, v in by_dn.items()}


def trunc_candidates(
    brains: dict[str, list[dict[str, Any]]], gen: dict[str, int]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tag in BRAINS:
        n = int(gen.get(tag, 0))
        if n <= 0:
            continue
        out.extend(brains[tag][:n])
    return out


def part_a_trunc(
    actuals: dict[int, set[int]],
    by_dn: dict[int, dict[str, list[dict[str, Any]]]],
) -> dict[str, Any]:
    """brain_review[:n] trunc — fillable면 V2와 티켓 동일해야 함."""
    # named + small grid (각 ≤5)
    policies: dict[str, dict[str, int]] = {
        "baseline_5_5_5": {"markov": 5, "stat": 5, "review": 5},
        "trunc_m5_s5_r3": {"markov": 5, "stat": 5, "review": 3},
        "trunc_m5_s3_r5": {"markov": 5, "stat": 3, "review": 5},
        "trunc_m3_s5_r5": {"markov": 3, "stat": 5, "review": 5},
        "trunc_m5_s1_r1": {"markov": 5, "stat": 1, "review": 1},
        "starve_m2_s5_r5": {"markov": 2, "stat": 5, "review": 5},
        "starve_m5_s0_r5": {"markov": 5, "stat": 0, "review": 5},
        "starve_m5_s5_r0": {"markov": 5, "stat": 5, "review": 0},
    }

    dns = [
        dn
        for dn in range(D_LO, D_HI + 1)
        if dn in actuals and all(len((by_dn.get(dn) or {}).get(b) or []) >= 5 for b in BRAINS)
    ]

    baseline_fps: dict[int, tuple] = {}
    for dn in dns:
        cands = trunc_candidates(by_dn[dn], policies["baseline_5_5_5"])
        baseline_fps[dn] = ticket_fp(issue_v2(cands))

    results: dict[str, Any] = {}
    for name, gen in policies.items():
        bests: list[int] = []
        identical = 0
        for dn in dns:
            cands = trunc_candidates(by_dn[dn], gen)
            issued = issue_v2(cands)
            if not issued:
                continue
            fp = ticket_fp(issued)
            if fp == baseline_fps[dn]:
                identical += 1
            actual = actuals[dn]
            best = max(len(set(c["nums"]) & actual) for c in issued)
            bests.append(best)
        sm = summarize(bests)
        p_null = (
            float(binomtest(sm["ge3"], sm["n"], NULL_GE3, alternative="greater").pvalue)
            if sm["n"]
            else 1.0
        )
        results[name] = {
            "gen": gen,
            "pool_sum": sum(gen.values()),
            "fillable": fillable(gen),
            "identical_to_baseline_rate": round(identical / max(1, sm["n"]), 4),
            "identical_n": identical,
            **sm,
            "delta_ge3_vs_v2pin": round(sm["ge3_rate"] - V2_GE3, 4),
            "p_vs_null": round(p_null, 6),
        }
    return {"n_draws": len(dns), "policies": results}


def part_b_live(actuals: dict[int, set[int]], dns: list[int]) -> dict[str, Any]:
    """live predict_sets(n) per brain · V2 wire · no AUX (fillable set_no만 사용)."""
    needed: dict[str, set[int]] = {b: set() for b in BRAINS}
    for m, s, r in LIVE_MIXES.values():
        needed["markov"].add(m)
        needed["stat"].add(s)
        needed["review"].add(r)

    # cache: dn -> tag -> n_sets -> list[cand]
    cache: dict[int, dict[str, dict[int, list[dict[str, Any]]]]] = {}
    t_gen = 0.0
    for i, dn in enumerate(dns):
        set_learn_as_of(int(dn))
        hist = _get_draws_before(dn)
        if not hist:
            continue
        cache[dn] = {b: {} for b in BRAINS}
        t0 = time.perf_counter()
        for tag in BRAINS:
            for n in sorted(needed[tag]):
                if n <= 0:
                    cache[dn][tag][n] = []
                    continue
                raw = MODS[tag].predict_sets(hist, n)
                cands: list[dict[str, Any]] = []
                for j, s in enumerate(raw):
                    nums = [int(x) for x in (s.get("nums") or [])]
                    if len(nums) != 6:
                        continue
                    sn = int(s.get("rank") or s.get("set_no") or (j + 1))
                    cands.append(
                        {
                            "nums": sorted(nums),
                            "brain_tag": tag,
                            "confidence": float(s.get("confidence") or 50),
                            "set_no": sn,
                            "pred_set_no": sn,
                            "method": s.get("method") or tag,
                        }
                    )
                cache[dn][tag][n] = cands
        t_gen += time.perf_counter() - t0
        if (i + 1) % 100 == 0:
            print(f"  live gen {i+1}/{len(dns)} elapsed_gen={t_gen:.1f}s", flush=True)

    usable = [dn for dn in dns if dn in cache and dn in actuals]
    # sanity: n_sets changes set1?
    sanity_n = 0
    sanity_diff = 0
    for dn in usable[:50]:
        for tag in BRAINS:
            if 3 in cache[dn][tag] and 5 in cache[dn][tag]:
                a = cache[dn][tag][3]
                b = cache[dn][tag][5]
                if a and b:
                    sanity_n += 1
                    if tuple(a[0]["nums"]) != tuple(b[0]["nums"]):
                        sanity_diff += 1

    results: dict[str, Any] = {}
    baseline_fps: dict[int, tuple] = {}
    base = LIVE_MIXES["baseline_5_5_5"]
    for dn in usable:
        cands: list[dict[str, Any]] = []
        for tag, n in zip(BRAINS, base):
            cands.extend(cache[dn][tag].get(n) or [])
        baseline_fps[dn] = ticket_fp(issue_v2(cands))

    for name, (nm, ns, nr) in LIVE_MIXES.items():
        gen = {"markov": nm, "stat": ns, "review": nr}
        bests: list[int] = []
        identical = 0
        for dn in usable:
            cands = []
            for tag, n in zip(BRAINS, (nm, ns, nr)):
                cands.extend(cache[dn][tag].get(n) or [])
            issued = issue_v2(cands)
            if len(issued) < 5:
                # still score if any
                if not issued:
                    continue
            fp = ticket_fp(issued)
            if fp == baseline_fps.get(dn):
                identical += 1
            actual = actuals[dn]
            best = max(len(set(c["nums"]) & actual) for c in issued)
            bests.append(best)
        sm = summarize(bests)
        p_null = (
            float(binomtest(sm["ge3"], sm["n"], NULL_GE3, alternative="greater").pvalue)
            if sm["n"]
            else 1.0
        )
        results[name] = {
            "gen": gen,
            "pool_sum": nm + ns + nr,
            "fillable": fillable(gen),
            "identical_to_live_baseline_rate": round(identical / max(1, sm["n"]), 4),
            **sm,
            "delta_ge3_vs_v2pin": round(sm["ge3_rate"] - V2_GE3, 4),
            "delta_mean_vs_v2pin": round(sm["mean"] - V2_MEAN, 4),
            "p_vs_null": round(p_null, 6),
        }

    base_sm = results["baseline_5_5_5"]
    for name, row in results.items():
        row["delta_ge3_vs_live_baseline"] = round(row["ge3_rate"] - base_sm["ge3_rate"], 4)
        row["delta_mean_vs_live_baseline"] = round(row["mean"] - base_sm["mean"], 4)

    return {
        "n_draws": len(usable),
        "gen_elapsed_sec": round(t_gen, 1),
        "sanity_nsets_set1_diff_rate": round(sanity_diff / max(1, sanity_n), 4),
        "sanity_n": sanity_n,
        "policies": results,
    }


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    actuals, by_dn = load_stored(con)
    con.close()

    print("Part A trunc…", flush=True)
    part_a = part_a_trunc(actuals, by_dn)

    dns = [
        dn
        for dn in range(D_LO, D_HI + 1)
        if dn in actuals and all(len((by_dn.get(dn) or {}).get(b) or []) >= 5 for b in BRAINS)
    ]
    print(f"Part B live regen n={len(dns)} mixes={len(LIVE_MIXES)}…", flush=True)
    part_b = part_b_live(actuals, dns)

    live_pols = part_b["policies"]
    base = live_pols["baseline_5_5_5"]
    ranked = sorted(
        live_pols.items(),
        key=lambda kv: (kv[1]["ge3_rate"], kv[1]["mean"]),
        reverse=True,
    )
    best_name, best = ranked[0]
    delta_vs_live = best["ge3_rate"] - base["ge3_rate"]
    delta_vs_pin = best["ge3_rate"] - V2_GE3

    # fillable trunc identity check
    trunc_fillable_identical = all(
        v["identical_to_baseline_rate"] >= 0.999
        for k, v in part_a["policies"].items()
        if v["fillable"] and k != "baseline_5_5_5"
    )

    pass_gate = bool(
        best_name != "baseline_5_5_5"
        and delta_vs_live >= DELTA_GE3_HIT
        and best["ge3_rate"] > V2_GE3
        and best["p_vs_null"] < ALPHA
    )

    gates = {
        "live_baseline_near_v2pin": bool(abs(base["ge3_rate"] - V2_GE3) < 0.01),
        "trunc_fillable_identical": trunc_fillable_identical,
        "best_vs_live_delta_ge3": round(delta_vs_live, 4),
        "best_vs_pin_delta_ge3": round(delta_vs_pin, 4),
        "delta_hit": DELTA_GE3_HIT,
        "PASS": pass_gate,
    }

    code_lever = {
        "SETS_PER_PREDICT_BRAIN": 5,
        "per_brain_gen_dict": None,
        "note": "균등 정수 1개만 · 뇌별 생성개수 레버는 코드에 없음(관측=가상 n_sets)",
        "issue_lever_unchanged": {"MARKOV_WIRE_BRAIN_QUOTA": QUOTA, "method": "set_no_asc"},
    }

    payload = {
        "id": "K-GENMIX",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "db_code_write": False,
        "axis": {
            "id": "K-GENMIX",
            "hypothesis": (
                "뇌별 predict_sets(n_sets) 비율을 바꾸면 diversify_pick 산출이 달라지고 "
                "V2 set_no_asc(m3+s1+r1) 발권 후 best-of-5 ge3가 개선된다"
            ),
            "orthogonal_to_v2": True,
            "why_not_forbidden_rehash": (
                "AUX가중·슬롯재픽(SUM/BAND/EV/SETNO/SETPACK)·GENDIV(Jaccard)·TUNE 미사용. "
                "생성 n_sets(풀 구성)만 변경 · 발권 쿼터/set_no_asc 고정. "
                "SETCOUNT는 장수/null 분리·본축은 동일5장·뇌별비율."
            ),
        },
        "code_lever": code_lever,
        "v2_pin": {"ge3": V2_GE3, "mean": V2_MEAN, "quota": QUOTA},
        "part_a_trunc": part_a,
        "part_b_live": part_b,
        "best_live": {
            "name": best_name,
            **best,
        },
        "gates": gates,
        "recommended_next": (
            None
            if not pass_gate
            else "K-GENMIX-WIRE 검토(coordinator에 뇌별 n_sets dict · 형 승인)"
        ),
        "note": (
            "Part A: stored trunc는 fillable 시 티켓동일(구조적 null). "
            "Part B: live n_sets가 실레버(set1 불일치 확인). AUX/DB 미기록."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"gates": gates, "best_live": payload["best_live"], "baseline": base}, ensure_ascii=False, indent=2))
    print(f"wrote {OUT} PASS={pass_gate}", flush=True)


if __name__ == "__main__":
    main()
