# -*- coding: utf-8 -*-
"""K-STAT-NUM-NEXT-FREQ — 과거학습용 번호별 출현·다음회 빈도 (READ-ONLY).

앵커 회차 당첨 6번호 각각에 대해:
  - 1~anchor 출현 횟수
  - 윈도우(1주/2주/1년/2년/10년/20년≈회차) 출현
  - 해당 번호가 나온 회차의 '다음 회' 번호 빈도 top

Usage:
  python tools/_k_stat_num_next_freq.py --anchor 1234
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

# 주 1회 가정
WINDOWS = {
    "1w": 1,
    "2w": 2,
    "1y": 52,
    "2y": 104,
    "10y": 520,
    "20y": 1040,
}
TOP_N = 15


def load_draws(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT draw_no, draw_date, num1,num2,num3,num4,num5,num6, bonus
        FROM lotto_draws ORDER BY draw_no
        """
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
        out.append(
            {
                "draw_no": int(d["draw_no"]),
                "draw_date": d.get("draw_date"),
                "nums": nums,
                "bonus": int(d["bonus"]) if d.get("bonus") is not None else None,
            }
        )
    return out


def analyze_number(
    num: int,
    draws: list[dict[str, Any]],
    anchor: int,
) -> dict[str, Any]:
    """num에 대해 1..anchor 구간 통계."""
    by_no = {d["draw_no"]: d for d in draws}
    # appearances of num at or before anchor
    hits = [d for d in draws if d["draw_no"] <= anchor and num in d["nums"]]
    hit_nos = [d["draw_no"] for d in hits]
    n_appear = len(hits)
    # expected under uniform ~ 6/45 * anchor
    expected = round(anchor * 6 / 45, 3)

    # window counts: last W draws ending at anchor (inclusive)
    win_counts: dict[str, Any] = {}
    for name, w in WINDOWS.items():
        lo = max(1, anchor - w + 1)
        cnt = sum(1 for dn in hit_nos if lo <= dn <= anchor)
        span = anchor - lo + 1
        win_counts[name] = {
            "window_draws": span,
            "appearances": cnt,
            "rate": round(cnt / span, 6) if span else 0.0,
            "null_rate": round(6 / 45, 6),
        }

    # next-draw frequency: for each appearance at N (N < anchor, need N+1 <= anchor
    # for training view; also allow N+1 == anchor+1 for "what followed historically
    # including predicting into future" — user asked 다음 회차 당첨 출현.
    # Use all N where num in D_N and N+1 exists and N+1 <= max available,
    # but for frequency table used as past learning as_of anchor: N+1 <= anchor
    # (no peek at 1235 when analyzing 1234 as problem). Offer both.
    next_asof: Counter[int] = Counter()
    next_full: Counter[int] = Counter()  # includes N+1 up to DB max (peek ref)
    n_pairs_asof = 0
    n_pairs_full = 0
    for d in hits:
        n = d["draw_no"]
        nxt = by_no.get(n + 1)
        if not nxt:
            continue
        n_pairs_full += 1
        for x in nxt["nums"]:
            next_full[x] += 1
        if n + 1 <= anchor:
            n_pairs_asof += 1
            for x in nxt["nums"]:
                next_asof[x] += 1

    def top_table(ctr: Counter[int], pairs: int) -> list[dict[str, Any]]:
        rows = []
        for x, c in ctr.most_common(TOP_N):
            rows.append(
                {
                    "num": x,
                    "count": c,
                    "rate_per_pair": round(c / pairs, 6) if pairs else 0.0,
                    "null_per_pair": round(6 / 45, 6),
                }
            )
        return rows

    # gaps: draws since last appearance before/at anchor
    last = hit_nos[-1] if hit_nos else None
    gap = (anchor - last) if last is not None else None

    # carry into 1235 if exists (reference only when analyzing 1234)
    nxt_anchor = by_no.get(anchor + 1)
    in_next_actual = bool(nxt_anchor and num in nxt_anchor["nums"]) if nxt_anchor else None

    return {
        "num": num,
        "appearances_1_to_anchor": n_appear,
        "expected_uniform": expected,
        "delta_vs_expected": round(n_appear - expected, 3),
        "first_draw": hit_nos[0] if hit_nos else None,
        "last_draw": last,
        "gap_from_last_to_anchor": gap,
        "windows": win_counts,
        "next_freq_asof_anchor": {
            "note": "번호 출현 회차 N의 다음 N+1 (N+1<=anchor · 컨닝금지)",
            "n_pairs": n_pairs_asof,
            "top15": top_table(next_asof, n_pairs_asof),
            "hit_count_dist_note": "count = 다음회 6개 중 해당 번호 포함 횟수",
        },
        "next_freq_full_incl_after_anchor": {
            "note": "참고·peek 가능 — N+1이 DB에 있으면 포함(1235 포함 가능)",
            "n_pairs": n_pairs_full,
            "top15": top_table(next_full, n_pairs_full),
        },
        "in_anchor_plus_1_actual": in_next_actual,
    }


