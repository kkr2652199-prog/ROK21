# -*- coding: utf-8 -*-
"""K-COVER-DIAG — 세트 간 중복 + cold-free 보강 진단 (wire 없음 · SELECT-ONLY).

Usage:
  python tools/_k_cover_diag.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KCOVER_DIAG.json"
OUT_MD = ROOT / "reports" / "20260805_KCOVER_DIAG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1036, 1235
H = 8
ALPHA = 2.0 / (H + 1.0)
INIT = 6.0 / 45.0
COLD_K = 5
JACCARD_EXPECTED = 0.122
UNIQUE_EXPECTED = 26.5
PERIODS = {
    "early_1036_1115": (1036, 1115),
    "mid_1116_1175": (1116, 1175),
    "late_1176_1235": (1176, 1235),
}


def jaccard(a: set[int], b: set[int]) -> float:
    u = a | b
    if not u:
        return 0.0
    return len(a & b) / len(u)


def load_draws() -> list[dict[str, Any]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6
        FROM lotto_draws WHERE draw_no BETWEEN 1 AND 1235
        ORDER BY draw_no
        """
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
        out.append({"draw_no": int(d["draw_no"]), "nums": nums, "set": set(nums)})
    return out


def ema_before(draws: list[dict]) -> dict[int, dict[int, float]]:
    ema = {n: INIT for n in range(1, 46)}
    before: dict[int, dict[int, float]] = {}
    for d in draws:
        before[d["draw_no"]] = dict(ema)
        s = d["set"]
        for n in range(1, 46):
            ind = 1.0 if n in s else 0.0
            ema[n] = ALPHA * ind + (1.0 - ALPHA) * ema[n]
    return before


def cold_k5(ema: dict[int, float]) -> set[int]:
    ordered = sorted(ema.items(), key=lambda x: (x[1], x[0]))
    return {n for n, _ in ordered[:COLD_K]}


