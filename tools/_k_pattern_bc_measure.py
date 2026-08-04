# -*- coding: utf-8 -*-
"""K-PATTERN-BC-MEASURE — B 구조전환 사이클 · C PMI 클러스터 실측 (wire 없음).

READ-ONLY: lotto_draws SELECT only. engine/coordinator/signal_pool 미수정.
Usage:
  python tools/_k_pattern_bc_measure.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KPATTERN_BC_MEASURE.json"
OUT_MD = ROOT / "reports" / "20260805_KPATTERN_BC_MEASURE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

# Fixed from KSIGNAL_TAXONOMY_V1 (지시서) — 재계산 없음
TOP20 = [
    (11, 21),
    (1, 28),
    (10, 31),
    (6, 38),
    (33, 40),
    (25, 36),
    (6, 28),
    (12, 24),
    (34, 42),
    (10, 22),
    (19, 21),
    (5, 11),
    (8, 39),
    (3, 24),
    (2, 25),
    (3, 22),
    (37, 40),
    (5, 20),
    (14, 15),
    (3, 20),
]
BOTTOM10 = [
    (8, 12),
    (24, 43),
    (8, 26),
    (6, 33),
    (11, 40),
    (11, 34),
    (26, 32),
    (3, 25),
    (4, 30),
    (37, 44),
]


def pct(xs: list[float] | list[int], q: float) -> float:
    if not xs:
        return 0.0
    s = sorted(float(x) for x in xs)
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


def zone_label(nums: list[int]) -> str:
    has_low = any(1 <= n <= 15 for n in nums)
    has_mid = any(16 <= n <= 30 for n in nums)
    has_high = any(31 <= n <= 45 for n in nums)
    n_zones = int(has_low) + int(has_mid) + int(has_high)
    if n_zones >= 2:
        return "mix"
    if has_low:
        return "low"
    if has_mid:
        return "mid"
    return "high"


def sum_tier(s: int) -> str:
    if s < 116:
        return "low"
    if s > 160:
        return "high"
    return "mid"


def runs(series: list[Any]) -> list[int]:
    if not series:
        return []
    out: list[int] = []
    cur = series[0]
    length = 1
    for v in series[1:]:
        if v == cur:
            length += 1
        else:
            out.append(length)
            cur = v
            length = 1
    out.append(length)
    return out


def run_hist(run_lens: list[int]) -> dict[str, int]:
    h = {"1": 0, "2": 0, "3": 0, "4": 0, "5plus": 0}
    for L in run_lens:
        if L <= 0:
            continue
        if L >= 5:
            h["5plus"] += 1
        else:
            h[str(L)] += 1
    return h


def summarize_runs(run_lens: list[int]) -> dict[str, Any]:
    if not run_lens:
        return {
            "run_summary": {"mean": 0, "median": 0, "p90": 0, "max": 0},
            "run_hist": run_hist([]),
            "transition_threshold_p90": 0,
        }
    p90 = pct(run_lens, 0.90)
    # threshold = p90 of completed run lengths (= 전환 직전 N의 p90)
    return {
        "run_summary": {
            "mean": round(mean(run_lens), 6),
            "median": round(median(run_lens), 6),
            "p90": p90,
            "max": int(max(run_lens)),
        },
        "run_hist": run_hist(run_lens),
        "transition_threshold_p90": int(round(p90)) if p90 == int(p90) else p90,
    }


def current_run_len(series: list[Any]) -> int:
    if not series:
        return 0
    last = series[-1]
    n = 0
    for v in reversed(series):
        if v == last:
            n += 1
        else:
            break
    return n


def measure_b(draws: list[dict]) -> dict[str, Any]:
    odd_series = [sum(1 for x in d["nums"] if x % 2) for d in draws]
    zone_series = [zone_label(d["nums"]) for d in draws]
    sum_series = [sum_tier(sum(d["nums"])) for d in draws]

    def pack(series: list[Any]) -> dict[str, Any]:
        rl = runs(series)
        base = summarize_runs(rl)
        thr = base["transition_threshold_p90"]
        cur = current_run_len(series)
        # thr may be float — compare numerically
        thr_f = float(thr)
        imminent = cur >= thr_f if thr_f > 0 else False
        return {
            **base,
            "current_run_1235": cur,
            "transition_imminent": bool(imminent),
        }

    odd_k = pack(odd_series)
    zone = pack(zone_series)
    sum_t = pack(sum_series)
    return {
        "id": "B_structure_transition",
        "odd_k": odd_k,
        "zone": zone,
        "sum_tier": sum_t,
        "success_check": {
            "B_has_run_dist": True,
            "B_has_threshold": True,
            "B_has_current": True,
        },
        "_meta": {
            "labels_at_1235": {
                "odd_k": odd_series[-1],
                "zone": zone_series[-1],
                "sum_tier": sum_series[-1],
            }
        },
    }


def cluster_count(nums_set: set[int], pairs: list[tuple[int, int]]) -> int:
    return sum(1 for a, b in pairs if a in nums_set and b in nums_set)


def cluster_hist(counts: list[int]) -> dict[str, int]:
    h = {"0": 0, "1": 0, "2": 0, "3plus": 0}
    for c in counts:
        if c <= 0:
            h["0"] += 1
        elif c == 1:
            h["1"] += 1
        elif c == 2:
            h["2"] += 1
        else:
            h["3plus"] += 1
    return h


def next_rates(groups_next: list[int]) -> dict[str, float]:
    n = len(groups_next)
    if n == 0:
        return {"0": 0.0, "1": 0.0, "ge2": 0.0}
    z = sum(1 for x in groups_next if x == 0) / n
    o = sum(1 for x in groups_next if x == 1) / n
    g = sum(1 for x in groups_next if x >= 2) / n
    return {"0": round(z, 6), "1": round(o, 6), "ge2": round(g, 6)}


def measure_c(draws: list[dict]) -> dict[str, Any]:
    top_counts = [cluster_count(d["set"], TOP20) for d in draws]
    bot_counts = [cluster_count(d["set"], BOTTOM10) for d in draws]

    after_high: list[int] = []
    after_low: list[int] = []
    for i in range(len(top_counts) - 1):
        nxt = top_counts[i + 1]
        if top_counts[i] >= 2:
            after_high.append(nxt)
        elif top_counts[i] == 0:
            after_low.append(nxt)

    n = len(top_counts)
    top_hist = cluster_hist(top_counts)
    bot_hist = cluster_hist(bot_counts)
    return {
        "id": "C_pmi_cluster",
        "top20_pairs_used": len(TOP20),
        "top20_pairs": [{"a": a, "b": b} for a, b in TOP20],
        "cluster_dist": {
            "hist": top_hist,
            "mean": round(mean(top_counts), 6) if top_counts else 0.0,
            "median": round(median(top_counts), 6) if top_counts else 0.0,
            "p90": pct(top_counts, 0.90),
            "frac_ge2": round(sum(1 for c in top_counts if c >= 2) / n, 6) if n else 0.0,
            "frac_zero": round(sum(1 for c in top_counts if c == 0) / n, 6) if n else 0.0,
        },
        "transition": {
            "after_high_ge2_next": next_rates(after_high),
            "after_low_0_next": next_rates(after_low),
            "n_after_high": len(after_high),
            "n_after_low": len(after_low),
        },
        "bottom10_contrast": {
            "bottom10_pairs": [{"a": a, "b": b} for a, b in BOTTOM10],
            "hist": bot_hist,
            "mean": round(mean(bot_counts), 6) if bot_counts else 0.0,
            "frac_ge2": round(sum(1 for c in bot_counts if c >= 2) / n, 6) if n else 0.0,
            "note": "top20 vs bottom10 · PMI 가설 교차검증",
        },
        "success_check": {
            "C_has_cluster_dist": True,
            "C_has_transition": True,
            "C_has_bottom_contrast": True,
        },
        "_meta": {"cluster_at_1235": top_counts[-1] if top_counts else None},
    }


def signal_b(b: dict[str, Any]) -> str:
    """런 구조·임박 신호 수로 약/중/강 (진단용 · 예측 클레임 아님)."""
    labels = [b["odd_k"], b["zone"], b["sum_tier"]]
    imminent_n = sum(1 for x in labels if x["transition_imminent"])
    max_run = max(x["run_summary"]["max"] for x in labels)
    mean_run = mean(x["run_summary"]["mean"] for x in labels)
    # geometric baseline ~ short runs; long max / multiple imminent → stronger structure
    if imminent_n >= 2 and max_run >= 6:
        return "STRONG"
    if imminent_n >= 1 or max_run >= 5 or mean_run >= 2.2:
        return "MODERATE"
    return "WEAK"


def signal_c(c: dict[str, Any]) -> str:
    top_m = c["cluster_dist"]["mean"]
    bot_m = c["bottom10_contrast"]["mean"]
    top_g = c["cluster_dist"]["frac_ge2"]
    bot_g = c["bottom10_contrast"]["frac_ge2"]
    ratio = (top_m / bot_m) if bot_m > 0 else float("inf")
    # PMI 가설: top mean / frac_ge2 > bottom
    if ratio >= 1.5 and top_g > bot_g * 1.3:
        return "STRONG"
    if ratio >= 1.15 and top_g > bot_g:
        return "MODERATE"
    return "WEAK"


def write_md(payload: dict[str, Any]) -> str:
    b = payload["B"]
    c = payload["C"]
    sm = payload["summary"]
    lines = [
        "# K-PATTERN-BC-MEASURE — B·C 패턴 실측 (2026-08-05)",
        "",
        f"- **판정:** `{payload['verdict']}` · wire=`{payload['wire']}` · n={payload['n_draws']}",
        f"- **범위:** draw {payload['draw_range'][0]}~{payload['draw_range'][1]}",
        "- **금지:** 발권 ge3 클레임 · engine wire · 당첨P↑ 주장",
        "",
        "## 요약",
        "",
        f"| 축 | 신호(진단) |",
        f"|----|------------|",
        f"| B 구조전환 | **{sm['B_signal']}** |",
        f"| C PMI클러스터 | **{sm['C_signal']}** |",
        f"| C top/bottom mean비 | **{sm.get('C_top_vs_bottom_mean_ratio', '미확인')}** |",
        "",
        f"> {sm['note']}",
        "",
        "## B — 구조 전환 사이클",
        "",
        "> **zone 주의:** 정의상 2구역 이상 포함=mix. 6번호 당첨은 거의 항상 mix → "
        "런 mean/max가 비정상적으로 큼. odd_k·sum_tier가 전환 신호의 주 축.",
        "",
        "| 레이블 | run mean | median | p90 | max | thr(p90) | current@1235 | 임박 |",
        "|--------|----------|--------|-----|-----|----------|--------------|------|",
    ]
    for key, title in (("odd_k", "odd_k"), ("zone", "zone"), ("sum_tier", "sum_tier")):
        x = b[key]
        rs = x["run_summary"]
        lines.append(
            f"| {title} | {rs['mean']} | {rs['median']} | {rs['p90']} | {rs['max']} | "
            f"{x['transition_threshold_p90']} | {x['current_run_1235']} | "
            f"{'임박' if x['transition_imminent'] else '미임박'} |"
        )
    lines += [
        "",
        f"- 1235 레이블: `{b.get('_meta', {}).get('labels_at_1235')}`",
        f"- success: `{b['success_check']}`",
        "",
        "### 런 hist",
        "",
    ]
    for key in ("odd_k", "zone", "sum_tier"):
        lines.append(f"- **{key}:** `{b[key]['run_hist']}`")
    lines += [
        "",
        "## C — PMI 클러스터",
        "",
        f"- top20 pairs used: {c['top20_pairs_used']}",
        f"- cluster mean/median/p90: "
        f"{c['cluster_dist']['mean']} / {c['cluster_dist']['median']} / {c['cluster_dist']['p90']}",
        f"- frac_ge2={c['cluster_dist']['frac_ge2']} · frac_zero={c['cluster_dist']['frac_zero']}",
        f"- hist: `{c['cluster_dist']['hist']}`",
        "",
        "### 전이 (예측 클레임 금지)",
        "",
        f"- after_high(n={c['transition']['n_after_high']}): `{c['transition']['after_high_ge2_next']}`",
        f"- after_low(n={c['transition']['n_after_low']}): `{c['transition']['after_low_0_next']}`",
        "",
        "### bottom10 대조",
        "",
        f"- mean={c['bottom10_contrast']['mean']} · frac_ge2={c['bottom10_contrast']['frac_ge2']}",
        f"- hist: `{c['bottom10_contrast']['hist']}`",
        f"- note: {c['bottom10_contrast']['note']}",
        f"- success: `{c['success_check']}`",
        "",
        "## 산출물",
        "",
        f"- JSON: `docs/benchmarks/{OUT_JSON.name}`",
        f"- tool: `tools/_k_pattern_bc_measure.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    draws = load_draws()
    if len(draws) != 1235:
        print(f"WARN: expected 1235 draws, got {len(draws)}", file=sys.stderr)

    b = measure_b(draws)
    c = measure_c(draws)
    # strip private meta from success surface but keep in JSON under _meta for MD
    payload = {
        "id": "K-PATTERN-BC-MEASURE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "MEASURED",
        "wire": False,
        "draw_range": [1, 1235],
        "n_draws": len(draws),
        "B": b,
        "C": c,
        "summary": {
            "B_signal": signal_b(b),
            "C_signal": signal_c(c),
            "note": (
                "당첨회차 내부 진단 · 발권 ge3 클레임 금지 · "
                "zone은 6번호가 저/중/고 2구역 이상이면 mix → 대부분 mix라 런이 매우 김"
            ),
            "C_top_vs_bottom_mean_ratio": round(
                (c["cluster_dist"]["mean"] / c["bottom10_contrast"]["mean"])
                if c["bottom10_contrast"]["mean"] > 0
                else 0.0,
                6,
            ),
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
        "tool": "tools/_k_pattern_bc_measure.py",
        "prior": [
            "docs/benchmarks/20260805_KPATTERN_OWN_V1.json",
            "docs/benchmarks/20260805_KSIGNAL_TAXONOMY_V1.json",
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
                "n": len(draws),
                "B_signal": payload["summary"]["B_signal"],
                "C_signal": payload["summary"]["C_signal"],
                "odd_k": b["odd_k"]["current_run_1235"],
                "zone": b["zone"]["current_run_1235"],
                "sum_tier": b["sum_tier"]["current_run_1235"],
                "cluster_mean": c["cluster_dist"]["mean"],
                "bottom_mean": c["bottom10_contrast"]["mean"],
                "json": str(OUT_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
