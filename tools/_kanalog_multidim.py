# -*- coding: utf-8 -*-
"""K-ANALOG-MULTIDIM — 적중 0~6 전분포 + 다차원 조건부 분석 (READ-ONLY).

1차원(3개+ only) 금지 — 겹침 2/3/4/5/6 · pattern_sim · chain · base→actual 전부 slice.
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260728_KANALOG_multidim.json"

METHODS = [
    ("M_freq", "단순 빈도"),
    ("M_weighted", "유사도 가중"),
    ("M_overlap2", "겹침2+"),
    ("M_overlap3", "겹침3+"),
    ("M_overlap4", "겹침4+"),
    ("M_ov_bucket", "겹침 tier 2D"),
    ("M_b_route", "B-route pattern≥0.85"),
    ("M_chain8", "chain W=8 3D"),
    ("M_exclude_base", "base 제외 신규"),
    ("M_positional", "자리별 archive"),
    ("M_ensemble", "다수결 ensemble"),
    ("M_greedy_pair", "탐욕 쌍"),
]

# 이론: 6개 고르면 k개 일치 P(k) = C(6,k)*C(39,6-k)/C(45,6)
def _binom(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    c = 1
    for i in range(k):
        c = c * (n - i) // (i + 1)
    return c


def theoretical_match_dist() -> dict[str, float]:
    denom = _binom(45, 6)
    return {
        str(k): round(_binom(6, k) * _binom(39, 6 - k) / denom, 4)
        for k in range(7)
    }


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
    return sorted(random.Random(seed).sample(range(1, 46), 6))


def _psim_bin(v: float) -> str:
    if v < 0.85:
        return "lt0.85"
    if v < 0.90:
        return "0.85-0.90"
    if v < 0.95:
        return "0.90-0.95"
    return "ge0.95"


def _summarize_matches(ms: list[int]) -> dict:
    n = len(ms)
    dist = Counter(ms)
    return {
        "n": n,
        "mean": round(mean(ms), 4) if n else 0,
        "match_dist": {str(k): dist.get(k, 0) for k in range(7)},
        "match_rate": {
            str(k): round(dist.get(k, 0) / n, 4) if n else 0 for k in range(7)
        },
        "tier0": dist.get(0, 0),
        "tier1": dist.get(1, 0),
        "tier2": dist.get(2, 0),
        "tier3_plus": sum(dist.get(k, 0) for k in range(3, 7)),
    }


def run_multidim(start: int, end: int) -> dict:
    from app.testlotto.analog_service import (
        _chain_pattern_sim,
        draw_nums,
        find_analogs,
        matched_count,
        predict_from_analogs,
    )
    from app.testlotto.data_service import _get_draws_before

    draw_by = _load_draws_upto(end)
    all_methods = [m[0] for m in METHODS] + ["M_random"]
    stats = {m: [] for m in all_methods}

    # 다차원 버킷 — method별 match list
    def _mk() -> dict[str, list[int]]:
        return defaultdict(list)

    by_top1_ov: dict[str, dict[str, list[int]]] = defaultdict(_mk)
    by_psim: dict[str, dict[str, list[int]]] = defaultdict(_mk)
    by_max_ov: dict[str, dict[str, list[int]]] = defaultdict(_mk)
    by_n_ov3: dict[str, dict[str, list[int]]] = defaultdict(_mk)
    by_n_ov4: dict[str, dict[str, list[int]]] = defaultdict(_mk)
    by_chain8: dict[str, dict[str, list[int]]] = defaultdict(_mk)
    by_base_repeat: dict[str, dict[str, list[int]]] = defaultdict(_mk)
    cross_ov_match: dict[str, Counter] = defaultdict(Counter)
    cross_3d: dict[str, dict[str, list[int]]] = defaultdict(_mk)

    track_methods = ("M_weighted", "M_random", "M_overlap4", "M_chain8", "M_ensemble")

    per_draw_meta: list[dict] = []

    for n in range(start, end + 1):
        if n not in draw_by or (n - 1) not in draw_by:
            continue
        base_nums = draw_nums(draw_by[n - 1])
        actual = draw_nums(draw_by[n])
        past = _get_draws_before(n - 1)
        analogs = find_analogs(base_nums, past)
        top1 = analogs[0] if analogs else None
        top1_ov = int(top1["overlap"]) if top1 else 0
        top1_psim = float(top1["pattern_sim"]) if top1 else 0.0
        max_ov = max((int(a["overlap"]) for a in analogs), default=0)
        n_ov3 = sum(1 for a in analogs if int(a["overlap"]) >= 3)
        n_ov4 = sum(1 for a in analogs if int(a["overlap"]) >= 4)
        chain8 = (
            _chain_pattern_sim(n - 1, int(top1["draw_no"]), draw_by, window=8)
            if top1
            else 0.0
        )
        base_repeat = len(set(base_nums) & set(actual))  # N-1→N 유지 개수

        row_matches: dict[str, int] = {}
        for mid, _ in METHODS:
            pred = predict_from_analogs(
                base_nums, analogs, draw_by, mid, target_draw_no=n
            )
            mc = matched_count(pred, actual)
            stats[mid].append(mc)
            row_matches[mid] = mc

        rmc = matched_count(_random_pred(n * 10007), actual)
        stats["M_random"].append(rmc)
        row_matches["M_random"] = rmc

        def _push(bucket: dict, key: str) -> None:
            for m in track_methods:
                if m in row_matches:
                    bucket[key][m].append(row_matches[m])

        _push(by_top1_ov, str(top1_ov))
        _push(by_psim, _psim_bin(top1_psim))
        _push(by_max_ov, str(max_ov))
        _push(by_n_ov3, str(n_ov3))
        _push(by_n_ov4, str(n_ov4))
        ch_bin = "ch_lo" if chain8 < 0.85 else ("ch_mid" if chain8 < 0.95 else "ch_hi")
        _push(by_chain8, ch_bin)
        _push(by_base_repeat, str(base_repeat))

        cross_ov_match[str(top1_ov)][row_matches["M_weighted"]] += 1
        key3 = f"ov{top1_ov}|{_psim_bin(top1_psim)}|{ch_bin}"
        _push(cross_3d, key3)

        per_draw_meta.append(
            {
                "target": n,
                "top1_ov": top1_ov,
                "top1_psim": round(top1_psim, 4),
                "max_ov": max_ov,
                "n_ov3": n_ov3,
                "n_ov4": n_ov4,
                "chain8": round(chain8, 4),
                "base_repeat": base_repeat,
                "M_weighted": row_matches["M_weighted"],
                "M_random": row_matches["M_random"],
            }
        )

    n_draws = len(per_draw_meta)

    # 전체 summary
    summary = {m: _summarize_matches(stats[m]) for m in all_methods}

    def _slice_summary(buckets: dict) -> dict:
        out = {}
        for key in sorted(buckets.keys(), key=lambda x: (len(x), x)):
            sub = {}
            for method in ("M_weighted", "M_random", "M_overlap4", "M_chain8"):
                ms = buckets[key].get(method, [])
                if ms:
                    sub[method] = _summarize_matches(ms)
            out[key] = sub
        return out

    # 3D cells: n>=10 & mean beats random
    best_cells = []
    for key, buckets in cross_3d.items():
        for method in track_methods:
            if method == "M_random":
                continue
            ms = buckets.get(method, [])
            rm = buckets.get("M_random", [])
            if len(ms) < 10 or not rm:
                continue
            dm = mean(ms) - mean(rm)
            if dm > 0.03:
                best_cells.append(
                    {
                        "cell": key,
                        "method": method,
                        "n": len(ms),
                        "mean": round(mean(ms), 4),
                        "random_mean": round(mean(rm), 4),
                        "delta": round(dm, 4),
                    }
                )
    best_cells.sort(key=lambda x: -x["delta"])

    # cross_ov_match → rates
    cross_rates = {}
    for ov, cnt in sorted(cross_ov_match.items(), key=lambda x: int(x[0])):
        total = sum(cnt.values())
        cross_rates[ov] = {
            "n": total,
            "dist": {str(k): cnt.get(k, 0) for k in range(7)},
            "rate": {str(k): round(cnt.get(k, 0) / total, 4) if total else 0 for k in range(7)},
            "mean_M_weighted": round(
                mean(by_top1_ov[ov]["M_weighted"]) if by_top1_ov[ov]["M_weighted"] else 0,
                4,
            ),
            "mean_M_random": round(
                mean(by_top1_ov[ov]["M_random"]) if by_top1_ov[ov]["M_random"] else 0,
                4,
            ),
        }

    theory = theoretical_match_dist()

    # 이론 vs 관측 (M_random)
    random_obs = summary["M_random"]["match_rate"]
    chi_note = {
        str(k): {
            "theory": theory[str(k)],
            "random_obs": random_obs[str(k)],
            "M_weighted_obs": summary["M_weighted"]["match_rate"][str(k)],
        }
        for k in range(7)
    }

    best_mean = max(
        ((k, v["mean"]) for k, v in summary.items() if k != "M_random"),
        key=lambda x: x[1],
    )

    return {
        "task": "K-ANALOG-MULTIDIM",
        "scenario": "0~6 전분포 · top1_overlap×pattern×chain 다차원",
        "range": {"start": start, "end": end, "n_draws": n_draws},
        "theoretical_random_dist": theory,
        "theory_vs_observed": chi_note,
        "methods": {m[0]: m[1] for m in METHODS},
        "summary": summary,
        "best_by_mean": {"method": best_mean[0], "mean": best_mean[1]},
        "dim_1d": {
            "by_top1_overlap": _slice_summary(by_top1_ov),
            "by_top1_pattern_sim": _slice_summary(by_psim),
            "by_max_overlap_top15": _slice_summary(by_max_ov),
            "by_count_overlap3_in_top15": _slice_summary(by_n_ov3),
            "by_count_overlap4_in_top15": _slice_summary(by_n_ov4),
            "by_chain8_sim_bin": _slice_summary(by_chain8),
            "by_base_to_actual_repeat": _slice_summary(by_base_repeat),
        },
        "dim_2d": {
            "cross_top1overlap_x_matchcount": cross_rates,
            "cross_overlap_x_pattern_x_chain_3d": _slice_summary(cross_3d),
        },
        "dim_3d_best_cells": best_cells[:15],
        "spotlight": {
            "1234": next((r for r in per_draw_meta if r["target"] == 1234), None),
            "match0_examples": [r for r in per_draw_meta if r["M_weighted"] == 0][:5],
            "match4_examples": [r for r in per_draw_meta if r["M_weighted"] >= 4][:5],
        },
        "ai_ideas_tested": [
            "M_ov_bucket — 겹침 tier 2D 가중",
            "M_b_route — B-only pattern rescue (2차 회의)",
            "M_chain8 — analog×chain W=8 3D",
            "M_exclude_base — carry-out 신규번호",
            "M_ensemble — freq+weighted+ov_bucket 다수결",
            "M_overlap2/3/4 — 겹침 1D sweep (2~4)",
        ],
        "disclaimer": "과도한 slice는 n 작음 · 우위 주장 금지 · READ-ONLY",
    }


def main() -> int:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 1234
    payload = run_multidim(start, end)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    s = payload["summary"]
    print(json.dumps({
        "n": payload["range"]["n_draws"],
        "theory": payload["theoretical_random_dist"],
        "M_weighted_dist": s["M_weighted"]["match_rate"],
        "M_random_dist": s["M_random"]["match_rate"],
        "by_top1_ov": {
            k: v.get("M_weighted", {}).get("mean", "?")
            for k, v in payload["dim_1d"]["by_top1_overlap"].items()
        },
        "best_3d_cells": payload["dim_3d_best_cells"][:5],
        "out": str(OUT),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
