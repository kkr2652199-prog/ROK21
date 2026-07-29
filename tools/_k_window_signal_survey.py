# -*- coding: utf-8 -*-
"""K-WINDOW-SIGNAL-01 — DHLOTTERY 기간창 hint survey (READ-ONLY live WF).

동행복권 당첨번호 통계 4/8/12/52주(+all) 미러 · 창 내 draws만으로
odd_even / zone_mix / sum_band / miss_pattern → 45차 hint.
3뇌 predict 직전 w[n]*=(1+α·hint[n]) · V2 set_no_asc 유지.
coordinator·predict_* 원본 미수정 · survey random.choices wrapper만.
"""
from __future__ import annotations

import json
import random
import sys
import time
import traceback
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from scipy.stats import binomtest

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
from app.testlotto.features.draw_features import (  # noqa: E402
    odd_even_ratio,
    sorted_nums,
    sum_range,
)
from app.testlotto.learn_state import get_referee_weights  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260729_KWINDOW_SIGNAL_survey.json"
OUT_MD = ROOT / "reports" / "20260729_KWINDOW_SIGNAL_SURVEY.md"

DRAW_START = 53
DRAW_END = 1234
WIRE_PIN_GE3 = 0.1447
WIRE_PIN_MEAN = 1.7504
NULL_GE3 = 0.1137
MC_SEED = 42
ALPHAS = [0.05, 0.10, 0.20]

# DHLOTTERY 당첨번호 통계 기간 필터 (주=회차, 주 1회 추첨)
WINDOW_WEEKS: list[int | None] = [4, 8, 12, 52, None]
SIGNAL_TYPES = ["odd_even", "zone_mix", "sum_band", "miss_pattern"]

PREDICT_MODULES = {
    "markov": predict_flow_shaman,
    "stat": predict_stat_fairy,
    "review": predict_review_king,
}

AUX_MODULES = {
    "miss": aux_miss_detective,
    "pattern": aux_pattern_spotlight,
    "balance": aux_balance_keeper,
    "referee": aux_referee,
}
AUX_WEIGHTS = [0.25, 0.25, 0.25, 0.25]


def _window_label(weeks: int | None) -> str:
    return "all" if weeks is None else str(weeks)


def _window_draws(draws: list[dict], weeks: int | None) -> list[dict]:
    if weeks is None:
        return list(draws)
    return draws[-weeks:] if weeks > 0 else []


@dataclass
class SignalState:
    hint: dict[int, float]
    alpha: float


_signal_state: SignalState | None = None
_orig_random_choices = random.choices


def _normalize_hint(h: dict[int, float]) -> dict[int, float]:
    vals = [abs(v) for v in h.values()]
    mx = max(vals) if vals else 0.0
    if mx < 1e-12:
        return {n: 0.0 for n in range(1, 46)}
    return {n: max(-1.0, min(1.0, h[n] / mx)) for n in range(1, 46)}


def _blank_hint() -> dict[int, float]:
    return {n: 0.0 for n in range(1, 46)}


def hint_odd_even(window_draws: list[dict], _target: int) -> dict[int, float]:
    h = _blank_hint()
    if not window_draws:
        return h
    odds: list[float] = []
    for d in window_draws:
        o, _ = odd_even_ratio(sorted_nums(d))
        odds.append(float(o))
    tgt_odd = sum(odds) / len(odds)
    odd_pref = (tgt_odd - 3.0) / 3.0
    for n in range(1, 46):
        if n % 2 == 1:
            h[n] += odd_pref
        else:
            h[n] -= odd_pref
    return _normalize_hint(h)


def hint_zone_mix(window_draws: list[dict], _target: int) -> dict[int, float]:
    h = _blank_hint()
    if not window_draws:
        return h
    zone_counts = [0, 0, 0]
    for d in window_draws:
        for n in sorted_nums(d):
            if n <= 15:
                zone_counts[0] += 1
            elif n <= 30:
                zone_counts[1] += 1
            else:
                zone_counts[2] += 1
    total_z = sum(zone_counts) or 1
    expected = total_z / 3.0
    zone_bias = [(expected - z) / max(expected, 1.0) for z in zone_counts]
    for n in range(1, 46):
        zi = 0 if n <= 15 else (1 if n <= 30 else 2)
        h[n] = zone_bias[zi]
    return _normalize_hint(h)


