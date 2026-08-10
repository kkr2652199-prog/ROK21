# -*- coding: utf-8 -*-
"""K-BLEND-STRENGTH-SWEEP — 단일 BLEND_STRENGTH 스윕 (wire=False).

측정만. SCORE_WEIGHTS/cand_A 고정. ge3 미사용.
BLEND_STRENGTH 기본인자는 정의시점 고정이므로 blend_weights를 런타임 패치한다.
"""
from __future__ import annotations

import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260810_KBLEND_STRENGTH_SWEEP.json"
OUT_MD = ROOT / "reports" / "20260810_KBLEND_STRENGTH_SWEEP.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
PRIOR = ROOT / "docs" / "benchmarks" / "20260810_KGENSPARK_IDEA_CHECK.json"

LO, HI = 1100, 1235
SEEDS = [0, 42, 123, 999, 7]
SWEEP = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75]
CURRENT = 0.55
WARM_BACK = 80
ABS_THR = 0.01

CAND_A = {
    "stat": (0.25, 0.35, 0.40),
    "markov": (0.55, 0.20, 0.25),
    "review": (0.55, 0.20, 0.25),
}


def _precheck() -> dict[str, Any]:
    from app.testlotto.brains.shared import crowd_signal as cs
    import app.testlotto.signal_pool as sp

    blend = float(cs.BLEND_STRENGTH)
    weights = {k: tuple(sp.SCORE_WEIGHTS_BY_BRAIN[k]) for k in ("stat", "markov", "review")}
    ok_blend = abs(blend - CURRENT) < 1e-12
    ok_w = weights == CAND_A
    prior_ok = False
    if PRIOR.exists():
        prior = json.loads(PRIOR.read_text(encoding="utf-8"))
        prior_ok = bool(prior.get("pass") is True)
    return {
        "blend_ok": ok_blend,
        "blend": blend,
        "weights_ok": ok_w,
        "weights": {k: list(v) for k, v in weights.items()},
        "prior_pass": prior_ok,
        "ok": ok_blend and ok_w and prior_ok,
    }


def _patch_blend(strength: float) -> Callable[[], None]:
    """엔진이 strength 없이 호출해도 스윕값이 쓰이도록 blend_weights 교체."""
    from app.testlotto.brains.shared import crowd_signal as cs

    orig = cs.blend_weights
    saved_const = cs.BLEND_STRENGTH

    def wrapped(
        base: dict[int, float],
        table: dict[int, float],
        *,
        strength: float | None = None,
        brain: str | None = None,
    ) -> dict[int, float]:
        # 스윕값 강제. brain 인자는 호환용(구 공용 스윕).
        use = float(strength) if strength is not None else float(cs.BLEND_STRENGTH)
        return orig(base, table, strength=use, brain=brain)

    cs.BLEND_STRENGTH = float(strength)
    cs.blend_weights = wrapped  # type: ignore[assignment]

    def restore() -> None:
        cs.BLEND_STRENGTH = saved_const
        cs.blend_weights = orig  # type: ignore[assignment]

    return restore


