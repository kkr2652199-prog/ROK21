# -*- coding: utf-8 -*-
"""K-STRUCTURE-COVER — 구조 질량 covering survey (wire 없음).

pool+repack 후보 → struct_cover_v1 5장 vs 현행 repack 5장 ge3 대조.
명분: K-MATH-PATTERN-WARRANT (합·존·홀짝·연속).

Usage:
  python tools/_k_structure_cover_survey.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KSTRUCTURE_COVER_survey.json"
OUT_MD = ROOT / "reports" / "20260805_KSTRUCTURE_COVER_SURVEY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BRAINS = ("stat", "markov", "review")
LO, HI = 1035, 1234
NULL5 = 0.1137
PIN = 0.1447
REF_HYBRID = {"stat": 0.165, "markov": 0.130, "review": 0.135}


def _hits(nums, actual) -> int:
    return len(set(int(x) for x in nums) & actual)


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_view_cache import get_cached_pool_view_any_schema
    from app.testlotto.structure_cover import (
        STRUCTURE_COVER_WIRE,
        coverage_report,
        select_structure_cover,
    )

    init_testlotto_db()
    conn = get_lotto_db()
    draws = {
        int(r["draw_no"]): {int(r[f"num{k}"]) for k in range(1, 7)}
        for r in conn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
            "WHERE draw_no BETWEEN ? AND ?",
            (LO, HI),
        )
    }
    conn.close()

    base_bests: dict[str, list[int]] = {b: [] for b in BRAINS}
    cover_bests: dict[str, list[int]] = {b: [] for b in BRAINS}
    cover_unique: dict[str, list[int]] = {b: [] for b in BRAINS}
    base_unique: dict[str, list[int]] = {b: [] for b in BRAINS}
    n_ok = 0

    for dno in range(LO, HI + 1):
        if dno not in draws:
            continue
        pv = get_cached_pool_view_any_schema(dno)
        if not pv or not pv.get("ok"):
            continue
        actual = draws[dno]
        n_ok += 1
        for tag in BRAINS:
            pool = pv.get("pool_by_brain", {}).get(tag) or []
            repack = pv.get("repack_by_brain", {}).get(tag) or []
            if not pool or not repack:
                continue
            # baseline = 현행 repack
            bh = max((_hits(s["nums"], actual) for s in repack), default=0)
            base_bests[tag].append(bh)
            base_unique[tag].append(
                coverage_report(repack).get("unique_structure_keys", 0)
            )

            cands = []
            for s in pool:
                cands.append({**s, "kind": "pool"})
            for s in repack:
                cands.append({**s, "kind": "repack"})
            picked = select_structure_cover(cands, n_sets=5)
            ch = max((_hits(s["nums"], actual) for s in picked), default=0)
            cover_bests[tag].append(ch)
            cover_unique[tag].append(
                coverage_report(picked).get("unique_structure_keys", 0)
            )

    def pack(bests: list[int]) -> dict:
        n = len(bests)
        g = sum(1 for x in bests if x >= 3)
        rate = round(g / n, 4) if n else 0.0
        return {
            "n": n,
            "ge3_count": g,
            "ge3_rate": rate,
            "mean_best": round(mean(bests), 4) if bests else 0.0,
            "delta_vs_null": round(rate - NULL5, 4),
            "delta_vs_pin": round(rate - PIN, 4),
        }

    by_brain = {}
    any_up = False
    for tag in BRAINS:
        b = pack(base_bests[tag])
        c = pack(cover_bests[tag])
        dlt = round(c["ge3_rate"] - b["ge3_rate"], 4)
        if dlt >= 0.01:
            any_up = True
        by_brain[tag] = {
            "baseline_repack": b,
            "struct_cover": c,
            "delta_ge3": dlt,
            "ref_hybrid_ge3": REF_HYBRID.get(tag),
            "mean_unique_keys_baseline": round(mean(base_unique[tag]), 4)
            if base_unique[tag]
            else 0,
            "mean_unique_keys_cover": round(mean(cover_unique[tag]), 4)
            if cover_unique[tag]
            else 0,
        }

    # wire 권고: 어떤 뇌든 +0.01 이상이고 baseline 이상
    wire_brains = [t for t in BRAINS if by_brain[t]["delta_ge3"] >= 0.01]
    verdict = "GO-WAIT" if wire_brains else ("HOLD" if not any_up else "WATCH")
    if not wire_brains and any(
        by_brain[t]["delta_ge3"] > 0 for t in BRAINS
    ):
        verdict = "WATCH"
    if all(by_brain[t]["delta_ge3"] <= 0 for t in BRAINS):
        verdict = "HOLD"

    payload = {
        "id": "K-STRUCTURE-COVER",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "phase": "survey",
        "wire": False,
        "STRUCTURE_COVER_WIRE_live": STRUCTURE_COVER_WIRE,
        "draw_range": [LO, HI],
        "n_draws": n_ok,
        "axis": "sum+zone+odd+consec covering (mass bands)",
        "warrant_ref": "20260805_KMATH_PATTERN_WARRANT.json",
        "by_brain": by_brain,
        "verdict": {
            "label": verdict,
            "wire_brains": wire_brains,
            "next": (
                f"struct_cover wire GO-WAIT ({','.join(wire_brains)}) · 형 GO"
                if wire_brains
                else "STRUCTURE_COVER HOLD · 설계모듈 유지 · 형 다음축/AUTO설계"
            ),
        },
        "pass": True,  # survey 완료
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-STRUCTURE-COVER — 구조 질량 covering survey",
        "",
        f"📅 {payload['ts'][:10]} · **{verdict}** · wire=**False** · n=**{n_ok}** ({LO}~{HI})",
        "",
        "## 0) 한 줄",
        "",
        "명분(합·존·홀짝·연속)으로 5장이 **구조키를 넓게 덮도록** 재선정. "
        "1등확률 보증 아님 · 현행 repack 대비 ge3만 대조.",
        "",
        "## 1) 결과",
        "",
        "| 뇌 | baseline ge3 | cover ge3 | Δ | uniq키 base→cover |",
        "|----|-------------:|----------:|---:|------------------:|",
    ]
    for tag in BRAINS:
        r = by_brain[tag]
        lines.append(
            f"| {tag} | {r['baseline_repack']['ge3_rate']:.4f} | "
            f"{r['struct_cover']['ge3_rate']:.4f} | {r['delta_ge3']:+.4f} | "
            f"{r['mean_unique_keys_baseline']:.2f}→{r['mean_unique_keys_cover']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## 2) 설계 요지 (`structure_cover.py`)",
            "",
            "- 축: sum_bucket / odd / zone_key / has_consec",
            "- 질량 가점: 홀짝 2~4 · 합 100~180 · 존 혼합 · **연속 감점 없음**",
            "- 극단(0·6홀, 존≥5) 감점",
            "- 탐욕: 새 구조키 + 부분축 다양성 + 질량",
            "- `STRUCTURE_COVER_WIRE=False` 고정(이번 패치)",
            "",
            f"## 3) 판정 **{verdict}**",
            "",
            f"- wire 후보 뇌: {wire_brains or '없음'}",
            f"- 다음: {payload['verdict']['next']}",
            "",
            f"근거: `{OUT_JSON.name}` · 명분 `{payload['warrant_ref']}`",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "n": n_ok,
        "by_brain": {t: {"base": by_brain[t]["baseline_repack"]["ge3_rate"], "cover": by_brain[t]["struct_cover"]["ge3_rate"], "d": by_brain[t]["delta_ge3"]} for t in BRAINS},
        "wire_brains": wire_brains,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
