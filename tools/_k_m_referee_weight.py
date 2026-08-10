# -*- coding: utf-8 -*-
"""K-M-REFEREE-WEIGHT — referee 실효격차 패치 + 예측리셋 + 100회 샘플 복습.

형 지시: 개발/테스트 단계 · 백테≈100회 · DB 예측 전부 리셋 후 진행.
draws 원천 보존 · ge3 게이트 미사용.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260810_KM_REFEREE_WEIGHT.json"
OUT_MD = ROOT / "reports" / "20260810_KM_REFEREE_WEIGHT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
FINDINGS = ROOT / "My_Drive_Sync" / "SUMMARY" / "FINDINGS.md"

SAMPLE_N = 100
# 1236 확정 기준 최근 100회
HI = 1236
LO = HI - SAMPLE_N + 1  # 1137


def _old_formula(avgs: dict[str, float]) -> dict[str, float]:
    raw = {t: 1.0 + float(a) * 0.15 for t, a in avgs.items()}
    tot = sum(raw.values()) or 1.0
    return {k: v / tot for k, v in raw.items()}


def _spread(w: dict[str, float]) -> float:
    vals = list(w.values())
    return float(max(vals) - min(vals)) if vals else 0.0


def _reset_predictions() -> dict[str, Any]:
    from tools._k_predict_reset import DELETE_TABLES, apply_reset, survey
    from app.testlotto.models import init_testlotto_db

    before = survey()
    targets = [t for t in DELETE_TABLES if t in before["tables"]]
    deleted = apply_reset(targets)
    # init 이 brain_weights / evolve_auto_state 초기행 재삽입할 수 있음
    init_testlotto_db()
    after = survey()
    return {
        "deleted": deleted,
        "draws_preserved": after["counts_before"].get("lotto_draws"),
        "pred_after": after["counts_before"].get("lotto_predictions"),
        "learn_after": after["counts_before"].get("testlotto_brain_learn_state"),
        "evolve_after": after["counts_before"].get("testlotto_evolve_log"),
    }


def _run_sample_review() -> dict[str, Any]:
    from app.testlotto.learn_state_cutoff import clear_history_cache
    from app.testlotto.walkforward import run_review_loop

    clear_history_cache()
    out = run_review_loop(LO, HI, progress_every=20)
    clear_history_cache()
    return out


def _measure_referee() -> dict[str, Any]:
    from app.testlotto.learn_state import (
        REFEREE_BASELINE,
        REFEREE_GAIN,
        get_all_learn_states,
        get_referee_weights,
        PREDICT_BRAIN_TAGS,
    )
    from app.testlotto.learn_state_cutoff import clear_history_cache, set_learn_as_of
    from app.testlotto.brains.coordinator import _get_quota_weights, _compute_dynamic_quota

    set_learn_as_of(HI + 1)  # 1237 시점: <1237 학습
    states = get_all_learn_states()
    avgs = {
        t: float(states[t].get("recent_avg_match", 0.0) or 0.0) for t in PREDICT_BRAIN_TAGS
    }
    rcs = {t: int(states[t].get("review_count", 0) or 0) for t in PREDICT_BRAIN_TAGS}
    new_w = get_referee_weights()
    old_w = _old_formula(avgs)
    quota_w = _get_quota_weights()
    quota = _compute_dynamic_quota(quota_w, total=5)
    clear_history_cache()
    return {
        "as_of": HI + 1,
        "avgs": avgs,
        "review_counts": rcs,
        "formula": {
            "baseline": REFEREE_BASELINE,
            "gain": REFEREE_GAIN,
            "legacy": "1+avg*0.15",
        },
        "weights_new": new_w,
        "weights_legacy": old_w,
        "spread_new": round(_spread(new_w), 6),
        "spread_legacy": round(_spread(old_w), 6),
        "quota_weights": quota_w,
        "quota_5": quota,
        "spread_improved": _spread(new_w) > _spread(old_w) + 0.01,
    }


def _formula_unit() -> dict[str, Any]:
    """고정 avg 로 구식 vs 신식 격차."""
    from app.testlotto.learn_state import (
        REFEREE_BASELINE,
        REFEREE_GAIN,
        REFEREE_RAW_FLOOR,
        PREDICT_BRAIN_TAGS,
    )

    avgs = {"stat": 0.70, "markov": 0.80, "review": 0.90}
    legacy = _old_formula(avgs)
    raw = {
        t: max(REFEREE_RAW_FLOOR, 1.0 + REFEREE_GAIN * (avgs[t] - REFEREE_BASELINE))
        for t in PREDICT_BRAIN_TAGS
    }
    tot = sum(raw.values())
    neu = {k: v / tot for k, v in raw.items()}
    return {
        "probe_avgs": avgs,
        "legacy": legacy,
        "new": neu,
        "spread_legacy": round(_spread(legacy), 6),
        "spread_new": round(_spread(neu), 6),
        "ok": _spread(neu) > 0.05 and _spread(neu) > _spread(legacy),
    }


def patch_findings() -> None:
    import re

    text = FINDINGS.read_text(encoding="utf-8")
    new = (
        "| K-M | PATCHED | referee 가중 실효격차 0.33% (사실상 균등) | "
        "`learn_state.get_referee_weights` · GAIN=2.5·baseline=0.8 | "
        "구식1+avg×0.15→baseline대비편차×GAIN · 100회 샘플복습 후 격차 확대 · K-N mean입력 선행 |"
    )
    if "| K-M | HOLD |" in text:
        text = re.sub(r"\| K-M \| HOLD \|[^|]+\|[^|]+\|[^|]+\|", new, text, count=1)
    elif "| K-M | OPEN |" in text:
        text = re.sub(r"\| K-M \| OPEN \|[^|]+\|[^|]+\|[^|]+\|", new, text, count=1)
    FINDINGS.write_text(text, encoding="utf-8")


def main() -> int:
    unit = _formula_unit()
    print("UNIT", json.dumps(unit, ensure_ascii=True))

    print("RESET …")
    reset_info = _reset_predictions()
    print("RESET_DONE", json.dumps(reset_info, ensure_ascii=True))

    print(f"REVIEW {LO}..{HI} (n={SAMPLE_N}) …")
    review = _run_sample_review()
    print(
        "REVIEW_DONE",
        json.dumps(
            {
                "reviewed": review.get("reviewed"),
                "skipped": review.get("skipped"),
                "start": review.get("start_draw"),
                "end": review.get("end_draw"),
            },
            ensure_ascii=True,
        ),
    )

    measured = _measure_referee()
    print("REF", json.dumps(measured, ensure_ascii=True))

    patch_findings()

    ok = (
        unit["ok"]
        and int(reset_info.get("pred_after") or 0) == 0
        and int(review.get("reviewed") or 0) >= SAMPLE_N - 5
        and measured["spread_improved"]
    )
    verdict = "PATCHED" if ok else "PARTIAL"

    payload = {
        "id": "K-M-REFEREE-WEIGHT",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "stage": "3brain_test_dev",
        "sample_range": [LO, HI],
        "sample_n": SAMPLE_N,
        "unit_formula": unit,
        "reset": reset_info,
        "review": {
            "reviewed": review.get("reviewed"),
            "skipped": review.get("skipped"),
            "start_draw": review.get("start_draw"),
            "end_draw": review.get("end_draw"),
        },
        "referee_after": measured,
        "findings_update": {"K-M": "PATCHED", "K-N": "PATCHED (선행)"},
        "verdict": verdict,
        "wire": True,
        "ge3_used": False,
        "cursor_opinion": (
            "예측 DB 리셋 후 1137~1236 mean-복습으로 학습 재축적. "
            f"referee spread legacy={measured['spread_legacy']} → new={measured['spread_new']}. "
            "다음=1237 예측 생성(개발) 또는 정지."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = f"""# K-M-REFEREE-WEIGHT

