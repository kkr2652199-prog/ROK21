# -*- coding: utf-8 -*-
"""K-COLD-EXCLUDE-DIAG — EMA H=8 cold 번호 제외 사후필터 진단 (wire 없음).

lotto_predictions SELECT-ONLY · 재발권 없음.
Usage:
  python tools/_k_cold_exclude_diag.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KCOLD_EXCLUDE_DIAG.json"
OUT_MD = ROOT / "reports" / "20260805_KCOLD_EXCLUDE_DIAG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1036, 1235
H = 8
ALPHA = 2.0 / (H + 1.0)
INIT = 6.0 / 45.0
KS = (3, 5, 7)
PERIODS = {
    "early_1036_1115": (1036, 1115),
    "mid_1116_1175": (1116, 1175),
    "late_1176_1235": (1176, 1235),
}


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


def ema_states_before(draws: list[dict]) -> dict[int, dict[int, float]]:
    """draw_no -> EMA state immediately BEFORE that draw."""
    ema = {n: INIT for n in range(1, 46)}
    before: dict[int, dict[int, float]] = {}
    for d in draws:
        before[d["draw_no"]] = dict(ema)
        s = d["set"]
        for n in range(1, 46):
            ind = 1.0 if n in s else 0.0
            ema[n] = ALPHA * ind + (1.0 - ALPHA) * ema[n]
    return before


def cold_bottom(ema: dict[int, float], k: int) -> list[int]:
    ordered = sorted(ema.items(), key=lambda x: (x[1], x[0]))  # low ema first
    return [n for n, _ in ordered[:k]]


def load_preds(lo: int, hi: int) -> dict[int, list[dict[str, Any]]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT target_draw_no, brain_tag, num1,num2,num3,num4,num5,num6, matched_count
        FROM lotto_predictions
        WHERE target_draw_no BETWEEN ? AND ?
        ORDER BY target_draw_no, id
        """,
        (lo, hi),
    ).fetchall()
    conn.close()
    by: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        d = dict(r)
        dno = int(d["target_draw_no"])
        nums = [int(d[f"num{k}"]) for k in range(1, 7)]
        by.setdefault(dno, []).append(
            {
                "nums": nums,
                "set": set(nums),
                "brain_tag": str(d.get("brain_tag") or ""),
                "matched_count": d.get("matched_count"),
            }
        )
    return by


def hits(pred: dict, actual: set[int]) -> int:
    if pred.get("matched_count") is not None and int(pred["matched_count"]) >= 0:
        return int(pred["matched_count"])
    return len(pred["set"] & actual)


def ge3_rate(flags: list[int]) -> float:
    if not flags:
        return 0.0
    return round(sum(flags) / len(flags), 6)


def pack_verdict(delta: float, low_sample: bool) -> str:
    if low_sample:
        return "LOW_SAMPLE"
    if delta >= 0.010:
        return "VIABLE"
    if delta >= 0.005:
        return "MARGINAL"
    return "NOT_VIABLE"


def measure_for_k(
    k: int,
    draws_by: dict[int, dict],
    before: dict[int, dict[int, float]],
    preds: dict[int, list[dict]],
    dnos: list[int],
) -> dict[str, Any]:
    all_ge3: list[int] = []
    clean_ge3: list[int] = []
    dirty_ge3: list[int] = []
    contaminated = 0
    total = 0
    # draw-level best_of among clean (meta)
    draw_all_best: list[int] = []
    draw_clean_best: list[int] = []
    draws_with_clean = 0

    for dno in dnos:
        actual = draws_by[dno]["set"]
        cold = set(cold_bottom(before[dno], k))
        plist = preds.get(dno) or []
        best_all = 0
        best_clean = -1
        for p in plist:
            mc = hits(p, actual)
            ge3 = 1 if mc >= 3 else 0
            all_ge3.append(ge3)
            total += 1
            dirty = bool(p["set"] & cold)
            if dirty:
                contaminated += 1
                dirty_ge3.append(ge3)
            else:
                clean_ge3.append(ge3)
                best_clean = max(best_clean, mc)
            best_all = max(best_all, mc)
        draw_all_best.append(best_all)
        if best_clean >= 0:
            draws_with_clean += 1
            draw_clean_best.append(best_clean)

    clean_n = len(clean_ge3)
    low = clean_n < 100
    c_ge3 = ge3_rate(clean_ge3)
    a_ge3 = ge3_rate(all_ge3)
    d_ge3 = ge3_rate(dirty_ge3)
    delta = round(c_ge3 - a_ge3, 6)
    return {
        "contamination_rate": round(contaminated / total, 6) if total else 0.0,
        "clean_n_sets": clean_n,
        "dirty_n_sets": len(dirty_ge3),
        "total_n_sets": total,
        "clean_ge3": c_ge3,
        "dirty_ge3": d_ge3,
        "all_ge3": a_ge3,
        "delta": delta,
        "low_sample": low,
        "verdict": pack_verdict(delta, low),
        "draw_level_meta": {
            "all_best_ge3": ge3_rate([1 if b >= 3 else 0 for b in draw_all_best]),
            "clean_best_ge3": ge3_rate([1 if b >= 3 else 0 for b in draw_clean_best])
            if draw_clean_best
            else 0.0,
            "n_draws_with_clean": draws_with_clean,
            "n_draws": len(dnos),
            "note": "draw-level best_of among remaining clean sets (참고)",
        },
    }


