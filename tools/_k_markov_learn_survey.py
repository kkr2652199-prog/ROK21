# -*- coding: utf-8 -*-
"""K-MARKOV-LEARN-SURVEY — markov learn_state 배선 QUICK gate (READ-ONLY live WF).

A baseline_markov_old: stored brain_review + wire quota (learn 미소비 markov)
B markov_learn_wired: live WF 3뇌 재예측 + wired markov (K-F)
PASS: markov_learn_wired ge3 > 0.1218 AND p < 0.15
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.bench_quick_gate import (  # noqa: E402
    DRAW_END,
    DRAW_START,
    MC_SEED,
    NULL_GE3,
    QUICK_N_EVAL,
    WIRE_PIN_GE3,
    WIRE_PIN_MEAN,
    enrich_metrics,
    filter_draw_rows,
    gate_criteria_doc,
    resolve_eval_window,
)
from tools._k_window_signal_survey import (  # noqa: E402
    _live_candidates,
)

from app.testlotto.brains.coordinator import (  # noqa: E402
    apply_coordinator_scoring,
    apply_markov_wire_quota,
)
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402

random.seed(MC_SEED)

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260801_KMARKOV_LEARN_survey.json"
OUT_MD = ROOT / "reports" / "20260801_KMARKOV_LEARN_SURVEY.md"
DRIVE_MD = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

POOL_BRAINS = ("stat", "markov", "review")
STRATEGIES = ("baseline_markov_old", "markov_learn_wired")
LIVE_BASELINE_GE3 = 0.1218
PASS_P_MAX = 0.15
SURVEY_ID = "K-MARKOV-LEARN-SURVEY"


def _load_stored_by_draw(
    draw_start: int, draw_end: int
) -> dict[int, dict[str, list[dict]]]:
    conn = get_lotto_db()
    by_dn: dict[int, dict[str, list[dict]]] = defaultdict(
        lambda: {b: [] for b in POOL_BRAINS}
    )
    for r in conn.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE brain_tag IN (?,?,?) AND draw_no BETWEEN ? AND ?",
        (*POOL_BRAINS, draw_start, draw_end),
    ):
        dn, tag = int(r["draw_no"]), str(r["brain_tag"])
        if tag not in POOL_BRAINS:
            continue
        try:
            raw = json.loads(r["predicted_sets_json"] or "[]")
        except json.JSONDecodeError:
            continue
        cands: list[dict] = []
        for i, s in enumerate(raw[:5]):
            nums = [int(x) for x in (s.get("nums") or [])]
            if len(nums) != 6:
                continue
            sn = int(s.get("set_no") or s.get("pred_set_no") or (i + 1))
            cands.append(
                {
                    "nums": nums,
                    "brain_tag": tag,
                    "method": s.get("method") or tag,
                    "confidence": float(s.get("confidence") or 50),
                    "reasoning": s.get("reasoning") or "",
                    "set_no": sn,
                    "pred_set_no": sn,
                }
            )
        by_dn[dn][tag] = cands
    conn.close()
    return {dn: dict(v) for dn, v in by_dn.items()}


def _best_match(selected: list[dict], actual: set[int]) -> int:
    if not selected:
        return 0
    return max(len(set(int(x) for x in c["nums"]) & actual) for c in selected)


def run_survey() -> dict[str, Any]:
    init_lotto_db()
    eval_window = resolve_eval_window(
        n_eval=QUICK_N_EVAL,
        draw_start=DRAW_START,
        draw_end=DRAW_END,
        sample_mode="tail",
    )

    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    rows = filter_draw_rows(rows, eval_window)

    stored = _load_stored_by_draw(
        int(rows[0]["draw_no"]) if rows else eval_window.draw_start,
        int(rows[-1]["draw_no"]) if rows else eval_window.draw_end,
    )

    acc: dict[str, list[int]] = {s: [] for s in STRATEGIES}
    means: dict[str, list[float]] = {s: [] for s in STRATEGIES}

    t0 = time.time()
    for ri, row in enumerate(rows):
        if ri % 50 == 0:
            print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        # A: stored brain_review (old markov, no learn wiring)
        by_brain = stored.get(draw_no) or {}
        if all(len(by_brain.get(b) or []) >= 5 for b in POOL_BRAINS):
            flat_a: list[dict] = []
            for b in POOL_BRAINS:
                flat_a.extend(by_brain[b])
            scored_a = apply_coordinator_scoring(flat_a, draws, draw_no)
            issued_a = apply_markov_wire_quota(scored_a)
            best_a = _best_match(issued_a, actual)
            acc["baseline_markov_old"].append(best_a)
            means["baseline_markov_old"].append(float(best_a))

        # B: live WF all 3 brains (markov learn wired)
        random.seed(MC_SEED)
        live_cands = _live_candidates(draws, draw_no)
        scored_b = apply_coordinator_scoring(live_cands, draws, draw_no)
        issued_b = apply_markov_wire_quota(scored_b)
        best_b = _best_match(issued_b, actual)
        acc["markov_learn_wired"].append(best_b)
        means["markov_learn_wired"].append(float(best_b))

    n_eval = len(acc["markov_learn_wired"])
    elapsed = round(time.time() - t0, 1)

    strategies_out: dict[str, Any] = {}
    wired = None
    for strat in STRATEGIES:
        bests = acc[strat]
        n = len(bests)
        ge3_c = sum(1 for x in bests if x >= 3)
        ge4_c = sum(1 for x in bests if x >= 4)
        mean_v = sum(means[strat]) / n if n else 0.0
        base = enrich_metrics(ge3_c, n, mean_v, gate_mode="quick")
        base["delta_ge3_vs_live_baseline"] = round(base["ge3_rate"] - LIVE_BASELINE_GE3, 4)
        strategies_out[strat] = {
            **base,
            "ge4_rate": round(ge4_c / n, 4) if n else 0.0,
            "ge4_count": ge4_c,
            "pipeline": (
                "stored brain_review + wire quota"
                if strat == "baseline_markov_old"
                else "live WF 3뇌 + markov learn_state wired"
            ),
        }
        if strat == "markov_learn_wired":
            wired = strategies_out[strat]

    pass_gate = bool(
        wired
        and wired["ge3_rate"] > LIVE_BASELINE_GE3
        and wired["p_value"] < PASS_P_MAX
    )

    before_ge3 = strategies_out.get("baseline_markov_old", {}).get("ge3_rate")
    after_ge3 = wired["ge3_rate"] if wired else None

    out: dict[str, Any] = {
        "id": SURVEY_ID,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": elapsed,
        "n_eval": n_eval,
        "draw_range": [int(rows[0]["draw_no"]), int(rows[-1]["draw_no"])] if rows else [],
        "seed": MC_SEED,
        "gate_mode": "quick",
        "null_ge3": NULL_GE3,
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "live_baseline_ge3": LIVE_BASELINE_GE3,
        "pass_ge3_min": LIVE_BASELINE_GE3,
        "pass_p_max": PASS_P_MAX,
        "strategies": strategies_out,
        "before_after": {
            "baseline_markov_old_ge3": before_ge3,
            "markov_learn_wired_ge3": after_ge3,
            "delta_ge3": round((after_ge3 or 0) - (before_ge3 or 0), 4)
            if after_ge3 is not None and before_ge3 is not None
            else None,
        },
        "gates": {
            "quick_pass": pass_gate,
            "criterion": f"markov_learn_wired ge3 > {LIVE_BASELINE_GE3} AND p < {PASS_P_MAX}",
            "criteria_doc": gate_criteria_doc(),
        },
        "pass_gate": pass_gate,
        "verdict": "PASS" if pass_gate else "FAIL",
        "recommended_next": (
            "K-MARKOV-LEARN-FULL" if pass_gate else "K-ATTACK-HOLD"
        ),
        "db_code_write": False,
        "coordinator_modified": False,
        "predict_flow_shaman_modified": True,
        "predict_markov_hook": "visit_post_process",
    }
    return out


def _write_report(out: dict[str, Any]) -> None:
    n = out["n_eval"]
    wired = out["strategies"]["markov_learn_wired"]
    old = out["strategies"].get("baseline_markov_old", {})
    ba = out.get("before_after") or {}

    lines = [
        f"# {SURVEY_ID} — markov learn_state 배선 QUICK survey",
        "",
        f"날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · **{out['verdict']}** · "
        f"seed={out['seed']} · n={n} · gate=quick",
        "",
        "## 1. 📋 선생님이 준 숙제",
        "| 항목 | 내용 |",
        "|------|------|",
        f"| **ID** | {SURVEY_ID} |",
        "| **질문** | markov visit_count에 learn_state(carry/ending/overdue) 배선 시 live WF ge3가 live baseline(0.1218)을 넘는가? |",
        f"| **PASS** | markov_learn_wired ge3 > {LIVE_BASELINE_GE3} AND p < {PASS_P_MAX} |",
        "| **금지** | random.choices · _get_draws_before · boost cap · coordinator quota · DB reset |",
        "",
        "## 2. 🔧 학생이 한 일",
        "| 항목 | 값 |",
        "|------|-----|",
        "| 도구 | `tools/_k_markov_learn_survey.py` |",
        "| 배선 | `predict_flow_shaman.apply_markov_learn_boost` (survey용 · **FAIL 후 롤백**) |",
        f"| n_eval | {n} · draw {out['draw_range']} · seed={out['seed']} |",
        "| coordinator_modified | false |",
        "",
        "## 3. 📊 풀이",
        "| strategy | pipeline | ge3_rate | mean | p | Δlive_base | Δpin |",
        "|----------|----------|--------:|-----:|--:|-----------:|-----:|",
        f"| baseline_markov_old | stored review | {old.get('ge3_rate', '—')} | {old.get('mean', '—')} | {old.get('p_value', '—')} | {old.get('delta_ge3_vs_live_baseline', '—')} | {old.get('delta_ge3_vs_pin', '—')} |",
        f"| **markov_learn_wired** | live WF wired | **{wired['ge3_rate']}** | **{wired['mean']}** | **{wired['p_value']}** | **{wired.get('delta_ge3_vs_live_baseline')}** | **{wired['delta_ge3_vs_pin']}** |",
        "",
        "## 4. ✅/❌ 맞은·틀린 것",
        f"- pass_gate: **{out['pass_gate']}** · criterion: ge3>{LIVE_BASELINE_GE3} p<{PASS_P_MAX}",
        f"- wired ge3={wired['ge3_rate']} p={wired['p_value']}",
        f"- recommended_next: **{out['recommended_next']}**",
        "",
        "## 5. 📝 복습",
        "- K-F: markov learn_state 소비 경로 추가 (K-ARCHITECTURE-REVIEW 미작동 항목)",
        "- stored baseline vs live wired 비교 — pin(0.1447)과 live baseline(0.1218) 혼동 금지",
        "",
        "## 6. 📎 근거 (null · live_baseline · pin)",
        "| label | ge3 | mean | 출처 |",
        "|-------|----:|-----:|------|",
        f"| null | **{NULL_GE3}** | 0.8000 | theory E[match] |",
        f"| live_baseline | **{LIVE_BASELINE_GE3}** | — | K-10SET-DET-LAB-FULL collapse |",
        f"| pin (WIRE-V2) | **{WIRE_PIN_GE3}** | **{WIRE_PIN_MEAN}** | stored verify FULL1182 |",
        f"| JSON | `{OUT_JSON}` | | |",
        "",
        "## 7. before / after (K-F 배선)",
        "| | ge3_rate | mean | p |",
        "|---|--------:|-----:|--:|",
        f"| before (stored markov old) | {ba.get('baseline_markov_old_ge3')} | {old.get('mean')} | {old.get('p_value')} |",
        f"| after (markov_learn_wired) | {ba.get('markov_learn_wired_ge3')} | {wired['mean']} | {wired['p_value']} |",
        f"| Δge3 | **{ba.get('delta_ge3')}** | — | — |",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE_MD.parent.mkdir(parents=True, exist_ok=True)
    DRIVE_MD.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_MD}", flush=True)
    print(f"wrote {DRIVE_MD}", flush=True)


def main() -> None:
    print(
        f"{SURVEY_ID} QUICK n={QUICK_N_EVAL} draw tail seed={MC_SEED}",
        flush=True,
    )
    out = run_survey()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON}", flush=True)
    _write_report(out)
    wired = out["strategies"]["markov_learn_wired"]
    print(
        f"verdict={out['verdict']}: wired ge3={wired['ge3_rate']} p={wired['p_value']} "
        f"old ge3={out['strategies']['baseline_markov_old']['ge3_rate']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
