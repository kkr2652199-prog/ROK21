# -*- coding: utf-8 -*-
"""메타 선별기 — 기본은 서로 덜 겹치는 포트폴리오 K장.

운영 기본 (20260726 채택):
  aux 상위 후보에서 Jaccard 패널티로 K=3 선택.
  1장만 필요하면 port[0] (+ optional ending 1슬롯).
"""
from __future__ import annotations

from typing import Any


def meta_assemble_sets(
    pool_sets: list[list[int]],
    draws_before: list[dict],
    target_draw_no: int,
    *,
    k: int = 3,
    min_vote: int = 2,
    replace_slots: int = 1,
) -> list[dict[str, Any]]:
    from tools.run_meta_hybrid_ending_wf import ending_next_boost, hybrid_ending
    from tools.run_meta_hybrid_wf import _load_traps, pick_aux_seed
    from tools.run_portfolio_set_picker_wf import pick_portfolio

    if not pool_sets:
        return []

    traps = _load_traps()
    # wrap pool as entries for portfolio
    entries = [{"nums": list(s), "brain": "pool", "set_no": i + 1} for i, s in enumerate(pool_sets)]
    port = pick_portfolio(entries, draws_before, target_draw_no, traps, k=max(1, min(k, 5)))
    ending = ending_next_boost(draws_before)

    out: list[dict[str, Any]] = []
    for i, nums in enumerate(port):
        if i == 0 and replace_slots > 0:
            hy = hybrid_ending(
                nums,
                pool_sets,
                draws_before,
                ending,
                min_vote=min_vote,
                replace_slots=replace_slots,
            )
            out.append(
                {
                    "nums": hy["nums"],
                    "method": "portfolio_aux_div_ending_r1",
                    "n_replaced": hy.get("n_replaced", 0),
                    "portfolio_index": i,
                    "meta": hy,
                }
            )
        else:
            out.append(
                {
                    "nums": nums,
                    "method": "portfolio_aux_div",
                    "n_replaced": 0,
                    "portfolio_index": i,
                    "meta": {"seed": {"nums": nums}},
                }
            )
    return out[:k]


def meta_picker_status() -> dict[str, Any]:
    from pathlib import Path
    import json

    root = Path(__file__).resolve().parents[2]
    bench = root / "docs" / "benchmarks" / "20260726_신뢰_odd_even_순위장선택"
    port = bench / "portfolio_wf_summary.json"
    trust = bench / "summary.json"
    out: dict[str, Any] = {
        "ui_enabled": False,
        "default_method": "portfolio_aux_div K=3",
        "reason": "포트폴리오 채택·단장 UI는 oracle 대비 아직 보류",
    }
    if port.exists():
        p = json.loads(port.read_text(encoding="utf-8"))
        out["portfolio"] = {
            "avg_best": p.get("avg_portfolio3_best"),
            "avg_aux1": p.get("avg_aux1"),
            "adopt": p.get("adopt_portfolio"),
        }
        # enable meta API use (not full UI) when portfolio adopted
        out["api_assemble_ready"] = bool(p.get("adopt_portfolio"))
    if trust.exists():
        t = json.loads(trust.read_text(encoding="utf-8"))
        out["trust"] = t.get("trust_brain_vs_random")
        out["odd_even"] = t.get("decisions", {}).get("odd_even")
    return out
