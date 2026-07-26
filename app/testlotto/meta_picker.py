# -*- coding: utf-8 -*-
"""메타 선별기 — 풀에서 K개 6수 세트 조립 (컨닝 금지 호출 규약).

기본: 보조4뇌 시드 + L_ending 1슬롯 교체 (20260726 ending_r1 소폭 우위).
UI 풀배선은 pass_p1 전 deferred. 호출 측 draws = target 이전만.
"""
from __future__ import annotations

from typing import Any

from app.testlotto.brains.coordinator import _aux_composite_score


def meta_assemble_sets(
    pool_sets: list[list[int]],
    draws_before: list[dict],
    target_draw_no: int,
    *,
    k: int = 1,
    min_vote: int = 2,
    replace_slots: int = 1,
) -> list[dict[str, Any]]:
    """예측 풀 → 재조립 K세트."""
    from tools.run_meta_hybrid_ending_wf import ending_next_boost, hybrid_ending
    from tools.run_meta_hybrid_wf import _load_traps, pick_aux_seed

    if not pool_sets:
        return []

    traps = _load_traps()
    seed = pick_aux_seed(pool_sets, draws_before, target_draw_no, traps)
    ending = ending_next_boost(draws_before)
    primary = hybrid_ending(
        seed["nums"],
        pool_sets,
        draws_before,
        ending,
        min_vote=min_vote,
        replace_slots=replace_slots,
    )
    out = [
        {
            "nums": primary["nums"],
            "method": "hybrid_aux_seed_ending_r1",
            "aux_seed_score": seed.get("aux_score"),
            "n_replaced": primary.get("n_replaced", 0),
            "meta": {"seed": seed, **primary},
        }
    ]

    if k >= 2:
        alt = hybrid_ending(
            seed["nums"],
            pool_sets,
            draws_before,
            ending,
            min_vote=3,
            replace_slots=1,
        )
        if alt["nums"] != primary["nums"]:
            out.append(
                {
                    "nums": alt["nums"],
                    "method": "hybrid_vote3_ending_r1",
                    "n_replaced": alt.get("n_replaced", 0),
                    "meta": {"seed": seed, **alt},
                }
            )

    if k >= 3:
        scored = []
        for s in pool_sets:
            scored.append((_aux_composite_score(list(s), draws_before, target_draw_no), s))
        scored.sort(key=lambda x: -x[0])
        if len(scored) >= 2:
            second = sorted(int(x) for x in scored[1][1])
            out.append(
                {
                    "nums": second,
                    "method": "aux_seed_second",
                    "aux_seed_score": round(scored[1][0], 4),
                    "n_replaced": 0,
                    "meta": {"seed": {"nums": second, "aux_score": round(scored[1][0], 4)}},
                }
            )

    return out[:k]


def meta_picker_status() -> dict[str, Any]:
    """UI 게이트: P1 pass + ending 소폭 개선 메모."""
    from pathlib import Path
    import json

    root = Path(__file__).resolve().parents[2]
    bench = root / "docs" / "benchmarks" / "20260726_형계획_세트합집합_메타선별"
    hybrid = bench / "hybrid_wf_summary.json"
    ending = bench / "hybrid_ending_wf_summary.json"

    if not hybrid.exists():
        return {"ui_enabled": False, "reason": "hybrid_wf_summary.json missing"}
    data = json.loads(hybrid.read_text(encoding="utf-8"))
    passed = bool(data.get("pass_p1"))
    out: dict[str, Any] = {
        "ui_enabled": passed,
        "pass_p1": passed,
        "avg_meta": data.get("avg_meta"),
        "avg_seed": data.get("avg_seed"),
        "avg_oracle_best": data.get("avg_oracle_best"),
        "default_method": "hybrid_aux_seed_ending_r1",
        "reason": "P1 pass" if passed else "P1 not passed — UI deferred",
    }
    if ending.exists():
        ed = json.loads(ending.read_text(encoding="utf-8"))
        v = (ed.get("variants") or {}).get("ending_r1") or {}
        out["ending_r1_avg_match"] = v.get("avg_match")
        out["ending_r1_delta_vs_baseline"] = v.get("delta_vs_baseline")
        out["ending_best_variant"] = ed.get("best_variant")
    return out
