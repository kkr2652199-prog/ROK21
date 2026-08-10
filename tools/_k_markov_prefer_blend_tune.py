# -*- coding: utf-8 -*-
"""K-MARKOV-PREFER-BLEND-TUNE — markov BLEND만 스윕 (뇌 독립).

원칙: 공유=lotto_draws만. review BLEND/W_* 불변. ge3 미사용. wire=False(측정).
게이트( markov 축 ):
  · prefer_delta(cand) > prefer_delta(base)
  · prefer_delta > 0 · prefer_split_both_pos
  · |Δprefer| ≥ ABS_THR
  · 독립성: |prize_delta(cand)−prize_delta(base)| < PRIZE_ISO_THR
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260810_KMARKOV_PREFER_BLEND_TUNE.json"
OUT_MD = ROOT / "reports" / "20260810_KMARKOV_PREFER_BLEND_TUNE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236  # 100회 · 1236=마지막 가정
SEEDS = [0, 42, 123]
SWEEP = [0.40, 0.50, 0.55, 0.65, 0.75, 0.85]
CURRENT = 0.55
WARM_BACK = 80
ABS_THR = 0.01
PRIZE_ISO_THR = 0.005  # review 축 거의 불변

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
        "independence_api": {
            "prefer_table_brain_kw": True,
            "prize_table_brain_kw": True,
            "blend_weights_brain_kw": True,
        },
        "ok": ok_by and ok_w,
    }


def _patch_markov_blend(strength: float) -> Callable[[], None]:
    from app.testlotto.brains.shared import crowd_signal as cs

    saved = dict(cs.BLEND_STRENGTH_BY_BRAIN)
    cs.BLEND_STRENGTH_BY_BRAIN = dict(saved)
    cs.BLEND_STRENGTH_BY_BRAIN["markov"] = float(strength)
    # review 고정
    cs.BLEND_STRENGTH_BY_BRAIN["review"] = float(saved.get("review", CURRENT))

    def restore() -> None:
        cs.BLEND_STRENGTH_BY_BRAIN.clear()
        cs.BLEND_STRENGTH_BY_BRAIN.update(saved)

    return restore


def _run_one(seed: int, markov_blend: float) -> dict[str, Any]:
    import random
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import (
        _actual,
        _fw_proxy,
        _set_weights,
        _top15,
    )

    restore = _patch_markov_blend(markov_blend)
    saved_w = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    _set_weights(sp, CAND_A)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
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
        }
    finally:
        sp.SCORE_WEIGHTS_BY_BRAIN.clear()
        sp.SCORE_WEIGHTS_BY_BRAIN.update(saved_w)
        restore()


def _aggregate(
    blend: float,
    by_seed: list[dict[str, Any]],
    *,
    base_prefer: float | None,
    base_prize: float | None,
) -> dict[str, Any]:
    prefer_mean = mean(d["prefer_mean"] for d in by_seed if d["prefer_mean"] is not None)
    prize_mean = mean(d["prize_mean"] for d in by_seed if d["prize_mean"] is not None)
    pref_lo_m = mean(d["prefer_first_half"] for d in by_seed if d["prefer_first_half"] is not None)
    pref_hi_m = mean(d["prefer_second_half"] for d in by_seed if d["prefer_second_half"] is not None)
    split_rate = mean(1.0 if d["prefer_split_both_pos"] else 0.0 for d in by_seed)
    prefer_split_both_pos = bool(pref_lo_m > 0 and pref_hi_m > 0)

    is_base = abs(blend - CURRENT) < 1e-12
    cond_prefer_pos = prefer_mean > 0
    cond_split = prefer_split_both_pos
    if is_base:
        cond_improve = True
        cond_abs = True
        abs_d = 0.0
        prize_iso = True
        prize_drift = 0.0
    else:
        assert base_prefer is not None and base_prize is not None
        abs_d = abs(prefer_mean - base_prefer)
        prize_drift = abs(prize_mean - base_prize)
        cond_improve = prefer_mean > base_prefer
        cond_abs = abs_d >= ABS_THR
        prize_iso = prize_drift < PRIZE_ISO_THR

    gate_pass = bool(
        cond_prefer_pos and cond_split and cond_improve and cond_abs and prize_iso
    )
    return {
        "markov_blend": blend,
        "prefer_delta_mean": round(prefer_mean, 6),
        "prize_delta_mean": round(prize_mean, 6),
        "prefer_split_both_pos": prefer_split_both_pos,
        "prefer_split_both_pos_rate": round(split_rate, 4),
        "prefer_first_half_mean": round(pref_lo_m, 6),
        "prefer_second_half_mean": round(pref_hi_m, 6),
        "gate_pass": gate_pass,
        "gate_detail": {
            "cond_prefer_pos": cond_prefer_pos,
            "cond_split": cond_split,
            "cond_improve": cond_improve,
            "cond_abs": cond_abs,
            "abs_dprefer": round(abs_d, 6),
            "prize_iso": prize_iso,
            "prize_drift": round(prize_drift, 6),
            "is_baseline": is_base,
        },
        "per_seed": by_seed,
    }


def _select_best(results: list[dict[str, Any]]) -> tuple[float | None, str]:
    passers = [
        r for r in results if r["gate_pass"] and abs(r["markov_blend"] - CURRENT) > 1e-12
    ]
    if not passers:
        return None, "게이트 통과 개선 후보 없음"
    win = max(passers, key=lambda r: r["prefer_delta_mean"])
    return win["markov_blend"], (
        f"prefer 최대={win['markov_blend']} "
        f"(prefer={win['prefer_delta_mean']}, prize_drift={win['gate_detail']['prize_drift']})"
    )


def _verdict(results: list[dict[str, Any]], best: float | None) -> str:
    base = next(r for r in results if abs(r["markov_blend"] - CURRENT) < 1e-12)
    if not base["gate_detail"]["cond_prefer_pos"] or not base["gate_detail"]["cond_split"]:
        return "ROLLBACK_CANDIDATE"
    improve = [
        r for r in results if r["gate_pass"] and abs(r["markov_blend"] - CURRENT) > 1e-12
    ]
    if improve and best is not None and abs(best - CURRENT) > 1e-12:
        return "APPLY_CANDIDATE"
    return "NO_IMPROVE"


def _write_md(payload: dict[str, Any]) -> None:
    rows = []
    for r in payload["results"]:
        g = r["gate_detail"]
        rows.append(
            f"| {r['markov_blend']:.2f} | {r['prefer_delta_mean']:+.6f} | "
            f"{r['prize_delta_mean']:+.6f} | {g['prize_drift']:.4f} | "
            f"{'Y' if r['gate_pass'] else 'N'} | "
            f"{g['cond_prefer_pos']}/{g['cond_split']}/{g['cond_improve']}/"
            f"{g['cond_abs']}/{g['prize_iso']} |"
        )
    md = f"""# K-MARKOV-PREFER-BLEND-TUNE

