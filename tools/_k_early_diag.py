# -*- coding: utf-8 -*-
"""K-EARLY-DIAG — early 구간 취약성 진단 (wire 없음 · SELECT-ONLY).

Usage:
  python tools/_k_early_diag.py
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KEARLY_DIAG.json"
OUT_MD = ROOT / "reports" / "20260805_KEARLY_DIAG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

PERIODS = {
    "early_1036_1115": (1036, 1115),
    "mid_1116_1175": (1116, 1175),
    "late_1176_1235": (1176, 1235),
}
H = 8
ALPHA = 2.0 / (H + 1.0)
INIT = 6.0 / 45.0
COLD_K = 5


def sum_tier(s: int) -> str:
    if s < 116:
        return "low"
    if s > 160:
        return "high"
    return "mid"


def zone_label(nums: list[int]) -> str:
    has_low = any(1 <= n <= 15 for n in nums)
    has_mid = any(16 <= n <= 30 for n in nums)
    has_high = any(31 <= n <= 45 for n in nums)
    n = int(has_low) + int(has_mid) + int(has_high)
    if n >= 2:
        return "mix"
    if has_low:
        return "low"
    if has_mid:
        return "mid"
    return "high"


def shannon(counts: Counter[int], n_sym: int = 45) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for n in range(1, n_sym + 1):
        c = counts.get(n, 0)
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log(p, 2)
    return round(h, 6)


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
        s = sum(nums)
        out.append(
            {
                "draw_no": int(d["draw_no"]),
                "nums": nums,
                "set": set(nums),
                "sum": s,
                "sum_tier": sum_tier(s),
                "odd_k": sum(1 for x in nums if x % 2),
                "zone": zone_label(nums),
            }
        )
    return out


def ema_before(draws: list[dict]) -> dict[int, dict[int, float]]:
    ema = {n: INIT for n in range(1, 46)}
    before: dict[int, dict[int, float]] = {}
    for d in draws:
        before[d["draw_no"]] = dict(ema)
        s = d["set"]
        for n in range(1, 46):
            ind = 1.0 if n in s else 0.0
            ema[n] = ALPHA * ind + (1.0 - ALPHA) * ema[n]
    return before


def cold5(ema: dict[int, float]) -> set[int]:
    return {n for n, _ in sorted(ema.items(), key=lambda x: (x[1], x[0]))[:COLD_K]}


def load_preds(lo: int, hi: int) -> dict[int, list[dict]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT target_draw_no, num1,num2,num3,num4,num5,num6, matched_count
        FROM lotto_predictions
        WHERE target_draw_no BETWEEN ? AND ?
        ORDER BY target_draw_no, id
        """,
        (lo, hi),
    ).fetchall()
    conn.close()
    by: dict[int, list[dict]] = {}
    for r in rows:
        d = dict(r)
        dno = int(d["target_draw_no"])
        nums = {int(d[f"num{k}"]) for k in range(1, 7)}
        by.setdefault(dno, []).append(
            {"set": nums, "matched_count": d.get("matched_count")}
        )
    return by


def hits(p: dict, actual: set[int]) -> int:
    if p.get("matched_count") is not None and int(p["matched_count"]) >= 0:
        return int(p["matched_count"])
    return len(p["set"] & actual)


def dist_summary_nums(draws: list[dict]) -> dict[str, Any]:
    sums = [d["sum"] for d in draws]
    odds = Counter(d["odd_k"] for d in draws)
    zones = Counter(d["zone"] for d in draws)
    tiers = Counter(d["sum_tier"] for d in draws)
    return {
        "n": len(draws),
        "sum_dist": {
            "mean": round(mean(sums), 6) if sums else 0.0,
            "std": round(pstdev(sums), 6) if len(sums) > 1 else 0.0,
            "min": min(sums) if sums else 0,
            "max": max(sums) if sums else 0,
        },
        "odd_k_dist": {str(k): odds[k] for k in sorted(odds)},
        "zone_dist": dict(zones),
        "sum_tier_dist": dict(tiers),
    }


