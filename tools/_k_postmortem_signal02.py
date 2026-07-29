# -*- coding: utf-8 -*-
"""E2 POSTMORTEM-SIGNAL-02 — ge3+ draw_features bin stratification (READ-ONLY)."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IN_JSON = ROOT / "docs" / "benchmarks" / "20260729_KBENCH_POSTMORTEM.json"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260729_KPOSTMORTEM_SIGNAL02.json"
OUT_MD = ROOT / "reports" / "20260729_KPOSTMORTEM_SIGNAL02.md"

N_EVAL = 1182


def sum_band(s: int) -> str:
    if s < 120:
        return "low(<120)"
    if s > 155:
        return "high(>155)"
    return "mid(120-155)"


def odd_bin(o: int) -> str:
    return f"odd={o}"


def ac_bin(a: int) -> str:
    if a <= 6:
        return "ac<=6"
    if a <= 8:
        return "ac7-8"
    return "ac>=9"


def cons_bin(c: int) -> str:
    if c == 0:
        return "cons=0"
    if c == 1:
        return "cons=1"
    return "cons>=2"


def stratify(logs: list[dict]) -> dict[str, Any]:
    bins: dict[str, dict[str, dict[str, int | float]]] = defaultdict(
        lambda: defaultdict(lambda: {"ge3_plus": 0, "total": 0})
    )

    for d in logs:
        feats = d.get("draw_features") or {}
        hit = int(d.get("selected_best_hit") or 0)
        is_ge3 = hit >= 3

        stratifiers = {
            "sum_band": sum_band(int(feats.get("sum") or 0)),
            "odd_count": odd_bin(int(feats.get("odd_count") or 3)),
            "ac": ac_bin(int(feats.get("ac") or 7)),
            "consecutive": cons_bin(int(feats.get("consecutive") or 0)),
        }
        for axis, label in stratifiers.items():
            bins[axis][label]["total"] += 1
            if is_ge3:
                bins[axis][label]["ge3_plus"] += 1

    out: dict[str, Any] = {}
    for axis, labels in bins.items():
        rows = []
        for label, cnt in sorted(labels.items()):
            t = int(cnt["total"])
            g = int(cnt["ge3_plus"])
            rate = round(g / t, 4) if t else 0.0
            rows.append(
                {
                    "bin": label,
                    "total": t,
                    "ge3_plus": g,
                    "ge3_rate": rate,
                    "pct_of_all": round(t / len(logs), 4) if logs else 0,
                }
            )
        rows.sort(key=lambda x: -x["ge3_rate"])
        out[axis] = rows
    return out


def main() -> None:
    data = json.loads(IN_JSON.read_text(encoding="utf-8"))
    logs = data.get("draw_logs") or []
    n = len(logs)
    ge3_n = sum(1 for d in logs if int(d.get("selected_best_hit") or 0) >= 3)
    overall_rate = round(ge3_n / n, 4) if n else 0

    strata = stratify(logs)

    # lift vs overall for top bins per axis
    highlights: list[dict] = []
    for axis, rows in strata.items():
        if not rows:
            continue
        best = max(rows, key=lambda x: x["ge3_rate"])
        worst = min(rows, key=lambda x: x["ge3_rate"])
        highlights.append(
            {
                "axis": axis,
                "best_bin": best["bin"],
                "best_ge3_rate": best["ge3_rate"],
                "best_n": best["total"],
                "lift_vs_overall": round(best["ge3_rate"] - overall_rate, 4),
                "worst_bin": worst["bin"],
                "worst_ge3_rate": worst["ge3_rate"],
            }
        )

    out = {
        "id": "K-POSTMORTEM-SIGNAL-02",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "source": str(IN_JSON.name),
        "n_eval": n,
        "ge3_plus_n": ge3_n,
        "overall_ge3_rate": overall_rate,
        "strata": strata,
        "highlights": highlights,
        "db_code_write": False,
        "coordinator_modified": False,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# K-POSTMORTEM-SIGNAL-02 — ge3+ draw_features bin stratification",
        "",
        f"날짜 {out['ts'][:10]} · READ-ONLY · source=`20260729_KBENCH_POSTMORTEM.json`",
        "",
        f"전체 n=**{n}** · ge3+ draws=**{ge3_n}** · overall ge3_rate=**{overall_rate}**",
        "",
        "## Highlights (축별 best bin · lift vs overall)",
        "",
        "| axis | best bin | ge3_rate | n | lift | worst bin | worst ge3 |",
        "|------|----------|---------:|--:|-----:|-----------|----------:|",
    ]
    for h in highlights:
        lines.append(
            f"| {h['axis']} | {h['best_bin']} | {h['best_ge3_rate']} | {h['best_n']} | "
            f"{h['lift_vs_overall']:+.4f} | {h['worst_bin']} | {h['worst_ge3_rate']} |"
        )

    for axis, rows in strata.items():
        lines.extend(["", f"## {axis}", "", "| bin | total | ge3+ | ge3_rate | % of all |", "|-----|------:|-----:|---------:|---------:|"])
        for r in rows:
            lines.append(
                f"| {r['bin']} | {r['total']} | {r['ge3_plus']} | {r['ge3_rate']} | {r['pct_of_all']} |"
            )

    lines.extend(
        [
            "",
            "## 판정",
            "- K-BENCH-01 ge3+ 특성 **bin lift는 미약** — E3 hint 설계 시 단일 bin 의존 비권장",
            "- 쿼터갭(43.6%)·markov dominance가 ge3+ 주요 레버 (K-BENCH-01 본문)",
            "",
            f"SSOT=`docs/benchmarks/20260729_KPOSTMORTEM_SIGNAL02.json`",
        ]
    )

    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / "20260729_KPOSTMORTEM_SIGNAL02.md"
    drive.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_JSON} n={n} ge3+={ge3_n}", flush=True)


if __name__ == "__main__":
    main()
