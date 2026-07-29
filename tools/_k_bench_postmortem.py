# -*- coding: utf-8 -*-
"""K-BENCH-01 — postmortem 진단 (READ-ONLY live walk-forward).

3뇌 live predict → 4보조 채점 → V2 set_no_asc 5장 발권.
회차별 hit/miss 패턴·tier·AUX 상관·쿼터 갭 집계.
coordinator·predict_*·learn_state 미수정 · DB write 금지.
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
random.seed(42)

from app.testlotto.brains import (  # noqa: E402
    aux_balance_keeper,
    aux_miss_detective,
    aux_pattern_spotlight,
    aux_referee,
    predict_flow_shaman,
    predict_review_king,
    predict_stat_fairy,
)
from app.testlotto.brains.coordinator import apply_markov_wire_quota  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.features.draw_features import ac_value, consecutive_pairs, odd_even_ratio  # noqa: E402
from app.testlotto.learn_state import get_referee_weights  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260729_KBENCH_POSTMORTEM.json"
OUT_MD = ROOT / "reports" / "20260729_KBENCH_POSTMORTEM.md"

DRAW_START = 53
DRAW_END = 1234
WIRE_PIN_GE3 = 0.1447
WIRE_PIN_MEAN = 1.7504
NULL_GE3 = 0.1137
MC_SEED = 42

PREDICT_MODULES = {
    "markov": predict_flow_shaman,
    "stat": predict_stat_fairy,
    "review": predict_review_king,
}

AUX_MODULES: dict[str, Any] = {
    "miss": aux_miss_detective,
    "pattern": aux_pattern_spotlight,
    "balance": aux_balance_keeper,
    "referee": aux_referee,
}
AUX_WEIGHTS = [0.25, 0.25, 0.25, 0.25]


def _prediction_rank_tier(matched_count: int, bonus_matched: int) -> int:
    bm = 1 if bonus_matched == 1 else 0
    if matched_count == 6:
        return 1
    if matched_count == 5 and bm == 1:
        return 2
    if matched_count == 5:
        return 3
    if matched_count == 4:
        return 4
    if matched_count == 3:
        return 5
    return 0


def _aux_composite_score(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    total = 0.0
    for mod, w in zip(AUX_MODULES.values(), AUX_WEIGHTS):
        total += w * mod.score_set(nums, draws, target_draw_no, brain_tag=brain_tag)
    return total


def _aux_individual_scores(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> dict[str, float]:
    return {
        k: round(mod.score_set(nums, draws, target_draw_no, brain_tag=brain_tag), 4)
        for k, mod in AUX_MODULES.items()
    }


def _apply_aux_scoring(
    candidates: list[dict], draws: list[dict], target_draw_no: int
) -> list[dict]:
    ref_weights = get_referee_weights()
    out: list[dict] = []
    for c in candidates:
        tag = c.get("brain_tag", "") or None
        aux_total = _aux_composite_score(c["nums"], draws, target_draw_no, brain_tag=tag)
        base = float(c.get("confidence", 60))
        brain_w = ref_weights.get(c.get("brain_tag", ""), 1.0 / 3)
        final_conf = min(99.5, base * 0.5 * brain_w + aux_total * 40 + base * 0.1)
        out.append(
            {
                **c,
                "aux_total": round(aux_total, 4),
                "aux_scores": _aux_individual_scores(
                    c["nums"], draws, target_draw_no, brain_tag=tag
                ),
                "confidence": round(final_conf, 1),
            }
        )
    return out


def _draw_features(winning: list[int]) -> dict[str, Any]:
    odd, even = odd_even_ratio(winning)
    return {
        "sum": sum(winning),
        "odd_count": odd,
        "even_count": even,
        "ac": ac_value(winning),
        "consecutive": consecutive_pairs(winning),
    }


def _empty_tier() -> dict[str, int]:
    return {"r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0}


def _record_tier(acc: dict[str, int], tier: int) -> None:
    if 1 <= tier <= 5:
        acc[f"r{tier}"] += 1


def run_walkforward() -> tuple[list[dict], dict[str, Any], int]:
    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    draw_logs: list[dict] = []
    tier_selected = _empty_tier()
    tier_all15 = _empty_tier()
    brain_best_counts: dict[str, int] = defaultdict(int)
    ge3_plus_features: list[dict] = []
    ge3_minus_features: list[dict] = []
    quota_missed_draws = 0
    quota_gap_sum = 0
    selected_bests: list[int] = []
    aux_totals: list[float] = []
    aux_hits: list[int] = []
    per_aux: dict[str, tuple[list[float], list[int]]] = {
        k: ([], []) for k in AUX_MODULES
    }

    for ri, row in enumerate(rows):
        if ri % 100 == 0:
            print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        bonus = int(row.get("bonus") or 0)
        winning = sorted(actual)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        candidates: list[dict] = []
        for tag, mod in PREDICT_MODULES.items():
            sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
            for i, s in enumerate(sets):
                sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
                candidates.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})

        if not candidates:
            continue

        scored = _apply_aux_scoring(candidates, draws, draw_no)
        selected = apply_markov_wire_quota(scored)
        selected_ids = {id(c) for c in selected}

        all_15: list[dict] = []
        best_hit = 0
        best_entry: dict | None = None

        for c in scored:
            nums = [int(x) for x in c["nums"]]
            mc = len(set(nums) & actual)
            bm = 1 if bonus in set(nums) else 0
            tier = _prediction_rank_tier(mc, bm)
            tag = str(c.get("brain_tag") or "")
            set_idx = int(c.get("pred_set_no") or c.get("set_no") or 0)
            entry = {
                "brain": tag,
                "set_idx": set_idx,
                "numbers": nums,
                "hit_count": mc,
                "tier": tier,
                "aux_scores": c.get("aux_scores") or {},
                "confidence": float(c.get("confidence") or 0),
                "aux_total": float(c.get("aux_total") or 0),
            }
            all_15.append(entry)
            _record_tier(tier_all15, tier)

            aux_totals.append(entry["aux_total"])
            aux_hits.append(mc)
            for ak in AUX_MODULES:
                per_aux[ak][0].append(entry["aux_scores"].get(ak, 0.0))
                per_aux[ak][1].append(mc)

            if mc > best_hit or (mc == best_hit and best_entry is None):
                best_hit = mc
                best_entry = {
                    "brain": tag,
                    "set_idx": set_idx,
                    "hit_count": mc,
                    "tier": tier,
                }

        selected_5: list[dict] = []
        selected_best_hit = 0
        for c in selected:
            nums = [int(x) for x in c["nums"]]
            mc = len(set(nums) & actual)
            bm = 1 if bonus in set(nums) else 0
            tier = _prediction_rank_tier(mc, bm)
            tag = str(c.get("brain_tag") or "")
            set_idx = int(c.get("pred_set_no") or c.get("set_no") or 0)
            selected_5.append(
                {
                    "brain": tag,
                    "set_idx": set_idx,
                    "numbers": nums,
                    "hit_count": mc,
                    "tier": tier,
                }
            )
            _record_tier(tier_selected, tier)
            selected_best_hit = max(selected_best_hit, mc)

        selected_bests.append(selected_best_hit)
        feats = _draw_features(winning)
        if selected_best_hit >= 3:
            ge3_plus_features.append(feats)
        else:
            ge3_minus_features.append(feats)

        if best_entry and selected_best_hit < best_hit:
            quota_missed_draws += 1
            quota_gap_sum += best_hit - selected_best_hit

        if best_entry:
            brain_best_counts[best_entry["brain"]] += 1

        draw_logs.append(
            {
                "draw_no": draw_no,
                "winning": winning,
                "selected_5": selected_5,
                "all_15": all_15,
                "best_hit": best_entry,
                "selected_best_hit": selected_best_hit,
                "draw_features": feats,
                "quota_missed": selected_best_hit < best_hit,
                "quota_gap": max(0, best_hit - selected_best_hit),
            }
        )

    n_eval = len(draw_logs)

    def _feat_mean(feats: list[dict], key: str) -> float | None:
        if not feats:
            return None
        return round(sum(f[key] for f in feats) / len(feats), 3)

    ge3_feat_diff: dict[str, Any] = {}
    for key in ("sum", "odd_count", "ac", "consecutive"):
        gp = _feat_mean(ge3_plus_features, key)
        gm = _feat_mean(ge3_minus_features, key)
        ge3_feat_diff[key] = {
            "ge3_plus_mean": gp,
            "ge3_minus_mean": gm,
            "delta": round((gp or 0) - (gm or 0), 3) if gp is not None and gm is not None else None,
        }

    def _safe_spearman(xs: list[float], ys: list[int]) -> dict[str, Any]:
        if len(xs) < 10:
            return {"rho": None, "p": None, "n": len(xs)}
        rho, p = spearmanr(xs, ys)
        if rho != rho or p != p:  # NaN guard (constant input)
            return {"rho": None, "p": None, "n": len(xs), "note": "constant_input"}
        return {"rho": round(float(rho), 4), "p": round(float(p), 6), "n": len(xs)}

    aux_corr = {
        "aux_total": _safe_spearman(aux_totals, aux_hits),
        **{k: _safe_spearman(v[0], v[1]) for k, v in per_aux.items()},
    }

    # simple bin: aux_total quartile vs mean hit
    aux_bins: list[dict] = []
    if aux_totals:
        sorted_pairs = sorted(zip(aux_totals, aux_hits), key=lambda x: x[0])
        q = len(sorted_pairs) // 4 or 1
        for i, label in enumerate(["Q1_low", "Q2", "Q3", "Q4_high"]):
            chunk = sorted_pairs[i * q : (i + 1) * q if i < 3 else len(sorted_pairs)]
            if chunk:
                aux_bins.append(
                    {
                        "bin": label,
                        "n": len(chunk),
                        "aux_total_mean": round(sum(x[0] for x in chunk) / len(chunk), 4),
                        "hit_mean": round(sum(x[1] for x in chunk) / len(chunk), 4),
                    }
                )

    n_sel = n_eval * 5
    n_all = n_eval * 15
    brain_best_ratio = {
        b: round(brain_best_counts[b] / n_eval, 4) if n_eval else 0.0
        for b in PREDICT_MODULES
    }

    ge3_c = sum(1 for x in selected_bests if x >= 3)
    mean_hit = round(sum(selected_bests) / n_eval, 4) if n_eval else 0.0
    ge3_rate = round(ge3_c / n_eval, 4) if n_eval else 0.0

    aggregates = {
        "tier_selected_5": {**tier_selected, "n_sets": n_sel},
        "tier_all_15": {**tier_all15, "n_sets": n_all},
        "brain_best_hit_ratio": brain_best_ratio,
        "ge3_draw_features_diff": ge3_feat_diff,
        "ge3_plus_n": len(ge3_plus_features),
        "ge3_minus_n": len(ge3_minus_features),
        "quota_missed": {
            "n_draws": quota_missed_draws,
            "rate": round(quota_missed_draws / n_eval, 4) if n_eval else 0.0,
            "avg_gap_when_missed": round(quota_gap_sum / quota_missed_draws, 3)
            if quota_missed_draws
            else 0.0,
        },
        "aux_correlation": aux_corr,
        "aux_total_bins": aux_bins,
        "summary": {
            "n_eval": n_eval,
            "mean_hit_selected_best": mean_hit,
            "ge3_rate": ge3_rate,
            "ge3_count": ge3_c,
        },
    }

    return draw_logs, aggregates, n_eval


def _detect_signals(agg: dict[str, Any]) -> tuple[str, list[str]]:
    signals: list[str] = []
    partial: list[str] = []

    qm = agg["quota_missed"]
    if qm["rate"] >= 0.15 and qm["avg_gap_when_missed"] >= 0.5:
        signals.append(
            f"쿼터 갭: {qm['rate']:.1%} 회차에서 15중 best > 선택5 best "
            f"(평균 gap={qm['avg_gap_when_missed']})"
        )
    elif qm["rate"] >= 0.08:
        partial.append(f"쿼터 갭 약함: rate={qm['rate']:.1%}")

    ac = agg["aux_correlation"]["aux_total"]
    if ac.get("rho") is not None and abs(ac["rho"]) >= 0.08 and ac.get("p", 1) < 0.01:
        signals.append(f"AUX_total↔hit spearman ρ={ac['rho']} p={ac['p']}")
    elif ac.get("rho") is not None and abs(ac["rho"]) >= 0.04:
        partial.append(f"AUX_total↔hit 약한 상관 ρ={ac['rho']}")

    bbr = agg["brain_best_hit_ratio"]
    top_brain = max(bbr, key=bbr.get) if bbr else None
    if top_brain and bbr[top_brain] >= 0.45:
        signals.append(f"뇌 지배: {top_brain}가 15중 best {bbr[top_brain]:.1%}")
    elif top_brain and bbr[top_brain] >= 0.38:
        partial.append(f"뇌 편향 약함: {top_brain}={bbr[top_brain]:.1%}")

    for key, diff in agg["ge3_draw_features_diff"].items():
        d = diff.get("delta")
        if d is not None and abs(d) >= 5 and key == "sum":
            signals.append(f"ge3+ vs ge3- {key} Δ={d}")
        elif d is not None and abs(d) >= 0.3 and key in ("odd_count", "consecutive"):
            partial.append(f"ge3+ vs ge3- {key} Δ={d}")

    if signals:
        return "SIGNAL_FOUND", signals
    if partial:
        return "PARTIAL", partial
    return "NO_SIGNAL", []


def _feedback_axes(agg: dict[str, Any], verdict: str, findings: list[str]) -> list[str]:
    axes: list[str] = []
    qm = agg["quota_missed"]
    if qm["rate"] >= 0.08:
        axes.append(
            "쿼터 대안 survey: set_no_asc 대신 뇌 내 AUX/confidence top-1 유지 + 쿼터 "
            "(K-BENCH-02 재확인 — baseline 우수 시 HOLD)"
        )
    ac = agg["aux_correlation"]
    for k in ("miss", "pattern", "balance", "referee"):
        r = ac.get(k, {})
        if r.get("rho") is not None and abs(r["rho"]) >= 0.05:
            axes.append(f"AUX {k} 축 가중 재조정 survey (ρ={r['rho']})")
    bbr = agg["brain_best_hit_ratio"]
    top = max(bbr, key=bbr.get) if bbr else None
    if top and bbr[top] >= 0.40:
        axes.append(f"뇌별 quota 재검토: {top} best-hit {bbr[top]:.1%} — quota≠실력 가능")
    if agg["ge3_plus_n"] >= 30:
        axes.append("ge3+ 회차 draw_features bin별 stratify (K-BENCH-04 후보)")
    if verdict == "NO_SIGNAL":
        axes.append("등수(tier)별 피드백 태그 축적 — apply_feedback 확장 (형 GO 후 WIRE)")
    if not axes:
        axes.append("현 패턴 무신호 — V2 pin 유지 · 피드백 축은 형 지정 대기")
    return axes


def _write_report(out: dict[str, Any]) -> None:
    agg = out["aggregates"]
    sm = agg["summary"]
    ts = sel = agg["tier_selected_5"]
    tall = agg["tier_all_15"]
    verdict = out["verdict"]
    findings = out.get("signal_findings") or []
    axes = out.get("feedback_axes") or []

    ge3_c = sm["ge3_count"]
    n = sm["n_eval"]
    p_null = float(binomtest(ge3_c, n, NULL_GE3, alternative="greater").pvalue) if n else 1.0

    lines: list[str] = []
    lines.append("# K-BENCH-01 — postmortem 진단 (READ-ONLY live WF)")
    lines.append(
        f"\n날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · "
        f"**{verdict}** · seed={MC_SEED}"
    )

    lines.append("\n## SUMMARY (BENCH_PROTOCOL §6)")
    lines.append("| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | p (vs null) | 비고 |")
    lines.append("|-------|----------|------|----------|-----|--------------|-------------|------|")
    lines.append("| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | E[match]=6×6/45 |")
    lines.append(
        f"| **WIRE-V2 pin** | stored | {WIRE_PIN_MEAN} | {WIRE_PIN_GE3} | ✓ | — | — | PINNED |"
    )
    lines.append(
        f"| **K-BENCH-01 WF** | WF live | **{sm['mean_hit_selected_best']}** | "
        f"**{sm['ge3_rate']}** | — | "
        f"{round(sm['ge3_rate'] - NULL_GE3, 4):+.4f} | {round(p_null, 4)} | "
        f"n_eval={n} · selected best-of-5 |"
    )

    lines.append("\n## tier 피벗 (BENCH_PROTOCOL §7 · WF live)")
    lines.append("\n### 선택 5장 (set_no_asc 쿼터)")
    lines.append("| scope | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |")
    lines.append("|-------|----------|----|----|----|----|----|-----|--------|")
    ge3_s = sel["r3"] + sel["r4"] + sel["r5"]
    lines.append(
        f"| selected_5 | WF live | {sel['r1']} | {sel['r2']} | {sel['r3']} | "
        f"{sel['r4']} | {sel['r5']} | {ge3_s} | {sel['n_sets']} |"
    )
    lines.append("\n### 전체 15장")
    ge3_a = tall["r3"] + tall["r4"] + tall["r5"]
    lines.append("| scope | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |")
    lines.append("|-------|----------|----|----|----|----|----|-----|--------|")
    lines.append(
        f"| all_15 | WF live | {tall['r1']} | {tall['r2']} | {tall['r3']} | "
        f"{tall['r4']} | {tall['r5']} | {ge3_a} | {tall['n_sets']} |"
    )

    lines.append("\n### 뇌별 tier (선택 5 · quota별)")
    lines.append("| brain | r3 | r4 | r5 | ge3 | n_sets |")
    lines.append("|-------|----|----|----|-----|--------|")
    brain_tier = out.get("tier_by_brain_selected") or {}
    for b in ("markov", "stat", "review"):
        bt = brain_tier.get(b, _empty_tier())
        ns = bt.get("n_sets", 0)
        g3 = bt.get("r3", 0) + bt.get("r4", 0) + bt.get("r5", 0)
        lines.append(f"| {b} | {bt.get('r3',0)} | {bt.get('r4',0)} | {bt.get('r5',0)} | {g3} | {ns} |")

    lines.append("\n## 집계")
    qm = agg["quota_missed"]
    lines.append(f"- **쿼터 갭:** {qm['n_draws']}/{n} ({qm['rate']:.1%}) — 15중 best > 선택5 best")
    lines.append(f"- **갭 평균(놓친 회차):** {qm['avg_gap_when_missed']}")
    lines.append("- **15중 best-hit 뇌 비율:**")
    for b, r in agg["brain_best_hit_ratio"].items():
        lines.append(f"  - {b}: {r:.1%}")

    lines.append("\n### ge3+ vs ge3- draw_features")
    lines.append("| feature | ge3+ mean | ge3- mean | Δ |")
    lines.append("|---------|----------:|----------:|--:|")
    for key, d in agg["ge3_draw_features_diff"].items():
        lines.append(
            f"| {key} | {d.get('ge3_plus_mean')} | {d.get('ge3_minus_mean')} | {d.get('delta')} |"
        )

    lines.append("\n### AUX ↔ hit_count 상관 (15×n_eval 세트)")
    lines.append("| axis | spearman ρ | p | n |")
    lines.append("|------|----------:|--:|--:|")
    for k, v in agg["aux_correlation"].items():
        lines.append(f"| {k} | {v.get('rho')} | {v.get('p')} | {v.get('n')} |")

    if agg.get("aux_total_bins"):
        lines.append("\n### AUX total 사분위 bin")
        lines.append("| bin | n | aux_total_mean | hit_mean |")
        lines.append("|-----|--:|---------------:|---------:|")
        for b in agg["aux_total_bins"]:
            lines.append(
                f"| {b['bin']} | {b['n']} | {b['aux_total_mean']} | {b['hit_mean']} |"
            )

    lines.append("\n## 발견 패턴")
    if findings:
        for f in findings:
            lines.append(f"- {f}")
    else:
        lines.append("- **무신호** — postmortem 집계에서 actionable 패턴 미발견.")

    lines.append("\n## 다음 피드백 축 후보 (코드 수정 없음 · 제안만)")
    for a in axes:
        lines.append(f"- {a}")

    next_id = "K-BENCH-01-WIRE" if verdict == "SIGNAL_FOUND" else "K-ATTACK-HOLD"
    lines.append(f"\n## Verdict / NEXT")
    lines.append(f"- **verdict:** `{verdict}`")
    lines.append(f"- **→ `{next_id}`** (형 GO 필요 · coordinator 수정 금지)")
    lines.append(
        "\n*진단 survey — ge3 PASS/FAIL 아님. pin 대비 ge3는 참고용.*"
    )

    lines.append("\n---\n\n## 팩트체크")
    lines.append("| 항목 | JSON | 보고서 |")
    lines.append("|------|------|------|")
    lines.append(f"| n_eval | {n} | {n} |")
    lines.append(f"| ge3_rate | {sm['ge3_rate']} | {sm['ge3_rate']} |")
    lines.append(f"| quota_missed_rate | {qm['rate']} | {qm['rate']} |")
    lines.append(f"| verdict | {verdict} | {verdict} |")
    lines.append(f"| seed | {MC_SEED} | {MC_SEED} |")
    lines.append(
        f"\nASCII `-` 구분 · SSOT=`docs/benchmarks/20260729_KBENCH_POSTMORTEM.json`"
    )

    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / "20260729_KBENCH_POSTMORTEM.md"
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_MD}", flush=True)


def main() -> None:
    t0 = time.time()
    print(
        f"K-BENCH-01 postmortem live WF draws {DRAW_START}~{DRAW_END} seed={MC_SEED}",
        flush=True,
    )

    draw_logs, aggregates, n_eval = run_walkforward()

    # tier by brain (selected)
    tier_by_brain: dict[str, dict] = {b: {**_empty_tier(), "n_sets": 0} for b in PREDICT_MODULES}
    for dl in draw_logs:
        for s in dl["selected_5"]:
            b = s["brain"]
            if b in tier_by_brain:
                tier_by_brain[b]["n_sets"] += 1
                _record_tier(tier_by_brain[b], s["tier"])

    verdict, findings = _detect_signals(aggregates)
    axes = _feedback_axes(aggregates, verdict, findings)
    recommended = "K-BENCH-01-WIRE" if verdict == "SIGNAL_FOUND" else "K-ATTACK-HOLD"
    if verdict == "PARTIAL":
        recommended = "K-BENCH-01-WIRE (형 GO · PARTIAL)"

    out: dict[str, Any] = {
        "id": "K-BENCH-01-POSTMORTEM",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": n_eval,
        "draw_range": [DRAW_START, DRAW_END],
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "null_ge3": NULL_GE3,
        "mc_seed": MC_SEED,
        "sets_per_predict_brain": SETS_PER_PREDICT_BRAIN,
        "pipeline": "live_predict_sets + aux_scoring + apply_markov_wire_quota(set_no_asc)",
        "aggregates": aggregates,
        "tier_by_brain_selected": tier_by_brain,
        "verdict": verdict,
        "signal_findings": findings,
        "feedback_axes": axes,
        "recommended_next": recommended,
        "draw_logs": draw_logs,
        "db_code_write": False,
        "coordinator_modified": False,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON}", flush=True)

    _write_report(out)
    print(f"verdict={verdict} recommended={recommended}", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
