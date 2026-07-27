# -*- coding: utf-8 -*-
"""K-W post-KP3: review live 산출 vs A/C ending 거리 재측정 (READ-ONLY · 적중↑아님)."""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260727_KW_post_KP3.json"
KW_BASE = ROOT / "docs" / "benchmarks" / "20260727_KW_alignment.json"
SEED = 20260727
AS_OF = 1235
N_SETS = 500


def _load_draws_A() -> list[list[int]]:
    import sqlite3

    con = sqlite3.connect(str(ROOT / "data" / "lotto_testlotto.db"))
    rows = con.execute(
        "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    con.close()
    return [sorted(int(x) for x in r) for r in rows]


def _sample_uniform(n: int, rng: random.Random) -> list[list[int]]:
    pool = list(range(1, 46))
    return [sorted(rng.sample(pool, 6)) for _ in range(n)]


def _ending_counts(sets: list[list[int]]) -> np.ndarray:
    e = Counter()
    for s in sets:
        for x in s:
            e[x % 10] += 1
    return np.array([e.get(d, 0) for d in range(10)], dtype=float)


def _chi2_df(a: np.ndarray, b: np.ndarray) -> float:
    tbl = np.vstack([a, b]).astype(float)
    tbl = tbl[:, tbl.sum(axis=0) > 0]
    if tbl.shape[1] < 2:
        return 0.0
    keep, rare_a, rare_b = [], 0.0, 0.0
    for j in range(tbl.shape[1]):
        if tbl[:, j].sum() >= 5:
            keep.append(j)
        else:
            rare_a += tbl[0, j]
            rare_b += tbl[1, j]
    cols = [tbl[:, j] for j in keep]
    if rare_a + rare_b > 0:
        cols.append(np.array([rare_a, rare_b]))
    if len(cols) < 2:
        return 0.0
    t = np.column_stack(cols)
    chi2, _, dof, _ = stats.chi2_contingency(t)
    return float(chi2 / max(1, int(dof)))


def _sample_review_live(n_sets: int, seed: int) -> list[list[int]]:
    from app.testlotto.brains.predict_review_king import build_review_weights
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    set_learn_as_of(AS_OF)
    draws = _get_draws_before(AS_OF)
    weights = build_review_weights(draws)
    rng = random.Random(seed)
    out: list[list[int]] = []
    used: set[tuple[int, ...]] = set()
    attempts = 0
    while len(out) < n_sets and attempts < n_sets * 40:
        attempts += 1
        pool = list(range(1, 46))
        w = [weights[n] for n in pool]
        pick: list[int] = []
        for _ in range(6):
            if not pool:
                break
            chosen = rng.choices(pool, weights=w, k=1)[0]
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
        out.append(sorted(pick))
    return out


def _smoke_predict_sets() -> bool:
    from app.testlotto.brains.predict_review_king import predict_sets
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    set_learn_as_of(AS_OF)
    draws = _get_draws_before(AS_OF)
    try:
        r = predict_sets(draws, n_sets=2)
        return len(r) >= 1 and len(r[0].get("nums") or []) == 6
    except Exception:
        return False


def main() -> int:
    base = json.loads(KW_BASE.read_text(encoding="utf-8")) if KW_BASE.is_file() else {}
    base_rev = (base.get("brains") or {}).get("review") or {}
    before_vs_A = float((base_rev.get("vs_A") or {}).get("ending_chi2_df") or 0)
    before_vs_C = float((base_rev.get("vs_C") or {}).get("ending_chi2_df") or 0)

    A = _load_draws_A()
    live = _sample_review_live(N_SETS, SEED)
    C = _sample_uniform(len(live), random.Random(SEED + 7))

    end_A = _ending_counts(A)
    end_B = _ending_counts(live)
    end_C = _ending_counts(C)
    after_vs_A = _chi2_df(end_B, end_A)
    after_vs_C = _chi2_df(end_B, end_C)

    predict_ok = _smoke_predict_sets()
    ending_improved = after_vs_A < before_vs_A and after_vs_C < before_vs_C
    # post-KP3: ending should not be top deviation far_both style (both large)
    not_far_both = min(after_vs_A, after_vs_C) < 5.0

    checks = {
        "predict_sets_ok": predict_ok,
        "n_live_sets": len(live) == N_SETS,
        "ending_vs_A_improved": after_vs_A < before_vs_A,
        "ending_vs_C_improved": after_vs_C < before_vs_C,
        "ending_not_far_both": not_far_both,
        "rates_nameerror_fixed": predict_ok,
    }
    verify_pass = all(checks.values())

    payload = {
        "task": "K-W-POST-KP3",
        "as_of": AS_OF,
        "n_sets": N_SETS,
        "seed": SEED,
        "baseline_kw_file": str(KW_BASE.name),
        "review_ending": {
            "before_stored_review": {"vs_A": before_vs_A, "vs_C": before_vs_C},
            "after_live_KP3": {"vs_A": after_vs_A, "vs_C": after_vs_C},
            "delta": {
                "vs_A": after_vs_A - before_vs_A,
                "vs_C": after_vs_C - before_vs_C,
            },
            "hist_live_0to9": end_B.astype(int).tolist(),
        },
        "checks": checks,
        "verify_pass": verify_pass,
        "note": "적중↑아님 · K-P3 ending질량균등 후 live review vs A/C · stored KW는 사전표본",
        "kw_alignment_label_hint": (
            "무해_C근접_끝수완화" if ending_improved and not_far_both else "관측대기"
        ),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
