# -*- coding: utf-8 -*-
"""K-EXCLUDE-HIST-01 — 1~1234 당첨번호 패턴 catalog (배제 준비 · READ-ONLY).

WF as_of 정책: 전체 catalog는 「1235 예측용 as_of=1235」 참고용.
백테 T회에는 draws < T 만 사용해야 함 (LEAKAGE_POLICY.md).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260730_KEXCLUDE_HIST_survey.json"
OUT_MD = ROOT / "reports" / "20260730_KEXCLUDE_HIST_SURVEY.md"
DB = ROOT / "data" / "lotto_testlotto.db"


def _max_consecutive_run(nums: list[int]) -> int:
    s = sorted(nums)
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def _zone(n: int) -> str:
    if n <= 15:
        return "low"
    if n <= 30:
        return "mid"
    return "high"


def _load_draws() -> list[dict]:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT draw_no, draw_date, num1,num2,num3,num4,num5,num6, bonus "
        "FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        nums = [int(r[f"num{k}"]) for k in range(1, 7)]
        out.append(
            {
                "draw_no": int(r["draw_no"]),
                "draw_date": r["draw_date"],
                "nums": nums,
                "bonus": int(r["bonus"]),
                "sum": sum(nums),
                "odd": sum(1 for x in nums if x % 2),
                "max_run": _max_consecutive_run(nums),
                "zones": Counter(_zone(x) for x in nums),
            }
        )
    return out


def _run_analysis(draws: list[dict]) -> dict:
    n = len(draws)
    run_dist = Counter(d["max_run"] for d in draws)
    sum_vals = [d["sum"] for d in draws]
    odd_dist = Counter(d["odd"] for d in draws)
    zone_low = sum(1 for d in draws if d["zones"]["low"] >= 4)
    zone_high = sum(1 for d in draws if d["zones"]["high"] >= 4)

    # pair co-occurrence top (1st prize combos only)
    pair_cnt: Counter = Counter()
    for d in draws:
        nums = sorted(d["nums"])
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair_cnt[(nums[i], nums[j])] += 1

    rare_pairs = [(p, c) for p, c in pair_cnt.items() if c == 1]
    common_pairs = pair_cnt.most_common(10)

    # exclusion risk notes
    exclude_notes = []
    pct_pair = 100 * (n - run_dist.get(1, 0)) / n
    exclude_notes.append(
        {
            "pattern": "2연속_이상_포함",
            "draws": n - run_dist.get(1, 0),
            "pct": round(pct_pair, 2),
            "risk": "high" if pct_pair > 40 else "medium",
            "note": "2연속 전부 배제 시 역사 당첨의 상당 부분 형태 제거",
        }
    )
    exclude_notes.append(
        {
            "pattern": "3연속_이상",
            "draws": sum(run_dist.get(k, 0) for k in run_dist if k >= 3),
            "pct": round(100 * sum(run_dist.get(k, 0) for k in run_dist if k >= 3) / n, 2),
            "risk": "medium",
            "note": "3연속+ 배제는 표본 적지만 당첨 사례 존재",
        }
    )
    exclude_notes.append(
        {
            "pattern": "4연속_이상",
            "draws": sum(run_dist.get(k, 0) for k in run_dist if k >= 4),
            "pct": round(100 * sum(run_dist.get(k, 0) for k in run_dist if k >= 4) / n, 2),
            "risk": "low",
            "note": "희귀 tail · 배제 후보(λ sweep 필요)",
        }
    )

    # per-draw samples for consecutive >=3
    samples_run3 = [
        {"draw_no": d["draw_no"], "nums": d["nums"], "max_run": d["max_run"]}
        for d in draws
        if d["max_run"] >= 3
    ][:15]

    return {
        "n_draws": n,
        "draw_range": [draws[0]["draw_no"], draws[-1]["draw_no"]],
        "consecutive_max_run": {str(k): v for k, v in sorted(run_dist.items())},
        "has_2plus_consecutive_pct": round(pct_pair, 2),
        "sum_stats": {
            "min": min(sum_vals),
            "max": max(sum_vals),
            "mean": round(mean(sum_vals), 1),
            "median": median(sum_vals),
            "p05": sorted(sum_vals)[int(n * 0.05)],
            "p95": sorted(sum_vals)[int(n * 0.95)],
        },
        "odd_count_dist": {str(k): v for k, v in sorted(odd_dist.items())},
        "zone_skew_4plus_low": zone_low,
        "zone_skew_4plus_high": zone_high,
        "pair_never_repeat_count": len(rare_pairs),
        "pair_top10": [{"pair": list(p), "count": c} for p, c in common_pairs],
        "exclude_risk_notes": exclude_notes,
        "samples_max_run_ge3": samples_run3,
        "leakage_policy": "catalog_as_of_1235_ok · backtest_T_use_draws_lt_T_only",
    }


def _write_md(payload: dict) -> None:
    a = payload["analysis"]
    lines = [
        "# K-EXCLUDE-HIST-01 — 당첨 패턴 catalog (배제 준비)",
        "",
        f"날짜 {payload['ts'][:10]} · **READ-ONLY** · n={a['n_draws']} · {a['draw_range'][0]}~{a['draw_range'][1]}회",
        "",
        "## 1. 숙제",
        "",
        "| 항목 | 내용 |",
        "|------|------|",
        "| **질문** | 1~1234 1등 당첨 6개 패턴 · 배제 후보 tail |",
        "| **누수** | 1235 예측=1~1234 OK · 1120 백테=1119까지만 |",
        "",
        "## 2. 연속 번호 (붙은 번호)",
        "",
        "| 최장 연속 | 회차 수 |",
        "|-----------|--------:|",
    ]
    for k, v in sorted(a["consecutive_max_run"].items(), key=lambda x: int(x[0])):
        label = "연속 없음" if k == "1" else f"{k}연속"
        lines.append(f"| {label} | {v} |")
    lines.append(f"\n**2연속 이상 포함:** {a['has_2plus_consecutive_pct']}%")
    lines.append("\n## 3. 합·홀짝")
    ss = a["sum_stats"]
    lines.append(f"- 합: min={ss['min']} max={ss['max']} mean={ss['mean']} p05={ss['p05']} p95={ss['p95']}")
    lines.append(f"- 홀짝 분포: `{a['odd_count_dist']}`")
    lines.append("\n## 4. 배제 위험 (과배제 주의)")
    lines.append("| 패턴 | 회차 | % | 위험 |")
    lines.append("|------|-----:|--:|------|")
    for n in a["exclude_risk_notes"]:
        lines.append(f"| {n['pattern']} | {n['draws']} | {n['pct']} | {n['risk']} |")
    lines.append("\n## 5. 3연속+ 샘플 (최대 15건)")
    for s in a["samples_max_run_ge3"]:
        lines.append(f"- {s['draw_no']}회: {s['nums']} (max_run={s['max_run']})")
    lines.append("\n## 6. 다음")
    lines.append("- K-EXCLUDE-SURVEY: combined + 배제 ON/OFF · λ sweep")
    lines.append(f"\n*JSON:* `{OUT_JSON}`")
    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
    drive.write_text(text, encoding="utf-8")


def main() -> None:
    draws = _load_draws()
    analysis = _run_analysis(draws)
    payload = {
        "id": "K-EXCLUDE-HIST-01",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "analysis": analysis,
        "note": "1등 당첨 6+보너스만 · 2~3등 조합 원본 없음 · 5등은 백테로 보조",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_md(payload)
    print(f"wrote {OUT_JSON}", flush=True)
    print(f"wrote {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()
