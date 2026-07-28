# -*- coding: utf-8 -*-
"""K-SETPACK-TOP6 — 번호점수 top6을 set1 강제 재조립 (READ-ONLY).

기존 배선 파일 미수정. DB mode=ro.
풀: testlotto_brain_review · brains stat/markov/review · draw 53~1234.
산출: docs/benchmarks/20260729_KSETPACK_top6.json

알고리즘 (재현):
  1) 뇌·회차별 기존 5세트 nums 로드
  2) 번호점수 = 5세트 출현횟수 (동점 시 번호 오름차순)
     (민감도: conf_sum = 해당 번호가 속한 세트의 confidence 합)
  3) set1 = 점수 top6
  4) set2~5: 기존 set_no 2~5에서 set1 번호 제거 후,
     set1과 비중복 우선·점수 내림차순으로 6개까지 보충
     (부족 시 set1 번호도 허용, 점수 오름차순=약한 번호부터)
  5) GATHER와 구분: set1만 몰아주기(교차세트 스티치/독립집합 없음)
"""
from __future__ import annotations

import json
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KSETPACK_top6.json"

BRAINS = ("stat", "markov", "review")
D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137  # null_n5


def summarize(ms: list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {
            "n": 0,
            "mean": 0.0,
            "ge3": 0,
            "ge3_rate": 0.0,
            "ge4": 0,
            "ge4_rate": 0.0,
        }
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


def binom_p(ge3_count: int, n: int, p0: float = NULL_GE3) -> float:
    if n <= 0:
        return 1.0
    return float(binomtest(ge3_count, n, p0, alternative="greater").pvalue)


def score_by_count(sets: list[dict]) -> dict[int, float]:
    c: Counter[int] = Counter()
    for s in sets:
        for n in s["nums"]:
            c[n] += 1
    return {n: float(v) for n, v in c.items()}


def score_by_conf_sum(sets: list[dict]) -> dict[int, float]:
    acc: dict[int, float] = defaultdict(float)
    for s in sets:
        conf = float(s.get("confidence") or 0)
        for n in s["nums"]:
            acc[n] += conf
    return dict(acc)


def top6(scores: dict[int, float]) -> tuple[int, ...]:
    # 점수 내림 · 번호 오름 (재현)
    ranked = sorted(scores.keys(), key=lambda n: (-scores[n], n))
    # 점수가 없는 번호는 풀에 없음 — 부족 시 1..45에서 0점 보충
    if len(ranked) < 6:
        for n in range(1, 46):
            if n not in scores:
                ranked.append(n)
            if len(ranked) >= 6:
                break
    return tuple(sorted(ranked[:6]))


def refill_set(
    keep: set[int],
    set1: set[int],
    scores: dict[int, float],
) -> tuple[int, ...]:
    """set1 중복 최소화하며 6개 채움."""
    cur = set(keep) - set1  # set1 제거
    # 후보1: set1 밖, 점수 내림·번호 오름
    pool_out = [n for n in range(1, 46) if n not in set1 and n not in cur]
    pool_out.sort(key=lambda n: (-scores.get(n, 0.0), n))
    for n in pool_out:
        if len(cur) >= 6:
            break
        cur.add(n)
    # 후보2: 여전히 부족 → set1에서 약한 번호(점수 오름·번호 오름)
    if len(cur) < 6:
        pool_in = sorted(set1 - cur, key=lambda n: (scores.get(n, 0.0), n))
        for n in pool_in:
            if len(cur) >= 6:
                break
            cur.add(n)
    # 후보3: 최후 — 임의 잔여
    if len(cur) < 6:
        for n in range(1, 46):
            if n not in cur:
                cur.add(n)
            if len(cur) >= 6:
                break
    return tuple(sorted(cur))


def repack_top6(
    sets: list[dict],
    scores: dict[int, float],
) -> list[tuple[int, ...]]:
    """set1=top6, set2~5=기존 set_no 순서 재조립."""
    ordered = sorted(sets, key=lambda s: int(s.get("set_no") or s.get("rank") or 0))
    if len(ordered) < 5:
        return []
    s1 = top6(scores)
    s1set = set(s1)
    out: list[tuple[int, ...]] = [s1]
    # 기존 2~5번째 세트 기준 (set_no 정렬 후 index 1..4)
    for s in ordered[1:5]:
        keep = set(s["nums"])
        out.append(refill_set(keep, s1set, scores))
    return out


def best_match(sets: list[tuple[int, ...]], actual: set[int]) -> int:
    if not sets:
        return 0
    return max(len(set(s) & actual) for s in sets)


def set1_match(sets: list[tuple[int, ...]], actual: set[int]) -> int:
    if not sets:
        return 0
    return len(set(sets[0]) & actual)


def load_all(con: sqlite3.Connection) -> tuple[
    dict[int, set[int]],
    dict[int, dict[str, list[dict]]],
]:
    draws: dict[int, set[int]] = {}
    for r in con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ?",
        (D_LO, D_HI),
    ):
        draws[int(r[0])] = {int(r[i]) for i in range(1, 7)}

    by_dn: dict[int, dict[str, list[dict]]] = defaultdict(dict)
    for r in con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE brain_tag IN (?,?,?) AND draw_no BETWEEN ? AND ?",
        (*BRAINS, D_LO, D_HI),
    ):
        dn = int(r[0])
        tag = str(r[1])
        try:
            raw = json.loads(r[2] or "[]")
        except json.JSONDecodeError:
            continue
        parsed: list[dict] = []
        for i, s in enumerate(raw[:5]):
            nums = tuple(sorted(int(x) for x in (s.get("nums") or [])))
            if len(nums) != 6:
                continue
            parsed.append(
                {
                    "nums": nums,
                    "confidence": float(s.get("confidence") or 0),
                    "set_no": int(s.get("set_no") or s.get("rank") or (i + 1)),
                    "rank": int(s.get("rank") or (i + 1)),
                }
            )
        if len(parsed) >= 5:
            by_dn[dn][tag] = parsed[:5]
    return draws, {dn: dict(v) for dn, v in by_dn.items()}


