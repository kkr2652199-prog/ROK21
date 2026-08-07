# -*- coding: utf-8 -*-
"""K-STAT-NUM-ASSOC-FULL — 과거학습 번호→다음회 연관 전수 (A+B+C+F).

A) early/mid/late 구간
B) lift 임계 스윕 1.10 / 1.15 / 1.20
C) 6번호 top15 합집합이 실제 다음6 커버 개수
F) null 시뮬 (다음회 번호를 균등 랜덤 6개로 치환한 뒤 동일 지표)

WIRE/발권 금지. asof: N+1 <= anchor.

Usage:
  python tools/_k_stat_num_assoc_full.py
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NULL = 6 / 45
MIN_COUNT = 12
LIFT_THRESHOLDS = (1.10, 1.15, 1.20)
TOP_M = 15
ANCHOR_LO = 200  # 충분한 과거 pairs
NULL_SEED = 20260808
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KSTAT_NUM_ASSOC_FULL.json"
OUT_MD = ROOT / "reports" / "20260808_KSTAT_NUM_ASSOC_FULL.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def load_draws() -> list[dict[str, Any]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT draw_no, draw_date, num1,num2,num3,num4,num5,num6
            FROM lotto_draws ORDER BY draw_no
            """
        ).fetchall()
    finally:
        conn.close()
    out = []
    for r in rows:
        d = dict(r)
        out.append(
            {
                "draw_no": int(d["draw_no"]),
                "draw_date": d.get("draw_date"),
                "nums": sorted(int(d[f"num{k}"]) for k in range(1, 7)),
            }
        )
    return out


def build_appear_index(draws: list[dict]) -> dict[int, list[int]]:
    """num -> sorted draw_nos where num appeared."""
    idx: dict[int, list[int]] = {n: [] for n in range(1, 46)}
    for d in draws:
        for x in d["nums"]:
            idx[x].append(d["draw_no"])
    return idx


def next_counts_for(
    num: int,
    anchor: int,
    appear: dict[int, list[int]],
    next_nums: dict[int, list[int]],
) -> tuple[int, Counter[int]]:
    """Pairs where num at N, N+1<=anchor. Returns (n_pairs, counter of next nums)."""
    ctr: Counter[int] = Counter()
    n_pairs = 0
    for n in appear[num]:
        if n >= anchor:
            break
        n1 = n + 1
        if n1 > anchor:
            continue
        nxt = next_nums.get(n1)
        if not nxt:
            continue
        n_pairs += 1
        ctr.update(nxt)
    return n_pairs, ctr


def top15_and_lifts(
    ctr: Counter[int], n_pairs: int
) -> tuple[list[int], dict[int, float], dict[int, int]]:
    lifts: dict[int, float] = {}
    counts: dict[int, int] = {}
    for y in range(1, 46):
        c = int(ctr.get(y, 0))
        counts[y] = c
        rate = c / n_pairs if n_pairs else 0.0
        lifts[y] = rate / NULL if NULL else 0.0
    # top15 by lift then count
    order = sorted(range(1, 46), key=lambda y: (-lifts[y], -counts[y], y))
    return order[:TOP_M], lifts, counts


def high_lift_set(
    lifts: dict[int, float], counts: dict[int, int], thr: float
) -> set[int]:
    return {y for y in range(1, 46) if lifts[y] >= thr and counts[y] >= MIN_COUNT}


def period_of(anchor: int, lo: int, hi: int) -> str:
    span = hi - lo + 1
    a = lo + span // 3
    b = lo + 2 * span // 3
    if anchor <= a:
        return "early"
    if anchor <= b:
        return "mid"
    return "late"