def _run_one(seed: int, blend: float) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import (
        _actual,
        _fw_proxy,
        _set_weights,
        _top15,
    )

    restore = _patch_blend(blend)
    saved_w = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    _set_weights(sp, CAND_A)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prize_early: list[float] = []
        prize_mid: list[float] = []
        prize_late: list[float] = []
        prefer_all: list[tuple[int, float]] = []
        prize_all: list[float] = []

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
            prefer_d = mean(fw[n] for n in _top15(scores["markov"])) - all_mean
            prize_d = mean(fw[n] for n in _top15(scores["review"])) - all_mean
            prefer_all.append((dno, prefer_d))
            prize_all.append(prize_d)
            if LO <= dno <= LO + 44:
                prize_early.append(prize_d)
            elif LO + 45 <= dno <= LO + 89:
                prize_mid.append(prize_d)
            else:
                prize_late.append(prize_d)
            learner.update_from_pool(pool_br, _actual(dno))

        mid = (LO + HI) // 2
        pref_lo = [v for d, v in prefer_all if d <= mid]
        pref_hi = [v for d, v in prefer_all if d > mid]
        return {
            "seed": seed,
            "n": len(prize_all),
            "prize_mean": round(mean(prize_all), 6) if prize_all else None,
            "prefer_mean": round(mean(v for _, v in prefer_all), 6) if prefer_all else None,
            "prefer_first_half": round(mean(pref_lo), 6) if pref_lo else None,
            "prefer_second_half": round(mean(pref_hi), 6) if pref_hi else None,
            "prefer_split_both_pos": bool(
                pref_lo and pref_hi and mean(pref_lo) > 0 and mean(pref_hi) > 0
            ),
            "consistent_neg": all(
                mean(xs) < 0 for xs in (prize_early, prize_mid, prize_late) if xs
            ),
            "early_mean": round(mean(prize_early), 6) if prize_early else None,
            "mid_mean": round(mean(prize_mid), 6) if prize_mid else None,
            "late_mean": round(mean(prize_late), 6) if prize_late else None,
        }
    finally:
        sp.SCORE_WEIGHTS_BY_BRAIN.clear()
        sp.SCORE_WEIGHTS_BY_BRAIN.update(saved_w)
        restore()


def _aggregate(blend: float, by_seed: list[dict[str, Any]], base_prize: float | None) -> dict[str, Any]:
    prize_by = {f"seed_{d['seed']}": d["prize_mean"] for d in by_seed}
    prefer_by = {f"seed_{d['seed']}": d["prefer_mean"] for d in by_seed}
    prize_mean = mean(d["prize_mean"] for d in by_seed if d["prize_mean"] is not None)
    prefer_mean = mean(d["prefer_mean"] for d in by_seed if d["prefer_mean"] is not None)
    pref_lo_m = mean(d["prefer_first_half"] for d in by_seed if d["prefer_first_half"] is not None)
    pref_hi_m = mean(d["prefer_second_half"] for d in by_seed if d["prefer_second_half"] is not None)
    split_rate = mean(1.0 if d["prefer_split_both_pos"] else 0.0 for d in by_seed)
    cn_rate = mean(1.0 if d["consistent_neg"] else 0.0 for d in by_seed)
    prefer_split_both_pos = bool(pref_lo_m > 0 and pref_hi_m > 0)

    is_base = abs(blend - CURRENT) < 1e-12
    cond1_dir = prize_mean < 0
    if is_base:
        cond1 = cond1_dir
        cond3_abs = 0.0
        cond3 = True  # baseline — 개선임계 면제
    else:
        assert base_prize is not None
        cond1 = cond1_dir and (prize_mean < base_prize)
        cond3_abs = abs(prize_mean - base_prize)
        cond3 = cond3_abs >= ABS_THR
    cond2 = (prefer_mean > 0) and prefer_split_both_pos
    gate_pass = bool(cond1 and cond2 and cond3)

    return {
        "blend": blend,
        "prize_delta_mean": round(prize_mean, 6),
        "prize_delta_by_seed": prize_by,
        "prefer_delta_mean": round(prefer_mean, 6),
        "prefer_delta_by_seed": prefer_by,
        "prefer_split_both_pos": prefer_split_both_pos,
        "prefer_split_both_pos_rate": round(split_rate, 4),
        "prefer_first_half_mean": round(pref_lo_m, 6),
        "prefer_second_half_mean": round(pref_hi_m, 6),
        "consistent_neg_rate": round(cn_rate, 4),
        "gate_pass": gate_pass,
        "gate_detail": {
            "cond1": cond1,
            "cond2": cond2,
            "cond3": cond3,
            "cond3_abs": round(cond3_abs, 6),
            "is_baseline": is_base,
            "aux_cn_ge_2_3": cn_rate >= (2.0 / 3.0),
        },
        "per_seed": by_seed,
    }