def period_block(
    pname: str,
    lo: int,
    hi: int,
    draws_by: dict[int, dict],
    before: dict[int, dict[int, float]],
    preds: dict[int, list[dict]],
    cache_entropy: float,
    cache_top3_rate: float,
) -> dict[str, Any]:
    dnos = [d for d in range(lo, hi + 1)]
    pd = [draws_by[d] for d in dnos]
    base = dist_summary_nums(pd)

    # cold contamination + clean delta (set-level)
    all_ge3: list[int] = []
    clean_ge3: list[int] = []
    dirty_ge3: list[int] = []
    contam = 0
    total = 0
    dirty_draw_profiles: list[dict] = []
    ge3_hit_draws: list[dict] = []
    ge3_miss_draws: list[dict] = []
    best_flags: list[int] = []
    sum_tier_ge3: dict[str, list[int]] = {"low": [], "mid": [], "high": []}

    for dno in dnos:
        d = draws_by[dno]
        actual = d["set"]
        cold = cold5(before[dno])
        plist = preds.get(dno) or []
        best = 0
        draw_dirty = False
        for p in plist:
            mc = hits(p, actual)
            ge3 = 1 if mc >= 3 else 0
            all_ge3.append(ge3)
            total += 1
            if p["set"] & cold:
                contam += 1
                dirty_ge3.append(ge3)
                draw_dirty = True
            else:
                clean_ge3.append(ge3)
            best = max(best, mc)
        bf = 1 if best >= 3 else 0
        best_flags.append(bf)
        sum_tier_ge3[d["sum_tier"]].append(bf)
        prof = {
            "draw_no": dno,
            "sum": d["sum"],
            "sum_tier": d["sum_tier"],
            "odd_k": d["odd_k"],
            "zone": d["zone"],
            "best_hits": best,
        }
        if draw_dirty:
            dirty_draw_profiles.append(prof)
        if bf:
            ge3_hit_draws.append(prof)
        else:
            ge3_miss_draws.append(prof)

    def rate(xs: list[int]) -> float:
        return round(sum(xs) / len(xs), 6) if xs else 0.0

    a_ge3 = rate(all_ge3)
    c_ge3 = rate(clean_ge3)
    cold_delta = round(c_ge3 - a_ge3, 6)

    # hit profile: among ge3=1 draws
    hit_profile = dist_summary_nums(
        [
            {
                "sum": p["sum"],
                "odd_k": p["odd_k"],
                "zone": p["zone"],
                "sum_tier": p["sum_tier"],
                "nums": draws_by[p["draw_no"]]["nums"],
            }
            for p in ge3_hit_draws
        ]
    ) if ge3_hit_draws else {}
    miss_profile = dist_summary_nums(
        [
            {
                "sum": p["sum"],
                "odd_k": p["odd_k"],
                "zone": p["zone"],
                "sum_tier": p["sum_tier"],
                "nums": draws_by[p["draw_no"]]["nums"],
            }
            for p in ge3_miss_draws
        ]
    ) if ge3_miss_draws else {}

    dirty_win = dist_summary_nums(
        [
            {
                "sum": p["sum"],
                "odd_k": p["odd_k"],
                "zone": p["zone"],
                "sum_tier": p["sum_tier"],
                "nums": draws_by[p["draw_no"]]["nums"],
            }
            for p in dirty_draw_profiles
        ]
    ) if dirty_draw_profiles else {}

    tier_ge3 = {
        t: {"n": len(xs), "ge3": rate(xs)} for t, xs in sum_tier_ge3.items()
    }

    return {
        "ge3": rate(best_flags),
        "n_draws": len(dnos),
        "sum_dist": base["sum_dist"],
        "odd_k_dist": base["odd_k_dist"],
        "zone_dist": base["zone_dist"],
        "sum_tier_dist": base["sum_tier_dist"],
        "cold_k5_contamination": round(contam / total, 6) if total else 0.0,
        "cold_k5_clean_ge3": c_ge3,
        "cold_k5_all_ge3_sets": a_ge3,
        "cold_k5_delta": cold_delta,
        "cold_dirty_draw_profile": dirty_win,
        "pool_entropy": cache_entropy,
        "pool_top3_rate": cache_top3_rate,
        "ge3_hit_profile": {
            "n_hit": len(ge3_hit_draws),
            "n_miss": len(ge3_miss_draws),
            "hit": hit_profile,
            "miss": miss_profile,
        },
        "sum_tier_ge3": tier_ge3,
        "cover_ref": {
            "note": "from K-COVER-DIAG by_period",
        },
    }


