# -*- coding: utf-8 -*-
"""K-TRANSITION-HIT-WARRANT — D_N → D_{N+1} 적중번호 명분 라벨 전수.

READ-ONLY. wire/brain/engine/발권 미접촉.
당첨확률↑ 클레임 금지 — 설명 라벨 비율만.

Usage:
  python tools/_k_transition_hit_warrant.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KTRANSITION_HIT_WARRANT.json"
OUT_MD = ROOT / "reports" / "20260805_KTRANSITION_HIT_WARRANT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 101, 1234  # N 기준 · N+1 = 102..1235
SIM_K = 2
SPOT_N = 1234


def _conn():
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    return get_lotto_db()


def load_draws(conn) -> dict[int, list[int]]:
    rows = conn.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6
        FROM lotto_draws ORDER BY draw_no
        """
    ).fetchall()
    out: dict[int, list[int]] = {}
    for r in rows:
        d = dict(r)
        out[int(d["draw_no"])] = sorted(int(d[f"num{k}"]) for k in range(1, 7))
    return out


def load_transition_top15(conn) -> dict[int, list[int]]:
    rows = conn.execute(
        """
        SELECT draw_no, top15 FROM transition_log WHERE sim_k=?
        """,
        (SIM_K,),
    ).fetchall()
    out: dict[int, list[int]] = {}
    for r in rows:
        d = dict(r)
        top = json.loads(d["top15"])
        out[int(d["draw_no"])] = [int(x) for x in top]
    return out


def zone_of(n: int) -> str:
    if n <= 15:
        return "L"
    if n <= 30:
        return "M"
    return "H"


def consec_members(nums: list[int]) -> set[int]:
    """번호가 D_{N+1} 세트 내 연속쌍에 속하면 포함."""
    s = set(nums)
    hit: set[int] = set()
    for x in nums:
        if (x - 1) in s or (x + 1) in s:
            hit.add(x)
    return hit


def label_number(
    num: int,
    d_n: set[int],
    top15: list[int],
    consec: set[int],
) -> dict[str, Any]:
    labels: list[str] = []
    # 1) carry = D_N ∩ D_{N+1}
    if num in d_n:
        labels.append("carry")
    # 2) trans_top15
    rank: int | None = None
    if num in top15:
        labels.append("trans_top15")
        rank = top15.index(num) + 1  # 1-based
    # 3) struct_consec
    if num in consec:
        labels.append("struct_consec")
    # 4) attribute tags (소속 · unexplained 판정에는 미사용)
    labels.append(f"struct_zone_{zone_of(num)}")
    labels.append("struct_odd" if num % 2 else "struct_even")

    primary = {"carry", "trans_top15", "struct_consec"}
    has_primary = bool(primary & set(labels))
    if not has_primary:
        labels.append("unexplained")

    return {
        "num": num,
        "labels": labels,
        "trans_top15_rank": rank,
        "explained": has_primary,
    }