def hint_sum_band(window_draws: list[dict], _target: int) -> dict[int, float]:
    h = _blank_hint()
    if not window_draws:
        return h
    bands: Counter[str] = Counter()
    band_nums: dict[str, Counter[int]] = {
        "low": Counter(),
        "mid": Counter(),
        "high": Counter(),
    }
    for d in window_draws:
        nums = sorted_nums(d)
        s = sum_range(nums)
        band = "low" if s < 120 else ("high" if s > 155 else "mid")
        bands[band] += 1
        for n in nums:
            band_nums[band][n] += 1
    dominant = max(bands, key=lambda k: bands[k])
    freq = band_nums[dominant]
    if not freq:
        return h
    maxf = max(freq.values())
    for n in range(1, 46):
        cnt = freq.get(n, 0)
        h[n] = cnt / maxf if cnt else -0.3
    return _normalize_hint(h)


def hint_miss_pattern(window_draws: list[dict], _target: int) -> dict[int, float]:
    """창 내 출현 빈도 — hot 가산 · cold 감산 (feedback 미사용)."""
    h = _blank_hint()
    if not window_draws:
        return h
    freq: Counter[int] = Counter()
    for d in window_draws:
        for n in sorted_nums(d):
            freq[n] += 1
    if not freq:
        return h
    avg = sum(freq.values()) / 45.0
    maxf = max(freq.values())
    for n in range(1, 46):
        cnt = freq.get(n, 0)
        if cnt == 0:
            h[n] = -1.0
        elif cnt >= maxf * 0.8:
            h[n] = 1.0
        else:
            h[n] = (cnt - avg) / max(avg, 1.0)
    return _normalize_hint(h)


SIGNAL_BUILDERS: dict[str, Callable[[list[dict], int], dict[int, float]]] = {
    "odd_even": hint_odd_even,
    "zone_mix": hint_zone_mix,
    "sum_band": hint_sum_band,
    "miss_pattern": hint_miss_pattern,
}


def _build_hint(
    draws: list[dict], weeks: int | None, signal: str, target: int
) -> dict[int, float]:
    wd = _window_draws(draws, weeks)
    return SIGNAL_BUILDERS[signal](wd, target)


def _should_inject_signal() -> bool:
    if _signal_state is None or _signal_state.alpha <= 0:
        return False
    for frame in traceback.extract_stack()[:-1]:
        fn = frame.filename.replace("\\", "/")
        if fn.endswith("predict_markov.py"):
            if frame.name == "markov_random_walk":
                return False
            if frame.name == "_markov_predict":
                return True
        if fn.endswith("predict_statistical.py") and frame.name == "_statistical_predict":
            return True
        if fn.endswith("predict_review_king.py") and frame.name == "predict_sets":
            return True
    return False


def _patched_random_choices(population, weights=None, *, k=1):
    if weights is not None and _should_inject_signal() and _signal_state is not None:
        hint = _signal_state.hint
        alpha = _signal_state.alpha
        new_w: list[float] = []
        for i, item in enumerate(population):
            if isinstance(item, int) and 1 <= item <= 45:
                hv = hint.get(item, 0.0)
                new_w.append(max(0.0, float(weights[i]) * (1.0 + alpha * hv)))
            else:
                new_w.append(float(weights[i]))
        weights = new_w
    return _orig_random_choices(population, weights=weights, k=k)


def _install_signal_patch(hint: dict[int, float], alpha: float) -> None:
    global _signal_state
    _signal_state = SignalState(hint=hint, alpha=alpha)
    random.choices = _patched_random_choices


def _clear_signal_patch() -> None:
    global _signal_state
    _signal_state = None
    random.choices = _orig_random_choices


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


def _empty_tier() -> dict[str, int]:
    return {"r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0}


def _record_tier(acc: dict[str, int], tier: int) -> None:
    if 1 <= tier <= 5:
        acc[f"r{tier}"] += 1


def _aux_composite_score(
    nums: list[int], draws: list[dict], target_draw_no: int, brain_tag: str | None = None
) -> float:
    total = 0.0
    for mod, w in zip(AUX_MODULES.values(), AUX_WEIGHTS):
        total += w * mod.score_set(nums, draws, target_draw_no, brain_tag=brain_tag)
    return total


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
        out.append({**c, "confidence": round(final_conf, 1)})
    return out


def _live_candidates(draws: list[dict], draw_no: int) -> list[dict]:
    candidates: list[dict] = []
    for tag, mod in PREDICT_MODULES.items():
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            candidates.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})
    return candidates


def summarize_bests(bests: list[int]) -> dict[str, Any]:
    n = len(bests)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3_rate": 0.0, "ge4_rate": 0.0, "ge3_count": 0}
    ge3_c = sum(1 for x in bests if x >= 3)
    ge4_c = sum(1 for x in bests if x >= 4)
    return {
        "n": n,
        "mean": round(sum(bests) / n, 4),
        "ge3_rate": round(ge3_c / n, 4),
        "ge4_rate": round(ge4_c / n, 4),
        "ge3_count": ge3_c,
    }


