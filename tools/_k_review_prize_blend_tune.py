# -*- coding: utf-8 -*-
"""K-REVIEW-PRIZE-BLEND-TUNE — review BLEND만 스윕 (뇌 독립).

원칙: 공유=lotto_draws만. markov BLEND/W_* 불변. ge3 미사용. wire=False.
게이트( review 축 ):
  · prize_delta(cand) < prize_delta(base)  (더 음수)
  · prize_delta < 0
  · |Δprize| ≥ ABS_THR
  · 독립성: |prefer_delta(cand)−prefer_delta(base)| < PREFER_ISO_THR
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260810_KREVIEW_PRIZE_BLEND_TUNE.json"
OUT_MD = ROOT / "reports" / "20260810_KREVIEW_PRIZE_BLEND_TUNE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
SWEEP = [0.40, 0.50, 0.55, 0.65, 0.75, 0.85]
CURRENT = 0.55
WARM_BACK = 80
ABS_THR = 0.01
PREFER_ISO_THR = 0.005

CAND_A = {
    "stat": (0.25, 0.35, 0.40),
    "markov": (0.55, 0.20, 0.25),
    "review": (0.55, 0.20, 0.25),
}


def _precheck() -> dict[str, Any]:
    from app.testlotto.brains.shared import crowd_signal as cs
    import app.testlotto.signal_pool as sp

    by = dict(cs.BLEND_STRENGTH_BY_BRAIN)
    weights = {k: tuple(sp.SCORE_WEIGHTS_BY_BRAIN[k]) for k in ("stat", "markov", "review")}
    ok_by = (
        abs(float(by.get("markov", -1)) - CURRENT) < 1e-12
        and abs(float(by.get("review", -1)) - CURRENT) < 1e-12
    )
    ok_w = weights == CAND_A
    return {
        "blend_by_brain": by,
        "blend_by_ok": ok_by,
        "weights_ok": ok_w,
        "weights": {k: list(v) for k, v in weights.items()},
        "ok": ok_by and ok_w,
    }


def _patch_review_blend(strength: float) -> Callable[[], None]:
    from app.testlotto.brains.shared import crowd_signal as cs

    saved = dict(cs.BLEND_STRENGTH_BY_BRAIN)
    cs.BLEND_STRENGTH_BY_BRAIN = dict(saved)
    cs.BLEND_STRENGTH_BY_BRAIN["review"] = float(strength)
    cs.BLEND_STRENGTH_BY_BRAIN["markov"] = float(saved.get("markov", CURRENT))

    def restore() -> None:
        cs.BLEND_STRENGTH_BY_BRAIN.clear()
        cs.BLEND_STRENGTH_BY_BRAIN.update(saved)

    return restore


def _run_one(seed: int, review_blend: float) -> dict[str, Any]:
    import random
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import (
        _actual,
        _fw_proxy,
        _set_weights,
        _top15,
    )

    restore = _patch_review_blend(review_blend)
    saved_w = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    _set_weights(sp, CAND_A)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer_all: list[float] = []
        prize_all: list[tuple[int, float]] = []
        prize_early: list[float] = []
        prize_mid: list[float] = []
        prize_late: list[float] = []

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
            prefer_all.append(prefer_d)
            prize_all.append((dno, prize_d))
            if LO <= dno <= LO + 32:
                prize_early.append(prize_d)
            elif LO + 33 <= dno <= LO + 65:
                prize_mid.append(prize_d)
            else:
                prize_late.append(prize_d)
            learner.update_from_pool(pool_br, _actual(dno))

        return {
            "seed": seed,
            "n": len(prize_all),
            "prize_mean": round(mean(v for _, v in prize_all), 6) if prize_all else None,
            "prefer_mean": round(mean(prefer_all), 6) if prefer_all else None,
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


def _aggregate(
    blend: float,
    by_seed: list[dict[str, Any]],
    *,
    base_prize: float | None,
    base_prefer: float | None,
) -> dict[str, Any]:
    prefer_mean = mean(d["prefer_mean"] for d in by_seed if d["prefer_mean"] is not None)
    prize_mean = mean(d["prize_mean"] for d in by_seed if d["prize_mean"] is not None)
    cn_rate = mean(1.0 if d["consistent_neg"] else 0.0 for d in by_seed)

    is_base = abs(blend - CURRENT) < 1e-12
    cond_prize_neg = prize_mean < 0
    if is_base:
        cond_improve = True
        cond_abs = True
        abs_d = 0.0
        prefer_iso = True
        prefer_drift = 0.0
    else:
        assert base_prize is not None and base_prefer is not None
        abs_d = abs(prize_mean - base_prize)
        prefer_drift = abs(prefer_mean - base_prefer)
        cond_improve = prize_mean < base_prize
        cond_abs = abs_d >= ABS_THR
        prefer_iso = prefer_drift < PREFER_ISO_THR

    gate_pass = bool(cond_prize_neg and cond_improve and cond_abs and prefer_iso)
    return {
        "review_blend": blend,
        "prize_delta_mean": round(prize_mean, 6),
        "prefer_delta_mean": round(prefer_mean, 6),
        "consistent_neg_rate": round(cn_rate, 4),
        "gate_pass": gate_pass,
        "gate_detail": {
            "cond_prize_neg": cond_prize_neg,
            "cond_improve": cond_improve,
            "cond_abs": cond_abs,
            "abs_dprize": round(abs_d, 6),
            "prefer_iso": prefer_iso,
            "prefer_drift": round(prefer_drift, 6),
            "is_baseline": is_base,
            "aux_cn_ge_2_3": cn_rate >= (2.0 / 3.0),
        },
        "per_seed": by_seed,
    }


def _select_best(results: list[dict[str, Any]]) -> tuple[float | None, str]:
    passers = [
        r for r in results if r["gate_pass"] and abs(r["review_blend"] - CURRENT) > 1e-12
    ]
    if not passers:
        return None, "게이트 통과 개선 후보 없음"
    win = min(passers, key=lambda r: r["prize_delta_mean"])
    return win["review_blend"], (
        f"prize 최음수={win['review_blend']} "
        f"(prize={win['prize_delta_mean']}, prefer_drift={win['gate_detail']['prefer_drift']})"
    )


def _verdict(results: list[dict[str, Any]], best: float | None) -> str:
    base = next(r for r in results if abs(r["review_blend"] - CURRENT) < 1e-12)
    if not base["gate_detail"]["cond_prize_neg"]:
        return "ROLLBACK_CANDIDATE"
    improve = [
        r for r in results if r["gate_pass"] and abs(r["review_blend"] - CURRENT) > 1e-12
    ]
    if improve and best is not None and abs(best - CURRENT) > 1e-12:
        return "APPLY_CANDIDATE"
    return "NO_IMPROVE"


def _write_md(payload: dict[str, Any]) -> None:
    rows = []
    for r in payload["results"]:
        g = r["gate_detail"]
        rows.append(
            f"| {r['review_blend']:.2f} | {r['prize_delta_mean']:+.6f} | "
            f"{r['prefer_delta_mean']:+.6f} | {g['prefer_drift']:.4f} | "
            f"{r['consistent_neg_rate']:.2f} | "
            f"{'Y' if r['gate_pass'] else 'N'} | "
            f"{g['cond_prize_neg']}/{g['cond_improve']}/{g['cond_abs']}/{g['prefer_iso']} |"
        )
    md = f"""# K-REVIEW-PRIZE-BLEND-TUNE

