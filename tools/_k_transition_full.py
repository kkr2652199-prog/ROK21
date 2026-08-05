# -*- coding: utf-8 -*-
"""K-TRANSITION-FULL — 전회차 유사전이·이월 rolling 진단 (wire 없음 · SELECT-ONLY).

Usage:
  python tools/_k_transition_full.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KTRANSITION_FULL.json"
OUT_MD = ROOT / "reports" / "20260805_KTRANSITION_FULL.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

DRAW_LO, DRAW_HI = 1, 1235
ROLL_START = 101  # skip first 100 for sample size
BASELINE_HIT = 2.0  # 15 * (6/45)
MIN_SIMILAR = 10  # skip draw if similar_draws < 10
TOP_M = 15
ANCHOR = 1235
CARRY_1235_NUMS = [15, 43]  # verify from data


def load_draws() -> list[set[int]]:
    """Index 0 = draw 1. Length = DRAW_HI."""
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6
        FROM lotto_draws WHERE draw_no BETWEEN ? AND ?
        ORDER BY draw_no
        """,
        (DRAW_LO, DRAW_HI),
    ).fetchall()
    conn.close()
    out: list[set[int]] = []
    for r in rows:
        d = dict(r)
        assert int(d["draw_no"]) == DRAW_LO + len(out)
        out.append({int(d[f"num{k}"]) for k in range(1, 7)})
    return out


def presence_matrix(draws: list[set[int]]) -> np.ndarray:
    """(N, 45) bool."""
    n = len(draws)
    p = np.zeros((n, 45), dtype=bool)
    for i, s in enumerate(draws):
        for x in s:
            p[i, x - 1] = True
    return p


def rolling_sim_hits(
    draws: list[set[int]],
    *,
    min_common: int,
    roll_start: int = ROLL_START,
    min_similar: int = MIN_SIMILAR,
    top_m: int = TOP_M,
) -> dict[str, Any]:
    """For each draw N (1-indexed >= roll_start), find past draws with
    |∩| >= min_common, aggregate next-draw freqs, top_m vs actual hit.
    """
    n = len(draws)
    # presence for fast intersection counts via bit ops
    # represent each draw as uint64 bitmask (45 bits fit)
    masks = np.zeros(n, dtype=np.uint64)
    for i, s in enumerate(draws):
        m = np.uint64(0)
        for x in s:
            m |= np.uint64(1) << np.uint64(x - 1)
        masks[i] = m

    hit_dist = Counter()
    hits: list[int] = []
    n_skipped_low = 0
    # optional: track mean similar count
    similar_counts: list[int] = []

    for ni in range(roll_start - 1, n):  # 0-based index of N
        target = masks[ni]
        # past indices 0..ni-1; next of i is i+1, need i+1 < ni (next must be before N)
        # similar draw i must have i+1 existing and i+1 != N's index... next is D_{i+1}
        # i ranges 0..ni-2 so that i+1 <= ni-1 (past only)
        if ni < 2:
            n_skipped_low += 1
            continue
        past = masks[:ni]
        # popcount of AND
        commons = np.bitwise_count(past & target) if hasattr(np, "bitwise_count") else None
        if commons is None:
            # fallback: python loop for older numpy
            commons = np.array(
                [int(bin(int(past[j] & target)).count("1")) for j in range(ni)],
                dtype=np.int8,
            )
        # similar indices j where commons>=min_common and j+1 < ni (next in past)
        # j from 0..ni-2
        cand = np.flatnonzero(commons[: ni - 1] >= min_common)
        n_sim = int(cand.size)
        if n_sim < min_similar:
            n_skipped_low += 1
            continue
        similar_counts.append(n_sim)
        freq = np.zeros(45, dtype=np.int32)
        for j in cand:
            nxt = draws[j + 1]
            for x in nxt:
                freq[x - 1] += 1
        # top15 by freq, tie-break by number ascending for stability
        order = np.lexsort((np.arange(45), -freq))
        top = set(int(i + 1) for i in order[:top_m])
        hit = len(draws[ni] & top)
        hits.append(hit)
        hit_dist[hit] += 1

    mean_hit = float(np.mean(hits)) if hits else 0.0
    delta = mean_hit - BASELINE_HIT
    if delta >= 0.15:
        verdict = "STRONG"
    elif delta >= 0.05:
        verdict = "MARGINAL"
    else:
        verdict = "NOISE"

    dist = {str(k): int(hit_dist.get(k, 0)) for k in range(7)}
    return {
        "n_valid_draws": len(hits),
        "n_skipped_low_support": n_skipped_low,
        "mean_hit": round(mean_hit, 6),
        "delta": round(delta, 6),
        "hit_dist": dist,
        "mean_n_similar": round(float(np.mean(similar_counts)), 3) if similar_counts else 0.0,
        "verdict": verdict,
        "min_common": min_common,
        "min_similar": min_similar,
        "top_m": top_m,
    }


