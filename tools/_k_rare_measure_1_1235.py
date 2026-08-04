# -*- coding: utf-8 -*-
"""K-RARE-MEASURE — 1~1235 실측 vs 이론 템플릿 가중 + rare_bundle 갭.

예측/발권 wire 없음. 진단층 측정만.

Usage:
  python tools/_k_rare_measure_1_1235.py
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

C45_6 = math.comb(45, 6)


def _odd(nums: list[int]) -> int:
    return sum(1 for n in nums if n % 2)


def _zones(nums: list[int]) -> tuple[int, int, int]:
    low = sum(1 for n in nums if 1 <= n <= 15)
    mid = sum(1 for n in nums if 16 <= n <= 30)
    high = sum(1 for n in nums if 31 <= n <= 45)
    return low, mid, high


def _max_run(nums: list[int]) -> int:
    s = sorted(nums)
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def _n_consec_pairs(nums: list[int]) -> int:
    s = sorted(nums)
    return sum(1 for i in range(5) if s[i + 1] == s[i] + 1)


def _span(nums: list[int]) -> int:
    s = sorted(nums)
    return s[-1] - s[0]


def theory_odd_even() -> dict[str, float]:
    """P(odd=k) = C(23,k)*C(22,6-k)/C(45,6) for k where feasible."""
    out = {}
    for k in range(0, 7):
        if k > 23 or (6 - k) > 22:
            out[str(k)] = 0.0
            continue
        out[str(k)] = math.comb(23, k) * math.comb(22, 6 - k) / C45_6
    return out


def theory_zone_all_low() -> float:
    return math.comb(15, 6) / C45_6


def theory_parity_all_odd() -> float:
    return math.comb(23, 6) / C45_6


def theory_parity_all_even() -> float:
    return math.comb(22, 6) / C45_6


def theory_consec_ge1_pair() -> float:
    # no consecutive pair ↔ C(40,6) via gap transform
    return 1.0 - math.comb(40, 6) / C45_6


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.rare_bundle import PATTERN_META, detect_patterns

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6
        FROM lotto_draws WHERE draw_no BETWEEN 1 AND 1235
        ORDER BY draw_no
        """
    ).fetchall()
    cat_n = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(is_ultra_rare),0) FROM testlotto_rare_bundle_catalog"
    ).fetchone()
    hit_ultra = conn.execute(
        "SELECT COALESCE(SUM(is_ultra_rare_hit),0) FROM testlotto_rare_bundle_hits"
    ).fetchone()[0]
    conn.close()

    draws = []
    for r in rows:
        d = dict(r)
        nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
        draws.append({"draw_no": int(d["draw_no"]), "nums": nums})

    n = len(draws)
    unique = len({tuple(d["nums"]) for d in draws})

    odd_c = Counter(_odd(d["nums"]) for d in draws)
    zone_all_low = sum(1 for d in draws if all(x <= 15 for x in d["nums"]))
    zone_all_high = sum(1 for d in draws if all(x >= 31 for x in d["nums"]))
    all_odd = sum(1 for d in draws if _odd(d["nums"]) == 6)
    all_even = sum(1 for d in draws if _odd(d["nums"]) == 0)
    consec_ge1 = sum(1 for d in draws if _n_consec_pairs(d["nums"]) >= 1)
    run6 = sum(1 for d in draws if _max_run(d["nums"]) >= 6)
    run5 = sum(1 for d in draws if _max_run(d["nums"]) >= 5)
    arith = sum(
        1
        for d in draws
        if len({d["nums"][i + 1] - d["nums"][i] for i in range(5)}) == 1
    )

    # pattern hits via detect_patterns
    pat_c: Counter[str] = Counter()
    for d in draws:
        for p in detect_patterns(d["nums"]):
            pat_c[p] += 1

    th_oe = theory_odd_even()
    comparisons = [
        {
            "id": "odd_k",
            "rows": [
                {
                    "k": k,
                    "emp": round(odd_c.get(k, 0) / n, 4),
                    "null": round(th_oe[str(k)], 4),
                    "n_emp": odd_c.get(k, 0),
                }
                for k in range(0, 7)
            ],
        },
        {
            "id": "consec_ge1_pair",
            "emp": round(consec_ge1 / n, 4),
            "null": round(theory_consec_ge1_pair(), 4),
            "n_emp": consec_ge1,
        },
        {
            "id": "zone_all_low_1_15",
            "emp": round(zone_all_low / n, 6),
            "null": round(theory_zone_all_low(), 6),
            "n_emp": zone_all_low,
            "w": math.comb(15, 6),
        },
        {
            "id": "zone_all_high_31_45",
            "emp": round(zone_all_high / n, 6),
            "null": round(theory_zone_all_low(), 6),
            "n_emp": zone_all_high,
            "w": math.comb(15, 6),
        },
        {
            "id": "parity_all_odd",
            "emp": round(all_odd / n, 6),
            "null": round(theory_parity_all_odd(), 6),
            "n_emp": all_odd,
            "w": math.comb(23, 6),
        },
        {
            "id": "parity_all_even",
            "emp": round(all_even / n, 6),
            "null": round(theory_parity_all_even(), 6),
            "n_emp": all_even,
            "w": math.comb(22, 6),
        },
        {
            "id": "consec_run_ge6",
            "emp": round(run6 / n, 6),
            "null": round(40 / C45_6, 6),
            "n_emp": run6,
            "w": 40,
        },
        {
            "id": "consec_run_ge5",
            "emp": round(run5 / n, 6),
            "n_emp": run5,
            "null_note": "exact w needs inclusion; PATTERN_META consec_5_window≈660",
            "w_ref": 660,
        },
        {
            "id": "arithmetic_6",
            "emp": round(arith / n, 6),
            "null": round(165 / C45_6, 6),
            "n_emp": arith,
            "w": 165,
        },
    ]

    # gaps: taxonomy axes missing from rare_bundle PATTERN_META / catalog
    existing_meta = set(PATTERN_META.keys())
    taxonomy_wanted = {
        "odd_even_k",  # full 0..6 distribution templates
        "zone_triplet_l_m_h",  # all (l,m,h) with l+m+h=6
        "sum_bin",
        "span_bin",
        "consec_pair_count",
        "max_run",
        "ending_digit_hist",
        "carry_k",  # as_of dependent
        "lo_hi_4way",  # LotteryCodex LO/LE/HO/HE
    }
    covered_approx = {
        "odd_even_k": "partial via parity_all_odd/even only",
        "zone_triplet_l_m_h": "partial zone_all_low/high only",
        "sum_bin": "MISSING",
        "span_bin": "partial spread_min_gap7/8",
        "consec_pair_count": "partial consec_*plus runs",
        "max_run": "partial consec_*plus",
        "ending_digit_hist": "MISSING",
        "carry_k": "MISSING (as_of; WARRANT has hist)",
        "lo_hi_4way": "MISSING",
    }
    gaps = [
        {
            "axis": a,
            "status": covered_approx[a],
            "in_PATTERN_META": a in existing_meta,
        }
        for a in sorted(taxonomy_wanted)
    ]

    payload = {
        "id": "K-RARE-MEASURE-1_1235",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "draw_range": [1, 1235],
        "n_draws": n,
        "unique_drawn_sets": unique,
        "duplicate_sets": n - unique,
        "C_45_6": C45_6,
        "coverage_of_universe": round(unique / C45_6, 8),
        "rare_bundle": {
            "catalog_n": int(cat_n[0]),
            "ultra_n": int(cat_n[1] or 0),
            "ultra_hits_in_history": int(hit_ultra or 0),
            "PATTERN_META_keys": sorted(existing_meta),
        },
        "detect_pattern_counts": {k: int(v) for k, v in sorted(pat_c.items())},
        "comparisons": comparisons,
        "taxonomy_gaps": gaps,
        "verdict": "MEASURED",
        "wire": False,
        "note": "진단 측정 · 발권/λ/cover 미변경 · 당첨P↑ 클레임 없음",
    }

    out_json = ROOT / "docs" / "benchmarks" / "20260805_KRARE_MEASURE_1_1235.json"
    out_md = ROOT / "reports" / "20260805_KRARE_MEASURE_1_1235.md"
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / out_md.name
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-RARE-MEASURE-1_1235",
        "",
        f"📅 {payload['ts'][:10]} · **MEASURED** · wire=False · n={n}",
        "",
        "## 우주",
        "",
        f"- C(45,6)=**{C45_6}** · unique={unique} · dup={n - unique} · coverage={payload['coverage_of_universe']}",
        f"- rare_bundle catalog={payload['rare_bundle']['catalog_n']} ultra={payload['rare_bundle']['ultra_n']} hist_ultra_hits={payload['rare_bundle']['ultra_hits_in_history']}",
        "",
        "## 실측 vs 이론 (요약)",
        "",
    ]
    for c in comparisons:
        if c["id"] == "odd_k":
            lines.append("### odd=k")
            for row in c["rows"]:
                lines.append(
                    f"- k={row['k']}: emp={row['emp']} null={row['null']} n={row['n_emp']}"
                )
        else:
            lines.append(
                f"- **{c['id']}**: emp={c.get('emp')} null={c.get('null')} n={c.get('n_emp')} w={c.get('w', c.get('w_ref'))}"
            )
    lines.extend(["", "## taxonomy 갭", ""])
    for g in gaps:
        lines.append(f"- `{g['axis']}`: {g['status']}")
    lines.extend(
        [
            "",
            "## detect_patterns 회수 (1~1235)",
            "",
        ]
    )
    for k, v in sorted(pat_c.items(), key=lambda x: -x[1]):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", f"근거: `{out_json.name}`", ""])
    text = "\n".join(lines)
    out_md.write_text(text, encoding="utf-8")
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(json.dumps({"ok": True, "out": out_json.name, "gaps": len(gaps)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