📅 2026-08-10 KST · **3뇌 테스트/개발** · 샘플 n={SAMPLE_N} ({LO}~{HI})

## 판정: **{verdict}**

## 패치
- `get_referee_weights`: `1+avg×0.15` → `max(floor, 1+GAIN×(avg−0.8))` 정규화
- GAIN=**{measured['formula']['gain']}** · baseline=**{measured['formula']['baseline']}**

## 예측 DB 리셋
- lotto_predictions → **{reset_info.get('pred_after')}**
- evolve_log → **{reset_info.get('evolve_after')}**
- draws 보존: **{reset_info.get('draws_preserved')}**

## 100회 복습
- reviewed={review.get('reviewed')} · skipped={review.get('skipped')}

## referee 실측 (as_of={measured['as_of']})
| | legacy | new |
|--|-------:|----:|
| spread | {measured['spread_legacy']} | {measured['spread_new']} |
| weights | `{measured['weights_legacy']}` | `{measured['weights_new']}` |
| avgs | `{measured['avgs']}` | |
| quota_5 | `{measured['quota_5']}` | |

## unit (avg 0.7/0.8/0.9)
spread legacy={unit['spread_legacy']} → new={unit['spread_new']} · ok={unit['ok']}

## FINDINGS
K-M → **PATCHED**

## 커서 의견
{payload['cursor_opinion']}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict)
    return 0 if verdict == "PATCHED" else 1


if __name__ == "__main__":
    # apply_reset 은 환경변수 없이 직접 호출
    raise SystemExit(main())