📅 2026-08-10 KST · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_markov_prefer_blend_tune.py`  
원칙: **공유=lotto_draws만** · markov BLEND만 스윕 · review BLEND 고정 {CURRENT}

## 사전확인
- BLEND_STRENGTH_BY_BRAIN markov/review={CURRENT}/{CURRENT} → {'OK' if payload['precheck']['blend_by_ok'] else 'FAIL'}
- SCORE_WEIGHTS=cand_A → {'OK' if payload['precheck']['weights_ok'] else 'FAIL'}

## 스윕
- markov_blend: {payload['sweep_range']}
- seeds: {payload['seeds']}
- draws: {payload['draw_range']} (n≈100)
- base prefer@{CURRENT}: **{payload['base_prefer_delta']:+.6f}**
- base prize@{CURRENT}: **{payload['base_prize_delta']:+.6f}** (독립성 기준)

## 결과표

| markov_blend | preferΔ | prizeΔ(모니터) | |Δprize| | gate | pos/split/↑/|Δ|/iso |
|-------------:|--------:|---------------:|--------:|:----:|:--------------------:|
{chr(10).join(rows)}

## 판정
- **best_markov_blend** = `{payload['best_blend']}`
- **verdict** = **{payload['verdict']}**
- reason: {payload['best_reason']}

## 커서 의견
{payload['cursor_opinion']}

## 독립성
- review `BLEND_STRENGTH_BY_BRAIN['review']` 불변
- 게이트에 prize_iso(|Δprize|<{PRIZE_ISO_THR}) 포함
- 동결: random.choices / _get_draws_before / boost상한 / ge3클레임 금지
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
                    "id": "K-MARKOV-PREFER-BLEND-TUNE",
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
    print(f"== markov_blend={CURRENT} (base) ==")
    base_runs = [_run_one(s, CURRENT) for s in SEEDS]
    base_agg = _aggregate(CURRENT, base_runs, base_prefer=None, base_prize=None)
    base_prefer = base_agg["prefer_delta_mean"]
    base_prize = base_agg["prize_delta_mean"]
    print(
        f"  prefer={base_prefer} prize={base_prize} "
        f"split={base_agg['prefer_split_both_pos']} gate={base_agg['gate_pass']}"
    )

    results: list[dict[str, Any]] = []
    for b in SWEEP:
        if abs(b - CURRENT) < 1e-12:
            results.append(base_agg)
            continue
        print(f"== markov_blend={b} ==")
        runs = [_run_one(s, b) for s in SEEDS]
        agg = _aggregate(b, runs, base_prefer=base_prefer, base_prize=base_prize)
        print(
            f"  prefer={agg['prefer_delta_mean']} prize={agg['prize_delta_mean']} "
            f"gate={agg['gate_pass']} detail={agg['gate_detail']}"
        )
        results.append(agg)

    results.sort(key=lambda r: r["markov_blend"])
    best, reason = _select_best(results)
    verdict = _verdict(results, best)

    if verdict == "APPLY_CANDIDATE":
        opinion = (
            f"best={best} — markov BLEND만 교체 후보. "
            f"`BLEND_STRENGTH_BY_BRAIN['markov']={best}` · review 유지 {CURRENT}. "
            "형 GO 없이 자동 APPLY하지 않음(이번 턴은 측정+후보)."
        )
    elif verdict == "ROLLBACK_CANDIDATE":
        opinion = (
            f"현재 markov {CURRENT} 가 prefer 축 실패. HOLD/롤백 검토. review 건드리지 말 것."
        )
    else:
        opinion = (
            f"개선 게이트 통과 후보 없음. markov BLEND={CURRENT} HOLD. "
            "다음 권장: ② review prize BLEND 단독 스윕."
        )

    payload = {
        "id": "K-MARKOV-PREFER-BLEND-TUNE",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "precheck": pre,
        "sweep_range": SWEEP,
        "seeds": SEEDS,
        "draw_range": [LO, HI],
        "base_prefer_delta": base_prefer,
        "base_prize_delta": base_prize,
        "abs_thr": ABS_THR,
        "prize_iso_thr": PRIZE_ISO_THR,
        "results": [
            {k: v for k, v in r.items() if k != "per_seed"}
            | {"per_seed_n": len(r.get("per_seed", []))}
            for r in results
        ],
        "results_detail": results,
        "best_blend": best,
        "best_reason": reason,
        "verdict": verdict,
        "current_markov_blend": CURRENT,
        "cursor_opinion": opinion,
        "wire": False,
        "ge3_used": False,
        "independence": {
            "shared": "lotto_draws only",
            "tuned_knob": "BLEND_STRENGTH_BY_BRAIN['markov']",
            "frozen_knob": "BLEND_STRENGTH_BY_BRAIN['review']",
        },
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
