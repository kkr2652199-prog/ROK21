# -*- coding: utf-8 -*-
"""K-STRUCT-SURVEY — 4보조 spearman · analog 구조유사 · AUX 가중 (READ-ONLY).

산출: docs/benchmarks/20260729_KSTRUCT_survey.json
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KSTRUCT_survey.json"
BRAINS = ("stat", "markov", "review")
D_LO, D_HI = 2, 1234
RR_MEAN = 1.7428


def spearman(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 5:
        return 0.0

    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
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
        return {"n": 0, "mean": 0.0, "ge3_rate": 0.0, "ge3": 0}
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
        SELECT draw_no, brain_tag, predicted_sets_json
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN ? AND ? AND brain_tag IN ('stat','markov','review')
        """,
        (D_LO, D_HI),
    ).fetchall()
    con.close()
    by: dict[int, dict[str, list[dict]]] = defaultdict(dict)
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
            if len(nums) < 6:
                continue
            parsed.append(
                {
                    "nums": nums,
                    "match": int(s["matched_count"]) if s.get("matched_count") is not None else 0,
                    "conf": float(s.get("confidence") or 0),
                    "set_no": int(s.get("set_no") or 0),
                }
            )
        if parsed:
            by[d][tag] = parsed
    return by


def composite(scores: dict[str, float], weights: dict[str, float]) -> float:
    return sum(weights[k] * scores[k] for k in weights)