def carry_analysis(draws: list[set[int]]) -> dict[str, Any]:
    """draw 2..1235: carry between N-1 and N; transition of carry counts."""
    n = len(draws)
    carry_counts: list[int] = []
    for i in range(1, n):
        carry_counts.append(len(draws[i - 1] & draws[i]))
    full_dist = Counter(carry_counts)
    full = {str(k): int(full_dist.get(k, 0)) for k in range(7)}

    # transition: carry_t -> carry_{t+1}
    # carry_counts[i] = carry at draw (i+2) i.e. between draw i+1 and i+2? 
    # carry_counts[0] = |D1∩D2| for draw_no=2
    # carry_counts[k] corresponds to draw_no = k+2
    trans: dict[int, Counter] = defaultdict(Counter)
    for t in range(len(carry_counts) - 1):
        a = carry_counts[t]
        b = carry_counts[t + 1]
        trans[a][b] += 1

    carry_transition: dict[str, Any] = {}
    for a in range(7):
        row = trans.get(a, Counter())
        tot = sum(row.values())
        if tot == 0:
            continue
        probs = {str(b): round(row[b] / tot, 6) for b in range(7) if row[b]}
        carry_transition[str(a)] = {
            "n": tot,
            "counts": {str(b): int(row[b]) for b in range(7) if row[b]},
            "probs": probs,
        }

    # verify 1235 carry
    d1234 = draws[ANCHOR - 2]
    d1235 = draws[ANCHOR - 1]
    carry_set = sorted(d1234 & d1235)
    cur_carry = len(carry_set)

    # pred 1236 carry_count dist = P(carry_{next} | carry_1235 = cur)
    key = str(cur_carry)
    if key in carry_transition:
        pred = carry_transition[key]["probs"]
        pred_n = carry_transition[key]["n"]
    else:
        pred = {}
        pred_n = 0

    return {
        "n_draws": len(carry_counts),
        "full_dist": full,
        "mean_carry": round(float(np.mean(carry_counts)), 6),
        "carry_transition": carry_transition,
        "current_1235_carry": cur_carry,
        "carry_numbers_1235": carry_set,
        "pred_1236_carry_dist": pred,
        "pred_1236_from_n": pred_n,
        "note": "pred_1236 = empirical P(next_carry | carry_1235); 예측 클레임 아님",
    }


def brain_replace(verdict: str) -> str:
    if verdict == "STRONG":
        return "즉시착수"
    if verdict == "MARGINAL":
        return "소규모테스트"
    return "보류"