def cross_pattern(per_num: list[dict[str, Any]], anchor_nums: list[int]) -> dict[str, Any]:
    """6번호 next_top15 교집합·겹침."""
    sets = []
    for p in per_num:
        tops = {r["num"] for r in p["next_freq_asof_anchor"]["top15"]}
        sets.append(tops)
    if not sets:
        return {}
    inter_all = set.intersection(*sets) if sets else set()
    # union of top15
    union = set.union(*sets) if sets else set()
    # how many of anchor+1 (if labeled) covered — handled outside
    # pairwise overlap sizes
    pair_ov = {}
    for i, a in enumerate(anchor_nums):
        for j, b in enumerate(anchor_nums):
            if j <= i:
                continue
            pair_ov[f"{a}&{b}"] = len(sets[i] & sets[j])
    return {
        "top15_intersection_all6": sorted(inter_all),
        "top15_union_size": len(union),
        "pairwise_top15_overlap": pair_ov,
    }


def run(anchor: int) -> dict[str, Any]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        draws = load_draws(conn)
    finally:
        conn.close()

    by_no = {d["draw_no"]: d for d in draws}
    if anchor not in by_no:
        raise SystemExit(f"anchor {anchor} not in DB")
    ad = by_no[anchor]
    per = [analyze_number(n, draws, anchor) for n in ad["nums"]]
    cross = cross_pattern(per, ad["nums"])

    nxt = by_no.get(anchor + 1)
    actual_next = nxt["nums"] if nxt else None
    # which next-top15 (asof) hit actual next
    hit_from_tops = {}
    if actual_next:
        actual_s = set(actual_next)
        for p in per:
            tops = {r["num"] for r in p["next_freq_asof_anchor"]["top15"]}
            hit_from_tops[str(p["num"])] = sorted(tops & actual_s)

    # ideas (conservative notes, not wire)
    ideas = [
        "번호별 '다음회 빈도'는 과거학습 뇌의 자연 재료(전이와 유사하나 앵커=단일번호).",
        "asof(컨닝금지) top15 ∩ 실제 다음회를 6번호 합치면 커버리지 측정 가능.",
        "윈도우 1y/2y vs 전구간 출현 Δ로 hot/cold 라벨을 unexplained에 붙일 수 있음.",
        "6개 next-top15 교집합이 비면 '공통 다음번호' 신화 약함 — 번호별 특화 신호 쪽.",
        "발권 wire 전: 카탈로그·커버리지 전수(1233↓) 후 HOLD/GO.",
    ]

    return {
        "id": "K-STAT-NUM-NEXT-FREQ",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "MEASURED",
        "wire": False,
        "brain": "과거학습",
        "tag": "stat",
        "anchor": {
            "draw_no": anchor,
            "draw_date": ad["draw_date"],
            "nums": ad["nums"],
            "prize_note": "형 제공 메타(1등 인원·당첨금)는 DB 외 참고",
        },
        "actual_next": {
            "draw_no": anchor + 1 if nxt else None,
            "nums": actual_next,
            "carry_from_anchor": sorted(set(ad["nums"]) & set(actual_next or [])),
        },
        "windows_def": WINDOWS,
        "per_number": per,
        "cross": cross,
        "top15_vs_actual_next": hit_from_tops,
        "ideas": ideas,
        "pass": True,
        "tool": "tools/_k_stat_num_next_freq.py",
        "forbid": ["engine 수정", "발권가중", "WIRE ON", "당첨P↑ 클레임"],
    }


