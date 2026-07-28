# -*- coding: utf-8 -*-
"""K-ATTACK-BAYES — 3뇌 예측벡터 rolling 상관 → inv-corr 동적가중 (READ-ONLY).

설계:
  - 뇌별 예측벡터 = 5세트의 번호 출현 카운트 (길이 45)
  - 창=50: target 직전 50회만 (컨닝 금지)
  - 창 내 매회 뇌쌍 Pearson corr → 뇌 i의 avg_corr = 타뇌와 평균상관
  - w_i ∝ 1/(avg_corr_i + eps), 합=1
  - baseline = 고정가중 1/3
  - 발권 프록시:
      soft  — Σ w_i * best_set_match_i  (연속 점수)
      pick  — argmax w 뇌 best_set 1장
  - conf_pick — SLICE 힌트 대조: max confidence 뇌 1장

산출: docs/benchmarks/20260729_KBAYES_dyn_weight.json
"""
from __future__ import annotations

import json
import math
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KBAYES_dyn_weight.json"

BRAINS = ("stat", "markov", "review")
WINDOW = 50
EPS = 1e-3
D_LO, D_HI = 2, 1234


def pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n < 2 or n != len(b):
        return 0.0
    ma = sum(a) / n
    mb = sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    if da < 1e-12 or db < 1e-12:
        return 0.0
    return num / (da * db)


def vec45(sets: list[dict]) -> list[float]:
    v = [0.0] * 45
    for s in sets:
        for n in s.get("nums") or []:
            i = int(n)
            if 1 <= i <= 45:
                v[i - 1] += 1.0
    return v


def best_match(sets: list[dict], actual: set[int], best_set_no: int | None) -> tuple[int, float]:
    """return (matched_count, confidence) of best_set."""
    if not sets:
        return 0, 0.0
    chosen = None
    if best_set_no is not None:
        chosen = next(
            (s for s in sets if int(s.get("set_no") or 0) == int(best_set_no)),
            None,
        )
    if chosen is None:
        chosen = max(
            sets,
            key=lambda s: float(s.get("confidence") or 0),
            default=sets[0],
        )
    nums = set(int(n) for n in (chosen.get("nums") or []))
    return len(nums & actual), float(chosen.get("confidence") or 0)


