# -*- coding: utf-8 -*-
"""겹침 분석(저장된 15장) + 다양성 패치 라이브 WF(최근 회차 재예측).

동결: random.choices 라인 미수정. oversample→diversify_pick 만 사용.
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
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
from app.testlotto.set_diversity import (  # noqa: E402
    avg_pairwise_jaccard,
    number_concentration,
)
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402
from tools.run_meta_vote2_wf import _best_single_match, _load_draws  # noqa: E402
from tools.run_set_picker_wf import _load_tagged_sets  # noqa: E402

OUT_DIR = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_겹침분석_다양성패치"
)


def analyze_stored() -> dict[str, Any]:
    tagged = _load_tagged_sets()
    draws = _load_draws()
    per_brain_j = defaultdict(list)
    all_j = []
    conc = []
    uniq = []
    best15 = []
    best_brain = defaultdict(list)

    for d in draws:
        td = int(d["draw_no"])
        ents = tagged.get(td) or []
        if len(ents) < 5:
            continue
        actual = sorted_nums(d)
        bonus = int(d["bonus"])
        by = defaultdict(list)
        for e in ents:
            by[e["brain"]].append(e["nums"])
        all_sets = [e["nums"] for e in ents]
        all_j.append(avg_pairwise_jaccard(all_sets))
        conc.append(number_concentration(all_sets))
        uniq.append(len(set().union(*[set(s) for s in all_sets])))
        best15.append(_best_single_match(all_sets, actual, bonus)["matched_count"])
        for b, ss in by.items():
            if len(ss) >= 2:
                per_brain_j[b].append(avg_pairwise_jaccard(ss))
            if ss:
                best_brain[b].append(
                    _best_single_match(ss, actual, bonus)["matched_count"]
                )

    def avg(xs: list[float]) -> float:
        return round(sum(xs) / max(1, len(xs)), 4)

    return {
        "n": len(all_j),
        "avg_jaccard_all15": avg(all_j),
        "avg_jaccard_within_brain": {b: avg(v) for b, v in per_brain_j.items()},
        "avg_unique_all15": avg([float(u) for u in uniq]),
        "avg_top6_share": avg([c["top6_share"] for c in conc]),
        "avg_best15": avg([float(x) for x in best15]),
        "avg_best_per_brain": {b: avg([float(x) for x in v]) for b, v in best_brain.items()},
        "note": "저장 풀(과거 산출) 기준. 패치 전 베이스라인.",
    }


def live_diversity_wf(*, last_n: int = 40, seed: int = 20260726) -> dict[str, Any]:
    """최근 last_n 회차: 다양성 패치로 3×5 재생성 vs 랜덤 15 vs 저장 풀."""
    random.seed(seed)
    init_testlotto_db()
    tagged = _load_tagged_sets()
    draws = _load_draws()
    rows = []
    use = [d for d in draws if len(tagged.get(int(d["draw_no"]), [])) >= 5][-last_n:]

    for d in use:
        td = int(d["draw_no"])
        before = _get_draws_before(td)
        if len(before) < 20:
            continue
        actual = sorted_nums(d)
        bonus = int(d["bonus"])

        # new diversified generation
        new_sets = []
        for mod in (predict_stat_fairy, predict_flow_shaman, predict_review_king):
            new_sets.extend([x["nums"] for x in mod.predict_sets(before, 5)])

        stored = [e["nums"] for e in tagged.get(td, [])]
        rng = random.Random(seed + td)
        rand_sets = [sorted(rng.sample(range(1, 46), 6)) for _ in range(len(new_sets))]

        def pack(sets: list[list[int]], label: str) -> dict[str, Any]:
            if not sets:
                return {"label": label, "empty": True}
            return {
                "label": label,
                "n_sets": len(sets),
                "unique": len(set().union(*[set(s) for s in sets])),
                "jaccard": round(avg_pairwise_jaccard(sets), 4),
                "top6_share": number_concentration(sets)["top6_share"],
                "best": _best_single_match(sets, actual, bonus)["matched_count"],
                "mean": round(
                    sum(
                        score_predicted_set(s, actual, bonus)["matched_count"]
                        for s in sets
                    )
                    / len(sets),
                    4,
                ),
            }

        rows.append(
            {
                "draw_no": td,
                "stored": pack(stored, "stored"),
                "diversified": pack(new_sets, "diversified"),
                "random15": pack(rand_sets, "random"),
            }
        )

    def col_avg(path: str) -> float:
        # path like diversified.best
        a, b = path.split(".")
        xs = [r[a][b] for r in rows if not r[a].get("empty")]
        return round(sum(xs) / max(1, len(xs)), 4)

    summary = {
        "ok": True,
        "n": len(rows),
        "last_n_requested": last_n,
        "seed": seed,
        "no_peek": True,
        "random_choices_untouched": True,
        "avg_unique_stored": col_avg("stored.unique"),
        "avg_unique_diversified": col_avg("diversified.unique"),
        "avg_unique_random": col_avg("random15.unique"),
        "avg_jaccard_stored": col_avg("stored.jaccard"),
        "avg_jaccard_diversified": col_avg("diversified.jaccard"),
        "avg_best_stored": col_avg("stored.best"),
        "avg_best_diversified": col_avg("diversified.best"),
        "avg_best_random": col_avg("random15.best"),
        "delta_best_div_vs_stored": round(
            col_avg("diversified.best") - col_avg("stored.best"), 4
        ),
        "delta_best_div_vs_random": round(
            col_avg("diversified.best") - col_avg("random15.best"), 4
        ),
        "delta_unique_div_vs_stored": round(
            col_avg("diversified.unique") - col_avg("stored.unique"), 4
        ),
        "adopt": (
            col_avg("diversified.unique") >= col_avg("stored.unique") + 0.5
            or col_avg("diversified.best") >= col_avg("random15.best")
        ),
        "note": (
            "diversified=각 뇌 oversample 후 diversify_pick→5장×3. "
            "stored=DB 과거 산출. random=동일 장수 균등샘플."
        ),
    }
    return {"summary": summary, "rows": rows}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stored = analyze_stored()
    (OUT_DIR / "overlap_stored_baseline.json").write_text(
        json.dumps(stored, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    live = live_diversity_wf(last_n=40)
    (OUT_DIR / "diversity_live_wf.json").write_text(
        json.dumps(live["summary"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "diversity_live_wf_rows.json").write_text(
        json.dumps(live["rows"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    payload = {"stored_baseline": stored, "live_wf": live["summary"]}
    (OUT_DIR / "summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("WROTE", OUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