def run() -> dict[str, Any]:
    conn = _conn()
    try:
        draws = load_draws(conn)
        tops = load_transition_top15(conn)
        n_log = len(tops)
    finally:
        conn.close()

    per_draw: list[dict[str, Any]] = []
    label_hits = Counter()  # label -> number-occurrences
    primary_hits = Counter()
    n_numbers = 0
    n_explained = 0
    n_unexplained = 0
    n_draws_ok = 0
    n_skip_no_log = 0
    n_skip_no_next = 0

    # co-occurrence of primary labels on same number
    combo = Counter()

    for n in range(LO, HI + 1):
        if n + 1 not in draws:
            n_skip_no_next += 1
            continue
        if n not in tops:
            n_skip_no_log += 1
            continue
        d_n = set(draws[n])
        d_n1 = draws[n + 1]
        top15 = tops[n]
        consec = consec_members(d_n1)
        carry_nums = sorted(d_n & set(d_n1))

        labeled = [label_number(x, d_n, top15, consec) for x in d_n1]
        n_draws_ok += 1
        for lab in labeled:
            n_numbers += 1
            for L in lab["labels"]:
                label_hits[L] += 1
            prim = [L for L in lab["labels"] if L in ("carry", "trans_top15", "struct_consec")]
            if lab["explained"]:
                n_explained += 1
                primary_hits[tuple(sorted(prim))] += 1
                combo["|".join(sorted(prim)) or "none"] += 1
            else:
                n_unexplained += 1

        row = {
            "N": n,
            "N1": n + 1,
            "D_N": draws[n],
            "D_N1": d_n1,
            "carry": carry_nums,
            "top15": top15,
            "numbers": labeled,
        }
        per_draw.append(row)

    # rates
    def rate(c: int) -> float:
        return round(c / n_numbers, 6) if n_numbers else 0.0

    rates = {
        "carry": rate(label_hits.get("carry", 0)),
        "trans_top15": rate(label_hits.get("trans_top15", 0)),
        "struct_consec": rate(label_hits.get("struct_consec", 0)),
        "unexplained": rate(label_hits.get("unexplained", 0)),
        "explained_any_primary": rate(n_explained),
    }

    # expected baselines (combinatorial / empirical refs — 설명용)
    # random top15 ∩ one number: 15/45 = 1/3
    # carry per number given mean carry≈0.826 over 6 → ~0.138
    baselines = {
        "trans_top15_null_per_num": round(15 / 45, 6),
        "note": "null은 균등 가정. carry/consec는 세트 구조 의존 — 비율만 보고 확률↑ 금지",
    }

    spot = next((r for r in per_draw if r["N"] == SPOT_N), None)

    # aggregate: how often each primary alone vs stacked
    primary_combo_rates = {
        k: {"count": v, "rate_of_explained": round(v / n_explained, 6) if n_explained else 0.0}
        for k, v in sorted(combo.items(), key=lambda x: -x[1])
    }

    # period stability on explained rate
    periods = {
        "early": (101, 478),
        "mid": (479, 856),
        "late": (857, 1234),
    }
    by_period: dict[str, Any] = {}
    for name, (lo, hi) in periods.items():
        rows = [r for r in per_draw if lo <= r["N"] <= hi]
        nums = [lab for r in rows for lab in r["numbers"]]
        exp = sum(1 for lab in nums if lab["explained"])
        tot = len(nums)
        by_period[name] = {
            "n_draws": len(rows),
            "n_numbers": tot,
            "explained_rate": round(exp / tot, 6) if tot else 0.0,
            "unexplained_rate": round(1 - (exp / tot), 6) if tot else 0.0,
        }
    erates = [by_period[k]["explained_rate"] for k in ("early", "mid", "late")]
    by_period["max_gap"] = round(max(erates) - min(erates), 6) if erates else 0.0
    by_period["stable"] = by_period["max_gap"] < 0.05

    # compact sample rows for JSON (full dump too large — keep spot + summary only)
    # store per_draw_summary counts only; spot full; optional first/last 3
    sample_heads = per_draw[:2]
    sample_tails = per_draw[-2:]

    payload: dict[str, Any] = {
        "id": "K-TRANSITION-HIT-WARRANT",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "CATALOG",
        "wire": False,
        "claim": "설명 라벨 비율만 · 당첨확률↑ 금지",
        "range": {"N_lo": LO, "N_hi": HI, "N1_max": HI + 1},
        "n_draws": n_draws_ok,
        "n_numbers": n_numbers,
        "n_explained": n_explained,
        "n_unexplained": n_unexplained,
        "n_skip_no_log": n_skip_no_log,
        "n_skip_no_next": n_skip_no_next,
        "transition_log_rows": n_log,
        "sim_k": SIM_K,
        "label_definition": {
            "carry": "num ∈ D_N ∩ D_{N+1}",
            "trans_top15": "num ∈ transition_log.top15 (draw_no=N, sim_k=2)",
            "trans_top15_rank": "1-based index in top15",
            "struct_consec": "num ∈ consecutive pair within D_{N+1}",
            "struct_zone_*": "L1-15 / M16-30 / H31-45 attribute",
            "struct_odd/even": "parity attribute",
            "explained": "carry OR trans_top15 OR struct_consec",
            "unexplained": "no primary warrant (zone/parity alone do not explain)",
        },
        "rates": rates,
        "label_counts": dict(label_hits),
        "primary_combo": primary_combo_rates,
        "baselines": baselines,
        "by_period": by_period,
        "spot_1234_1235": spot,
        "sample_heads": sample_heads,
        "sample_tails": sample_tails,
        "pass": True,
        "tool": "tools/_k_transition_hit_warrant.py",
        "prior": [
            "docs/benchmarks/20260805_KTRANSITION_COLLECT_DESIGN.json",
            "docs/benchmarks/20260805_KTRANSITION_FUSION_N200.json",
            "My_Drive_Sync/SUMMARY/WARRANT.md",
        ],
        "forbid": [
            "engine.py",
            "random.choices",
            "발권 INSERT",
            "coordinator 수정",
            "WIRE ON",
            "당첨확률↑ 클레임",
        ],
    }
    return payload


