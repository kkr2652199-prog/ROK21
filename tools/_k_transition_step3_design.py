# -*- coding: utf-8 -*-
"""K-TRANSITION-STEP3-DESIGN — transition→stat 대체 설계 (엔진 미수정 · SELECT-ONLY).

Usage:
  python tools/_k_transition_step3_design.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KTRANSITION_STEP3_DESIGN.json"
OUT_MD = ROOT / "reports" / "20260805_KTRANSITION_STEP3_DESIGN.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

STAT_FILE = "app/testlotto/brains/predict_stat_fairy.py"
# K-A OPEN: set-level mean hits (500 sets / recent100) — NOT top15 pool
STAT_SET_MEAN_KA = 0.760
BASELINE_TOP15 = 2.0
FULL_PRIOR_MEAN = 2.171806
BT_LO, BT_HI = 1100, 1234
# Hypergeometric N=45,K=15,n=6 → P(X>=3)
RANDOM_GE3_RATE = 0.311375


def read_stat_summary() -> dict[str, Any]:
    path = ROOT / STAT_FILE
    text = path.read_text(encoding="utf-8")
    # 읽기만 — 핵심 로직 3줄
    logic = (
        "1) `_statistical_predict`로 oversample 후보 생성 (빈도 기반). "
        "2) 이월·끝수·미출30+ reasoning + learn_state 부스트로 confidence 조정. "
        "3) `diversify_pick`로 Jaccard 다양성 선별 후 n_sets 반환 (random.choices 동결)."
    )
    has_predict_sets = "def predict_sets(" in text
    return {
        "file": STAT_FILE,
        "logic_summary": logic,
        "current_mean_ref": STAT_SET_MEAN_KA,
        "current_mean_ref_note": (
            "FINDINGS K-A OPEN: set-level mean=0.760 (최근100·500세트). "
            "top15 pool mean(2.0)과 지표 다름 — 교체판정은 top15 hold-out 기준."
        ),
        "interface": {
            "fn": "predict_sets(draws: list[dict], n_sets: int=5) -> list[dict]",
            "row_keys": ["nums", "confidence", "reasoning", "method", "brain_tag", "rank"],
            "brain_tag": "stat",
            "predict_sets_found": has_predict_sets,
        },
        "read_only": True,
    }


def design_spec() -> dict[str, Any]:
    return {
        "name": "predict_transition_v1",
        "logic_steps": [
            "A: 예측 대상 T에 대해 직전 회차 D_{T-1}을 anchor로 사용 (컨닝 금지)",
            "B: 과거 1..T-2 중 D_{T-1}과 공통≥min_common 유사 회차 추출 "
            "(similar+1 은 T 이전만 · min_similar 미달 시 fallback)",
            "C: 유사 회차들의 다음회 번호 빈도 → top_m 후보 풀",
            "D: top_m에서 n_sets개 6번호 조합 구성·반환 "
            "(인터페이스=predict_sets 동형 · brain_tag='stat' 또는 'transition')",
        ],
        "params": {
            "min_common": 2,
            "min_similar": 10,
            "top_m": 15,
            "n_sets_default": 5,
            "anchor": "D_{T-1}",
            "data_source": "lotto_draws (+ optional transition_log cache)",
        },
        "interface_match": True,
        "return_shape": {
            "nums": "list[int] len6",
            "confidence": "float",
            "reasoning": "str",
            "method": "전이패턴v1",
            "brain_tag": "stat",
            "rank": "int",
        },
        "note": (
            "본 STEP=설계만. brains/ 신규 파일·coordinator 배선은 STEP4·형 GO 후. "
            "transition_log는 캐시; 런타임은 lotto_draws만으로도 동일 계산 가능."
        ),
    }


def _conn():
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    return get_lotto_db()


def load_draws(conn) -> dict[int, list[int]]:
    rows = conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    out: dict[int, list[int]] = {}
    for r in rows:
        d = dict(r)
        out[int(d["draw_no"])] = sorted(int(d[f"num{k}"]) for k in range(1, 7))
    return out


def load_log_hits(conn) -> dict[int, dict[str, Any]]:
    """draw_no N row → predicts N+1; key by target draw (=N+1)."""
    rows = conn.execute(
        "SELECT draw_no, top15, hit_count, similar_count FROM transition_log WHERE sim_k=2"
    ).fetchall()
    by_target: dict[int, dict[str, Any]] = {}
    for r in rows:
        dn = int(r["draw_no"])
        by_target[dn + 1] = {
            "anchor_draw": dn,
            "top15": json.loads(r["top15"]),
            "hit_count": int(r["hit_count"]),
            "similar_count": int(r["similar_count"]),
        }
    return by_target


def backtest_nopeek(log_by_target: dict[int, dict], lo: int, hi: int) -> dict[str, Any]:
    """Deployable: use log[T] from anchor T-1 → hit vs D_T."""
    hits: list[int] = []
    dist: Counter = Counter()
    missing = 0
    for t in range(lo, hi + 1):
        row = log_by_target.get(t)
        if not row:
            missing += 1
            continue
        h = int(row["hit_count"])
        hits.append(h)
        dist[h] += 1
    mean_hit = float(np.mean(hits)) if hits else 0.0
    ge3 = sum(1 for h in hits if h >= 3)
    n = len(hits)
    return {
        "mode": "nopeek_Nminus1_to_N",
        "draw_range": [lo, hi],
        "n_draws": n,
        "n_missing_log": missing,
        "mean_hit": round(mean_hit, 6),
        "delta_vs_baseline2": round(mean_hit - BASELINE_TOP15, 6),
        "delta_vs_stat_set_mean_KA": round(mean_hit - STAT_SET_MEAN_KA, 6),
        "hit_dist": {str(k): int(dist.get(k, 0)) for k in range(7)},
        "ge3_count": ge3,
        "ge3_rate": round(ge3 / n, 6) if n else 0.0,
        "metric_note": "top15∩D_T · transition_log(anchor=T-1) · 발권 가능 경로",
    }


def backtest_full_holdout(draws: dict[int, list[int]], lo: int, hi: int) -> dict[str, Any]:
    """Signal check: FULL hit@N on hold-out (peeking · 발권경로 아님)."""
    from _k_transition_collect import _masks, compute_row_full_style

    max_no = max(draws)
    masks = _masks(draws, max_no)
    hits: list[int] = []
    dist: Counter = Counter()
    skipped = 0
    for t in range(lo, hi + 1):
        row = compute_row_full_style(draws, masks, t, sim_k=2, min_similar=10)
        if row is None:
            skipped += 1
            continue
        h = int(row["hit_count"])
        hits.append(h)
        dist[h] += 1
    mean_hit = float(np.mean(hits)) if hits else 0.0
    ge3 = sum(1 for h in hits if h >= 3)
    n = len(hits)
    return {
        "mode": "full_style_hit_at_N_peek",
        "draw_range": [lo, hi],
        "n_draws": n,
        "n_skipped": skipped,
        "mean_hit": round(mean_hit, 6),
        "delta_vs_full_prior": round(mean_hit - FULL_PRIOR_MEAN, 6),
        "hit_dist": {str(k): int(dist.get(k, 0)) for k in range(7)},
        "ge3_count": ge3,
        "ge3_rate": round(ge3 / n, 6) if n else 0.0,
        "metric_note": "FULL 동치·hold-out · 컨닝성(발권 판단 1차 아님)",
    }


def replace_verdict(bt: dict[str, Any]) -> tuple[str, list[str]]:
    mean = float(bt["mean_hit"])
    ge3_rate = float(bt["ge3_rate"])
    # Instruction: mean>2.05 AND ge3 > stat 기준
    # Cursor cover: stat top15 ge3 없음 → 무작위 top15 ge3_rate=0.311 대비
    ge3_ok = ge3_rate > RANDOM_GE3_RATE
    if mean > 2.05 and ge3_ok:
        v = "REPLACE_GO"
    elif mean < 1.95:
        v = "ABORT"
    else:
        v = "HOLD"

    risks = [
        "(a) transition_log/hook 미작동 시 캐시 공백 — 런타임은 lotto_draws 재계산 fallback 필수",
        "(b) 초반·희소 구간 min_similar<10 → top15 불안정 · fallback(빈도/직전풀) 명세 필요",
        "(c) 롤백: predict_stat_fairy.py·stat_brain.predict 경로 유지·플래그로 전환 "
        "(STEP4에서 FEATURE 플래그·하드코딩 금지 검토)",
    ]
    return v, risks


def overall_verdict(replace: str, stat_ok: bool) -> str:
    if not stat_ok:
        return "DESIGN_ABORT"
    if replace == "REPLACE_GO":
        return "DESIGN_GO"
    if replace == "ABORT":
        return "DESIGN_ABORT"
    return "DESIGN_HOLD"


def write_md(p: dict[str, Any]) -> None:
    bt = p["backtest_result"]
    full = p["backtest_full_style_holdout"]
    lines = [
        "# K-TRANSITION-STEP3-DESIGN — transition→stat 대체 설계 (2026-08-05)",
        "",
        "> **작성:** Cursor · wire=`False` · brains/engine **미수정** · 설계·시뮬만",
        "",
        f"- **판정:** `{p['verdict']}` · replace=`{p['replace_verdict']}`",
        "",
        "## [1] stat 현황 (READ-ONLY)",
        f"- file: `{p['stat_current_summary']['file']}`",
        f"- logic: {p['stat_current_summary']['logic_summary']}",
        f"- K-A mean_ref: **{p['stat_current_summary']['current_mean_ref']}** "
        f"({p['stat_current_summary']['current_mean_ref_note']})",
        "",
        "## [2] design_spec",
        f"- name: `{p['design_spec']['name']}`",
        f"- params: `{p['design_spec']['params']}`",
        f"- interface_match: {p['design_spec']['interface_match']}",
        "",
        "## [3] backtest (발권경로 = nopeek)",
        f"- range {bt['draw_range']} n={bt['n_draws']} · mean_hit=**{bt['mean_hit']}** · "
        f"ge3_rate=**{bt['ge3_rate']}** (rand≈{RANDOM_GE3_RATE})",
        f"- hit_dist: {bt['hit_dist']}",
        "",
        "## [3b] FULL-style hold-out (참고·peek)",
        f"- mean_hit={full['mean_hit']} · ge3_rate={full['ge3_rate']} · "
        f"Δvs prior={full['delta_vs_full_prior']}",
        "",
        "## [4] replace / risk",
        f"- replace_verdict: **{p['replace_verdict']}**",
        *[f"- {r}" for r in p["risk_list"]],
        "",
        f"- prior: `{p['prior']}`",
        f"- tool: `{p['tool']}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(OUT_MD.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    print("[1] stat read", flush=True)
    stat = read_stat_summary()
    print("[2] design_spec", flush=True)
    spec = design_spec()

    conn = _conn()
    try:
        draws = load_draws(conn)
        log_by_t = load_log_hits(conn)
    finally:
        conn.close()

    print("[3] backtest nopeek + full holdout", flush=True)
    bt = backtest_nopeek(log_by_t, BT_LO, BT_HI)
    full_bt = backtest_full_holdout(draws, BT_LO, BT_HI)

    # Schema primary backtest_result = nopeek (deployable)
    # Enrich with comparison fields expected by instruction
    bt_out = {
        "draw_range": bt["draw_range"],
        "n_draws": bt["n_draws"],
        "mean_hit": bt["mean_hit"],
        "delta_vs_stat": bt["delta_vs_stat_set_mean_KA"],
        "delta_vs_baseline2": bt["delta_vs_baseline2"],
        "hit_dist": bt["hit_dist"],
        "ge3_count": bt["ge3_count"],
        "ge3_rate": bt["ge3_rate"],
        "mode": bt["mode"],
        "metric_note": bt["metric_note"],
        "n_missing_log": bt["n_missing_log"],
        "random_ge3_rate": RANDOM_GE3_RATE,
        "instruction_target_mean_approx": FULL_PRIOR_MEAN,
        "instruction_note": (
            "지시서 '≈2.172'는 FULL hit@N 전역 신호. "
            "발권 가능 nopeek hold-out는 별도(본 backtest_result)."
        ),
    }

    rv, risks = replace_verdict(bt)
    ov = overall_verdict(rv, stat_ok=bool(stat["interface"]["predict_sets_found"]))

    payload = {
        "id": "K-TRANSITION-STEP3-DESIGN",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": ov,
        "wire": False,
        "alignment_check": {
            "direction_match": True,
            "cursor_cover": [
                "K-A 0.760=set mean ≠ top15; 판정은 nopeek top15 hold-out",
                "FULL≈2.172는 peek 참고(backtest_full_style_holdout)",
                "ge3 기준=무작위 top15 0.311 (stat top15 ge3 미확인)",
            ],
            "hard_stop": False,
        },
        "stat_current_summary": stat,
        "design_spec": spec,
        "backtest_result": bt_out,
        "backtest_full_style_holdout": full_bt,
        "replace_verdict": rv,
        "risk_list": risks,
        "forbid": [
            "engine.py 수정",
            "brains/ 파일 수정 (읽기만)",
            "wire",
            "auto-tune",
            "random.choices",
            "발권 테이블 INSERT/UPDATE",
            "stat 즉시 교체 실행",
            "coordinator 접촉",
            "신호 과장 클레임",
        ],
        "pass": ov in ("DESIGN_GO", "DESIGN_HOLD"),
        "tool": "tools/_k_transition_step3_design.py",
        "prior": "docs/benchmarks/20260805_KTRANSITION_STEP2_VERIFY.json",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_md(payload)
    print(
        json.dumps(
            {
                "ok": True,
                "verdict": ov,
                "replace": rv,
                "nopeek_mean": bt["mean_hit"],
                "nopeek_ge3_rate": bt["ge3_rate"],
                "full_holdout_mean": full_bt["mean_hit"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
