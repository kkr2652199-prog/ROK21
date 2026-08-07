# -*- coding: utf-8 -*-
"""K-STAT-NUM-ASSOC — 과거학습: 번호→다음회 연관(리프트) 정밀 (READ-ONLY).

앵커 회차 당첨 6번호 각각:
  - N에 번호 X 출현 → N+1 각 번호 출현 count/rate/lift (asof: N+1<=anchor)
  - 유의 후보: lift>=1.15 & count>= min_count
  - 앵커 6번호 상호 동반출현(같은 회)
  - 실제 다음회(anchor+1) 대비 커버(참고)

Usage:
  python tools/_k_stat_num_assoc.py --anchor 1234
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NULL = 6 / 45  # P(number in a random 6-set)
MIN_COUNT = 12
LIFT_HI = 1.15
LIFT_LO = 0.85
TOP_SHOW = 20


def load_draws(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT draw_no, draw_date, num1,num2,num3,num4,num5,num6
        FROM lotto_draws ORDER BY draw_no
        """
    ).fetchall()
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


def next_assoc(num: int, draws: list[dict], anchor: int) -> dict[str, Any]:
    by = {d["draw_no"]: d for d in draws}
    hits = [d for d in draws if d["draw_no"] < anchor and num in d["nums"]]
    # need N+1 <= anchor for nopeek training table
    pairs = []
    for d in hits:
        n1 = d["draw_no"] + 1
        if n1 > anchor:
            continue
        nxt = by.get(n1)
        if not nxt:
            continue
        pairs.append((d["draw_no"], nxt["nums"]))

    ctr: Counter[int] = Counter()
    for _, nums in pairs:
        for x in nums:
            ctr[x] += 1
    n_pairs = len(pairs)
    rows = []
    for y in range(1, 46):
        c = int(ctr.get(y, 0))
        rate = c / n_pairs if n_pairs else 0.0
        lift = rate / NULL if NULL else 0.0
        rows.append(
            {
                "num": y,
                "count": c,
                "rate": round(rate, 6),
                "lift": round(lift, 4),
                "null": round(NULL, 6),
            }
        )
    rows.sort(key=lambda r: (-r["lift"], -r["count"], r["num"]))
    high = [r for r in rows if r["lift"] >= LIFT_HI and r["count"] >= MIN_COUNT]
    low = [r for r in rows if r["lift"] <= LIFT_LO and r["count"] >= MIN_COUNT]
    # self-follow (carry): P(num again next)
    self_row = next(r for r in rows if r["num"] == num)

    return {
        "num": num,
        "n_pairs_asof": n_pairs,
        "appearances_before_anchor": len(hits),
        "self_next": self_row,  # 이월 성향
        "top_by_lift": rows[:TOP_SHOW],
        "high_lift": high[:TOP_SHOW],
        "low_lift": sorted(low, key=lambda r: (r["lift"], r["count"]))[:10],
        "all_lifts_compact": {str(r["num"]): r["lift"] for r in rows},
    }


def cooccur_among_anchor(anchor_nums: list[int], draws: list[dict], anchor: int) -> dict[str, Any]:
    """앵커 6번호가 과거(<=anchor) 같은 회에 몇 번 같이 나왔는지."""
    pair_c: Counter[tuple[int, int]] = Counter()
    for d in draws:
        if d["draw_no"] > anchor:
            continue
        s = set(d["nums"]) & set(anchor_nums)
        if len(s) < 2:
            continue
        xs = sorted(s)
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                pair_c[(xs[i], xs[j])] += 1
    # expected rough: C ways — just report counts
    pairs = [
        {"a": a, "b": b, "same_draw_count_1_to_anchor": c}
        for (a, b), c in sorted(pair_c.items(), key=lambda x: -x[1])
    ]
    return {"pairs": pairs, "n_anchor_nums": len(anchor_nums)}