def write_md(payload: dict[str, Any]) -> None:
    rates = payload["rates"]
    spot = payload.get("spot_1234_1235") or {}
    lines = [
        "# K-TRANSITION-HIT-WARRANT — D_N→D_{N+1} 적중 명분 카탈로그 (2026-08-05)",
        "",
        "> READ-ONLY · wire=False · **당첨확률↑ 클레임 금지** · 설명 라벨 비율만",
        "",
        f"- **판정:** `{payload['verdict']}`",
        f"- range N={payload['range']['N_lo']}~{payload['range']['N_hi']} · "
        f"n_draws=**{payload['n_draws']}** · n_numbers=**{payload['n_numbers']}**",
        f"- transition_log rows=**{payload['transition_log_rows']}** (sim_k={payload['sim_k']})",
        "",
        "## 라벨 정의",
        "",
        "| 라벨 | 의미 |",
        "|------|------|",
        "| carry | ∈ D_N ∩ D_{N+1} |",
        "| trans_top15 | ∈ transition top15 (유사≥2 next-freq) |",
        "| struct_consec | D_{N+1} 내 연속쌍 소속 |",
        "| struct_zone_*/odd/even | 소속 속성 (단독으로는 explained 아님) |",
        "| unexplained | primary 명분 없음 |",
        "",
        "## 전수 비율 (번호 단위)",
        "",
        f"- explained_any_primary=**{rates['explained_any_primary']}** "
        f"({payload['n_explained']}/{payload['n_numbers']})",
        f"- unexplained=**{rates['unexplained']}** ({payload['n_unexplained']})",
        f"- carry=**{rates['carry']}**",
        f"- trans_top15=**{rates['trans_top15']}** (null≈{payload['baselines']['trans_top15_null_per_num']})",
        f"- struct_consec=**{rates['struct_consec']}**",
        "",
        "## primary 조합 (explained 내부)",
        "",
    ]
    for k, v in payload["primary_combo"].items():
        lines.append(f"- `{k or 'none'}`: count={v['count']} · share={v['rate_of_explained']}")
    lines += [
        "",
        "## 구간별 explained_rate",
        "",
        f"- early/mid/late = "
        f"{payload['by_period']['early']['explained_rate']} / "
        f"{payload['by_period']['mid']['explained_rate']} / "
        f"{payload['by_period']['late']['explained_rate']}",
        f"- max_gap=**{payload['by_period']['max_gap']}** · "
        f"stable=**{payload['by_period']['stable']}**",
        "",
        "## spot 1234→1235",
        "",
    ]
    if spot:
        lines.append(f"- D_N=`{spot['D_N']}`")
        lines.append(f"- D_N1=`{spot['D_N1']}`")
        lines.append(f"- carry=`{spot['carry']}`")
        for lab in spot["numbers"]:
            lines.append(
                f"- {lab['num']}: {lab['labels']}"
                + (f" rank={lab['trans_top15_rank']}" if lab.get("trans_top15_rank") else "")
            )
    lines += [
        "",
        "## 해석 (과장 금지)",
        "",
        "- 본 카탈로그는 「다음 회 번호가 어떤 서술로 붙는가」비율이다.",
        "- trans_top15 비율이 null(15/45)과 비슷하면 **전이 top15는 배포 예측력이 없다** "
        "(COLLECT mean≈2.0과 정합).",
        "- carry/consec는 세트 구조·이월 서술 — WARRANT.md 뇌 성적과 별개.",
        "- 패치 대비: 라벨을 **학습 로그·설명 문자열**에 붙이는 쪽부터 · 발권 가중은 형 GO.",
        "",
        f"- tool: `{payload['tool']}`",
        f"- JSON: `docs/benchmarks/20260805_KTRANSITION_HIT_WARRANT.json`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")


def main() -> int:
    payload = run()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_md(payload)
    print(
        json.dumps(
            {
                "ok": True,
                "verdict": payload["verdict"],
                "n_draws": payload["n_draws"],
                "rates": payload["rates"],
                "by_period_stable": payload["by_period"]["stable"],
                "out": str(OUT_JSON),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
