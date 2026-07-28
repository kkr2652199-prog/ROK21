# -*- coding: utf-8 -*-
"""K-PATTERN-2 — 패턴AUX 분위수 × matched (전행 · READ-ONLY).

목표: 보조 '패턴돋보기' 유지/축소 근거 + 공격적 연구 축 후보 수치.
산출: docs/benchmarks/20260729_KPATTERN2_aux_quartile.json
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KPATTERN2_aux_quartile.json"

PIPE_SCORE_RE = re.compile(r"\[보조4뇌:([0-9.]+)\]")
AUX_SCORE_RE = re.compile(
    r"(오답탐정|패턴돋보기|균형지킴이)[^\|]*?점수?\s*([0-9.]+)"
)
AUX_SIMPLE_RE = re.compile(r"(오답탐정):([0-9.]+)")


def parse_aux(reasoning: str) -> dict[str, float]:
    text = reasoning or ""
    out: dict[str, float] = {}
    m = PIPE_SCORE_RE.search(text)
    if m:
        try:
            out["aux4_agg"] = float(m.group(1))
        except ValueError:
            pass
    for m in AUX_SIMPLE_RE.finditer(text):
        try:
            out[m.group(1)] = float(m.group(2))
        except ValueError:
            pass
    for m in AUX_SCORE_RE.finditer(text):
        try:
            out[m.group(1)] = float(m.group(2))
        except ValueError:
            pass
    return out


def quartile_edges(vals: list[float]) -> list[float]:
    """Return [q0,q25,q50,q75,q100] via nearest-rank."""
    if not vals:
        return [0, 0, 0, 0, 0]
    s = sorted(vals)
    n = len(s)

    def q(p: float) -> float:
        if n == 1:
            return s[0]
        idx = min(n - 1, max(0, int(round(p * (n - 1)))))
        return s[idx]

    return [s[0], q(0.25), q(0.5), q(0.75), s[-1]]


def assign_q(v: float, edges: list[float]) -> int:
    """1..4 quartile bucket (inclusive high)."""
    _, q1, q2, q3, _ = edges
    if v <= q1:
        return 1
    if v <= q2:
        return 2
    if v <= q3:
        return 3
    return 4


def bucket_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return {"n": 0}
    ms = [int(x["matched"]) for x in items]
    n = len(ms)
    return {
        "n": n,
        "matched_mean": round(sum(ms) / n, 4),
        "ge3": sum(1 for m in ms if m >= 3),
        "ge3_rate": round(sum(1 for m in ms if m >= 3) / n, 4),
        "ge4": sum(1 for m in ms if m >= 4),
        "ge4_rate": round(sum(1 for m in ms if m >= 4) / n, 4),
        "ge5": sum(1 for m in ms if m >= 5),
        "ge6": sum(1 for m in ms if m >= 6),
    }


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT draw_no, brain_tag, matched_count, bonus_matched,
               predicted_sets_json, best_set_no
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN 2 AND 1234
        ORDER BY draw_no, brain_tag
        """
    ).fetchall()

    # Unit A: best-set rows (3698)
    best_rows: list[dict[str, Any]] = []
    # Unit B: all 5 sets (expand)
    all_sets: list[dict[str, Any]] = []

    for r in rows:
        try:
            sets = json.loads(r["predicted_sets_json"] or "[]")
        except Exception:
            sets = []
        bsn = int(r["best_set_no"] or 1)
        best = next(
            (s for s in sets if int(s.get("set_no") or 0) == bsn),
            sets[bsn - 1] if sets else {},
        )
        aux_b = parse_aux(best.get("reasoning") or "")
        if "패턴돋보기" in aux_b:
            best_rows.append(
                {
                    "draw": int(r["draw_no"]),
                    "brain": r["brain_tag"],
                    "matched": int(r["matched_count"]),
                    "pattern": aux_b["패턴돋보기"],
                    "balance": aux_b.get("균형지킴이"),
                    "miss": aux_b.get("오답탐정"),
                    "aux4": aux_b.get("aux4_agg"),
                }
            )
        for s in sets:
            aux = parse_aux(s.get("reasoning") or "")
            if "패턴돋보기" not in aux:
                continue
            mc = s.get("matched_count")
            if mc is None:
                continue
            all_sets.append(
                {
                    "draw": int(r["draw_no"]),
                    "brain": r["brain_tag"],
                    "set_no": int(s.get("set_no") or 0),
                    "matched": int(mc),
                    "pattern": aux["패턴돋보기"],
                    "balance": aux.get("균형지킴이"),
                    "miss": aux.get("오답탐정"),
                    "aux4": aux.get("aux4_agg"),
                }
            )

    def analyze(unit: str, items: list[dict[str, Any]], score_key: str) -> dict[str, Any]:
        vals = [float(x[score_key]) for x in items if x.get(score_key) is not None]
        edges = quartile_edges(vals)
        buckets: dict[int, list] = defaultdict(list)
        for x in items:
            if x.get(score_key) is None:
                continue
            q = assign_q(float(x[score_key]), edges)
            buckets[q].append(x)
        by_q = {f"Q{q}": bucket_stats(buckets[q]) for q in (1, 2, 3, 4)}
        # monotone check Q4 vs Q1
        q1m = by_q["Q1"].get("matched_mean") or 0
        q4m = by_q["Q4"].get("matched_mean") or 0
        q1g3 = by_q["Q1"].get("ge3_rate") or 0
        q4g3 = by_q["Q4"].get("ge3_rate") or 0
        q1g4 = by_q["Q1"].get("ge4_rate") or 0
        q4g4 = by_q["Q4"].get("ge4_rate") or 0
        return {
            "unit": unit,
            "score": score_key,
            "n": len(items),
            "score_edges_q0_q25_q50_q75_q100": edges,
            "by_quartile": by_q,
            "lift": {
                "matched_mean_Q4_minus_Q1": round(q4m - q1m, 4),
                "ge3_rate_Q4_minus_Q1": round(q4g3 - q1g3, 4),
                "ge4_rate_Q4_minus_Q1": round(q4g4 - q1g4, 4),
            },
        }

    analyses = {
        "best_pattern": analyze("best_set", best_rows, "pattern"),
        "best_balance": analyze(
            "best_set",
            [x for x in best_rows if x.get("balance") is not None],
            "balance",
        ),
        "best_aux4": analyze(
            "best_set",
            [x for x in best_rows if x.get("aux4") is not None],
            "aux4",
        ),
        "allsets_pattern": analyze("all_5_sets", all_sets, "pattern"),
        "allsets_balance": analyze(
            "all_5_sets",
            [x for x in all_sets if x.get("balance") is not None],
            "balance",
        ),
    }

    # brain-stratified pattern on best
    by_brain = {}
    for tag in ("stat", "markov", "review"):
        sub = [x for x in best_rows if x["brain"] == tag]
        by_brain[tag] = analyze(f"best_{tag}", sub, "pattern")

    # top decile vs bottom (more aggressive cut)
    def decile_compare(items: list[dict[str, Any]], key: str) -> dict[str, Any]:
        if len(items) < 20:
            return {"n": len(items)}
        s = sorted(items, key=lambda x: float(x[key]))
        k = max(1, len(s) // 10)
        bot = s[:k]
        top = s[-k:]
        return {
            "n_each": k,
            "bottom10": bucket_stats(bot),
            "top10": bucket_stats(top),
            "matched_mean_lift": round(
                bucket_stats(top)["matched_mean"] - bucket_stats(bot)["matched_mean"], 4
            ),
            "ge4_rate_lift": round(
                bucket_stats(top)["ge4_rate"] - bucket_stats(bot)["ge4_rate"], 4
            ),
            "ge6_in_top10": bucket_stats(top).get("ge6", 0),
            "ge5_in_top10": bucket_stats(top).get("ge5", 0),
        }

    aggressive = {
        "best_pattern_decile": decile_compare(best_rows, "pattern"),
        "allsets_pattern_decile": decile_compare(all_sets, "pattern"),
    }

    # decision rule
    lift = analyses["best_pattern"]["lift"]
    keep_pattern = (
        lift["matched_mean_Q4_minus_Q1"] > 0.02
        or lift["ge3_rate_Q4_minus_Q1"] > 0.01
        or lift["ge4_rate_Q4_minus_Q1"] > 0.002
    )
    decision = {
        "pattern_aux_keep": bool(keep_pattern),
        "reason": (
            "Q4>Q1 lift on matched/ge3/ge4 → 유지·가중 실험 후보"
            if keep_pattern
            else "분위수 lift 약함 → K-PATTERN-1 신호는 조건부/샘플; 가중 성급 금지"
        ),
        "next_attack_axes": [
            "K-ATTACK-COVER: covering/wheel 수학 — N장으로 4·5등 보장 설계 (1등 확률은 티켓수로 정직 계산)",
            "K-ATTACK-SLICE: 구간일치+패턴AUX 상위 교집합에서만 라이브 세트 승격",
            "K-ATTACK-SEARCH: 뇌당 오버샘플(20~60)→AUX·covering 필터→top5 (K-Y 방식 확장)",
            "K-ATTACK-BAYES: 3뇌 사후가중(성적상관↓ 이용) — 삭제가 아니라 동적 가중",
            "K-ATTACK-EV: 공동당첨 최소화·인기조합 회피 (잭팟 EV) — 예측이 아닌 배당 최적화",
        ],
        "ambition": {
            "goal": "프로젝트 생애 1등 ≥1회 (정직 확률·과학적 탐색)",
            "not": "보장·마케팅 허위·null 무시",
            "stance": "보수 기각이 아니라 공격적 가설검정 + 커버링·슬라이스·오버샘플",
        },
    }

    payload = {
        "id": "K-PATTERN-2",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "window": [2, 1234],
        "definition": {
            "pattern_score": "reasoning '패턴돋보기 … 점수X'",
            "quartiles": "nearest-rank on score within unit",
            "units": "best_set rows · all 5 sets with matched_count",
        },
        "analyses": analyses,
        "by_brain_best_pattern": by_brain,
        "aggressive_decile": aggressive,
        "decision": decision,
        "links": {
            "pattern1": "docs/benchmarks/20260729_KPATTERN_tier4_vs_control.json",
            "trust": "docs/benchmarks/20260729_KTRUST_bench.json",
            "warrant": "My_Drive_Sync/SUMMARY/WARRANT.md",
        },
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print("best_pattern", analyses["best_pattern"]["by_quartile"])
    print("lift", analyses["best_pattern"]["lift"])
    print("allsets lift", analyses["allsets_pattern"]["lift"])
    print("decile", aggressive["best_pattern_decile"])
    print("KEEP", decision["pattern_aux_keep"], decision["reason"])
    con.close()


if __name__ == "__main__":
    main()