def eval_anchor(
    anchor: int,
    actual_next: list[int],
    nums: list[int],
    appear: dict[int, list[int]],
    next_nums: dict[int, list[int]],
    *,
    fake_next: list[int] | None = None,
) -> dict[str, Any]:
    target = fake_next if fake_next is not None else actual_next
    act = set(target)
    per_top: list[list[int]] = []
    per_lifts: list[dict[int, float]] = []
    per_counts: list[dict[int, int]] = []
    self_lifts = []
    for x in nums:
        n_pairs, ctr = next_counts_for(x, anchor, appear, next_nums)
        top, lifts, counts = top15_and_lifts(ctr, n_pairs)
        per_top.append(top)
        per_lifts.append(lifts)
        per_counts.append(counts)
        self_lifts.append(lifts.get(x, 0.0))

    # mean lift on actual 6
    mean_lifts_y = []
    for y in target:
        vals = [per_lifts[i].get(y, 0.0) for i in range(6)]
        mean_lifts_y.append(sum(vals) / 6)
    mean_lift_avg = sum(mean_lifts_y) / len(mean_lifts_y) if mean_lifts_y else 0.0

    # C) union cover
    union = set()
    for t in per_top:
        union |= set(t)
    union_cover = len(union & act)

    # B) multi_top1 / high_lift hits per threshold
    by_thr: dict[str, Any] = {}
    for thr in LIFT_THRESHOLDS:
        vote: Counter[int] = Counter()
        for i in range(6):
            for y in high_lift_set(per_lifts[i], per_counts[i], thr):
                vote[y] += 1
        top1 = vote.most_common(1)[0][0] if vote else None
        top3 = [n for n, _ in vote.most_common(3)]
        by_thr[str(thr)] = {
            "multi_top1": top1,
            "multi_top1_hit": bool(top1 in act) if top1 is not None else False,
            "multi_top3_hit_n": len(set(top3) & act),
            "n_high_unique": len(vote),
        }

    # also top15-by-lift vote (rank based, thr-independent): each num's top15 vote
    vote15: Counter[int] = Counter()
    for t in per_top:
        vote15.update(t)
    t1 = vote15.most_common(1)[0][0] if vote15 else None

    return {
        "mean_lift_on_actual6_avg": round(mean_lift_avg, 6),
        "union15_cover_n": union_cover,  # 0..6
        "union15_size": len(union),
        "multi_top1_by_rank15": t1,
        "multi_top1_by_rank15_hit": bool(t1 in act) if t1 is not None else False,
        "by_thr": by_thr,
        "mean_self_lift": round(sum(self_lifts) / 6, 6),
        "carry_n": len(set(nums) & set(actual_next)),  # always real carry
    }


