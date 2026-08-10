# -*- coding: utf-8 -*-
"""K-STAT-PATTERN-TUNE — stat HINT 창(miss_pattern)만 스윕.

원칙: 공유=lotto_draws만. markov/review SCORE/BLEND/HINT 불변. ge3 미사용.
축: HINT_SPEC_BY_BRAIN['stat'] = (weeks, 'miss_pattern')
게이트:
  · top15_hit(cand) > top15_hit(base)
  · |Δhit| ≥ ABS_THR
  · 독립성: |prefer−base|<ISO · |prize−base|<ISO
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260810_KSTAT_PATTERN_TUNE.json"
OUT_MD = ROOT / "reports" / "20260810_KSTAT_PATTERN_TUNE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
SWEEP_WEEKS = [13, 20, 26, 39, 52]
CURRENT_WEEKS = 26
SIGNAL = "miss_pattern"
WARM_BACK = 80
ABS_THR = 0.005
ISO_THR = 0.005

CAND_A = {
    "stat": (0.25, 0.35, 0.40),
    "markov": (0.55, 0.20, 0.25),
    "review": (0.55, 0.20, 0.25),
}


def _precheck() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.shared import crowd_signal as cs

    spec = sp.HINT_SPEC_BY_BRAIN.get("stat")
    weights = {k: tuple(sp.SCORE_WEIGHTS_BY_BRAIN[k]) for k in ("stat", "markov", "review")}
    ok_spec = spec == (CURRENT_WEEKS, SIGNAL)
    ok_w = weights == CAND_A
    blend = dict(cs.BLEND_STRENGTH_BY_BRAIN)
    return {
        "stat_hint_spec": list(spec) if spec else None,
        "spec_ok": ok_spec,
        "weights_ok": ok_w,
        "weights": {k: list(v) for k, v in weights.items()},
        "blend_by_brain": blend,
        "ok": ok_spec and ok_w,
    }


def _patch_stat_weeks(weeks: int) -> Callable[[], None]:
    import app.testlotto.signal_pool as sp

    saved = dict(sp.HINT_SPEC_BY_BRAIN)
    sp.HINT_SPEC_BY_BRAIN = dict(saved)
    sp.HINT_SPEC_BY_BRAIN["stat"] = (int(weeks), SIGNAL)
    # markov/review 고정
    sp.HINT_SPEC_BY_BRAIN["markov"] = saved["markov"]
    sp.HINT_SPEC_BY_BRAIN["review"] = saved["review"]

    def restore() -> None:
        sp.HINT_SPEC_BY_BRAIN.clear()
        sp.HINT_SPEC_BY_BRAIN.update(saved)

    return restore


def _run_one(seed: int, weeks: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import (
        _actual,
        _fw_proxy,
        _set_weights,
        _top15,
    )

    restore = _patch_stat_weeks(weeks)
    saved_w = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    _set_weights(sp, CAND_A)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer_all: list[float] = []
        prize_all: list[float] = []
        hit_all: list[float] = []

        for dno in range(LO, HI + 1):
            sp.set_learn_as_of(dno)
            draws = sp._get_draws_before(dno)
            if len(draws) < 50:
                continue
            fw = _fw_proxy(draws)
            all_mean = mean(fw[n] for n in range(1, 46))
            if all_mean <= 1e-12:
                continue
            random.seed(seed)
            pool = sp.expand_pool(draws, dno, seed=seed)
            pool_br = sp._pool_by_brain(pool)
            num_ema, pos_ema = learner.snapshot()
            hint_by = sp.build_hint_by_brain(draws, dno)
            fallback = sp._build_hint(draws, dno)
            scores = {}
            for tag in sp.BRAIN_TAGS:
                scores[tag] = sp.number_scores(
                    pool_br.get(tag, []),
                    hint_by.get(tag, fallback),
                    num_ema,
                    pos_ema,
                    brain_tag=tag,
                )
            prefer_all.append(mean(fw[n] for n in _top15(scores["markov"])) - all_mean)
            prize_all.append(mean(fw[n] for n in _top15(scores["review"])) - all_mean)
            actual = _actual(dno)
            hit_all.append(len(set(_top15(scores["stat"])) & actual) / 6.0)
            learner.update_from_pool(pool_br, actual)

        return {
            "seed": seed,
            "n": len(hit_all),
            "stat_top15_hit": round(mean(hit_all), 6) if hit_all else None,
            "prefer_mean": round(mean(prefer_all), 6) if prefer_all else None,
            "prize_mean": round(mean(prize_all), 6) if prize_all else None,
        }
    finally:
        sp.SCORE_WEIGHTS_BY_BRAIN.clear()
        sp.SCORE_WEIGHTS_BY_BRAIN.update(saved_w)
        restore()


def _aggregate(
    weeks: int,
    by_seed: list[dict[str, Any]],
    *,
    base_hit: float | None,
    base_prefer: float | None,
    base_prize: float | None,
) -> dict[str, Any]:
    hit = mean(d["stat_top15_hit"] for d in by_seed if d["stat_top15_hit"] is not None)
    prefer = mean(d["prefer_mean"] for d in by_seed if d["prefer_mean"] is not None)
    prize = mean(d["prize_mean"] for d in by_seed if d["prize_mean"] is not None)

    is_base = weeks == CURRENT_WEEKS
    if is_base:
        cond_improve = True
        cond_abs = True
        abs_d = 0.0
        prefer_iso = True
        prize_iso = True
        prefer_drift = 0.0
        prize_drift = 0.0
    else:
        assert base_hit is not None and base_prefer is not None and base_prize is not None
        abs_d = abs(hit - base_hit)
        prefer_drift = abs(prefer - base_prefer)
        prize_drift = abs(prize - base_prize)
        cond_improve = hit > base_hit
        cond_abs = abs_d >= ABS_THR
        prefer_iso = prefer_drift < ISO_THR
        prize_iso = prize_drift < ISO_THR

    gate_pass = bool(cond_improve and cond_abs and prefer_iso and prize_iso)
    return {
        "stat_weeks": weeks,
        "stat_top15_hit_mean": round(hit, 6),
        "prefer_delta_mean": round(prefer, 6),
        "prize_delta_mean": round(prize, 6),
        "gate_pass": gate_pass,
        "gate_detail": {
            "cond_improve": cond_improve,
            "cond_abs": cond_abs,
            "abs_dhit": round(abs_d, 6),
            "prefer_iso": prefer_iso,
            "prize_iso": prize_iso,
            "prefer_drift": round(prefer_drift, 6),
            "prize_drift": round(prize_drift, 6),
            "is_baseline": is_base,
        },
        "per_seed": by_seed,
    }


def _select_best(results: list[dict[str, Any]]) -> tuple[int | None, str]:
    passers = [
        r for r in results if r["gate_pass"] and r["stat_weeks"] != CURRENT_WEEKS
    ]
    if not passers:
        return None, "게이트 통과 개선 후보 없음"
    win = max(passers, key=lambda r: r["stat_top15_hit_mean"])
    return win["stat_weeks"], (
        f"hit 최대 weeks={win['stat_weeks']} "
        f"(hit={win['stat_top15_hit_mean']}, "
        f"prefer_drift={win['gate_detail']['prefer_drift']}, "
        f"prize_drift={win['gate_detail']['prize_drift']})"
    )


def _verdict(results: list[dict[str, Any]], best: int | None) -> str:
    improve = [
        r for r in results if r["gate_pass"] and r["stat_weeks"] != CURRENT_WEEKS
    ]
    if improve and best is not None and best != CURRENT_WEEKS:
        return "APPLY_CANDIDATE"
    return "NO_IMPROVE"


def _write_md(payload: dict[str, Any]) -> None:
    rows = []
    for r in payload["results"]:
        g = r["gate_detail"]
        rows.append(
            f"| {r['stat_weeks']} | {r['stat_top15_hit_mean']:.6f} | "
            f"{r['prefer_delta_mean']:+.6f} | {r['prize_delta_mean']:+.6f} | "
            f"{g['prefer_drift']:.4f}/{g['prize_drift']:.4f} | "
            f"{'Y' if r['gate_pass'] else 'N'} | "
            f"{g['cond_improve']}/{g['cond_abs']}/{g['prefer_iso']}/{g['prize_iso']} |"
        )
    md = f"""# K-STAT-PATTERN-TUNE