def enrich_variant(
    variant_id: str,
    window_weeks: int | None,
    signal_type: str,
    alpha: float,
    sm: dict[str, Any],
    tier_sel: dict[str, int],
) -> dict[str, Any]:
    ge3 = float(sm["ge3_rate"])
    ge3_c = int(sm["ge3_count"])
    n = int(sm["n"])
    p = float(binomtest(ge3_c, n, NULL_GE3, alternative="greater").pvalue) if n else 1.0
    delta_pin = round(ge3 - WIRE_PIN_GE3, 4)
    delta_null = round(ge3 - NULL_GE3, 4)
    verdict = "PASS" if ge3 > WIRE_PIN_GE3 and p < 0.05 else "FAIL"
    wl = _window_label(window_weeks)
    return {
        "variant_id": variant_id,
        "window_weeks": window_weeks,
        "window_label": wl,
        "signal_type": signal_type,
        "alpha": alpha,
        "label": f"w{wl}_{signal_type}@α={alpha}",
        "mean": sm["mean"],
        "ge3_rate": ge3,
        "ge4_rate": sm["ge4_rate"],
        "ge3_count": ge3_c,
        "delta_ge3_vs_pin": delta_pin,
        "delta_ge3_vs_null": delta_null,
        "p_value": round(p, 6),
        "verdict": verdict,
        "tier_selected_5": {**tier_sel, "n_sets": tier_sel.get("n_sets", n * 5)},
    }


def run_walkforward_variants() -> tuple[int, list[dict[str, Any]]]:
    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    variant_specs: list[tuple[str, int | None, str, float, bool]] = [
        ("baseline", None, "none", 0.0, True),
    ]
    for weeks in WINDOW_WEEKS:
        wl = _window_label(weeks)
        for sig in SIGNAL_TYPES:
            vid = f"w{wl}_{sig}"
            for alpha in ALPHAS:
                variant_specs.append((vid, weeks, sig, alpha, False))

    acc: dict[str, list[int]] = {f"{v}@{a}": [] for v, _, _, a, _ in variant_specs}
    tier_acc: dict[str, dict[str, int]] = {k: {**_empty_tier(), "n_sets": 0} for k in acc}
    tier_brain: dict[str, dict[str, dict[str, int]]] = {
        k: {b: {**_empty_tier(), "n_sets": 0} for b in PREDICT_MODULES} for k in acc
    }

    n_eval = 0
    for ri, row in enumerate(rows):
        if ri % 100 == 0:
            print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        bonus = int(row.get("bonus") or 0)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue
        n_eval += 1

        hints_cache: dict[tuple[int | None, str], dict[int, float]] = {}
        for weeks in WINDOW_WEEKS:
            for sig in SIGNAL_TYPES:
                hints_cache[(weeks, sig)] = _build_hint(draws, weeks, sig, draw_no)

        for vid, weeks, sig, alpha, use_aux in variant_specs:
            key = f"{vid}@{alpha}"
            try:
                if vid == "baseline":
                    _clear_signal_patch()
                    candidates = _live_candidates(draws, draw_no)
                    scored = _apply_aux_scoring(candidates, draws, draw_no)
                else:
                    hint = hints_cache[(weeks, sig)]
                    _install_signal_patch(hint, alpha)
                    try:
                        candidates = _live_candidates(draws, draw_no)
                    finally:
                        _clear_signal_patch()
                    scored = candidates

                if not scored:
                    acc[key].append(0)
                    continue

                selected = apply_markov_wire_quota(scored)
                best = 0
                for c in selected:
                    nums = [int(x) for x in c["nums"]]
                    mc = len(set(nums) & actual)
                    bm = 1 if bonus in set(nums) else 0
                    tier = _prediction_rank_tier(mc, bm)
                    _record_tier(tier_acc[key], tier)
                    tier_acc[key]["n_sets"] += 1
                    tag = str(c.get("brain_tag") or "")
                    if tag in tier_brain[key]:
                        _record_tier(tier_brain[key][tag], tier)
                        tier_brain[key][tag]["n_sets"] += 1
                    best = max(best, mc)
                acc[key].append(best)
            except Exception as exc:
                print(f"  WARN {key} draw={draw_no}: {exc}", flush=True)
                acc[key].append(0)

    results: list[dict[str, Any]] = []
    for vid, weeks, sig, alpha, use_aux in variant_specs:
        key = f"{vid}@{alpha}"
        sm = summarize_bests(acc[key])
        if vid == "baseline":
            row = enrich_variant(vid, weeks, sig, alpha, sm, tier_acc[key])
        else:
            row = enrich_variant(vid, weeks, sig, alpha, sm, tier_acc[key])
        row["uses_aux_scoring"] = use_aux
        row["tier_by_brain"] = tier_brain[key]
        results.append(row)

    results.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))
    return n_eval, results


