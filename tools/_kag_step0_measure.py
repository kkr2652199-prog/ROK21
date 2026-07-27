# -*- coding: utf-8 -*-
"""K-AG STEP0: pair_score 분포 · zone 정의불일치 · 미소비키 재확인 (READ 측정)."""
from __future__ import annotations

import json
import math
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260727_KAG_step0_measure.json"
AS_OF = 1234
WINDOW = 100
SEED = 20260727


def quantiles(xs: list[float]) -> dict:
    if not xs:
        return {}
    s = sorted(xs)
    def q(p):
        i = (len(s) - 1) * p
        lo, hi = int(math.floor(i)), int(math.ceil(i))
        if lo == hi:
            return s[lo]
        return s[lo] * (hi - i) + s[hi] * (i - lo)
    return {
        "n": len(s),
        "min": s[0],
        "mean": statistics.mean(s),
        "stdev": statistics.pstdev(s) if len(s) > 1 else 0.0,
        "q25": q(0.25),
        "q50": q(0.50),
        "q75": q(0.75),
        "q90": q(0.90),
        "q95": q(0.95),
        "q99": q(0.99),
        "max": s[-1],
        "frac_ge_30": sum(1 for x in s if x >= 30) / len(s),
        "frac_eq_cap_if_div30": sum(1 for x in s if x >= 30) / len(s),
    }


def main() -> int:
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.features.draw_features import build_pair_freq, pair_set, sorted_nums
    from app.testlotto.brains import aux_pattern_spotlight as pat
    from app.testlotto.brains import aux_balance_keeper as bal
    import inspect

    draws = _get_draws_before(AS_OF)
    assert draws, "no draws"
    # pair freq on last 100 before as_of
    window_draws = draws[-WINDOW:]
    pf = build_pair_freq(draws, window=WINDOW)

    # winning combos in window: pair_score
    win_scores = []
    for d in window_draws:
        nums = sorted_nums(d)
        win_scores.append(float(sum(pf.get(p, 0) for p in pair_set(nums))))

    # null: random C(45,6) samples scored against same pf
    rng = random.Random(SEED)
    null_scores = []
    universe = list(range(1, 46))
    for _ in range(5000):
        nums = sorted(rng.sample(universe, 6))
        null_scores.append(float(sum(pf.get(p, 0) for p in pair_set(nums))))

    # also score next-draw style: for each draw in window, use pf built from draws before that draw
    rolling_win = []
    for i, d in enumerate(window_draws):
        before = draws[: len(draws) - WINDOW + i]  # all before this window draw? careful
        # proper: draws with draw_no < d['draw_no'], last 100
        prior = [x for x in draws if int(x["draw_no"]) < int(d["draw_no"])][-WINDOW:]
        if len(prior) < 10:
            continue
        pf_i = build_pair_freq(prior, window=WINDOW)
        nums = sorted_nums(d)
        rolling_win.append(float(sum(pf_i.get(p, 0) for p in pair_set(nums))))

    # /30 source in code
    src = inspect.getsource(pat.score_set)
    pair_line = [ln.strip() for ln in src.splitlines() if "30" in ln or "pair" in ln]

    # zone mismatch
    bal_src = inspect.getsource(bal.score_set) + inspect.getsource(bal._historical_targets)
    tgt = bal._historical_targets(draws)
    # theory LMH
    from math import comb
    N = comb(45, 6)
    lmh_pmf = {}
    for L in range(0, 7):
        for M in range(0, 7 - L):
            H = 6 - L - M
            c = comb(15, L) * comb(15, M) * comb(15, H)
            lmh_pmf[(L, M, H)] = c / N
    mode = max(lmh_pmf, key=lmh_pmf.get)
    e_max = sum(max(t) * p for t, p in lmh_pmf.items())

    # unused keys consume check
    import app.testlotto.brains.aux_pattern_spotlight as ap
    import app.testlotto.brains.aux_balance_keeper as ab
    consume = {
        "pair_boost_in_pattern": "pair_boost" in Path(ap.__file__).read_text(encoding="utf-8"),
        "consecutive_boost_in_pattern": "consecutive_boost" in Path(ap.__file__).read_text(encoding="utf-8"),
        "odd_even_in_balance": "odd_even_balance" in Path(ab.__file__).read_text(encoding="utf-8"),
    }

    # proposed divisor candidates WITH EVIDENCE from this measure only
    q_null = quantiles(null_scores)
    q_win = quantiles(win_scores)
    q_roll = quantiles(rolling_win)
    # Use null q95 as soft cap (distribution-based, not arbitrary 30)
    proposed = {
        "method": "null_q95_of_pair_score_vs_window100_pair_freq",
        "divisor": q_null["q95"],
        "rationale": (
            "K-U: pair not advantageous (FDR0). Normalize by null(candidate) q95 "
            "so typical random combos sit near 1.0 soft-cap without claiming hit uplift. "
            "Winning q95 recorded for contrast only."
        ),
        "legacy_30_saturation_null": q_null["frac_ge_30"],
        "legacy_30_saturation_win": q_win["frac_ge_30"],
        "win_q95": q_win["q95"],
        "rolling_win_q95": q_roll.get("q95"),
    }

    out = {
        "meta": {
            "as_of": AS_OF,
            "window": WINDOW,
            "seed": SEED,
            "disclaimer": "명분·배선 정합. 1등 확률 상승 작업 아님.",
        },
        "pair": {
            "code_divisor_legacy": 30.0,
            "code_lines": pair_line,
            "source_note": "literal /30.0 in aux_pattern_spotlight.score_set — no derived comment in code",
            "win_in_window_same_pf": q_win,
            "null_5000": q_null,
            "rolling_win_causal": q_roll,
            "proposed_divisor": proposed,
        },
        "zone": {
            "historical_targets_zone_key": tgt["zone"],
            "historical_targets_meaning": "mean of max(zone_counts) over last 80 draws",
            "score_uses": "zone_spread = max-min of (L,M,H); zone_score=1-min(1,spread/4); tgt['zone'] UNUSED in score_set",
            "definition_conflict": True,
            "theory_mode_lmh": list(mode),
            "theory_mode_p": lmh_pmf[mode],
            "theory_E_max_zone": e_max,
            "kz_mode_p_ref": 0.14212602485432888,
            "kz_E_max_zone_ref": 3.1484685195689166,
        },
        "unused_keys": {
            "keys": ["pair_boost", "consecutive_boost", "odd_even_balance"],
            "consumed_in_aux_modules_now": consume,
            "ky_status": "학습되나 미소비",
        },
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("null_q95", q_null["q95"], "win_q95", q_win["q95"], "sat30_null", q_null["frac_ge_30"])
    print("zone_conflict", True, "mode", mode, "p", lmh_pmf[mode])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