def summarize(ms: list[float] | list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {"n": 0}
    vals = [float(x) for x in ms]
    ge3 = sum(1 for x in vals if x >= 3)
    ge4 = sum(1 for x in vals if x >= 4)
    return {
        "n": n,
        "mean": round(sum(vals) / n, 4),
        "ge3": ge3,
        "ge3_rate": round(ge3 / n, 4),
        "ge4": ge4,
        "ge4_rate": round(ge4 / n, 4),
        "ge5": sum(1 for x in vals if x >= 5),
        "ge6": sum(1 for x in vals if x >= 6),
    }


def delta(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    if not a.get("n") or not b.get("n"):
        return {}
    return {
        "mean": round(a["mean"] - b["mean"], 4),
        "ge3_rate": round(a["ge3_rate"] - b["ge3_rate"], 4),
        "ge4_rate": round(a["ge4_rate"] - b["ge4_rate"], 4),
    }


def inv_corr_weights(avg_corr: dict[str, float]) -> dict[str, float]:
    raw = {b: 1.0 / (avg_corr.get(b, 0.0) + EPS) for b in BRAINS}
    s = sum(raw.values()) or 1.0
    return {b: raw[b] / s for b in BRAINS}


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    draws = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (1, D_HI),
    ).fetchall()
    actuals = {
        int(r[0]): set(int(r[i]) for i in range(1, 7)) for r in draws
    }

    rows = con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json, best_set_no "
        "FROM testlotto_brain_review WHERE draw_no BETWEEN ? AND ?",
        (D_LO, D_HI),
    ).fetchall()
    con.close()

    # per draw → brain → {vec, match, conf}
    by_draw: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in rows:
        tag = r["brain_tag"]
        if tag not in BRAINS:
            continue
        d = int(r["draw_no"])
        try:
            sets = json.loads(r["predicted_sets_json"] or "[]")
        except Exception:
            sets = []
        m, conf = best_match(sets, actuals.get(d, set()), r["best_set_no"])
        by_draw[d][tag] = {
            "vec": vec45(sets),
            "match": m,
            "conf": conf,
        }

    # only draws with all 3 brains
    complete = sorted(d for d, br in by_draw.items() if all(b in br for b in BRAINS))

    soft_base: list[float] = []
    soft_dyn: list[float] = []
    pick_rr: list[int] = []
    pick_dyn: list[int] = []
    pick_conf: list[int] = []
    pick_by_brain: dict[str, list[int]] = {b: [] for b in BRAINS}
    weight_hist: list[dict[str, float]] = []
    corr_hist: list[dict[str, float]] = []
    pair_corr_sum = {"stat_markov": 0.0, "stat_review": 0.0, "markov_review": 0.0}
    pair_n = 0
    skipped_short_window = 0
    eval_i = 0

    for d in complete:
        prior = [x for x in complete if d - WINDOW <= x < d]
        if len(prior) < WINDOW:
            skipped_short_window += 1
            continue

        # avg pairwise corr per brain over window (vector corr each prior draw)
        sum_corr = {b: 0.0 for b in BRAINS}
        cnt = {b: 0 for b in BRAINS}
        for pd in prior:
            vecs = {b: by_draw[pd][b]["vec"] for b in BRAINS}
            pairs = [
                ("stat", "markov", "stat_markov"),
                ("stat", "review", "stat_review"),
                ("markov", "review", "markov_review"),
            ]
            local: dict[tuple[str, str], float] = {}
            for a, b, key in pairs:
                c = pearson(vecs[a], vecs[b])
                local[(a, b)] = c
                local[(b, a)] = c
                pair_corr_sum[key] += c
            pair_n += 1
            for b in BRAINS:
                others = [local[(b, o)] for o in BRAINS if o != b]
                sum_corr[b] += sum(others) / len(others)
                cnt[b] += 1

        avg_corr = {b: (sum_corr[b] / cnt[b] if cnt[b] else 0.0) for b in BRAINS}
        w_dyn = inv_corr_weights(avg_corr)
        w_base = {b: 1.0 / 3.0 for b in BRAINS}

        matches = {b: by_draw[d][b]["match"] for b in BRAINS}
        confs = {b: by_draw[d][b]["conf"] for b in BRAINS}

        soft_base.append(sum(w_base[b] * matches[b] for b in BRAINS))
        soft_dyn.append(sum(w_dyn[b] * matches[b] for b in BRAINS))

        rr_brain = BRAINS[eval_i % 3]
        pick_rr.append(matches[rr_brain])
        pick_dyn.append(
            matches[max(BRAINS, key=lambda b: (w_dyn[b], confs[b], -BRAINS.index(b)))]
        )
        pick_conf.append(matches[max(BRAINS, key=lambda b: (confs[b], -BRAINS.index(b)))])
        for b in BRAINS:
            pick_by_brain[b].append(matches[b])
        eval_i += 1

        weight_hist.append({b: round(w_dyn[b], 4) for b in BRAINS})
        corr_hist.append({b: round(avg_corr[b], 4) for b in BRAINS})

    n_eval = len(soft_dyn)
    mean_w = {
        b: round(sum(h[b] for h in weight_hist) / n_eval, 4) if n_eval else 0.0
        for b in BRAINS
    }
    mean_avg_corr = {
        b: round(sum(h[b] for h in corr_hist) / n_eval, 4) if n_eval else 0.0
        for b in BRAINS
    }
    mean_pair = {
        k: round(v / pair_n, 4) if pair_n else 0.0 for k, v in pair_corr_sum.items()
    }

    s_soft_base = summarize(soft_base)
    s_soft_dyn = summarize(soft_dyn)
    s_pick_rr = summarize(pick_rr)
    s_pick_dyn = summarize(pick_dyn)
    s_pick_conf = summarize(pick_conf)
    s_by_brain = {b: summarize(pick_by_brain[b]) for b in BRAINS}

    out = {
        "id": "K-ATTACK-BAYES",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "window": [D_LO, D_HI],
        "rolling_window": WINDOW,
        "brains": list(BRAINS),
        "method": {
            "vector": "45-dim count of nums across 5 predicted sets",
            "corr": "pearson(vec_i, vec_j) per prior draw, avg over WINDOW",
            "weight": "w_i ∝ 1/(avg_corr_i + eps), eps=1e-3",
            "no_peek": "weights from draws in [d-WINDOW, d)",
            "db_code_write": False,
        },
        "n_complete_draws": len(complete),
        "n_eval": n_eval,
        "skipped_short_window": skipped_short_window,
        "corr_summary": {
            "mean_avg_corr_per_brain": mean_avg_corr,
            "mean_pairwise_over_window_draws": mean_pair,
        },
        "weight_summary": {
            "mean_dyn_weight": mean_w,
            "baseline_weight": {b: round(1 / 3, 4) for b in BRAINS},
        },
        "policies": {
            "soft_equal": s_soft_base,
            "soft_invcorr": s_soft_dyn,
            "pick_round_robin": s_pick_rr,
            "pick_invcorr": s_pick_dyn,
            "pick_max_conf": s_pick_conf,
            "pick_single_brain": s_by_brain,
        },
        "delta_vs_baseline": {
            "soft_invcorr_minus_soft_equal": delta(s_soft_dyn, s_soft_base),
            "pick_invcorr_minus_round_robin": delta(s_pick_dyn, s_pick_rr),
            "pick_invcorr_minus_pick_max_conf": delta(s_pick_dyn, s_pick_conf),
        },
        "verdict_hint": {
            "note": (
                "soft≈null이면 가중 혼합은 무력. "
                "pick delta>0이면 저상관 뇌 1장 선택이 RR/conf 대비 이득. "
                "배선은 별도 GO."
            ),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "n_eval": n_eval,
        "delta_soft": out["delta_vs_baseline"]["soft_invcorr_minus_soft_equal"],
        "delta_pick_vs_rr": out["delta_vs_baseline"]["pick_invcorr_minus_round_robin"],
        "vs_conf": out["delta_vs_baseline"]["pick_invcorr_minus_pick_max_conf"],
        "mean_w": mean_w,
        "mean_pair": mean_pair,
        "pick_invcorr": s_pick_dyn,
        "pick_rr": s_pick_rr,
        "pick_conf": s_pick_conf,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