def _select_best(results: list[dict[str, Any]]) -> tuple[float | None, str]:
    passers = [r for r in results if r["gate_pass"] and abs(r["blend"] - CURRENT) > 1e-12]
    # 개선 후보만 (base 제외). base는 게이트 면제라 별도.
    if not passers:
        return None, "게이트 통과 개선 후보 없음"

    best_prize = min(passers, key=lambda r: r["prize_delta_mean"])
    best_prefer = max(passers, key=lambda r: r["prefer_delta_mean"])
    if abs(best_prize["blend"] - best_prefer["blend"]) < 1e-12:
        b = best_prize["blend"]
        return b, (
            f"best_prize==best_prefer={b} "
            f"(prize={best_prize['prize_delta_mean']}, prefer={best_prefer['prefer_delta_mean']})"
        )

    # rank: prize 더 음수=1, prefer 더 양수=1
    prize_ord = sorted(passers, key=lambda r: r["prize_delta_mean"])  # asc
    prefer_ord = sorted(passers, key=lambda r: -r["prefer_delta_mean"])  # desc
    prize_rank = {r["blend"]: i + 1 for i, r in enumerate(prize_ord)}
    prefer_rank = {r["blend"]: i + 1 for i, r in enumerate(prefer_ord)}
    scored = []
    for r in passers:
        avg_r = (prize_rank[r["blend"]] + prefer_rank[r["blend"]]) / 2.0
        scored.append((avg_r, r["prize_delta_mean"], -r["prefer_delta_mean"], r))
    scored.sort(key=lambda t: (t[0], t[1], t[2]))
    win = scored[0][3]
    return win["blend"], (
        f"합산rank 최적={win['blend']} "
        f"(prize_rank={prize_rank[win['blend']]}, prefer_rank={prefer_rank[win['blend']]}, "
        f"avg={scored[0][0]:.2f}; best_prize={best_prize['blend']}, "
        f"best_prefer={best_prefer['blend']})"
    )


def _verdict(
    results: list[dict[str, Any]], best: float | None
) -> str:
    base = next(r for r in results if abs(r["blend"] - CURRENT) < 1e-12)
    # ROLLBACK: 현재값이 방향(cond1_dir via prize<0) 또는 cond2 실패
    # baseline gate_detail.cond1 = prize<0, cond2 = prefer
    if not base["gate_detail"]["cond1"] or not base["gate_detail"]["cond2"]:
        return "ROLLBACK_CANDIDATE"
    improve = [r for r in results if r["gate_pass"] and abs(r["blend"] - CURRENT) > 1e-12]
    if improve and best is not None and abs(best - CURRENT) > 1e-12:
        return "APPLY_CANDIDATE"
    return "NO_IMPROVE"


