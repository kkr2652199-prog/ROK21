# -*- coding: utf-8 -*-
"""K-STAT-TUNE-WIRE verify — READ-ONLY walk-forward."""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
random.seed(42)

from app.testlotto.brains import predict_flow_shaman, predict_review_king, predict_stat_fairy
from app.testlotto.brains.coordinator import apply_coordinator_scoring, apply_markov_wire_quota
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN
from app.testlotto.data_service import _get_draws_before
from app.testlotto.learn_state_cutoff import set_learn_as_of
from app.testlotto.models import get_lotto_db, init_lotto_db

WIRE_PIN_GE3 = 0.1447  # KMARKOV_WIRE_V2 pin
TARGET_GE3 = 0.1447  # PASS 기준 (wire pin 이상)
NULL_GE3 = 0.1137
DRAW_START = 53
DRAW_END = 1234
N_EVAL = DRAW_END - DRAW_START + 1

init_lotto_db()
conn = get_lotto_db()
rows = conn.execute(
    "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
    (DRAW_START, DRAW_END),
).fetchall()
conn.close()

hit3, hit4, total = 0, 0, 0

for row in rows:
    row = dict(row)
    draw_no = row["draw_no"]
    actual = {row[f"num{k}"] for k in range(1, 7)}

    set_learn_as_of(int(draw_no))
    draws = _get_draws_before(draw_no)
    if not draws:
        continue

    MODULES = {"markov": predict_flow_shaman, "stat": predict_stat_fairy, "review": predict_review_king}
    QUOTA = {"markov": 3, "stat": 1, "review": 1}

    candidates = []
    for tag, mod in MODULES.items():
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            candidates.append({**s, "brain_tag": tag, "pred_set_no": i + 1})

    scored = apply_coordinator_scoring(candidates, draws, draw_no)
    selected = apply_markov_wire_quota(scored)

    best = max((len(set(s["nums"]) & actual) for s in selected), default=0)
    if best >= 3:
        hit3 += 1
    if best >= 4:
        hit4 += 1
    total += 1

ge3_rate = round(hit3 / total, 4) if total else 0
ge4_rate = round(hit4 / total, 4) if total else 0
mean_val = round(
    (ge3_rate * 3 + ge4_rate * 4) / (ge3_rate + ge4_rate) if (ge3_rate + ge4_rate) > 0 else 0,
    4,
)

# p-value (이항검정)
from scipy.stats import binomtest

res = binomtest(hit3, total, NULL_GE3, alternative="greater")
p_val = round(res.pvalue, 6)

verdict = "PASS" if ge3_rate >= TARGET_GE3 and p_val < 0.05 else "FAIL"

result = {
    "id": "K-STAT-TUNE-WIRE",
    "ts": datetime.now().isoformat(timespec="seconds"),
    "n_eval": total,
    "draw_range": [DRAW_START, DRAW_END],
    "wire_pin_ge3": WIRE_PIN_GE3,
    "null_ge3": NULL_GE3,
    "params_wired": {
        "recency_decay": 0.02,
        "gap_threshold": 20,
        "hot_window": 10,
        "top_pairs": 30,
        "pair_bonus_cap": 0.5,
    },
    "result": {
        "ge3_rate": ge3_rate,
        "ge4_rate": ge4_rate,
        "ge3_count": hit3,
        "p_value": p_val,
    },
    "delta_ge3_vs_pin": round(ge3_rate - WIRE_PIN_GE3, 4),
    "verdict": verdict,
    "pass": verdict == "PASS",
    "recommended_next": "K-REVIEW-TUNE" if verdict == "PASS" else "ROLLBACK",
}

out_json = Path("docs/benchmarks/20260729_KSTAT_WIRE_verify.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
