# -*- coding: utf-8 -*-
"""K-REVIEW-QUOTA-SIM — review quota 증가 live coordinator 경로 시뮬.

path: predict_sets → aux → dedup → dynamic_brain_quota(BENCH_FIXED)
DB INSERT/UPDATE 없음 · 종료 시 BENCH_FIXED_QUOTA=None 원복 필수.
Usage:
  python tools/_k_review_quota_sim.py
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KREVIEW_QUOTA_SIM.json"
OUT_MD = ROOT / "reports" / "20260805_KREVIEW_QUOTA_SIM.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1036, 1235
SEEDS = (42, 0, 7)

SCENARIOS: list[tuple[str, dict[str, int]]] = [
    ("A_stat0_markov80_review20", {"stat": 0, "markov": 4, "review": 1}),
    ("B_markov70_review30", {"stat": 0, "markov": 3, "review": 2}),
    ("C_markov60_review40", {"stat": 0, "markov": 3, "review": 2}),  # 정수슬롯=B와 동일
    ("D_markov50_review50", {"stat": 0, "markov": 2, "review": 3}),
    ("E_stat10_markov50_review40", {"stat": 1, "markov": 2, "review": 2}),
]


def scenario_verdict(avg: float, delta: float) -> str:
    if avg >= 0.138 and delta > 0:
        return "REVIEW_GAIN"
    if avg < 0.120:
        return "DEGRADED"
    if delta > 0:
        return "MILD_GAIN"
    if delta < 0:
        return "NO_GAIN"
    return "FLAT"


def load_actuals(lo: int, hi: int) -> dict[int, set[int]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (lo, hi),
    ).fetchall()
    conn.close()
    return {
        int(dict(r)["draw_no"]): {int(dict(r)[f"num{k}"]) for k in range(1, 7)}
        for r in rows
    }


def fuse_one(dno: int, actual: set[int]) -> tuple[int, dict[str, int]]:
    """live coordinator 발권 경로 in-memory · DB 미기록."""
    import app.testlotto.brains.coordinator as coord
    from app.testlotto.brains.coordinator import (
        PREDICT_BRAINS,
        PREDICT_MODULES,
        SETS_PER_PREDICT_BRAIN,
        _apply_aux_scoring,
        _seed_independent_brain,
        dynamic_brain_quota,
    )
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.ticket_dedup import dedup_enabled, dedup_ticket_list

    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    if not draws:
        return 0, {}

    candidates: list[dict] = []
    for brain in PREDICT_BRAINS:
        tag = brain["tag"]
        mod = PREDICT_MODULES[tag]
        _seed_independent_brain(dno)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            conf = float(s.get("confidence", 60))
            candidates.append({**s, "confidence": conf, "pred_set_no": sn, "set_no": sn})

    scored = _apply_aux_scoring(candidates, draws, dno)
    scored.sort(key=lambda x: x["confidence"], reverse=True)

    if dedup_enabled():

        def _regen(brain_tag: str, seen: set[tuple[int, ...]], replace_of: dict | None = None):
            mod = PREDICT_MODULES.get(brain_tag)
            if mod is None:
                return None
            _seed_independent_brain(dno)
            raw = mod.predict_sets(draws, 1)
            if not raw:
                return None
            return _apply_aux_scoring(raw, draws, dno)[0]

        scored, _ = dedup_ticket_list(scored, regenerate=_regen)
        scored.sort(key=lambda x: x["confidence"], reverse=True)

    issued = dynamic_brain_quota(scored)
    slot_c: dict[str, int] = {"stat": 0, "markov": 0, "review": 0}
    best = 0
    for pred in issued:
        tag = str(pred.get("brain_tag") or "")
        if tag in slot_c:
            slot_c[tag] += 1
        nums = [int(x) for x in pred["nums"]]
        best = max(best, len(set(nums) & actual))
    return best, slot_c


def run_scenario(
    label: str,
    slots: dict[str, int],
    seed: int,
    actuals: dict[int, set[int]],
) -> dict[str, Any]:
    import app.testlotto.brains.coordinator as coord

    coord.BENCH_FIXED_QUOTA = dict(slots)
    coord.BRAIN_RNG_SEED_BASE = int(seed)
    assert coord.BENCH_FIXED_QUOTA == slots

    bests: list[int] = []
    slot_sum = {"stat": 0, "markov": 0, "review": 0}
    t0 = time.time()
    total = HI - LO + 1
    for i, dno in enumerate(range(LO, HI + 1), 1):
        random.seed(int(seed) + int(dno))
        best, sc = fuse_one(dno, actuals[dno])
        bests.append(best)
        for k in slot_sum:
            slot_sum[k] += sc.get(k, 0)
        if i % 50 == 0 or i == total:
            print(
                f"  [{label} s{seed} {i}/{total}] best={best} "
                f"elapsed={time.time()-t0:.0f}s",
                flush=True,
            )

    n = len(bests)
    ge3_count = sum(1 for b in bests if b >= 3)
    return {
        "ge3": round(ge3_count / n, 6) if n else 0.0,
        "mean": round(mean(bests), 6) if n else 0.0,
        "ge3_count": ge3_count,
        "n": n,
        "avg_slots": {k: round(slot_sum[k] / n, 4) for k in slot_sum} if n else {},
        "elapsed_sec": round(time.time() - t0, 1),
    }


def confirm_rollback() -> bool:
    import app.testlotto.brains.coordinator as coord

    coord.BENCH_FIXED_QUOTA = None
    coord.BRAIN_RNG_SEED_BASE = 42
    # also ensure source file still None (we only mutate runtime)
    text = (ROOT / "app" / "testlotto" / "brains" / "coordinator.py").read_text(
        encoding="utf-8"
    )
    file_ok = "BENCH_FIXED_QUOTA: dict[str, int] | None = None" in text
    runtime_ok = coord.BENCH_FIXED_QUOTA is None
    return file_ok and runtime_ok


def write_md(p: dict[str, Any]) -> str:
    lines = [
        "# K-REVIEW-QUOTA-SIM — review quota live 경로 시뮬 (2026-08-05)",
        "",
        f"- **판정:** `{p['verdict']}` · wire=`{p['wire']}`",
        f"- path: `{p['path']}`",
        f"- range: {p['draw_range']} n={p['n_draws']} · seeds={p['seeds']}",
        f"- rollback_confirmed=**{p['rollback_confirmed']}**",
        "",
        "## baseline A",
        "",
        f"```json\n{json.dumps(p['baseline'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## scenarios",
        "",
        "| 시나리오 | slots | avg_ge3 | range | Δ vs A | verdict |",
        "|----------|-------|---------|-------|--------|---------|",
    ]
    for k, sc in p["scenarios"].items():
        lines.append(
            f"| {k} | `{sc['slots']}` | **{sc['avg_ge3']}** | {sc['range_ge3']} | "
            f"{sc['delta_vs_baseline']:+.4f} | {sc['verdict']} |"
        )
    lines += [
        "",
        "## best",
        "",
        f"```json\n{json.dumps(p['best_scenario'], ensure_ascii=False, indent=2)}\n```",
        "",
        f"- note: C 슬롯은 B와 동일(0/3/2) · 정수 배분 한계",
        f"- tool: `tools/_k_review_quota_sim.py`",
        f"- JSON: `docs/benchmarks/{OUT_JSON.name}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    import app.testlotto.brains.coordinator as coord

    # safety: start from None
    coord.BENCH_FIXED_QUOTA = None
    coord.BRAIN_RNG_SEED_BASE = 42

    actuals = load_actuals(LO, HI)
    assert len(actuals) == HI - LO + 1

    results: dict[str, dict[str, Any]] = {}
    # C 슬롯 == B → 재실행 생략(정수 배분 동일)
    slot_key = lambda s: (s["stat"], s["markov"], s["review"])
    done_by_slots: dict[tuple[int, int, int], str] = {}
    try:
        for label, slots in SCENARIOS:
            sk = slot_key(slots)
            if sk in done_by_slots:
                src = done_by_slots[sk]
                print(f"=== {label} slots={slots} · COPY from {src} ===", flush=True)
                results[label] = dict(results[src])
                results[label] = {
                    **results[src],
                    "slots": slots,
                    "copied_from": src,
                }
                continue
            print(f"=== {label} slots={slots} ===", flush=True)
            by_seed: dict[str, dict[str, Any]] = {}
            for seed in SEEDS:
                by_seed[str(seed)] = run_scenario(label, slots, seed, actuals)
                # restore between seeds too
                coord.BENCH_FIXED_QUOTA = None
            ge3s = [by_seed[str(s)]["ge3"] for s in SEEDS]
            avg = round(mean(ge3s), 6)
            rng = round(max(ge3s) - min(ge3s), 6)
            results[label] = {
                "slots": slots,
                "by_seed": {
                    str(s): {
                        "ge3": by_seed[str(s)]["ge3"],
                        "mean": by_seed[str(s)]["mean"],
                    }
                    for s in SEEDS
                },
                "avg_ge3": avg,
                "range_ge3": rng,
                "detail": by_seed,
            }
            done_by_slots[sk] = label
            print(f"  => avg_ge3={avg} range={rng}", flush=True)
    finally:
        rollback_ok = confirm_rollback()
        print("ROLLBACK runtime+file None:", rollback_ok, "FIXED=", coord.BENCH_FIXED_QUOTA)

    base = results["A_stat0_markov80_review20"]
    baseline = {
        "label": "A_stat0_markov80_review20",
        "slots": base["slots"],
        "by_seed": base["by_seed"],
        "avg_ge3": base["avg_ge3"],
        "range_ge3": base["range_ge3"],
    }

    scenarios_out: dict[str, Any] = {}
    best_label = "A_stat0_markov80_review20"
    best_avg = baseline["avg_ge3"]
    for label, slots in SCENARIOS:
        if label.startswith("A_"):
            continue
        r = results[label]
        delta = round(r["avg_ge3"] - baseline["avg_ge3"], 6)
        v = scenario_verdict(r["avg_ge3"], delta)
        scenarios_out[label] = {
            "slots": r["slots"],
            "by_seed": r["by_seed"],
            "avg_ge3": r["avg_ge3"],
            "range_ge3": r["range_ge3"],
            "delta_vs_baseline": delta,
            "verdict": v,
            "note": "슬롯=B와 동일" if label.startswith("C_") else "",
        }
        # best among B-E (and vs baseline)
        if r["avg_ge3"] > best_avg:
            best_avg = r["avg_ge3"]
            best_label = label

    if best_label.startswith("A_"):
        best_scenario = {
            "label": best_label,
            "avg_ge3": baseline["avg_ge3"],
            "delta_vs_baseline": 0.0,
            "slots": baseline["slots"],
            "note": "테스트 시나리오 전부 baseline 미상회",
        }
    else:
        best_scenario = {
            "label": best_label,
            "avg_ge3": results[best_label]["avg_ge3"],
            "delta_vs_baseline": round(
                results[best_label]["avg_ge3"] - baseline["avg_ge3"], 6
            ),
            "slots": results[best_label]["slots"],
        }

    payload = {
        "id": "K-REVIEW-QUOTA-SIM",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": f"BEST_SCENARIO: {best_scenario['label']}",
        "wire": False,
        "path": "live coordinator BENCH_FIXED_QUOTA · brains.predict_sets → aux → dedup → quota (in-memory · no DB write)",
        "draw_range": [LO, HI],
        "n_draws": HI - LO + 1,
        "seeds": list(SEEDS),
        "baseline": baseline,
        "scenarios": scenarios_out,
        "best_scenario": best_scenario,
        "rollback_confirmed": confirm_rollback(),
        "forbid": [
            "pool_view_cache 재조합 경로",
            "random.choices",
            "_get_draws_before mutate",
            "engine.py",
            "auto-tune",
            "DB INSERT/UPDATE",
            "BENCH_FIXED_QUOTA 원복 누락",
        ],
        "pass": True,
        "tool": "tools/_k_review_quota_sim.py",
        "prior": "docs/benchmarks/20260805_KSTAT_SEED_DIAG.json",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = write_md(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        DRIVE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"drive copy skip: {e}", file=sys.stderr)

    print(
        json.dumps(
            {
                "ok": True,
                "baseline_avg": baseline["avg_ge3"],
                "best": best_scenario,
                "rollback": payload["rollback_confirmed"],
                "FIXED": __import__(
                    "app.testlotto.brains.coordinator", fromlist=["BENCH_FIXED_QUOTA"]
                ).BENCH_FIXED_QUOTA,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
