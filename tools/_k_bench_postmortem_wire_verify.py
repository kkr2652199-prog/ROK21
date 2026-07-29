# -*- coding: utf-8 -*-
"""K-BENCH-01-WIRE verify — tier 피드백 배선 live WF (READ-ONLY DB).

PASS: ge3_rate > WIRE_PIN_GE3 (0.1447) AND p < 0.05 vs null.
FAIL: learn_state tier 변경 롤백 권고.
"""
from __future__ import annotations

import copy
import json
import random
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import patch

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
random.seed(42)

from app.testlotto.brains import (  # noqa: E402
    aux_balance_keeper,
    aux_miss_detective,
    aux_pattern_spotlight,
    aux_referee,
    predict_flow_shaman,
    predict_review_king,
    predict_stat_fairy,
)
from app.testlotto.brains.coordinator import apply_markov_wire_quota  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.draw_analysis import detect_missed_patterns  # noqa: E402
from app.testlotto.learn_state import (  # noqa: E402
    PREDICT_BRAIN_TAGS,
    _empty_state,
    get_referee_weights,
)
from app.testlotto.learn_state_cutoff import apply_feedback_pure, set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260729_KBENCH01_WIRE_verify.json"
OUT_MD = ROOT / "reports" / "20260729_KBENCH01_WIRE.md"

DRAW_START = 53
DRAW_END = 1234
WIRE_PIN_GE3 = 0.1447
WIRE_PIN_MEAN = 1.7504
NULL_GE3 = 0.1137
MC_SEED = 42
ALPHA = 0.05

PREDICT_MODULES = {
    "markov": predict_flow_shaman,
    "stat": predict_stat_fairy,
    "review": predict_review_king,
}

AUX_MODULES: dict[str, Any] = {
    "miss": aux_miss_detective,
    "pattern": aux_pattern_spotlight,
    "balance": aux_balance_keeper,
    "referee": aux_referee,
}
AUX_WEIGHTS = [0.25, 0.25, 0.25, 0.25]


@contextmanager
def _in_memory_learn_states(states: dict[str, dict[str, Any]]) -> Iterator[None]:
    def _load(tag: str) -> dict[str, Any]:
        return copy.deepcopy(states.get(tag) or _empty_state())

    with patch("app.testlotto.learn_state.load_learn_state", side_effect=_load):
        with patch(
            "app.testlotto.brains.predict_stat_fairy.load_learn_state",
            side_effect=_load,
        ):
            with patch(
                "app.testlotto.brains.predict_review_king.load_learn_state",
                side_effect=_load,
            ):
                yield


