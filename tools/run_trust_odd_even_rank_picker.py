# -*- coding: utf-8 -*-
"""신뢰 점검: odd_even 오탐 + 뇌 vs 랜덤 + 순위형 장선택.

1) odd_even detect 비율 vs 랜덤 기준선 → 자기강화면 수정
2) 3뇌 best-of-15 vs 랜덤 15장 best — 패턴 신호 있는지
3) 쌍대(순위) 장선택 WF — aux 이기면 채택
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.draw_analysis import detect_missed_patterns  # noqa: E402
from app.testlotto.features.draw_features import odd_even_ratio, sorted_nums  # noqa: E402
from app.testlotto.models import get_lotto_db, init_testlotto_db  # noqa: E402
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402
from tools.run_meta_hybrid_ending_wf import ending_next_boost, hybrid_ending  # noqa: E402
from tools.run_meta_hybrid_wf import _load_traps, fast_aux_composite  # noqa: E402
from tools.run_meta_vote2_wf import (  # noqa: E402
    _best_single_match,
    _draws_before,
    _hist_freq,
    _load_draws,
)
from tools.run_set_picker_wf import (  # noqa: E402
    FEAT_NAMES,
    _load_tagged_sets,
    feat_vector,
    fit_ridge,
    predict,
)

OUT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_신뢰_odd_even_순위장선택"
)
OUT.mkdir(parents=True, exist_ok=True)


def _rand_set(rng: random.Random) -> list[int]:
    return sorted(rng.sample(range(1, 46), 6))


def audit_odd_even(all_draws: list[dict], tagged: dict, sample_n: int = 400) -> dict:
    """현재 detect의 odd_even 발화율 vs 랜덤."""
    rng = random.Random(42)
    brain_hits = 0
    brain_n = 0
    rand_hits = 0
    rand_n = 0
    # from review json missed if available
    review_oe = Counter()
    conn = get_lotto_db()
    try:
        for r in conn.execute(
            "SELECT missed_patterns FROM testlotto_brain_review WHERE brain_tag='stat' LIMIT 2000"
        ):
            try:
                mp = json.loads(r[0] or "[]")
            except json.JSONDecodeError:
                mp = []
            review_oe["total"] += 1
            if "odd_even" in mp:
                review_oe["odd_even"] += 1
    finally:
        conn.close()

    draws_use = [d for d in all_draws if int(d["draw_no"]) >= 200][-sample_n:]
    for d in draws_use:
        td = int(d["draw_no"])
        before = _draws_before(all_draws, td)
        actual = sorted_nums(d)
        entries = tagged.get(td) or []
        if not entries:
            continue
        # first set of first brain available
        pred = entries[0]["nums"]
        missed = detect_missed_patterns(pred, actual, before)
        brain_n += 1
        if "odd_even" in missed:
            brain_hits += 1
        for _ in range(3):
            rp = _rand_set(rng)
            rm = detect_missed_patterns(rp, actual, before)
            rand_n += 1
            if "odd_even" in rm:
                rand_hits += 1

    return {
        "detect_code_brain_rate": round(brain_hits / max(1, brain_n), 4),
        "detect_code_random_rate": round(rand_hits / max(1, rand_n), 4),
        "review_stat_odd_even_rate": round(
            review_oe["odd_even"] / max(1, review_oe["total"]), 4
        ),
        "n_brain": brain_n,
        "n_random": rand_n,
        "self_reinforce_suspect": (
            abs(
                (brain_hits / max(1, brain_n))
                - (rand_hits / max(1, rand_n))
            )
            < 0.05
            and (brain_hits / max(1, brain_n)) > 0.4
        ),
    }


def simulate_new_odd_even(
    all_draws: list[dict], tagged: dict, sample_n: int = 400
) -> dict:
    """신로직 후보 발화율."""
    rng = random.Random(7)

    def new_miss(pred: list[int], actual: list[int]) -> bool:
        odd_a, _ = odd_even_ratio(actual)
        odd_p, _ = odd_even_ratio(pred)
        # 당첨이 흔함(2~4홀)인데 예측이 극단(0,1,5,6)일 때만
        return odd_a in (2, 3, 4) and odd_p in (0, 1, 5, 6)

    bh = bn = rh = rn = 0
    draws_use = [d for d in all_draws if int(d["draw_no"]) >= 200][-sample_n:]
    for d in draws_use:
        td = int(d["draw_no"])
        actual = sorted_nums(d)
        entries = tagged.get(td) or []
        if not entries:
            continue
        bn += 1
        if new_miss(entries[0]["nums"], actual):
            bh += 1
        for _ in range(3):
            rn += 1
            if new_miss(_rand_set(rng), actual):
                rh += 1
    return {
        "new_brain_rate": round(bh / max(1, bn), 4),
        "new_random_rate": round(rh / max(1, rn), 4),
        "rule": "actual_odd in 2..4 AND pred_odd in {0,1,5,6}",
    }


def trust_brain_vs_random(all_draws: list[dict], tagged: dict) -> dict:
    rng = random.Random(99)
    b_best = []
    r_best = []
    b_avg = []
    for d in all_draws:
        td = int(d["draw_no"])
        entries = tagged.get(td) or []
        if len(entries) < 5:
            continue
        actual = sorted_nums(d)
        bonus = int(d["bonus"])
        sets = [e["nums"] for e in entries]
        bb = _best_single_match(sets, actual, bonus)["matched_count"]
        ba = sum(
            score_predicted_set(s, actual, bonus)["matched_count"] for s in sets
        ) / len(sets)
        rb = 0
        for _ in range(len(sets)):
            sc = score_predicted_set(_rand_set(rng), actual, bonus)["matched_count"]
            if sc > rb:
                rb = sc
        b_best.append(bb)
        r_best.append(rb)
        b_avg.append(ba)
    n = len(b_best)
    return {
        "n": n,
        "avg_brain_best_of_sets": round(sum(b_best) / n, 4),
        "avg_random_best_of_same_n": round(sum(r_best) / n, 4),
        "avg_brain_mean_set": round(sum(b_avg) / n, 4),
        "lift_best_vs_random": round(
            sum(b_best) / n - sum(r_best) / n, 4
        ),
        "brain_has_signal": (sum(b_best) / n) > (sum(r_best) / n) + 0.05,
        "note": "동일 장수 랜덤 대비 뇌 best 세트. 양수 lift=패턴 신호.",
    }


def rank_picker_wf(all_draws: list[dict], tagged: dict) -> dict:
    """쌍대 순위: A가 B보다 match 높으면 feat(A)-feat(B) → +1 학습."""
    traps = _load_traps()
    history_pairs: list[tuple[list[float], float]] = []
    rows = []
    min_train = 100

    for d in all_draws:
        td = int(d["draw_no"])
        entries = tagged.get(td) or []
        if len(entries) < 5:
            continue
        before = _draws_before(all_draws, td)
        if len(before) < 10:
            continue
        actual = sorted_nums(d)
        bonus = int(d["bonus"])
        sets_nums = [e["nums"] for e in entries]
        ending = ending_next_boost(before)
        feats = [
            feat_vector(e, sets_nums, before, td, traps, ending) for e in entries
        ]
        labels = [
            float(score_predicted_set(e["nums"], actual, bonus)["matched_count"])
            for e in entries
        ]

        # aux baseline
        aux_best = max(
            entries,
            key=lambda e: fast_aux_composite(list(e["nums"]), before, td, traps),
        )
        aux_m = score_predicted_set(aux_best["nums"], actual, bonus)["matched_count"]
        oracle = _best_single_match(sets_nums, actual, bonus)["matched_count"]

        if len(history_pairs) >= min_train * 3:
            # fit on pairwise diffs
            X = [p[0] for p in history_pairs[-8000:]]
            y = [p[1] for p in history_pairs[-8000:]]
            w = fit_ridge(X, y, l2=8.0)
            scores = [predict(w, feats[i]) for i in range(len(entries))]
            pick = entries[max(range(len(entries)), key=lambda i: scores[i])]
            pm = score_predicted_set(pick["nums"], actual, bonus)["matched_count"]
            hy = hybrid_ending(
                pick["nums"], sets_nums, before, ending, min_vote=2, replace_slots=1
            )
            hm = score_predicted_set(hy["nums"], actual, bonus)["matched_count"]
            rows.append(
                {
                    "draw_no": td,
                    "oracle": oracle,
                    "aux": aux_m,
                    "rank_picker": pm,
                    "rank_picker_ending": hm,
                    "delta_vs_aux": pm - aux_m,
                }
            )

        # add pairwise samples (limit pairs per draw)
        order = sorted(range(len(entries)), key=lambda i: -labels[i])
        for a_i in range(min(6, len(order))):
            for b_i in range(a_i + 1, min(8, len(order))):
                i, j = order[a_i], order[b_i]
                if labels[i] == labels[j]:
                    continue
                diff = [feats[i][k] - feats[j][k] for k in range(len(feats[i]))]
                # label +1 if i better
                history_pairs.append((diff, 1.0 if labels[i] > labels[j] else 0.0))

    n = len(rows)
    if n == 0:
        return {"ok": False, "error": "no rows"}

    def avg(k: str) -> float:
        return round(sum(r[k] for r in rows) / n, 4)

    return {
        "ok": True,
        "n_eval": n,
        "avg_oracle": avg("oracle"),
        "avg_aux": avg("aux"),
        "avg_rank_picker": avg("rank_picker"),
        "avg_rank_picker_ending": avg("rank_picker_ending"),
        "beats_aux": sum(1 for r in rows if r["delta_vs_aux"] > 0),
        "mean_delta_vs_aux": avg("delta_vs_aux"),
        "adopt": avg("rank_picker") >= avg("aux") + 0.03,
        "feat_names": FEAT_NAMES,
    }


def main() -> int:
    init_testlotto_db()
    all_draws = _load_draws()
    tagged = _load_tagged_sets()

    oe_old = audit_odd_even(all_draws, tagged)
    oe_new = simulate_new_odd_even(all_draws, tagged)
    trust = trust_brain_vs_random(all_draws, tagged)
    rank = rank_picker_wf(all_draws, tagged)

    # decide odd_even fix
    apply_fix = bool(oe_old.get("self_reinforce_suspect") or oe_old["detect_code_brain_rate"] > 0.35)

    summary = {
        "ok": True,
        "odd_even_current": oe_old,
        "odd_even_proposed": oe_new,
        "apply_odd_even_fix": apply_fix,
        "trust_brain_vs_random": trust,
        "rank_picker": rank,
        "decisions": {
            "odd_even": "FIX" if apply_fix else "KEEP",
            "rank_picker": "ADOPT" if rank.get("adopt") else "REJECT",
            "brains_trusted_over_random": trust.get("brain_has_signal"),
        },
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("WROTE", OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
