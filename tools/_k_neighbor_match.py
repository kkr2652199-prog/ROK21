# -*- coding: utf-8 -*-
"""K-NEIGHBOR-MATCH — Jaccard kNN 유사 회차 패턴 진단 (wire 없음 · SELECT-ONLY).

Usage:
  python tools/_k_neighbor_match.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KNEIGHBOR_MATCH.json"
OUT_MD = ROOT / "reports" / "20260805_KNEIGHBOR_MATCH.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

ANCHOR = 1235
BASELINE_GE3 = 0.135  # fusion ticket best_of_5 참고(지표 다름)
# Hypergeometric N=45,K=15,n=6 → P(X>=3)≈0.3114 · E[X]=2.0
RANDOM_TOP15_GE3 = 0.311375
RANDOM_TOP15_MEAN_HIT = 2.0
BT_LO, BT_HI = 1136, 1235
HIGH_LO, HIGH_HI = 1036, 1235


def jaccard(a: set[int], b: set[int]) -> float:
    u = a | b
    if not u:
        return 0.0
    return len(a & b) / len(u)


def sum_tier(s: int) -> str:
    if s < 116:
        return "low"
    if s > 160:
        return "high"
    return "mid"


def load_draws() -> list[dict[str, Any]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6
        FROM lotto_draws WHERE draw_no BETWEEN 1 AND 1235
        ORDER BY draw_no
        """
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
        out.append(
            {
                "draw_no": int(d["draw_no"]),
                "nums": nums,
                "set": set(nums),
                "sum": sum(nums),
                "sum_tier": sum_tier(sum(nums)),
            }
        )
    return out


def top_k_neighbors(
    anchor: set[int],
    draws: list[dict],
    *,
    exclude_draw: int,
    k: int,
    max_draw: int | None = None,
) -> list[dict[str, Any]]:
    """Past draws with draw_no < exclude_draw (and optionally <= max_draw)."""
    scored: list[tuple[float, int, set[int]]] = []
    for d in draws:
        dn = d["draw_no"]
        if dn >= exclude_draw:
            continue
        if max_draw is not None and dn > max_draw:
            continue
        # need next draw to exist for scoring
        if dn + 1 > draws[-1]["draw_no"]:
            continue
        sim = jaccard(anchor, d["set"])
        scored.append((sim, dn, d["set"]))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    out = []
    for sim, dn, s in scored[:k]:
        out.append({"draw_no": dn, "jaccard": round(sim, 6), "nums": sorted(s)})
    return out


def next_scores(
    neighbors: list[dict], draws_by: dict[int, dict]
) -> dict[int, int]:
    scores = {n: 0 for n in range(1, 46)}
    for nb in neighbors:
        nxt = draws_by.get(nb["draw_no"] + 1)
        if not nxt:
            continue
        for n in nxt["set"]:
            scores[n] += 1
    return scores


def scores_to_top15(scores: dict[int, int]) -> dict[str, Any]:
    ordered = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    top15 = [{"num": n, "score": sc} for n, sc in ordered[:15]]
    return {
        "top15_numbers": [x["num"] for x in top15],
        "top15_detail": top15,
        "top1_score": top15[0]["score"] if top15 else 0,
        "all_scores": {str(n): scores[n] for n in range(1, 46)},
    }


def backtest_100(draws: list[dict], draws_by: dict[int, dict]) -> dict[str, Any]:
    """For each n in 1136..1235: neighbors of D_{n-1}, score top15 vs D_n."""
    hits_ge3: list[int] = []
    hit_counts: list[int] = []
    for n in range(BT_LO, BT_HI + 1):
        prev = draws_by[n - 1]["set"]
        actual = draws_by[n]["set"]
        # neighbors among draws with next available, draw_no < n-1? 
        # "D_{n-1} 기준 top-10 유사 회차" among 1..n-2 (strict past before n-1)
        nbs = top_k_neighbors(prev, draws, exclude_draw=n - 1, k=10)
        # if exclude_draw = n-1, we search draw_no < n-1, good (no peek at n-1 itself as neighbor source for next of n-1)
        # Wait: we want similar to D_{n-1}, so candidates are draws i < n-1, then look at D_{i+1}.
        # Using D_{n-1} as anchor is correct; exclude_draw=n-1 means i < n-1. Good.
        scores = next_scores(nbs, draws_by)
        top15 = set(scores_to_top15(scores)["top15_numbers"])
        hc = len(actual & top15)
        hit_counts.append(hc)
        hits_ge3.append(1 if hc >= 3 else 0)
    rate = round(mean(hits_ge3), 6) if hits_ge3 else 0.0
    mean_hit = round(mean(hit_counts), 6) if hit_counts else 0.0
    # 1차 판정: 무작위 top15 적중 대비 (지표 동치)
    delta_rand = round(rate - RANDOM_TOP15_GE3, 6)
    # 참고: fusion 티켓 ge3와는 지표 불일치 → 판정에 쓰지 않음
    delta_fusion_ref = round(rate - BASELINE_GE3, 6)
    verdict = "VIABLE" if delta_rand >= 0.010 else "NOISE"
    return {
        "draw_range": [BT_LO, BT_HI],
        "k": 10,
        "top_m": 15,
        "n": len(hits_ge3),
        "knn_ge3_rate": rate,
        "mean_hit_in_top15": mean_hit,
        "baseline_ge3": BASELINE_GE3,
        "delta": delta_rand,
        "delta_vs_fusion_ticket_ref": delta_fusion_ref,
        "random_top15_ge3": RANDOM_TOP15_GE3,
        "random_top15_mean_hit": RANDOM_TOP15_MEAN_HIT,
        "delta_mean_hit_vs_random": round(mean_hit - RANDOM_TOP15_MEAN_HIT, 6),
        "verdict": verdict,
        "note": (
            "ge3=|D_n∩score_top15|>=3 · 판정은 Hypergeometric 무작위 대비. "
            "baseline_ge3=0.135은 fusion 티켓 참고용(지표 다름·판정 미사용)"
        ),
    }


