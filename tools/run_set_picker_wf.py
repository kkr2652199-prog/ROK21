# -*- coding: utf-8 -*-
"""I-13 장선택 학습 WF — 15장 중 1장 고르기 (컨닝 금지).

학습: 과거 회차(t' < t)의 (세트 피처 → 실제 matched_count)로 선형 가중 적합.
예측: t에서 피처만으로 예상 match 최대인 장 선택.
비교: aux시드, aux+ending_r1, 오라클 best장.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
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

OUT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_형계획_세트합집합_메타선별"
    / "set_picker_wf_summary.json"
)
OUT_TOOLS = ROOT / "tools" / "_set_picker_wf_result.json"

BRAIN_IDX = {"stat": 0, "markov": 1, "review": 2}
FEAT_NAMES = [
    "vote_sum",
    "aux",
    "ending_sum",
    "hist_sum",
    "overlap_top12",
    "brain_stat",
    "brain_markov",
    "brain_review",
    "set_no_norm",
    "uniq_boost",  # 세트 내 번호가 다른 세트에도 많이 나옴(중복도)
]


def _vote(sets: list[list[int]]) -> Counter:
    c: Counter = Counter()
    for s in sets:
        c.update(set(int(n) for n in s))
    return c


def _load_tagged_sets() -> dict[int, list[dict[str, Any]]]:
    """draw/target -> list of {brain, set_no, nums, conf}."""
    init_testlotto_db()
    conn = get_lotto_db()
    by: dict[int, list[dict[str, Any]]] = defaultdict(list)
    try:
        # prefer predictions rows (have conf); fill from review json
        for r in conn.execute(
            """
            SELECT target_draw_no, brain_tag, confidence,
                   num1,num2,num3,num4,num5,num6
            FROM lotto_predictions
            WHERE brain_tag IN ('stat','markov','review')
            ORDER BY target_draw_no, brain_tag, id
            """
        ):
            td = int(r["target_draw_no"])
            tag = str(r["brain_tag"])
            nums = [int(r["num1"]), int(r["num2"]), int(r["num3"]),
                     int(r["num4"]), int(r["num5"]), int(r["num6"])]
            # set_no = count so far for this brain
            sn = sum(1 for x in by[td] if x["brain"] == tag) + 1
            by[td].append(
                {
                    "brain": tag,
                    "set_no": sn,
                    "nums": nums,
                    "conf": float(r["confidence"] or 0),
                }
            )

        for r in conn.execute(
            """
            SELECT draw_no, brain_tag, predicted_sets_json
            FROM testlotto_brain_review
            WHERE brain_tag IN ('stat','markov','review')
            """
        ):
            td = int(r["draw_no"])
            tag = str(r["brain_tag"])
            if sum(1 for x in by[td] if x["brain"] == tag) >= 5:
                continue
            try:
                data = json.loads(r["predicted_sets_json"] or "[]")
            except json.JSONDecodeError:
                continue
            for item in data:
                if sum(1 for x in by[td] if x["brain"] == tag) >= 5:
                    break
                if isinstance(item, dict) and "nums" in item:
                    nums = [int(x) for x in item["nums"][:6]]
                elif isinstance(item, list) and len(item) >= 6:
                    nums = [int(x) for x in item[:6]]
                else:
                    continue
                sn = sum(1 for x in by[td] if x["brain"] == tag) + 1
                by[td].append(
                    {"brain": tag, "set_no": sn, "nums": nums, "conf": 0.0}
                )
    finally:
        conn.close()
    return dict(by)


def feat_vector(
    entry: dict[str, Any],
    sets_nums: list[list[int]],
    draws_before: list[dict],
    target: int,
    traps: set[int],
    ending: Counter,
) -> list[float]:
    nums = entry["nums"]
    vote = _vote(sets_nums)
    hist = _hist_freq(draws_before)
    pool = list(vote.keys())
    pool.sort(
        key=lambda n: (hist.get(n, 0), ending.get(n, 0), vote[n], -n), reverse=True
    )
    top12 = set(pool[:12])
    brain = entry["brain"]
    return [
        float(sum(vote[int(n)] for n in nums)),
        float(fast_aux_composite(list(nums), draws_before, target, traps)),
        float(sum(ending.get(int(n), 0) for n in nums)),
        float(sum(hist.get(int(n), 0) for n in nums)),
        float(len(set(int(n) for n in nums) & top12)),
        1.0 if brain == "stat" else 0.0,
        1.0 if brain == "markov" else 0.0,
        1.0 if brain == "review" else 0.0,
        float(entry["set_no"]) / 5.0,
        float(sum(vote[int(n)] for n in nums) / 6.0),
    ]


def fit_ridge(
    X: list[list[float]], y: list[float], l2: float = 1.0
) -> list[float]:
    """간단한 정규방정식 ridge (절편 포함). numpy 없이 순수 파이썬."""
    if not X:
        return [0.0] * (len(FEAT_NAMES) + 1)
    n = len(X)
    d = len(X[0]) + 1  # +bias
    # build XtX, Xty
    A = [[0.0] * d for _ in range(d)]
    b = [0.0] * d
    for i in range(n):
        row = X[i] + [1.0]
        yi = y[i]
        for a in range(d):
            b[a] += row[a] * yi
            for c in range(d):
                A[a][c] += row[a] * row[c]
    for i in range(d - 1):  # don't regularize bias as hard
        A[i][i] += l2
    # gaussian elimination
    M = [A[i][:] + [b[i]] for i in range(d)]
    for col in range(d):
        piv = max(range(col, d), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        if abs(M[col][col]) < 1e-12:
            continue
        div = M[col][col]
        for j in range(col, d + 1):
            M[col][j] /= div
        for r in range(d):
            if r == col:
                continue
            fac = M[r][col]
            for j in range(col, d + 1):
                M[r][j] -= fac * M[col][j]
    return [M[i][d] for i in range(d)]


def predict(w: list[float], x: list[float]) -> float:
    return sum(w[i] * x[i] for i in range(len(x))) + w[-1]


def run() -> dict[str, Any]:
    init_testlotto_db()
    traps = _load_traps()
    all_draws = _load_draws()
    tagged = _load_tagged_sets()

    # precompute per-draw set records with labels (label uses actual — only stored for past)
    history: list[dict[str, Any]] = []
    rows_out: list[dict[str, Any]] = []

    min_train = 80

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

        feats = []
        labels = []
        for e in entries:
            x = feat_vector(e, sets_nums, before, td, traps, ending)
            y = float(score_predicted_set(e["nums"], actual, bonus)["matched_count"])
            feats.append(x)
            labels.append(y)

        oracle = _best_single_match(sets_nums, actual, bonus)

        # baselines
        aux_scores = [
            (fast_aux_composite(list(e["nums"]), before, td, traps), e)
            for e in entries
        ]
        aux_best = max(aux_scores, key=lambda t: t[0])[1]
        aux_match = score_predicted_set(aux_best["nums"], actual, bonus)["matched_count"]
        hy = hybrid_ending(
            aux_best["nums"], sets_nums, before, ending, min_vote=2, replace_slots=1
        )
        hy_match = score_predicted_set(hy["nums"], actual, bonus)["matched_count"]

        # train on history only
        if len(history) < min_train:
            # still record history after
            history.append({"feats": feats, "labels": labels, "td": td})
            continue

        X_train: list[list[float]] = []
        y_train: list[float] = []
        for h in history:
            X_train.extend(h["feats"])
            y_train.extend(h["labels"])
        # subsample last 400 draws worth (~6000 rows) for speed
        max_rows = 6000
        if len(X_train) > max_rows:
            X_train = X_train[-max_rows:]
            y_train = y_train[-max_rows:]

        w = fit_ridge(X_train, y_train, l2=5.0)
        scored = [(predict(w, feats[i]), entries[i], labels[i]) for i in range(len(entries))]
        pick = max(scored, key=lambda t: t[0])[1]
        pick_match = score_predicted_set(pick["nums"], actual, bonus)["matched_count"]

        # also: pick then ending_r1
        hy2 = hybrid_ending(
            pick["nums"], sets_nums, before, ending, min_vote=2, replace_slots=1
        )
        hy2_match = score_predicted_set(hy2["nums"], actual, bonus)["matched_count"]

        rows_out.append(
            {
                "draw_no": td,
                "n_sets": len(entries),
                "oracle": oracle["matched_count"],
                "aux": aux_match,
                "aux_ending": hy_match,
                "picker": pick_match,
                "picker_ending": hy2_match,
                "pick_brain": pick["brain"],
                "pick_set_no": pick["set_no"],
                "delta_picker_vs_aux": pick_match - aux_match,
                "delta_picker_vs_oracle": pick_match - oracle["matched_count"],
            }
        )
        history.append({"feats": feats, "labels": labels, "td": td})

    n = len(rows_out)
    if n == 0:
        return {"ok": False, "error": "no rows"}

    def avg(k: str) -> float:
        return round(sum(r[k] for r in rows_out) / n, 4)

    # final weights on all history for inspection
    X_all: list[list[float]] = []
    y_all: list[float] = []
    for h in history:
        X_all.extend(h["feats"])
        y_all.extend(h["labels"])
    if len(X_all) > 8000:
        X_all, y_all = X_all[-8000:], y_all[-8000:]
    w_final = fit_ridge(X_all, y_all, l2=5.0)
    weights = {FEAT_NAMES[i]: round(w_final[i], 5) for i in range(len(FEAT_NAMES))}
    weights["bias"] = round(w_final[-1], 5)

    brain_pick = Counter(r["pick_brain"] for r in rows_out)

    summary = {
        "ok": True,
        "no_peek": True,
        "n_eval": n,
        "min_train_draws": min_train,
        "avg_oracle": avg("oracle"),
        "avg_aux": avg("aux"),
        "avg_aux_ending": avg("aux_ending"),
        "avg_picker": avg("picker"),
        "avg_picker_ending": avg("picker_ending"),
        "picker_beats_aux": sum(1 for r in rows_out if r["delta_picker_vs_aux"] > 0),
        "picker_ties_aux": sum(1 for r in rows_out if r["delta_picker_vs_aux"] == 0),
        "picker_loses_aux": sum(1 for r in rows_out if r["delta_picker_vs_aux"] < 0),
        "mean_delta_vs_aux": avg("delta_picker_vs_aux"),
        "mean_gap_to_oracle_picker": round(avg("oracle") - avg("picker"), 4),
        "mean_gap_to_oracle_aux": round(avg("oracle") - avg("aux"), 4),
        "pass_vs_aux": avg("picker") > avg("aux"),
        "pass_closer_oracle": (avg("oracle") - avg("picker"))
        < (avg("oracle") - avg("aux")),
        "brain_pick_counts": dict(brain_pick),
        "feature_weights": weights,
        "adopt_picker": bool(
            avg("picker") >= avg("aux") + 0.03
            or (
                avg("picker") > avg("aux")
                and (avg("oracle") - avg("picker"))
                < (avg("oracle") - avg("aux")) - 0.02
            )
        ),
        "note": (
            "장선택=과거 피처→match 선형회귀 WF. "
            "당첨은 학습 라벨로만 쓰고 예측 시점 피처에 넣지 않음."
        ),
    }
    return {"summary": summary, "rows_tail": rows_out[-30:]}


def main() -> int:
    result = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(result.get("summary", result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    OUT_TOOLS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result.get("summary", result), ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0 if result.get("summary", {}).get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
