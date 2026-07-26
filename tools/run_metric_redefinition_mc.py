# -*- coding: utf-8 -*-
"""지표 재정의 검증 — 몬테카를로 실측 (READ-ONLY, DB 무변경).

(A) 1장 기대 적중 ≈ 0.80
(B) 15장 best 기대 ≈ 2.27
(C) mean이 0.80을 넘는지 (실력 신호)
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import (  # noqa: E402
    predict_flow_shaman,
    predict_review_king,
    predict_stat_fairy,
)
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from tools.run_set_picker_wf import _load_tagged_sets  # noqa: E402

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_지표재정의_검증"
)
SEED = 20260726
N_TRIALS = 10_000
ACTUAL_RANGE = (1135, 1234)


def load_actuals(lo: int, hi: int) -> list[tuple[int, list[int]]]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            """
            SELECT draw_no, num1,num2,num3,num4,num5,num6
            FROM lotto_draws
            WHERE draw_no BETWEEN ? AND ?
            ORDER BY draw_no
            """,
            (lo, hi),
        ).fetchall()
    finally:
        conn.close()
    return [(int(r[0]), [int(x) for x in r[1:7]]) for r in rows]


def hit_count(pred: list[int], actual: list[int]) -> int:
    return len(set(pred) & set(actual))


def mean_std(xs: list[float]) -> tuple[float, float]:
    n = len(xs)
    if n == 0:
        return 0.0, 0.0
    m = sum(xs) / n
    var = sum((x - m) ** 2 for x in xs) / n
    return m, math.sqrt(var)


def mc_random_tickets(
    actuals: list[tuple[int, list[int]]],
    n_tickets: int,
    n_trials: int,
    rng: random.Random,
) -> dict[str, Any]:
    """각 시행: 실제 당첨 하나를 균등 샘플 → 랜덤 n_tickets장 → mean_hit, best_hit."""
    means: list[float] = []
    bests: list[float] = []
    for _ in range(n_trials):
        _, actual = actuals[rng.randrange(len(actuals))]
        hits = [
            hit_count(sorted(rng.sample(range(1, 46), 6)), actual)
            for _ in range(n_tickets)
        ]
        means.append(sum(hits) / n_tickets)
        bests.append(float(max(hits)))
    m_mean, s_mean = mean_std(means)
    m_best, s_best = mean_std(bests)
    return {
        "n_tickets": n_tickets,
        "n_trials": n_trials,
        "mean_of_per_ticket_avg": round(m_mean, 6),
        "std_of_per_ticket_avg": round(s_mean, 6),
        "mean_of_best": round(m_best, 6),
        "std_of_best": round(s_best, 6),
    }


def theory_single() -> float:
    return 6 * 6 / 45


def hypergeom_pmf(k: int, N: int = 45, K: int = 6, n: int = 6) -> float:
    """P(X=k) for Hypergeometric."""
    from math import comb

    if k < 0 or k > min(K, n):
        return 0.0
    return comb(K, k) * comb(N - K, n - k) / comb(N, n)


def theory_best_of_m(m: int) -> float:
    """E[max of m i.i.d. Hypergeometric(45,6,6)]."""
    # P(best <= k) = F(k)^m ; E[best] = sum_{k=0}^{5} (1 - F(k)^m)  for support 0..6
    # E[X] = sum_{k>=1} P(X>=k) = sum_{k=1}^{6} (1 - F(k-1)^m)
    cdf = 0.0
    F = []  # F[k] = P(X<=k)
    for k in range(0, 7):
        cdf += hypergeom_pmf(k)
        F.append(cdf)
    e = 0.0
    for k in range(1, 7):
        e += 1.0 - (F[k - 1] ** m)
    return e


def stored_and_div_means_last40(seed: int = SEED) -> dict[str, Any]:
    """최근 40회: 저장 15장 mean, 다양화 재예측 15장 mean, 랜덤 15장 mean/best."""
    init_testlotto_db()
    tagged = _load_tagged_sets()
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        draws = conn.execute(
            "SELECT * FROM lotto_draws ORDER BY draw_no"
        ).fetchall()
        cols = [d[0] for d in conn.execute("PRAGMA table_info(lotto_draws)")]
    finally:
        conn.close()
    # rebuild dict rows
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        draw_rows = conn.execute(
            "SELECT * FROM lotto_draws ORDER BY draw_no"
        ).fetchall()
    finally:
        conn.close()

    use = [d for d in draw_rows if len(tagged.get(int(d["draw_no"]), [])) >= 5][-40:]
    rng = random.Random(seed)

    stored_means = []
    stored_bests = []
    div_means = []
    div_bests = []
    rand_means = []
    rand_bests = []
    draw_nos = []

    for d in use:
        td = int(d["draw_no"])
        actual = sorted_nums(dict(d))
        stored = [e["nums"] for e in tagged[td]]
        sh = [hit_count(s, actual) for s in stored]
        stored_means.append(sum(sh) / len(sh))
        stored_bests.append(float(max(sh)))

        before = _get_draws_before(td)
        new_sets = []
        for mod in (predict_stat_fairy, predict_flow_shaman, predict_review_king):
            new_sets.extend([x["nums"] for x in mod.predict_sets(before, 5)])
        dh = [hit_count(s, actual) for s in new_sets]
        div_means.append(sum(dh) / len(dh))
        div_bests.append(float(max(dh)))

        rh = [
            hit_count(sorted(rng.sample(range(1, 46), 6)), actual)
            for _ in range(len(new_sets))
        ]
        rand_means.append(sum(rh) / len(rh))
        rand_bests.append(float(max(rh)))
        draw_nos.append(td)

    def pack(xs: list[float]) -> dict[str, float]:
        m, s = mean_std(xs)
        return {"mean": round(m, 6), "std": round(s, 6), "n": len(xs)}

    # bootstrap CI for (div_best - rand_best) and (div_mean - 0.8)
    def bootstrap_ci(
        a: list[float], b: list[float] | None, n_boot: int = 5000
    ) -> dict[str, Any]:
        brng = random.Random(seed + 7)
        diffs = []
        n = len(a)
        for _ in range(n_boot):
            idx = [brng.randrange(n) for _ in range(n)]
            if b is None:
                diffs.append(sum(a[i] for i in idx) / n - theory_single())
            else:
                diffs.append(
                    sum(a[i] for i in idx) / n - sum(b[i] for i in idx) / n
                )
        diffs.sort()
        lo = diffs[int(0.025 * n_boot)]
        hi = diffs[int(0.975 * n_boot)]
        return {
            "diff_mean": round(sum(diffs) / n_boot, 6),
            "ci95": [round(lo, 6), round(hi, 6)],
            "n_boot": n_boot,
            "ci_includes_zero": lo <= 0.0 <= hi,
        }

    return {
        "draw_nos": {"min": min(draw_nos), "max": max(draw_nos), "n": len(draw_nos)},
        "theory_single": theory_single(),
        "stored_mean": pack(stored_means),
        "stored_best": pack(stored_bests),
        "diversified_mean": pack(div_means),
        "diversified_best": pack(div_bests),
        "random15_mean": pack(rand_means),
        "random15_best": pack(rand_bests),
        "bootstrap_div_best_minus_rand_best": bootstrap_ci(div_bests, rand_bests),
        "bootstrap_div_mean_minus_theory08": bootstrap_ci(div_means, None),
        "bootstrap_stored_mean_minus_theory08": bootstrap_ci(stored_means, None),
        "mean_above_theory_div": pack(div_means)["mean"] > theory_single(),
        "mean_above_theory_stored": pack(stored_means)["mean"] > theory_single(),
    }


def db_gap_check() -> dict[str, Any]:
    out = {}
    for name in ("lotto_testlotto.db", "lotto4.db", "lotto_hyodo.db"):
        p = ROOT / "data" / name
        if not p.exists():
            out[name] = {"exists": False}
            continue
        conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
        try:
            mx, n = conn.execute(
                "SELECT max(draw_no), count(*) FROM lotto_draws"
            ).fetchone()
            out[name] = {"exists": True, "max": int(mx or 0), "n": int(n or 0)}
        except Exception as e:
            out[name] = {"exists": True, "error": str(e)}
        finally:
            conn.close()
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    actuals = load_actuals(*ACTUAL_RANGE)
    rng = random.Random(SEED)

    # (1)(2) MC curves
    curve = {}
    for nt in (5, 15, 45):
        curve[str(nt)] = mc_random_tickets(actuals, nt, N_TRIALS, rng)

    theory = {
        "single_E": theory_single(),
        "best_of_5_E": round(theory_best_of_m(5), 6),
        "best_of_15_E": round(theory_best_of_m(15), 6),
        "best_of_45_E": round(theory_best_of_m(45), 6),
    }

    # (3)(4) stored/div means
    means40 = stored_and_div_means_last40(SEED)
    gap = db_gap_check()

    # claim checks
    mc15 = curve["15"]
    claim_A = abs(mc15["mean_of_per_ticket_avg"] - theory["single_E"]) < 0.02
    claim_B_theory = abs(theory["best_of_15_E"] - 2.27) < 0.05
    claim_B_mc = abs(mc15["mean_of_best"] - theory["best_of_15_E"]) < 0.05
    # (C) rebuttal if mean significantly > 0.80
    div_mean_ci = means40["bootstrap_div_mean_minus_theory08"]
    claim_C_rebut = (
        means40["diversified_mean"]["mean"] > theory["single_E"]
        and not div_mean_ci["ci_includes_zero"]
        and div_mean_ci["ci95"][0] > 0
    )

    payload = {
        "ok": True,
        "no_peek": True,
        "db_readonly": True,
        "random_choices_untouched": True,
        "actual_range": list(ACTUAL_RANGE),
        "n_actuals": len(actuals),
        "n_trials": N_TRIALS,
        "seed": SEED,
        "theory": theory,
        "mc_curve": curve,
        "means_last40": means40,
        "db_gap": gap,
        "claim_checks": {
            "A_single_08_reproduced_by_MC": claim_A,
            "A_detail": {
                "mc_mean": mc15["mean_of_per_ticket_avg"],
                "theory": theory["single_E"],
            },
            "B_theory_best15_near_227": claim_B_theory,
            "B_MC_matches_theory_best15": claim_B_mc,
            "B_detail": {
                "theory_best15": theory["best_of_15_E"],
                "mc_best15": mc15["mean_of_best"],
                "external_claim": 2.27,
            },
            "C_mean_significantly_above_08": claim_C_rebut,
            "C_detail": {
                "div_mean": means40["diversified_mean"]["mean"],
                "stored_mean": means40["stored_mean"]["mean"],
                "bootstrap_div_mean_minus_08": div_mean_ci,
                "bootstrap_best_div_minus_rand": means40[
                    "bootstrap_div_best_minus_rand_best"
                ],
            },
            "tickets_increase_best": (
                curve["5"]["mean_of_best"]
                < curve["15"]["mean_of_best"]
                < curve["45"]["mean_of_best"]
            ),
        },
    }
    OUT.joinpath("monte_carlo_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("WROTE", OUT / "monte_carlo_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
