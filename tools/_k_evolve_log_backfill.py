# -*- coding: utf-8 -*-
"""K-EVOLVE-LOG Phase1 — pool 캐시 백필 + 벤치 JSON/보고서.

Usage:
  python tools/_k_evolve_log_backfill.py
  python tools/_k_evolve_log_backfill.py --start 1035 --end 1234
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KEVOLVE_LOG.json"
OUT_MD = ROOT / "reports" / "20260804_KEVOLVE_LOG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1035)
    ap.add_argument("--end", type=int, default=1234)
    ap.add_argument("--sample-draw", type=int, default=1200)
    args = ap.parse_args()

    from app.testlotto.evolve_log import (
        WEIGHT_APPLIED,
        backfill_from_pool_cache,
        get_evolve_log,
    )
    from app.testlotto.models import init_testlotto_db

    init_testlotto_db()
    print(f"K-EVOLVE-LOG backfill {args.start}~{args.end} ...", flush=True)
    result = backfill_from_pool_cache(args.start, args.end)
    sample = get_evolve_log(args.sample_draw)

    payload = {
        "id": "K-EVOLVE-LOG",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "phase": 1,
        "weight_applied": WEIGHT_APPLIED,
        "wire_to_predict": False,
        "draw_range": [args.start, args.end],
        "backfill": {
            "filled_draws": result["filled_draws"],
            "missing_cache": result["missing_cache"],
        },
        "summary": result["summary"],
        "sample_draw": args.sample_draw,
        "sample_ok": bool(sample and sample.get("ok")),
        "sample_brains": list((sample or {}).get("brains") or {}.keys()),
        "api": {
            "log": "/api/testlotto/evolve/log/{draw_no}",
            "summary": f"/api/testlotto/evolve/summary?start={args.start}&end={args.end}",
        },
        "forbid": [
            "apply_feedback_change",
            "W_HINT_tune",
            "quota_change",
            "best_as_learn_input",
        ],
        "pass": result["filled_draws"] > 0 and WEIGHT_APPLIED == 0.0,
    }

    # API path prefix - check how routes are mounted
    lines = [
        "# K-EVOLVE-LOG — Phase1 회차 진화 로그 (가중 0)",
        "",
        f"`{payload['ts']}` · {args.start}~{args.end} · **wire 없음 · weight={WEIGHT_APPLIED}**",
        "",
        "## 0. 한 줄",
        "",
        f"pool_view 캐시→`testlotto_evolve_log` 백필 **{result['filled_draws']}**회차 · "
        f"캐시 miss **{result['missing_cache']}** · 학습 가중 **0** · "
        f"PASS=**{payload['pass']}**",
        "",
        "## 1. 뇌별 요약 (발권 repack best_of_5 참고)",
        "",
        "| 뇌 | n | ge3_rate | avg_best | avg_mean |",
        "|----|---|---------:|---------:|---------:|",
    ]
    for tag, s in (result["summary"].get("by_brain") or {}).items():
        lines.append(
            f"| {tag} | {s['n']} | **{s['ge3_rate']:.4f}** | {s['avg_best_hits']} | {s['avg_mean_hits']} |"
        )
    lines.extend(
        [
            "",
            "> ge3/best는 **참고 지표**. Phase1에서 학습 입력으로 쓰지 않음 (K-N).",
            "",
            "## 2. 저장 내용",
            "",
            "- pool 10 + repack 5 nums/hits",
            "- features: sum·parity·zone·max_run·span (발권 평균 + best 세트)",
            "- miss_tags: carry_over / overdue / ending_digit",
            "- assemble_mode · weight_applied=0 · as_of=draw_no",
            "",
            "## 3. 조회 API",
            "",
            f"- `GET .../evolve/log/{{draw_no}}` · sample {args.sample_draw} ok={payload['sample_ok']}",
            f"- `GET .../evolve/summary?start={args.start}&end={args.end}`",
            "",
            "## 4. 다음 (Phase2 · 형 GO)",
            "",
            "- `K-EVOLVE-SIGNAL` — best학습 차단 + 구조신호 λ survey",
            "- 이번 패치: predict/W_*/quota/coordinator **미수정**",
            "",
            "## 금지 준수",
            "",
            "동결 3종 · kweon · FINDINGS 무단 · FAIL→auto-tune · best→실력 학습",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print("pass=", payload["pass"], "sample=", payload["sample_ok"])


if __name__ == "__main__":
    main()