def summarize(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    n = len(rows)
    if not n:
        return {"n": 0, "label": label}
    ml = [r["mean_lift_on_actual6_avg"] for r in rows]
    uc = [r["union15_cover_n"] for r in rows]
    r15 = [r["multi_top1_by_rank15_hit"] for r in rows]
    carry = [r["carry_n"] for r in rows]
    out: dict[str, Any] = {
        "label": label,
        "n": n,
        "mean_lift_avg": round(sum(ml) / n, 6),
        "median_mean_lift": round(sorted(ml)[n // 2], 6),
        "frac_mean_lift_ge_1_05": round(sum(1 for x in ml if x >= 1.05) / n, 6),
        "frac_mean_lift_ge_1_15": round(sum(1 for x in ml if x >= 1.15) / n, 6),
        "frac_mean_lift_near_1": round(sum(1 for x in ml if 0.95 <= x <= 1.05) / n, 6),
        "mean_union15_cover": round(sum(uc) / n, 6),
        "mean_union15_cover_null_ref": round(6 * (15 * 6 - 0) / 45, 4),  # rough; better below
        "union_cover_null_approx": round(6 * (1 - (1 - TOP_M / 45) ** 1), 4),  # wrong
        "note_union_null": "C(15 from ~union size)~; empiric null from F",
        "rank15_top1_hit_rate": round(sum(1 for x in r15 if x) / n, 6),
        "rank15_top1_null": round(6 / 45, 6),
        "mean_carry_n": round(sum(carry) / n, 6),
        "by_thr": {},
    }
    for thr in LIFT_THRESHOLDS:
        hits = [r["by_thr"][str(thr)]["multi_top1_hit"] for r in rows]
        t3 = [r["by_thr"][str(thr)]["multi_top3_hit_n"] for r in rows]
        out["by_thr"][str(thr)] = {
            "multi_top1_hit_rate": round(sum(1 for x in hits if x) / n, 6),
            "mean_multi_top3_hit_n": round(sum(t3) / n, 6),
            "top1_null": round(6 / 45, 6),
        }
    return out


def main() -> int:
    t0 = time.time()
    draws = load_draws()
    by = {d["draw_no"]: d for d in draws}
    max_d = max(by)
    # anchors with next existing
    anchors = [d for d in range(ANCHOR_LO, max_d) if (d in by and d + 1 in by)]
    lo, hi = anchors[0], anchors[-1]
    appear = build_appear_index(draws)
    next_nums = {d["draw_no"]: d["nums"] for d in draws}

    real_rows: list[dict[str, Any]] = []
    null_rows: list[dict[str, Any]] = []
    by_period: dict[str, list[dict]] = {"early": [], "mid": [], "late": []}
    rng = random.Random(NULL_SEED)

    for i, a in enumerate(anchors, 1):
        nums = by[a]["nums"]
        actual = by[a + 1]["nums"]
        row = eval_anchor(a, actual, nums, appear, next_nums)
        row["anchor"] = a
        row["period"] = period_of(a, lo, hi)
        real_rows.append(row)
        by_period[row["period"]].append(row)

        fake = sorted(rng.sample(range(1, 46), 6))
        nrow = eval_anchor(a, actual, nums, appear, next_nums, fake_next=fake)
        nrow["anchor"] = a
        null_rows.append(nrow)

        if i % 100 == 0 or i == len(anchors):
            print(f"  [{i}/{len(anchors)}] anchor={a} elapsed={time.time()-t0:.0f}s", flush=True)

    agg_all = summarize(real_rows, "all")
    # fix union null from F empiric
    null_agg = summarize(null_rows, "null_sim")
    agg_all["mean_union15_cover_null_empiric"] = null_agg["mean_union15_cover"]
    agg_all["rank15_top1_hit_null_empiric"] = null_agg["rank15_top1_hit_rate"]
    agg_all["mean_lift_null_empiric"] = null_agg["mean_lift_avg"]

    period_agg = {k: summarize(v, k) for k, v in by_period.items()}

    # delta vs null
    def delta(a: float | None, b: float | None) -> float | None:
        if a is None or b is None:
            return None
        return round(a - b, 6)

    vs_null = {
        "mean_lift_delta": delta(agg_all["mean_lift_avg"], null_agg["mean_lift_avg"]),
        "union_cover_delta": delta(
            agg_all["mean_union15_cover"], null_agg["mean_union15_cover"]
        ),
        "rank15_top1_hit_delta": delta(
            agg_all["rank15_top1_hit_rate"], null_agg["rank15_top1_hit_rate"]
        ),
        "by_thr": {
            str(thr): {
                "top1_hit_delta": delta(
                    agg_all["by_thr"][str(thr)]["multi_top1_hit_rate"],
                    null_agg["by_thr"][str(thr)]["multi_top1_hit_rate"],
                )
            }
            for thr in LIFT_THRESHOLDS
        },
    }

    # verdict heuristic
    weak = (
        abs(vs_null["mean_lift_delta"] or 0) < 0.03
        and abs(vs_null["union_cover_delta"] or 0) < 0.15
        and abs(vs_null["rank15_top1_hit_delta"] or 0) < 0.03
    )
    verdict = "NOISE_LIKE" if weak else "SIGNAL_CHECK"

    reads = [
        f"전수 n={len(real_rows)} anchors [{lo},{hi}]",
        f"mean_lift real={agg_all['mean_lift_avg']} null={null_agg['mean_lift_avg']} Δ={vs_null['mean_lift_delta']}",
        f"union15_cover real={agg_all['mean_union15_cover']} null={null_agg['mean_union15_cover']} Δ={vs_null['union_cover_delta']}",
        f"rank15_top1_hit real={agg_all['rank15_top1_hit_rate']} null={null_agg['rank15_top1_hit_rate']} Δ={vs_null['rank15_top1_hit_delta']}",
    ]
    for thr in LIFT_THRESHOLDS:
        r = agg_all["by_thr"][str(thr)]["multi_top1_hit_rate"]
        n = null_agg["by_thr"][str(thr)]["multi_top1_hit_rate"]
        reads.append(f"thr{thr} top1_hit real={r} null={n} Δ={vs_null['by_thr'][str(thr)]['top1_hit_delta']}")

    payload = {
        "id": "K-STAT-NUM-ASSOC-FULL",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "wire": False,
        "brain": "과거학습",
        "pass": True,
        "params": {
            "anchor_lo": ANCHOR_LO,
            "anchor_hi": hi,
            "n_anchors": len(anchors),
            "null": NULL,
            "min_count": MIN_COUNT,
            "top_m": TOP_M,
            "lift_thresholds": list(LIFT_THRESHOLDS),
            "null_seed": NULL_SEED,
            "bundle": ["A_period", "B_thr_sweep", "C_union15", "F_null_sim"],
        },
        "aggregate_all": agg_all,
        "aggregate_null_sim": null_agg,
        "aggregate_by_period": period_agg,
        "vs_null": vs_null,
        "pattern_read": reads,
        "ideas": [
            "NOISE_LIKE면 발권 wire 금지 · 명분 로그만.",
            "구간(period)만 튀면 레짐 의심 · 전체 wire 금지.",
            "임계 스윕이 모두 null 동급이면 임계 튜닝 무의미.",
        ],
        "elapsed_s": round(time.time() - t0, 2),
        "tool": "tools/_k_stat_num_assoc_full.py",
        "prior": "docs/benchmarks/20260808_KSTAT_NUM_ASSOC_SAMPLE.json",
        # compact per-anchor optional: omit full rows to keep JSON small — store summary only
        "samples_head": real_rows[:3],
        "samples_tail": real_rows[-3:],
    }

    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# K-STAT-NUM-ASSOC-FULL — 전수 A+B+C+F (2026-08-08)",
        "",
        f"- **판정:** `{verdict}` · wire=`False` · brain=**과거학습**",
        f"- anchors n=**{len(anchors)}** · range [{lo},{hi}] · elapsed={payload['elapsed_s']}s",
        "",
        "## vs null (F)",
        "",
        f"| 지표 | real | null_sim | Δ |",
        f"|------|-----:|---------:|--:|",
        f"| mean_lift | {agg_all['mean_lift_avg']} | {null_agg['mean_lift_avg']} | {vs_null['mean_lift_delta']} |",
        f"| union15_cover | {agg_all['mean_union15_cover']} | {null_agg['mean_union15_cover']} | {vs_null['union_cover_delta']} |",
        f"| rank15_top1_hit | {agg_all['rank15_top1_hit_rate']} | {null_agg['rank15_top1_hit_rate']} | {vs_null['rank15_top1_hit_delta']} |",
        "",
        "## B) 임계 스윕 top1_hit",
        "",
    ]
    for thr in LIFT_THRESHOLDS:
        r = agg_all["by_thr"][str(thr)]
        n = null_agg["by_thr"][str(thr)]
        lines.append(
            f"- thr={thr}: real=**{r['multi_top1_hit_rate']}** · null={n['multi_top1_hit_rate']} · "
            f"Δ={vs_null['by_thr'][str(thr)]['top1_hit_delta']}"
        )
    lines += ["", "## A) 구간별 mean_lift / union_cover / top1_hit", ""]
    for k in ("early", "mid", "late"):
        p = period_agg[k]
        lines.append(
            f"- **{k}** n={p['n']}: meanL={p['mean_lift_avg']} · "
            f"union={p['mean_union15_cover']} · top1={p['rank15_top1_hit_rate']}"
        )
    lines += ["", "## 패턴 읽기", ""]
    for r in reads:
        lines.append(f"- {r}")
    lines += [
        "",
        "## 해석",
        "",
        "- 당첨P↑ 클레임 금지.",
        "- NOISE_LIKE = 전수에서도 실측≈null → 과거학습 발권 패치 근거 약함.",
        "",
        f"- tool: `{payload['tool']}`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "verdict": verdict,
                "n": len(anchors),
                "vs_null": vs_null,
                "mean_lift": agg_all["mean_lift_avg"],
                "union": agg_all["mean_union15_cover"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