📅 2026-08-10 KST · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_review_prize_blend_tune.py`  
원칙: **공유=lotto_draws만** · review BLEND만 스윕 · markov BLEND 고정 {CURRENT}

## 사전확인
- BY_BRAIN markov/review={CURRENT}/{CURRENT} → {'OK' if payload['precheck']['blend_by_ok'] else 'FAIL'}
- SCORE_WEIGHTS=cand_A → {'OK' if payload['precheck']['weights_ok'] else 'FAIL'}

## 스윕
- review_blend: {payload['sweep_range']}
- seeds: {payload['seeds']}
- draws: {payload['draw_range']}
- base prize@{CURRENT}: **{payload['base_prize_delta']:+.6f}**
- base prefer@{CURRENT}: **{payload['base_prefer_delta']:+.6f}** (독립성 기준)

## 결과표

| review_blend | prizeΔ | preferΔ(모니터) | |Δprefer| | cn | gate | neg/↑/|Δ|/iso |
|-------------:|-------:|----------------:|---------:|---:|:----:|:---------------:|
{chr(10).join(rows)}

## 판정
- **best_review_blend** = `{payload['best_blend']}`
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
    print(f"== review_blend={CURRENT} (base) ==")
    base_runs = [_run_one(s, CURRENT) for s in SEEDS]
    base_agg = _aggregate(CURRENT, base_runs, base_prize=None, base_prefer=None)
    base_prize = base_agg["prize_delta_mean"]
    base_prefer = base_agg["prefer_delta_mean"]
    print(
        f"  prize={base_prize} prefer={base_prefer} "
        f"cn={base_agg['consistent_neg_rate']} gate={base_agg['gate_pass']}"
    )

    results: list[dict[str, Any]] = []
    for b in SWEEP:
        if abs(b - CURRENT) < 1e-12:
            results.append(base_agg)
            continue
        print(f"== review_blend={b} ==")
        runs = [_run_one(s, b) for s in SEEDS]
        agg = _aggregate(b, runs, base_prize=base_prize, base_prefer=base_prefer)
        print(
            f"  prize={agg['prize_delta_mean']} prefer={agg['prefer_delta_mean']} "
            f"gate={agg['gate_pass']} detail={agg['gate_detail']}"
        )
        results.append(agg)

    results.sort(key=lambda r: r["review_blend"])
    best, reason = _select_best(results)
    verdict = _verdict(results, best)

    if verdict == "APPLY_CANDIDATE":
        opinion = (
            f"best={best} — review BLEND만 교체 후보. "
            f"`BLEND_STRENGTH_BY_BRAIN['review']={best}` · markov 유지 {CURRENT}."
        )
    elif verdict == "ROLLBACK_CANDIDATE":
        opinion = f"현재 review {CURRENT} 가 prize<0 실패. HOLD/롤백 검토."
    else:
        opinion = (
            f"개선 게이트 통과 후보 없음. review BLEND={CURRENT} HOLD. "
            "다음 권장: ③ stat 패턴 단독(또는 W_CROWD_BY_BRAIN 뇌별)."
        )

    payload = {
        "id": "K-REVIEW-PRIZE-BLEND-TUNE",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "precheck": pre,
        "sweep_range": SWEEP,
        "seeds": SEEDS,
        "draw_range": [LO, HI],
        "base_prize_delta": base_prize,
        "base_prefer_delta": base_prefer,
        "abs_thr": ABS_THR,
        "prefer_iso_thr": PREFER_ISO_THR,
        "results": [
            {k: v for k, v in r.items() if k != "per_seed"}
            | {"per_seed_n": len(r.get("per_seed", []))}
            for r in results
        ],
        "results_detail": results,
        "best_blend": best,
        "best_reason": reason,
        "verdict": verdict,
        "current_review_blend": CURRENT,
        "cursor_opinion": opinion,
        "wire": False,
        "ge3_used": False,
        "independence": {
            "shared": "lotto_draws only",
            "tuned_knob": "BLEND_STRENGTH_BY_BRAIN['review']",
            "frozen_knob": "BLEND_STRENGTH_BY_BRAIN['markov']",
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