def write_md(p: dict[str, Any]) -> None:
    bk = p["by_sim_k"]
    lines = [
        "# K-TRANSITION-FULL — 전회차 유사전이·이월 rolling (2026-08-05)",
        "",
        f"- **판정:** `{p['verdict']}` · wire=`{p['wire']}`",
        f"- range `{p['draw_range']}` · baseline_hit={p['random_baseline_hit']}",
        f"- brain_replace: **{p['brain_replace_verdict']}** (target=`{p['brain_replace_target']}`)",
        "",
        "## by_sim_k",
    ]
    for k in ("sim_k2", "sim_k3", "sim_k4"):
        s = bk[k]
        lines.append(
            f"- **{k}**: n_valid={s['n_valid_draws']} · mean_hit={s['mean_hit']} · "
            f"delta={s['delta']} · **{s['verdict']}** · hit_dist={s['hit_dist']}"
        )
    ca = p["carry_analysis"]
    lines += [
        "",
        "## carry_analysis",
        f"- full_dist: `{ca['full_dist']}` · mean_carry={ca.get('mean_carry')}",
        f"- 1235 carry={ca['current_1235_carry']} nums=`{ca['carry_numbers_1235']}`",
        f"- pred_1236_carry_dist: `{ca['pred_1236_carry_dist']}` (n={ca.get('pred_1236_from_n')})",
        "",
        f"- signal_summary: {p['signal_summary']}",
        f"- tool: `{p['tool']}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(OUT_MD.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    print("[load]", flush=True)
    draws = load_draws()
    assert len(draws) == DRAW_HI - DRAW_LO + 1
    print(f"[load] N={len(draws)}", flush=True)

    by: dict[str, Any] = {}
    for name, k in (("sim_k2", 2), ("sim_k3", 3), ("sim_k4", 4)):
        print(f"[roll] {name} min_common={k}", flush=True)
        by[name] = rolling_sim_hits(draws, min_common=k)
        print(
            f"  n={by[name]['n_valid_draws']} mean={by[name]['mean_hit']} "
            f"delta={by[name]['delta']} {by[name]['verdict']}",
            flush=True,
        )

    # primary verdict = sim_k2 (instruction STEP1/2 default: 공통 2개 이상)
    primary = by["sim_k2"]
    verdict = primary["verdict"]

    print("[carry]", flush=True)
    ca = carry_analysis(draws)
    # sanity vs instruction claim
    if ca["carry_numbers_1235"] != CARRY_1235_NUMS:
        # record actual; don't force
        print(f"[warn] carry_1235 actual={ca['carry_numbers_1235']}", flush=True)

    br = brain_replace(verdict)
    if verdict == "NOISE":
        summary = (
            f"sim_k2 mean_hit={primary['mean_hit']} delta={primary['delta']} "
            f"(baseline {BASELINE_HIT}) · k3 Δ={by['sim_k3']['delta']} · "
            f"k4 Δ={by['sim_k4']['delta']} · 교체 보류"
        )
    elif verdict == "MARGINAL":
        summary = (
            f"sim_k2 Δ={primary['delta']} MARGINAL · "
            f"k3={by['sim_k3']['verdict']} k4={by['sim_k4']['verdict']}"
        )
    else:
        summary = (
            f"sim_k2 Δ={primary['delta']} STRONG · "
            f"k3 Δ={by['sim_k3']['delta']} k4 Δ={by['sim_k4']['delta']}"
        )

    payload = {
        "id": "K-TRANSITION-FULL",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "wire": False,
        "draw_range": [ROLL_START, DRAW_HI],
        "n_draws": DRAW_HI - ROLL_START + 1,
        "random_baseline_hit": BASELINE_HIT,
        "primary_metric": "sim_k2",
        "by_sim_k": by,
        "carry_analysis": ca,
        "brain_replace_verdict": br,
        "brain_replace_target": "stat",
        "brain_replace_note": (
            "현재 3뇌 markov80%/review20%/stat0% · "
            "STRONG→stat교체 즉시착수 · MARGINAL→형GO 소규모테스트 · "
            "NOISE→보류·cold-free 단독"
        ),
        "signal_summary": summary,
        "forbid": [
            "random.choices",
            "engine.py 직접 수정",
            "auto-tune",
            "wire",
            "DB INSERT/UPDATE",
            "_get_draws_before mutate",
            "신호 과장 클레임 (판정 기준 수치만 기재)",
        ],
        "pass": True,
        "tool": "tools/_k_transition_full.py",
        "prior": "docs/benchmarks/20260805_KASSOC_RULE_DIAG.json",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_md(payload)
    print(
        json.dumps(
            {
                "ok": True,
                "verdict": verdict,
                "brain": br,
                "k2": {
                    "mean": primary["mean_hit"],
                    "delta": primary["delta"],
                    "n": primary["n_valid_draws"],
                },
                "k3": {
                    "mean": by["sim_k3"]["mean_hit"],
                    "delta": by["sim_k3"]["delta"],
                    "n": by["sim_k3"]["n_valid_draws"],
                },
                "k4": {
                    "mean": by["sim_k4"]["mean_hit"],
                    "delta": by["sim_k4"]["delta"],
                    "n": by["sim_k4"]["n_valid_draws"],
                },
                "carry_1235": ca["carry_numbers_1235"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