def high_sum_analysis(draws: list[dict], draws_by: dict[int, dict]) -> dict[str, Any]:
    highs = [d for d in draws if HIGH_LO <= d["draw_no"] <= HIGH_HI and d["sum_tier"] == "high"]
    max_jacs: list[float] = []
    details = []
    for d in highs:
        # max jaccard to any past draw before this one
        best = 0.0
        for prev in draws:
            if prev["draw_no"] >= d["draw_no"]:
                break
            best = max(best, jaccard(d["set"], prev["set"]))
        max_jacs.append(best)
        details.append({"draw_no": d["draw_no"], "sum": d["sum"], "max_jaccard": round(best, 6)})

    avg_max = round(mean(max_jacs), 6) if max_jacs else 0.0
    # compare to mid-tier draws in same range
    mids = [d for d in draws if HIGH_LO <= d["draw_no"] <= HIGH_HI and d["sum_tier"] == "mid"]
    mid_max = []
    for d in mids[:80]:  # sample cap for speed — actually n mid ~100, do all
        best = 0.0
        for prev in draws:
            if prev["draw_no"] >= d["draw_no"]:
                break
            best = max(best, jaccard(d["set"], prev["set"]))
        mid_max.append(best)
    # do all mids properly
    mid_max = []
    for d in mids:
        best = 0.0
        for prev in draws:
            if prev["draw_no"] >= d["draw_no"]:
                break
            best = max(best, jaccard(d["set"], prev["set"]))
        mid_max.append(best)
    avg_mid = round(mean(mid_max), 6) if mid_max else 0.0

    # root: if high has clearly lower max jaccard → rare context
    if avg_max + 0.02 < avg_mid:
        root = "희귀문맥"
    else:
        root = "pool실패"

    return {
        "n_high_draws": len(highs),
        "avg_max_jaccard": avg_max,
        "avg_max_jaccard_mid_ref": avg_mid,
        "n_mid_ref": len(mids),
        "max_jaccard_hist": dict(Counter(round(x, 2) for x in max_jacs)),
        "sample": details[:10],
        "root_cause": root,
        "note": "max_jaccard = 해당 HIGH 회차 vs 그 이전 전체 최대 Jaccard",
    }


def lag_bonus(draws: list[dict], draws_by: dict[int, dict], anchor: set[int]) -> dict[str, Any]:
    # carry: numbers in both 1234 and 1235
    d1234 = draws_by[1234]["set"]
    d1235 = draws_by[1235]["set"]
    carry = sorted(d1234 & d1235)

    # consecutive pairs in 1235
    nums = sorted(d1235)
    consec = []
    for i in range(len(nums) - 1):
        if nums[i + 1] - nums[i] == 1:
            consec.append([nums[i], nums[i + 1]])

    # historical: when a number appears as carry (in D_t and D_{t-1}), rate it appears in D_{t+1}
    carry_next_hits = 0
    carry_next_trials = 0
    consec_next_hits = 0
    consec_next_trials = 0

    for i in range(1, len(draws) - 1):
        prev_s = draws[i - 1]["set"]
        cur_s = draws[i]["set"]
        nxt_s = draws[i + 1]["set"]
        carries = prev_s & cur_s
        for n in carries:
            carry_next_trials += 1
            if n in nxt_s:
                carry_next_hits += 1
        cur_sorted = sorted(cur_s)
        for a, b in zip(cur_sorted, cur_sorted[1:]):
            if b - a == 1:
                consec_next_trials += 2  # both ends
                consec_next_hits += int(a in nxt_s) + int(b in nxt_s)

    carry_rate = round(carry_next_hits / carry_next_trials, 6) if carry_next_trials else 0.0
    consec_rate = (
        round(consec_next_hits / consec_next_trials, 6) if consec_next_trials else 0.0
    )
    # random baseline ~ 6/45
    rand = 6.0 / 45.0
    viable = (carry_rate >= rand + 0.02) or (consec_rate >= rand + 0.02)

    return {
        "carry_numbers": carry,
        "consecutive_pairs": consec,
        "carry_reappear_rate": carry_rate,
        "consecutive_member_reappear_rate": consec_rate,
        "random_baseline": round(rand, 6),
        "n_carry_trials": carry_next_trials,
        "n_consec_trials": consec_next_trials,
        "viable": viable,
        "note": "다음회 재출현율 vs 6/45 · 발권 ge3 클레임 금지",
    }