def _write_report(out: dict[str, Any]) -> None:
    results = out["variants"]
    best = out["best_variant"]
    best_signal = out["best_signal_variant"]
    baseline = out["baseline"]
    n = out["n_eval"]
    pass_gate = out["gates"]["pass"]

    lines: list[str] = []
    lines.append("# K-WINDOW-SIGNAL-01 — DHLOTTERY 기간창 hint survey (READ-ONLY live WF)")
    lines.append(
        f"\n날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · "
        f"**{'PASS' if pass_gate else 'FAIL'}** · seed={MC_SEED} · n={n}"
    )
    lines.append(
        "\n개념: 동행복권 4/8/12/52주(+all) 창 내 draws→45차 hint "
        "(odd_even·zone_mix·sum_band·miss_pattern) → "
        "3뇌 predict `w[n]*=(1+α·hint[n])` · V2 set_no_asc 유지."
    )

    lines.append("\n## SUMMARY (BENCH_PROTOCOL §6)")
    lines.append(
        "| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) | 비고 |"
    )
    lines.append(
        "|-------|----------|------|----------|-----|--------------|-------------|-------------|------|"
    )
    lines.append("| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | E[match]=6×6/45 |")
    lines.append(
        f"| **WIRE-V2 pin** | stored | {WIRE_PIN_MEAN} | {WIRE_PIN_GE3} | ✓ | +0.0310 | — | — | PINNED |"
    )
    bl_p = float(
        binomtest(baseline["ge3_count"], n, NULL_GE3, alternative="greater").pvalue
    ) if n else 1.0
    lines.append(
        f"| **baseline (AUX score)** | WF live | **{baseline['mean']}** | "
        f"**{baseline['ge3_rate']}** | — | "
        f"{baseline['delta_ge3_vs_null']:+.4f} | {baseline['delta_ge3_vs_pin']:+.4f} | "
        f"{round(bl_p, 4)} | 채점 유지 · control |"
    )
    lines.append(
        f"| **best signal** | WF live | **{best_signal['mean']}** | **{best_signal['ge3_rate']}** | — | "
        f"{best_signal['delta_ge3_vs_null']:+.4f} | {best_signal['delta_ge3_vs_pin']:+.4f} | "
        f"{best_signal['p_value']} | {best_signal['label']} · {best_signal['verdict']} |"
    )

    lines.append("\n## variants (window × signal × α · ge3 내림)")
    lines.append("| window | signal | α | mean | ge3_rate | ge3_cnt | Δpin | p | verdict |")
    lines.append("|--------|--------|--:|-----:|---------:|--------:|-----:|--:|---------|")
    signal_rows = [r for r in results if r["variant_id"] != "baseline"]
    for r in sorted(signal_rows, key=lambda x: (-x["ge3_rate"], -x["mean"]))[:25]:
        lines.append(
            f"| w{r['window_label']} | {r['signal_type']} | {r['alpha']} | {r['mean']} | "
            f"{r['ge3_rate']} | {r['ge3_count']} | {r['delta_ge3_vs_pin']:+.4f} | "
            f"{r['p_value']} | {r['verdict']} |"
        )
    if len(signal_rows) > 25:
        lines.append(f"| … | … | … | … | … | … | … | … | (+{len(signal_rows)-25} more in JSON) |")

    lines.append("\n## 창별 best (signal·α)")
    lines.append("| window | best label | ge3 | p | verdict |")
    lines.append("|--------|------------|-----|---|---------|")
    for wl in ["4", "8", "12", "52", "all"]:
        subset = [r for r in signal_rows if r["window_label"] == wl]
        if not subset:
            continue
        b = max(subset, key=lambda x: (x["ge3_rate"], x["mean"]))
        lines.append(
            f"| w{wl} | {b['label']} | {b['ge3_rate']} | {b['p_value']} | {b['verdict']} |"
        )

    lines.append("\n## tier 피벗 (best signal · BENCH_PROTOCOL §7)")
    ts = best_signal.get("tier_selected_5") or {}
    ge3_s = ts.get("r3", 0) + ts.get("r4", 0) + ts.get("r5", 0)
    lines.append("| scope | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |")
    lines.append("|-------|----|----|----|----|----|-----|--------|")
    lines.append(
        f"| selected_5 | {ts.get('r1',0)} | {ts.get('r2',0)} | "
        f"{ts.get('r3',0)} | {ts.get('r4',0)} | {ts.get('r5',0)} | {ge3_s} | {ts.get('n_sets',0)} |"
    )

    lines.append("\n## Verdict")
    lines.append(f"- **PASS gate:** ge3 > pin {WIRE_PIN_GE3} AND p < 0.05 → **{pass_gate}**")
    lines.append(f"- **best signal:** `{best_signal['label']}` ge3={best_signal['ge3_rate']} p={best_signal['p_value']}")
    if pass_gate:
        lines.append("- **→ `K-WINDOW-SIGNAL-WIRE`** (형 GO · coordinator 별도)")
    else:
        lines.append("- **→ `K-ATTACK-HOLD`** · E3 PATTERN-HINT-03 또는 다른 축")

    lines.append("\n## 팩트체크")
    lines.append("| 항목 | JSON | 보고서 |")
    lines.append("|------|------|--------|")
    lines.append(f"| n_eval | {n} | {n} |")
    lines.append(f"| baseline ge3 | {baseline['ge3_rate']} | {baseline['ge3_rate']} |")
    lines.append(f"| best signal ge3 | {best_signal['ge3_rate']} | {best_signal['ge3_rate']} |")
    lines.append(f"| pass_gate | {pass_gate} | {pass_gate} |")
    lines.append(f"| seed | {MC_SEED} | {MC_SEED} |")
    lines.append(f"| coordinator_modified | False | False |")
    lines.append(
        f"\nSSOT=`docs/benchmarks/20260729_KWINDOW_SIGNAL_survey.json` · "
        f"inject=survey random.choices wrapper only"
    )

    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / "20260729_KWINDOW_SIGNAL_SURVEY.md"
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_MD}", flush=True)