def main() -> None:
    from app.testlotto.analog_service import (
        draw_nums,
        find_analogs,
        matched_count,
        predict_from_analogs,
    )
    from app.testlotto.brains import (
        aux_balance_keeper,
        aux_miss_detective,
        aux_pattern_spotlight,
    )
    from app.testlotto.learn_state import get_referee_weights
    from app.testlotto.learn_state_cutoff import (
        clear_history_cache,
        ensure_history_built,
        set_learn_as_of,
    )

    t0 = time.perf_counter()
    draws = load_draws()
    by_rev = load_reviews()
    draw_by_no = {int(d["draw_no"]): d for d in draws}
    ordered = [int(d["draw_no"]) for d in draws]

    clear_history_cache()
    ensure_history_built()

    # ── STEP 1 ──
    print("STEP1 aux spearman…")
    xs = {
        "aux_pattern": [],
        "aux_balance": [],
        "aux_miss": [],
        "aux_referee": [],
        "composite": [],
    }
    ys: list[float] = []
    # cache scored sets for step3: draw -> tag -> list[{scores, match}]
    scored_cache: dict[int, dict[str, list[dict]]] = defaultdict(dict)

    w_base = {
        "aux_pattern": 0.25,
        "aux_balance": 0.25,
        "aux_miss": 0.25,
        "aux_referee": 0.25,
    }

    complete = sorted(d for d, br in by_rev.items() if all(b in br for b in BRAINS))
    for d in complete:
        hist = [draw_by_no[x] for x in ordered if x < d]
        if len(hist) < 5:
            continue
        set_learn_as_of(d)
        try:
            ref_w = get_referee_weights()
        except Exception:
            ref_w = {b: 1 / 3 for b in BRAINS}

        for tag in BRAINS:
            rows = []
            for s in by_rev[d][tag]:
                nums = s["nums"]
                sp = {
                    "aux_pattern": aux_pattern_spotlight.score_set(
                        nums, hist, d, brain_tag=tag
                    ),
                    "aux_balance": aux_balance_keeper.score_set(
                        nums, hist, d, brain_tag=tag
                    ),
                    "aux_miss": aux_miss_detective.score_set(
                        nums, hist, d, brain_tag=tag
                    ),
                    # referee set-score is constant 0.5; use brain weight as meta-signal
                    "aux_referee": float(ref_w.get(tag, 1 / 3)),
                }
                for k in xs:
                    if k == "composite":
                        continue
                    xs[k].append(sp[k])
                comp = composite(sp, w_base)
                xs["composite"].append(comp)
                ys.append(float(s["match"]))
                rows.append({"scores": sp, "match": s["match"], "comp": comp})
            scored_cache[d][tag] = rows

    step1 = {
        "aux_pattern": spearman(xs["aux_pattern"], ys),
        "aux_balance": spearman(xs["aux_balance"], ys),
        "aux_miss": spearman(xs["aux_miss"], ys),
        "aux_referee": spearman(xs["aux_referee"], ys),
        "composite": spearman(xs["composite"], ys),
        "n_sets": len(ys),
        "note": "aux_referee=brain_w(get_referee_weights); score_set은 상수0.5",
    }
    print("STEP1", step1)

    # ── STEP 2 ──
    print("STEP2 analog…")
    methods = ("M_freq", "M_weighted", "M_chain8")
    analog_ms: dict[str, list[int]] = {m: [] for m in methods}
    analog_aux_ms: list[int] = []

    for d in complete:
        if d < 100:
            continue
        prev = draw_by_no.get(d - 1)
        if not prev:
            continue
        hist = [draw_by_no[x] for x in ordered if x < d - 1]
        if len(hist) < 30:
            continue
        base = draw_nums(prev)
        analogs = find_analogs(base, hist, top_k=15)
        actual = [int(draw_by_no[d][f"num{k}"]) for k in range(1, 7)]
        preds = {}
        for m in methods:
            pred = predict_from_analogs(
                base, analogs, draw_by_no, m, target_draw_no=d
            )
            preds[m] = pred
            analog_ms[m].append(matched_count(pred, actual))

        # aux filter: among 3 methods, pick highest pattern+balance avg
        set_learn_as_of(d)
        hist_d = [draw_by_no[x] for x in ordered if x < d]
        best_m = None
        best_sc = -1.0
        for m, pred in preds.items():
            sc = 0.5 * aux_pattern_spotlight.score_set(pred, hist_d, d)
            sc += 0.5 * aux_balance_keeper.score_set(pred, hist_d, d)
            if sc > best_sc:
                best_sc = sc
                best_m = m
        analog_aux_ms.append(matched_count(preds[best_m], actual))

    step2_methods = {m: summarize(analog_ms[m]) for m in methods}
    step2_aux = summarize(analog_aux_ms)
    best_analog_mean = max(step2_methods[m]["mean"] for m in methods)
    step2 = {
        **{m: step2_methods[m] for m in methods},
        "analog_plus_aux_filter": step2_aux,
        "delta_vs_rr": round(best_analog_mean - RR_MEAN, 4),
        "delta_aux_vs_rr": round(step2_aux["mean"] - RR_MEAN, 4),
    }
    print("STEP2", {k: (v.get("mean") if isinstance(v, dict) else v) for k, v in step2.items()})

    # ── STEP 3 ──
    print("STEP3 weight combos…")
    combos = {
        "baseline": w_base,
        "combo_A": {
            "aux_pattern": 0.40,
            "aux_balance": 0.40,
            "aux_miss": 0.10,
            "aux_referee": 0.10,
        },
        "combo_B": {
            "aux_pattern": 0.35,
            "aux_balance": 0.35,
            "aux_miss": 0.20,
            "aux_referee": 0.10,
        },
        "combo_C": {
            "aux_pattern": 0.30,
            "aux_balance": 0.30,
            "aux_miss": 0.20,
            "aux_referee": 0.20,
        },
    }

    step3_out: dict[str, Any] = {}
    for name, w in combos.items():
        picks: list[int] = []
        for d, tags in scored_cache.items():
            for tag in BRAINS:
                rows = tags.get(tag) or []
                if not rows:
                    continue
                best = max(
                    rows,
                    key=lambda r: (
                        composite(r["scores"], w),
                        -r.get("match", 0),
                    ),
                )
                picks.append(best["match"])
        step3_out[name] = summarize(picks)

    best_combo = max(step3_out, key=lambda k: (step3_out[k]["mean"], step3_out[k]["ge3_rate"]))
    base_mean = step3_out["baseline"]["mean"]
    step3 = {
        **step3_out,
        "best_combo": best_combo,
        "delta_best_vs_baseline": round(step3_out[best_combo]["mean"] - base_mean, 4),
    }
    print("STEP3", {k: v.get("mean") if isinstance(v, dict) else v for k, v in step3.items()})

    # ── verdict ──
    pass1 = step1["composite"] > 0.03
    pass2 = step2["delta_vs_rr"] > 0 or step2["delta_aux_vs_rr"] > 0
    pass3 = best_combo != "baseline" and step3["delta_best_vs_baseline"] > 0.01

    recommended = "없음"
    if pass1 or pass3:
        recommended = "K-AUX-REWEIGHT"
    elif pass2:
        recommended = "K-ANALOG-3뇌결합"

    # prefer stronger signal if both
    if pass1 and pass2:
        recommended = "K-AUX-REWEIGHT" if step1["composite"] >= 0.03 else "K-ANALOG-3뇌결합"
    if pass3 and not pass1 and not pass2:
        recommended = "K-AUX-REWEIGHT"

    verdict = "유망" if recommended != "없음" else "관측종료"

    out = {
        "id": "K-STRUCT-SURVEY",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.perf_counter() - t0, 1),
        "step1_aux_spearman": step1,
        "step2_analog": step2,
        "step3_aux_weight": step3,
        "gates": {
            "step1_composite_gt_003": pass1,
            "step2_delta_vs_rr_gt0": pass2,
            "step3_best_not_baseline_delta_gt_001": pass3,
        },
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "step1": step1,
                "step2_means": {m: step2[m]["mean"] for m in methods},
                "step2_aux": step2_aux["mean"],
                "delta_vs_rr": step2["delta_vs_rr"],
                "step3_best": best_combo,
                "step3_delta": step3["delta_best_vs_baseline"],
                "recommended": recommended,
                "verdict": verdict,
                "sec": out["elapsed_sec"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