def _write_md(payload: dict[str, Any]) -> None:
    rows = []
    for r in payload["results"]:
        g = r["gate_detail"]
        rows.append(
            f"| {r['blend']:.2f} | {r['prize_delta_mean']:+.6f} | "
            f"{r['prefer_delta_mean']:+.6f} | {r['consistent_neg_rate']:.2f} | "
            f"{'Y' if r['gate_pass'] else 'N'} | "
            f"{g['cond1']}/{g['cond2']}/{g['cond3']} | {g['cond3_abs']:.4f} |"
        )
    md = f"""# K-BLEND-STRENGTH-SWEEP

📅 2026-08-10 KST · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_blend_strength_sweep.py`  
선행: `20260810_KGENSPARK_IDEA_CHECK.json` pass={payload['precheck']['prior_pass']}

## 사전확인
- BLEND_STRENGTH 코드값={payload['precheck']['blend']} (기대 0.55) → {'OK' if payload['precheck']['blend_ok'] else 'FAIL'}
- SCORE_WEIGHTS_BY_BRAIN=cand_A → {'OK' if payload['precheck']['weights_ok'] else 'FAIL'}

## 스윕
- range: {payload['sweep_range']}
- seeds: {payload['seeds']}
- draws: {payload['draw_range']} (n=136)
- base prize@{CURRENT}: **{payload['base_prize_delta']:.6f}**

## 결과표

| blend | prizeΔ mean | preferΔ mean | cn_rate | gate | c1/c2/c3 | |Δprize| |
|------:|------------:|-------------:|--------:|:----:|:--------:|--------:|
{chr(10).join(rows)}

## 판정
- **best_blend** = `{payload['best_blend']}`
- **verdict** = **{payload['verdict']}**
- reason: {payload['best_reason']}

## 커서 의견
{payload['cursor_opinion']}

## 금지 준수
coordinator/engine/random.choices/_get_draws_before/SCORE_WEIGHTS/ge3/DB쓰기 — 미접촉.
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")


def main() -> int:
    pre = _precheck()
    if not pre["ok"]:
        print("PRECHECK_FAIL", json.dumps(pre, ensure_ascii=False, indent=2))
        OUT_JSON.write_text(
            json.dumps(
                {
                    "id": "K-BLEND-STRENGTH-SWEEP",
                    "precheck": pre,
                    "verdict": "ABORT_PRECHECK",
                    "wire": False,
                    "ge3_used": False,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 2

    print("PRECHECK_OK", pre)
    # base 먼저
    print(f"== blend={CURRENT} (base) ==")
    base_seed_runs = [_run_one(s, CURRENT) for s in SEEDS]
    base_agg = _aggregate(CURRENT, base_seed_runs, base_prize=None)
    base_prize = base_agg["prize_delta_mean"]
    print(
        f"  prize={base_prize} prefer={base_agg['prefer_delta_mean']} "
        f"cn={base_agg['consistent_neg_rate']} gate={base_agg['gate_pass']}"
    )

    results: list[dict[str, Any]] = []
    for b in SWEEP:
        if abs(b - CURRENT) < 1e-12:
            results.append(base_agg)
            continue
        print(f"== blend={b} ==")
        runs = [_run_one(s, b) for s in SEEDS]
        agg = _aggregate(b, runs, base_prize=base_prize)
        print(
            f"  prize={agg['prize_delta_mean']} prefer={agg['prefer_delta_mean']} "
            f"cn={agg['consistent_neg_rate']} gate={agg['gate_pass']} "
            f"detail={agg['gate_detail']}"
        )
        results.append(agg)

    # SWEEP 순서 유지
    results.sort(key=lambda r: r["blend"])
    best, reason = _select_best(results)
    verdict = _verdict(results, best)

    if verdict == "APPLY_CANDIDATE":
        opinion = (
            f"best={best} 가 게이트 통과·현재 {CURRENT} 대비 prize 더 음수·|Δ|≥{ABS_THR}. "
            "형 GO 후 `crowd_signal.BLEND_STRENGTH` 교체만 하면 됨(SCORE_WEIGHTS 불변). "
            "추가 검증 권고: APPLY 직후 seed 5회 smoke로 cn_rate·prefer split 재확인."
        )
    elif verdict == "ROLLBACK_CANDIDATE":
        opinion = (
            f"현재 {CURRENT} 가 prize<0 또는 prefer 축 실패. "
            "형 GO 전 0.40 복원 후보 검토. 스윕 통과값이 있으면 그 값 우선 보고."
        )
    else:
        opinion = (
            f"개선 게이트 통과 후보 없음(또는 best={CURRENT}). "
            "현재값 유지 HOLD. 뇌별 W 분리·stat 튜닝으로 확대하지 말 것."
        )

    payload = {
        "id": "K-BLEND-STRENGTH-SWEEP",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "precheck": pre,
        "sweep_range": SWEEP,
        "seeds": SEEDS,
        "draw_range": [LO, HI],
        "base_prize_delta": base_prize,
        "results": [
            {k: v for k, v in r.items() if k != "per_seed"} | {"per_seed_n": len(r.get("per_seed", []))}
            for r in results
        ],
        "results_detail": results,
        "best_blend": best,
        "best_reason": reason,
        "verdict": verdict,
        "current_blend": CURRENT,
        "cursor_opinion": opinion,
        "wire": False,
        "ge3_used": False,
        "note_blend_patch": (
            "blend_weights default arg는 import시 고정 → 스윕 중 "
            "cs.BLEND_STRENGTH 설정 + blend_weights 래퍼로 강제 적용(코드 파일 미수정)."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_md(payload)
    print("VERDICT", verdict, "best", best)
    print("WROTE", OUT_JSON)
    print("WROTE", OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