def overall_verdict(bt: dict, lag: dict) -> str:
    if bt["verdict"] == "VIABLE":
        return "VIABLE"
    if bt["delta"] >= 0.005 or lag["viable"]:
        return "MARGINAL"
    return "NOISE"


def write_md(p: dict[str, Any]) -> str:
    lines = [
        "# K-NEIGHBOR-MATCH — kNN 유사 회차 패턴 진단 (2026-08-05)",
        "",
        f"- **판정:** `{p['verdict']}` · wire=`{p['wire']}`",
        f"- anchor {p['anchor_draw']}: `{p['anchor_numbers']}`",
        "",
        "## knn_scores @1235",
        "",
    ]
    for kk, block in p["knn_scores"].items():
        lines.append(f"### {kk} · top1_score={block['top1_score']}")
        lines.append(f"- top15: `{block['top15_numbers']}`")
        lines.append("")
    lines += [
        "## backtest_100",
        "",
        f"```json\n{json.dumps(p['backtest_100'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## high_sum_analysis",
        "",
        f"```json\n{json.dumps(p['high_sum_analysis'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## lag_bonus",
        "",
        f"```json\n{json.dumps(p['lag_bonus'], ensure_ascii=False, indent=2)}\n```",
        "",
        f"- wire_implication: {p['wire_implication']}",
        f"- tool: `tools/_k_neighbor_match.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    draws = load_draws()
    draws_by = {d["draw_no"]: d for d in draws}
    anchor_set = draws_by[ANCHOR]["set"]
    assert anchor_set == {6, 7, 11, 15, 39, 43}

    knn_scores: dict[str, Any] = {}
    knn_neighbors: dict[str, Any] = {}
    for k in (5, 10, 20):
        nbs = top_k_neighbors(anchor_set, draws, exclude_draw=ANCHOR, k=k)
        scores = next_scores(nbs, draws_by)
        pack = scores_to_top15(scores)
        knn_scores[f"k{k}"] = {
            "top15_numbers": pack["top15_numbers"],
            "top1_score": pack["top1_score"],
            "top15_detail": pack["top15_detail"],
        }
        knn_neighbors[f"k{k}"] = nbs

    bt = backtest_100(draws, draws_by)
    high = high_sum_analysis(draws, draws_by)
    lag = lag_bonus(draws, draws_by, anchor_set)
    verdict = overall_verdict(bt, lag)

    if bt["verdict"] == "VIABLE":
        wire_imp = (
            "neighbor kNN VIABLE · cold-free wire와 병행 검토 가능 · "
            "단 본 측정은 top15 적중이지 발권 티켓 ge3 아님 · 형 GO 후 live 경로 재검증"
        )
    elif verdict == "MARGINAL":
        wire_imp = (
            "neighbor 단독 wire 보류 · cold-free(Δ+0.03 COVER) 우선 · "
            "lag_bonus/neighbor는 보조 점수 후보"
        )
    else:
        wire_imp = (
            "neighbor NOISE · cold-free wire GO 여부를 형 결정으로 분리 검토 · "
            "kNN 통합 보류"
        )

    payload = {
        "id": "K-NEIGHBOR-MATCH",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "wire": False,
        "anchor_draw": ANCHOR,
        "anchor_numbers": sorted(anchor_set),
        "knn_scores": knn_scores,
        "knn_neighbors": knn_neighbors,
        "backtest_100": bt,
        "high_sum_analysis": high,
        "lag_bonus": lag,
        "wire_implication": wire_imp,
        "forbid": [
            "random.choices",
            "engine.py",
            "auto-tune",
            "wire",
            "DB INSERT/UPDATE",
            "_get_draws_before mutate",
            "ge3 향상 클레임",
        ],
        "pass": True,
        "tool": "tools/_k_neighbor_match.py",
        "prior": "docs/benchmarks/20260805_KEARLY_DIAG.json",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = write_md(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        DRIVE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"drive copy skip: {e}", file=sys.stderr)

    print(
        json.dumps(
            {
                "ok": True,
                "verdict": verdict,
                "k10_top15": knn_scores["k10"]["top15_numbers"],
                "bt": bt,
                "high": {
                    "n": high["n_high_draws"],
                    "avg_max_j": high["avg_max_jaccard"],
                    "mid_ref": high["avg_max_jaccard_mid_ref"],
                    "root": high["root_cause"],
                },
                "lag": {
                    "carry": lag["carry_numbers"],
                    "consec": lag["consecutive_pairs"],
                    "carry_rate": lag["carry_reappear_rate"],
                    "viable": lag["viable"],
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
