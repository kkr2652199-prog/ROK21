# -*- coding: utf-8 -*-
"""K-W-CROWD-BY-BRAIN-TUNE — W_CROWD/W_STRUCT 뇌별 스윕.

확정 knobs 유지: markovBLEND0.55 · reviewBLEND0.85 · SCORE cand_A · statHINT52.
공유=lotto_draws만. ge3 미사용·클레임금지.
  · markov: prefer↑ + |Δprefer|≥ABS · prize_iso
  · review: prize↓(더음수) + |Δprize|≥ABS · prefer_iso
W_STRUCT = 1 - W_CROWD (합=1 강제).
wire=False 측정 → gate 통과 시만 코드 APPLY.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KW_CROWD_BY_BRAIN_TUNE.json"
OUT_MD = ROOT / "reports" / "20260811_KW_CROWD_BY_BRAIN_TUNE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
SWEEP = [0.50, 0.60, 0.70, 0.80, 0.90]
CURRENT = 0.70
WARM_BACK = 80
ABS_THR = 0.01
ISO_THR = 0.005

BLEND_LOCK = {"markov": 0.55, "review": 0.85}
CAND_A = {
    "stat": (0.25, 0.35, 0.40),
    "markov": (0.55, 0.20, 0.25),
    "review": (0.55, 0.20, 0.25),
}


def _precheck() -> dict[str, Any]:
    from app.testlotto.brains.shared import crowd_signal as cs
    import app.testlotto.signal_pool as sp

    blend = dict(cs.BLEND_STRENGTH_BY_BRAIN)
    wc = dict(cs.W_CROWD_BY_BRAIN)
    ws = dict(cs.W_STRUCT_BY_BRAIN)
    weights = {k: tuple(sp.SCORE_WEIGHTS_BY_BRAIN[k]) for k in ("stat", "markov", "review")}
    hint = dict(sp.HINT_SPEC_BY_BRAIN)
    ok = (
        abs(float(blend.get("markov", -1)) - 0.55) < 1e-12
        and abs(float(blend.get("review", -1)) - 0.85) < 1e-12
        and abs(float(wc.get("markov", -1)) - CURRENT) < 1e-12
        and abs(float(wc.get("review", -1)) - CURRENT) < 1e-12
        and weights == CAND_A
        and hint.get("stat") == (52, "miss_pattern")
    )
    return {
        "ok": ok,
        "blend": blend,
        "W_CROWD_BY_BRAIN": wc,
        "W_STRUCT_BY_BRAIN": ws,
        "weights": {k: list(v) for k, v in weights.items()},
        "hint_stat": list(hint.get("stat") or []),
    }


def _patch_w(brain: str, w_crowd: float) -> Callable[[], None]:
    from app.testlotto.brains.shared import crowd_signal as cs

    saved_c = dict(cs.W_CROWD_BY_BRAIN)
    saved_s = dict(cs.W_STRUCT_BY_BRAIN)
    saved_b = dict(cs.BLEND_STRENGTH_BY_BRAIN)
    cs.W_CROWD_BY_BRAIN = dict(saved_c)
    cs.W_STRUCT_BY_BRAIN = dict(saved_s)
    cs.BLEND_STRENGTH_BY_BRAIN = dict(BLEND_LOCK)
    cs.W_CROWD_BY_BRAIN[brain] = float(w_crowd)
    cs.W_STRUCT_BY_BRAIN[brain] = float(1.0 - w_crowd)
    # 다른 뇌는 base 유지
    other = "review" if brain == "markov" else "markov"
    cs.W_CROWD_BY_BRAIN[other] = float(saved_c.get(other, CURRENT))
    cs.W_STRUCT_BY_BRAIN[other] = float(saved_s.get(other, 1.0 - CURRENT))

    def restore() -> None:
        cs.W_CROWD_BY_BRAIN.clear()
        cs.W_CROWD_BY_BRAIN.update(saved_c)
        cs.W_STRUCT_BY_BRAIN.clear()
        cs.W_STRUCT_BY_BRAIN.update(saved_s)
        cs.BLEND_STRENGTH_BY_BRAIN.clear()
        cs.BLEND_STRENGTH_BY_BRAIN.update(saved_b)

    return restore


def _run_one(seed: int, brain: str, w_crowd: float) -> dict[str, Any]:
    import random
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy, _set_weights, _top15

    restore = _patch_w(brain, w_crowd)
    saved_w = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    _set_weights(sp, CAND_A)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer_all: list[tuple[int, float]] = []
        prize_all: list[tuple[int, float]] = []

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
            prize_all.append((dno, prize_d))
            learner.update_from_pool(pool_br, _actual(dno))

        mid = (LO + HI) // 2
        pref_lo = [v for d, v in prefer_all if d <= mid]
        pref_hi = [v for d, v in prefer_all if d > mid]
        prize_lo = [v for d, v in prize_all if d <= mid]
        prize_hi = [v for d, v in prize_all if d > mid]
        return {
            "seed": seed,
            "n": len(prefer_all),
            "prefer_mean": round(mean(v for _, v in prefer_all), 6) if prefer_all else None,
            "prize_mean": round(mean(v for _, v in prize_all), 6) if prize_all else None,
            "prefer_first_half": round(mean(pref_lo), 6) if pref_lo else None,
            "prefer_second_half": round(mean(pref_hi), 6) if pref_hi else None,
            "prize_first_half": round(mean(prize_lo), 6) if prize_lo else None,
            "prize_second_half": round(mean(prize_hi), 6) if prize_hi else None,
            "prefer_split_both_pos": bool(
                pref_lo and pref_hi and mean(pref_lo) > 0 and mean(pref_hi) > 0
            ),
            "prize_split_both_neg": bool(
                prize_lo and prize_hi and mean(prize_lo) < 0 and mean(prize_hi) < 0
            ),
        }
    finally:
        sp.SCORE_WEIGHTS_BY_BRAIN.clear()
        sp.SCORE_WEIGHTS_BY_BRAIN.update(saved_w)
        restore()


def _agg_markov(
    w: float, by_seed: list[dict[str, Any]], *, base_prefer: float | None, base_prize: float | None
) -> dict[str, Any]:
    prefer_mean = mean(d["prefer_mean"] for d in by_seed if d["prefer_mean"] is not None)
    prize_mean = mean(d["prize_mean"] for d in by_seed if d["prize_mean"] is not None)
    split = bool(
        mean(d["prefer_first_half"] for d in by_seed) > 0
        and mean(d["prefer_second_half"] for d in by_seed) > 0
    )
    is_base = abs(w - CURRENT) < 1e-12
    if is_base:
        gate = prefer_mean > 0 and split
        detail = {
            "cond_prefer_pos": prefer_mean > 0,
            "cond_split": split,
            "cond_improve": True,
            "cond_abs": True,
            "iso": True,
            "abs_d": 0.0,
            "drift": 0.0,
            "is_baseline": True,
        }
    else:
        assert base_prefer is not None and base_prize is not None
        abs_d = abs(prefer_mean - base_prefer)
        drift = abs(prize_mean - base_prize)
        detail = {
            "cond_prefer_pos": prefer_mean > 0,
            "cond_split": split,
            "cond_improve": prefer_mean > base_prefer,
            "cond_abs": abs_d >= ABS_THR,
            "iso": drift < ISO_THR,
            "abs_d": round(abs_d, 6),
            "drift": round(drift, 6),
            "is_baseline": False,
        }
        gate = all(
            [
                detail["cond_prefer_pos"],
                detail["cond_split"],
                detail["cond_improve"],
                detail["cond_abs"],
                detail["iso"],
            ]
        )
    return {
        "brain": "markov",
        "w_crowd": w,
        "w_struct": round(1.0 - w, 6),
        "prefer_delta_mean": round(prefer_mean, 6),
        "prize_delta_mean": round(prize_mean, 6),
        "gate_pass": gate,
        "gate_detail": detail,
        "per_seed": by_seed,
    }


def _agg_review(
    w: float, by_seed: list[dict[str, Any]], *, base_prefer: float | None, base_prize: float | None
) -> dict[str, Any]:
    prefer_mean = mean(d["prefer_mean"] for d in by_seed if d["prefer_mean"] is not None)
    prize_mean = mean(d["prize_mean"] for d in by_seed if d["prize_mean"] is not None)
    split = bool(
        mean(d["prize_first_half"] for d in by_seed) < 0
        and mean(d["prize_second_half"] for d in by_seed) < 0
    )
    is_base = abs(w - CURRENT) < 1e-12
    if is_base:
        gate = prize_mean < 0 and split
        detail = {
            "cond_prize_neg": prize_mean < 0,
            "cond_split": split,
            "cond_improve": True,
            "cond_abs": True,
            "iso": True,
            "abs_d": 0.0,
            "drift": 0.0,
            "is_baseline": True,
        }
    else:
        assert base_prefer is not None and base_prize is not None
        abs_d = abs(prize_mean - base_prize)
        drift = abs(prefer_mean - base_prefer)
        detail = {
            "cond_prize_neg": prize_mean < 0,
            "cond_split": split,
            "cond_improve": prize_mean < base_prize,  # 더 음수
            "cond_abs": abs_d >= ABS_THR,
            "iso": drift < ISO_THR,
            "abs_d": round(abs_d, 6),
            "drift": round(drift, 6),
            "is_baseline": False,
        }
        gate = all(
            [
                detail["cond_prize_neg"],
                detail["cond_split"],
                detail["cond_improve"],
                detail["cond_abs"],
                detail["iso"],
            ]
        )
    return {
        "brain": "review",
        "w_crowd": w,
        "w_struct": round(1.0 - w, 6),
        "prefer_delta_mean": round(prefer_mean, 6),
        "prize_delta_mean": round(prize_mean, 6),
        "gate_pass": gate,
        "gate_detail": detail,
        "per_seed": by_seed,
    }


def _select(results: list[dict[str, Any]], axis: str) -> tuple[float | None, str]:
    passers = [r for r in results if r["gate_pass"] and abs(r["w_crowd"] - CURRENT) > 1e-12]
    if not passers:
        return None, "게이트 통과 개선 후보 없음"
    if axis == "prefer":
        win = max(passers, key=lambda r: r["prefer_delta_mean"])
        return win["w_crowd"], f"prefer최대 w={win['w_crowd']} prefer={win['prefer_delta_mean']}"
    win = min(passers, key=lambda r: r["prize_delta_mean"])  # 더 음수
    return win["w_crowd"], f"prize최음수 w={win['w_crowd']} prize={win['prize_delta_mean']}"


def _apply(brain: str, w: float) -> None:
    path = ROOT / "app" / "testlotto" / "brains" / "shared" / "crowd_signal.py"
    text = path.read_text(encoding="utf-8")
    # rewrite both dicts keeping other brain
    from app.testlotto.brains.shared import crowd_signal as cs

    wc = dict(cs.W_CROWD_BY_BRAIN)
    ws = dict(cs.W_STRUCT_BY_BRAIN)
    wc[brain] = float(w)
    ws[brain] = float(1.0 - w)
    new_wc = (
        "W_CROWD_BY_BRAIN: dict[str, float] = {"
        f'"markov": {wc["markov"]:.2f}, "review": {wc["review"]:.2f}'
        "}"
    )
    new_ws = (
        "W_STRUCT_BY_BRAIN: dict[str, float] = {"
        f'"markov": {ws["markov"]:.2f}, "review": {ws["review"]:.2f}'
        "}"
    )
    import re

    text2, n1 = re.subn(
        r"W_CROWD_BY_BRAIN: dict\[str, float\] = \{[^}]+\}",
        new_wc,
        text,
        count=1,
    )
    text3, n2 = re.subn(
        r"W_STRUCT_BY_BRAIN: dict\[str, float\] = \{[^}]+\}",
        new_ws,
        text2,
        count=1,
    )
    if n1 != 1 or n2 != 1:
        raise RuntimeError(f"apply replace failed n1={n1} n2={n2}")
    # comment note
    note = f"# {brain} W_CROWD={w:.2f}: K-W-CROWD-BY-BRAIN-TUNE APPLY\n"
    if "K-W-CROWD-BY-BRAIN-TUNE" not in text3:
        text3 = text3.replace(
            "W_CROWD_BY_BRAIN: dict[str, float]",
            note + "W_CROWD_BY_BRAIN: dict[str, float]",
            1,
        )
    path.write_text(text3, encoding="utf-8")
    # live module update
    cs.W_CROWD_BY_BRAIN.clear()
    cs.W_CROWD_BY_BRAIN.update(wc)
    cs.W_STRUCT_BY_BRAIN.clear()
    cs.W_STRUCT_BY_BRAIN.update(ws)


def main() -> int:
    pre = _precheck()
    print("precheck", pre)
    if not pre["ok"]:
        print("PRECHECK_FAIL — abort (확정 knobs 불일치)")
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(
            json.dumps({"id": "K-W-CROWD-BY-BRAIN-TUNE", "verdict": "PRECHECK_FAIL", "pre": pre}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        return 1

    order = [CURRENT] + [w for w in SWEEP if abs(w - CURRENT) > 1e-12]

    markov_rows: list[dict[str, Any]] = []
    base_prefer = base_prize = None
    for w in order:
        print(f"== markov W_CROWD={w} ==")
        by = [_run_one(s, "markov", w) for s in SEEDS]
        if abs(w - CURRENT) < 1e-12:
            row = _agg_markov(w, by, base_prefer=None, base_prize=None)
            base_prefer = row["prefer_delta_mean"]
            base_prize = row["prize_delta_mean"]
            row = _agg_markov(w, by, base_prefer=base_prefer, base_prize=base_prize)
        else:
            row = _agg_markov(w, by, base_prefer=base_prefer, base_prize=base_prize)
        markov_rows.append(row)
        print("  prefer", row["prefer_delta_mean"], "prize", row["prize_delta_mean"], "gate", row["gate_pass"])

    best_m, reason_m = _select(markov_rows, "prefer")

    # review sweep: 다른 뇌 W=CURRENT 유지 (측정 중 wire 없음)
    review_rows: list[dict[str, Any]] = []
    base_prefer_r = base_prize_r = None
    for w in order:
        print(f"== review W_CROWD={w} ==")
        by = [_run_one(s, "review", w) for s in SEEDS]
        if abs(w - CURRENT) < 1e-12:
            row = _agg_review(w, by, base_prefer=None, base_prize=None)
            base_prefer_r = row["prefer_delta_mean"]
            base_prize_r = row["prize_delta_mean"]
            row = _agg_review(w, by, base_prefer=base_prefer_r, base_prize=base_prize_r)
        else:
            row = _agg_review(w, by, base_prefer=base_prefer_r, base_prize=base_prize_r)
        review_rows.append(row)
        print("  prefer", row["prefer_delta_mean"], "prize", row["prize_delta_mean"], "gate", row["gate_pass"])

    best_r, reason_r = _select(review_rows, "prize")

    applied: dict[str, Any] = {}
    if best_m is not None:
        _apply("markov", best_m)
        applied["markov"] = best_m
    if best_r is not None:
        _apply("review", best_r)
        applied["review"] = best_r

    if applied:
        verdict = "APPLY"
    elif any(r["gate_pass"] for r in markov_rows + review_rows):
        verdict = "NO_IMPROVE"  # base only
    else:
        verdict = "NO_IMPROVE"

    # if only base gates, still NO_IMPROVE
    if best_m is None and best_r is None:
        verdict = "NO_IMPROVE"

    payload = {
        "id": "K-W-CROWD-BY-BRAIN-TUNE",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "precheck": pre,
        "locked_blends": BLEND_LOCK,
        "sweep": SWEEP,
        "abs_thr": ABS_THR,
        "iso_thr": ISO_THR,
        "markov": {"results": markov_rows, "best": best_m, "reason": reason_m},
        "review": {"results": review_rows, "best": best_r, "reason": reason_r},
        "applied": applied,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "wire_during_measure": False,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = f"""# K-W-CROWD-BY-BRAIN-TUNE

📅 2026-08-11 KST · **W_CROWD/STRUCT 뇌별 스윕** · 확정 BLEND 유지

## 잠금 전제
- markovBLEND **0.55** · reviewBLEND **0.85** · SCORE cand_A · statHINT52
- 구간 1137~1236 · seed {SEEDS} · ABS≥{ABS_THR} · ISO&lt;{ISO_THR}
- ge3 미사용

## markov (prefer↑ · prize iso)
| w_crowd | prefer | prize | gate |
|---------|--------|-------|------|
""" + "\n".join(
        f"| {r['w_crowd']:.2f} | {r['prefer_delta_mean']} | {r['prize_delta_mean']} | {r['gate_pass']} |"
        for r in markov_rows
    ) + f"""

best={best_m} · {reason_m}

## review (prize↓ · prefer iso)
| w_crowd | prefer | prize | gate |
|---------|--------|-------|------|
""" + "\n".join(
        f"| {r['w_crowd']:.2f} | {r['prefer_delta_mean']} | {r['prize_delta_mean']} | {r['gate_pass']} |"
        for r in review_rows
    ) + f"""

best={best_r} · {reason_r}

## 판정
- **{verdict}** · applied={applied}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict, "applied", applied)
    print("WROTE", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
