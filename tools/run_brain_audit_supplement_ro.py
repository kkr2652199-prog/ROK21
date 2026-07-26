# -*- coding: utf-8 -*-
"""뇌감사 보충: review-stat diff CI, learn_state 시점, 매출정규화 상관."""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.learn_state import load_learn_state  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from tools.run_set_picker_wf import _load_tagged_sets  # noqa: E402

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260726_뇌감사_비인기검증"
SEED = 20260726


def bootstrap_diff(a, b, n_boot=4000, seed=SEED):
    rng = random.Random(seed)
    n = min(len(a), len(b))
    diffs = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        diffs.append(sum(a[i] for i in idx) / n - sum(b[i] for i in idx) / n)
    diffs.sort()
    return {
        "mean_diff": round(sum(a[:n]) / n - sum(b[:n]) / n, 6),
        "ci95": [round(diffs[int(0.025 * n_boot)], 6), round(diffs[int(0.975 * n_boot)], 6)],
        "includes_0": diffs[int(0.025 * n_boot)] <= 0 <= diffs[int(0.975 * n_boot)],
    }


def hit_mean(sets, actual):
    return sum(len(set(s) & set(actual)) for s in sets) / max(1, len(sets))


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    da = math.sqrt(sum((x - mx) ** 2 for x in xs))
    db = math.sqrt(sum((y - my) ** 2 for y in ys))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def main():
    init_testlotto_db()
    tagged = _load_tagged_sets()
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    draws = [dict(zip([c[0] for c in conn.execute("PRAGMA table_info(lotto_draws)")], row)) for row in conn.execute("SELECT * FROM lotto_draws ORDER BY draw_no")]
    # simpler
    conn.row_factory = sqlite3.Row
    draws = [dict(r) for r in conn.execute("SELECT * FROM lotto_draws ORDER BY draw_no")]
    use = [d for d in draws if len(tagged.get(int(d["draw_no"]), [])) >= 5][-100:]

    by_brain = defaultdict(list)
    for d in use:
        actual = sorted_nums(d)
        buckets = defaultdict(list)
        for e in tagged[int(d["draw_no"])]:
            buckets[e["brain"]].append(e["nums"])
        for b, ss in buckets.items():
            by_brain[b].append(hit_mean(ss, actual))

    diffs = {
        "review_minus_stat": bootstrap_diff(by_brain["review"], by_brain["stat"]),
        "review_minus_markov": bootstrap_diff(by_brain["review"], by_brain["markov"]),
        "stat_minus_markov": bootstrap_diff(by_brain["stat"], by_brain["markov"]),
        "review_minus_0p8": bootstrap_diff(by_brain["review"], [0.8] * len(by_brain["review"])),
        "stat_minus_0p8": bootstrap_diff(by_brain["stat"], [0.8] * len(by_brain["stat"])),
        "markov_minus_0p8": bootstrap_diff(by_brain["markov"], [0.8] * len(by_brain["markov"])),
    }

    # coverage ablation unique delta
    from tools.run_brain_audit_unpopular_ro import ablation_last_n

    abl = ablation_last_n(tagged, draws, 100)
    # unique bootstrap diffs vs all3
    configs_sets = {}
    from collections import defaultdict as dd

    rows_u = {k: [] for k in ("all3", "no_stat", "no_markov", "no_review")}
    for d in use:
        by = dd(list)
        for e in tagged[int(d["draw_no"])]:
            by[e["brain"]].append(e["nums"])
        mapping = {
            "all3": ("stat", "markov", "review"),
            "no_stat": ("markov", "review"),
            "no_markov": ("stat", "review"),
            "no_review": ("stat", "markov"),
        }
        for name, brains in mapping.items():
            sets = []
            for b in brains:
                sets.extend(by.get(b, []))
            rows_u[name].append(float(len(set().union(*[set(s) for s in sets]))))
    cov_diff = {
        name: bootstrap_diff(rows_u[name], rows_u["all3"], seed=SEED + 3)
        for name in ("no_stat", "no_markov", "no_review")
    }

    learn = {tag: load_learn_state(tag) for tag in ("stat", "markov", "review")}
    learn_summary = {
        tag: {
            "last_draw_no": s.get("last_draw_no"),
            "review_count": s.get("review_count"),
            "recent_avg_match": s.get("recent_avg_match"),
            "adjustments": s.get("adjustments"),
        }
        for tag, s in learn.items()
    }

    # sales-normalized correlations for tier3
    rows = conn.execute(
        """
        SELECT d.draw_no, d.num1,d.num2,d.num3,d.num4,d.num5,d.num6,
               d.total_sales, t.winner_count, t.prize_per_game
        FROM lotto_draws d
        JOIN testlotto_draw_prize_tiers t ON t.draw_no=d.draw_no AND t.tier_rank=3
        WHERE IFNULL(t.winner_count,0)>0 AND IFNULL(d.total_sales,0)>0
        ORDER BY d.draw_no
        """
    ).fetchall()
    conn.close()

    ys_raw = [math.log(int(r[8])) for r in rows]
    ys_norm = [math.log(int(r[8]) / float(r[7])) for r in rows]  # winners per won sales
    feats = {"n_le31": [], "n_le12": [], "consec_pairs": [], "odd_count": [], "sum_nums": [], "carry_from_prev": []}
    prev = None
    for r in rows:
        nums = sorted(int(x) for x in r[1:7])
        feats["n_le31"].append(sum(1 for x in nums if x <= 31))
        feats["n_le12"].append(sum(1 for x in nums if x <= 12))
        feats["consec_pairs"].append(sum(1 for i in range(5) if nums[i + 1] == nums[i] + 1))
        feats["odd_count"].append(sum(1 for x in nums if x % 2))
        feats["sum_nums"].append(sum(nums))
        feats["carry_from_prev"].append(0 if prev is None else len(set(nums) & set(prev)))
        prev = nums

    n = len(ys_raw)
    thresh = 1.96 / math.sqrt(max(1, n - 3))
    corr = {}
    for name, xs in feats.items():
        xf = [float(x) for x in xs]
        r_raw = pearson(xf, ys_raw)
        r_norm = pearson(xf, ys_norm)
        corr[name] = {
            "r_log_winners": round(r_raw, 6),
            "r_log_winners_per_sales": round(r_norm, 6),
            "sig_raw": abs(r_raw) > thresh,
            "sig_norm": abs(r_norm) > thresh,
            "thresh": round(thresh, 6),
        }

    # effect with sales-norm strongest
    sig_norm = [k for k, v in corr.items() if v["sig_norm"]]
    effect_norm = None
    if sig_norm:
        best = max(sig_norm, key=lambda k: abs(corr[k]["r_log_winners_per_sales"]))
        xs = feats[best]
        paired = sorted(
            zip(
                xs,
                [int(r[8]) for r in rows],
                [float(r[9] or 0) for r in rows],
                [float(r[7]) for r in rows],
            )
        )
        q = max(1, len(paired) // 5)
        rsign = corr[best]["r_log_winners_per_sales"]
        low, high = paired[:q], paired[-q:]
        unpop, pop = (low, high) if rsign > 0 else (high, low)
        avg_p_u = sum(p for _, _, p, _ in unpop) / len(unpop)
        avg_p_p = sum(p for _, _, p, _ in pop) / len(pop)
        effect_norm = {
            "feature": best,
            "r_norm": corr[best]["r_log_winners_per_sales"],
            "unpop_avg_prize": round(avg_p_u, 2),
            "pop_avg_prize": round(avg_p_p, 2),
            "prize_ratio": round(avg_p_u / avg_p_p, 4) if avg_p_p else None,
            "unpop_avg_winners": round(sum(w for _, w, _, _ in unpop) / len(unpop), 2),
            "pop_avg_winners": round(sum(w for _, w, _, _ in pop) / len(pop), 2),
        }

    # filter pass-fail bootstrap
    from app.testlotto.filters import tier1_filter

    rng = random.Random(SEED)
    pass_h, fail_h = [], []
    for d in draws[-100:]:
        actual = sorted_nums(d)
        for _ in range(50):
            s = sorted(rng.sample(range(1, 46), 6))
            h = len(set(s) & set(actual))
            (pass_h if tier1_filter(s) else fail_h).append(h)
    # resample equal length comparison of means
    rng2 = random.Random(SEED + 1)
    n_min = min(len(pass_h), len(fail_h))
    diffs_f = []
    for _ in range(3000):
        mp = sum(pass_h[rng2.randrange(len(pass_h))] for _ in range(n_min)) / n_min
        mf = sum(fail_h[rng2.randrange(len(fail_h))] for _ in range(n_min)) / n_min
        diffs_f.append(mp - mf)
    diffs_f.sort()

    out = {
        "brain_mean_diffs": diffs,
        "coverage_unique_delta_vs_all3": cov_diff,
        "learn_state_now": learn_summary,
        "sales_normalized_corr": corr,
        "sig_norm_vars": sig_norm,
        "effect_norm": effect_norm,
        "filter_pass_minus_fail_ci": {
            "mean_pass": round(sum(pass_h) / len(pass_h), 6),
            "mean_fail": round(sum(fail_h) / len(fail_h), 6) if fail_h else None,
            "diff_ci95": [round(diffs_f[int(0.025 * 3000)], 6), round(diffs_f[int(0.975 * 3000)], 6)],
            "includes_0": diffs_f[int(0.025 * 3000)] <= 0 <= diffs_f[int(0.975 * 3000)],
        },
        "ablation_table": abl["table"],
        "leak_judgment_notes": {
            "draws_path": "coordinator/walkforward → _get_draws_before(target) → predict_sets(draws) — draws 누수 없음(코드)",
            "learn_state_path": "load_learn_state는 draw cutoff 없이 전역 1행. 과거 회차 재생성 시 미래 피드백 오염 가능",
            "stored_sets": "본 감사 A2/A3는 저장 tagged 세트 기준 — 생성 당시 시점 오염 여부는 미확인",
            "review_vs_0p8": "CI가 0을 포함하면 mean 우위 미입증",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    OUT.joinpath("audit_supplement.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
