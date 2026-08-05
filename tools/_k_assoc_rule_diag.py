# -*- coding: utf-8 -*-
"""K-ASSOC-RULE-DIAG — 당첨번호 연관규칙(1/2/3-gram→다음회) 전수 진단.

SELECT-ONLY / wire 없음. random.choices 미사용(np.random).

Usage:
  python tools/_k_assoc_rule_diag.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KASSOC_RULE_DIAG.json"
OUT_MD = ROOT / "reports" / "20260805_KASSOC_RULE_DIAG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

P0 = 6.0 / 45.0  # 0.1333...
DRAW_LO, DRAW_HI = 1, 1235
N_SIM = 1000
RNG_SEED = 42
STEP1_THR = 0.02
STEP2_THR = 0.04
STEP3_THR = 0.06
STEP2_MIN_SUP = 10
STEP3_MIN_SUP = 5


def load_draws_matrix() -> np.ndarray:
    """Return (N, 6) int array sorted rows, draw_no = index+DRAW_LO."""
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
    mat = np.zeros((len(rows), 6), dtype=np.int16)
    for i, r in enumerate(rows):
        d = dict(r)
        nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
        mat[i] = nums
        assert int(d["draw_no"]) == DRAW_LO + i
    return mat


def presence(mat: np.ndarray) -> np.ndarray:
    """(N, 45) bool — number m present in draw i (m=1..45 → col m-1)."""
    n = mat.shape[0]
    p = np.zeros((n, 45), dtype=bool)
    for i in range(n):
        p[i, mat[i] - 1] = True
    return p


def step1_deltas(pres: np.ndarray) -> np.ndarray:
    """45x45 delta matrix: delta[n-1, m-1] = P(m at k+1 | n at k) - P0.
    Diagonal included (carry).
    """
    n = pres.shape[0]
    # counts[n,m] = times n in k and m in k+1
    counts = np.zeros((45, 45), dtype=np.float64)
    support = np.zeros(45, dtype=np.float64)
    for i in range(n - 1):
        ns = np.flatnonzero(pres[i])
        ms = np.flatnonzero(pres[i + 1])
        support[ns] += 1
        for a in ns:
            counts[a, ms] += 1
    with np.errstate(divide="ignore", invalid="ignore"):
        rate = np.where(support[:, None] > 0, counts / support[:, None], np.nan)
    return rate - P0


def collect_step1(delta: np.ndarray) -> dict[str, Any]:
    # ignore nan
    flat = []
    for n in range(45):
        for m in range(45):
            d = float(delta[n, m])
            if np.isnan(d):
                continue
            flat.append((n + 1, m + 1, d))
    abs_sorted = sorted(flat, key=lambda x: abs(x[2]), reverse=True)
    pos = sorted(flat, key=lambda x: x[2], reverse=True)[:10]
    neg = sorted(flat, key=lambda x: x[2])[:10]
    cands = [t for t in flat if abs(t[2]) >= STEP1_THR]
    deltas = [t[2] for t in cands]
    max_d = max((t[2] for t in flat), default=0.0)
    min_d = min((t[2] for t in flat), default=0.0)
    return {
        "total_pairs_checked": len(flat),
        "signal_candidates": len(cands),
        "pos_candidates": sum(1 for d in deltas if d > 0),
        "neg_candidates": sum(1 for d in deltas if d < 0),
        "delta_dist": _dist(deltas),
        "max_delta": round(max_d, 6),
        "min_delta": round(min_d, 6),
        "top10_positive": [{"n": a, "m": b, "delta": round(d, 6)} for a, b, d in pos],
        "top10_negative": [{"n": a, "m": b, "delta": round(d, 6)} for a, b, d in neg],
        "top20_abs": [
            {"n": a, "m": b, "delta": round(d, 6)} for a, b, d in abs_sorted[:20]
        ],
        "_max_for_sim": max_d,
        "_cands": cands,
    }


def step2_rules(pres: np.ndarray, min_sup: int = STEP2_MIN_SUP) -> list[tuple]:
    """Return list of (n1,n2,m,delta,support) for pairs with support>=min_sup."""
    n = pres.shape[0]
    # support for each pair key
    from collections import defaultdict

    pair_sup: dict[tuple[int, int], int] = defaultdict(int)
    pair_next: dict[tuple[int, int], np.ndarray] = {}

    for i in range(n - 1):
        nums = [int(x) + 1 for x in np.flatnonzero(pres[i])]
        nxt = np.flatnonzero(pres[i + 1])
        for a, b in combinations(sorted(nums), 2):
            key = (a, b)
            pair_sup[key] += 1
            if key not in pair_next:
                pair_next[key] = np.zeros(45, dtype=np.int32)
            pair_next[key][nxt] += 1

    out = []
    for key, sup in pair_sup.items():
        if sup < min_sup:
            continue
        rates = pair_next[key] / float(sup)
        for m in range(45):
            d = float(rates[m] - P0)
            out.append((key[0], key[1], m + 1, d, sup))
    return out


def collect_step2(rules: list[tuple]) -> dict[str, Any]:
    if not rules:
        return {
            "total_pairs_checked": 0,
            "min_support": STEP2_MIN_SUP,
            "signal_candidates": 0,
            "pos_candidates": 0,
            "neg_candidates": 0,
            "delta_dist": _dist([]),
            "max_delta": 0.0,
            "min_delta": 0.0,
            "top20": [],
            "_max_for_sim": 0.0,
        }
    # total unique antecedent pairs × 45
    antecedents = {(a, b) for a, b, _, _, _ in rules}
    abs_sorted = sorted(rules, key=lambda x: abs(x[3]), reverse=True)
    cands = [r for r in rules if abs(r[3]) >= STEP2_THR]
    deltas = [r[3] for r in cands]
    max_d = max(r[3] for r in rules)
    min_d = min(r[3] for r in rules)
    top20 = [
        {
            "n1": a,
            "n2": b,
            "m": m,
            "delta": round(d, 6),
            "support": s,
        }
        for a, b, m, d, s in abs_sorted[:20]
    ]
    return {
        "total_pairs_checked": len(antecedents) * 45,
        "n_antecedents": len(antecedents),
        "min_support": STEP2_MIN_SUP,
        "signal_candidates": len(cands),
        "pos_candidates": sum(1 for d in deltas if d > 0),
        "neg_candidates": sum(1 for d in deltas if d < 0),
        "delta_dist": _dist(deltas),
        "max_delta": round(float(max_d), 6),
        "min_delta": round(float(min_d), 6),
        "top20": top20,
        "_max_for_sim": float(max_d),
    }


def step3_rules(pres: np.ndarray, min_sup: int = STEP3_MIN_SUP) -> list[tuple]:
    from collections import defaultdict

    n = pres.shape[0]
    trip_sup: dict[tuple[int, int, int], int] = defaultdict(int)
    trip_next: dict[tuple[int, int, int], np.ndarray] = {}

    for i in range(n - 1):
        nums = [int(x) + 1 for x in np.flatnonzero(pres[i])]
        nxt = np.flatnonzero(pres[i + 1])
        for trip in combinations(sorted(nums), 3):
            key = trip
            trip_sup[key] += 1
            if key not in trip_next:
                trip_next[key] = np.zeros(45, dtype=np.int32)
            trip_next[key][nxt] += 1

    out = []
    for key, sup in trip_sup.items():
        if sup < min_sup:
            continue
        rates = trip_next[key] / float(sup)
        for m in range(45):
            d = float(rates[m] - P0)
            out.append((key[0], key[1], key[2], m + 1, d, sup))
    return out


def collect_step3(rules: list[tuple]) -> dict[str, Any]:
    if not rules:
        return {
            "total_triples_checked": 0,
            "min_support": STEP3_MIN_SUP,
            "signal_candidates": 0,
            "pos_candidates": 0,
            "neg_candidates": 0,
            "delta_dist": _dist([]),
            "max_delta": 0.0,
            "min_delta": 0.0,
            "top10": [],
            "_max_for_sim": 0.0,
        }
    antecedents = {(a, b, c) for a, b, c, _, _, _ in rules}
    abs_sorted = sorted(rules, key=lambda x: abs(x[4]), reverse=True)
    cands = [r for r in rules if abs(r[4]) >= STEP3_THR]
    deltas = [r[4] for r in cands]
    max_d = max(r[4] for r in rules)
    min_d = min(r[4] for r in rules)
    top10 = [
        {
            "n1": a,
            "n2": b,
            "n3": c,
            "m": m,
            "delta": round(d, 6),
            "support": s,
        }
        for a, b, c, m, d, s in abs_sorted[:10]
    ]
    return {
        "total_triples_checked": len(antecedents) * 45,
        "n_antecedents": len(antecedents),
        "min_support": STEP3_MIN_SUP,
        "signal_candidates": len(cands),
        "pos_candidates": sum(1 for d in deltas if d > 0),
        "neg_candidates": sum(1 for d in deltas if d < 0),
        "delta_dist": _dist(deltas),
        "max_delta": round(float(max_d), 6),
        "min_delta": round(float(min_d), 6),
        "top10": top10,
        "_max_for_sim": float(max_d),
    }


def _dist(deltas: list[float]) -> dict[str, float]:
    if not deltas:
        return {"mean": 0.0, "std": 0.0, "max": 0.0, "min": 0.0, "n": 0}
    arr = np.asarray(deltas, dtype=np.float64)
    return {
        "mean": round(float(arr.mean()), 6),
        "std": round(float(arr.std(ddof=0)), 6),
        "max": round(float(arr.max()), 6),
        "min": round(float(arr.min()), 6),
        "n": int(arr.size),
    }


def random_draw_matrix(n_draws: int, rng: np.random.Generator) -> np.ndarray:
    """Independent uniform 6-subset per draw — null of no temporal association.
    Uses Generator.choice (NOT random.choices).
    """
    mat = np.zeros((n_draws, 6), dtype=np.int16)
    pool = np.arange(1, 46, dtype=np.int16)
    for i in range(n_draws):
        mat[i] = np.sort(rng.choice(pool, size=6, replace=False))
    return mat


def sim_max_deltas(n_draws: int, n_sim: int = N_SIM) -> dict[str, Any]:
    """For each step, distribution of max_delta under null."""
    rng = np.random.default_rng(RNG_SEED)
    m1 = np.empty(n_sim, dtype=np.float64)
    m2 = np.empty(n_sim, dtype=np.float64)
    m3 = np.empty(n_sim, dtype=np.float64)

    for s in range(n_sim):
        mat = random_draw_matrix(n_draws, rng)
        pres = presence(mat)
        d1 = step1_deltas(pres)
        # max over finite
        finite = d1[np.isfinite(d1)]
        m1[s] = float(finite.max()) if finite.size else 0.0

        r2 = step2_rules(pres, STEP2_MIN_SUP)
        m2[s] = max((r[3] for r in r2), default=0.0)

        r3 = step3_rules(pres, STEP3_MIN_SUP)
        m3[s] = max((r[4] for r in r3), default=0.0)

        if (s + 1) % 100 == 0:
            print(f"[sim] {s+1}/{n_sim}", flush=True)

    return {
        "step1": m1,
        "step2": m2,
        "step3": m3,
        "p95": {
            "step1": float(np.quantile(m1, 0.95)),
            "step2": float(np.quantile(m2, 0.95)),
            "step3": float(np.quantile(m3, 0.95)),
        },
    }


def step_verdict(max_delta: float, p95: float) -> str:
    return "SIGNAL" if max_delta > p95 else "NOISE"


def overall(v1: str, v2: str, v3: str) -> str:
    n_sig = sum(1 for v in (v1, v2, v3) if v == "SIGNAL")
    if n_sig >= 2:
        return "STRONG"
    if n_sig == 1:
        return "MARGINAL"
    return "NOISE"


def write_md(payload: dict[str, Any]) -> None:
    s1, s2, s3 = payload["step1_1gram"], payload["step2_2gram"], payload["step3_3gram"]
    lines = [
        "# K-ASSOC-RULE-DIAG — 연관규칙 전수 진단 (2026-08-05)",
        "",
        f"- **판정:** `{payload['verdict']}` · wire=`{payload['wire']}`",
        f"- draw_range: `{payload['draw_range']}` · P0={P0:.4f} · n_sim={N_SIM}",
        "",
        "## STEP1 1-gram",
        f"- candidates(|δ|≥{STEP1_THR}): {s1['signal_candidates']} "
        f"(+/− = {s1['pos_candidates']}/{s1['neg_candidates']})",
        f"- max_delta={s1['max_delta']} · sim_p95={s1['sim_p95_delta']} · "
        f"**{s1['verdict']}**",
        f"- top10+: `{s1['top10_positive'][:5]}` …",
        "",
        "## STEP2 2-gram",
        f"- antecedents≥{STEP2_MIN_SUP}: {s2.get('n_antecedents')} · "
        f"checked={s2['total_pairs_checked']}",
        f"- candidates(|δ|≥{STEP2_THR}): {s2['signal_candidates']}",
        f"- max_delta={s2['max_delta']} · sim_p95={s2['sim_p95_delta']} · "
        f"**{s2['verdict']}**",
        f"- top5 abs: `{s2['top20'][:5]}`",
        "",
        "## STEP3 3-gram",
        f"- antecedents≥{STEP3_MIN_SUP}: {s3.get('n_antecedents')} · "
        f"checked={s3['total_triples_checked']}",
        f"- candidates(|δ|≥{STEP3_THR}): {s3['signal_candidates']}",
        f"- max_delta={s3['max_delta']} · sim_p95={s3['sim_p95_delta']} · "
        f"**{s3['verdict']}**",
        f"- top10: `{s3['top10']}`",
        "",
        f"## 요약",
        f"- signal_summary: {payload['signal_summary']}",
        f"- next_step_implication: {payload['next_step_implication']}",
        f"- tool: `{payload['tool']}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(OUT_MD.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    print("[load] draws", flush=True)
    mat = load_draws_matrix()
    pres = presence(mat)
    print(f"[load] N={mat.shape[0]} draws {DRAW_LO}..{DRAW_HI}", flush=True)

    d1 = step1_deltas(pres)
    s1 = collect_step1(d1)
    print(f"[step1] max_delta={s1['max_delta']} cands={s1['signal_candidates']}", flush=True)

    r2 = step2_rules(pres)
    s2 = collect_step2(r2)
    print(f"[step2] max_delta={s2['max_delta']} cands={s2['signal_candidates']}", flush=True)

    r3 = step3_rules(pres)
    s3 = collect_step3(r3)
    print(f"[step3] max_delta={s3['max_delta']} cands={s3['signal_candidates']}", flush=True)

    print(f"[sim] start n={N_SIM}", flush=True)
    sim = sim_max_deltas(mat.shape[0], N_SIM)
    p95 = sim["p95"]

    v1 = step_verdict(s1["_max_for_sim"], p95["step1"])
    v2 = step_verdict(s2["_max_for_sim"], p95["step2"])
    v3 = step_verdict(s3["_max_for_sim"], p95["step3"])
    ov = overall(v1, v2, v3)

    for s, pkey, v in (
        (s1, "step1", v1),
        (s2, "step2", v2),
        (s3, "step3", v3),
    ):
        s["sim_p95_delta"] = round(p95[pkey], 6)
        s["sim_max_mean"] = round(float(sim[pkey].mean()), 6)
        s["verdict"] = v
        s.pop("_max_for_sim", None)
        s.pop("_cands", None)

    n_sig = sum(1 for v in (v1, v2, v3) if v == "SIGNAL")
    if ov == "NOISE":
        summary = (
            f"STEP1~3 모두 NOISE (SIGNAL {n_sig}/3). "
            f"maxδ 실측이 시뮬 p95 미달 — 조건부 편차는 표본변동 범위."
        )
        implication = "신호 없음 → cold-free wire 단독 진행 검토 (assoc wire 통합 보류)"
    elif ov == "MARGINAL":
        which = [f"STEP{i}" for i, v in enumerate((v1, v2, v3), 1) if v == "SIGNAL"]
        summary = f"{', '.join(which)}만 SIGNAL · 나머지 NOISE — 약한/국소 편차."
        implication = "신호 존재 → wire 통합 논의 (형 GO 후) · cold-free와 병행 검토"
    else:
        which = [f"STEP{i}" for i, v in enumerate((v1, v2, v3), 1) if v == "SIGNAL"]
        summary = f"{', '.join(which)} SIGNAL — 다단계 조건부 편차 동시 초과."
        implication = "신호 존재 → wire 통합 논의 (형 GO 후)"

    # compact matrix summary for JSON (full 45x45 as nested list rounded)
    matrix = [[round(float(d1[i, j]), 6) if np.isfinite(d1[i, j]) else None
               for j in range(45)] for i in range(45)]

    payload = {
        "id": "K-ASSOC-RULE-DIAG",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": ov,
        "wire": False,
        "draw_range": [DRAW_LO, DRAW_HI],
        "p0": round(P0, 6),
        "n_sim": N_SIM,
        "rng_seed": RNG_SEED,
        "sim_method": "independent_uniform_6subset_per_draw (np.random.Generator.choice)",
        "step1_1gram": {
            "total_pairs_checked": s1["total_pairs_checked"],
            "signal_candidates": s1["signal_candidates"],
            "pos_candidates": s1["pos_candidates"],
            "neg_candidates": s1["neg_candidates"],
            "delta_dist": s1["delta_dist"],
            "max_delta": s1["max_delta"],
            "min_delta": s1["min_delta"],
            "sim_p95_delta": s1["sim_p95_delta"],
            "sim_max_mean": s1["sim_max_mean"],
            "threshold_abs": STEP1_THR,
            "verdict": s1["verdict"],
            "top10_positive": s1["top10_positive"],
            "top10_negative": s1["top10_negative"],
            "top20_abs": s1["top20_abs"],
            "delta_matrix_45x45": matrix,
        },
        "step2_2gram": {
            "total_pairs_checked": s2["total_pairs_checked"],
            "n_antecedents": s2.get("n_antecedents", 0),
            "min_support": STEP2_MIN_SUP,
            "signal_candidates": s2["signal_candidates"],
            "pos_candidates": s2["pos_candidates"],
            "neg_candidates": s2["neg_candidates"],
            "delta_dist": s2["delta_dist"],
            "max_delta": s2["max_delta"],
            "min_delta": s2["min_delta"],
            "sim_p95_delta": s2["sim_p95_delta"],
            "sim_max_mean": s2["sim_max_mean"],
            "threshold_abs": STEP2_THR,
            "verdict": s2["verdict"],
            "top20": s2["top20"],
        },
        "step3_3gram": {
            "total_triples_checked": s3["total_triples_checked"],
            "n_antecedents": s3.get("n_antecedents", 0),
            "min_support": STEP3_MIN_SUP,
            "signal_candidates": s3["signal_candidates"],
            "pos_candidates": s3["pos_candidates"],
            "neg_candidates": s3["neg_candidates"],
            "delta_dist": s3["delta_dist"],
            "max_delta": s3["max_delta"],
            "min_delta": s3["min_delta"],
            "sim_p95_delta": s3["sim_p95_delta"],
            "sim_max_mean": s3["sim_max_mean"],
            "threshold_abs": STEP3_THR,
            "verdict": s3["verdict"],
            "top10": s3["top10"],
        },
        "overall_verdict": ov,
        "signal_summary": summary,
        "next_step_implication": implication,
        "forbid": [
            "random.choices",
            "engine.py",
            "auto-tune",
            "wire",
            "DB INSERT/UPDATE",
            "_get_draws_before mutate",
            "신호 존재 클레임 (판정 기준 충족 시에만 SIGNAL 기재)",
        ],
        "pass": True,
        "tool": "tools/_k_assoc_rule_diag.py",
        "prior": "docs/benchmarks/20260805_KNEIGHBOR_MATCH.json",
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
                "verdict": ov,
                "step1": v1,
                "step2": v2,
                "step3": v3,
                "max": [s1["max_delta"], s2["max_delta"], s3["max_delta"]],
                "p95": [s1["sim_p95_delta"], s2["sim_p95_delta"], s3["sim_p95_delta"]],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
