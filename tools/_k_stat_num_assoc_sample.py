# -*- coding: utf-8 -*-
"""K-STAT-NUM-ASSOC-SAMPLE — 과거회차 샘플링 (1234와 동일 리프트 방식).

- 최근 연속 10회(1233↓) + 계층 랜덤 20회 (early/mid/late)
- 각 앵커: 번호→다음회 lift · 실제다음 mean_lift · multi-support top1 hit?
- 공통 패턴 집계 (WIRE 금지)

Usage:
  python tools/_k_stat_num_assoc_sample.py
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools._k_stat_num_assoc import (  # noqa: E402
    LIFT_HI,
    MIN_COUNT,
    NULL,
    load_draws,
    next_assoc,
    score_vs_actual_next,
)

SEED = 20260808
N_RECENT = 10  # 1233..1224
N_RANDOM = 20
REF_ANCHOR = 1234
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KSTAT_NUM_ASSOC_SAMPLE.json"
OUT_MD = ROOT / "reports" / "20260808_KSTAT_NUM_ASSOC_SAMPLE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def pick_anchors(max_draw: int) -> list[int]:
    """max_draw = DB max; need anchor+1 exists → anchor <= max_draw-1."""
    hi = max_draw - 1  # e.g. 1234 if max=1235
    recent = list(range(hi - 1, hi - 1 - N_RECENT, -1))  # 1233..1224 if hi=1234
    # stratified random from [200, hi-50] excluding recent+ref
    ban = set(recent) | {REF_ANCHOR}
    lo, mid_lo, mid_hi = 200, 600, 1000
    pools = {
        "early": [d for d in range(lo, mid_lo) if d not in ban and d + 1 <= max_draw],
        "mid": [d for d in range(mid_lo, mid_hi) if d not in ban and d + 1 <= max_draw],
        "late": [d for d in range(mid_hi, hi - 50) if d not in ban and d + 1 <= max_draw],
    }
    rng = random.Random(SEED)
    picked: list[int] = []
    per = N_RANDOM // 3
    rem = N_RANDOM - per * 3
    for i, key in enumerate(("early", "mid", "late")):
        n = per + (1 if i < rem else 0)
        pool = pools[key]
        if len(pool) < n:
            n = len(pool)
        picked.extend(rng.sample(pool, n))
    # unique preserve order: recent first then random sorted for stability in report
    out = []
    seen = set()
    for d in recent + sorted(picked):
        if d not in seen and d >= 200:
            seen.add(d)
            out.append(d)
    return out


def analyze_one(anchor: int, draws: list[dict], by: dict[int, dict]) -> dict[str, Any]:
    ad = by[anchor]
    nxt = by.get(anchor + 1)
    per = [next_assoc(n, draws, anchor) for n in ad["nums"]]
    scored = score_vs_actual_next(per, nxt["nums"] if nxt else None)
    vote: Counter[int] = Counter()
    for p in per:
        for r in p["high_lift"]:
            vote[r["num"]] += 1
    multi_top = vote.most_common(3)
    multi1 = multi_top[0][0] if multi_top else None
    act = set(nxt["nums"]) if nxt else set()
    mean_lifts = []
    if scored.get("actual_next_summary"):
        mean_lifts = [v["mean_lift_from_6"] for v in scored["actual_next_summary"].values()]
    self_lifts = {str(p["num"]): p["self_next"]["lift"] for p in per}
    return {
        "anchor": anchor,
        "date": ad.get("draw_date"),
        "nums": ad["nums"],
        "next": nxt["nums"] if nxt else None,
        "carry": sorted(set(ad["nums"]) & act),
        "carry_n": len(set(ad["nums"]) & act),
        "mean_lift_on_actual6_avg": round(sum(mean_lifts) / len(mean_lifts), 4)
        if mean_lifts
        else None,
        "actual_mean_lifts": {
            k: v["mean_lift_from_6"] for k, v in (scored.get("actual_next_summary") or {}).items()
        },
        "multi_top1": multi1,
        "multi_top1_in_next": bool(multi1 in act) if multi1 is not None else None,
        "multi_top3": [{"num": n, "votes": c} for n, c in multi_top],
        "multi_top3_hit_n": len({n for n, _ in multi_top} & act),
        "mean_self_lift": round(sum(self_lifts.values()) / 6, 4),
        "self_lifts": self_lifts,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    mean_l = [r["mean_lift_on_actual6_avg"] for r in rows if r["mean_lift_on_actual6_avg"] is not None]
    multi_hit = [r["multi_top1_in_next"] for r in rows if r["multi_top1_in_next"] is not None]
    carry_ns = [r["carry_n"] for r in rows]
    top3_hits = [r["multi_top3_hit_n"] for r in rows]
    # how often mean_lift band
    ge_115 = sum(1 for x in mean_l if x >= 1.15)
    ge_105 = sum(1 for x in mean_l if x >= 1.05)
    near1 = sum(1 for x in mean_l if 0.95 <= x <= 1.05)
    # vote champions frequency
    champ = Counter(r["multi_top1"] for r in rows if r["multi_top1"] is not None)
    return {
        "n": n,
        "mean_of_mean_lift_on_actual": round(sum(mean_l) / len(mean_l), 4) if mean_l else None,
        "median_mean_lift": round(sorted(mean_l)[len(mean_l) // 2], 4) if mean_l else None,
        "frac_mean_lift_ge_1_15": round(ge_115 / len(mean_l), 4) if mean_l else None,
        "frac_mean_lift_ge_1_05": round(ge_105 / len(mean_l), 4) if mean_l else None,
        "frac_mean_lift_near_1": round(near1 / len(mean_l), 4) if mean_l else None,
        "multi_top1_hit_rate": round(sum(1 for x in multi_hit if x) / len(multi_hit), 4)
        if multi_hit
        else None,
        "null_top1_hit_approx": round(15 / 45, 4),  # if random from top15-ish; loose
        "note_top1_null": "단일번호가 다음6에 포함 P≈6/45≈0.133 (multi_top1은 1번호)",
        "multi_top1_null_p": round(6 / 45, 4),
        "mean_carry_n": round(sum(carry_ns) / n, 4) if n else None,
        "mean_multi_top3_hit_n": round(sum(top3_hits) / n, 4) if n else None,
        "multi_top1_champions": dict(champ.most_common(15)),
        "pattern_read": [],
    }


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        draws = load_draws(conn)
    finally:
        conn.close()
    by = {d["draw_no"]: d for d in draws}
    max_d = max(by)
    anchors = pick_anchors(max_d)
    # also append REF for comparison row flag
    rows = []
    for i, a in enumerate(anchors, 1):
        row = analyze_one(a, draws, by)
        row["bucket"] = "recent" if a >= max_d - 1 - N_RECENT else "random"
        rows.append(row)
        if i % 5 == 0 or i == len(anchors):
            print(f"  [{i}/{len(anchors)}] anchor={a}", flush=True)

    # ref 1234
    ref = analyze_one(REF_ANCHOR, draws, by)
    ref["bucket"] = "ref_1234"

    agg_all = aggregate(rows)
    agg_recent = aggregate([r for r in rows if r["bucket"] == "recent"])
    agg_rand = aggregate([r for r in rows if r["bucket"] == "random"])

    # pattern reads
    reads = []
    ml = agg_all["mean_of_mean_lift_on_actual"]
    if ml is not None and 0.95 <= ml <= 1.05:
        reads.append("표본 전체: 실제다음6 평균리프트~1 → 번호→다음 연관이 랜덤과 구분 약함")
    if agg_all["multi_top1_hit_rate"] is not None:
        if agg_all["multi_top1_hit_rate"] <= agg_all["multi_top1_null_p"] + 0.05:
            reads.append(
                f"multi_top1 적중률 {agg_all['multi_top1_hit_rate']} ~ null {agg_all['multi_top1_null_p']} → 투표1위 신호 약함"
            )
        else:
            reads.append("multi_top1 적중률이 null을 소폭 상회 — 전수 재확인 필요")
    if agg_all["mean_carry_n"] is not None and 0.7 <= agg_all["mean_carry_n"] <= 1.0:
        reads.append(f"평균 이월개수≈{agg_all['mean_carry_n']} (이론 mean carry≈0.83과 정합 가능)")
    agg_all["pattern_read"] = reads

    payload = {
        "id": "K-STAT-NUM-ASSOC-SAMPLE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "MEASURED",
        "wire": False,
        "brain": "과거학습",
        "seed": SEED,
        "params": {
            "null": NULL,
            "lift_hi": LIFT_HI,
            "min_count": MIN_COUNT,
            "n_recent": N_RECENT,
            "n_random": N_RANDOM,
            "ref_anchor": REF_ANCHOR,
        },
        "anchors": anchors,
        "n_sampled": len(rows),
        "ref_1234": {
            "mean_lift_on_actual6_avg": ref["mean_lift_on_actual6_avg"],
            "multi_top1": ref["multi_top1"],
            "multi_top1_in_next": ref["multi_top1_in_next"],
            "carry_n": ref["carry_n"],
            "actual_mean_lifts": ref["actual_mean_lifts"],
        },
        "aggregate_all": agg_all,
        "aggregate_recent": agg_recent,
        "aggregate_random": agg_rand,
        "samples": rows,
        "ideas": [
            "표본에서도 mean_lift≈1이면 과거학습 발권 wire 근거 약함 → 로그/명분만.",
            "1233↓ 전수는 표본 결론이 STABLE일 때만 비용 대비 효과.",
            "multi_top1 챔피언이 특정 번호에 몰리면 '자주 뽑히는 인기번호' 편향 의심.",
        ],
        "pass": True,
        "tool": "tools/_k_stat_num_assoc_sample.py",
        "prior": "docs/benchmarks/20260808_KSTAT_NUM_ASSOC_1234.json",
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# K-STAT-NUM-ASSOC-SAMPLE — 과거회차 리프트 샘플링 (2026-08-08)",
        "",
        f"- **판정:** `MEASURED` · wire=`False` · seed={SEED}",
        f"- 표본: 최근연속 **{N_RECENT}** + 계층랜덤 **{N_RANDOM}** · n=**{len(rows)}**",
        f"- 앵커목록: `{anchors}`",
        "",
        "## 집계 (전체 표본)",
        "",
        f"- 실제다음6 평균리프트의 평균: **{agg_all['mean_of_mean_lift_on_actual']}** "
        f"(median={agg_all['median_mean_lift']})",
        f"- mean_lift ≥1.15 비율: {agg_all['frac_mean_lift_ge_1_15']} · "
        f"≥1.05: {agg_all['frac_mean_lift_ge_1_05']} · near1: {agg_all['frac_mean_lift_near_1']}",
        f"- multi_top1 다음회 적중률: **{agg_all['multi_top1_hit_rate']}** "
        f"(null≈{agg_all['multi_top1_null_p']})",
        f"- 평균 이월개수: **{agg_all['mean_carry_n']}** · multi_top3 평균적중: {agg_all['mean_multi_top3_hit_n']}",
        f"- multi_top1 챔피언 빈도: `{agg_all['multi_top1_champions']}`",
        "",
        "### 패턴 읽기",
        "",
    ]
    for r in reads:
        lines.append(f"- {r}")
    lines += [
        "",
        "## 구간별",
        "",
        f"- recent: meanL={agg_recent['mean_of_mean_lift_on_actual']} · "
        f"top1_hit={agg_recent['multi_top1_hit_rate']}",
        f"- random: meanL={agg_rand['mean_of_mean_lift_on_actual']} · "
        f"top1_hit={agg_rand['multi_top1_hit_rate']}",
        "",
        "## 참고 1234",
        "",
        f"- `{payload['ref_1234']}`",
        "",
        "## 샘플 표 (요약)",
        "",
        "| anchor | carry_n | meanL | multi_top1 | hit? |",
        "|-------:|--------:|------:|----------:|:----:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['anchor']} | {r['carry_n']} | {r['mean_lift_on_actual6_avg']} | "
            f"{r['multi_top1']} | {r['multi_top1_in_next']} |"
        )
    lines += ["", "## 아이디어", ""]
    for i, idea in enumerate(payload["ideas"], 1):
        lines.append(f"{i}. {idea}")
    lines += ["", f"- tool: `{payload['tool']}`", ""]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "n": len(rows),
                "agg": {
                    "meanL": agg_all["mean_of_mean_lift_on_actual"],
                    "top1_hit": agg_all["multi_top1_hit_rate"],
                    "carry": agg_all["mean_carry_n"],
                },
                "reads": reads,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