def eval_brain(
    draws: dict[int, set[int]],
    by_dn: dict[int, dict[str, list[dict]]],
    brain: str,
    score_fn,
) -> dict[str, Any]:
    base_best: list[int] = []
    base_s1: list[int] = []
    pack_best: list[int] = []
    pack_s1: list[int] = []
    n_skip = 0

    for dn in range(D_LO, D_HI + 1):
        actual = draws.get(dn)
        sets = (by_dn.get(dn) or {}).get(brain)
        if not actual or not sets or len(sets) < 5:
            n_skip += 1
            continue
        base_tuples = [tuple(s["nums"]) for s in sorted(sets, key=lambda x: x["set_no"])]
        base_best.append(best_match(base_tuples, actual))
        base_s1.append(set1_match(base_tuples, actual))

        scores = score_fn(sets)
        packed = repack_top6(sets, scores)
        if len(packed) < 5:
            n_skip += 1
            continue
        pack_best.append(best_match(packed, actual))
        pack_s1.append(set1_match(packed, actual))

    sb = summarize(base_best)
    ss1 = summarize(base_s1)
    pb = summarize(pack_best)
    ps1 = summarize(pack_s1)
    p_null = binom_p(pb["ge3"], pb["n"])
    p_base = binom_p(sb["ge3"], sb["n"])

    gate_ge3_gt_base = pb["ge3_rate"] > sb["ge3_rate"]
    gate_p_lt_05 = p_null < 0.05
    passed = gate_ge3_gt_base and gate_p_lt_05

    return {
        "brain": brain,
        "n_eval": pb["n"],
        "n_skip_hint": n_skip,
        "baseline_5": {
            "best": sb,
            "set1": ss1,
            "binom_p_vs_null": round(p_base, 6),
        },
        "setpack_top6": {
            "best": pb,
            "set1": ps1,
            "binom_p_vs_null": round(p_null, 6),
        },
        "delta_vs_baseline": {
            "best_mean": round(pb["mean"] - sb["mean"], 4),
            "best_ge3_rate": round(pb["ge3_rate"] - sb["ge3_rate"], 4),
            "set1_mean": round(ps1["mean"] - ss1["mean"], 4),
            "ge4_rate": round(pb["ge4_rate"] - sb["ge4_rate"], 4),
        },
        "gates": {
            "best_ge3_gt_baseline": gate_ge3_gt_base,
            "binom_p_vs_null_lt_0_05": gate_p_lt_05,
            "pass": passed,
        },
    }


def pooled_metrics(per_brain: list[dict[str, Any]], key_path: str) -> dict[str, Any]:
    """뇌별 n·ge3 합산 후 재계산 (전체 풀)."""
    # key_path: "baseline_5.best" or "setpack_top6.best"
    parts = key_path.split(".")
    ge3 = 0
    ge4 = 0
    n = 0
    mean_acc = 0.0
    for b in per_brain:
        node = b
        for p in parts:
            node = node[p]
        n_i = int(node["n"])
        ge3 += int(node["ge3"])
        ge4 += int(node["ge4"])
        mean_acc += float(node["mean"]) * n_i
        n += n_i
    if n <= 0:
        return summarize([])
    return {
        "n": n,
        "mean": round(mean_acc / n, 4),
        "ge3": ge3,
        "ge3_rate": round(ge3 / n, 4),
        "ge4": ge4,
        "ge4_rate": round(ge4 / n, 4),
        "binom_p_vs_null": round(binom_p(ge3, n), 6),
    }


