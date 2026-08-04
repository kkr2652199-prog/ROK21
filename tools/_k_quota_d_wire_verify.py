# -*- coding: utf-8 -*-
"""K-QUOTA-D-WIRE — 고정 쿼터(stat2/markov3/review0) wire 검증.

Usage:
  python tools/_k_quota_d_wire_verify.py
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KQUOTA_D_WIRE.json"
OUT_MD = ROOT / "reports" / "20260805_KQUOTA_D_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

NULL_GE3 = 0.1137
PIN_GE3 = 0.1447
SEEDS = (42, 0, 7)
N100_LO, N100_HI = 1136, 1235
FULL_LO, FULL_HI = 1036, 1235


def _ge3_block(bests: list[int]) -> dict[str, float]:
    n = len(bests)
    if not n:
        return {"ge3": 0.0, "mean": 0.0, "n": 0}
    return {
        "ge3": round(sum(1 for b in bests if b >= 3) / n, 6),
        "mean": round(mean(bests), 6),
        "n": n,
    }


def _clear_preds(lo: int, hi: int) -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    cur = conn.execute(
        "DELETE FROM lotto_predictions WHERE target_draw_no BETWEEN ? AND ?",
        (lo, hi),
    )
    n = cur.rowcount
    conn.commit()
    conn.close()
    return int(n or 0)


def _slot_counts(lo: int, hi: int) -> dict[str, Any]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT brain_tag, COUNT(*) AS c
        FROM lotto_predictions
        WHERE target_draw_no BETWEEN ? AND ?
        GROUP BY brain_tag
        """,
        (lo, hi),
    ).fetchall()
    per_draw = conn.execute(
        """
        SELECT target_draw_no,
               SUM(CASE WHEN brain_tag='stat' THEN 1 ELSE 0 END) AS s,
               SUM(CASE WHEN brain_tag='markov' THEN 1 ELSE 0 END) AS m,
               SUM(CASE WHEN brain_tag='review' THEN 1 ELSE 0 END) AS r,
               COUNT(*) AS n
        FROM lotto_predictions
        WHERE target_draw_no BETWEEN ? AND ?
        GROUP BY target_draw_no
        """,
        (lo, hi),
    ).fetchall()
    conn.close()
    totals = {str(dict(r)["brain_tag"]): int(dict(r)["c"]) for r in rows}
    n_draws = len(per_draw) or 1
    avg = {
        "stat": round(totals.get("stat", 0) / n_draws, 4),
        "markov": round(totals.get("markov", 0) / n_draws, 4),
        "review": round(totals.get("review", 0) / n_draws, 4),
    }
    bad = [
        {
            "draw_no": int(dict(r)["target_draw_no"]),
            "stat": int(dict(r)["s"]),
            "markov": int(dict(r)["m"]),
            "review": int(dict(r)["r"]),
            "n": int(dict(r)["n"]),
        }
        for r in per_draw
        if int(dict(r)["s"]) != 2
        or int(dict(r)["m"]) != 3
        or int(dict(r)["r"]) != 0
        or int(dict(r)["n"]) != 5
    ]
    return {
        "totals": totals,
        "avg_slots_per_draw": avg,
        "n_draws_with_preds": len(per_draw),
        "n_mismatch_draws": len(bad),
        "mismatch_sample": bad[:5],
        "stat_slots_ok": avg["stat"] == 2.0 and totals.get("stat", 0) > 0,
    }


