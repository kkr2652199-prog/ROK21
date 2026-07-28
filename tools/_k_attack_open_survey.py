# -*- coding: utf-8 -*-
"""K-ATTACK-OPEN — 다음 공격 레버 3종 READ-ONLY 서베이.

A) analog overlap vs matched
B) markov steps×decay (결정론 top6 · seed walk)
C) conf 신호강도 재점수 (5세트 내 순위)

산출: docs/benchmarks/20260729_KOPEN_survey.json
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KOPEN_survey.json"

BRAINS = ("stat", "markov", "review")
D_LO, D_HI = 2, 1234
MIN_TRAIN = 50
RR_MEAN = 1.7428
RR_GE3 = 0.1337


def spearman(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 5:
        return 0.0

    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(vals):
            j = i
            while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx < 1e-12 or dy < 1e-12:
        return 0.0
    return round(num / (dx * dy), 4)


def summarize(ms: list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3_rate": 0.0}
    ge3 = sum(1 for x in ms if x >= 3)
    return {
        "n": n,
        "mean": round(sum(ms) / n, 4),
        "ge3": ge3,
        "ge3_rate": round(ge3 / n, 4),
    }


def load_draws() -> list[dict]:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1 AND ? ORDER BY draw_no",
        (D_HI,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def load_reviews() -> dict[int, dict[str, list[dict]]]:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT draw_no, brain_tag, predicted_sets_json, matched_count, best_set_no
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN ? AND ? AND brain_tag IN ('stat','markov','review')
        """,
        (D_LO, D_HI),
    ).fetchall()
    con.close()
    by: dict[int, dict[str, list[dict]]] = defaultdict(dict)
    meta: dict[int, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        d = int(r["draw_no"])
        tag = r["brain_tag"]
        try:
            sets = json.loads(r["predicted_sets_json"] or "[]")
        except Exception:
            sets = []
        parsed = []
        for s in sets:
            nums = [int(x) for x in (s.get("nums") or [])]
            parsed.append(
                {
                    "set_no": int(s.get("set_no") or 0),
                    "conf": float(s.get("confidence") or 0),
                    "match": int(s["matched_count"]) if s.get("matched_count") is not None else 0,
                    "nums": nums,
                }
            )
        by[d][tag] = parsed
        meta[d][tag] = {
            "best_match": int(r["matched_count"] or 0),
            "best_set_no": int(r["best_set_no"] or 1),
        }
    return by, meta  # type: ignore


def survey_lever_a(
    draws: list[dict],
    by_rev: dict[int, dict[str, list[dict]]],
) -> dict[str, Any]:
    from app.testlotto.analog_service import find_analogs, predict_from_analogs, draw_nums

    draw_by_no = {int(d["draw_no"]): d for d in draws}
    overlaps: list[float] = []
    matches: list[float] = []

    complete = sorted(d for d, br in by_rev.items() if all(b in br for b in BRAINS))
    for d in complete:
        if d < MIN_TRAIN + 2:
            continue
        prev = draw_by_no.get(d - 1)
        if not prev:
            continue
        base = draw_nums(prev)
        past = [draw_by_no[k] for k in sorted(draw_by_no) if k < d - 1]
        if len(past) < 20:
            continue
        analogs = find_analogs(base, past, top_k=15)
        analog_pred = set(
            predict_from_analogs(
                base, analogs, draw_by_no, "M_weighted", target_draw_no=d
            )
        )
        for tag in BRAINS:
            for s in by_rev[d][tag]:
                ov = len(set(s["nums"]) & analog_pred) / 6.0
                overlaps.append(ov)
                matches.append(float(s["match"]))

    r = spearman(overlaps, matches)
    verdict = "유망" if r > 0.03 else "관측종료"
    return {
        "overlap_spearman_r": r,
        "overlap_mean": round(sum(overlaps) / len(overlaps), 4) if overlaps else 0.0,
        "n_pairs": len(overlaps),
        "pass": r > 0.03,
        "verdict": verdict,
    }


def survey_lever_b(draws: list[dict]) -> dict[str, Any]:
    """결정론 top6 (visit) — steps×decay. random.choices 조합 생성은 사용하지 않음."""
    from app.testlotto.predict_markov import build_transition_matrix, markov_random_walk

    steps_list = [50, 80, 120, 200]
    decay_list = [0.01, 0.02, 0.05]
    draw_by_no = {int(d["draw_no"]): d for d in draws}
    ordered = sorted(draw_by_no)
    actuals = {
        dn: set(int(draw_by_no[dn][f"num{k}"]) for k in range(1, 7)) for dn in ordered
    }

    # eval draws with enough history
    eval_dns = [dn for dn in ordered if D_LO <= dn <= D_HI and dn >= MIN_TRAIN + 1]

    combos: list[dict[str, Any]] = []
    baseline = None

    for steps in steps_list:
        for decay in decay_list:
            ms: list[int] = []
            for dn in eval_dns:
                # draws before dn
                hist = [draw_by_no[x] for x in ordered if x < dn]
                if len(hist) < 2:
                    continue
                matrix = build_transition_matrix(hist, decay=decay)
                start = [hist[-1][f"num{k}"] for k in range(1, 7)]
                random.seed(dn * 10007 + steps * 13 + int(decay * 1000))
                visits = markov_random_walk(matrix, start, steps=steps)
                top6 = sorted(
                    sorted(visits.items(), key=lambda x: (-x[1], x[0]))[:6],
                    key=lambda x: x[0],
                )
                nums = [n for n, _ in top6]
                ms.append(len(set(nums) & actuals[dn]))

            s = summarize(ms)
            row = {
                "steps": steps,
                "decay": decay,
                "mean": s["mean"],
                "ge3_rate": s["ge3_rate"],
                "n": s["n"],
                "delta_mean_vs_rr": round(s["mean"] - RR_MEAN, 4),
                "delta_ge3_vs_rr": round(s["ge3_rate"] - RR_GE3, 4),
            }
            combos.append(row)
            if steps == 80 and abs(decay - 0.02) < 1e-9:
                baseline = row

    best = max(combos, key=lambda r: (r["mean"], r["ge3_rate"]))
    passed = best["mean"] > RR_MEAN or best["ge3_rate"] > RR_GE3
    return {
        "baseline_80_002": baseline,
        "best_combo": {"steps": best["steps"], "decay": best["decay"]},
        "best_mean": best["mean"],
        "best_ge3_rate": best["ge3_rate"],
        "delta_vs_baseline": round(
            best["mean"] - (baseline["mean"] if baseline else 0), 4
        ),
        "delta_vs_rr_mean": best["delta_mean_vs_rr"],
        "all_combos": combos,
        "method": "deterministic_top6_visit · seeded walk (no set random.choices)",
        "pass": passed,
        "verdict": "유망" if passed else "관측종료",
    }


def _rank01(scores: list[float]) -> list[float]:
    n = len(scores)
    if n <= 1:
        return [0.5] * n
    order = sorted(range(n), key=lambda i: scores[i])
    r = [0.0] * n
    for rank, i in enumerate(order):
        r[i] = rank / (n - 1)
    return r


def survey_lever_c(
    draws: list[dict],
    by_rev: dict[int, dict[str, list[dict]]],
) -> dict[str, Any]:
    from app.testlotto.predict_statistical import get_statistical_prob_vector
    from app.testlotto.predict_markov import (
        build_transition_matrix,
        get_markov_prob_vector,
        markov_random_walk,
    )

    draw_by_no = {int(d["draw_no"]): d for d in draws}
    ordered = sorted(draw_by_no)
    complete = sorted(d for d, br in by_rev.items() if all(b in br for b in BRAINS))

    per_brain: dict[str, dict[str, Any]] = {}
    pick_new: list[int] = []
    pick_orig: list[int] = []
    all_new_conf: list[float] = []
    all_match: list[float] = []

    for tag in BRAINS:
        confs: list[float] = []
        matches: list[float] = []
        bins = [0] * 10

        for d in complete:
            if d < MIN_TRAIN + 1:
                continue
            hist = [draw_by_no[x] for x in ordered if x < d]
            if len(hist) < 2:
                continue
            sets = by_rev[d][tag]
            if len(sets) < 2:
                continue

            if tag == "stat":
                pv = get_statistical_prob_vector(hist)
                # freq variance proxy: use recent freq of nums
                s1 = [sum(pv.get(n, 0) for n in s["nums"]) for s in sets]
                # secondary: avg gap from last seen — use 1-prob as rarity
                s2 = [sum(1.0 - pv.get(n, 0) for n in s["nums"]) for s in sets]
            elif tag == "markov":
                pv = get_markov_prob_vector(hist)
                matrix = build_transition_matrix(hist, decay=0.02)
                start = [hist[-1][f"num{k}"] for k in range(1, 7)]
                random.seed(d * 17 + 3)
                visits = markov_random_walk(matrix, start, steps=80)
                s1 = [sum(visits.get(n, 0) for n in s["nums"]) for s in sets]
                # transition from last draw nums
                last = set(start)
                s2 = []
                for s in sets:
                    sc = 0.0
                    for a in last:
                        for b in s["nums"]:
                            sc += matrix[a][b]
                    s2.append(sc)
            else:  # review
                recent = hist[-10:]
                recent_cnt: dict[int, int] = defaultdict(int)
                for row in recent:
                    for k in range(1, 7):
                        recent_cnt[int(row[f"num{k}"])] += 1
                carry = set(int(hist[-1][f"num{k}"]) for k in range(1, 7))
                s1 = [sum(recent_cnt.get(n, 0) for n in s["nums"]) for s in sets]
                s2 = [len(set(s["nums"]) & carry) for s in sets]

            r1, r2 = _rank01(s1), _rank01(s2)
            new_confs = [50 + 30 * a + 20 * b for a, b in zip(r1, r2)]
            # pick
            i_new = max(range(len(sets)), key=lambda i: (new_confs[i], -sets[i]["set_no"]))
            i_old = max(range(len(sets)), key=lambda i: (sets[i]["conf"], -sets[i]["set_no"]))
            pick_new.append(sets[i_new]["match"])
            pick_orig.append(sets[i_old]["match"])

            for nc, s in zip(new_confs, sets):
                confs.append(nc)
                matches.append(float(s["match"]))
                all_new_conf.append(nc)
                all_match.append(float(s["match"]))
                bins[max(0, min(9, int(nc // 10)))] += 1

        occupied = sum(1 for b in bins if b > 0)
        r = spearman(confs, matches)
        per_brain[tag] = {
            "spearman_r": r,
            "bin_occupied": occupied,
            "bins_n": bins,
            "n": len(confs),
        }

    spearman_ge2 = sum(1 for t in BRAINS if per_brain[t]["spearman_r"] > 0.05) >= 2
    bin_spread = max(per_brain[t]["bin_occupied"] for t in BRAINS)
    s_new = summarize(pick_new)
    s_orig = summarize(pick_orig)
    # cross RR compare: use mean of per-draw max-new across brains? use pool mean vs RR
    # Instruction: delta_vs_rr — use cross pick by max new_conf among brains one ticket
    # Approximate: compare s_new mean (3 tickets/draw pooled) is unfair vs RR 1.74
    # Better: one ticket = RR-style cycle brain with max new_conf set
    cross_new: list[int] = []
    eval_i = 0
    for d in complete:
        if d < MIN_TRAIN + 1:
            continue
        # reuse stored picks roughly: take markov/stat/review rotating with new_conf pick already in loop — recompute light
        tag = BRAINS[eval_i % 3]
        # fall back: use that brain's sets max orig for structure — need new conf again
        # simpler: use best of three pick_new already sequential — instead rebuild quick
        hist = [draw_by_no[x] for x in ordered if x < d]
        if len(hist) < 2:
            continue
        sets = by_rev[d][tag]
        # use orig conf as weak stand-in only if empty
        if not sets:
            continue
        # score with same formula fragment: use stored conf rank within set as proxy if needed
        # Full recompute for one brain:
        if tag == "stat":
            pv = get_statistical_prob_vector(hist)
            s1 = [sum(pv.get(n, 0) for n in s["nums"]) for s in sets]
            s2 = [sum(1.0 - pv.get(n, 0) for n in s["nums"]) for s in sets]
        elif tag == "markov":
            pv = get_markov_prob_vector(hist)
            s1 = [sum(pv.get(n, 0) for n in s["nums"]) for s in sets]
            s2 = s1[:]
        else:
            recent = hist[-10:]
            recent_cnt: dict[int, int] = defaultdict(int)
            for row in recent:
                for k in range(1, 7):
                    recent_cnt[int(row[f"num{k}"])] += 1
            carry = set(int(hist[-1][f"num{k}"]) for k in range(1, 7))
            s1 = [sum(recent_cnt.get(n, 0) for n in s["nums"]) for s in sets]
            s2 = [len(set(s["nums"]) & carry) for s in sets]
        r1, r2 = _rank01(s1), _rank01(s2)
        new_confs = [50 + 30 * a + 20 * b for a, b in zip(r1, r2)]
        i = max(range(len(sets)), key=lambda j: new_confs[j])
        cross_new.append(sets[i]["match"])
        eval_i += 1

    s_cross = summarize(cross_new)
    delta_vs_rr = round(s_cross["mean"] - RR_MEAN, 4)
    passed = bin_spread >= 3 and spearman_ge2
    # PASS conditions don't require beating RR for C, only bin+spearman
    return {
        "bin_spread": bin_spread,
        "spearman_by_brain": {t: per_brain[t]["spearman_r"] for t in BRAINS},
        "spearman_r_ge2": spearman_ge2,
        "per_brain": per_brain,
        "within_new_conf": s_new,
        "within_orig_conf": s_orig,
        "delta_new_vs_orig_mean": round(s_new["mean"] - s_orig["mean"], 4),
        "cross_rr_style": s_cross,
        "delta_vs_rr": delta_vs_rr,
        "pass": passed,
        "verdict": "유망" if passed else "관측종료",
    }


def main() -> None:
    t0 = time.perf_counter()
    draws = load_draws()
    by_rev, _meta = load_reviews()

    print("lever A…")
    a = survey_lever_a(draws, by_rev)
    print("A", a["verdict"], a["overlap_spearman_r"])

    print("lever B…")
    b = survey_lever_b(draws)
    print("B", b["verdict"], b["best_combo"], b["best_mean"])

    print("lever C…")
    c = survey_lever_c(draws, by_rev)
    print("C", c["verdict"], c["spearman_by_brain"], c["bin_spread"])

    # first PASS in order A→B→C
    recommended_next = "없음"
    recommended_id = "없음"
    if a.get("pass"):
        recommended_next = "A"
        recommended_id = "K-ANALOG-ACTIVATE"
    elif b.get("pass"):
        recommended_next = "B"
        recommended_id = "K-MARKOV-TUNE"
    elif c.get("pass"):
        recommended_next = "C"
        recommended_id = "K-CONF-REBUILD"

    out = {
        "id": "K-ATTACK-OPEN",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.perf_counter() - t0, 1),
        "lever_a_analog": a,
        "lever_b_markov_tune": b,
        "lever_c_conf_rebuild": c,
        "recommended_next": recommended_next,
        "recommended_id": recommended_id,
        "selection_rule": "first PASS in order A→B→C",
        "db_code_write": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "recommended_next": recommended_next,
        "recommended_id": recommended_id,
        "A": {"r": a["overlap_spearman_r"], "v": a["verdict"]},
        "B": {"best": b["best_combo"], "mean": b["best_mean"], "v": b["verdict"]},
        "C": {"spread": c["bin_spread"], "sp": c["spearman_by_brain"], "v": c["verdict"]},
        "sec": out["elapsed_sec"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
