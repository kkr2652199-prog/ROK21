# -*- coding: utf-8 -*-
"""K-BRAIN-JOINT-SMOKE — 뇌별 단독튜닝 후 합동 모니터 (성적클레임 금지).

현재 배선 고정값으로 1137~1236 × seed3 축지표만 확인.
ge3 미사용 · DB쓰기 없음 · wire=False(측정).
PASS 조건(건강):
  · prefer>0 · prefer_split_both_pos
  · prize<0 · consistent_neg (3구간)
  · knobs 실측 = 기대값 (markov BLEND0.55 · review0.85 · stat HINT52)
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KBRAIN_JOINT_SMOKE.json"
OUT_MD = ROOT / "reports" / "20260811_KBRAIN_JOINT_SMOKE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80

EXPECT = {
    "markov_blend": 0.55,
    "review_blend": 0.85,
    "stat_hint": (52, "miss_pattern"),
    "score_weights": {
        "stat": (0.25, 0.35, 0.40),
        "markov": (0.55, 0.20, 0.25),
        "review": (0.55, 0.20, 0.25),
    },
}


def _precheck() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.shared import crowd_signal as cs

    blend = dict(cs.BLEND_STRENGTH_BY_BRAIN)
    spec = sp.HINT_SPEC_BY_BRAIN.get("stat")
    weights = {k: tuple(sp.SCORE_WEIGHTS_BY_BRAIN[k]) for k in ("stat", "markov", "review")}
    ok = (
        abs(float(blend.get("markov", -1)) - EXPECT["markov_blend"]) < 1e-12
        and abs(float(blend.get("review", -1)) - EXPECT["review_blend"]) < 1e-12
        and spec == EXPECT["stat_hint"]
        and weights == EXPECT["score_weights"]
    )
    return {
        "blend_by_brain": blend,
        "stat_hint": list(spec) if spec else None,
        "weights": {k: list(v) for k, v in weights.items()},
        "ok": ok,
    }


def _run_one(seed: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import (
        _actual,
        _fw_proxy,
        _set_weights,
        _top15,
    )

    _set_weights(sp, EXPECT["score_weights"])
    learner = sp.RollingSignalLearner()
    sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)

    prefer_all: list[tuple[int, float]] = []
    prize_all: list[float] = []
    hit_all: list[float] = []
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
        scores = {
            tag: sp.number_scores(
                pool_br.get(tag, []),
                hint_by.get(tag, fallback),
                num_ema,
                pos_ema,
                brain_tag=tag,
            )
            for tag in sp.BRAIN_TAGS
        }
        prefer_d = mean(fw[n] for n in _top15(scores["markov"])) - all_mean
        prize_d = mean(fw[n] for n in _top15(scores["review"])) - all_mean
        hit = len(set(_top15(scores["stat"])) & _actual(dno)) / 6.0
        prefer_all.append((dno, prefer_d))
        prize_all.append(prize_d)
        hit_all.append(hit)
        if LO <= dno <= LO + 32:
            prize_early.append(prize_d)
        elif LO + 33 <= dno <= LO + 65:
            prize_mid.append(prize_d)
        else:
            prize_late.append(prize_d)
        learner.update_from_pool(pool_br, _actual(dno))

    mid = (LO + HI) // 2
    pref_lo = [v for d, v in prefer_all if d <= mid]
    pref_hi = [v for d, v in prefer_all if d > mid]
    return {
        "seed": seed,
        "n": len(hit_all),
        "prefer_mean": round(mean(v for _, v in prefer_all), 6),
        "prize_mean": round(mean(prize_all), 6),
        "stat_top15_hit": round(mean(hit_all), 6),
        "prefer_split_both_pos": bool(
            pref_lo and pref_hi and mean(pref_lo) > 0 and mean(pref_hi) > 0
        ),
        "consistent_neg": all(
            mean(xs) < 0 for xs in (prize_early, prize_mid, prize_late) if xs
        ),
        "prefer_first_half": round(mean(pref_lo), 6) if pref_lo else None,
        "prefer_second_half": round(mean(pref_hi), 6) if pref_hi else None,
    }


def main() -> int:
    pre = _precheck()
    print("PRECHECK", json.dumps(pre, ensure_ascii=False))
    if not pre["ok"]:
        payload = {
            "id": "K-BRAIN-JOINT-SMOKE",
            "verdict": "ABORT_PRECHECK",
            "precheck": pre,
            "wire": False,
            "ge3_used": False,
        }
        OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2

    runs = []
    for s in SEEDS:
        print(f"== seed={s} ==")
        r = _run_one(s)
        print(
            f"  prefer={r['prefer_mean']} prize={r['prize_mean']} "
            f"hit={r['stat_top15_hit']} split={r['prefer_split_both_pos']} "
            f"cn={r['consistent_neg']}"
        )
        runs.append(r)

    prefer = mean(r["prefer_mean"] for r in runs)
    prize = mean(r["prize_mean"] for r in runs)
    hit = mean(r["stat_top15_hit"] for r in runs)
    split_rate = mean(1.0 if r["prefer_split_both_pos"] else 0.0 for r in runs)
    cn_rate = mean(1.0 if r["consistent_neg"] else 0.0 for r in runs)
    pref_lo = mean(r["prefer_first_half"] for r in runs if r["prefer_first_half"] is not None)
    pref_hi = mean(r["prefer_second_half"] for r in runs if r["prefer_second_half"] is not None)

    health = {
        "prefer_pos": prefer > 0,
        "prefer_split": bool(pref_lo > 0 and pref_hi > 0),
        "prize_neg": prize < 0,
        "consistent_neg": cn_rate >= (2.0 / 3.0),
        "knobs_ok": True,
    }
    ok = all(health.values())
    verdict = "SMOKE_OK" if ok else "SMOKE_WARN"

    # 단독튜닝 시점 참고값 (성적클레임 아님 · 회귀모니터)
    refs = {
        "markov_prefer_solo_base": 0.244449,
        "review_prize_after_085": -0.074379,
        "stat_hit_after_52": 0.319444,
    }
    drift = {
        "prefer_vs_solo": round(prefer - refs["markov_prefer_solo_base"], 6),
        "prize_vs_solo": round(prize - refs["review_prize_after_085"], 6),
        "hit_vs_solo": round(hit - refs["stat_hit_after_52"], 6),
    }

    opinion = (
        "3축 건강 조건 충족. 뇌별 단독튜닝 값이 합동에서도 유지. "
        "ge3로 성적 주장 금지. 1237 양산 아님 — 형 다음 지시 대기."
        if ok
        else "건강 조건 일부 실패. 해당 축 단독 재점검 권고."
    )

    payload = {
        "id": "K-BRAIN-JOINT-SMOKE",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "precheck": pre,
        "expect_knobs": {
            "markov_blend": EXPECT["markov_blend"],
            "review_blend": EXPECT["review_blend"],
            "stat_hint": list(EXPECT["stat_hint"]),
        },
        "seeds": SEEDS,
        "draw_range": [LO, HI],
        "metrics": {
            "prefer_delta_mean": round(prefer, 6),
            "prize_delta_mean": round(prize, 6),
            "stat_top15_hit_mean": round(hit, 6),
            "prefer_split_both_pos_rate": round(split_rate, 4),
            "consistent_neg_rate": round(cn_rate, 4),
            "prefer_first_half_mean": round(pref_lo, 6),
            "prefer_second_half_mean": round(pref_hi, 6),
        },
        "health": health,
        "solo_refs": refs,
        "drift_vs_solo": drift,
        "per_seed": runs,
        "verdict": verdict,
        "cursor_opinion": opinion,
        "wire": False,
        "ge3_used": False,
        "note": "합동 smoke=모니터. 성적클레임·양산 아님.",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = f"""# K-BRAIN-JOINT-SMOKE