📅 2026-08-10 KST · **wire=False**(측정) · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_stat_pattern_hint_tune.py`  
원칙: **공유=lotto_draws만** · stat HINT 창만 스윕 · markov/review 고정

## 사전확인
- HINT_SPEC stat=({CURRENT_WEEKS}, {SIGNAL}) → {'OK' if payload['precheck']['spec_ok'] else 'FAIL'}
- SCORE_WEIGHTS=cand_A → {'OK' if payload['precheck']['weights_ok'] else 'FAIL'}
- BLEND_BY_BRAIN: {payload['precheck']['blend_by_brain']}

## 스윕
- weeks: {payload['sweep_range']}
- seeds: {payload['seeds']}
- draws: {payload['draw_range']}
- base hit@{CURRENT_WEEKS}: **{payload['base_hit']:.6f}**
- ABS_THR={ABS_THR} · ISO_THR={ISO_THR}

## 결과표

| weeks | top15_hit | preferΔ | prizeΔ | drift p/z | gate | ↑/|Δ|/iso |
|------:|----------:|--------:|-------:|----------:|:----:|:---------:|
{chr(10).join(rows)}

## 판정
- **best_weeks** = `{payload['best_weeks']}`
- **verdict** = **{payload['verdict']}**
- reason: {payload['best_reason']}

## 커서 의견
{payload['cursor_opinion']}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")


def main() -> int:
    pre = _precheck()
    if not pre["ok"]:
        print("PRECHECK_FAIL", json.dumps(pre, ensure_ascii=False, indent=2))
        return 2

    print("PRECHECK_OK", pre)
    print(f"== weeks={CURRENT_WEEKS} (base) ==")
    base_runs = [_run_one(s, CURRENT_WEEKS) for s in SEEDS]
    base_agg = _aggregate(
        CURRENT_WEEKS, base_runs, base_hit=None, base_prefer=None, base_prize=None
    )
    base_hit = base_agg["stat_top15_hit_mean"]
    base_prefer = base_agg["prefer_delta_mean"]
    base_prize = base_agg["prize_delta_mean"]
    print(
        f"  hit={base_hit} prefer={base_prefer} prize={base_prize} "
        f"gate={base_agg['gate_pass']}"
    )

    results: list[dict[str, Any]] = []
    for w in SWEEP_WEEKS:
        if w == CURRENT_WEEKS:
            results.append(base_agg)
            continue
        print(f"== weeks={w} ==")
        runs = [_run_one(s, w) for s in SEEDS]
        agg = _aggregate(
            w,
            runs,
            base_hit=base_hit,
            base_prefer=base_prefer,
            base_prize=base_prize,
        )
        print(
            f"  hit={agg['stat_top15_hit_mean']} gate={agg['gate_pass']} "
            f"detail={agg['gate_detail']}"
        )
        results.append(agg)

    results.sort(key=lambda r: r["stat_weeks"])
    best, reason = _select_best(results)
    verdict = _verdict(results, best)

    if verdict == "APPLY_CANDIDATE":
        opinion = (
            f"best_weeks={best} — `HINT_SPEC_BY_BRAIN['stat']=({best}, miss_pattern)` "
            f"교체 후보. markov/review HINT·BLEND 불변."
        )
    else:
        opinion = (
            f"개선 게이트 통과 후보 없음. stat HINT weeks={CURRENT_WEEKS} HOLD. "
            "다음 권장: SCORE_WEIGHTS_BY_BRAIN['stat'] 단독 스윕 또는 ④합동 smoke."
        )

    payload = {
        "id": "K-STAT-PATTERN-TUNE",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "knob": "HINT_SPEC_BY_BRAIN['stat'].weeks",
        "precheck": pre,
        "sweep_range": SWEEP_WEEKS,
        "seeds": SEEDS,
        "draw_range": [LO, HI],
        "base_hit": base_hit,
        "base_prefer_delta": base_prefer,
        "base_prize_delta": base_prize,
        "abs_thr": ABS_THR,
        "iso_thr": ISO_THR,
        "results": [
            {k: v for k, v in r.items() if k != "per_seed"}
            | {"per_seed_n": len(r.get("per_seed", []))}
            for r in results
        ],
        "results_detail": results,
        "best_weeks": best,
        "best_reason": reason,
        "verdict": verdict,
        "current_weeks": CURRENT_WEEKS,
        "cursor_opinion": opinion,
        "wire": False,
        "ge3_used": False,
        "independence": {
            "shared": "lotto_draws only",
            "tuned_knob": "HINT_SPEC_BY_BRAIN['stat']",
            "frozen": ["markov HINT/BLEND", "review HINT/BLEND", "SCORE_WEIGHTS"],
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_md(payload)
    print("VERDICT", verdict, "best", best)
    print("WROTE", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
