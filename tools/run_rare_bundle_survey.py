# -*- coding: utf-8 -*-
"""K-RARE-BUNDLE — 814만(C(45,6)) 극소 확률 번들 catalog → DB 저장.

예: 1-2-3-4-5-6 · 39-40-41-42-43-44 · 1·2·3+43·44·45 분할 등
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260803_KRARE_BUNDLE_survey.json"
OUT_MD = ROOT / "reports" / "20260803_KRARE_BUNDLE_SURVEY.md"


def _write_md(payload: dict) -> None:
    s = payload["summary"]
    lines = [
        "# K-RARE-BUNDLE — 814만 극소 확률 번들 선별",
        "",
        f"날짜 {payload['ts'][:10]} · n_draws={payload['n_draws']} · catalog={payload['catalog_saved']}",
        "",
        "## 1. 배경",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        f"| **전체 조합** | C(45,6) = **8,145,060** (약 814만) |",
        f"| **개별 조합 확률** | 1 / 8,145,060 |",
        "| **참고** | arXiv:math/0507469 · MathDoctors · LotteryCodex |",
        "",
        "## 2. DB 저장",
        "",
        "| 테이블 | 건수 |",
        "|--------|-----:|",
        f"| `testlotto_rare_bundle_catalog` | {s['catalog_total']} |",
        f"| `testlotto_rare_bundle_hits` | {payload['hits_saved']} |",
        f"| 극소(is_ultra_rare) catalog | {s['catalog_ultra_rare']} |",
        f"| **미당첨 극소 번들** | {s['ultra_never_drawn']} |",
        f"| 역사 6연속 당첨 | {s['historical_consec_6']} |",
        "",
        "## 3. 극소스의 극소 (TOP 15)",
        "",
        "| 순위 | 패턴 | 번호 | 814만순위 | 희귀점수 | 당첨회차 |",
        "|-----:|------|------|----------:|---------:|---------:|",
    ]
    for i, row in enumerate(payload.get("top_ultra", [])[:15], 1):
        nums = json.loads(row["nums_json"]) if isinstance(row["nums_json"], str) else row["nums_json"]
        hist = row.get("historical_draw_no") or "—"
        lines.append(
            f"| {i} | {row['pattern_label']} | {nums} | {row['combo_rank_814']:,} | "
            f"{row['rarity_score']:.2f} | {hist} |"
        )
    lines.extend(
        [
            "",
            "## 4. API",
            "",
            "- `GET /api/testlotto/rare-bundles/summary`",
            "- `GET /api/testlotto/rare-bundles/ultra?limit=50`",
            "",
            f"*JSON:* `{OUT_JSON}`",
        ]
    )
    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")


def main() -> None:
    from app.testlotto.rare_bundle_store import run_full_survey

    result = run_full_survey()
    payload = {
        "id": "K-RARE-BUNDLE-01",
        "ts": datetime.now().isoformat(timespec="seconds"),
        **result,
        "refs": [
            "https://arxiv.org/abs/math/0507469",
            "https://www.themathdoctors.org/probability-of-consecutive-numbers-in-a-lottery/",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    # serialize top_ultra rows
    serializable = dict(payload)
    serializable["top_ultra"] = [
        {k: v for k, v in row.items()} for row in payload.get("top_ultra", [])
    ]
    OUT_JSON.write_text(json.dumps(serializable, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _write_md(payload)
    print(f"catalog={result['catalog_saved']} hits={result['hits_saved']}", flush=True)
    print(f"ultra={result['summary']['catalog_ultra_rare']} never_drawn={result['summary']['ultra_never_drawn']}", flush=True)
    print(f"wrote {OUT_JSON}", flush=True)
    print(f"wrote {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()
