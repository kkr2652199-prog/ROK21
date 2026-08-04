# -*- coding: utf-8 -*-
"""K-EVOLVE-SIGNAL — best학습 차단 검증 + evolve_log 구조신호 λ survey.

- Part A: evolve_log에서 best vs mean 격차 (K-N 근거)
- Part B: as_of 절단 feature-bucket hit-rate로 후보 재선정 λ sweep
  (현재 회차 hits로 점수 만들지 않음 · 컨닝 없음)
- coordinator FEEDBACK_MATCH_MODE=mean 은 별도 wire (이 스크립트와 독립)

Usage:
  python tools/_k_evolve_signal_survey.py
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KEVOLVE_SIGNAL_survey.json"
OUT_MD = ROOT / "reports" / "20260804_KEVOLVE_SIGNAL_SURVEY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BRAINS = ("stat", "markov", "review")
LAMBDAS = (0.0, 0.1, 0.2, 0.3, 0.5)
NULL5 = 0.1137
PIN = 0.1447
# markov는 λ 절반 권고 → 별도 sweep에 half 표기
MARKOV_LAMBDA_SCALE = 0.5


def _feat_key(features: dict) -> tuple:
    if not features:
        return ("empty",)
    return (
        int(features.get("odd", -1)),
        int(features.get("zone_low", -1)),
        int(features.get("zone_mid", -1)),
        int(features.get("zone_high", -1)),
        int(features.get("max_run", -1)),
        int(round(float(features.get("sum", 0)) / 20.0)),  # sum bucket
    )


def _load_all_logs(lo: int, hi: int) -> dict[int, dict[str, dict]]:
    from app.testlotto.evolve_log import ensure_evolve_log_table
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    ensure_evolve_log_table()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT draw_no, brain_tag, best_hits, mean_hits,
               pool_json, repack_json, repack_hits_json, actual_nums_json
        FROM testlotto_evolve_log
        WHERE draw_no BETWEEN ? AND ?
        ORDER BY draw_no, brain_tag
        """,
        (lo, hi),
    ).fetchall()
    conn.close()
    out: dict[int, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        d = dict(r)
        dno = int(d["draw_no"])
        tag = str(d["brain_tag"])
        pool = json.loads(d["pool_json"] or "[]")
        repack = json.loads(d["repack_json"] or "[]")
        rh = {int(x["set_no"]): x for x in json.loads(d["repack_hits_json"] or "[]")}
        # attach features/hits onto repack
        for s in repack:
            sn = int(s.get("set_no") or 0)
            if sn in rh:
                s["hits"] = int(rh[sn].get("hits") or 0)
                s["features"] = rh[sn].get("features") or {}
            else:
                s["hits"] = -1
                s["features"] = {}
        # pool hits not in repack_hits — recompute vs actual for eval only
        actual = set(json.loads(d["actual_nums_json"] or "[]"))
        for s in pool:
            nums = [int(x) for x in s.get("nums") or []]
            s["hits"] = len(set(nums) & actual)
            from app.testlotto.evolve_log import set_features

            s["features"] = set_features(nums) if len(nums) == 6 else {}
        out[dno][tag] = {
            "best_hits": int(d["best_hits"]),
            "mean_hits": float(d["mean_hits"]),
            "pool": pool,
            "repack": repack,
            "actual": actual,
        }
    return dict(out)


def part_a_kn(logs: dict[int, dict[str, dict]]) -> dict[str, Any]:
    """best vs mean 격차 — K-N 근거."""
    by: dict[str, Any] = {}
    for tag in BRAINS:
        deltas = []
        for dno, brains in logs.items():
            if tag not in brains:
                continue
            b = brains[tag]
            deltas.append(b["best_hits"] - b["mean_hits"])
        by[tag] = {
            "n": len(deltas),
            "avg_best_minus_mean": round(mean(deltas), 4) if deltas else 0.0,
            "pct_best_gt_mean": round(
                sum(1 for x in deltas if x > 0) / len(deltas), 4
            )
            if deltas
            else 0.0,
            "note": "best>mean 비율 높을수록 best학습이 극단값 과신(K-N)",
        }
    return by


def _build_bucket_stats(
    logs: dict[int, dict[str, dict]], tag: str, before_draw: int
) -> dict[tuple, dict[str, float]]:
    """draw < before_draw 인 과거 세트의 feature-bucket별 평균 hits."""
    buckets: dict[tuple, list[int]] = defaultdict(list)
    for dno, brains in logs.items():
        if dno >= before_draw:
            continue
        row = brains.get(tag)
        if not row:
            continue
        for s in row["pool"] + row["repack"]:
            hits = int(s.get("hits", -1))
            if hits < 0:
                continue
            buckets[_feat_key(s.get("features") or {})].append(hits)
    out = {}
    for k, xs in buckets.items():
        out[k] = {"n": len(xs), "mean_hits": mean(xs)}
    return out


def _select_top5(
    candidates: list[dict],
    bucket_stats: dict[tuple, dict[str, float]],
    lam: float,
    global_mean: float,
) -> list[dict]:
    scored = []
    for s in candidates:
        nums = tuple(sorted(int(x) for x in s.get("nums") or []))
        if len(nums) != 6:
            continue
        fk = _feat_key(s.get("features") or {})
        hist = bucket_stats.get(fk, {}).get("mean_hits", global_mean)
        # λ=0 → 균등(원본 순서 유지용 작은 노이즈 대신 set_no)
        base = 1.0 / (1.0 + int(s.get("set_no") or 1))
        score = (1.0 - lam) * base + lam * float(hist)
        scored.append((score, nums, s))
    scored.sort(key=lambda x: (-x[0], x[1]))
    out = []
    seen = set()
    for sc, nums, s in scored:
        if nums in seen:
            continue
        seen.add(nums)
        out.append(s)
        if len(out) >= 5:
            break
    return out


def part_b_lambda(logs: dict[int, dict[str, dict]]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    draw_nos = sorted(logs.keys())
    for tag in BRAINS:
        lam_rows = {}
        for lam in LAMBDAS:
            eff = lam * (MARKOV_LAMBDA_SCALE if tag == "markov" else 1.0)
            bests = []
            for dno in draw_nos:
                row = logs[dno].get(tag)
                if not row:
                    continue
                buckets = _build_bucket_stats(logs, tag, dno)
                all_hits = []
                for d2, br in logs.items():
                    if d2 >= dno or tag not in br:
                        continue
                    for s in br[tag]["pool"] + br[tag]["repack"]:
                        if int(s.get("hits", -1)) >= 0:
                            all_hits.append(int(s["hits"]))
                gmean = mean(all_hits) if all_hits else 0.8
                cands = row["pool"] + row["repack"]
                picked = _select_top5(cands, buckets, eff, gmean)
                if not picked:
                    continue
                bests.append(max(int(s.get("hits") or 0) for s in picked))
            n = len(bests)
            ge3 = sum(1 for x in bests if x >= 3)
            rate = round(ge3 / n, 4) if n else 0.0
            lam_rows[str(lam)] = {
                "lambda_nominal": lam,
                "lambda_effective": round(eff, 4),
                "n": n,
                "ge3_count": ge3,
                "ge3_rate": rate,
                "mean_best": round(mean(bests), 4) if bests else 0.0,
                "delta_vs_null": round(rate - NULL5, 4),
                "delta_vs_pin": round(rate - PIN, 4),
            }
        # baseline = logged repack best (λ 무관 현행)
        base_bests = [logs[d][tag]["best_hits"] for d in draw_nos if tag in logs[d]]
        n0 = len(base_bests)
        g0 = sum(1 for x in base_bests if x >= 3)
        baseline = {
            "ge3_rate": round(g0 / n0, 4) if n0 else 0.0,
            "ge3_count": g0,
            "n": n0,
            "mean_best": round(mean(base_bests), 4) if base_bests else 0.0,
        }
        # best λ among deployable
        ranked = sorted(
            ((float(k), v) for k, v in lam_rows.items()),
            key=lambda kv: (-kv[1]["ge3_rate"], kv[0]),
        )
        best_lam = ranked[0] if ranked else (None, None)
        results[tag] = {
            "baseline_repack": baseline,
            "by_lambda": lam_rows,
            "best_lambda": best_lam[0],
            "best_ge3": best_lam[1]["ge3_rate"] if best_lam[1] else None,
            "delta_vs_baseline": (
                round(best_lam[1]["ge3_rate"] - baseline["ge3_rate"], 4)
                if best_lam[1]
                else None
            ),
        }
    return results


def main() -> None:
    from app.testlotto.brains import coordinator as coord

    lo, hi = 1035, 1234
    print("K-EVOLVE-SIGNAL load evolve_log...", flush=True)
    logs = _load_all_logs(lo, hi)
    kn = part_a_kn(logs)
    print("Part A K-N done", flush=True)
    print("Part B λ sweep...", flush=True)
    lam = part_b_lambda(logs)

    # wire status
    mode = getattr(coord, "FEEDBACK_MATCH_MODE", "unset")

    # verdict
    any_uplift = any(
        (lam[t].get("delta_vs_baseline") or 0) > 0 for t in ("stat", "review")
    )
    payload = {
        "id": "K-EVOLVE-SIGNAL",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "draw_range": [lo, hi],
        "n_draws": len(logs),
        "feedback_match_mode_live": mode,
        "k_n_block": {
            "wired": mode == "mean",
            "description": "coordinator._auto_feedback FEEDBACK_MATCH_MODE=mean",
            "best_vs_mean": kn,
        },
        "lambda_survey": lam,
        "null_ge3": NULL5,
        "wire_pin_ge3": PIN,
        "markov_lambda_scale": MARKOV_LAMBDA_SCALE,
        "verdict": {
            "kn_mean_wired": mode == "mean",
            "feature_lambda_beats_baseline_stat_or_review": any_uplift,
            "recommend_lambda_wire": False,  # fill below
            "next": "",
        },
    }
    # λ wire: baseline 대비 +≥0.01 이고, 동일 후보풀에서 λ=0보다도 나을 때만
    clear_tags = []
    for t in ("stat", "review"):
        d_base = lam[t].get("delta_vs_baseline") or 0
        best_l = lam[t].get("best_lambda")
        g_best = lam[t].get("best_ge3") or 0
        g_l0 = (lam[t].get("by_lambda") or {}).get("0.0", {}).get("ge3_rate") or 0
        if d_base >= 0.01 and best_l not in (None, 0.0) and g_best >= g_l0 + 0.005:
            clear_tags.append(t)
    clear = bool(clear_tags)
    payload["verdict"]["feature_lambda_beats_baseline_stat_or_review"] = any(
        (lam[t].get("delta_vs_baseline") or 0) > 0 for t in ("stat", "review")
    )
    payload["verdict"]["recommend_lambda_wire"] = clear
    payload["verdict"]["lambda_wire_brains"] = clear_tags
    payload["verdict"]["next"] = (
        f"feature λ wire GO-WAIT ({','.join(clear_tags)}) · mean 유지"
        if clear
        else "λ HOLD · mean-feedback(K-N차단) 유지 · Phase2 survey DONE"
    )

    lines = [
        "# K-EVOLVE-SIGNAL — best차단 + 구조신호 λ survey",
        "",
        f"`{payload['ts']}` · {lo}~{hi} · n={len(logs)}",
        "",
        "## 0. 한 줄",
        "",
        f"K-N 차단 wire: FEEDBACK_MATCH_MODE=**{mode}** · "
        f"feature λ가 baseline 상회(stat/review +≥0.01): **{clear}** · "
        f"다음: {payload['verdict']['next']}",
        "",
        "## 1. Part A — best vs mean (K-N)",
        "",
        "| 뇌 | n | avg(best−mean) | best>mean 비율 |",
        "|----|---|---------------:|---------------:|",
    ]
    for tag in BRAINS:
        k = kn[tag]
        lines.append(
            f"| {tag} | {k['n']} | {k['avg_best_minus_mean']:+.4f} | {k['pct_best_gt_mean']:.1%} |"
        )
    lines.extend(
        [
            "",
            "→ best가 mean보다 항상 크거나 같음. best를 실력으로 쓰면 극단 과신(K-N).",
            "",
            "## 2. Part B — feature-bucket λ → top5 재선정 ge3",
            "",
            "| 뇌 | baseline | best λ | best ge3 | Δ vs baseline |",
            "|----|---------:|-------:|---------:|--------------:|",
        ]
    )
    for tag in BRAINS:
        r = lam[tag]
        lines.append(
            f"| {tag} | {r['baseline_repack']['ge3_rate']:.4f} | {r['best_lambda']} | "
            f"**{r['best_ge3']:.4f}** | {r['delta_vs_baseline']:+.4f} |"
        )
    lines.extend(["", "### λ 상세", ""])
    for tag in BRAINS:
        lines.append(f"#### {tag}")
        lines.append("| λ | λ_eff | ge3 | mean_best | vs null |")
        lines.append("|--:|------:|----:|----------:|-------:|")
        for lk, v in lam[tag]["by_lambda"].items():
            lines.append(
                f"| {lk} | {v['lambda_effective']} | {v['ge3_rate']:.4f} | "
                f"{v['mean_best']} | {v['delta_vs_null']:+.4f} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 3. Wire 상태 · 권고",
            "",
            f"- `FEEDBACK_MATCH_MODE` live = **{mode}** (mean=K-N 차단)",
            f"- feature λ → signal_pool 가중 wire: **"
            f"{'GO-WAIT 형승인' if clear else 'HOLD'}**",
            "- W_HINT/quota/BOOST_CAPS: 미수정",
            "",
            "## 근거",
            "",
            "- `testlotto_evolve_log` · FINDINGS K-N · MULTI_AI_PATCH Phase2",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print("mode=", mode, "clear_uplift=", clear)
    print(json.dumps({t: {"base": lam[t]["baseline_repack"]["ge3_rate"], "best_l": lam[t]["best_lambda"], "best_g": lam[t]["best_ge3"], "d": lam[t]["delta_vs_baseline"]} for t in BRAINS}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
