# -*- coding: utf-8 -*-
"""K-ANALOG-BT — archive-next walk-forward 백테스트 (READ-ONLY).

시나리오: N-1 당첨(base) → 1..N-2 유사 analog → analog+1 관측 집계 → N 예측.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260728_KANALOG_backtest.json"

METHODS = [
    ("M_freq", "단순 빈도(analog+1)"),
    ("M_weighted", "유사도 가중 빈도"),
    ("M_overlap3", "겹침3+ only"),
    ("M_anchor_pair", "앵커·쌍 lift (AI)"),
    ("M_positional", "자리별 archive (statlotto)"),
    ("M_greedy_pair", "탐욕 쌍 연쇄 (AI)"),
]

# 기대값: 6/45 * 6 ≈ 0.8
RANDOM_EXPECT = 6 * 6 / 45


def _load_draws_upto(max_no: int) -> dict[int, dict]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT * FROM lotto_draws WHERE draw_no <= ? ORDER BY draw_no",
            (max_no,),
        ).fetchall()
        return {int(dict(r)["draw_no"]): dict(r) for r in rows}
    finally:
        conn.close()


def _random_pred(seed: int) -> list[int]:
    rng = random.Random(seed)
    return sorted(rng.sample(range(1, 46), 6))


def run_backtest(start: int, end: int) -> dict:
    from app.testlotto.analog_service import (
        draw_nums,
        find_analogs,
        matched_count,
        predict_from_analogs,
    )
    from app.testlotto.data_service import _get_draws_before

    draw_by = _load_draws_upto(end)
    stats = {m[0]: {"matches": [], "tier3_plus": 0} for m in METHODS}
    stats["M_random"] = {"matches": [], "tier3_plus": 0}
    per_draw: list[dict] = []

    for n in range(start, end + 1):
        if n not in draw_by or (n - 1) not in draw_by:
            continue
        base_row = draw_by[n - 1]
        actual = draw_nums(draw_by[n])
        base_nums = draw_nums(base_row)
        past = _get_draws_before(n - 1)  # 1..N-2
        analogs = find_analogs(base_nums, past)

        top1 = analogs[0] if analogs else None
        row: dict = {
            "target": n,
            "base": n - 1,
            "base_nums": base_nums,
            "actual": actual,
            "analog_n": len(analogs),
            "top1_draw": top1["draw_no"] if top1 else None,
            "top1_overlap": int(top1["overlap"]) if top1 else 0,
            "methods": {},
        }
        for mid, _label in METHODS:
            pred = predict_from_analogs(
                base_nums, analogs, draw_by, mid, target_draw_no=n
            )
            mc = matched_count(pred, actual)
            stats[mid]["matches"].append(mc)
            if mc >= 3:
                stats[mid]["tier3_plus"] += 1
            row["methods"][mid] = {"pred": pred, "matched": mc}

        rp = _random_pred(n * 10007)
        rmc = matched_count(rp, actual)
        stats["M_random"]["matches"].append(rmc)
        if rmc >= 3:
            stats["M_random"]["tier3_plus"] += 1
        row["methods"]["M_random"] = {"pred": rp, "matched": rmc}
        per_draw.append(row)

    n_draws = len(per_draw)
    summary = {}
    for key, st in stats.items():
        ms = st["matches"]
        dist = Counter(ms)
        summary[key] = {
            "n": len(ms),
            "mean_match": round(mean(ms), 4) if ms else 0,
            "median_match": round(median(ms), 4) if ms else 0,
            "tier3_plus_rate": round(st["tier3_plus"] / n_draws, 4) if n_draws else 0,
            "max_match": max(ms) if ms else 0,
            "match_dist": {str(k): dist[k] for k in sorted(dist.keys())},
        }

    # 조건부: TOP1 analog 겹침≥3
    hi_overlap = [r for r in per_draw if r.get("top1_overlap", 0) >= 3]
    conditional = {}
    if hi_overlap:
        for mid, _ in METHODS:
            ms = [r["methods"][mid]["matched"] for r in hi_overlap]
            conditional[mid] = {
                "n": len(ms),
                "mean_match": round(mean(ms), 4),
            }
        conditional["M_random"] = {
            "n": len(hi_overlap),
            "mean_match": round(
                mean(r["methods"]["M_random"]["matched"] for r in hi_overlap), 4
            ),
        }

    # analog vs random 승률 (회차별 M_weighted > random)
    beat_random = sum(
        1
        for r in per_draw
        if r["methods"]["M_weighted"]["matched"] > r["methods"]["M_random"]["matched"]
    )
    tie_random = sum(
        1
        for r in per_draw
        if r["methods"]["M_weighted"]["matched"] == r["methods"]["M_random"]["matched"]
    )

    # highlight 1233→1234
    spot = next((r for r in per_draw if r["target"] == 1234), None)

    # 적중 상위 5건 (M_weighted)
    top_hits = sorted(
        per_draw,
        key=lambda r: (-r["methods"]["M_weighted"]["matched"], -r.get("top1_overlap", 0)),
    )[:5]

    best_mean = max(
        ((k, v["mean_match"]) for k, v in summary.items() if k != "M_random"),
        key=lambda x: x[1],
        default=("?", 0),
    )

    return {
        "task": "K-ANALOG-BT",
        "scenario": "N-1 base → analog in 1..N-2 → analog+1 vote → predict N",
        "range": {"start": start, "end": end, "n_draws": n_draws},
        "random_expect_mean": round(RANDOM_EXPECT, 4),
        "methods": {m[0]: m[1] for m in METHODS},
        "methods_extra": {"M_random": "균등 무작위 baseline"},
        "summary": summary,
        "best_by_mean": {"method": best_mean[0], "mean_match": best_mean[1]},
        "vs_random": {
            k: round(summary[k]["mean_match"] - summary["M_random"]["mean_match"], 4)
            for k in summary
            if k != "M_random"
        },
        "spotlight_1234": spot,
        "pattern_analysis": {
            "top1_overlap_ge3": conditional,
            "M_weighted_beat_random_rate": round(beat_random / n_draws, 4) if n_draws else 0,
            "M_weighted_tie_random_rate": round(tie_random / n_draws, 4) if n_draws else 0,
            "top5_hits_M_weighted": top_hits,
        },
        "disclaimer": "독립 시행 가정 하 적중↑ 기대 금지 · walk-forward 컨닝 없음(analog+1 < N)",
    }


def main() -> int:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1180
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 1234
    payload = run_backtest(start, end)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    s = payload["summary"]
    print(
        json.dumps(
            {
                "range": payload["range"],
                "random_expect": payload["random_expect_mean"],
                "best": payload["best_by_mean"],
                "1234": payload["spotlight_1234"],
                "means": {k: s[k]["mean_match"] for k in sorted(s.keys())},
                "out": str(OUT),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