def main() -> None:
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    draws, by_dn = load_all(con)
    con.close()

    print("[K-SETPACK-TOP6] count scoring ...", flush=True)
    per_count: list[dict[str, Any]] = []
    for brain in BRAINS:
        r = eval_brain(draws, by_dn, brain, score_by_count)
        per_count.append(r)
        g = r["gates"]
        print(
            f"  {brain} base_ge3={r['baseline_5']['best']['ge3_rate']} "
            f"pack_ge3={r['setpack_top6']['best']['ge3_rate']} "
            f"set1_mean {r['baseline_5']['set1']['mean']}→{r['setpack_top6']['set1']['mean']} "
            f"p_null={r['setpack_top6']['binom_p_vs_null']} pass={g['pass']}",
            flush=True,
        )

    print("[K-SETPACK-TOP6] conf_sum scoring (sensitivity) ...", flush=True)
    per_conf: list[dict[str, Any]] = []
    for brain in BRAINS:
        r = eval_brain(draws, by_dn, brain, score_by_conf_sum)
        per_conf.append(r)
        print(
            f"  {brain} pack_ge3={r['setpack_top6']['best']['ge3_rate']} "
            f"pass={r['gates']['pass']}",
            flush=True,
        )

    # primary = count
    any_pass = any(r["gates"]["pass"] for r in per_count)
    all_pass = all(r["gates"]["pass"] for r in per_count)

    pool_base = pooled_metrics(per_count, "baseline_5.best")
    pool_pack = pooled_metrics(per_count, "setpack_top6.best")
    pool_base_s1 = pooled_metrics(per_count, "baseline_5.set1")
    pool_pack_s1 = pooled_metrics(per_count, "setpack_top6.set1")

    pool_gate_ge3 = pool_pack["ge3_rate"] > pool_base["ge3_rate"]
    pool_gate_p = pool_pack["binom_p_vs_null"] < 0.05
    pool_pass = pool_gate_ge3 and pool_gate_p

    if any_pass or pool_pass:
        recommended = "K-SETPACK-WIRE"
        verdict = (
            f"PASS 후보: any_brain_pass={any_pass} pool_pass={pool_pass}. "
            f"pool pack ge3={pool_pack['ge3_rate']} vs base {pool_base['ge3_rate']} "
            f"p_null={pool_pack['binom_p_vs_null']}."
        )
    else:
        recommended = "없음"
        verdict = (
            f"FAIL: setpack best ge3가 현행5를 넘지 못하거나 null p≥0.05. "
            f"pool pack ge3={pool_pack['ge3_rate']} base={pool_base['ge3_rate']} "
            f"p_null={pool_pack['binom_p_vs_null']}."
        )

    out = {
        "id": "K-SETPACK-TOP6",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "draw_range": [D_LO, D_HI],
        "brains": list(BRAINS),
        "source": "testlotto_brain_review predicted_sets_json",
        "db_code_write": False,
        "null_n5": {"null_ge3": NULL_GE3, "note": "5세트 best-of null"},
        "method": {
            "primary_score": "appearance_count_across_5_sets",
            "sensitivity_score": "confidence_sum_across_sets_containing_number",
            "set1": "top6 by score desc, tie=number asc",
            "set2_to_5": (
                "existing set_no 2..5 minus set1 nums; "
                "refill preferring non-set1 by score desc; "
                "if short allow set1 by score asc"
            ),
            "vs_gather": (
                "GATHER=교차세트 스티치/독립집합으로 승자 모으기 시도; "
                "SETPACK=번호점수 top6만 set1에 몰아주기 (스티치 없음)"
            ),
        },
        "gates_definition": {
            "pass_per_brain": "setpack best ge3_rate > baseline best ge3_rate AND binom_p(ge3,n,null_ge3=0.1137,greater)<0.05",
            "pass_pool": "same on pooled 3-brain rows",
        },
        "primary_count": {
            "per_brain": per_count,
            "pool": {
                "baseline_best": pool_base,
                "setpack_best": pool_pack,
                "baseline_set1": pool_base_s1,
                "setpack_set1": pool_pack_s1,
                "delta_best_ge3": round(pool_pack["ge3_rate"] - pool_base["ge3_rate"], 4),
                "delta_best_mean": round(pool_pack["mean"] - pool_base["mean"], 4),
                "delta_set1_mean": round(pool_pack_s1["mean"] - pool_base_s1["mean"], 4),
                "gates": {
                    "best_ge3_gt_baseline": pool_gate_ge3,
                    "binom_p_vs_null_lt_0_05": pool_gate_p,
                    "pass": pool_pass,
                },
            },
            "any_brain_pass": any_pass,
            "all_brain_pass": all_pass,
        },
        "sensitivity_conf_sum": {
            "per_brain": [
                {
                    "brain": r["brain"],
                    "baseline_ge3": r["baseline_5"]["best"]["ge3_rate"],
                    "setpack_ge3": r["setpack_top6"]["best"]["ge3_rate"],
                    "setpack_set1_mean": r["setpack_top6"]["set1"]["mean"],
                    "binom_p_vs_null": r["setpack_top6"]["binom_p_vs_null"],
                    "pass": r["gates"]["pass"],
                }
                for r in per_conf
            ],
            "any_brain_pass": any(r["gates"]["pass"] for r in per_conf),
        },
        "recommended_next": recommended,
        "verdict": verdict,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "recommended_next": recommended,
        "pool": out["primary_count"]["pool"],
        "any_brain_pass": any_pass,
    }, ensure_ascii=False, indent=2))
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