def write_md(p: dict[str, Any]) -> str:
    lines = [
        "# K-COLD-EXCLUDE-DIAG — cold 번호 제외 진단 (2026-08-05)",
        "",
        f"- **판정:** `{p['verdict']}` · wire=`{p['wire']}` · n={p['n_draws']}",
        f"- EMA H={p['ema_h']} · α={ALPHA:.4f} · 사후필터(lotto_predictions SELECT-ONLY)",
        "",
        "## cold_sets",
        "",
        "| k | contam | clean_n | clean_ge3 | all_ge3 | Δ | verdict |",
        "|---|--------|---------|-----------|---------|---|---------|",
    ]
    for key in ("cold_k3", "cold_k5", "cold_k7"):
        c = p["cold_sets"][key]
        lines.append(
            f"| {key} | {c['contamination_rate']} | {c['clean_n_sets']} | "
            f"{c['clean_ge3']} | {c['all_ge3']} | {c['delta']:+.4f} | **{c['verdict']}** |"
        )
    lines += ["", "## by_period", ""]
    for per, block in p["by_period"].items():
        lines.append(f"### {per}")
        lines.append("| k | clean_ge3 | all_ge3 | Δ |")
        lines.append("|---|-----------|---------|---|")
        for key, row in block.items():
            lines.append(
                f"| {key} | {row['clean_ge3']} | {row['all_ge3']} | {row['delta']:+.4f} |"
            )
        lines.append("")
    lines += [
        "## best",
        "",
        f"```json\n{json.dumps(p['best'], ensure_ascii=False, indent=2)}\n```",
        "",
        f"- tool: `tools/_k_cold_exclude_diag.py`",
        f"- JSON: `docs/benchmarks/{OUT_JSON.name}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    draws = load_draws()
    before = ema_states_before(draws)
    draws_by = {d["draw_no"]: d for d in draws}
    preds = load_preds(LO, HI)
    dnos = list(range(LO, HI + 1))

    cold_sets: dict[str, Any] = {}
    for k in KS:
        cold_sets[f"cold_k{k}"] = measure_for_k(k, draws_by, before, preds, dnos)

    by_period: dict[str, Any] = {}
    for pname, (a, b) in PERIODS.items():
        pdnos = [d for d in dnos if a <= d <= b]
        by_period[pname] = {}
        for k in KS:
            m = measure_for_k(k, draws_by, before, preds, pdnos)
            by_period[pname][f"cold_k{k}"] = {
                "clean_ge3": m["clean_ge3"],
                "all_ge3": m["all_ge3"],
                "delta": m["delta"],
                "clean_n_sets": m["clean_n_sets"],
                "low_sample": m["low_sample"],
                "verdict": m["verdict"],
            }

    # best among k with not low_sample preferred
    ranked = sorted(
        ((k, cold_sets[f"cold_k{k}"]) for k in KS),
        key=lambda x: (not x[1]["low_sample"], x[1]["delta"]),
        reverse=True,
    )
    best_k, best_m = ranked[0]
    viable = (not best_m["low_sample"]) and best_m["delta"] >= 0.010
    overall = "VIABLE" if viable else (
        "MARGINAL"
        if (not best_m["low_sample"] and best_m["delta"] >= 0.005)
        else "NOT_VIABLE"
    )

    # snapshot cold at 1235 for report
    snap1235 = {f"k{k}": cold_bottom(before[1235], k) for k in KS}

    payload = {
        "id": "K-COLD-EXCLUDE-DIAG",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": overall,
        "wire": False,
        "draw_range": [LO, HI],
        "n_draws": HI - LO + 1,
        "ema_h": H,
        "alpha": round(ALPHA, 6),
        "cold_at_1235_before": snap1235,
        "cold_sets": cold_sets,
        "by_period": by_period,
        "best": {
            "cold_k": best_k,
            "delta": best_m["delta"],
            "viable": viable,
            "verdict": best_m["verdict"],
            "clean_ge3": best_m["clean_ge3"],
            "all_ge3": best_m["all_ge3"],
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
        "tool": "tools/_k_cold_exclude_diag.py",
        "prior": "docs/benchmarks/20260805_KEMA_MARKOV_DIAG.json",
        "note": "사후필터 시뮬 · 발권 ge3 향상 클레임 금지 · wire 후 재측정 필요",
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
                "verdict": overall,
                "best": payload["best"],
                "k3": {x: cold_sets["cold_k3"][x] for x in ("delta", "clean_ge3", "all_ge3", "clean_n_sets", "verdict")},
                "k5": {x: cold_sets["cold_k5"][x] for x in ("delta", "clean_ge3", "all_ge3", "clean_n_sets", "verdict")},
                "k7": {x: cold_sets["cold_k7"][x] for x in ("delta", "clean_ge3", "all_ge3", "clean_n_sets", "verdict")},
                "early_k5": by_period["early_1036_1115"]["cold_k5"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
