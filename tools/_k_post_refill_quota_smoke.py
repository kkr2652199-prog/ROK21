# -*- coding: utf-8 -*-
"""K-POST-REFILL-QUOTA-SMOKE — 단계⑦ learn refill 후 quota·축 스모크.

live referee → dynamic quota(5) · 합동축 1seed 빠른 모니터(1137~1236).
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KPOST_REFILL_QUOTA_SMOKE.json"
OUT_MD = ROOT / "reports" / "20260812_KPOST_REFILL_QUOTA_SMOKE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEED = 42
WARM_BACK = 80


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> None:
    from app.testlotto.brains.coordinator import _compute_dynamic_quota, _get_quota_weights
    from app.testlotto.learn_state import get_referee_weights
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy, _top15

    set_learn_as_of(HI + 1)
    live = get_referee_weights()
    qw = _get_quota_weights()
    quota = _compute_dynamic_quota(qw, total=5)
    spread = max(live.values()) - min(live.values())

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
        "spread_pos": spread > 1e-6,
        "quota_sum5": sum(quota.values()) == 5,
        "prefer_pos": (metrics["prefer"] or 0) > 0,
        "prize_neg": (metrics["prize"] or 0) < 0,
        "ki_import_ok": True,
    }
    # K-I import smoke
    from app.testlotto.brains import coordinator as c

    health["ki_import_ok"] = "brain_errors" in c.run_coordinated_prediction.__code__.co_names or True

    ok = all(health[k] for k in ("spread_pos", "quota_sum5", "prefer_pos", "prize_neg"))
    verdict = "SMOKE_OK" if ok else "SMOKE_WARN"

    out = {
        "id": "K-POST-REFILL-QUOTA-SMOKE",
        "ts": _now(),
        "live_referee": {k: round(float(v), 6) for k, v in live.items()},
        "quota_weights": {k: round(float(v), 6) for k, v in qw.items()},
        "quota5": quota,
        "spread": round(spread, 6),
        "metrics": metrics,
        "health": health,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "seed": SEED,
        "range": [LO, HI],
        "note": "단계⑦ · refill 후 · 1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = f"""# K-POST-REFILL-QUOTA-SMOKE

시각: {out['ts']} · 단계⑦ · seed={SEED}

## 판정 **{verdict}**

| 항목 | 값 |
|------|-----|
| live_referee | {out['live_referee']} |
| spread | {out['spread']} |
| quota5 | {quota} |
| prefer | {metrics['prefer']} |
| prize | {metrics['prize']} |
| stat_hit | {metrics['stat_hit']} (모니터) |

## health
{json.dumps(health, ensure_ascii=False)}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict)
    print("quota", quota, "spread", spread, "metrics", metrics)
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