📅 2026-08-11 KST · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_brain_joint_smoke.py`

## 배선 사전확인
- markov BLEND={pre['blend_by_brain'].get('markov')} (기대 0.55)
- review BLEND={pre['blend_by_brain'].get('review')} (기대 0.85)
- stat HINT={pre['stat_hint']} (기대 [52, miss_pattern])
- precheck → {'OK' if pre['ok'] else 'FAIL'}

## 합동 축지표 (1137~1236 · seeds {SEEDS})
| 축 | 값 | 건강 |
|----|---:|:----:|
| markov preferΔ | **{prefer:+.6f}** | {'Y' if health['prefer_pos'] and health['prefer_split'] else 'N'} |
| review prizeΔ | **{prize:+.6f}** | {'Y' if health['prize_neg'] and health['consistent_neg'] else 'N'} |
| stat top15_hit | **{hit:.6f}** | (모니터) |
| prefer split rate | {split_rate:.2f} | |
| cn_rate | {cn_rate:.2f} | |

## 단독튜닝 대비 drift (클레임 아님)
- prefer: {drift['prefer_vs_solo']:+.6f}
- prize: {drift['prize_vs_solo']:+.6f}
- hit: {drift['hit_vs_solo']:+.6f}

## 판정
- **verdict** = **{verdict}**
- {opinion}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict)
    print("WROTE", OUT_JSON)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
