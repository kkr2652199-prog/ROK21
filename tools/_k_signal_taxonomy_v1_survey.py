# -*- coding: utf-8 -*-
"""K-SIGNAL-TAXONOMY-V1 — L1 이론vs실측 · L3 PMI survey (진단 · wire 없음).

Usage:
  python tools/_k_signal_taxonomy_v1_survey.py
  python tools/_k_signal_taxonomy_v1_survey.py --skip-exact-w
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

C45_6 = math.comb(45, 6)
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KSIGNAL_TAXONOMY_V1.json"
OUT_MD = ROOT / "reports" / "20260805_KSIGNAL_TAXONOMY_V1.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


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


def _is_arith6(nums: list[int]) -> bool:
    s = sorted(nums)
    gaps = {s[i + 1] - s[i] for i in range(5)}
    return len(gaps) == 1 and next(iter(gaps)) > 0


def closed_form_w() -> dict[str, dict[str, Any]]:
    """공식·소열거로 확정 가능한 w."""
    from app.testlotto.rare_bundle import enumerate_arithmetic_6

    odd = {k: math.comb(23, k) * math.comb(22, 6 - k) for k in range(0, 7)}
    return {
        "parity_all_odd": {"w": math.comb(23, 6), "method": "C(23,6)"},
        "parity_all_even": {"w": math.comb(22, 6), "method": "C(22,6)"},
        "zone_all_low_1_15": {"w": math.comb(15, 6), "method": "C(15,6)"},
        "zone_all_high_31_45": {"w": math.comb(15, 6), "method": "C(15,6)"},
        "consec_6": {"w": 40, "method": "windows_1to40"},
        "consec_ge1_pair": {
            "w": C45_6 - math.comb(40, 6),
            "method": "C(45,6)-C(40,6)",
        },
        "rank_top1000": {"w": 1000, "method": "combinadic_slice"},
        "rank_bottom1000": {"w": 1000, "method": "combinadic_slice"},
        "split_exact_123_434445": {"w": 1, "method": "singleton"},
        "split_low10_high10": {
            "w": math.comb(10, 3) * math.comb(10, 3),
            "method": "C(10,3)*C(10,3)_extreme_split_proxy",
            "note": "low3+high3 only · detect_patterns는 mid 허용 더 넓음",
        },
        "arithmetic_6": {
            "w": len(enumerate_arithmetic_6()),
            "method": "enumerate_d_ge1",
        },
        "odd_k": {
            "w_by_k": odd,
            "method": "C(23,k)*C(22,6-k)",
        },
    }


def scan_universe_runs(*, skip: bool) -> dict[str, Any]:
    """전수 스캔으로 max_run / min_gap 템플릿 w (약 8M · 수십초)."""
    if skip:
        return {
            "skipped": True,
            "consec_3plus": {"w": None, "note": "use --no-skip for exact"},
            "consec_4plus": {"w": None},
            "consec_5plus": {"w": None},
            "spread_min_gap7": {"w": None},
            "spread_min_gap8": {"w": None},
        }
    c3 = c4 = c5 = g7 = g8 = 0
    # iterate combinations of 1..45 choose 6
    for combo in combinations(range(1, 46), 6):
        nums = list(combo)
        mr = _max_run(nums)
        if mr >= 3:
            c3 += 1
        if mr >= 4:
            c4 += 1
        if mr >= 5:
            c5 += 1
        gaps = [nums[i + 1] - nums[i] for i in range(5)]
        mg = min(gaps)
        if mg >= 7:
            g7 += 1
        if mg >= 8:
            g8 += 1
    return {
        "skipped": False,
        "method": "full_C45_6_scan",
        "consec_3plus": {"w": c3},
        "consec_4plus": {"w": c4},
        "consec_5plus": {"w": c5},
        "spread_min_gap7": {"w": g7},
        "spread_min_gap8": {"w": g8},
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


def empirical_l1(draws: list[dict]) -> dict[str, Any]:
    from app.testlotto.rare_bundle import detect_patterns

    n = len(draws)
    pat_c: Counter[str] = Counter()
    odd_c: Counter[int] = Counter()
    consec_ge1 = 0
    birthday_ge4 = 0  # count of nums <=31 >=4
    sum_le_120 = 0
    for d in draws:
        nums = d["nums"]
        for p in detect_patterns(nums):
            pat_c[p] += 1
        odd_c[sum(1 for x in nums if x % 2)] += 1
        if _n_consec_pairs(nums) >= 1:
            consec_ge1 += 1
        if sum(1 for x in nums if x <= 31) >= 4:
            birthday_ge4 += 1
        if sum(nums) <= 120:
            sum_le_120 += 1
    return {
        "n": n,
        "pattern_emp": {
            k: {"n": v, "rate": round(v / n, 6)} for k, v in sorted(pat_c.items())
        },
        "odd_k_emp": {
            str(k): {"n": odd_c.get(k, 0), "rate": round(odd_c.get(k, 0) / n, 6)}
            for k in range(0, 7)
        },
        "consec_ge1_pair_emp": {
            "n": consec_ge1,
            "rate": round(consec_ge1 / n, 6),
        },
        "l4_proxy_emp": {
            "birthday_le31_ge4": {
                "n": birthday_ge4,
                "rate": round(birthday_ge4 / n, 6),
            },
            "sum_le_120": {"n": sum_le_120, "rate": round(sum_le_120 / n, 6)},
        },
    }


def deviation_table(
    emp: dict[str, Any], closed: dict[str, Any], scanned: dict[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    n = emp["n"]

    def add(tag: str, w: int | None, method: str, emp_n: int | None = None, emp_rate: float | None = None):
        if emp_n is None:
            pe = emp["pattern_emp"].get(tag)
            if pe:
                emp_n, emp_rate = pe["n"], pe["rate"]
            elif tag == "consec_ge1_pair":
                emp_n = emp["consec_ge1_pair_emp"]["n"]
                emp_rate = emp["consec_ge1_pair_emp"]["rate"]
            else:
                emp_n, emp_rate = 0, 0.0
        p_th = (w / C45_6) if w is not None else None
        exp = (p_th * n) if p_th is not None else None
        dev = None
        if p_th is not None and emp_rate is not None:
            # relative: (emp - theory) / max(theory, eps)
            den = max(p_th, 1e-12)
            dev = round((emp_rate - p_th) / den, 4)
        rows.append(
            {
                "tag": tag,
                "w": w,
                "p_theory": round(p_th, 8) if p_th is not None else None,
                "emp_n": emp_n,
                "emp_rate": emp_rate,
                "expected_n": round(exp, 2) if exp is not None else None,
                "deviation_score": dev,
                "method": method,
            }
        )

    for tag in (
        "parity_all_odd",
        "parity_all_even",
        "zone_all_low_1_15",
        "zone_all_high_31_45",
        "consec_6",
        "arithmetic_6",
        "rank_top1000",
        "rank_bottom1000",
        "split_exact_123_434445",
        "consec_ge1_pair",
    ):
        meta = closed[tag]
        add(tag, int(meta["w"]), str(meta["method"]))

    for tag in ("consec_3plus", "consec_4plus", "consec_5plus", "spread_min_gap7", "spread_min_gap8"):
        meta = scanned.get(tag) or {}
        w = meta.get("w")
        method = scanned.get("method") or "skipped"
        add(tag, int(w) if w is not None else None, str(method))

    # odd_k full
    for k, w in closed["odd_k"]["w_by_k"].items():
        pe = emp["odd_k_emp"][str(k)]
        add(
            f"odd_k_{k}",
            int(w),
            "C(23,k)*C(22,6-k)",
            emp_n=pe["n"],
            emp_rate=pe["rate"],
        )
    return rows


def pmi_survey(draws: list[dict], *, top_k: int = 30) -> dict[str, Any]:
    n = len(draws)
    single = Counter()
    pair = Counter()
    for d in draws:
        nums = d["nums"]
        for a in nums:
            single[a] += 1
        for a, b in combinations(nums, 2):
            pair[(a, b)] += 1

    pmi_rows = []
    for (a, b), c_ab in pair.items():
        p_ab = c_ab / n
        p_a = single[a] / n
        p_b = single[b] / n
        if p_a <= 0 or p_b <= 0 or p_ab <= 0:
            continue
        pmi = math.log(p_ab / (p_a * p_b))
        pmi_rows.append(
            {
                "a": a,
                "b": b,
                "n_co": c_ab,
                "p_ab": round(p_ab, 6),
                "pmi": round(pmi, 6),
            }
        )
    pmi_rows.sort(key=lambda r: -r["pmi"])
    neg = sorted(pmi_rows, key=lambda r: r["pmi"])
    # set-level: mean PMI of actual historical draws
    set_scores = []
    pmi_map = {(r["a"], r["b"]): r["pmi"] for r in pmi_rows}
    for d in draws:
        vals = []
        for a, b in combinations(d["nums"], 2):
            vals.append(pmi_map.get((a, b), 0.0))
        set_scores.append(mean_or_0(vals))
    return {
        "n_draws": n,
        "n_pair_types_seen": len(pair),
        "n_pair_universe": math.comb(45, 2),
        "top_pmi": pmi_rows[:top_k],
        "bottom_pmi": neg[:top_k],
        "set_pmi_hist": {
            "mean": round(mean_or_0(set_scores), 6),
            "min": round(min(set_scores), 6) if set_scores else None,
            "max": round(max(set_scores), 6) if set_scores else None,
            "p10": round(percentile(set_scores, 0.10), 6),
            "p50": round(percentile(set_scores, 0.50), 6),
            "p90": round(percentile(set_scores, 0.90), 6),
        },
        "note": "as_of 없음 · 전체 1~1235 일괄 PMI(진단). 발권 wire 시에는 draw<target만.",
    }


def mean_or_0(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def percentile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    i = int(round(q * (len(s) - 1)))
    return s[max(0, min(len(s) - 1, i))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--skip-exact-w",
        action="store_true",
        help="skip full 8.14M scan for consec_3plus etc.",
    )
    args = ap.parse_args()

    print("load draws 1..1235…", flush=True)
    draws = load_draws()
    print(f"  n={len(draws)}", flush=True)

    closed = closed_form_w()
    print("L1 closed-form w…", flush=True)
    print(
        f"L1 universe scan (skip={args.skip_exact_w})…",
        flush=True,
    )
    scanned = scan_universe_runs(skip=args.skip_exact_w)
    emp = empirical_l1(draws)
    l1_rows = deviation_table(emp, closed, scanned)

    print("L3 PMI survey…", flush=True)
    pmi = pmi_survey(draws)

    scoring_schema = {
        "id": "signal_light_v1",
        "formula": (
            "score(set)=w1*deviation_score + w2*ema_divergence"
            " + w3*pmi_score + w4*(-popularity_penalty)"
        ),
        "weights_init": {"w1": 0, "w2": 0, "w3": 0, "w4": 0},
        "layers": {
            "L1": "deviation_score from template emp vs theory",
            "L2": "EMA multi-half-life — design only this turn",
            "L3": "set_pmi_score = mean PMI of pairs in set",
            "L4": "popularity_penalty (birthday/sum/consec)",
            "L5": "CUSUM regime — design only · separate GO",
        },
        "wire": False,
        "quota": "unchanged",
        "insert": "after brain set gen · before/parallel referee (GO later)",
    }

    l4_spec = {
        "purpose": "공유당첨 회피 EV · 당첨P 부스트 아님",
        "penalties": [
            {
                "id": "birthday_bias",
                "rule": "count(num<=31)/6 >= 4/6 → penalty += 1",
                "emp_rate_1_1235": emp["l4_proxy_emp"]["birthday_le31_ge4"]["rate"],
            },
            {
                "id": "sum_low_iqr",
                "rule": "sum(nums) <= 120 → penalty += 1 (IQR low proxy · refine later)",
                "emp_rate_1_1235": emp["l4_proxy_emp"]["sum_le_120"]["rate"],
                "note": "이론 합 mean≈138 · 120은 하측 근사 임계",
            },
            {
                "id": "consec_3plus",
                "rule": "max_run>=3 → penalty += 0.5 (tag already exists)",
                "emp_rate_1_1235": (emp["pattern_emp"].get("consec_3plus") or {}).get(
                    "rate"
                ),
            },
        ],
        "popularity_penalty": "sum of above · wire OFF · score only",
        "wire": False,
    }

    payload = {
        "id": "K-SIGNAL-TAXONOMY-V1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": "DOC_SURVEY",
        "wire": False,
        "C_45_6": C45_6,
        "draw_range": [1, 1235],
        "n_draws": len(draws),
        "problem": {
            "fusion_ge3_ref": 0.135,
            "stat_solo_ge3_ref": 0.165,
            "note": "fusion이 뇌별 우세 수치를 흡수 못함 · 신호 종류 부족",
        },
        "L1_deviation_table": l1_rows,
        "L1_scan_meta": {"skipped": scanned.get("skipped"), "method": scanned.get("method")},
        "L3_pmi": pmi,
        "L4_popularity_spec": l4_spec,
        "L2_L5_design_only": {
            "L2": "EMA H=8/26/78 parallel ranks · markov aux · quota untouched",
            "L5": "CUSUM regime · separate GO",
        },
        "scoring_schema": scoring_schema,
        "forbid": [
            "random.choices",
            "_get_draws_before mutate",
            "engine.py",
            "auto-tune",
            "quota change",
            "policy wire",
        ],
        "pass": True,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-SIGNAL-TAXONOMY-V1",
        "",
        f"📅 {payload['ts'][:10]} · **DOC_SURVEY** · wire=**False** · n={len(draws)}",
        "",
        "## 문제 인식",
        "",
        "- fusion ge3 정체 **0.135** · stat 단독 **0.165**가 fusion에 미반영",
        "- 신호 종류 부족 → L1~L5 진단층 먼저",
        "",
        "## L1 — 이론빈도 vs 실측 (deviation_score)",
        "",
        "| tag | w | p_theory | emp_rate | expected_n | deviation |",
        "|-----|--:|---------:|---------:|-----------:|----------:|",
    ]
    for r in l1_rows:
        if r["tag"].startswith("odd_k_"):
            continue  # summarize separately
        lines.append(
            f"| `{r['tag']}` | {r['w']} | {r['p_theory']} | {r['emp_rate']} | "
            f"{r['expected_n']} | {r['deviation_score']} |"
        )
    lines.extend(["", "### odd=k", ""])
    for r in l1_rows:
        if r["tag"].startswith("odd_k_"):
            lines.append(
                f"- {r['tag']}: emp={r['emp_rate']} th={r['p_theory']} "
                f"dev={r['deviation_score']} (n={r['emp_n']})"
            )
    if scanned.get("skipped"):
        lines.append(
            "\n> consec_3plus 등 exact w는 `--skip-exact-w`로 생략됨. "
            "재실행: `python tools/_k_signal_taxonomy_v1_survey.py`\n"
        )
    lines.extend(
        [
            "",
            "## L3 — PMI 공출현",
            "",
            f"- pair types seen = **{pmi['n_pair_types_seen']}** / {pmi['n_pair_universe']}",
            f"- historical set_pmi mean/p50/p90 = "
            f"**{pmi['set_pmi_hist']['mean']}** / {pmi['set_pmi_hist']['p50']} / "
            f"{pmi['set_pmi_hist']['p90']}",
            "",
            "### top PMI pairs",
            "",
        ]
    )
    for r in pmi["top_pmi"][:12]:
        lines.append(
            f"- ({r['a']},{r['b']}) n={r['n_co']} pmi=**{r['pmi']}**"
        )
    lines.extend(
        [
            "",
            "## L4 — 인기 페널티 스펙 (문서)",
            "",
            f"- birthday ≤31 ≥4/6 emp_rate = **{l4_spec['penalties'][0]['emp_rate_1_1235']}**",
            f"- sum≤120 emp_rate = **{l4_spec['penalties'][1]['emp_rate_1_1235']}**",
            f"- consec_3plus emp_rate = **{l4_spec['penalties'][2]['emp_rate_1_1235']}**",
            "- wire OFF · EV/공유 목적 · 당첨P↑ 클레임 금지",
            "",
            "## 신호등 통합 스코어 스키마",
            "",
            f"- `{scoring_schema['formula']}`",
            "- 모든 w 초기값 **0** (진단만)",
            "- quota / 발권 / engine.py 미수정",
            "",
            "## L2·L5 (이번 턴 설계만)",
            "",
            "- L2: EMA H=8/26/78 · markov 보조 스코어 (별도 구현 GO)",
            "- L5: CUSUM regime (별도 GO)",
            "",
            f"근거: `{OUT_JSON.name}`",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "pass": True,
                "l1_rows": len(l1_rows),
                "scan_skipped": scanned.get("skipped"),
                "pmi_top1": pmi["top_pmi"][0] if pmi["top_pmi"] else None,
                "out": OUT_JSON.name,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