def _aux_composite_score(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    total = 0.0
    for mod, w in zip(AUX_MODULES.values(), AUX_WEIGHTS):
        total += w * mod.score_set(nums, draws, target_draw_no, brain_tag=brain_tag)
    return total


def _aux_individual_scores(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> dict[str, float]:
    return {
        k: round(mod.score_set(nums, draws, target_draw_no, brain_tag=brain_tag), 4)
        for k, mod in AUX_MODULES.items()
    }


def _apply_aux_scoring(
    candidates: list[dict], draws: list[dict], target_draw_no: int
) -> list[dict]:
    ref_weights = get_referee_weights()
    out: list[dict] = []
    for c in candidates:
        tag = c.get("brain_tag", "") or None
        aux_total = _aux_composite_score(c["nums"], draws, target_draw_no, brain_tag=tag)
        base = float(c.get("confidence", 60))
        brain_w = ref_weights.get(c.get("brain_tag", ""), 1.0 / 3)
        final_conf = min(99.5, base * 0.5 * brain_w + aux_total * 40 + base * 0.1)
        out.append(
            {
                **c,
                "aux_total": round(aux_total, 4),
                "aux_scores": _aux_individual_scores(
                    c["nums"], draws, target_draw_no, brain_tag=tag
                ),
                "confidence": round(final_conf, 1),
            }
        )
    return out


def _brain_best_feedback(
    sets: list[dict],
    actual_list: list[int],
    bonus: int,
    draws: list[dict],
) -> tuple[int, int, list[str]]:
    best_mc, best_tier = 0, 0
    best_nums: list[int] = []
    for s in sets:
        scored = score_predicted_set(s.get("nums") or [], actual_list, bonus)
        mc = int(scored["matched_count"])
        tr = int(scored["tier_rank"])
        if mc > best_mc or (mc == best_mc and not best_nums):
            best_mc = mc
            best_tier = tr
            best_nums = [int(x) for x in (s.get("nums") or [])]
    missed = detect_missed_patterns(best_nums, actual_list, draws) if best_nums else []
    return best_mc, best_tier, missed


def run_walkforward() -> tuple[dict[str, Any], int]:
    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()

    brain_states = {tag: _empty_state() for tag in PREDICT_BRAIN_TAGS}
    selected_bests: list[int] = []
    tier_feedback_applied = 0
    tier_momentum_samples: list[float] = []

    with _in_memory_learn_states(brain_states):
        for ri, row in enumerate(rows):
            if ri % 100 == 0:
                print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
            row = dict(row)
            draw_no = int(row["draw_no"])
            actual = {int(row[f"num{k}"]) for k in range(1, 7)}
            bonus = int(row.get("bonus") or 0)
            actual_list = sorted(actual)

            set_learn_as_of(draw_no)
            draws = _get_draws_before(draw_no)
            if not draws:
                continue

            candidates: list[dict] = []
            per_brain_sets: dict[str, list[dict]] = {}
            for tag, mod in PREDICT_MODULES.items():
                sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
                per_brain_sets[tag] = sets
                for i, s in enumerate(sets):
                    sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
                    candidates.append({**s, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})

            if not candidates:
                continue

            scored = _apply_aux_scoring(candidates, draws, draw_no)
            selected = apply_markov_wire_quota(scored)

            selected_best_hit = 0
            for c in selected:
                mc = len(set(int(x) for x in c["nums"]) & actual)
                selected_best_hit = max(selected_best_hit, mc)
            selected_bests.append(selected_best_hit)

            for tag, sets in per_brain_sets.items():
                mc, tier, missed = _brain_best_feedback(sets, actual_list, bonus, draws)
                brain_states[tag] = apply_feedback_pure(
                    brain_states[tag],
                    draw_no,
                    mc,
                    missed,
                    tier_rank=tier,
                )
                tier_feedback_applied += 1
                tm = float(
                    (brain_states[tag].get("adjustments") or {}).get("tier_momentum", 0) or 0
                )
                tier_momentum_samples.append(tm)

    n_eval = len(selected_bests)
    ge3_c = sum(1 for x in selected_bests if x >= 3)
    ge3_rate = round(ge3_c / n_eval, 4) if n_eval else 0.0
    mean_hit = round(sum(selected_bests) / n_eval, 4) if n_eval else 0.0
    p_val = float(binomtest(ge3_c, n_eval, NULL_GE3, alternative="greater").pvalue) if n_eval else 1.0
    verdict = "PASS" if ge3_rate > WIRE_PIN_GE3 and p_val < ALPHA else "FAIL"

    end_states = {
        tag: {
            "tier_history_len": len(st.get("tier_history") or []),
            "recent_tier_ge3_rate": st.get("recent_tier_ge3_rate"),
            "tier_momentum": (st.get("adjustments") or {}).get("tier_momentum"),
            "tier_counts": st.get("tier_counts"),
        }
        for tag, st in brain_states.items()
    }

    result = {
        "id": "K-BENCH-01-WIRE",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "n_eval": n_eval,
        "draw_range": [DRAW_START, DRAW_END],
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "null_ge3": NULL_GE3,
        "mc_seed": MC_SEED,
        "params_wired": {
            "apply_feedback_tier": True,
            "hit_count_stored": True,
            "adjustments_tier_momentum": True,
            "tier_window": 20,
            "coordinator_modified": False,
        },
        "result": {
            "mean_hit_selected_best": mean_hit,
            "ge3_rate": ge3_rate,
            "ge3_count": ge3_c,
            "p_value": round(p_val, 6),
            "delta_ge3_vs_pin": round(ge3_rate - WIRE_PIN_GE3, 4),
        },
        "tier_feedback": {
            "events_applied": tier_feedback_applied,
            "tier_momentum_mean": round(
                sum(tier_momentum_samples) / len(tier_momentum_samples), 4
            )
            if tier_momentum_samples
            else 0.0,
            "end_states": end_states,
        },
        "verdict": verdict,
        "pass": verdict == "PASS",
        "recommended_next": "K-AUX-SIGNAL-SURVEY" if verdict == "PASS" else "ROLLBACK learn_state tier WIRE",
        "db_code_write": False,
    }
    return result, n_eval


def _write_report(out: dict[str, Any]) -> None:
    res = out["result"]
    tf = out.get("tier_feedback") or {}
    verdict = out["verdict"]

    lines = [
        "# K-BENCH-01-WIRE — tier 피드백 배선 검증 (live WF)",
        "",
        f"날짜 {out['ts'][:10]} · **{verdict}** · seed={MC_SEED}",
        "",
        "## SUMMARY (BENCH_PROTOCOL §6)",
        "| label | pipeline | mean | ge3_rate | pin | Δge3 vs pin | p (vs null) | 비고 |",
        "|-------|----------|------|----------|-----|-------------|-------------|------|",
        "| **theory_baseline** | — | 0.8000 | 0.1137 | — | — | — | E[match]=6×6/45 |",
        f"| **WIRE-V2 pin** | stored | {WIRE_PIN_MEAN} | {WIRE_PIN_GE3} | ✓ | — | — | PINNED |",
        f"| **K-BENCH-01-WIRE** | WF live+tier | **{res['mean_hit_selected_best']}** | "
        f"**{res['ge3_rate']}** | — | {res['delta_ge3_vs_pin']:+.4f} | {res['p_value']} | "
        f"n={out['n_eval']} |",
        "",
        "## PASS/FAIL 기준",
        f"- PASS: ge3 > {WIRE_PIN_GE3} **AND** p < {ALPHA}",
        f"- 실측: ge3={res['ge3_rate']} · p={res['p_value']} → **{verdict}**",
        "",
        "## tier 피드백 배선",
        f"- apply_feedback: tier_rank(1~5) + hit_count 저장",
        f"- adjustments.tier_momentum → stat/review 소비",
        f"- 피드백 이벤트: {tf.get('events_applied')} (in-memory, DB write 없음)",
        f"- tier_momentum 평균: {tf.get('tier_momentum_mean')}",
        "",
        "### 종료 learn_state 스냅샷 (stat/review)",
    ]
    for tag in ("stat", "review", "markov"):
        st = (tf.get("end_states") or {}).get(tag, {})
        lines.append(
            f"- **{tag}**: tier_hist={st.get('tier_history_len')} · "
            f"ge3_rate={st.get('recent_tier_ge3_rate')} · "
            f"momentum={st.get('tier_momentum')}"
        )

    lines.extend(
        [
            "",
            "## Verdict / NEXT",
            f"- **verdict:** `{verdict}`",
            f"- **→ `{out['recommended_next']}`**",
            "",
            "---",
            "",
            "## 팩트체크",
            "| 항목 | JSON | 보고서 |",
            "|------|------|------|",
            f"| ge3_rate | {res['ge3_rate']} | {res['ge3_rate']} |",
            f"| p_value | {res['p_value']} | {res['p_value']} |",
            f"| verdict | {verdict} | {verdict} |",
            f"| seed | {MC_SEED} | {MC_SEED} |",
            "",
            f"SSOT=`docs/benchmarks/20260729_KBENCH01_WIRE_verify.json`",
            "",
        ]
    )

    text = "\n".join(lines)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / "20260729_KBENCH01_WIRE.md"
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_MD}", flush=True)


def main() -> None:
    t0 = time.time()
    print(
        f"K-BENCH-01-WIRE verify live WF draws {DRAW_START}~{DRAW_END} seed={MC_SEED}",
        flush=True,
    )
    out, _ = run_walkforward()
    out["elapsed_sec"] = round(time.time() - t0, 1)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON}", flush=True)

    _write_report(out)
    print(f"verdict={out['verdict']} ge3={out['result']['ge3_rate']}", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
