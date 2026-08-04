# -*- coding: utf-8 -*-
"""K-EVOLVE-FEAT-LAM-REVAL — 풀히스토리(53~1234) feature-λ 재검증.

expand 이후 review λ=0.3 wire 유지 여부 판정.
증분 버킷으로 O(n) · PartB와 동일 점수식.

Usage:
  python tools/_k_evolve_feat_lam_revalidate.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KEVOLVE_FEAT_LAM_REVAL.json"
OUT_MD = ROOT / "reports" / "20260804_KEVOLVE_FEAT_LAM_REVAL.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BRAINS = ("stat", "markov", "review")
LAMBDAS = (0.0, 0.1, 0.2, 0.3, 0.5)
NULL5 = 0.1137
PIN = 0.1447
MARKOV_SCALE = 0.5
WIRED_LAM = 0.3
LO, HI = 53, 1234
TAIL_LO = 1035
REF_TAIL_REVIEW_03 = 0.145  # SIGNAL n200


def _thirds(draw_nos: list[int]) -> dict[str, tuple[int, int]]:
    n = len(draw_nos)
    a = n // 3
    b = 2 * n // 3
    return {
        "early": (draw_nos[0], draw_nos[a - 1]),
        "mid": (draw_nos[a], draw_nos[b - 1]),
        "late": (draw_nos[b], draw_nos[-1]),
    }


def _ge3(bests: list[int]) -> dict[str, Any]:
    n = len(bests)
    g = sum(1 for x in bests if x >= 3)
    rate = round(g / n, 4) if n else 0.0
    return {
        "n": n,
        "ge3_count": g,
        "ge3_rate": rate,
        "mean_best": round(mean(bests), 4) if bests else 0.0,
        "delta_vs_null": round(rate - NULL5, 4),
        "delta_vs_pin": round(rate - PIN, 4),
    }


def sweep_brain(logs: dict[int, dict], tag: str) -> dict[str, Any]:
    from app.testlotto.feature_lambda import feat_key, select_top5

    draw_nos = sorted(d for d in logs if tag in logs[d])
    # incremental buckets: list of hits per feat key
    bucket_hits: dict[tuple, list[int]] = defaultdict(list)
    all_hits: list[int] = []

    # per-lambda bests over full + windows
    per_lam: dict[float, list[tuple[int, int]]] = {lam: [] for lam in LAMBDAS}
    # (draw_no, best_hits)
    baseline: list[tuple[int, int]] = []

    for dno in draw_nos:
        row = logs[dno][tag]
        baseline.append((dno, int(row["best_hits"])))

        # stats from PAST only (already accumulated)
        stats = {
            k: {"n": len(xs), "mean_hits": mean(xs)} for k, xs in bucket_hits.items()
        }
        gmean = mean(all_hits) if all_hits else 0.8
        cands = row["pool"] + row["repack"]

        for lam in LAMBDAS:
            eff = lam * (MARKOV_SCALE if tag == "markov" else 1.0)
            picked = select_top5(cands, stats, eff, gmean)
            if not picked:
                continue
            bh = max(int(s.get("hits") or 0) for s in picked)
            per_lam[lam].append((dno, bh))

        # update buckets with CURRENT (for next draws)
        for s in cands:
            hits = int(s.get("hits", -1))
            if hits < 0:
                continue
            all_hits.append(hits)
            bucket_hits[feat_key(s.get("features") or {})].append(hits)

    by_lambda = {}
    for lam in LAMBDAS:
        pairs = per_lam[lam]
        bests = [h for _, h in pairs]
        row = _ge3(bests)
        row["lambda_nominal"] = lam
        row["lambda_effective"] = round(
            lam * (MARKOV_SCALE if tag == "markov" else 1.0), 4
        )
        by_lambda[str(lam)] = row

    base_bests = [h for _, h in baseline]
    baseline_row = _ge3(base_bests)

    ranked = sorted(
        ((float(k), v) for k, v in by_lambda.items()),
        key=lambda kv: (-kv[1]["ge3_rate"], kv[0]),
    )
    best_lam, best_v = ranked[0]

    # window cuts for wired λ and baseline
    thirds = _thirds(draw_nos)
    windows = {"full": (draw_nos[0], draw_nos[-1]), "tail200": (TAIL_LO, HI), **thirds}

    def slice_ge3(pairs: list[tuple[int, int]], lo: int, hi: int) -> dict:
        xs = [h for d, h in pairs if lo <= d <= hi]
        return _ge3(xs)

    wired_pairs = per_lam[WIRED_LAM]
    window_cmp = {}
    for wname, (wlo, whi) in windows.items():
        window_cmp[wname] = {
            "range": [wlo, whi],
            "baseline": slice_ge3(baseline, wlo, whi),
            f"lambda_{WIRED_LAM}": slice_ge3(wired_pairs, wlo, whi),
        }
        b = window_cmp[wname]["baseline"]["ge3_rate"]
        l = window_cmp[wname][f"lambda_{WIRED_LAM}"]["ge3_rate"]
        window_cmp[wname]["delta"] = round(l - b, 4)

    return {
        "n_draws": len(draw_nos),
        "draw_range": [draw_nos[0], draw_nos[-1]] if draw_nos else [],
        "baseline_repack": baseline_row,
        "by_lambda": by_lambda,
        "best_lambda": best_lam,
        "best_ge3": best_v["ge3_rate"],
        "delta_vs_baseline": round(best_v["ge3_rate"] - baseline_row["ge3_rate"], 4),
        "wired_lambda": WIRED_LAM,
        "wired_ge3": by_lambda[str(WIRED_LAM)]["ge3_rate"],
        "wired_delta_vs_baseline": round(
            by_lambda[str(WIRED_LAM)]["ge3_rate"] - baseline_row["ge3_rate"], 4
        ),
        "windows": window_cmp,
    }


def main() -> int:
    from app.testlotto.feature_lambda import FEATURE_LAMBDA_BY_BRAIN
    from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE
    from tools._k_evolve_signal_survey import _load_all_logs

    print(f"load evolve_log {LO}~{HI}...", flush=True)
    logs = _load_all_logs(LO, HI)
    print(f"  n_draws={len(logs)}", flush=True)

    survey: dict[str, Any] = {}
    for tag in BRAINS:
        print(f"sweep {tag}...", flush=True)
        survey[tag] = sweep_brain(logs, tag)
        r = survey[tag]
        print(
            f"  base={r['baseline_repack']['ge3_rate']} "
            f"bestλ={r['best_lambda']} ge3={r['best_ge3']} "
            f"wired0.3={r['wired_ge3']} Δ={r['wired_delta_vs_baseline']:+}",
            flush=True,
        )

    rev = survey["review"]
    tail = rev["windows"]["tail200"]
    full_keep = rev["wired_delta_vs_baseline"] >= 0.0
    tail_ok = abs(tail[f"lambda_{WIRED_LAM}"]["ge3_rate"] - REF_TAIL_REVIEW_03) < 1e-9 or (
        tail[f"lambda_{WIRED_LAM}"]["ge3_rate"] >= REF_TAIL_REVIEW_03 - 0.01
    )
    # keep wire if full Δ>=0 OR (full not worse than -0.005 and bestλ still 0.3)
    keep_wire = (
        FEATURE_LAMBDA_WIRE
        and FEATURE_LAMBDA_BY_BRAIN.get("review") == WIRED_LAM
        and (
            full_keep
            or (
                rev["wired_delta_vs_baseline"] >= -0.005
                and rev["best_lambda"] == WIRED_LAM
            )
        )
    )
    # AUTO prep gate note
    auto_ready = keep_wire and rev["windows"]["full"][f"lambda_{WIRED_LAM}"]["n"] >= 1000

    if keep_wire and full_keep:
        verdict = "KEEP"
        next_step = "Phase3 AUTO 설계/준비 · 형 GO"
    elif keep_wire:
        verdict = "KEEP-WEAK"
        next_step = "λ0.3 유지(약) · AUTO 전 QUICK 재확인 · 형 GO"
    else:
        verdict = "RECONSIDER"
        next_step = "review λ HOLD 검토 · 형 GO"

    payload = {
        "id": "K-EVOLVE-FEAT-LAM-REVAL",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "draw_range": [LO, HI],
        "n_draws": len(logs),
        "live": {
            "FEATURE_LAMBDA_WIRE": FEATURE_LAMBDA_WIRE,
            "FEATURE_LAMBDA_BY_BRAIN": dict(FEATURE_LAMBDA_BY_BRAIN),
        },
        "lambda_survey": survey,
        "null_ge3": NULL5,
        "wire_pin_ge3": PIN,
        "ref_signal_tail_review_l03": REF_TAIL_REVIEW_03,
        "verdict": {
            "label": verdict,
            "keep_review_lambda_03": keep_wire,
            "full_delta_vs_baseline": rev["wired_delta_vs_baseline"],
            "full_wired_ge3": rev["wired_ge3"],
            "full_baseline_ge3": rev["baseline_repack"]["ge3_rate"],
            "tail200_wired_ge3": tail[f"lambda_{WIRED_LAM}"]["ge3_rate"],
            "tail200_delta": tail["delta"],
            "best_lambda_full": rev["best_lambda"],
            "stat_markov": "HOLD 유지 권고"
            if (
                survey["stat"]["wired_delta_vs_baseline"] <= 0
                and survey["markov"]["wired_delta_vs_baseline"] <= 0
            )
            else "재검토",
            "auto_prep_gate": auto_ready,
            "next": next_step,
        },
        "pass": keep_wire,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-EVOLVE-FEAT-LAM-REVAL — 풀히스토리 λ 재검증",
        "",
        f"📅 {payload['ts'][:10]} · **{verdict}** · keep_wire={keep_wire}",
        "",
        f"range **{LO}~{HI}** n=**{len(logs)}** · live review λ=**{WIRED_LAM}**",
        "",
        "## review (wire 대상)",
        "",
        f"| 구간 | baseline | λ={WIRED_LAM} | Δ |",
        "|------|----------:|----------:|---:|",
    ]
    for wname, w in rev["windows"].items():
        lines.append(
            f"| {wname} {w['range']} | {w['baseline']['ge3_rate']:.4f} | "
            f"{w[f'lambda_{WIRED_LAM}']['ge3_rate']:.4f} | {w['delta']:+.4f} |"
        )
    lines.extend(
        [
            "",
            f"- full best λ=**{rev['best_lambda']}** ge3=**{rev['best_ge3']}**",
            f"- SIGNAL tail ref λ0.3=**{REF_TAIL_REVIEW_03}** · 실측 tail="
            f"**{tail[f'lambda_{WIRED_LAM}']['ge3_rate']}**",
            "",
            "## 전뇌 λ 요약",
            "",
            "| 뇌 | baseline | bestλ | best ge3 | λ0.3 ge3 | Δ0.3 |",
            "|----|----------:|------:|---------:|---------:|-----:|",
        ]
    )
    for tag in BRAINS:
        r = survey[tag]
        lines.append(
            f"| {tag} | {r['baseline_repack']['ge3_rate']:.4f} | {r['best_lambda']} | "
            f"{r['best_ge3']:.4f} | {r['wired_ge3']:.4f} | {r['wired_delta_vs_baseline']:+.4f} |"
        )
    lines.extend(
        [
            "",
            "## 판정",
            "",
            f"- **{verdict}** · review λ0.3 keep=**{keep_wire}**",
            f"- stat/markov: {payload['verdict']['stat_markov']}",
            f"- AUTO prep gate (로그충분+keep): **{auto_ready}**",
            f"- 다음: {next_step}",
            "",
            "> Phase3 AUTO는 다중AI안상 **맨 마지막** · 지금은 게이트 재검증.",
            "",
            f"근거: `{OUT_JSON.name}`",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps(payload["verdict"], ensure_ascii=False, indent=2))
    return 0 if keep_wire else 1


if __name__ == "__main__":
    raise SystemExit(main())
