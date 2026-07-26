# -*- coding: utf-8 -*-
"""메타 선별기 — 풀에서 K개 6수 세트 조립 (컨닝 금지 호출 규약).

P5: 앱 레벨 API. UI 배선은 P1 pass 후에만 라우트 연결.
호출 측은 반드시 draws = target 이전 회차만 넘긴다.
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
    replace_slots: int = 2,
) -> list[dict[str, Any]]:
    """예측 풀 → 재조립 K세트.

    Returns:
        [{"nums": [...], "method": "hybrid_aux_seed", "meta": {...}}, ...]
    """
    # lazy import to keep tools circularity low
    from tools.run_meta_hybrid_wf import hybrid_assemble

    if not pool_sets:
        return []

    primary = hybrid_assemble(
        pool_sets,
        draws_before,
        target_draw_no,
        min_vote=min_vote,
        replace_slots=replace_slots,
        use_similar_past=True,
    )
    out = [
        {
            "nums": primary["nums"],
            "method": "hybrid_aux_seed",
            "aux_seed_score": primary.get("seed", {}).get("aux_score"),
            "n_replaced": primary.get("n_replaced", 0),
            "meta": primary,
        }
    ]

    # 추가 세트: replace_slots 변형 / Vote≥3 변형
    if k >= 2:
        alt = hybrid_assemble(
            pool_sets,
            draws_before,
            target_draw_no,
            min_vote=3,
            replace_slots=1,
            use_similar_past=True,
        )
        if alt["nums"] != primary["nums"]:
            out.append(
                {
                    "nums": alt["nums"],
                    "method": "hybrid_vote3_r1",
                    "n_replaced": alt.get("n_replaced", 0),
                    "meta": alt,
                }
            )

    if k >= 3:
        # 보조점수 2위 시드 변형: 1위 제외 후 재시드
        scored = []
        for s in pool_sets:
            scored.append((_aux_composite_score(list(s), draws_before, target_draw_no), s))
        scored.sort(key=lambda x: -x[0])
        if len(scored) >= 2:
            second = sorted(int(x) for x in scored[1][1])
            # second as forced seed: wrap by putting it first in a synthetic assemble
            # reuse hybrid on pool but prefer second via temporary pool order trick:
            # call hybrid then if needed override — simpler: return second set as alt
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
    """UI 게이트: P1 pass 여부 요약 파일 읽기."""
    from pathlib import Path
    import json

    p = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "benchmarks"
        / "20260726_형계획_세트합집합_메타선별"
        / "hybrid_wf_summary.json"
    )
    if not p.exists():
        return {"ui_enabled": False, "reason": "hybrid_wf_summary.json missing"}
    data = json.loads(p.read_text(encoding="utf-8"))
    passed = bool(data.get("pass_p1"))
    return {
        "ui_enabled": passed,
        "pass_p1": passed,
        "avg_meta": data.get("avg_meta"),
        "avg_seed": data.get("avg_seed"),
        "avg_oracle_best": data.get("avg_oracle_best"),
        "reason": "P1 pass" if passed else "P1 not passed — UI deferred",
    }
