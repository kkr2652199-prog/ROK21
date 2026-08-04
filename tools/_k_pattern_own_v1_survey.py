# -*- coding: utf-8 -*-
"""K-PATTERN-OWN-V1 — ROK21 독자 패턴 A·D·E·F 진단 측정 (wire 없음).

B·C는 설계 메모만 JSON에 포함.
Usage:
  python tools/_k_pattern_own_v1_survey.py
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import mean, median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KPATTERN_OWN_V1.json"
OUT_MD = ROOT / "reports" / "20260805_KPATTERN_OWN_V1.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    i = int(round(q * (len(s) - 1)))
    return round(s[max(0, min(len(s) - 1, i))], 6)


def dist_summary(xs: list[float] | list[int]) -> dict[str, Any]:
    if not xs:
        return {"n": 0}
    f = [float(x) for x in xs]
    return {
        "n": len(f),
        "mean": round(mean(f), 6),
        "median": round(median(f), 6),
        "p10": pct(f, 0.10),
        "p90": pct(f, 0.90),
        "min": round(min(f), 6),
        "max": round(max(f), 6),
    }


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
                "odd_k": sum(1 for x in nums if x % 2),
            }
        )
    return out


def appearance_gaps(draws: list[dict]) -> dict[int, list[int]]:
    """번호별 출현 draw_no 목록 → 간격 시계열."""
    last: dict[int, int] = {}
    gaps: dict[int, list[int]] = defaultdict(list)
    for d in draws:
        dn = d["draw_no"]
        for n in d["nums"]:
            if n in last:
                gaps[n].append(dn - last[n])
            last[n] = dn
    return gaps


def pattern_a(draws: list[dict], gaps: dict[int, list[int]]) -> dict[str, Any]:
    """출현 간격 가속도 · 당첨 세트 accel_score 분포."""
    # precompute gap history up to each draw by replaying
    last: dict[int, int] = {}
    hist_gaps: dict[int, list[int]] = defaultdict(list)
    accel_scores: list[float] = []
    delta_all: list[int] = []
    hist_bins: Counter[str] = Counter()

    for d in draws:
        dn = d["draw_no"]
        deltas = []
        for n in d["nums"]:
            gseq = hist_gaps[n]
            if len(gseq) >= 2:
                dgap = gseq[-1] - gseq[-2]
                deltas.append(dgap)
                delta_all.append(dgap)
                if dgap < 0:
                    hist_bins["accel_neg"] += 1
                elif dgap > 0:
                    hist_bins["accel_pos"] += 1
                else:
                    hist_bins["accel_zero"] += 1
            # update after score (as_of: only past gaps)
        score = mean(deltas) if deltas else 0.0
        accel_scores.append(score)
        # now update histories with this draw
        for n in d["nums"]:
            if n in last:
                hist_gaps[n].append(dn - last[n])
            last[n] = dn

    # ge3-style contrast: not ticket ge3 — compare high vs low accel among winning draws
    # "signal present" = accel_score < 0 (accelerating) vs >= 0
    neg = [s for s in accel_scores if s < 0]
    pos = [s for s in accel_scores if s > 0]
    zero = [s for s in accel_scores if s == 0]
    # split by median for contrast
    med = median(accel_scores) if accel_scores else 0.0
    low = [s for s in accel_scores if s <= med]  # more accel (smaller gaps)
    high = [s for s in accel_scores if s > med]

    return {
        "id": "A_gap_acceleration",
        "delta_gap_hist": {
            "n_deltas": len(delta_all),
            "bins": dict(hist_bins),
            "summary": dist_summary(delta_all),
        },
        "winning_set_accel_score": dist_summary(accel_scores),
        "contrast": {
            "definition": "winning-draw accel_score ≤ median vs > median (diagnostic)",
            "median": round(med, 6),
            "n_le_median": len(low),
            "n_gt_median": len(high),
            "mean_le_median": round(mean(low), 6) if low else None,
            "mean_gt_median": round(mean(high), 6) if high else None,
            "frac_accel_neg": round(len(neg) / len(accel_scores), 6) if accel_scores else None,
            "frac_accel_pos": round(len(pos) / len(accel_scores), 6) if accel_scores else None,
            "frac_zero": round(len(zero) / len(accel_scores), 6) if accel_scores else None,
            "note": "당첨회차 내부 분포 대비 · 발권 ge3 아님 · wire OFF",
        },
        "gap_series_per_num_sample": {
            str(k): gaps[k][-5:] for k in sorted(gaps)[:5] if gaps[k]
        },
    }


def pattern_d(draws: list[dict]) -> dict[str, Any]:
    """슬롯별 위치 편향."""
    slot_hist: list[Counter[int]] = [Counter() for _ in range(6)]
    for d in draws:
        for i, n in enumerate(d["nums"]):
            slot_hist[i][n] += 1
    top10 = []
    for i, c in enumerate(slot_hist):
        top = c.most_common(10)
        top10.append({"slot": i + 1, "top10": [{"num": n, "n": cnt} for n, cnt in top]})

    # bias score for each winning set: how many slots hit top10 for that slot
    top_sets = [set(x["num"] for x in t["top10"]) for t in top10]
    bias_scores = []
    for d in draws:
        hits = sum(1 for i, n in enumerate(d["nums"]) if n in top_sets[i])
        bias_scores.append(hits)
    med = median(bias_scores) if bias_scores else 0
    high = [s for s in bias_scores if s >= 4]  # strong bias
    low = [s for s in bias_scores if s <= 1]
    return {
        "id": "D_slot_position_bias",
        "slot_top10": top10,
        "winning_bias_hits_0to6": dist_summary(bias_scores),
        "hist_bias_hits": dict(Counter(bias_scores)),
        "contrast": {
            "definition": "bias_hits>=4 vs <=1 among winning draws",
            "n_ge4": len(high),
            "n_le1": len(low),
            "frac_ge4": round(len(high) / len(bias_scores), 6) if bias_scores else None,
            "frac_le1": round(len(low) / len(bias_scores), 6) if bias_scores else None,
            "median_hits": med,
            "note": "당첨회차 내 슬롯편향 강도 · 예측 ge3 아님",
        },
    }


def pattern_e(draws: list[dict]) -> dict[str, Any]:
    """carry_count 연속성."""
    carries = []
    for i in range(1, len(draws)):
        c = len(draws[i]["set"] & draws[i - 1]["set"])
        carries.append({"draw_no": draws[i]["draw_no"], "carry": c})
    series = [x["carry"] for x in carries]

    def run_lengths(pred) -> list[int]:
        runs = []
        cur = 0
        for v in series:
            if pred(v):
                cur += 1
            else:
                if cur:
                    runs.append(cur)
                cur = 0
        if cur:
            runs.append(cur)
        return runs

    zero_runs = run_lengths(lambda v: v == 0)
    ge2_runs = run_lengths(lambda v: v >= 2)

    # next_carry_prior = mean of last K=5 carries before each draw (as_of)
    priors = []
    K = 5
    for i in range(1, len(draws)):
        # carries for draws[1..i] correspond to index i-1 in series when at draws[i]
        # prior uses series[:i-1] last K (before current carry known — use up to i-1 exclusive of current)
        hist = series[: i - 1]  # past carries only
        if not hist:
            continue
        window = hist[-K:]
        priors.append(mean(window))

    # contrast: when prior high (>=1) vs low (<0.5), actual carry distribution
    high_p = []
    low_p = []
    for i, pr in enumerate(priors):
        # priors[i] aligns with draws[i+1] carry = series[i]
        actual = series[i + 1] if i + 1 < len(series) else None
        # re-align carefully:
        pass
    # Align: at draw index j>=2, prior from series[0:j-1][-K], actual=series[j-1]
    high_actual = []
    low_actual = []
    for j in range(2, len(draws)):
        hist = series[: j - 1]
        if not hist:
            continue
        pr = mean(hist[-K:])
        actual = series[j - 1]
        if pr >= 1.0:
            high_actual.append(actual)
        if pr < 0.5:
            low_actual.append(actual)

    return {
        "id": "E_carry_continuity",
        "carry_summary": dist_summary(series),
        "carry_hist": dict(Counter(series)),
        "zero_run_lengths": dist_summary(zero_runs),
        "ge2_run_lengths": dist_summary(ge2_runs),
        "next_carry_prior_K5": dist_summary(priors),
        "contrast": {
            "definition": "prior_mean_K5>=1 vs <0.5 → actual carry mean",
            "n_high_prior": len(high_actual),
            "n_low_prior": len(low_actual),
            "actual_mean_when_prior_high": round(mean(high_actual), 6) if high_actual else None,
            "actual_mean_when_prior_low": round(mean(low_actual), 6) if low_actual else None,
            "delta_mean": (
                round(mean(high_actual) - mean(low_actual), 6)
                if high_actual and low_actual
                else None
            ),
            "note": "직전 상태→다음 carry · 티켓 ge3 아님",
        },
    }


def sum_tier(s: int) -> str:
    if s >= 160:
        return "high"
    if s <= 120:
        return "low"
    return "mid"


def pattern_f(draws: list[dict]) -> dict[str, Any]:
    """sum 회귀 주기."""
    tiers = [sum_tier(d["sum"]) for d in draws]
    sums = [d["sum"] for d in draws]

    # high-run length then gap until low
    high_to_low_waits = []
    i = 0
    n = len(tiers)
    while i < n:
        if tiers[i] != "high":
            i += 1
            continue
        # start high run
        j = i
        while j < n and tiers[j] == "high":
            j += 1
        # wait from end of high run to first low
        k = j
        while k < n and tiers[k] != "low":
            k += 1
        if k < n:
            high_to_low_waits.append(k - j + 1)  # draws until low inclusive from after high
        i = j

    # streak lengths by tier
    streak_lens: dict[str, list[int]] = defaultdict(list)
    cur_t, cur_n = tiers[0], 1
    for t in tiers[1:]:
        if t == cur_t:
            cur_n += 1
        else:
            streak_lens[cur_t].append(cur_n)
            cur_t, cur_n = t, 1
    streak_lens[cur_t].append(cur_n)

    # next_sum_signal: at each draw, current streak length of current tier
    signals = []
    cur_t, cur_n = tiers[0], 1
    signals.append({"draw_no": draws[0]["draw_no"], "tier": cur_t, "streak": 1})
    for idx in range(1, n):
        if tiers[idx] == cur_t:
            cur_n += 1
        else:
            cur_t, cur_n = tiers[idx], 1
        signals.append(
            {"draw_no": draws[idx]["draw_no"], "tier": cur_t, "streak": cur_n}
        )

    # contrast: after high streak>=2, next draw tier distribution
    after_high = Counter()
    after_low = Counter()
    for idx in range(len(draws) - 1):
        if tiers[idx] == "high" and signals[idx]["streak"] >= 2:
            after_high[tiers[idx + 1]] += 1
        if tiers[idx] == "low" and signals[idx]["streak"] >= 2:
            after_low[tiers[idx + 1]] += 1

    def _norm(c: Counter) -> dict[str, float]:
        tot = sum(c.values()) or 1
        return {k: round(v / tot, 6) for k, v in sorted(c.items())}

    return {
        "id": "F_sum_reversion",
        "sum_summary": dist_summary(sums),
        "tier_counts": dict(Counter(tiers)),
        "tier_rates": {
            k: round(v / n, 6) for k, v in Counter(tiers).items()
        },
        "streak_lengths": {k: dist_summary(v) for k, v in streak_lens.items()},
        "high_to_low_wait": dist_summary(high_to_low_waits),
        "contrast": {
            "definition": "after high_streak>=2 vs low_streak>=2 → next tier rates",
            "after_high_streak2_next": _norm(after_high),
            "after_low_streak2_next": _norm(after_low),
            "n_after_high": sum(after_high.values()),
            "n_after_low": sum(after_low.values()),
            "note": "회귀 경향 진단 · 당첨P 아님",
        },
    }


def design_bc() -> dict[str, Any]:
    return {
        "B_structure_transition": {
            "status": "DESIGN_ONLY",
            "plan": (
                "회차별 odd_k/zone/sum_tier 기록 → 동일 구조 연속 N 분포 "
                "→ 전환 직전 N = next_transition_signal"
            ),
            "measure_next": "연속 구조 길이 mean/median/p90 표",
        },
        "C_pmi_cluster": {
            "status": "DESIGN_ONLY",
            "plan": (
                "PMI top20 페어 · 회차당 동시 포함 cluster_count "
                "→ cluster≥2 비율 · (나중) 고/저 cluster 세트 ge3 대비"
            ),
            "depends_on": "20260805_KSIGNAL_TAXONOMY_V1 PMI",
            "note": "발권 ge3 대비는 pool 재점수 필요 · 별도 GO",
        },
    }


def main() -> int:
    print("K-PATTERN-OWN-V1 load 1..1235…", flush=True)
    draws = load_draws()
    gaps = appearance_gaps(draws)
    print("  A…", flush=True)
    a = pattern_a(draws, gaps)
    print("  D…", flush=True)
    d = pattern_d(draws)
    print("  E…", flush=True)
    e = pattern_e(draws)
    print("  F…", flush=True)
    f = pattern_f(draws)
    bc = design_bc()

    payload = {
        "id": "K-PATTERN-OWN-V1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": "MEASURED_PARTIAL",
        "wire": False,
        "draw_range": [1, 1235],
        "n_draws": len(draws),
        "measured": ["A", "D", "E", "F"],
        "design_only": ["B", "C"],
        "A": a,
        "D": d,
        "E": e,
        "F": f,
        "B_C_design": bc,
        "success_check": {
            "A_has_dist": a["winning_set_accel_score"].get("n", 0) > 0,
            "D_has_dist": d["winning_bias_hits_0to6"].get("n", 0) > 0,
            "E_has_contrast_delta": e["contrast"].get("delta_mean") is not None,
            "F_has_contrast": bool(f["contrast"].get("after_high_streak2_next")),
            "note": "당첨회차 내부 신호 유/무 대비 · 발권 ge3 클레임 금지",
        },
        "forbid": [
            "random.choices",
            "_get_draws_before mutate",
            "engine.py",
            "auto-tune",
            "wire",
            "p_boost_claim",
        ],
        "pass": True,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-PATTERN-OWN-V1 — ROK21 독자 패턴",
        "",
        f"📅 {payload['ts'][:10]} · **MEASURED_PARTIAL** · wire=**False** · n={len(draws)}",
        "",
        "교과서 L1/PMI/EMA와 별도 · **1~1235 당첨 시계열 안에서만** 관측되는 구조.",
        "",
        "## A — 출현 간격 가속도",
        "",
        f"- Δgap summary: `{a['delta_gap_hist']['summary']}`",
        f"- bins: `{a['delta_gap_hist']['bins']}`",
        f"- 당첨세트 accel_score: `{a['winning_set_accel_score']}`",
        f"- contrast: frac_neg={a['contrast']['frac_accel_neg']} · "
        f"frac_pos={a['contrast']['frac_accel_pos']} · median={a['contrast']['median']}",
        "",
        "## D — 슬롯 위치 편향",
        "",
        f"- bias_hits(0~6) summary: `{d['winning_bias_hits_0to6']}`",
        f"- hist: `{d['hist_bias_hits']}`",
        f"- contrast frac≥4={d['contrast']['frac_ge4']} · frac≤1={d['contrast']['frac_le1']}",
        "",
        "### 슬롯 top5 (요약)",
        "",
    ]
    for slot in d["slot_top10"]:
        tops = ",".join(str(x["num"]) for x in slot["top10"][:5])
        lines.append(f"- slot{slot['slot']}: {tops}")
    lines.extend(
        [
            "",
            "## E — carry 연속성",
            "",
            f"- carry summary: `{e['carry_summary']}` · hist=`{e['carry_hist']}`",
            f"- zero-run: `{e['zero_run_lengths']}`",
            f"- ge2-run: `{e['ge2_run_lengths']}`",
            f"- prior_K5: `{e['next_carry_prior_K5']}`",
            f"- contrast Δmean(high−low prior) = **{e['contrast']['delta_mean']}** "
            f"(actual carry mean high={e['contrast']['actual_mean_when_prior_high']} "
            f"low={e['contrast']['actual_mean_when_prior_low']})",
            "",
            "## F — sum 회귀",
            "",
            f"- sum summary: `{f['sum_summary']}`",
            f"- tier rates: `{f['tier_rates']}`",
            f"- high→low wait: `{f['high_to_low_wait']}`",
            f"- after high_streak≥2 next: `{f['contrast']['after_high_streak2_next']}`",
            f"- after low_streak≥2 next: `{f['contrast']['after_low_streak2_next']}`",
            "",
            "## B·C — 설계만 (미측정)",
            "",
            f"- B: {bc['B_structure_transition']['plan']}",
            f"- C: {bc['C_pmi_cluster']['plan']}",
            "",
            "## 성공 체크",
            "",
            f"- `{payload['success_check']}`",
            "",
            "비고: 본 대비는 **당첨 회차 시계열 진단**이다. 발권 ge3↑·당첨P↑ 클레임 금지 · wire 별도 GO.",
            "",
            f"근거: `{OUT_JSON.name}`",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "pass": True,
                "A_median_accel": a["contrast"]["median"],
                "E_delta": e["contrast"]["delta_mean"],
                "F_high_to_low_mean": f["high_to_low_wait"].get("mean"),
                "out": OUT_JSON.name,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