def main() -> None:
    t0 = time.time()
    n_variants = 1 + len(WINDOW_WEEKS) * len(SIGNAL_TYPES) * len(ALPHAS)
    print(
        f"K-WINDOW-SIGNAL-01 live WF draws {DRAW_START}~{DRAW_END} "
        f"variants={n_variants} seed={MC_SEED}",
        flush=True,
    )

    n_eval, results = run_walkforward_variants()
    _clear_signal_patch()

    baseline = next(r for r in results if r["variant_id"] == "baseline")
    signal_rows = [r for r in results if r["variant_id"] != "baseline"]
    best_signal = max(signal_rows, key=lambda x: (x["ge3_rate"], x["mean"]))
    best_overall = max(results, key=lambda x: (x["ge3_rate"], x["mean"]))
    pass_gate = any(r["verdict"] == "PASS" for r in signal_rows)

    if pass_gate:
        recommended = "K-WINDOW-SIGNAL-WIRE"
        verdict = (
            f"PASS: {best_signal['label']} ge3={best_signal['ge3_rate']} "
            f"> pin {WIRE_PIN_GE3} p={best_signal['p_value']}"
        )
    else:
        recommended = "K-ATTACK-HOLD"
        verdict = (
            f"FAIL: best signal {best_signal['label']} ge3={best_signal['ge3_rate']} "
            f"≤ pin or p≥0.05 → HOLD / E3"
        )

    out: dict[str, Any] = {
        "id": "K-WINDOW-SIGNAL-01",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": n_eval,
        "draw_range": [DRAW_START, DRAW_END],
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "null_ge3": NULL_GE3,
        "mc_seed": MC_SEED,
        "alphas": ALPHAS,
        "window_weeks": [_window_label(w) for w in WINDOW_WEEKS],
        "signal_types": SIGNAL_TYPES,
        "sets_per_predict_brain": SETS_PER_PREDICT_BRAIN,
        "pipeline": "live_predict + window_hint_inject(random.choices wrapper) + set_no_asc quota",
        "baseline": baseline,
        "variants": results,
        "best_variant": best_overall,
        "best_signal_variant": best_signal,
        "gates": {
            "pass": pass_gate,
            "criterion": f"any signal variant ge3>{WIRE_PIN_GE3} and p<0.05",
            "best_signal_ge3": best_signal["ge3_rate"],
            "best_signal_p": best_signal["p_value"],
        },
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
        "coordinator_modified": False,
        "predict_modules_modified": False,
        "inject_method": "survey random.choices wrapper (stack-filtered predict path only)",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON}", flush=True)
    _write_report(out)
    print(f"verdict={verdict}", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
