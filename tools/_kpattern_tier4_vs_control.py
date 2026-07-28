# -*- coding: utf-8 -*-
"""K-PATTERN-1 — 회차별 뇌 예측 패턴 분석 (READ-ONLY).

초점: 4등 31건 + 대조군(matched=1,2) 에서 뇌가 '어떻게' 맞췄는지 구조 비교.
출력: docs/benchmarks/20260729_KPATTERN_tier4_vs_control.json
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KPATTERN_tier4_vs_control.json"

PIPE_SCORE_RE = re.compile(r"\[보조4뇌:([0-9.]+)\]")
AUX_SCORE_RE = re.compile(
    r"(오답탐정|패턴돋보기|균형지킴이)[^\|]*?점수?\s*([0-9.]+)"
)
AUX_SIMPLE_RE = re.compile(r"(오답탐정):([0-9.]+)")


def _odd_even(nums: list[int]) -> tuple[int, int]:
    o = sum(1 for n in nums if n % 2)
    return o, len(nums) - o


def _zones(nums: list[int]) -> tuple[int, int, int]:
    l = sum(1 for n in nums if 1 <= n <= 15)
    m = sum(1 for n in nums if 16 <= n <= 30)
    h = sum(1 for n in nums if 31 <= n <= 45)
    return l, m, h


def _consec_pairs(nums: list[int]) -> int:
    s = sorted(nums)
    return sum(1 for i in range(len(s) - 1) if s[i + 1] - s[i] == 1)


def _carry_from_prev(pred: list[int], prev: list[int] | None) -> int:
    if not prev:
        return 0
    return len(set(pred) & set(prev))


def feat(nums: list[int], prev: list[int] | None = None) -> dict[str, Any]:
    nums = [int(n) for n in nums]
    o, e = _odd_even(nums)
    l, m, h = _zones(nums)
    return {
        "sum": sum(nums),
        "odd": o,
        "even": e,
        "oe": f"{o}:{e}",
        "zone_lmh": f"{l}:{m}:{h}",
        "consec": _consec_pairs(nums),
        "carry_prev": _carry_from_prev(nums, prev),
        "span": (max(nums) - min(nums)) if nums else 0,
    }


def parse_pipe(reasoning: str) -> dict[str, float]:
    """Parse K-PIPE / AUX scores from set reasoning text."""
    text = reasoning or ""
    out: dict[str, float] = {}
    m = PIPE_SCORE_RE.search(text)
    if m:
        try:
            out["aux4_agg"] = float(m.group(1))
        except ValueError:
            pass
    for m in AUX_SIMPLE_RE.finditer(text):
        try:
            out[m.group(1)] = float(m.group(2))
        except ValueError:
            pass
    for m in AUX_SCORE_RE.finditer(text):
        try:
            out[m.group(1)] = float(m.group(2))
        except ValueError:
            pass
    return out


def load_prev_map(con: sqlite3.Connection) -> dict[int, list[int]]:
    rows = con.execute(
        "SELECT draw_no, num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    by_no = {
        int(r[0]): sorted(int(r[i]) for i in range(1, 7)) for r in rows
    }
    prev: dict[int, list[int]] = {}
    ordered = sorted(by_no)
    for i, d in enumerate(ordered):
        if i == 0:
            continue
        prev[d] = by_no[ordered[i - 1]]
    return prev


def summarize_group(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        return {"n": 0}
    oe = Counter(e["pred_feat"]["oe"] for e in entries)
    zone = Counter(e["pred_feat"]["zone_lmh"] for e in entries)
    set_nos = Counter(e["set_no"] for e in entries)
    sums = [e["pred_feat"]["sum"] for e in entries]
    carries = [e["pred_feat"]["carry_prev"] for e in entries]
    consecs = [e["pred_feat"]["consec"] for e in entries]
    hit_pos = Counter()  # which ball ranks hit most? skip
    # actual vs pred overlap style
    act_oe = Counter(e["actual_feat"]["oe"] for e in entries)
    # pipe keys present
    pipe_keys = Counter()
    aux_sums: dict[str, list[float]] = defaultdict(list)
    for e in entries:
        for k, v in (e.get("pipe") or {}).items():
            pipe_keys[k] += 1
            aux_sums[k].append(float(v))
    aux_means = {
        k: round(sum(vs) / len(vs), 4) for k, vs in aux_sums.items() if vs
    }
    return {
        "n": len(entries),
        "set_no_hist": dict(set_nos.most_common()),
        "pred_oe_top": oe.most_common(5),
        "pred_zone_top": zone.most_common(5),
        "actual_oe_top": act_oe.most_common(5),
        "pred_sum_mean": round(sum(sums) / len(sums), 2),
        "pred_sum_min": min(sums),
        "pred_sum_max": max(sums),
        "carry_prev_mean": round(sum(carries) / len(carries), 3),
        "consec_mean": round(sum(consecs) / len(consecs), 3),
        "pipe_key_freq": dict(pipe_keys.most_common(10)),
        "aux_score_means": aux_means,
        "brains": dict(Counter(e["brain"] for e in entries)),
    }


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    prev_map = load_prev_map(con)

    # tier4 hits
    hit_rows = con.execute(
        """
        SELECT r.draw_no, r.brain_tag, r.matched_count, r.bonus_matched,
               r.predicted_sets_json, r.best_set_no, r.predicted_nums,
               d.num1,d.num2,d.num3,d.num4,d.num5,d.num6,d.bonus
        FROM testlotto_brain_review r
        JOIN lotto_draws d ON d.draw_no = r.draw_no
        WHERE r.draw_no BETWEEN 2 AND 1234 AND r.matched_count = 4
        ORDER BY r.draw_no
        """
    ).fetchall()

    # control: matched=1 or 2, sample stratified by brain (up to 100 each band)
    ctrl_rows = con.execute(
        """
        SELECT r.draw_no, r.brain_tag, r.matched_count, r.bonus_matched,
               r.predicted_sets_json, r.best_set_no, r.predicted_nums,
               d.num1,d.num2,d.num3,d.num4,d.num5,d.num6,d.bonus
        FROM testlotto_brain_review r
        JOIN lotto_draws d ON d.draw_no = r.draw_no
        WHERE r.draw_no BETWEEN 2 AND 1234 AND r.matched_count IN (1, 2)
        ORDER BY r.draw_no
        """
    ).fetchall()

    def build(rows, limit: int | None = None) -> list[dict[str, Any]]:
        out = []
        for r in rows:
            if limit and len(out) >= limit:
                break
            actual = sorted(int(r[f"num{i}"]) for i in range(1, 7))
            sets = json.loads(r["predicted_sets_json"] or "[]")
            bsn = int(r["best_set_no"] or 1)
            best = next(
                (s for s in sets if int(s.get("set_no") or 0) == bsn),
                sets[bsn - 1] if sets else {},
            )
            pred = [int(n) for n in (best.get("nums") or [])]
            if not pred and r["predicted_nums"]:
                try:
                    pred = [int(x) for x in str(r["predicted_nums"]).replace(",", " ").split() if x.isdigit()]
                except Exception:
                    pred = []
            prev = prev_map.get(int(r["draw_no"]))
            reasoning = best.get("reasoning") or ""
            hit_nums = sorted(set(pred) & set(actual))
            miss_nums = sorted(set(pred) - set(actual))
            out.append(
                {
                    "draw": int(r["draw_no"]),
                    "brain": r["brain_tag"],
                    "matched": int(r["matched_count"]),
                    "set_no": bsn,
                    "pred": pred,
                    "actual": actual,
                    "bonus": int(r["bonus"]),
                    "hit_nums": hit_nums,
                    "miss_nums": miss_nums,
                    "pred_feat": feat(pred, prev),
                    "actual_feat": feat(actual, prev),
                    "pipe": parse_pipe(reasoning),
                    "reasoning_head": (reasoning[:120] if reasoning else ""),
                }
            )
        return out

    hits = build(hit_rows)
    # stratified control ~90 (30 per matched band x brains roughly)
    ctrl_by = defaultdict(list)
    for r in ctrl_rows:
        key = (r["brain_tag"], int(r["matched_count"]))
        if len(ctrl_by[key]) < 20:
            ctrl_by[key].append(r)
    flat_ctrl = []
    for v in ctrl_by.values():
        flat_ctrl.extend(v)
    flat_ctrl.sort(key=lambda r: int(r["draw_no"]))
    controls = build(flat_ctrl)

    # all-set diversity for hits: how many of 5 sets share ≥3 with actual
    set_diversity = []
    for r in hit_rows:
        actual = set(int(r[f"num{i}"]) for i in range(1, 7))
        sets = json.loads(r["predicted_sets_json"] or "[]")
        matches = [len(set(s.get("nums") or []) & actual) for s in sets]
        set_diversity.append(
            {
                "draw": int(r["draw_no"]),
                "brain": r["brain_tag"],
                "per_set_match": matches,
                "best": max(matches) if matches else 0,
                "n_ge3": sum(1 for m in matches if m >= 3),
                "n_ge4": sum(1 for m in matches if m >= 4),
                "unique_nums_in_5sets": len({n for s in sets for n in (s.get("nums") or [])}),
            }
        )

    # hit number frequency across tier4
    hit_ball = Counter()
    miss_ball = Counter()
    for e in hits:
        for n in e["hit_nums"]:
            hit_ball[n] += 1
        for n in e["miss_nums"]:
            miss_ball[n] += 1

    # brain-specific style on hits
    by_brain = defaultdict(list)
    for e in hits:
        by_brain[e["brain"]].append(e)

    # carry: when 4 hit, was carry_prev high?
    # also: did pred OE match actual OE?
    oe_match = sum(1 for e in hits if e["pred_feat"]["oe"] == e["actual_feat"]["oe"])
    zone_match = sum(
        1 for e in hits if e["pred_feat"]["zone_lmh"] == e["actual_feat"]["zone_lmh"]
    )
    ctrl_oe = sum(1 for e in controls if e["pred_feat"]["oe"] == e["actual_feat"]["oe"])
    ctrl_zone = sum(
        1 for e in controls if e["pred_feat"]["zone_lmh"] == e["actual_feat"]["zone_lmh"]
    )

    payload = {
        "id": "K-PATTERN-1",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "window": [2, 1234],
        "definition": {
            "tier4": "best-set matched_count==4",
            "control": "stratified matched_count in {1,2}, up to 20 per (brain,matched)",
            "note": "READ-ONLY · not a tuning claim · pattern description only",
        },
        "summary": {
            "tier4_n": len(hits),
            "control_n": len(controls),
            "tier4_oe_structure_match_rate": round(oe_match / len(hits), 4) if hits else 0,
            "control_oe_structure_match_rate": round(ctrl_oe / len(controls), 4) if controls else 0,
            "tier4_zone_structure_match_rate": round(zone_match / len(hits), 4) if hits else 0,
            "control_zone_structure_match_rate": round(ctrl_zone / len(controls), 4)
            if controls
            else 0,
        },
        "tier4_group": summarize_group(hits),
        "control_group": summarize_group(controls),
        "tier4_by_brain": {k: summarize_group(v) for k, v in sorted(by_brain.items())},
        "hit_ball_freq_top15": hit_ball.most_common(15),
        "miss_ball_freq_top15": miss_ball.most_common(15),
        "set_diversity_tier4": {
            "mean_unique_nums_in_5sets": round(
                sum(x["unique_nums_in_5sets"] for x in set_diversity) / len(set_diversity), 2
            )
            if set_diversity
            else 0,
            "mean_n_ge3_among_5": round(
                sum(x["n_ge3"] for x in set_diversity) / len(set_diversity), 3
            )
            if set_diversity
            else 0,
            "mean_n_ge4_among_5": round(
                sum(x["n_ge4"] for x in set_diversity) / len(set_diversity), 3
            )
            if set_diversity
            else 0,
            "samples": set_diversity[:8],
        },
        "tier4_cases": [
            {
                "draw": e["draw"],
                "brain": e["brain"],
                "set_no": e["set_no"],
                "hit": e["hit_nums"],
                "miss": e["miss_nums"],
                "pred_oe": e["pred_feat"]["oe"],
                "act_oe": e["actual_feat"]["oe"],
                "pred_zone": e["pred_feat"]["zone_lmh"],
                "act_zone": e["actual_feat"]["zone_lmh"],
                "pred_sum": e["pred_feat"]["sum"],
                "act_sum": e["actual_feat"]["sum"],
                "carry_prev": e["pred_feat"]["carry_prev"],
                "pipe": e["pipe"],
            }
            for e in hits
        ],
        "external_ai_brief": {
            "sources": [
                "LottoWise ML lottery analysis",
                "statlotto NN lottery",
                "Walk-forward (Susan Potter)",
            ],
            "consensus": [
                "fair lottery has no learnable next-ball function",
                "use WF + random baseline; do not claim prediction edge from mean alone",
                "useful ML = anomaly / aggregate structure / EV of shared jackpot — not jackpot forecast",
                "pattern work should describe HOW brains choose (constraints), not WHETHER they beat random",
            ],
            "rok21_apply": [
                "step1 = describe prediction microstructure on tier4 vs control",
                "success = reproducible structural story + null-check, not more 1등",
                "next tune only after K-TRUST-BENCH random baseline JSON",
            ],
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print("tier4", payload["summary"])
    print("tier4_group set_no", payload["tier4_group"].get("set_no_hist"))
    print("tier4 carry mean", payload["tier4_group"].get("carry_prev_mean"))
    print("control carry mean", payload["control_group"].get("carry_prev_mean"))
    print("set diversity", payload["set_diversity_tier4"])
    con.close()


if __name__ == "__main__":
    main()