def _run_range(lo: int, hi: int, seed: int, label: str) -> dict[str, Any]:
    import app.testlotto.brains.coordinator as coord
    from app.testlotto.brains.coordinator import run_coordinated_prediction
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    coord.BRAIN_RNG_SEED_BASE = int(seed)
    coord.BENCH_FIXED_QUOTA = {"stat": 2, "markov": 3, "review": 0}
    deleted = _clear_preds(lo, hi)
    print(f"[{label}] seed={seed} clear={deleted} range={lo}~{hi}", flush=True)

    bests: list[int] = []
    t0 = time.time()
    total = hi - lo + 1
    for i, dno in enumerate(range(lo, hi + 1), 1):
        random.seed(int(seed) + int(dno))
        result = run_coordinated_prediction(dno)
        if result.get("error"):
            print(f"  WARN draw={dno} {result.get('error')}", flush=True)
            continue
        init_testlotto_db()
        conn = get_lotto_db()
        try:
            preds = conn.execute(
                "SELECT num1,num2,num3,num4,num5,num6,matched_count "
                "FROM lotto_predictions WHERE target_draw_no=?",
                (dno,),
            ).fetchall()
            actual_row = conn.execute(
                "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?",
                (dno,),
            ).fetchone()
        finally:
            conn.close()
        if not actual_row:
            continue
        actual = {int(dict(actual_row)[f"num{k}"]) for k in range(1, 7)}
        best = 0
        for p in preds:
            pd = dict(p)
            if pd.get("matched_count") is not None and int(pd["matched_count"]) >= 0:
                mc = int(pd["matched_count"])
            else:
                nums = {int(pd[f"num{k}"]) for k in range(1, 7)}
                mc = len(nums & actual)
            best = max(best, mc)
        bests.append(best)
        if i % 20 == 0 or i == total:
            print(
                f"  [{label} {i}/{total}] draw={dno} best={best} "
                f"elapsed={time.time()-t0:.0f}s",
                flush=True,
            )
    block = _ge3_block(bests)
    block["seed"] = seed
    block["elapsed_sec"] = round(time.time() - t0, 1)
    return block


def maybe_rollback(payload: dict[str, Any]) -> bool:
    """실패 시 BENCH_FIXED_QUOTA=None 복원 (git hard reset 640cb67 하지 않음)."""
    n100_avg = payload["n100_multiseed"]["avg_ge3"]
    full_ge3 = payload["full_n200"]["ge3"]
    slot_ok = payload["slot_log_ok"]
    hard_fail = (n100_avg < 0.120) or (full_ge3 < 0.120) or (not slot_ok)
    if not hard_fail:
        return False
    path = ROOT / "app" / "testlotto" / "brains" / "coordinator.py"
    text = path.read_text(encoding="utf-8")
    old = (
        'BENCH_FIXED_QUOTA: dict[str, int] | None = {"stat": 2, "markov": 3, "review": 0}'
    )
    new = "BENCH_FIXED_QUOTA: dict[str, int] | None = None"
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        payload["rolled_back"] = True
        payload["rollback_action"] = "BENCH_FIXED_QUOTA=None (quota-only · not git 640cb67)"
        print("ROLLBACK: BENCH_FIXED_QUOTA -> None", flush=True)
        return True
    payload["rolled_back"] = False
    payload["rollback_action"] = "FAILED_TO_PATCH — manual restore needed"
    return False


