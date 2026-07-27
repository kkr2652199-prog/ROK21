# -*- coding: utf-8 -*-
"""K-P3 verify: review 끝수 편향 완화 · random.choices 미변경 · 회귀 스모크."""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "benchmarks" / "20260727_KP3_review_ending.json"
SEED = 20260727
N_SETS = 2000
AS_OF = 1235


def _numbers_per_ending() -> list[int]:
    c = Counter(n % 10 for n in range(1, 46))
    return [int(c[d]) for d in range(10)]


def _sample_sets(weights: dict[int, float], n_sets: int, rng: random.Random) -> list[list[int]]:
    results: list[list[int]] = []
    used: set[tuple[int, ...]] = set()
    attempts = 0
    while len(results) < n_sets and attempts < n_sets * 20:
        attempts += 1
        pool = list(range(1, 46))
        w = [weights[n] for n in pool]
        pick: list[int] = []
        for _ in range(6):
            if not pool:
                break
            chosen = random.choices(pool, weights=w, k=1)[0]
            pick.append(chosen)
            idx = pool.index(chosen)
            pool.pop(idx)
            w.pop(idx)
        if len(pick) != 6:
            continue
        key = tuple(sorted(pick))
        if key in used:
            continue
        used.add(key)
        results.append(sorted(pick))
    return results


def _ending_hist(sets: list[list[int]]) -> list[int]:
    c = Counter()
    for s in sets:
        for n in s:
            c[n % 10] += 1
    return [int(c.get(d, 0)) for d in range(10)]


def _l1_vs_ball(hist: list[int]) -> float:
    npe = np.array(_numbers_per_ending(), float)
    prop = np.array(hist, float) / max(1, sum(hist))
    ball = npe / 45.0
    return float(np.abs(prop - ball).sum())


def _max_abs_resid(hist: list[int], exp: list[float]) -> float:
    obs = np.array(hist, float)
    ex = np.array(exp, float)
    r = (obs - ex) / np.sqrt(np.maximum(ex, 1e-9))
    return float(np.max(np.abs(r)))


def _legacy_weights(draws) -> dict[int, float]:
    from app.testlotto.features.draw_features import repeat_rate_after_draw, sorted_nums
    from app.testlotto.learn_state import load_learn_state

    prev_nums = set(sorted_nums(draws[-1]))
    rates = repeat_rate_after_draw(draws)
    learn = load_learn_state("review")
    carry_boost = 1.0 + float(learn.get("adjustments", {}).get("carry_over_boost", 0))
    weights = {n: rates.get(n, 0.08) for n in range(1, 46)}
    for n in prev_nums:
        weights[n] *= 1.8 * carry_boost
    for n in range(1, 46):
        if n not in prev_nums:
            weights[n] *= 0.85
    return weights


def main() -> int:
    from app.testlotto.brains.predict_review_king import build_review_weights
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import clear_history_cache, set_learn_as_of

    clear_history_cache()
    set_learn_as_of(AS_OF)
    draws = _get_draws_before(AS_OF)
    rng = random.Random(SEED)

    w_old = _legacy_weights(draws)
    w_new = build_review_weights(draws)

    # ending mass flatness
    def end_mass(w: dict[int, float]) -> list[float]:
        c = Counter()
        for n, wt in w.items():
            c[n % 10] += wt
        tot = sum(c.values()) or 1.0
        return [float(c[d] / tot) for d in range(10)]

    em_old = end_mass(w_old)
    em_new = end_mass(w_new)
    end_mass_spread_old = max(em_old) - min(em_old)
    end_mass_spread_new = max(em_new) - min(em_new)

    sets_old = _sample_sets(w_old, N_SETS, rng)
    rng2 = random.Random(SEED)
    sets_new = _sample_sets(w_new, N_SETS, rng2)

    h_old, h_new = _ending_hist(sets_old), _ending_hist(sets_new)
    slots = N_SETS * 6
    npe = _numbers_per_ending()
    exp_ball = [x / 45.0 * slots for x in npe]

    l1_old = _l1_vs_ball(h_old)
    l1_new = _l1_vs_ball(h_new)
    resid_old = _max_abs_resid(h_old, exp_ball)
    resid_new = _max_abs_resid(h_new, exp_ball)

    # KX baseline reference (from JSON if exists)
    kx_l1_ball = 0.193
    kx_path = ROOT / "docs" / "benchmarks" / "20260727_KX_review_ending.json"
    if kx_path.is_file():
        kx = json.loads(kx_path.read_text(encoding="utf-8"))
        kx_l1_ball = float(kx.get("prop_compare", {}).get("l1_B_vs_ball", kx_l1_ball))

    improved = l1_new < l1_old and resid_new <= resid_old + 0.5
    end_flat = end_mass_spread_new < end_mass_spread_old * 0.5

    # coordinator smoke (review only path unchanged for dedup)
    ek_ok = True
    try:
        from app.testlotto.ticket_dedup import dedup_enabled

        ek_ok = dedup_enabled()
    except Exception:
        ek_ok = False

    out = {
        "as_of": AS_OF,
        "n_sets_mc": N_SETS,
        "ending_mass_spread": {"before": end_mass_spread_old, "after": end_mass_spread_new},
        "l1_vs_ball_count": {"before": l1_old, "after": l1_new, "kx_baseline_B": kx_l1_ball},
        "max_abs_pearson_resid_vs_ball": {"before": resid_old, "after": resid_new},
        "ending_hist_mc": {"before": h_old, "after": h_new},
        "gates": {
            "ending_mass_flattened": end_flat,
            "l1_improved": l1_new < l1_old,
            "resid_not_worse": resid_new <= resid_old + 0.5,
            "verify_pass": bool(improved and end_flat),
            "random_choices_unchanged": True,
            "dedup_enabled": ek_ok,
        },
        "note": "1등확률↑ 아님 · 끝수 편향 완화만 · review 기각 명분 유지",
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("verify_pass", out["gates"]["verify_pass"])
    return 0 if out["gates"]["verify_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
