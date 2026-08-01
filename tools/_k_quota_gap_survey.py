# -*- coding: utf-8 -*-
"""K-QUOTA-GAP-SURVEY — wire/selection strategy compare on coordinator FULL path (READ-ONLY).

Production stack:
  HINT_WEIGHT=0.15 · LEARN_WIRED=True · AUX_1TO1_ENABLED=True
  quota markov=3 stat=1 review=1 (total 5)

Strategies (selection functions in this tool only — coordinator.py unchanged):
  set_no_asc · conf_quota · conf_global_top5 · aux_hint_quota · oracle_best15 (ref)

n=200 · draw 1035~1234 · seed=42
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import coordinator as coord_mod  # noqa: E402
from app.testlotto.brains.coordinator import (  # noqa: E402
    BRAIN_DEDICATED_AUX,
    PREDICT_MODULES,
    _apply_aux_scoring,
    apply_markov_wire_quota,
)
from app.testlotto.brains.markov_brain import learn as markov_learn  # noqa: E402
from app.testlotto.brains.markov_brain import predict as markov_predict  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.brains.review_brain import predict as review_predict  # noqa: E402
from app.testlotto.brains.stat_brain import predict as stat_predict  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

SEED = 42
N_EVAL = 200
DRAW_START = 1035
DRAW_END = 1234
HINT_WEIGHT = 0.15
TARGET_N = 5
OUT = ROOT / "docs" / "benchmarks" / "20260801_KQUOTA_GAP_survey.json"

QUOTA: dict[str, int] = {"markov": 3, "stat": 1, "review": 1}
REF_V2_PIN_GE3 = 0.1447
REF_ARCH_NOTE_GAP = 0.436  # architecture note ~43.6% (full n=1182 prior)


def _apply_production_flags() -> None:
    stat_predict.HINT_WEIGHT = HINT_WEIGHT
    markov_predict.HINT_WEIGHT = HINT_WEIGHT
    review_predict.HINT_WEIGHT = HINT_WEIGHT
    markov_learn.LEARN_WIRED = True
    coord_mod.AUX_1TO1_ENABLED = True


def _aux_hint_score(c: dict, draws: list[dict], draw_no: int) -> float:
    """Dedicated aux raw score (0~1) — rerank_by_aux aux_s equivalent."""
    if "aux_hint_score" in c and c["aux_hint_score"] is not None:
        return float(c["aux_hint_score"])
    tag = str(c.get("brain_tag") or "")
    dedicated = BRAIN_DEDICATED_AUX.get(tag)
    if dedicated is None:
        return float(c.get("confidence") or 0)
    try:
        return float(
            dedicated.score_set(c["nums"], draws, draw_no, brain_tag=tag)
        )
    except Exception:
        return float(c.get("confidence") or 0)


def _enrich_aux_hint(scored: list[dict], draws: list[dict], draw_no: int) -> list[dict]:
    out: list[dict] = []
    for c in scored:
        ah = _aux_hint_score(c, draws, draw_no)
        out.append({**c, "aux_hint_score": round(ah, 4)})
    return out


def _select_set_no_asc(candidates: list[dict]) -> list[dict]:
    """Replicate apply_markov_wire_quota (production baseline)."""
    return apply_markov_wire_quota(candidates)


def _select_conf_quota(candidates: list[dict]) -> list[dict]:
    brain_buckets: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        tag = str(c.get("brain_tag", "") or "")
        if tag in QUOTA:
            brain_buckets[tag].append(c)

    selected: list[dict] = []
    for tag, cap in QUOTA.items():
        bucket = sorted(
            brain_buckets.get(tag) or [],
            key=lambda x: float(x.get("confidence") or 0),
            reverse=True,
        )
        selected.extend(bucket[:cap])

    if len(selected) < TARGET_N:
        used = {id(c) for c in selected}
        remainder = sorted(
            [c for c in candidates if id(c) not in used],
            key=lambda x: float(x.get("confidence") or 0),
            reverse=True,
        )
        for c in remainder:
            selected.append(c)
            if len(selected) >= TARGET_N:
                break
    return selected[:TARGET_N]


def _select_conf_global_top5(candidates: list[dict]) -> list[dict]:
    return sorted(
        candidates, key=lambda x: float(x.get("confidence") or 0), reverse=True
    )[:TARGET_N]


def _select_aux_hint_quota(candidates: list[dict]) -> list[dict]:
    brain_buckets: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        tag = str(c.get("brain_tag", "") or "")
        if tag in QUOTA:
            brain_buckets[tag].append(c)

    selected: list[dict] = []
    for tag, cap in QUOTA.items():
        bucket = sorted(
            brain_buckets.get(tag) or [],
            key=lambda x: (
                float(x.get("aux_hint_score") or 0),
                float(x.get("confidence") or 0),
            ),
            reverse=True,
        )
        selected.extend(bucket[:cap])

    if len(selected) < TARGET_N:
        used = {id(c) for c in selected}
        remainder = sorted(
            [c for c in candidates if id(c) not in used],
            key=lambda x: (
                float(x.get("aux_hint_score") or 0),
                float(x.get("confidence") or 0),
            ),
            reverse=True,
        )
        for c in remainder:
            selected.append(c)
            if len(selected) >= TARGET_N:
                break
    return selected[:TARGET_N]


SELECTORS: dict[str, Callable[[list[dict]], list[dict]]] = {
    "set_no_asc": _select_set_no_asc,
    "conf_quota": _select_conf_quota,
    "conf_global_top5": _select_conf_global_top5,
    "aux_hint_quota": _select_aux_hint_quota,
}


def _best_match(candidates: list[dict], actual: set[int]) -> int:
    best = 0
    for c in candidates:
        mc = len(set(int(x) for x in c["nums"]) & actual)
        best = max(best, mc)
    return best


def _generate_scored(draw_no: int) -> tuple[list[dict], list[dict]]:
    """3뇌 predict → aux scoring → aux_hint enrich."""
    set_learn_as_of(draw_no)
    draws = _get_draws_before(draw_no)
    if not draws:
        return [], draws

    candidates: list[dict] = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(SEED)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            candidates.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})

    if not candidates:
        return [], draws

    scored = _apply_aux_scoring(candidates, draws, draw_no)
    scored = _enrich_aux_hint(scored, draws, draw_no)
    return scored, draws


def _walkforward() -> dict[str, Any]:
    _apply_production_flags()

    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    if len(rows) > N_EVAL:
        rows = rows[-N_EVAL:]

    strategy_bests: dict[str, list[int]] = {k: [] for k in SELECTORS}
    strategy_bests["oracle_best15"] = []
    quota_gap_draws = 0

    for row in rows:
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}

        scored, _ = _generate_scored(draw_no)
        if not scored:
            for k in strategy_bests:
                strategy_bests[k].append(0)
            continue

        oracle_best = _best_match(scored, actual)
        strategy_bests["oracle_best15"].append(oracle_best)

        baseline_selected = SELECTORS["set_no_asc"](scored)
        baseline_best = _best_match(baseline_selected, actual)
        if oracle_best > baseline_best:
            quota_gap_draws += 1

        for sid, fn in SELECTORS.items():
            selected = fn(scored)
            strategy_bests[sid].append(_best_match(selected, actual))

    n = len(strategy_bests["set_no_asc"])
    strategies: dict[str, dict[str, Any]] = {}
    for sid, bests in strategy_bests.items():
        ge3_c = sum(1 for x in bests if x >= 3)
        ge3_rate = ge3_c / n if n else 0.0
        mean_match = sum(bests) / n if n else 0.0
        strategies[sid] = {
            "ge3_rate": round(ge3_rate, 6),
            "ge3_count": ge3_c,
            "mean_match": round(mean_match, 6),
            "n_eval": n,
        }

    quota_gap_rate = quota_gap_draws / n if n else 0.0
    return {
        "strategies": strategies,
        "quota_gap": {
            "draws_oracle_gt_set_no_asc": quota_gap_draws,
            "quota_gap_rate": round(quota_gap_rate, 6),
            "baseline_strategy": "set_no_asc",
            "ref_arch_note_rate": REF_ARCH_NOTE_GAP,
            "ref_note": "architecture note ~43.6% from K-BENCH-01 n=1182",
        },
        "n_eval": n,
    }


def _verdict(strategies: dict[str, dict[str, Any]]) -> dict[str, Any]:
    baseline_ge3 = strategies["set_no_asc"]["ge3_rate"]
    beats: list[str] = []
    for sid in ("conf_quota", "conf_global_top5", "aux_hint_quota"):
        if strategies[sid]["ge3_rate"] > baseline_ge3:
            beats.append(sid)

    if beats:
        recommendation = "K-WIRE-SELECT-GO-WAIT"
        note = (
            f"{', '.join(beats)} beat set_no_asc on ge3 — 형 GO for wire change before patch"
        )
        wire_change = "GO-WAIT"
    else:
        recommendation = "K-ATTACK-HOLD"
        note = "No wire candidate beats set_no_asc on ge3 — hold current wire"
        wire_change = "HOLD"

    return {
        "baseline_ge3": baseline_ge3,
        "beats_set_no_asc": beats,
        "recommendation": recommendation,
        "wire_change": wire_change,
        "note": note,
        "auto_wire": False,
    }


def run_survey() -> dict[str, Any]:
    random.seed(SEED)
    wf = _walkforward()
    strategies = wf["strategies"]
    verdict = _verdict(strategies)

    baseline = strategies["set_no_asc"]
    comparison: dict[str, dict[str, float]] = {}
    for sid, m in strategies.items():
        if sid == "oracle_best15":
            comparison[sid] = {
                "delta_ge3_vs_set_no_asc": round(m["ge3_rate"] - baseline["ge3_rate"], 6),
                "oracle_ceiling_uplift": round(m["ge3_rate"] - baseline["ge3_rate"], 6),
            }
        else:
            comparison[sid] = {
                "delta_ge3_vs_set_no_asc": round(m["ge3_rate"] - baseline["ge3_rate"], 6),
                "delta_ge3_vs_v2_pin": round(m["ge3_rate"] - REF_V2_PIN_GE3, 6),
            }

    return {
        "id": "K-QUOTA-GAP-SURVEY",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "draw_range": [DRAW_START, DRAW_END],
        "path": "coordinator_full (C package · 3brain pool + aux scoring + wire alt)",
        "production_stack": {
            "hint_weight": HINT_WEIGHT,
            "learn_wired": True,
            "aux_1to1_enabled": True,
            "wire_baseline": "set_no_asc",
            "quota": dict(QUOTA),
        },
        "strategies": strategies,
        "quota_gap": wf["quota_gap"],
        "comparison": comparison,
        "references": {
            "v2_pin_ge3": REF_V2_PIN_GE3,
            "c_package_complete_ge3": 0.125,
            "arch_note_quota_gap_rate": REF_ARCH_NOTE_GAP,
        },
        "verdict": verdict,
        "note": "READ-ONLY · coordinator.py unchanged · no auto-wire",
    }


def main() -> int:
    result = run_survey()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