def write_md(p: dict[str, Any]) -> str:
    n100 = p["n100_multiseed"]
    full = p["full_n200"]
    lines = [
        "# K-QUOTA-D-WIRE — quota stat30/markov60/review10 실적용 (2026-08-05)",
        "",
        f"- **판정:** `{p['verdict']}` · wire=`{p['wire']}` · pass=`{p['pass']}`",
        f"- **변경 1곳:** `app/testlotto/brains/coordinator.py` · `BENCH_FIXED_QUOTA`",
        f"- before slots `{p['slots_before']}` → after `{p['slots_after']}`",
        "",
        "## N100 멀티시드 (1136~1235)",
        "",
        f"| seed | ge3 | mean |",
        f"|------|-----|------|",
        f"| 42 | {n100['seed42']['ge3']} | {n100['seed42']['mean']} |",
        f"| 0 | {n100['seed0']['ge3']} | {n100['seed0']['mean']} |",
        f"| 7 | {n100['seed7']['ge3']} | {n100['seed7']['mean']} |",
        f"| **avg** | **{n100['avg_ge3']}** | — |",
        f"| verdict | **{n100['verdict']}** | ≥0.135 PASS · ≥0.155 STRONG |",
        "",
        "## FULL n200 (1036~1235 · seed42)",
        "",
        f"- ge3=**{full['ge3']}** · vs_null={full['vs_null']} · vs_pin={full['vs_pin']}",
        f"- verdict=**{full['verdict']}** (PASS if ge3≥0.150)",
        "",
        "## 슬롯",
        "",
        f"- slot_log_ok=**{p['slot_log_ok']}**",
        f"- `{json.dumps(p.get('slot_detail', {}), ensure_ascii=False)}`",
        "",
        f"- rollback_target pin=`{p['rollback_target']}` · rolled_back=`{p.get('rolled_back', False)}`",
        f"- {p.get('rollback_action', '')}",
        "",
        "## 산출물",
        "",
        f"- JSON: `docs/benchmarks/{OUT_JSON.name}`",
        f"- tool: `tools/_k_quota_d_wire_verify.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    from app.testlotto.brains import coordinator as coord

    assert coord.BENCH_FIXED_QUOTA == {
        "stat": 2,
        "markov": 3,
        "review": 0,
    }, f"wire missing: {coord.BENCH_FIXED_QUOTA}"

    n100_blocks: dict[int, dict[str, Any]] = {}
    for seed in SEEDS:
        n100_blocks[seed] = _run_range(N100_LO, N100_HI, seed, f"n100_s{seed}")

    avg_ge3 = round(mean([n100_blocks[s]["ge3"] for s in SEEDS]), 6)
    if avg_ge3 >= 0.155:
        n100_verdict = "STRONG_PASS"
    elif avg_ge3 >= 0.135:
        n100_verdict = "PASS"
    else:
        n100_verdict = "FAIL"

    full = _run_range(FULL_LO, FULL_HI, 42, "full_n200")
    full_ge3 = full["ge3"]
    full_verdict = "PASS" if full_ge3 >= 0.150 else "FAIL"

    slot_detail = _slot_counts(FULL_LO, FULL_HI)
    slot_ok = bool(slot_detail["stat_slots_ok"] and slot_detail["n_mismatch_draws"] == 0)

    overall_pass = (
        n100_verdict in ("PASS", "STRONG_PASS")
        and full_verdict == "PASS"
        and slot_ok
    )
    # hard-fail rollback thresholds separate
    payload: dict[str, Any] = {
        "id": "K-QUOTA-D-WIRE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS" if overall_pass else "FAIL",
        "wire": True,
        "quota_before": {"stat": 0, "markov": 80, "review": 20},
        "quota_after": {"stat": 30, "markov": 60, "review": 10},
        "slots_before": {"stat": 0, "markov": 4, "review": 1},
        "slots_after": {"stat": 2, "markov": 3, "review": 0},
        "change": {
            "file": "app/testlotto/brains/coordinator.py",
            "symbol": "BENCH_FIXED_QUOTA",
            "value": {"stat": 2, "markov": 3, "review": 0},
            "note": "지시서 path app/testlotto/coordinator.py 는 없음 · brains/coordinator.py 가 SSOT",
        },
        "n100_multiseed": {
            "seed42": {"ge3": n100_blocks[42]["ge3"], "mean": n100_blocks[42]["mean"]},
            "seed0": {"ge3": n100_blocks[0]["ge3"], "mean": n100_blocks[0]["mean"]},
            "seed7": {"ge3": n100_blocks[7]["ge3"], "mean": n100_blocks[7]["mean"]},
            "avg_ge3": avg_ge3,
            "verdict": n100_verdict,
            "detail": {str(s): n100_blocks[s] for s in SEEDS},
        },
        "full_n200": {
            "draw_range": [FULL_LO, FULL_HI],
            "ge3": full_ge3,
            "mean": full["mean"],
            "vs_null": round(full_ge3 - NULL_GE3, 6),
            "vs_pin": round(full_ge3 - PIN_GE3, 6),
            "verdict": full_verdict,
            "elapsed_sec": full.get("elapsed_sec"),
        },
        "slot_log_ok": slot_ok,
        "slot_detail": slot_detail,
        "rollback_target": "640cb67",
        "rolled_back": False,
        "pass": overall_pass,
        "prior": "docs/benchmarks/20260805_KPATCH_1235_PREP.json",
        "tool": "tools/_k_quota_d_wire_verify.py",
    }

    maybe_rollback(payload)
    # if rolled back, wire false
    if payload.get("rolled_back"):
        payload["wire"] = False
        payload["verdict"] = "FAIL"
        payload["pass"] = False

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = write_md(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        DRIVE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"drive copy skip: {e}", file=sys.stderr)

    print(json.dumps({
        "ok": True,
        "verdict": payload["verdict"],
        "n100_avg": avg_ge3,
        "n100_verdict": n100_verdict,
        "full_ge3": full_ge3,
        "full_verdict": full_verdict,
        "slot_ok": slot_ok,
        "rolled_back": payload.get("rolled_back"),
    }, ensure_ascii=False))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