def write_md(payload: dict[str, Any], path: Path) -> None:
    a = payload["anchor"]
    nxt = payload["actual_next"]
    lines = [
        f"# K-STAT-NUM-NEXT-FREQ — 과거학습 번호별 다음회 빈도 (anchor {a['draw_no']})",
        "",
        f"- **판정:** `{payload['verdict']}` · wire=`False` · brain=**과거학습**",
        f"- 앵커: **{a['draw_no']}** ({a['draw_date']}) `{a['nums']}`",
        f"- 실제 다음: **{nxt['draw_no']}** `{nxt['nums']}` · carry=`{nxt['carry_from_anchor']}`",
        "",
        "## 윈도우 정의 (주1회≈)",
        "",
        "| 키 | 회차 수 |",
        "|----|--------:|",
    ]
    for k, v in WINDOWS.items():
        lines.append(f"| {k} | {v} |")
    lines += ["", "## 번호별 요약", ""]
    for p in payload["per_number"]:
        lines.append(f"### 번호 {p['num']}")
        lines.append(
            f"- 1~{a['draw_no']} 출현 **{p['appearances_1_to_anchor']}** "
            f"(균등기대 {p['expected_uniform']} · Δ {p['delta_vs_expected']})"
        )
        lines.append(
            f"- 첫/마지막 출현: {p['first_draw']} / {p['last_draw']} · "
            f"gap(앵커기준)={p['gap_from_last_to_anchor']}"
        )
        lines.append(
            f"- 다음회 포함(실제 {nxt['draw_no']}): `{p['in_anchor_plus_1_actual']}`"
        )
        lines.append("- 윈도우 출현:")
        for wk, wv in p["windows"].items():
            lines.append(
                f"  - {wk}: {wv['appearances']}/{wv['window_draws']} "
                f"(rate={wv['rate']} · null={wv['null_rate']})"
            )
        lines.append(
            f"- next top15 (asof·n_pairs={p['next_freq_asof_anchor']['n_pairs']}): "
            + ", ".join(
                f"{r['num']}×{r['count']}"
                for r in p["next_freq_asof_anchor"]["top15"][:10]
            )
        )
        hit = payload["top15_vs_actual_next"].get(str(p["num"]), [])
        lines.append(f"- asof top15 ∩ 실제다음: `{hit}`")
        lines.append("")
    lines += [
        "## 교차 패턴",
        "",
        f"- 6번호 next-top15 교집합: `{payload['cross'].get('top15_intersection_all6')}`",
        f"- union size: **{payload['cross'].get('top15_union_size')}**",
        "",
        "## 아이디어 (wire 금지)",
        "",
    ]
    for i, idea in enumerate(payload["ideas"], 1):
        lines.append(f"{i}. {idea}")
    lines += [
        "",
        f"- tool: `{payload['tool']}`",
        f"- JSON: `docs/benchmarks/{path.stem.replace('reports/', '')}.json`".replace(
            "20260808_KSTAT_NUM_NEXT_FREQ_1234.md",
            "20260808_KSTAT_NUM_NEXT_FREQ_1234.json",
        ),
        "",
    ]
    # fix json line simply
    lines[-2] = f"- JSON: `docs/benchmarks/{path.name.replace('.md', '.json')}`"
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", type=int, default=1234)
    args = ap.parse_args()
    payload = run(args.anchor)
    stem = f"20260808_KSTAT_NUM_NEXT_FREQ_{args.anchor}"
    out_json = ROOT / "docs" / "benchmarks" / f"{stem}.json"
    out_md = ROOT / "reports" / f"{stem}.md"
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / out_md.name
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_md(payload, out_md)
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(out_md.read_text(encoding="utf-8"), encoding="utf-8")
    # brief console
    print(
        json.dumps(
            {
                "ok": True,
                "anchor": args.anchor,
                "nums": payload["anchor"]["nums"],
                "next": payload["actual_next"]["nums"],
                "carry": payload["actual_next"]["carry_from_anchor"],
                "intersection_top15": payload["cross"].get("top15_intersection_all6"),
                "hits_vs_next": payload["top15_vs_actual_next"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
