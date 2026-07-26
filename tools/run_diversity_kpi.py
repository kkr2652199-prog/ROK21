# -*- coding: utf-8 -*-
"""P4 다양성 KPI — Jaccard / unique pool / cover6 (뇌 추가 게이트)."""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from tools.run_meta_vote2_wf import _load_draws, _load_sets_by_draw  # noqa: E402

OUT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_형계획_세트합집합_메타선별"
    / "diversity_kpi.json"
)

# 게이트(핀): 새 뇌 추가 전 현재 베이스라인 기록. 추가 후 unique↓ 또는 cover6↓면 거부.
GATE = {
    "min_avg_unique_pool": 20.0,
    "min_cover6_rate": 0.25,
    "max_avg_pairwise_jaccard": 0.45,
}


def jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def main() -> int:
    init_testlotto_db()
    draws = _load_draws()
    sets_by = _load_sets_by_draw()
    rows = []
    for d in draws:
        td = int(d["draw_no"])
        sets = sets_by.get(td) or []
        if len(sets) < 5:
            continue
        actual = set(sorted_nums(d))
        set_sets = [set(s) for s in sets]
        uniq: set[int] = set()
        for s in set_sets:
            uniq |= s
        cover = len(actual & uniq)
        pairs = list(combinations(range(len(set_sets)), 2))
        if pairs:
            jac = sum(jaccard(set_sets[i], set_sets[j]) for i, j in pairs) / len(pairs)
        else:
            jac = 0.0
        rows.append(
            {
                "draw_no": td,
                "n_sets": len(sets),
                "unique_pool": len(uniq),
                "cover": cover,
                "cover6": cover >= 6,
                "avg_pairwise_jaccard": round(jac, 4),
            }
        )

    n = len(rows)
    avg_unique = sum(r["unique_pool"] for r in rows) / n
    cover6_rate = sum(1 for r in rows if r["cover6"]) / n
    avg_jac = sum(r["avg_pairwise_jaccard"] for r in rows) / n

    gate_ok = (
        avg_unique >= GATE["min_avg_unique_pool"]
        and cover6_rate >= GATE["min_cover6_rate"]
        and avg_jac <= GATE["max_avg_pairwise_jaccard"]
    )

    payload = {
        "ok": True,
        "n_draws": n,
        "avg_unique_pool": round(avg_unique, 4),
        "cover6_rate": round(cover6_rate, 4),
        "avg_pairwise_jaccard": round(avg_jac, 4),
        "gate": GATE,
        "gate_pass_current_baseline": gate_ok,
        "brain_add_rule": (
            "새 뇌 추가 후 avg_unique≥min AND cover6_rate≥min AND avg_jaccard≤max. "
            "하나라도 악화(unique↓ cover6↓ jaccard↑)면 거부."
        ),
        "window_last100": _window(rows[-100:]) if n >= 100 else None,
        "note": "현재 3뇌 베이스라인. Track C 진입 전 이 KPI로 게이트.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0


def _window(rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    return {
        "n": n,
        "avg_unique_pool": round(sum(r["unique_pool"] for r in rows) / n, 4),
        "cover6_rate": round(sum(1 for r in rows if r["cover6"]) / n, 4),
        "avg_pairwise_jaccard": round(
            sum(r["avg_pairwise_jaccard"] for r in rows) / n, 4
        ),
    }


if __name__ == "__main__":
    raise SystemExit(main())