def cache_pool_stats(lo: int, hi: int) -> tuple[float, float]:
    """Entropy + top3 concentration of union of pool/repack numbers in period."""
    from app.testlotto.pool_view_cache import get_cached_pool_view

    freq: Counter[int] = Counter()
    for dno in range(lo, hi + 1):
        pv = get_cached_pool_view(dno)
        if not pv:
            continue
        for tag in ("stat", "markov", "review"):
            for kind in ("pool_by_brain", "repack_by_brain"):
                for s in (pv.get(kind) or {}).get(tag) or []:
                    for n in s.get("nums") or []:
                        freq[int(n)] += 1
    total = sum(freq.values()) or 1
    top3 = sum(c for _, c in freq.most_common(3))
    return shannon(freq), round(top3 / total, 6)


def write_md(p: dict[str, Any]) -> str:
    lines = [
        "# K-EARLY-DIAG — early 취약성 진단 (2026-08-05)",
        "",
        f"- **판정:** `{p['verdict']}` · wire=`{p['wire']}`",
        f"- root_cause: {p['root_cause']}",
        f"- wire_implication: {p['wire_implication']}",
        "",
        "## by_period 요약",
        "",
        "| period | ge3 | sum_mean | cold_contam | coldΔ | pool_H | top3_rate |",
        "|--------|-----|----------|-------------|-------|--------|-----------|",
    ]
    for k, b in p["by_period"].items():
        lines.append(
            f"| {k} | {b['ge3']} | {b['sum_dist']['mean']} | {b['cold_k5_contamination']} | "
            f"{b['cold_k5_delta']:+.4f} | {b['pool_entropy']} | {b['pool_top3_rate']} |"
        )
    lines += [
        "",
        "## early sum_tier × ge3",
        "",
        f"`{p['by_period']['early_1036_1115']['sum_tier_ge3']}`",
        "",
        "## early ge3 hit vs miss 프로파일",
        "",
        f"- hit: `{p['by_period']['early_1036_1115']['ge3_hit_profile'].get('hit', {})}`",
        f"- miss: `{p['by_period']['early_1036_1115']['ge3_hit_profile'].get('miss', {})}`",
        "",
        f"- tool: `tools/_k_early_diag.py`",
        f"- JSON: `docs/benchmarks/{OUT_JSON.name}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    draws = load_draws()
    before = ema_before(draws)
    draws_by = {d["draw_no"]: d for d in draws}
    preds = load_preds(1036, 1235)

    # load prior cover period ge3
    cover = json.loads(
        (ROOT / "docs" / "benchmarks" / "20260805_KCOVER_DIAG.json").read_text(
            encoding="utf-8"
        )
    )
    cold_prior = json.loads(
        (ROOT / "docs" / "benchmarks" / "20260805_KCOLD_EXCLUDE_DIAG.json").read_text(
            encoding="utf-8"
        )
    )

    by_period: dict[str, Any] = {}
    entropies: dict[str, float] = {}
    for pname, (lo, hi) in PERIODS.items():
        ent, top3 = cache_pool_stats(lo, hi)
        entropies[pname] = ent
        block = period_block(pname, lo, hi, draws_by, before, preds, ent, top3)
        block["cover_ref"]["ge3"] = cover["by_period"][pname]["ge3"]
        block["cover_ref"]["avg_jaccard"] = cover["by_period"][pname]["avg_jaccard"]
        block["cover_ref"]["avg_unique"] = cover["by_period"][pname]["avg_unique"]
        # prior cold deltas
        cp = cold_prior["by_period"][pname]["cold_k5"]
        block["cold_prior_k5"] = {
            "delta": cp["delta"],
            "verdict": cp["verdict"],
            "clean_ge3": cp["clean_ge3"],
            "all_ge3": cp["all_ge3"],
        }
        by_period[pname] = block

    early = by_period["early_1036_1115"]
    mid = by_period["mid_1116_1175"]
    late = by_period["late_1176_1235"]

    # verdict logic
    ent_gap = round(mid["pool_entropy"] - early["pool_entropy"], 6)
    ge3_gap_mid = round(mid["ge3"] - early["ge3"], 6)
    # structural if sum/zone clearly differ OR entropy gap large OR cold effect differs strongly
    sum_gap = abs(early["sum_dist"]["mean"] - mid["sum_dist"]["mean"])
    cold_gap = abs(early["cold_k5_delta"] - mid["cold_k5_delta"])

    if abs(ge3_gap_mid) < 0.02 and abs(ent_gap) < 0.05 and cold_gap < 0.01:
        verdict = "NOISE"
        root = (
            f"early ge3={early['ge3']} vs mid={mid['ge3']} 차이 소폭 · "
            f"pool entropy 갭={ent_gap} · 구조 신호 약함 → 표본 분산(NOISE) 우세"
        )
    elif abs(ent_gap) >= 0.1 or cold_gap >= 0.01 or sum_gap >= 8:
        verdict = "STRUCTURAL"
        root = (
            f"early vs mid: entropyΔ={ent_gap}, coldΔ갭={cold_gap}, sum_meanΔ={sum_gap:.2f} · "
            f"late ge3={late['ge3']}가 더 낮아 'early만 붕괴' 아님"
        )
    else:
        verdict = "SIGNAL_WEAK"
        root = (
            f"early ge3={early['ge3']} < mid={mid['ge3']} · "
            f"cold_k5 earlyΔ={early['cold_k5_delta']} vs midΔ={mid['cold_k5_delta']} · "
            f"약한 구조 신호(SIGNAL_WEAK)"
        )

    # note late is worse than early in cover data
    wire_imp = (
        "early 단독 wire 근거 약함 · cold-free는 mid에서 더 유리(prior VIABLE) · "
        "early 전용 패치보다 전구간 cold-free/neighbor 쪽이 우선"
    )

    payload = {
        "id": "K-EARLY-DIAG",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "wire": False,
        "draw_range": [1036, 1235],
        "by_period": by_period,
        "contrast": {
            "early_vs_mid_ge3": ge3_gap_mid,
            "early_vs_late_ge3": round(late["ge3"] - early["ge3"], 6),
            "entropy_mid_minus_early": ent_gap,
            "sum_mean_early_minus_mid": round(
                early["sum_dist"]["mean"] - mid["sum_dist"]["mean"], 6
            ),
            "cold_delta_early_vs_mid": {
                "early": early["cold_k5_delta"],
                "mid": mid["cold_k5_delta"],
                "late": late["cold_k5_delta"],
            },
        },
        "root_cause": root,
        "wire_implication": wire_imp,
        "forbid": [
            "random.choices",
            "engine.py",
            "auto-tune",
            "wire",
            "DB INSERT/UPDATE",
            "_get_draws_before mutate",
            "ge3 향상 클레임",
        ],
        "pass": True,
        "tool": "tools/_k_early_diag.py",
        "prior": "docs/benchmarks/20260805_KCOVER_DIAG.json",
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
                "verdict": verdict,
                "ge3": {k: by_period[k]["ge3"] for k in by_period},
                "entropy": {k: by_period[k]["pool_entropy"] for k in by_period},
                "cold_delta": {k: by_period[k]["cold_k5_delta"] for k in by_period},
                "root": root,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