def score_vs_actual_next(
    per: list[dict[str, Any]], actual_next: list[int] | None
) -> dict[str, Any]:
    if not actual_next:
        return {}
    act = set(actual_next)
    out = {}
    for p in per:
        lifts = []
        for y in act:
            L = float(p["all_lifts_compact"].get(str(y), 0))
            lifts.append({"num": y, "lift": L})
        lifts.sort(key=lambda r: -r["lift"])
        # high_lift set hit
        hi = {r["num"] for r in p["high_lift"]}
        out[str(p["num"])] = {
            "actual_next_lifts": lifts,
            "high_lift_hit_actual": sorted(hi & act),
            "mean_lift_on_actual6": round(
                sum(x["lift"] for x in lifts) / len(lifts), 4
            ),
        }
    # aggregate: for each actual next num, mean lift across 6 anchors
    by_y = {}
    for y in act:
        vals = [float(p["all_lifts_compact"].get(str(y), 0)) for p in per]
        by_y[str(y)] = {
            "mean_lift_from_6": round(sum(vals) / len(vals), 4),
            "max_lift_from_6": round(max(vals), 4),
            "from": {str(p["num"]): float(p["all_lifts_compact"].get(str(y), 0)) for p in per},
        }
    return {"per_anchor_num": out, "actual_next_summary": by_y}


def yearly_opinion_block() -> dict[str, Any]:
    return {
        "question": "년도별 출현 횟수를 더 쪼개야 하나?",
        "cursor_view": "LOW_PRIORITY",
        "reason": [
            "총출현(1~anchor)과 최근 윈도우(1y/2y/10y)로 hot/cold는 이미 충분.",
            "연도별 절대횟수는 표본(연≈52회)이 작아 노이즈·달력효과에 흔들림.",
            "과거학습 핵심은 '총횟수'가 아니라 'X 나온 다음 회에 Y가 얼마나' (조건부·리프트).",
            "연도 분해는 레짐변화(특정 연도만 튀는 번호) 의심될 때만 후순위.",
        ],
        "do_now": "번호→다음회 연관(리프트) 정밀",
    }


def run(anchor: int) -> dict[str, Any]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        draws = load_draws(conn)
    finally:
        conn.close()
    by = {d["draw_no"]: d for d in draws}
    if anchor not in by:
        raise SystemExit(f"missing {anchor}")
    ad = by[anchor]
    nxt = by.get(anchor + 1)
    per = [next_assoc(n, draws, anchor) for n in ad["nums"]]
    # strip bulky all_lifts from disk? keep for scoring then compact in file
    scored = score_vs_actual_next(per, nxt["nums"] if nxt else None)
    co = cooccur_among_anchor(ad["nums"], draws, anchor)

    # cross: numbers that are high_lift for >=2 of the 6
    vote: Counter[int] = Counter()
    for p in per:
        for r in p["high_lift"]:
            vote[r["num"]] += 1
    multi = [
        {"num": n, "n_anchor_nums_supporting": c}
        for n, c in vote.most_common(20)
        if c >= 2
    ]

    # compact per for JSON (drop all_lifts_compact full 45 — keep in scored refs)
    per_out = []
    for p in per:
        per_out.append(
            {
                "num": p["num"],
                "n_pairs_asof": p["n_pairs_asof"],
                "appearances_before_anchor": p["appearances_before_anchor"],
                "self_next": p["self_next"],
                "top_by_lift": p["top_by_lift"],
                "high_lift": p["high_lift"],
                "low_lift": p["low_lift"],
            }
        )

    ideas = [
        "연도별 총횟수보다 조건부(다음회) 리프트가 과거학습 축에 맞음.",
        "self_next lift≈1이면 이월도 특별하지 않음 — 15/43는 단건 성공일 수 있음.",
        "high_lift를 6번호에서 투표(≥2 지지)한 후보만 모아 다음회 커버 전수(1233↓).",
        "동반출현(같은 회)과 다음회 연관은 다른 축 — 둘 다 로그 라벨로만 우선.",
        "wire/발권가중 금지 · 패턴 카탈로그만.",
    ]

    return {
        "id": "K-STAT-NUM-ASSOC",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "MEASURED",
        "wire": False,
        "brain": "과거학습",
        "tag": "stat",
        "anchor": {
            "draw_no": anchor,
            "draw_date": ad["draw_date"],
            "nums": ad["nums"],
        },
        "actual_next": {
            "draw_no": anchor + 1 if nxt else None,
            "nums": nxt["nums"] if nxt else None,
            "carry": sorted(set(ad["nums"]) & set(nxt["nums"])) if nxt else [],
        },
        "params": {
            "null": NULL,
            "min_count": MIN_COUNT,
            "lift_hi": LIFT_HI,
            "lift_lo": LIFT_LO,
            "asof": "N+1 <= anchor",
        },
        "yearly_count_opinion": yearly_opinion_block(),
        "per_number": per_out,
        "cooccur_among_anchor6": co,
        "multi_support_high_lift": multi,
        "vs_actual_next": scored,
        "ideas": ideas,
        "pass": True,
        "tool": "tools/_k_stat_num_assoc.py",
        "prior": f"docs/benchmarks/20260808_KSTAT_NUM_NEXT_FREQ_{anchor}.json",
    }


