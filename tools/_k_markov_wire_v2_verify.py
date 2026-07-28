# -*- coding: utf-8 -*-
"""K-MARKOV-WIRE-V2-VERIFY — set_no 쿼터 발권 vs null.

brain_review set_no 순서 + apply_markov_wire_quota (confidence 정렬 없음).
산출: docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.coordinator import (  # noqa: E402
    MARKOV_WIRE_BRAIN_QUOTA,
    MARKOV_WIRE_ENABLED,
    apply_coordinator_scoring,
    apply_markov_wire_quota,
)
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KMARKOV_WIRE_V2_verify.json"
V1 = ROOT / "docs" / "benchmarks" / "20260729_KMARKOV_WIRE_verify.json"

POOL_BRAINS = ("stat", "markov", "review")
D_LO, D_HI = 53, 1234
NULL_GE3 = 0.1137
PASS_GE3_MIN = 0.1362
ALPHA = 0.05


def load_all(con: sqlite3.Connection):
    draws: dict[int, set[int]] = {}
    for r in con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1 AND ?",
        (D_HI,),
    ):
        draws[int(r[0])] = {int(r[i]) for i in range(1, 7)}

    by_dn: dict[int, dict[str, list[dict]]] = defaultdict(
        lambda: {b: [] for b in POOL_BRAINS}
    )
    for r in con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE brain_tag IN (?,?,?) AND draw_no BETWEEN 2 AND ?",
        (*POOL_BRAINS, D_HI),
    ):
        dn, tag = int(r[0]), str(r[1])
        if tag not in POOL_BRAINS:
            continue
        try:
            raw = json.loads(r[2] or "[]")
        except json.JSONDecodeError:
            continue
        cands: list[dict] = []
        for i, s in enumerate(raw[:5]):
            nums = [int(x) for x in (s.get("nums") or [])]
            if len(nums) != 6:
                continue
            sn = int(s.get("set_no") or (i + 1))
            cands.append(
                {
                    "nums": nums,
                    "brain_tag": tag,
                    "method": s.get("method") or tag,
                    "confidence": float(s.get("confidence") or 50),
                    "reasoning": s.get("reasoning") or "",
                    "set_no": sn,
                    "pred_set_no": sn,
                }
            )
        by_dn[dn][tag] = cands
    return draws, {dn: dict(v) for dn, v in by_dn.items()}


def main() -> None:
    t0 = time.time()
    if not MARKOV_WIRE_ENABLED:
        print("WARN: MARKOV_WIRE_ENABLED=False", flush=True)

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    actuals, by_dn = load_all(con)
    con.close()

    bests: list[int] = []
    for dn in range(D_LO, D_HI + 1):
        by_brain = by_dn.get(dn) or {}
        actual = actuals.get(dn)
        if not actual:
            continue
        if not all(len(by_brain.get(b) or []) >= 5 for b in POOL_BRAINS):
            continue

        flat: list[dict] = []
        for b in POOL_BRAINS:
            flat.extend(by_brain[b])

        set_learn_as_of(int(dn))
        hist = _get_draws_before(dn)
        if not hist:
            continue
        # AUX rescoring (nums·set_no 보존) — confidence 정렬하지 않고 quota
        scored = apply_coordinator_scoring(flat, hist, dn)
        issued = apply_markov_wire_quota(scored)
        if not issued:
            continue
        best = max(len(set(c["nums"]) & actual) for c in issued)
        bests.append(best)

    n = len(bests)
    ge3_c = sum(1 for x in bests if x >= 3)
    ge4_c = sum(1 for x in bests if x >= 4)
    mean = sum(bests) / n if n else 0.0
    ge3 = ge3_c / n if n else 0.0
    ge4 = ge4_c / n if n else 0.0
    delta = ge3 - NULL_GE3
    p_val = float(binomtest(ge3_c, n, NULL_GE3, alternative="greater").pvalue) if n else 1.0
    passed = bool(ge3 >= PASS_GE3_MIN and p_val < ALPHA)

    v1 = {}
    if V1.exists():
        v1j = json.loads(V1.read_text(encoding="utf-8"))
        v1 = {
            "mean": v1j.get("mean"),
            "ge3_rate": v1j.get("ge3_rate"),
            "p_value": v1j.get("p_value"),
            "pass": v1j.get("pass"),
        }

    note = (
        "set_no_asc quota = E_markov3mix2 재현 목표. "
        "AUX confidence 정렬 없음. 예측 재생성 없음."
    )
    if not passed:
        note += " FAIL → MARKOV_WIRE_ENABLED=False 롤백."

    out = {
        "id": "K-MARKOV-WIRE-V2-VERIFY",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": n,
        "draw_range": [D_LO, D_HI],
        "quota_method": "set_no_asc",
        "wire_enabled": MARKOV_WIRE_ENABLED,
        "wire_quota": dict(MARKOV_WIRE_BRAIN_QUOTA),
        "mean": round(mean, 4),
        "ge3_rate": round(ge3, 4),
        "ge4_rate": round(ge4, 4),
        "ge3_count": ge3_c,
        "null_ge3": NULL_GE3,
        "delta_ge3": round(delta, 4),
        "p_value": round(p_val, 6),
        "pass_ge3_min": PASS_GE3_MIN,
        "pass": passed,
        "v1_compare": v1,
        "baseline_ref": {
            "E_markov3mix2_ge3": 0.1447,
            "D_markov5_ge3": 0.1362,
            "RR_ge3": 0.1337,
        },
        "note": note,
        "db_code_write": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"wrote {OUT} PASS={passed}", flush=True)


if __name__ == "__main__":
    main()
