# -*- coding: utf-8 -*-
"""K-TRUST-BENCH + K-CREW — 신뢰 벤치 + 3뇌·4보조 '사공' 효율 (READ-ONLY).

산출:
  docs/benchmarks/20260729_KTRUST_bench.json
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KTRUST_bench.json"

# BENCH_PROTOCOL
NULL_MEAN_1SET = 0.8  # 6*(6/45)
BEST_OF_15_CEILING = 2.27  # documented constant
WINDOWS = {
    "full_2_1234": (2, 1234),
    "recent_100": (1135, 1234),
    "recent_200": (1035, 1234),
    "mid_500": (735, 1234),
}


def _hyper_mean(k: int = 6, K: int = 6, N: int = 45) -> float:
    return k * (K / N)


def _mc_best_of_n(n_sets: int, trials: int = 8000, seed: int = 42) -> dict[str, float]:
    """Random tickets: mean of best-of-n matched vs one draw (approx null)."""
    rng = random.Random(seed + n_sets)
    bests: list[int] = []
    means: list[float] = []
    ge3 = 0
    ge4 = 0
    for _ in range(trials):
        actual = set(rng.sample(range(1, 46), 6))
        matches = []
        for _s in range(n_sets):
            pred = set(rng.sample(range(1, 46), 6))
            matches.append(len(pred & actual))
        b = max(matches)
        bests.append(b)
        means.append(sum(matches) / len(matches))
        if b >= 3:
            ge3 += 1
        if b >= 4:
            ge4 += 1
    return {
        "n_sets": n_sets,
        "trials": trials,
        "best_mean": round(sum(bests) / len(bests), 4),
        "allset_mean": round(sum(means) / len(means), 4),
        "best_ge3_rate": round(ge3 / trials, 4),
        "best_ge4_rate": round(ge4 / trials, 4),
    }


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 1.0
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def _parse_best_nums(predicted_sets_json: str, best_set_no: int, predicted_nums: str | None) -> list[int]:
    try:
        sets = json.loads(predicted_sets_json or "[]")
        best = next(
            (s for s in sets if int(s.get("set_no") or 0) == int(best_set_no)),
            sets[int(best_set_no) - 1] if sets else {},
        )
        nums = [int(n) for n in (best.get("nums") or [])]
        if nums:
            return nums
    except Exception:
        pass
    if predicted_nums:
        parts = str(predicted_nums).replace(",", " ").split()
        return [int(x) for x in parts if x.isdigit()][:6]
    return []


def _all_set_matches(predicted_sets_json: str, actual: set[int]) -> list[int]:
    try:
        sets = json.loads(predicted_sets_json or "[]")
    except Exception:
        return []
    out = []
    for s in sets:
        nums = set(int(n) for n in (s.get("nums") or []))
        out.append(len(nums & actual))
    return out


def window_stats(rows_by_brain: dict[str, list[sqlite3.Row]], lo: int, hi: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for tag, rows in rows_by_brain.items():
        ms = [int(r["matched_count"]) for r in rows if lo <= int(r["draw_no"]) <= hi]
        if not ms:
            out[tag] = {"n": 0}
            continue
        n = len(ms)
        out[tag] = {
            "n": n,
            "best_mean": round(sum(ms) / n, 4),
            "ge3": sum(1 for m in ms if m >= 3),
            "ge3_rate": round(sum(1 for m in ms if m >= 3) / n, 4),
            "ge4": sum(1 for m in ms if m >= 4),
            "ge4_rate": round(sum(1 for m in ms if m >= 4) / n, 4),
            "ge5": sum(1 for m in ms if m >= 5),
            "ge6": sum(1 for m in ms if m >= 6),
        }
    return out


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    rows = con.execute(
        """
        SELECT draw_no, brain_tag, matched_count, bonus_matched,
               predicted_sets_json, best_set_no, predicted_nums
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN 2 AND 1234
        ORDER BY draw_no, brain_tag
        """
    ).fetchall()

    by_brain: dict[str, list[sqlite3.Row]] = defaultdict(list)
    by_draw: dict[int, dict[str, sqlite3.Row]] = defaultdict(dict)
    for r in rows:
        by_brain[r["brain_tag"]].append(r)
        by_draw[int(r["draw_no"])][r["brain_tag"]] = r

    # actuals
    actuals = {
        int(r[0]): set(int(r[i]) for i in range(1, 7))
        for r in con.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no BETWEEN 2 AND 1234"
        )
    }

    # --- TRUST windows ---
    trust_windows = {}
    for name, (lo, hi) in WINDOWS.items():
        st = window_stats(by_brain, lo, hi)
        trust_windows[name] = {
            "range": [lo, hi],
            "brains": st,
            "null_1set_mean": NULL_MEAN_1SET,
            "note": "brain best_mean = review best-set matched (not all-5-set mean)",
        }

    # all-set mean (BENCH_PROTOCOL preferred) for recent_100 + full — sample parse
    allset_means: dict[str, Any] = {}
    for win_name, (lo, hi) in [("full_2_1234", (2, 1234)), ("recent_100", (1135, 1234))]:
        tag_sums: dict[str, list[float]] = defaultdict(list)
        for d in range(lo, hi + 1):
            act = actuals.get(d)
            if not act:
                continue
            for tag, r in by_draw.get(d, {}).items():
                ms = _all_set_matches(r["predicted_sets_json"], act)
                if ms:
                    tag_sums[tag].append(sum(ms) / len(ms))
        allset_means[win_name] = {
            tag: {
                "n": len(vs),
                "all5_mean": round(sum(vs) / len(vs), 4) if vs else 0,
                "delta_vs_null08": round((sum(vs) / len(vs)) - NULL_MEAN_1SET, 4) if vs else 0,
            }
            for tag, vs in sorted(tag_sums.items())
        }

    # MC null for best-of-5 / best-of-15
    null_mc = {
        "best_of_1": _mc_best_of_n(1, trials=5000),
        "best_of_5": _mc_best_of_n(5, trials=5000),
        "best_of_15": _mc_best_of_n(15, trials=5000),
        "doc_ceiling_best15": BEST_OF_15_CEILING,
    }

    # --- CREW / 사공 analysis ---
    jacc_pairs: dict[str, list[float]] = defaultdict(list)
    match_corr_pairs: dict[str, list[tuple[float, float]]] = defaultdict(list)
    per_draw_max: list[int] = []
    per_draw_mean: list[float] = []
    unique_union15: list[int] = []
    unique_one_brain5: list[int] = []
    pool15_best: list[int] = []
    single5_best: dict[str, list[int]] = defaultdict(list)
    same_draw_ge4_brains: list[dict[str, Any]] = []
    both_ge3: int = 0
    draws_complete = 0

    tags = ["stat", "markov", "review"]
    pairs = [("stat", "markov"), ("stat", "review"), ("markov", "review")]

    for d, br in by_draw.items():
        if not all(t in br for t in tags):
            continue
        act = actuals.get(d)
        if not act:
            continue
        draws_complete += 1
        nums = {}
        matches = {}
        all_matches = {}
        for t in tags:
            r = br[t]
            nums[t] = set(_parse_best_nums(r["predicted_sets_json"], int(r["best_set_no"]), r["predicted_nums"]))
            matches[t] = int(r["matched_count"])
            all_matches[t] = _all_set_matches(r["predicted_sets_json"], act)
            single5_best[t].append(matches[t])

        for a, b in pairs:
            jacc_pairs[f"{a}|{b}"].append(_jaccard(nums[a], nums[b]))
            match_corr_pairs[f"{a}|{b}"].append((float(matches[a]), float(matches[b])))

        mx = max(matches.values())
        per_draw_max.append(mx)
        per_draw_mean.append(sum(matches.values()) / 3)
        if sum(1 for m in matches.values() if m >= 3) >= 2:
            both_ge3 += 1
        ge4_tags = [t for t, m in matches.items() if m >= 4]
        if len(ge4_tags) >= 2:
            same_draw_ge4_brains.append({"draw": d, "brains": ge4_tags})

        # pool 15 unique + best
        pool_ms = []
        union = set()
        for t in tags:
            r = br[t]
            try:
                sets = json.loads(r["predicted_sets_json"] or "[]")
            except Exception:
                sets = []
            for s in sets:
                ns = [int(n) for n in (s.get("nums") or [])]
                union |= set(ns)
                pool_ms.append(len(set(ns) & act))
            unique_one_brain5.append(
                len({n for s in sets for n in (s.get("nums") or [])})
            )
        unique_union15.append(len(union))
        pool15_best.append(max(pool_ms) if pool_ms else 0)

    def _pearson(pairs_ab: list[tuple[float, float]]) -> float | None:
        if len(pairs_ab) < 3:
            return None
        xs = [p[0] for p in pairs_ab]
        ys = [p[1] for p in pairs_ab]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        deny = math.sqrt(sum((y - my) ** 2 for y in ys))
        if denx == 0 or deny == 0:
            return None
        return round(num / (denx * deny), 4)

    crew = {
        "draws_with_3brains": draws_complete,
        "pairwise_jaccard_bestset_mean": {
            k: round(sum(v) / len(v), 4) for k, v in sorted(jacc_pairs.items()) if v
        },
        "pairwise_matched_pearson": {
            k: _pearson(v) for k, v in sorted(match_corr_pairs.items())
        },
        "per_draw_max_matched_mean": round(sum(per_draw_max) / len(per_draw_max), 4)
        if per_draw_max
        else 0,
        "per_draw_mean_of_3_mean": round(sum(per_draw_mean) / len(per_draw_mean), 4)
        if per_draw_mean
        else 0,
        "oracle_gain_max_minus_mean": round(
            (sum(per_draw_max) - sum(per_draw_mean)) / len(per_draw_max), 4
        )
        if per_draw_max
        else 0,
        "draws_with_2plus_brains_ge3": both_ge3,
        "draws_with_2plus_brains_ge3_rate": round(both_ge3 / draws_complete, 4)
        if draws_complete
        else 0,
        "same_draw_multi_brain_ge4": same_draw_ge4_brains,
        "unique_nums_mean_one_brain_5sets": round(
            sum(unique_one_brain5) / len(unique_one_brain5), 2
        )
        if unique_one_brain5
        else 0,
        "unique_nums_mean_union_3x5": round(sum(unique_union15) / len(unique_union15), 2)
        if unique_union15
        else 0,
        "pool15_best_mean": round(sum(pool15_best) / len(pool15_best), 4)
        if pool15_best
        else 0,
        "pool15_ge4_rate": round(sum(1 for x in pool15_best if x >= 4) / len(pool15_best), 4)
        if pool15_best
        else 0,
        "single_brain_best_mean": {
            t: round(sum(vs) / len(vs), 4) for t, vs in sorted(single5_best.items())
        },
        "aux_note": (
            "AUX 4뇌는 nums를 바꾸지 않고 confidence/reasoning만 부여(K-PIPE). "
            "brain_review best 채점은 실당첨 대비 tier — AUX가 matched_count를 직접 만들지 않음. "
            "라이브 발권 순서에만 AUX·referee 가중 영향."
        ),
    }

    # efficiency verdict helpers
    # If brains highly correlated (jaccard high + pearson high) → redundancy (사공)
    j_vals = list(crew["pairwise_jaccard_bestset_mean"].values())
    p_vals = [v for v in crew["pairwise_matched_pearson"].values() if v is not None]
    avg_j = round(sum(j_vals) / len(j_vals), 4) if j_vals else 0
    avg_p = round(sum(p_vals) / len(p_vals), 4) if p_vals else 0

    verdict = {
        "question_a": "역할분담(3+4) 유지 vs 뇌 줄이고 세트 늘리기",
        "evidence": {
            "avg_pairwise_jaccard_bestset": avg_j,
            "avg_pairwise_matched_pearson": avg_p,
            "union_unique_vs_single5": {
                "union_3x5": crew["unique_nums_mean_union_3x5"],
                "single_5": crew["unique_nums_mean_one_brain_5sets"],
                "extra_coverage": round(
                    crew["unique_nums_mean_union_3x5"] - crew["unique_nums_mean_one_brain_5sets"], 2
                ),
            },
            "pool15_best_vs_null_mc": {
                "observed_pool15_best_mean": crew["pool15_best_mean"],
                "null_mc_best15_mean": null_mc["best_of_15"]["best_mean"],
                "delta": round(crew["pool15_best_mean"] - null_mc["best_of_15"]["best_mean"], 4),
            },
            "multi_brain_ge4_same_draw": len(same_draw_ge4_brains),
        },
        "interpretation": [],
        "recommendation": "",
    }

    # interpretation rules
    if avg_j >= 0.45:
        verdict["interpretation"].append(
            f"best-set Jaccard≈{avg_j}: 뇌 간 번호 겹침 큼 → 예측 다양성 약함(사공 위험 신호)"
        )
    elif avg_j <= 0.25:
        verdict["interpretation"].append(
            f"best-set Jaccard≈{avg_j}: 뇌 간 번호 분리 양호 → 역할분담 공간 있음"
        )
    else:
        verdict["interpretation"].append(
            f"best-set Jaccard≈{avg_j}: 중간 겹침 — 완전 중복도 완전 분업도 아님"
        )

    if avg_p is not None and avg_p >= 0.35:
        verdict["interpretation"].append(
            f"matched Pearson≈{avg_p}: 성적도 같이 움직임 → 앙상블 이득 제한"
        )
    elif avg_p is not None and avg_p <= 0.15:
        verdict["interpretation"].append(
            f"matched Pearson≈{avg_p}: 성적 상관 낮음 → 보완 가능성"
        )
    else:
        verdict["interpretation"].append(
            f"matched Pearson≈{avg_p}: 약한~중간 상관"
        )

    extra = verdict["evidence"]["union_unique_vs_single5"]["extra_coverage"]
    verdict["interpretation"].append(
        f"3×5 합집합 고유번호가 단일5 대비 +{extra}개 — "
        + ("커버 이득 있음" if extra >= 8 else "커버 이득 작음(중복 다수)")
    )

    delta_null = verdict["evidence"]["pool15_best_vs_null_mc"]["delta"]
    verdict["interpretation"].append(
        f"pool15 best mean − null MC best15 = {delta_null} "
        + ("(null 근처·우위 주장 금지)" if abs(delta_null) < 0.15 else "(추가 검증 필요)")
    )

    # recommendation
    if avg_j >= 0.4 and extra < 8:
        rec = (
            "사공 신호 강함: 뇌 수 유지보다 **세트 다양성·단일뇌 깊이** 실험이 우선. "
            "다만 AUX는 nums 불변이라 '줄이기' 전에 명분(WARRANT) 라벨부터 정리."
        )
    elif avg_j <= 0.28 and extra >= 10:
        rec = (
            "역할분담 이득 관측: **3예측 유지**가 합리적. "
            "세트만 늘리면(1뇌×15) 같은 생성기 복제라 다양성≠보장. "
            "다음=생성 정책 다양화 검증."
        )
    else:
        rec = (
            "중간 판정: **지금 당장 뇌 축소 비권고**. "
            "효율 개선은 (1) random baseline 정직 보고 (2) 패턴AUX 조건부 slice "
            "(3) set 생성 다양성 — 사공 해소는 '뇌 삭제'보다 **중복 제거·역할 선명화**."
        )
    verdict["recommendation"] = rec

    external = {
        "sources": [
            "arXiv ensemble diversity bias-variance-diversity tradeoff",
            "Metaculus AI crowd: accurate+diverse > more correlated copies",
            "BENCH_PROTOCOL K-O: mean alone cannot rank brains",
            "LottoWise: fair lottery no learnable next-ball",
        ],
        "consensus": [
            "correlated ensemble members → diminishing returns (사공)",
            "diversity without individual quality can hurt",
            "for lottery, more tickets mainly buy best-of-N ceiling, not skill",
            "ROK21: keep role labels if complementary; do not add brains for marketing",
        ],
    }

    payload = {
        "id": "K-TRUST-BENCH",
        "also": "K-CREW",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "window_full": [2, 1234],
        "trust": {
            "windows": trust_windows,
            "all5_set_means": allset_means,
            "null_mc": null_mc,
            "protocol": "BENCH_PROTOCOL.md · null 0.8 · best15 ceiling 2.27",
        },
        "crew": crew,
        "verdict": verdict,
        "external_ai": external,
        "pattern1_link": "docs/benchmarks/20260729_KPATTERN_tier4_vs_control.json",
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print("recent100 all5", allset_means.get("recent_100"))
    print("full best windows brains", {k: trust_windows["full_2_1234"]["brains"][k] for k in tags})
    print("jaccard", crew["pairwise_jaccard_bestset_mean"])
    print("pearson", crew["pairwise_matched_pearson"])
    print("union", crew["unique_nums_mean_union_3x5"], "single5", crew["unique_nums_mean_one_brain_5sets"])
    print("pool15", crew["pool15_best_mean"], "null15", null_mc["best_of_15"]["best_mean"])
    print("REC:", rec)
    con.close()


if __name__ == "__main__":
    main()
