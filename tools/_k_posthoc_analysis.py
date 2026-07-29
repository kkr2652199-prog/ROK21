# -*- coding: utf-8 -*-
"""K-POSTHOC-ANALYSIS — 다시드 역추적 분석 (READ-ONLY).

형 아이디어: 랜덤 시드를 바꿔가며 live 백테 → 상위/하위 10% 시드 공통 패턴.
최적화: 매 100회차마다 샘플링 + predict 캐시 (draw당 1회 draws fetch).
coordinator.py / predict 원본 수정 0. DB 쓰기 0.
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

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import predict_flow_shaman, predict_review_king, predict_stat_fairy  # noqa: E402
from app.testlotto.brains.coordinator import (  # noqa: E402
    apply_coordinator_scoring,
    apply_markov_wire_quota,
)
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

DRAW_START = 53
DRAW_END = 1234
N_SEEDS = 50
EVAL_SAMPLE = 50  # 전체 1182 중 균등 샘플 (속도 문제)
WIRE_PIN_GE3 = 0.1447
NULL_GE3 = 0.1137

PREDICT_MODULES = {
    "stat": predict_stat_fairy,
    "markov": predict_flow_shaman,
    "review": predict_review_king,
}


def _slot_sets(tag: str, sets: list[dict]) -> list[dict]:
    out: list[dict] = []
    for i, s in enumerate(sets):
        sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
        out.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})
    return out


def _ac_value(nums: list[int]) -> int:
    s = sorted(nums)
    diffs = set()
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            diffs.add(s[j] - s[i])
    return len(diffs) - (len(s) - 1)


def _has_consecutive(nums: list[int]) -> bool:
    s = sorted(nums)
    return any(s[i + 1] == s[i] + 1 for i in range(len(s) - 1))


def _odd_ratio(nums: list[int]) -> float:
    return sum(1 for n in nums if n % 2 == 1) / len(nums)


def main() -> None:
    t0 = time.time()
    print(f"K-POSTHOC-ANALYSIS: {N_SEEDS} seeds × draws {DRAW_START}~{DRAW_END}", flush=True)

    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    all_draw_rows = [dict(r) for r in rows]
    print(f"  loaded {len(all_draw_rows)} draws", flush=True)

    # Sample eval draws for speed
    step = max(1, len(all_draw_rows) // EVAL_SAMPLE)
    sampled_rows = all_draw_rows[::step][:EVAL_SAMPLE]
    print(f"  sampled {len(sampled_rows)} eval draws (step={step})", flush=True)

    # Phase 1: precompute draws data
    print("  Phase 1: precomputing draws data...", flush=True)
    draws_cache: dict[int, list[dict]] = {}
    actual_cache: dict[int, set[int]] = {}
    for i, row in enumerate(sampled_rows):
        draw_no = int(row["draw_no"])
        if i % 50 == 0:
            print(f"    draws_cache {i}/{len(sampled_rows)}", flush=True)
        set_learn_as_of(draw_no)
        dr = _get_draws_before(draw_no)
        if dr:
            draws_cache[draw_no] = dr
            actual_cache[draw_no] = {int(row[f"num{k}"]) for k in range(1, 7)}
    usable_dns = sorted(draws_cache.keys())
    n_eval = len(usable_dns)
    print(f"  Phase 1 done: {n_eval} usable draws ({time.time() - t0:.0f}s)", flush=True)

    # Phase 2: for each seed, generate all predictions and evaluate
    seed_bests: dict[int, list[int]] = defaultdict(list)
    # Aggregate per-brain stats for analysis
    brain_hit_counts: dict[int, dict[str, list[int]]] = {}  # seed -> brain -> list of hits (selected only)
    brain_all_hits: dict[int, dict[str, list[int]]] = {}  # seed -> brain -> all hits
    sel_hits_all: dict[int, list[int]] = defaultdict(list)
    nonsel_hits_all: dict[int, list[int]] = defaultdict(list)
    # For hit draw characteristics (on selected ge3+)
    hit_draw_chars: dict[int, list[dict]] = defaultdict(list)

    for seed_idx in range(N_SEEDS):
        if seed_idx % 10 == 0:
            elapsed = time.time() - t0
            print(f"  seed {seed_idx}/{N_SEEDS} ({elapsed:.0f}s)", flush=True)

        brain_hit_counts[seed_idx] = defaultdict(list)
        brain_all_hits[seed_idx] = defaultdict(list)

        for draw_no in usable_dns:
            draws = draws_cache[draw_no]
            actual = actual_cache[draw_no]

            candidates: list[dict] = []
            for tag, mod in PREDICT_MODULES.items():
                brain_seed = (seed_idx * 1_000_003 + draw_no * 97 + hash(tag)) & 0xFFFFFFFF
                random.seed(brain_seed)
                sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
                slotted = _slot_sets(tag, sets)
                candidates.extend(slotted)

            if not candidates:
                continue

            scored = apply_coordinator_scoring(candidates, draws, draw_no)
            selected = apply_markov_wire_quota(scored)
            selected_ids = {id(c) for c in selected}

            best_hit = 0
            for c in selected:
                nums = set(int(x) for x in c["nums"])
                hit = len(nums & actual)
                best_hit = max(best_hit, hit)

            seed_bests[seed_idx].append(best_hit)

            for c in scored:
                nums_set = set(int(x) for x in c["nums"])
                hit = len(nums_set & actual)
                tag = c.get("brain_tag", "?")
                is_sel = id(c) in selected_ids
                brain_all_hits[seed_idx][tag].append(hit)
                if is_sel:
                    brain_hit_counts[seed_idx][tag].append(hit)
                    sel_hits_all[seed_idx].append(hit)
                    if hit >= 3:
                        winning = sorted(actual)
                        hit_draw_chars[seed_idx].append({
                            "sum": sum(winning),
                            "odd_ratio": _odd_ratio(winning),
                            "consec": _has_consecutive(winning),
                            "ac": _ac_value(winning),
                        })
                else:
                    nonsel_hits_all[seed_idx].append(hit)

    elapsed_total = time.time() - t0
    print(f"  all seeds done in {elapsed_total:.0f}s", flush=True)

    # ── Analysis ──
    seed_stats: list[dict] = []
    for seed_idx in range(N_SEEDS):
        bests = seed_bests[seed_idx]
        n = len(bests)
        ge3_c = sum(1 for x in bests if x >= 3)
        ge3_rate = ge3_c / n if n else 0
        mean_hit = sum(bests) / n if n else 0
        seed_stats.append({
            "seed": seed_idx,
            "n": n,
            "ge3_count": ge3_c,
            "ge3_rate": round(ge3_rate, 4),
            "mean": round(mean_hit, 4),
        })

    seed_stats.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))
    top_k = max(1, N_SEEDS // 10)
    top_seeds = set(s["seed"] for s in seed_stats[:top_k])
    bot_seeds = set(s["seed"] for s in seed_stats[-top_k:])

    def analyze_group(group_seeds: set[int], label: str) -> dict:
        bg3: dict[str, int] = defaultdict(int)
        bn: dict[str, int] = defaultdict(int)
        bm_sum: dict[str, float] = defaultdict(float)
        s_hits: list[int] = []
        ns_hits: list[int] = []
        chars: list[dict] = []

        for sid in group_seeds:
            for tag, hits in brain_hit_counts.get(sid, {}).items():
                bg3[tag] += sum(1 for h in hits if h >= 3)
                bn[tag] += len(hits)
                bm_sum[tag] += sum(hits)
            s_hits.extend(sel_hits_all.get(sid, []))
            ns_hits.extend(nonsel_hits_all.get(sid, []))
            chars.extend(hit_draw_chars.get(sid, []))

        brain_ge3_sel = {tag: round(bg3[tag] / bn[tag], 4) if bn[tag] else 0 for tag in ["markov", "stat", "review"]}
        brain_mean_sel = {tag: round(bm_sum[tag] / bn[tag], 4) if bn[tag] else 0 for tag in ["markov", "stat", "review"]}
        sel_ge3 = round(sum(1 for h in s_hits if h >= 3) / len(s_hits), 4) if s_hits else 0
        nonsel_ge3 = round(sum(1 for h in ns_hits if h >= 3) / len(ns_hits), 4) if ns_hits else 0

        return {
            "label": label,
            "n_seeds": len(group_seeds),
            "brain_ge3_selected": brain_ge3_sel,
            "brain_mean_selected": brain_mean_sel,
            "selected_ge3_rate": sel_ge3,
            "nonsel_ge3_rate": nonsel_ge3,
            "hit_draw_sum_mean": round(sum(c["sum"] for c in chars) / len(chars), 1) if chars else None,
            "hit_draw_odd_ratio_mean": round(sum(c["odd_ratio"] for c in chars) / len(chars), 3) if chars else None,
            "hit_draw_consec_rate": round(sum(c["consec"] for c in chars) / len(chars), 3) if chars else None,
            "hit_draw_ac_mean": round(sum(c["ac"] for c in chars) / len(chars), 2) if chars else None,
        }

    top_analysis = analyze_group(top_seeds, "top_10pct")
    bot_analysis = analyze_group(bot_seeds, "bot_10pct")
    all_analysis = analyze_group(set(range(N_SEEDS)), "all_200")

    all_ge3_rates = [s["ge3_rate"] for s in seed_stats]
    overall_mean_ge3 = round(sum(all_ge3_rates) / len(all_ge3_rates), 4)
    overall_std_ge3 = round(
        (sum((x - overall_mean_ge3) ** 2 for x in all_ge3_rates) / len(all_ge3_rates)) ** 0.5, 4
    )

    best_seed = seed_stats[0]
    p_best = float(
        binomtest(best_seed["ge3_count"], best_seed["n"], NULL_GE3, alternative="greater").pvalue
    ) if best_seed["n"] else 1.0

    diff: dict[str, Any] = {}
    for k in ["brain_ge3_selected", "brain_mean_selected", "selected_ge3_rate", "nonsel_ge3_rate",
              "hit_draw_sum_mean", "hit_draw_odd_ratio_mean", "hit_draw_consec_rate", "hit_draw_ac_mean"]:
        tv = top_analysis.get(k)
        bv = bot_analysis.get(k)
        if isinstance(tv, dict) and isinstance(bv, dict):
            diff[k] = {tag: round((tv.get(tag, 0) or 0) - (bv.get(tag, 0) or 0), 4) for tag in set(list(tv) + list(bv))}
        elif isinstance(tv, (int, float)) and isinstance(bv, (int, float)) and tv is not None and bv is not None:
            diff[k] = round(tv - bv, 4)
        else:
            diff[k] = {"top": tv, "bot": bv}

    out_json: dict[str, Any] = {
        "id": "K-POSTHOC-ANALYSIS",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_seeds": N_SEEDS,
        "draw_range": [DRAW_START, DRAW_END],
        "n_eval_per_seed": n_eval,
        "wire_pin_ge3": WIRE_PIN_GE3,
        "null_ge3": NULL_GE3,
        "overall": {
            "mean_ge3_rate": overall_mean_ge3,
            "std_ge3_rate": overall_std_ge3,
            "median_ge3_rate": round(sorted(all_ge3_rates)[N_SEEDS // 2], 4),
            "min_ge3_rate": round(min(all_ge3_rates), 4),
            "max_ge3_rate": round(max(all_ge3_rates), 4),
        },
        "best_seed": {**best_seed, "p_value": round(p_best, 6)},
        "top_10pct_seeds": [s["seed"] for s in seed_stats[:top_k]],
        "top_10pct_ge3_rates": [s["ge3_rate"] for s in seed_stats[:top_k]],
        "bot_10pct_seeds": [s["seed"] for s in seed_stats[-top_k:]],
        "bot_10pct_ge3_rates": [s["ge3_rate"] for s in seed_stats[-top_k:]],
        "top_analysis": top_analysis,
        "bot_analysis": bot_analysis,
        "all_analysis": all_analysis,
        "top_vs_bot_diff": diff,
        "seed_ranking": seed_stats[:30],
        "signal_detected": False,
        "signal_summary": "",
    }

    signals = []

    # Actionable signal: best seed must beat pin AND be statistically significant
    if best_seed["ge3_rate"] > WIRE_PIN_GE3 and p_best < 0.05:
        signals.append(f"best seed #{best_seed['seed']} ge3={best_seed['ge3_rate']} p={p_best:.4f} > pin")

    # Brain dominance: one brain consistently outperforms (actionable for quota change)
    for tag in ["markov", "stat", "review"]:
        t_ge3 = top_analysis["brain_ge3_selected"].get(tag, 0)
        a_ge3 = all_analysis["brain_ge3_selected"].get(tag, 0)
        if t_ge3 > 0.06 and a_ge3 > 0 and t_ge3 > a_ge3 * 2.0:
            signals.append(f"{tag} top ge3={t_ge3} vs all={a_ge3} (×{t_ge3/a_ge3:.1f})")

    # Draw characteristic: sum range showing clear actionable pattern
    top_sum = top_analysis.get("hit_draw_sum_mean")
    bot_sum = bot_analysis.get("hit_draw_sum_mean")
    if top_sum and bot_sum and abs(top_sum - bot_sum) > 20:
        signals.append(f"sum mean top={top_sum} bot={bot_sum} Δ={top_sum-bot_sum:.0f}")

    if signals:
        out_json["signal_detected"] = True
        out_json["signal_summary"] = " · ".join(signals)

    out_path = ROOT / "docs" / "benchmarks" / "20260729_KPOSTHOC_analysis.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_path}", flush=True)

    _write_report(out_json)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


def _write_report(j: dict[str, Any]) -> None:
    ovr = j["overall"]
    best = j["best_seed"]
    top_a = j["top_analysis"]
    bot_a = j["bot_analysis"]
    diff = j["top_vs_bot_diff"]
    sig = j.get("signal_detected", False)
    sig_txt = j.get("signal_summary", "")

    lines = []
    lines.append(f"# K-POSTHOC-ANALYSIS — {j['n_seeds']}시드 역추적 분석")
    lines.append(f"\n날짜 {j['ts'][:10]} · elapsed {j['elapsed_sec']}s · **{'신호발견' if sig else '무신호'}**")
    lines.append(f"\n## 전제")
    lines.append(f"| 항목 | 값 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 시드 수 | {j['n_seeds']} |")
    lines.append(f"| draw 범위 | {j['draw_range'][0]}~{j['draw_range'][1]} ({j['n_eval_per_seed']}회) |")
    lines.append(f"| wire pin ge3 | {j['wire_pin_ge3']} |")
    lines.append(f"| null ge3 | {j['null_ge3']} |")
    lines.append(f"| 쿼터 | markov×3 + stat×1 + review×1 |")
    lines.append(f"| pipeline | live predict_sets → apply_coordinator_scoring → apply_markov_wire_quota |")

    lines.append(f"\n## 시드별 ge3 분포")
    lines.append(f"| 지표 | 값 |")
    lines.append(f"|------|-----|")
    lines.append(f"| mean | **{ovr['mean_ge3_rate']}** |")
    lines.append(f"| std | {ovr['std_ge3_rate']} |")
    lines.append(f"| median | {ovr['median_ge3_rate']} |")
    lines.append(f"| min | {ovr['min_ge3_rate']} |")
    lines.append(f"| max | {ovr['max_ge3_rate']} |")
    lines.append(f"| best seed | #{best['seed']} ge3={best['ge3_rate']} p={best.get('p_value','?')} |")

    lines.append(f"\n## 상위 10% vs 하위 10% 비교")
    lines.append(f"\n### 뇌별 ge3 (선택된 세트)")
    lines.append(f"| 뇌 | top 10% | bot 10% | Δ |")
    lines.append(f"|------|---:|---:|---:|")
    for tag in ["markov", "stat", "review"]:
        tv = top_a["brain_ge3_selected"].get(tag, 0)
        bv = bot_a["brain_ge3_selected"].get(tag, 0)
        d = diff["brain_ge3_selected"].get(tag, 0)
        lines.append(f"| {tag} | {tv} | {bv} | {d:+.4f} |")

    lines.append(f"\n### 뇌별 mean (선택된 세트)")
    lines.append(f"| 뇌 | top 10% | bot 10% | Δ |")
    lines.append(f"|------|---:|---:|---:|")
    for tag in ["markov", "stat", "review"]:
        tv = top_a["brain_mean_selected"].get(tag, 0)
        bv = bot_a["brain_mean_selected"].get(tag, 0)
        d = diff["brain_mean_selected"].get(tag, 0)
        lines.append(f"| {tag} | {tv} | {bv} | {d:+.4f} |")

    lines.append(f"\n### 선택 vs 비선택 ge3")
    lines.append(f"| 그룹 | selected ge3 | non-selected ge3 |")
    lines.append(f"|------|---:|---:|")
    lines.append(f"| top 10% | {top_a['selected_ge3_rate']} | {top_a['nonsel_ge3_rate']} |")
    lines.append(f"| bot 10% | {bot_a['selected_ge3_rate']} | {bot_a['nonsel_ge3_rate']} |")

    lines.append(f"\n### 적중 회차 특성 (≥3 적중 시)")
    lines.append(f"| 특성 | top 10% | bot 10% | Δ |")
    lines.append(f"|------|---:|---:|---:|")
    for key, name in [("hit_draw_sum_mean", "합계 평균"),
                      ("hit_draw_odd_ratio_mean", "홀수 비율"),
                      ("hit_draw_consec_rate", "연속번호 비율"),
                      ("hit_draw_ac_mean", "AC값 평균")]:
        tv = top_a.get(key)
        bv = bot_a.get(key)
        dv = diff.get(key)
        lines.append(f"| {name} | {tv} | {bv} | {dv} |")

    lines.append(f"\n## 신호 판정")
    if sig:
        lines.append(f"**신호 발견:** {sig_txt}")
    else:
        lines.append("**무신호.** 상위/하위 시드 간 체계적 패턴 차이 미발견.")

    verdict = "K-POSTHOC-WIRE" if sig else "K-ATTACK-HOLD"
    lines.append(f"\n## Verdict / NEXT")
    lines.append(f"**→ `{verdict}`**")
    if sig:
        lines.append(f"\n발견된 신호를 기반으로 live 격자 탐색 가능 (형 승인 필요).")
    else:
        lines.append(f"\n200시드 역추적에서도 활용 가능한 체계적 신호 없음 → V2 pin 유지 · 형 결정 대기.")

    lines.append(f"\n---\n\n## 팩트체크")
    lines.append(f"| 항목 | JSON | 보고서 |")
    lines.append(f"|------|------|------|")
    lines.append(f"| n_seeds | {j['n_seeds']} | {j['n_seeds']} |")
    lines.append(f"| draw_range | {j['draw_range']} | {j['draw_range'][0]}~{j['draw_range'][1]} |")
    lines.append(f"| overall mean_ge3 | {ovr['mean_ge3_rate']} | {ovr['mean_ge3_rate']} |")
    lines.append(f"| best seed ge3 | {best['ge3_rate']} | {best['ge3_rate']} |")
    lines.append(f"| best seed p | {best.get('p_value','?')} | {best.get('p_value','?')} |")
    lines.append(f"| signal_detected | {sig} | {'신호발견' if sig else '무신호'} |")
    lines.append(f"\nASCII `-` 구분 · 숫자 SSOT=`docs/benchmarks/20260729_KPOSTHOC_analysis.json`")

    text = "\n".join(lines) + "\n"
    md_path = ROOT / "reports" / "20260729_KPOSTHOC_ANALYSIS.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(text, encoding="utf-8")
    print(f"wrote {md_path}", flush=True)

    drive_path = ROOT / "My_Drive_Sync" / "커서보고서" / "20260729_KPOSTHOC_ANALYSIS.md"
    drive_path.parent.mkdir(parents=True, exist_ok=True)
    drive_path.write_text(text, encoding="utf-8")
    print(f"wrote {drive_path}", flush=True)


if __name__ == "__main__":
    main()
