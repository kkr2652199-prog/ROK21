# -*- coding: utf-8 -*-
"""K-SIGNAL tail-100 walk-forward backtest → JSON + DB + 한글 보고서.

- tail-100 (최근 완료 100회) · seed=42 · walk-forward
- combined + signal_repack per-draw DB 적재
- eval 구간 lotto_predictions(+pool-view 캐시)만 reset · backtest 테이블 유지
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.bench_quick_gate import (  # noqa: E402
    DRAW_END,
    MC_SEED,
    NULL_GE3,
    WIRE_PIN_GE3,
    WIRE_PIN_MEAN,
    resolve_eval_window,
)
from tools.import_k_signal_backtest import (  # noqa: E402
    _run_repack_per_draw,
    _run_select_per_draw,
)
from tools._k_signal_repack_survey import _reset_predictions_for_eval  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260730_KSIGNAL_BACKTEST_tail100.json"
OUT_MD = ROOT / "reports" / "20260730_BACKTEST_TAIL100.md"
SURVEY_ID = "K-SIGNAL-BACKTEST-TAIL100"
N_EVAL = 100


def _write_report(payload: dict, md_path: Path) -> None:
    runs = payload.get("runs") or []
    reset = payload.get("db_reset") or {}
    dr = payload.get("draw_range") or [0, 0]
    lines = [
        "# K-SIGNAL-BACKTEST-TAIL100 — 최근 100회 walk-forward 백테스트",
        "",
        f"날짜 {datetime.now().strftime('%Y-%m-%d')} · gate=**tail100** · seed=**{MC_SEED}**",
        "",
        "---",
        "",
        "## 1. 📋 선생님이 준 숙제",
        "",
        "| 항목 | 내용 |",
        "|------|------|",
        f"| **ID** | `{SURVEY_ID}` |",
        "| **질문** | 최근 100회에서 combined·signal_repack ge3/tier는? pin/null 대비? |",
        "| **PASS (참고)** | QUICK: ge3>null(0.1137) AND p<0.15 |",
        "| **금지** | coordinator wire · backtest 테이블 삭제 · 컨닝 |",
        "",
        "## 2. 🔧 학생이 한 일",
        "",
        "### DB reset (eval 구간만)",
        "",
        "```json",
        json.dumps(reset, ensure_ascii=False, indent=2),
        "```",
        "",
        "| 유지 | 삭제(범위内) |",
        "|------|-------------|",
        "| testlotto_backtest_runs · draw_results(기존 run) | lotto_predictions eval구간 |",
        f"| pool_view_cache(범위外) | pool_view_cache {dr[0]}~{dr[1]} |",
        "",
        "### 실행 파라미터",
        "",
        "| key | value |",
        "|-----|-------|",
        f"| n_eval | {N_EVAL} |",
        f"| draw_range | {dr[0]}–{dr[1]} |",
        "| sample_mode | tail |",
        f"| seed | {MC_SEED} |",
        f"| strategies | combined · signal_repack |",
        "",
        "## 3. 📊 풀이 (결과표)",
        "",
        "### SUMMARY",
        "",
        "| label | strategy | mean | ge3_rate | ge3_cnt | Δpin | p | verdict | run_id |",
        "|-------|----------|-----:|---------:|--------:|-----:|--:|---------|-------:|",
        f"| theory_baseline | — | 0.8000 | {NULL_GE3} | — | — | — | null | — |",
        f"| WIRE-V2 pin | stored | {WIRE_PIN_MEAN} | {WIRE_PIN_GE3} | — | — | — | pin | — |",
    ]
    for r in runs:
        m = r.get("metrics") or {}
        sid = r.get("strategy_id", "")
        lines.append(
            f"| **{sid}** | WF live | {m.get('mean', 0):.4f} | {m.get('ge3_rate', 0):.4f} "
            f"| {m.get('ge3_count', 0)} | {m.get('delta_ge3_vs_pin', 0):+.4f} "
            f"| {m.get('p_value', 1):.6f} | {m.get('verdict', '')} | {r.get('run_id', '')} |"
        )
    lines.extend(
        [
            "",
            "### tier 피벗 (run별)",
            "",
        ]
    )
    for r in runs:
        t = (r.get("metrics") or {}).get("tiers") or {}
        lines.append(
            f"- **{r.get('strategy_id')}** (run_id={r.get('run_id')}): "
            f"1등={t.get('r1', 0)} · 2등={t.get('r2', 0)} · 3등={t.get('r3', 0)} · "
            f"4등={t.get('r4', 0)} · 5등={t.get('r5', 0)}"
        )
    lines.extend(
        [
            "",
            "## 4. ✅ 맞은 것 / ❌ 틀린 것",
            "",
            "- walk-forward only · frozen 경로 미수정 · backtest 기록 append/replace(동 survey+strategy)",
            "- UI: 「🎯 3뇌 예측」 단일 버튼 SSOT",
            "",
            "## 5. 다음",
            "",
            "- K-SIGNAL-SELECT-FULL (1182) · wire=형 GO 전 금지",
            "",
            f"*JSON:* `{OUT_JSON.as_posix()}`",
        ]
    )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="K-SIGNAL tail-100 backtest")
    ap.add_argument("--n-eval", type=int, default=N_EVAL)
    ap.add_argument("--which", choices=["repack", "select", "both"], default="both")
    ap.add_argument("--skip-reset", action="store_true", help="eval reset 생략(디버그)")
    ap.add_argument("--output-json", type=str, default=str(OUT_JSON))
    ap.add_argument("--output-md", type=str, default=str(OUT_MD))
    args = ap.parse_args()

    eval_window = resolve_eval_window(args.n_eval, draw_end=DRAW_END, sample_mode="tail")
    t0 = time.time()
    json_path = Path(args.output_json)
    md_path = Path(args.output_md)

    db_reset: dict = {"skipped": True}
    if not args.skip_reset:
        db_reset = _reset_predictions_for_eval(
            eval_window.draw_start,
            eval_window.draw_end,
            clear_pool_view_cache=True,
        )

    payload: dict = {
        "id": SURVEY_ID,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "n_eval": args.n_eval,
        "draw_range": [eval_window.draw_start, eval_window.draw_end],
        "eval_window": {
            "n_eval_target": eval_window.n_eval_target,
            "sample_mode": eval_window.sample_mode,
            "quick_gate": eval_window.quick_gate,
        },
        "gate_mode": "tail100",
        "mc_seed": MC_SEED,
        "null_ge3": NULL_GE3,
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "db_reset": db_reset,
        "runs": [],
    }

    src_json = str(json_path.as_posix())
    if args.which in ("repack", "both"):
        print(f"{SURVEY_ID} signal_repack tail-{args.n_eval} WF...", flush=True)
        payload["runs"].append(
            _run_repack_per_draw(
                eval_window,
                survey_id=SURVEY_ID,
                gate_mode="tail100",
                source_json=src_json,
            )
        )

    if args.which in ("select", "both"):
        print(f"{SURVEY_ID} combined tail-{args.n_eval} WF...", flush=True)
        payload["runs"].append(
            _run_select_per_draw(
                eval_window,
                survey_id=SURVEY_ID,
                gate_mode="tail100",
                source_json=src_json,
            )
        )

    payload["elapsed_sec"] = round(time.time() - t0, 1)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(payload, md_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
    print(f"Wrote {json_path} · {md_path}", flush=True)


if __name__ == "__main__":
    main()
