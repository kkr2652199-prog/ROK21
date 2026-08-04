# -*- coding: utf-8 -*-
"""K-EMA-MARKOV-DIAG — L2 EMA 다중 반감기 진단 (wire 없음 · READ-ONLY).

Usage:
  python tools/_k_ema_markov_diag.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KEMA_MARKOV_DIAG.json"
OUT_MD = ROOT / "reports" / "20260805_KEMA_MARKOV_DIAG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

HALVES = (8, 26, 78)
INIT = 6.0 / 45.0  # 0.1333...
TOP_N = 15
RANDOM_HIT = TOP_N / 45.0 * 6.0  # 2.0
WARM = 79  # first eval draw after H=78 warm


def pct(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    i = int(round(q * (len(s) - 1)))
    return round(s[max(0, min(len(s) - 1, i))], 6)


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
        out.append({"draw_no": int(d["draw_no"]), "nums": nums, "set": set(nums)})
    return out


def compute_ema_series(draws: list[dict]) -> dict[int, list[dict[int, float]]]:
    """Return {H: [state_after_draw_0, ...]} length = n_draws.
    state_after_draw_i = EMA after observing draws[i].
    For predict draw t (1-index draw_no), use state after draws with draw_no < t.
    """
    series: dict[int, list[dict[int, float]]] = {}
    for H in HALVES:
        alpha = 2.0 / (H + 1.0)
        ema = {n: INIT for n in range(1, 46)}
        hist: list[dict[int, float]] = []
        for d in draws:
            # update with this draw
            s = d["set"]
            for n in range(1, 46):
                ind = 1.0 if n in s else 0.0
                ema[n] = alpha * ind + (1.0 - alpha) * ema[n]
            hist.append(dict(ema))
        series[H] = hist
    return series


def state_before(series_h: list[dict[int, float]], idx: int) -> dict[int, float]:
    """EMA state immediately before draws[idx] (after previous draw)."""
    if idx <= 0:
        return {n: INIT for n in range(1, 46)}
    return series_h[idx - 1]


def top_k(ema: dict[int, float], k: int = TOP_N) -> list[int]:
    return [n for n, _ in sorted(ema.items(), key=lambda x: (-x[1], x[0]))[:k]]


def rank_list(ema: dict[int, float]) -> list[dict[str, Any]]:
    ordered = sorted(ema.items(), key=lambda x: (-x[1], x[0]))
    return [
        {"num": n, "ema_val": round(v, 8), "rank": i + 1}
        for i, (n, v) in enumerate(ordered)
    ]


def top_bottom(ema: dict[int, float], k: int = 5) -> dict[str, list[dict[str, Any]]]:
    ordered = sorted(ema.items(), key=lambda x: (-x[1], x[0]))
    top = [{"num": n, "ema": round(v, 8)} for n, v in ordered[:k]]
    bot = [{"num": n, "ema": round(v, 8)} for n, v in ordered[-k:]]
    return {"top5": top, "bottom5": bot}


def signal_test(
    draws: list[dict], series: dict[int, list[dict[int, float]]], H: int
) -> dict[str, Any]:
    hits: list[int] = []
    # idx for draw_no >= WARM
    for idx, d in enumerate(draws):
        if d["draw_no"] < WARM:
            continue
        ema = state_before(series[H], idx)
        tops = set(top_k(ema, TOP_N))
        hc = sum(1 for n in d["nums"] if n in tops)
        hits.append(hc)
    arr = np.array(hits, dtype=float)
    m = float(arr.mean()) if len(arr) else 0.0
    # one-sample t-test vs RANDOM_HIT
    if len(arr) >= 2:
        t_res = stats.ttest_1samp(arr, RANDOM_HIT, alternative="greater")
        p = float(t_res.pvalue)
    else:
        p = 1.0
    delta = m - RANDOM_HIT
    verdict = "SIGNAL" if (delta > 0 and p < 0.05) else "NOISE"
    return {
        "n": len(hits),
        "mean_hit": round(m, 6),
        "std_hit": round(float(arr.std(ddof=1)), 6) if len(arr) > 1 else 0.0,
        "vs_random_delta": round(delta, 6),
        "p_value": round(p, 8),
        "hit_ge3_rate": round(sum(1 for h in hits if h >= 3) / len(hits), 6) if hits else 0.0,
        "verdict": verdict,
        "random_expect": RANDOM_HIT,
    }


def divergence_analysis(
    draws: list[dict], series: dict[int, list[dict[int, float]]]
) -> dict[str, Any]:
    scores: list[float] = []
    # for each draw t (need before-state for EMA at end of t-1... use after t for score of winning nums)
    # divergence of winning nums using EMA state AFTER draw t (includes t) or BEFORE?
    # Concept: at time t after observing, short vs long. Use state after draw t.
    for idx, d in enumerate(draws):
        e8 = series[8][idx]
        e78 = series[78][idx]
        divs = [e8[n] - e78[n] for n in d["nums"]]
        scores.append(mean(divs))

    # contrast: median-split (절대 0 분할은 당첨세트 평균이 거의 항상 +라 붕괴)
    med = float(np.median(scores)) if scores else 0.0
    hi_next: list[int] = []
    lo_next: list[int] = []
    for idx in range(len(draws) - 1):
        if draws[idx + 1]["draw_no"] < WARM:
            continue
        sc = scores[idx]
        ema8_after = series[8][idx]  # = state before next
        tops = set(top_k(ema8_after, TOP_N))
        nxt_hit = sum(1 for n in draws[idx + 1]["nums"] if n in tops)
        ge3 = 1 if nxt_hit >= 3 else 0
        if sc > med:
            hi_next.append(ge3)
        else:
            lo_next.append(ge3)

    hi_rate = mean(hi_next) if hi_next else 0.0
    lo_rate = mean(lo_next) if lo_next else 0.0
    delta = hi_rate - lo_rate
    usable = len(hi_next) >= 30 and len(lo_next) >= 30
    div_verdict = "SIGNAL" if (usable and delta > 0.01) else "NOISE"
    return {
        "dist": {
            "mean": round(mean(scores), 6),
            "std": round(pstdev(scores), 6) if len(scores) > 1 else 0.0,
            "p10": pct(scores, 0.10),
            "p90": pct(scores, 0.90),
            "median": round(med, 6),
            "n": len(scores),
        },
        "contrast": {
            "definition": (
                "div_score(t)>median vs ≤median → next draw hit≥3 into EMA8 top15 "
                "(절대0 분할 폐기: 당첨세트 평균 divergence가 거의 항상 +)"
            ),
            "n_pos": len(hi_next),
            "n_neg": len(lo_next),
            "div_pos_ge3_rate": round(hi_rate, 6),
            "div_neg_ge3_rate": round(lo_rate, 6),
            "delta": round(delta, 6),
            "usable_groups": usable,
        },
        "verdict": div_verdict,
    }


def write_md(p: dict[str, Any]) -> str:
    lines = [
        "# K-EMA-MARKOV-DIAG — L2 EMA 다중 반감기 진단 (2026-08-05)",
        "",
        f"- **판정:** `{p['verdict']}` · wire=`{p['wire']}` · draws 1~1235",
        f"- H={p['halflife']} · α=2/(H+1) · init=6/45 · warm from draw {WARM}",
        "",
        "## 1235 스냅샷 top5/bottom5",
        "",
    ]
    for hk, block in p["ema_snapshot_1235"].items():
        lines.append(f"### {hk}")
        lines.append(f"- top5: `{block['top5']}`")
        lines.append(f"- bottom5: `{block['bottom5']}`")
        lines.append("")
    lines += ["## signal_test (top15 → next-draw hits · expect 2.0)", ""]
    lines += [
        "| H | mean_hit | Δ vs rand | p | ge3_rate | verdict |",
        "|---|----------|-----------|---|----------|---------|",
    ]
    for H in ("H8", "H26", "H78"):
        s = p["signal_test"][H]
        lines.append(
            f"| {H} | {s['mean_hit']} | {s['vs_random_delta']:+.4f} | {s['p_value']} | "
            f"{s['hit_ge3_rate']} | **{s['verdict']}** |"
        )
    lines += [
        "",
        "## divergence",
        "",
        f"```json\n{json.dumps(p['divergence'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## ensemble_top15 @1235",
        "",
        f"`{p['ensemble_top15_1235']}`",
        "",
        "## implication",
        "",
        f"```json\n{json.dumps(p['implication'], ensure_ascii=False, indent=2)}\n```",
        "",
        f"- tool: `tools/_k_ema_markov_diag.py`",
        f"- JSON: `docs/benchmarks/{OUT_JSON.name}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    draws = load_draws()
    assert len(draws) == 1235
    series = compute_ema_series(draws)
    last_idx = len(draws) - 1

    snap = {
        "H8": top_bottom(series[8][last_idx]),
        "H26": top_bottom(series[26][last_idx]),
        "H78": top_bottom(series[78][last_idx]),
    }

    sig = {
        "H8": signal_test(draws, series, 8),
        "H26": signal_test(draws, series, 26),
        "H78": signal_test(draws, series, 78),
    }
    any_signal = any(sig[k]["verdict"] == "SIGNAL" for k in sig)

    div = divergence_analysis(draws, series)

    e8 = series[8][last_idx]
    e26 = series[26][last_idx]
    e78 = series[78][last_idx]
    ensemble = {
        n: 0.5 * e8[n] + 0.3 * e26[n] + 0.2 * e78[n] for n in range(1, 46)
    }
    ens_rank = rank_list(ensemble)
    ens_top15 = [
        {"num": r["num"], "score": round(ensemble[r["num"]], 8), "rank": r["rank"]}
        for r in ens_rank[:15]
    ]

    if any_signal:
        overall = "SIGNAL"
        viable = True
        nxt = "markov pool 재점수 wire GO 후보 · 형 승인 후만"
    else:
        overall = "NOISE"
        viable = False
        nxt = "L2 EMA 예측력 약함 · 다른 방향 탐색 또는 설계 재검토"

    if div["verdict"] == "SIGNAL":
        nxt += " · divergence 필터 설계 병행 가능"

    payload = {
        "id": "K-EMA-MARKOV-DIAG",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": overall,
        "wire": False,
        "draw_range": [1, 1235],
        "halflife": list(HALVES),
        "alpha": {str(H): round(2.0 / (H + 1.0), 6) for H in HALVES},
        "init_ema": INIT,
        "warm_start_draw": WARM,
        "ema_snapshot_1235": snap,
        "signal_test": sig,
        "divergence": div,
        "ensemble_top15_1235": ens_top15,
        "ema8_rank_1235": rank_list(e8),
        "ema26_rank_1235": rank_list(e26),
        "ema78_rank_1235": rank_list(e78),
        "implication": {
            "markov_pool_rescore_viable": viable,
            "recommended_next": nxt,
        },
        "forbid": [
            "random.choices",
            "_get_draws_before mutate",
            "engine.py",
            "auto-tune",
            "wire",
            "DB INSERT/UPDATE",
        ],
        "pass": True,
        "tool": "tools/_k_ema_markov_diag.py",
        "prior": [
            "docs/benchmarks/20260805_KSIGNAL_TAXONOMY_V1.json",
            "docs/benchmarks/20260805_KREVIEW_QUOTA_SIM.json",
        ],
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
                "verdict": overall,
                "signal": {k: {"mean": v["mean_hit"], "d": v["vs_random_delta"], "p": v["p_value"], "v": v["verdict"]} for k, v in sig.items()},
                "div": div["contrast"],
                "div_verdict": div["verdict"],
                "viable": viable,
                "ens_top15": [x["num"] for x in ens_top15],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