def write_md(payload: dict[str, Any], path: Path) -> None:
    a = payload["anchor"]
    nxt = payload["actual_next"]
    op = payload["yearly_count_opinion"]
    lines = [
        f"# K-STAT-NUM-ASSOC — 번호→다음회 연관 정밀 (anchor {a['draw_no']})",
        "",
        f"- **판정:** `{payload['verdict']}` · wire=`False` · **과거학습**",
        f"- 앵커 **{a['draw_no']}** `{a['nums']}` → 다음 `{nxt['nums']}` carry=`{nxt['carry']}`",
        f"- asof: N+1≤{a['draw_no']} · null=6/45 · high lift≥{payload['params']['lift_hi']} & count≥{payload['params']['min_count']}",
        "",
        "## 연도별 출현 횟수 — 커서 의견",
        "",
        f"- 우선순위: **{op['cursor_view']}**",
    ]
    for r in op["reason"]:
        lines.append(f"- {r}")
    lines += ["", "## 번호별 self(이월) · high_lift 샘플", ""]
    for p in payload["per_number"]:
        s = p["self_next"]
        lines.append(
            f"### {p['num']} · pairs={p['n_pairs_asof']} · "
            f"self_next lift=**{s['lift']}** (count={s['count']})"
        )
        hi = ", ".join(f"{r['num']}(L{r['lift']},n{r['count']})" for r in p["high_lift"][:8])
        lines.append(f"- high_lift: {hi or '(없음)'}")
        vs = payload["vs_actual_next"].get("per_anchor_num", {}).get(str(p["num"]), {})
        if vs:
            lines.append(
                f"- 실제다음 6개 평균 lift=**{vs['mean_lift_on_actual6']}** · "
                f"high∩실제=`{vs['high_lift_hit_actual']}`"
            )
        lines.append("")
    lines += ["## 실제 다음번호가 6앵커로부터 받은 평균 lift", ""]
    for y, info in (payload["vs_actual_next"].get("actual_next_summary") or {}).items():
        lines.append(
            f"- **{y}**: mean_lift=**{info['mean_lift_from_6']}** · max={info['max_lift_from_6']}"
        )
    lines += [
        "",
        "## 2개 이상 앵커번호가 high_lift로 지지한 후보",
        "",
    ]
    for m in payload["multi_support_high_lift"][:15]:
        lines.append(f"- {m['num']}: {m['n_anchor_nums_supporting']}개 번호가 지지")
    lines += ["", "## 앵커6 과거 동반(같은 회) top", ""]
    for pr in payload["cooccur_among_anchor6"]["pairs"][:10]:
        lines.append(f"- {pr['a']}&{pr['b']}: {pr['same_draw_count_1_to_anchor']}회")
    lines += ["", "## 아이디어", ""]
    for i, idea in enumerate(payload["ideas"], 1):
        lines.append(f"{i}. {idea}")
    lines += ["", f"- tool: `{payload['tool']}`", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", type=int, default=1234)
    args = ap.parse_args()
    payload = run(args.anchor)
    stem = f"20260808_KSTAT_NUM_ASSOC_{args.anchor}"
    out_j = ROOT / "docs" / "benchmarks" / f"{stem}.json"
    out_m = ROOT / "reports" / f"{stem}.md"
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / out_m.name
    out_j.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_md(payload, out_m)
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(out_m.read_text(encoding="utf-8"), encoding="utf-8")
    # console brief
    summ = payload["vs_actual_next"].get("actual_next_summary") or {}
    print(
        json.dumps(
            {
                "ok": True,
                "yearly_priority": payload["yearly_count_opinion"]["cursor_view"],
                "carry": payload["actual_next"]["carry"],
                "actual_mean_lifts": {k: v["mean_lift_from_6"] for k, v in summ.items()},
                "multi_top5": payload["multi_support_high_lift"][:5],
                "self_lifts": {
                    str(p["num"]): p["self_next"]["lift"] for p in payload["per_number"]
                },
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
