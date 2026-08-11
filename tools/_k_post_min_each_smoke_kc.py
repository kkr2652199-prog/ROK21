# -*- coding: utf-8 -*-
"""K-POST-MIN-EACH-SMOKE + K-C factcheck — 단계⑨⑩.

⑨ min_each=1 후 quota m3/r1/s1 · 축 prefer+/prize− (seed42·1137~1236)
⑩ K-C: 구「최저성적=최고가중」이 live에서 성립하는지 재실측
ge3미클레임 · DB쓰기 없음.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KPOST_MIN_EACH_SMOKE_KC.json"
OUT_MD = ROOT / "reports" / "20260812_KPOST_MIN_EACH_SMOKE_KC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEED = 42
WARM_BACK = 80


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> None:
    from app.testlotto.brains.coordinator import (
        QUOTA_ADAPTIVE_MIN_EACH,
        _compute_dynamic_quota,
        _get_quota_weights,
    )
    from app.testlotto.learn_state import PREDICT_BRAIN_TAGS, get_all_learn_states, get_referee_weights
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy, _top15

    set_learn_as_of(HI + 1)
    live = get_referee_weights()
    states = get_all_learn_states()
    avgs = {
        t: float(states[t].get("recent_avg_match", 0.0) or 0.0) for t in PREDICT_BRAIN_TAGS
    }
    qw = _get_quota_weights()
    quota = _compute_dynamic_quota(qw, total=5)

    # K-C: 최저 avg 뇌 == 최고 weight?
    avg_lo = min(avgs, key=avgs.get)
    w_hi = max(live, key=live.get)
    kc_reverse = avg_lo == w_hi
    kc = {
        "avgs": {k: round(v, 6) for k, v in avgs.items()},
        "live_referee": {k: round(float(v), 6) for k, v in live.items()},
        "lowest_avg_brain": avg_lo,
        "highest_weight_brain": w_hi,
        "reverse_ranking": kc_reverse,
        "verdict": "STALE_CLOSE" if not kc_reverse else "STILL_OPEN",
        "note": "구 K-C는 legacy 1+avg*0.15·균등 시기. K-M/J/refill 후 재실측.",
    }

    learner = sp.RollingSignalLearner()
    sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=SEED)
    prefer: list[float] = []
    prize: list[float] = []
    hits: list[float] = []
    for dno in range(LO, HI + 1):
        sp.set_learn_as_of(dno)
        draws = sp._get_draws_before(dno)
        if len(draws) < 50:
            continue
        fw = _fw_proxy(draws)
        all_mean = mean(fw[n] for n in range(1, 46))
        if all_mean <= 1e-12:
            continue
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED)
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
        prefer.append(mean(fw[n] for n in _top15(scores["markov"])) - all_mean)
        prize.append(mean(fw[n] for n in _top15(scores["review"])) - all_mean)
        hits.append(len(set(_top15(scores["stat"])) & _actual(dno)) / 6.0)
        learner.update_from_pool(pool_br, _actual(dno))

    metrics = {
        "prefer": round(mean(prefer), 6) if prefer else None,
        "prize": round(mean(prize), 6) if prize else None,
        "stat_hit": round(mean(hits), 6) if hits else None,
        "n": len(prefer),
    }
    health = {
        "min_each": int(QUOTA_ADAPTIVE_MIN_EACH) == 1,
        "quota_all_ge1": all(v >= 1 for v in quota.values()),
        "quota_sum5": sum(quota.values()) == 5,
        "prefer_pos": (metrics["prefer"] or 0) > 0,
        "prize_neg": (metrics["prize"] or 0) < 0,
    }
    smoke_ok = all(health.values())
    smoke_verdict = "SMOKE_OK" if smoke_ok else "SMOKE_WARN"

    out = {
        "id": "K-POST-MIN-EACH-SMOKE-KC",
        "ts": _now(),
        "step": "9+10",
        "quota": quota,
        "min_each": int(QUOTA_ADAPTIVE_MIN_EACH),
        "metrics": metrics,
        "health": health,
        "smoke_verdict": smoke_verdict,
        "kc": kc,
        "ge3_used_as_claim": False,
        "note": "1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = f"""# K-POST-MIN-EACH-SMOKE + K-C

시각: {out['ts']} · 단계⑨⑩ · seed={SEED}

## ⑨ 판정 **{smoke_verdict}**
- min_each={QUOTA_ADAPTIVE_MIN_EACH} · quota=`{quota}`
- prefer={metrics['prefer']} · prize={metrics['prize']} · hit={metrics['stat_hit']}(모니터)

## ⑩ K-C 판정 **{kc['verdict']}**
- avgs=`{kc['avgs']}`
- live=`{kc['live_referee']}`
- 최저avg=`{kc['lowest_avg_brain']}` · 최고가중=`{kc['highest_weight_brain']}`
- reverse_ranking={kc['reverse_ranking']} → {kc['note']}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("SMOKE", smoke_verdict, "quota", quota, "metrics", metrics)
    print("K-C", kc["verdict"], "reverse", kc_reverse)
    print("WROTE", OUT_JSON)
    raise SystemExit(0 if smoke_ok and not kc_reverse else 1)


if __name__ == "__main__":
    main()
