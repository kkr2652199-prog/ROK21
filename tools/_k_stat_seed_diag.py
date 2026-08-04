# -*- coding: utf-8 -*-
"""K-STAT-SEED-DIAG — 뇌별 seed 안정성 진단 (wire 없음 · DB 쓰기 없음).

signal_pool.build_pool_and_repack 과 동일 경로를 WF 증분으로 재현.
Usage:
  python tools/_k_stat_seed_diag.py
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KSTAT_SEED_DIAG.json"
OUT_MD = ROOT / "reports" / "20260805_KSTAT_SEED_DIAG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1136, 1235
SEEDS = (42, 0, 7, 99, 1)
BRAINS = ("stat", "markov", "review")


def sensitivity(range_ge3: float) -> str:
    if range_ge3 >= 0.10:
        return "HIGH_SENSITIVITY"
    if range_ge3 >= 0.05:
        return "MODERATE"
    return "STABLE"


def shannon_entropy(counts: Counter[int], *, n_symbols: int = 45) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for n in range(1, n_symbols + 1):
        c = counts.get(n, 0)
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log(p, 2)
    return round(h, 6)


def slot_entropy(sets: list[list[int]]) -> float:
    if not sets:
        return 0.0
    ents = []
    for slot in range(6):
        c: Counter[int] = Counter()
        for nums in sets:
            sn = sorted(nums)
            c[sn[slot]] += 1
        ents.append(shannon_entropy(c))
    return round(mean(ents), 6)


def diversity_block(sets: list[list[int]]) -> dict[str, Any]:
    freq: Counter[int] = Counter()
    sums: list[int] = []
    for nums in sets:
        for n in nums:
            freq[int(n)] += 1
        sums.append(sum(nums))
    total_num_slots = sum(freq.values()) or 1
    top3 = freq.most_common(3)
    top3_rate = round(sum(c for _, c in top3) / total_num_slots, 6)
    return {
        "n_sets": len(sets),
        "top3_nums": [{"num": n, "count": c} for n, c in top3],
        "top3_rate": top3_rate,
        "sum_mean": round(mean(sums), 6) if sums else 0.0,
        "sum_std": round(pstdev(sums), 6) if len(sums) > 1 else 0.0,
        "sum_min": min(sums) if sums else 0,
        "sum_max": max(sums) if sums else 0,
        "entropy": shannon_entropy(freq),
        "slot_entropy": slot_entropy(sets),
        "biased": top3_rate > 0.30,
    }


def summarize_ge3(by_seed: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ge3s = [float(v["ge3"]) for v in by_seed.values()]
    r = round(max(ge3s) - min(ge3s), 6) if ge3s else 0.0
    return {
        "mean_ge3": round(mean(ge3s), 6) if ge3s else 0.0,
        "std_ge3": round(pstdev(ge3s), 6) if len(ge3s) > 1 else 0.0,
        "min_ge3": round(min(ge3s), 6) if ge3s else 0.0,
        "max_ge3": round(max(ge3s), 6) if ge3s else 0.0,
        "range_ge3": r,
        "sensitivity": sensitivity(r),
    }


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


def run_seed_walk(
    seed: int,
    lo: int,
    hi: int,
    actuals: dict[int, set[int]],
    *,
    collect_stat_sets: bool = False,
) -> tuple[dict[str, dict[str, Any]], list[list[int]]]:
    """한 seed로 lo~hi WF · DB 쓰기 없음."""
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.signal_pool import (
        RollingSignalLearner,
        _build_hint,
        _get_draws_before,
        _pool_by_brain,
        expand_pool,
        repack_by_brain,
        warm_learner_to_draw,
    )

    learner = RollingSignalLearner()
    warm_from = max(1, lo - 200)
    warm_learner_to_draw(learner, warm_from, lo, seed=seed)

    bests: dict[str, list[int]] = {b: [] for b in BRAINS}
    means: dict[str, list[float]] = {b: [] for b in BRAINS}
    stat_sets: list[list[int]] = []

    for dno in range(lo, hi + 1):
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        if not draws:
            continue
        num_ema, pos_ema = learner.snapshot()
        random.seed(seed)
        pool = expand_pool(draws, dno, seed=seed)
        pool_br = _pool_by_brain(pool)
        hint = _build_hint(draws, dno)
        repacked = repack_by_brain(
            pool_br, hint, num_ema, pos_ema, target_draw_no=dno
        )
        by_tag: dict[str, list[list[int]]] = {b: [] for b in BRAINS}
        for c in repacked:
            tag = str(c.get("brain_tag") or "")
            if tag in by_tag:
                by_tag[tag].append([int(x) for x in c["nums"]])

        actual = actuals[dno]
        for tag in BRAINS:
            hits = [len(set(nums) & actual) for nums in by_tag[tag][:5]]
            if not hits:
                continue
            bests[tag].append(max(hits))
            means[tag].append(mean(hits))
            if collect_stat_sets and tag == "stat":
                stat_sets.extend(by_tag[tag][:5])

        # WF learner update (actual known after predict — same as warm)
        learner.update_from_pool(pool_br, actual)

    out: dict[str, dict[str, Any]] = {}
    for tag in BRAINS:
        b = bests[tag]
        n = len(b)
        ge3_count = sum(1 for x in b if x >= 3)
        out[tag] = {
            "ge3": round(ge3_count / n, 6) if n else 0.0,
            "mean": round(mean(b), 6) if n else 0.0,
            "ge3_count": ge3_count,
            "n": n,
            "mean_of_set_means": round(mean(means[tag]), 6) if means[tag] else 0.0,
        }
    return out, stat_sets


def write_md(p: dict[str, Any]) -> str:
    lines = [
        "# K-STAT-SEED-DIAG — 뇌 seed 안정성 진단 (2026-08-05)",
        "",
        f"- **판정(stat):** `{p['verdict']}` · wire=`{p['wire']}` · n={p['n_draws']} ({p['draw_range'][0]}~{p['draw_range'][1]})",
        f"- seeds: `{p['seeds_tested']}` · eval=best_of_5 · path=signal_pool hybrid/repack (DB 미쓰기)",
        "",
        "## 뇌별 ge3 (시드)",
        "",
    ]
    for brain in BRAINS:
        sm = p[brain]["summary"]
        lines += [
            f"### {brain} · sensitivity=**{sm['sensitivity']}** · range={sm['range_ge3']}",
            "",
            "| seed | ge3 | mean | ge3_count |",
            "|------|-----|------|-----------|",
        ]
        for s in p["seeds_tested"]:
            row = p[brain]["by_seed"][str(s)]
            lines.append(
                f"| {s} | {row['ge3']} | {row['mean']} | {row.get('ge3_count', '')} |"
            )
        lines += [
            f"| **mean/std** | **{sm['mean_ge3']}** / {sm['std_ge3']} | min={sm['min_ge3']} max={sm['max_ge3']} | |",
            "",
        ]
    lines += [
        "## pool_diversity (stat · seed42 vs seed0)",
        "",
        f"```json\n{json.dumps(p['pool_diversity'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## cross_compare",
        "",
        f"```json\n{json.dumps(p['cross_compare'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## implication",
        "",
        f"```json\n{json.dumps(p['implication'], ensure_ascii=False, indent=2)}\n```",
        "",
        f"- tool: `tools/_k_stat_seed_diag.py`",
        f"- JSON: `docs/benchmarks/{OUT_JSON.name}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    actuals = load_actuals(LO, HI)
    assert len(actuals) == HI - LO + 1, f"expected 100 draws, got {len(actuals)}"

    by_brain_seed: dict[str, dict[str, dict[str, Any]]] = {b: {} for b in BRAINS}
    div42: dict[str, Any] = {}
    div0: dict[str, Any] = {}

    t0 = time.time()
    for seed in SEEDS:
        collect = seed in (42, 0)
        print(f"[seed={seed}] walk {LO}~{HI} collect_stat={collect}", flush=True)
        metrics, stat_sets = run_seed_walk(
            seed, LO, HI, actuals, collect_stat_sets=collect
        )
        for tag in BRAINS:
            by_brain_seed[tag][str(seed)] = metrics[tag]
        print(
            f"  stat={metrics['stat']['ge3']} markov={metrics['markov']['ge3']} "
            f"review={metrics['review']['ge3']} elapsed={time.time()-t0:.0f}s",
            flush=True,
        )
        if seed == 42:
            div42 = diversity_block(stat_sets)
        elif seed == 0:
            div0 = diversity_block(stat_sets)

    summaries = {b: summarize_ge3(by_brain_seed[b]) for b in BRAINS}
    # overall verdict follows STAT (지시 목적)
    verdict = summaries["stat"]["sensitivity"]
    if verdict == "MODERATE":
        # schema binary uses HIGH if ≥0.05; keep MODERATE as finer label, map overall
        pass

    ranges = {b: summaries[b]["range_ge3"] for b in BRAINS}
    most_stable = min(ranges, key=ranges.get)
    most_sensitive = max(ranges, key=ranges.get)
    diversity_gap = round(abs(div42.get("entropy", 0) - div0.get("entropy", 0)), 6)
    biased = bool(div42.get("biased") or div0.get("biased"))

    safe = summaries["stat"]["sensitivity"] == "STABLE"
    if summaries["stat"]["sensitivity"] == "HIGH_SENSITIVITY":
        next_rec = "pool 안정화 선행 (seed 민감) · quota 증가 HOLD"
    elif summaries["stat"]["sensitivity"] == "MODERATE":
        next_rec = "소규모 quota만 허용 · live coordinator 경로 재측정 후 GO"
    else:
        next_rec = "quota 증가 후보 재검토 가능 · live coordinator 경로 검증 필수"

    payload = {
        "id": "K-STAT-SEED-DIAG",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "wire": False,
        "draw_range": [LO, HI],
        "n_draws": HI - LO + 1,
        "seeds_tested": list(SEEDS),
        "path": "signal_pool.expand_pool+repack_by_brain (hy_p45_r123 / markov baseline) · SELECT-ONLY",
        "stat": {"by_seed": by_brain_seed["stat"], "summary": summaries["stat"]},
        "markov": {"by_seed": by_brain_seed["markov"], "summary": summaries["markov"]},
        "review": {"by_seed": by_brain_seed["review"], "summary": summaries["review"]},
        "pool_diversity": {
            "stat_seed42": {
                "top3_rate": div42.get("top3_rate", 0.0),
                "sum_mean": div42.get("sum_mean", 0.0),
                "sum_std": div42.get("sum_std", 0.0),
                "entropy": div42.get("entropy", 0.0),
                "slot_entropy": div42.get("slot_entropy", 0.0),
                "detail": div42,
            },
            "stat_seed0": {
                "top3_rate": div0.get("top3_rate", 0.0),
                "sum_mean": div0.get("sum_mean", 0.0),
                "sum_std": div0.get("sum_std", 0.0),
                "entropy": div0.get("entropy", 0.0),
                "slot_entropy": div0.get("slot_entropy", 0.0),
                "detail": div0,
            },
            "diversity_gap": diversity_gap,
            "verdict": "BIASED" if biased else "DIVERSE",
        },
        "cross_compare": {
            "most_stable_brain": most_stable,
            "most_sensitive_brain": most_sensitive,
            "stat_vs_markov_range_diff": round(
                summaries["stat"]["range_ge3"] - summaries["markov"]["range_ge3"], 6
            ),
            "note": (
                "hybrid solo best_of_5 · QUOTA-D-WIRE 괴리 가설(stat seed 민감) 검증용 · "
                "발권 ge3 약속 금지"
            ),
        },
        "implication": {
            "quota_increase_safe": safe,
            "recommended_next": next_rec,
        },
        "forbid": [
            "random.choices",
            "_get_draws_before mutate",
            "engine.py",
            "auto-tune",
            "wire",
            "DB INSERT/UPDATE",
        ],
        "pass": True,
        "tool": "tools/_k_stat_seed_diag.py",
        "prior": "docs/benchmarks/20260805_KQUOTA_D_WIRE.json",
        "elapsed_sec": round(time.time() - t0, 1),
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
                "verdict": verdict,
                "stat": summaries["stat"],
                "markov": summaries["markov"],
                "review": summaries["review"],
                "pool": payload["pool_diversity"]["verdict"],
                "safe": safe,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