def load_preds(lo: int, hi: int) -> dict[int, list[set[int]]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT target_draw_no, num1,num2,num3,num4,num5,num6, matched_count
        FROM lotto_predictions
        WHERE target_draw_no BETWEEN ? AND ?
        ORDER BY target_draw_no, id
        """,
        (lo, hi),
    ).fetchall()
    # also keep matched for ge3
    by_sets: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        d = dict(r)
        dno = int(d["target_draw_no"])
        nums = {int(d[f"num{k}"]) for k in range(1, 7)}
        mc = d.get("matched_count")
        by_sets.setdefault(dno, []).append({"set": nums, "matched_count": mc})
    conn.close()
    return by_sets  # type: ignore[return-value]


def load_cache_sets(lo: int, hi: int) -> dict[int, list[set[int]]]:
    """All repack sets from pool_view_cache (3 brains × 5)."""
    from app.testlotto.pool_view_cache import get_cached_pool_view

    out: dict[int, list[set[int]]] = {}
    for dno in range(lo, hi + 1):
        pv = get_cached_pool_view(dno)
        if not pv:
            out[dno] = []
            continue
        sets: list[set[int]] = []
        for tag in ("stat", "markov", "review"):
            for s in pv.get("repack_by_brain", {}).get(tag) or []:
                sets.append({int(x) for x in s["nums"]})
        out[dno] = sets
    return out


def draw_metrics(sets: list[set[int]]) -> dict[str, Any]:
    if len(sets) < 2:
        return {
            "avg_jaccard": 0.0,
            "unique": 0,
            "bias_ge2": 0.0,
            "n_sets": len(sets),
        }
    pairs = [jaccard(a, b) for a, b in combinations(sets, 2)]
    freq: Counter[int] = Counter()
    for s in sets:
        for n in s:
            freq[n] += 1
    n_nums = sum(freq.values()) or 1
    bias = sum(c for c in freq.values() if c >= 2) / n_nums
    uniq = len(freq)
    return {
        "avg_jaccard": mean(pairs),
        "unique": uniq,
        "bias_ge2": bias,
        "n_sets": len(sets),
    }


def best_ge3(sets: list[set[int]], actual: set[int], matched: list[int | None] | None = None) -> int:
    best = 0
    for i, s in enumerate(sets):
        if matched is not None and matched[i] is not None and int(matched[i]) >= 0:  # type: ignore[arg-type]
            mc = int(matched[i])  # type: ignore[arg-type]
        else:
            mc = len(s & actual)
        best = max(best, mc)
    return best


def overlap_verdict(avg_j: float) -> str:
    if avg_j > 0.20:
        return "HIGH_OVERLAP"
    if avg_j >= 0.15:
        return "MODERATE"
    return "NORMAL"


def replace_verdict(delta_ge3: float) -> str:
    if delta_ge3 >= 0.010:
        return "IMPROVE"
    if delta_ge3 >= 0.005:
        return "MARGINAL"
    return "NO_GAIN"


def write_md(p: dict[str, Any]) -> str:
    o = p["overlap_diag"]
    c = p["cold_free_replace"]
    lines = [
        "# K-COVER-DIAG — 세트 중복 + cold-free 보강 (2026-08-05)",
        "",
        f"- **판정:** `{p['verdict']}` · wire=`{p['wire']}` · n={p['n_draws']}",
        "",
        "## overlap",
        "",
        f"| 지표 | 실측 | 기대 |",
        f"|------|------|------|",
        f"| avg Jaccard | **{o['avg_jaccard']}** | {o['jaccard_expected']} |",
        f"| avg unique/draw | **{o['avg_unique_per_draw']}** | {o['unique_expected']} |",
        f"| bias_rate_ge2 | {o['bias_rate_ge2']} | — |",
        f"| verdict | **{o['verdict']}** | — |",
        "",
        f"- unique hist: `{o['unique_hist']}`",
        "",
        "## cold_free_replace",
        "",
        f"```json\n{json.dumps(c, ensure_ascii=False, indent=2)}\n```",
        "",
        "## by_period",
        "",
        "| period | Jaccard | unique | ge3 |",
        "|--------|---------|--------|-----|",
    ]
    for k, v in p["by_period"].items():
        lines.append(f"| {k} | {v['avg_jaccard']} | {v['avg_unique']} | {v['ge3']} |")
    lines += [
        "",
        "## implication",
        "",
        f"```json\n{json.dumps(p['implication'], ensure_ascii=False, indent=2)}\n```",
        "",
        f"- tool: `tools/_k_cover_diag.py`",
        f"- JSON: `docs/benchmarks/{OUT_JSON.name}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    draws = load_draws()
    before = ema_before(draws)
    by_draw = {d["draw_no"]: d for d in draws}
    preds = load_preds(LO, HI)
    cache = load_cache_sets(LO, HI)

    dnos = list(range(LO, HI + 1))
    jacs: list[float] = []
    uniqs: list[int] = []
    biases: list[float] = []
    ge3_flags: list[int] = []
    unique_hist: Counter[int] = Counter()

    # cold-free replace accumulators (only on replaced draws for after; before on all for baseline compare)
    before_j: list[float] = []
    before_u: list[int] = []
    before_g: list[int] = []
    after_j: list[float] = []
    after_u: list[int] = []
    after_g: list[int] = []
    n_replaced = 0
    n_skip_no_candidate = 0

    period_acc: dict[str, dict[str, list]] = {
        k: {"j": [], "u": [], "g": []} for k in PERIODS
    }

    for dno in dnos:
        actual = by_draw[dno]["set"]
        plist = preds.get(dno) or []
        sets = [p["set"] for p in plist]
        matched = [p.get("matched_count") for p in plist]
        m = draw_metrics(sets)
        jacs.append(m["avg_jaccard"])
        uniqs.append(m["unique"])
        biases.append(m["bias_ge2"])
        unique_hist[m["unique"]] += 1
        bg = best_ge3(sets, actual, matched)
        ge3_flags.append(1 if bg >= 3 else 0)

        for pname, (a, b) in PERIODS.items():
            if a <= dno <= b:
                period_acc[pname]["j"].append(m["avg_jaccard"])
                period_acc[pname]["u"].append(m["unique"])
                period_acc[pname]["g"].append(1 if bg >= 3 else 0)

        # --- cold-free replace ---
        cold = cold_k5(before[dno])
        dirty_idx = [i for i, s in enumerate(sets) if s & cold]
        before_j.append(m["avg_jaccard"])
        before_u.append(m["unique"])
        before_g.append(1 if bg >= 3 else 0)

        if not dirty_idx:
            # nothing to replace — after = before
            after_j.append(m["avg_jaccard"])
            after_u.append(m["unique"])
            after_g.append(1 if bg >= 3 else 0)
            continue

        # candidates: cache cold-free sets not already in issued
        issued_frozen = {frozenset(s) for s in sets}
        cands = [
            s
            for s in cache.get(dno, [])
            if not (s & cold) and frozenset(s) not in issued_frozen
        ]
        if not cands:
            n_skip_no_candidate += 1
            after_j.append(m["avg_jaccard"])
            after_u.append(m["unique"])
            after_g.append(1 if bg >= 3 else 0)
            continue

        new_sets = list(sets)
        # replace each dirty with candidate maximizing unique coverage of current selection
        used_cand: set[int] = set()
        replaced_any = False
        for di in dirty_idx:
            best_i = None
            best_score = -1
            current_union = set().union(*(new_sets[j] for j in range(len(new_sets)) if j != di))
            for ci, cset in enumerate(cands):
                if ci in used_cand:
                    continue
                score = len(current_union | cset)  # prefer more unique coverage
                # tie-break: lower jaccard to remaining
                if score > best_score:
                    best_score = score
                    best_i = ci
            if best_i is None:
                continue
            new_sets[di] = cands[best_i]
            used_cand.add(best_i)
            replaced_any = True

        if not replaced_any:
            n_skip_no_candidate += 1
            after_j.append(m["avg_jaccard"])
            after_u.append(m["unique"])
            after_g.append(1 if bg >= 3 else 0)
            continue

        n_replaced += 1
        am = draw_metrics(new_sets)
        ag = best_ge3(new_sets, actual, None)
        after_j.append(am["avg_jaccard"])
        after_u.append(am["unique"])
        after_g.append(1 if ag >= 3 else 0)

    avg_j = round(mean(jacs), 6) if jacs else 0.0
    avg_u = round(mean(uniqs), 6) if uniqs else 0.0
    ov = overlap_verdict(avg_j)
    overall_ge3 = round(mean(ge3_flags), 6) if ge3_flags else 0.0

    b_ge3 = round(mean(before_g), 6) if before_g else 0.0
    a_ge3 = round(mean(after_g), 6) if after_g else 0.0
    b_u = round(mean(before_u), 6) if before_u else 0.0
    a_u = round(mean(after_u), 6) if after_u else 0.0
    d_ge3 = round(a_ge3 - b_ge3, 6)
    d_u = round(a_u - b_u, 6)
    rv = replace_verdict(d_ge3)

    by_period = {}
    for pname, acc in period_acc.items():
        by_period[pname] = {
            "avg_jaccard": round(mean(acc["j"]), 6) if acc["j"] else 0.0,
            "avg_unique": round(mean(acc["u"]), 6) if acc["u"] else 0.0,
            "ge3": round(mean(acc["g"]), 6) if acc["g"] else 0.0,
            "n": len(acc["j"]),
        }

    cover_viable = ov == "HIGH_OVERLAP"
    cold_viable = rv == "IMPROVE"
    if cold_viable:
        nxt = "cold-free replace wire GO 후보 · 형 승인 후"
    elif cover_viable:
        nxt = "세트 다양화(커버) 설계 · 형 GO"
    else:
        nxt = "각도3(early 취약성) 진행 · covering/cold-free 우선순위 낮음"

    payload = {
        "id": "K-COVER-DIAG",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": ov if ov != "MODERATE" else "MODERATE",
        "wire": False,
        "draw_range": [LO, HI],
        "n_draws": len(dnos),
        "overlap_diag": {
            "avg_jaccard": avg_j,
            "jaccard_expected": JACCARD_EXPECTED,
            "avg_unique_per_draw": avg_u,
            "unique_expected": UNIQUE_EXPECTED,
            "unique_min": min(uniqs) if uniqs else 0,
            "unique_max": max(uniqs) if uniqs else 0,
            "unique_hist": {str(k): unique_hist[k] for k in sorted(unique_hist)},
            "bias_rate_ge2": round(mean(biases), 6) if biases else 0.0,
            "avg_best_ge3": overall_ge3,
            "verdict": ov,
        },
        "cold_free_replace": {
            "n_replaced_draws": n_replaced,
            "n_skip_no_candidate": n_skip_no_candidate,
            "cold_k": COLD_K,
            "before": {
                "avg_jaccard": round(mean(before_j), 6) if before_j else 0.0,
                "avg_unique": b_u,
                "avg_ge3": b_ge3,
            },
            "after": {
                "avg_jaccard": round(mean(after_j), 6) if after_j else 0.0,
                "avg_unique": a_u,
                "avg_ge3": a_ge3,
            },
            "delta_ge3": d_ge3,
            "delta_unique": d_u,
            "verdict": rv,
            "note": "대체 후보=pool_view_cache repack cold-free · 발권 재생성 아님",
        },
        "by_period": by_period,
        "implication": {
            "cover_wire_viable": cover_viable,
            "cold_free_add_viable": cold_viable,
            "recommended_next": nxt,
        },
        "forbid": [
            "random.choices",
            "_get_draws_before mutate",
            "engine.py",
            "auto-tune",
            "wire",
            "DB INSERT/UPDATE",
        ],
        "pass": True,
        "tool": "tools/_k_cover_diag.py",
        "prior": "docs/benchmarks/20260805_KCOLD_EXCLUDE_DIAG.json",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = write_md(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        DRIVE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"drive copy skip: {e}", file=sys.stderr)

    print(
        json.dumps(
            {
                "ok": True,
                "verdict": payload["verdict"],
                "overlap": payload["overlap_diag"],
                "replace": {
                    "n": n_replaced,
                    "d_ge3": d_ge3,
                    "d_u": d_u,
                    "v": rv,
                },
                "period": by_period,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
