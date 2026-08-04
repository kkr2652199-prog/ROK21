# -*- coding: utf-8 -*-
"""K-PIN-GAP-DIAG — FUTURE-WIRE FULL pin갭(Δ−0.0263) 원인 진단.

수정3건 반영:
  - FULL thirds n=394 (N100 25/25/50는 보조)
  - 1차=기존 JSON READ-ONLY · seed 스윕만 N100 WF(별도 명시)
  - wire/engine 패치 없음

Usage:
  python tools/_k_pin_gap_diag.py              # JSON 분석만
  python tools/_k_pin_gap_diag.py --seed-sweep  # + N100 seed 스윕 (DB reset·재기입)
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PIN = 0.1447
NULL5 = 0.1137
FULL_GE3 = 0.1184
N100_GE3 = 0.1500
QUICK_GE3 = 0.1350

SOLO = {"stat": 0.09, "markov": 0.13, "review": 0.11}
QUOTA_FULL = {"stat": 0.0, "markov": 80.0, "review": 20.0}


def _load(name: str) -> dict[str, Any]:
    p = ROOT / "docs" / "benchmarks" / name
    return json.loads(p.read_text(encoding="utf-8"))


def analyze_from_json() -> dict[str, Any]:
    full = _load("20260803_KFUTURE_WIRE_FULL.json")
    n100 = _load("20260803_KFUTURE_WIRE_N100.json")
    quick = _load("20260803_KFUTURE_WIRE_QUICK200.json")

    fp = full["by_period"]
    early_gap = round(fp["early"]["ge3_rate"] - PIN, 4)
    mid_gap = round(fp["mid"]["ge3_rate"] - PIN, 4)
    late_gap = round(fp["late"]["ge3_rate"] - PIN, 4)
    worst = min(
        (("early", early_gap), ("mid", mid_gap), ("late", late_gap)),
        key=lambda x: x[1],
    )

    # 가중 solo 혼합 기대(단순 선형 · 독립가정 근사)
    blend = round(
        (QUOTA_FULL["markov"] / 100) * SOLO["markov"]
        + (QUOTA_FULL["review"] / 100) * SOLO["review"]
        + (QUOTA_FULL["stat"] / 100) * SOLO["stat"],
        4,
    )
    dilution_vs_blend = round(FULL_GE3 - blend, 4)
    dilution_vs_markov = round(FULL_GE3 - SOLO["markov"], 4)
    markov_vs_pin = round(SOLO["markov"] - PIN, 4)

    # pin갭 분해(설명용 · 가산 아님)
    gap_pin = round(FULL_GE3 - PIN, 4)
    gap_n100_collapse = round(FULL_GE3 - N100_GE3, 4)
    gap_early_excess = round(fp["early"]["ge3_rate"] - FULL_GE3, 4)

    period_block = {
        "window": "FULL",
        "draw_range": full["draw_range"],
        "n_eval": full["n_eval"],
        "split": "thirds_by_draw_index",
        "n_each": 394,
        "note": "N100의 25/25/50·「mid 붕괴」는 FULL pin갭 진단에 사용 금지",
        "by_period": {
            k: {
                "n": v["n"],
                "ge3_rate": v["ge3_rate"],
                "ge3_count": v["ge3_count"],
                "mean": v["mean"],
                "delta_ge3_vs_pin": round(v["ge3_rate"] - PIN, 4),
                "delta_ge3_vs_null": round(v["ge3_rate"] - NULL5, 4),
            }
            for k, v in fp.items()
        },
        "worst_vs_pin": {"period": worst[0], "delta_ge3_vs_pin": worst[1]},
        "mid_collapse_claim": False,
        "mid_vs_early_ge3": round(fp["mid"]["ge3_rate"] - fp["early"]["ge3_rate"], 4),
    }

    n100_period = {
        "window": "N100_aux_only",
        "draw_range": n100["draw_range"],
        "split": "25/25/50",
        "by_period": {
            k: {
                "n": v["n"],
                "ge3_rate": v["ge3_rate"],
                "delta_ge3_vs_pin": round(v["ge3_rate"] - PIN, 4),
            }
            for k, v in n100["by_period"].items()
        },
        "note": "보조 창. late가 pin 대비 최약(−0.0247). mid 붕괴 아님.",
    }

    brain_block = {
        "quota_avg_pct_full": QUOTA_FULL,
        "solo_ge3_priors_ref": SOLO,
        "solo_source": "K-HIGHWAY-BACKTEST-100 by_brain (docs/benchmarks/20260801_KHIGHWAY_BACKTEST_100.json)",
        "linear_blend_ge3": blend,
        "full_fused_ge3": FULL_GE3,
        "dilution_vs_blend": dilution_vs_blend,
        "dilution_vs_markov_solo": dilution_vs_markov,
        "markov_solo_vs_pin": markov_vs_pin,
        "stat_share_pct": 0.0,
        "lockin_effect": {
            "markov_share_pct": 80.0,
            "interpretation": (
                "quota 고착으로 fused≈markov 지배. "
                "단 markov solo 0.13 자체도 pin 0.1447 미달(Δ−0.0147)이므로 "
                "pin갭 전량이 희석만으로 설명되지 않음."
            ),
            "pin_gap_explained_by_quota_alone": False,
            "est_gap_from_dilution_vs_markov": dilution_vs_markov,
            "residual_gap_markov_to_pin": markov_vs_pin,
        },
    }

    km_kn = {
        "K-M": {
            "status": "HOLD",
            "source": "reports/20260727_KM_KN_분산검정.md · FINDINGS",
            "weight_max_delta_vs_uniform": 0.0018,
            "top5_membership_mismatch_vs_uniform_pct": 5.0,
            "effective_referee_leverage": "~0%",
            "pin_gap_contribution": {
                "verdict": "negligible",
                "rationale": (
                    "referee≈균등·멤버십 95% 동일. "
                    "FULL pin갭 Δ−0.0263을 가중 변동(0.18%p)으로 설명 불가. "
                    "현 live quota는 SOLO_GE3_PRIORS×dominance(학습 referee 실효0)에 의해 4/0/1 고정."
                ),
                "est_ge3_delta_attributable": 0.0,
            },
        },
        "K-N": {
            "status": "HOLD",
            "source": "reports/20260727_KM_KN_분산검정.md · FINDINGS",
            "finding": "학습입력 best → null상 실력 증거 없음(창100)",
            "pin_gap_contribution": {
                "verdict": "low_indirect",
                "rationale": (
                    "FULL WF는 learn_state reset 후 재누적. "
                    "early(0.099)가 late(0.1244)보다 낮아 "
                    "「잘못된 best학습 누적」이 early 붕괴의 주원인 가설과 불일치. "
                    "간접(가중·boost 경로) 가능하나 pin갭 주성분으로 수치 미입증."
                ),
                "est_ge3_delta_attributable": None,
                "note": "미확인(직접 계수 분리 실험 없음) — null로 표기하지 않고 None",
            },
        },
    }

    return {
        "id": "K-PIN-GAP-DIAG",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "json_readonly_primary",
        "eval_mode": "best_of_5",
        "references": {
            "full_ge3": FULL_GE3,
            "quick_ge3": QUICK_GE3,
            "n100_ge3": N100_GE3,
            "wire_pin_ge3": PIN,
            "null_ge3_best_of_5": NULL5,
            "delta_full_vs_pin": gap_pin,
            "delta_full_vs_n100": gap_n100_collapse,
            "sources": {
                "full": "docs/benchmarks/20260803_KFUTURE_WIRE_FULL.json",
                "quick": "docs/benchmarks/20260803_KFUTURE_WIRE_QUICK200.json",
                "n100": "docs/benchmarks/20260803_KFUTURE_WIRE_N100.json",
            },
        },
        "period_decomposition": period_block,
        "n100_period_aux": n100_period,
        "quick_period_aux": {
            "window": "QUICK200",
            "by_period": {
                k: {
                    "n": v["n"],
                    "ge3_rate": v["ge3_rate"],
                    "delta_ge3_vs_pin": round(v["ge3_rate"] - PIN, 4),
                }
                for k, v in quick["by_period"].items()
            },
        },
        "brain_contribution": brain_block,
        "km_kn": km_kn,
        "gap_drivers_ranked": [
            {
                "rank": 1,
                "driver": "FULL_early_period_weakness",
                "evidence": f"early ge3={fp['early']['ge3_rate']} Δpin={early_gap} (n=394)",
                "share_note": "기간 중 pin 대비 최악 · mid 붕괴 아님",
            },
            {
                "rank": 2,
                "driver": "n100_to_full_collapse",
                "evidence": f"0.1500→0.1184 Δ={gap_n100_collapse}",
                "share_note": "소표본 행운/구간의존 · pin과 별개이나 동시 관측",
            },
            {
                "rank": 3,
                "driver": "markov80_quota_lock_plus_solo_below_pin",
                "evidence": (
                    f"quota markov80% · fused={FULL_GE3} · "
                    f"blend≈{blend} · markov_solo={SOLO['markov']} vs pin={PIN}"
                ),
                "share_note": "희석(−0.0116 vs solo) + solo자체 pin미달(−0.0147)",
            },
            {
                "rank": 4,
                "driver": "K-M_referee",
                "evidence": "membership mismatch 5% · wΔ≈0.0018",
                "share_note": "pin갭 기여 ≈0",
            },
            {
                "rank": 5,
                "driver": "K-N_best_feedback",
                "evidence": "early≪late → 누적오인 주원인 불일치",
                "share_note": "직접 기여 미입증(low_indirect)",
            },
        ],
        "seed_sensitivity": {
            "status": "pending_or_see_seed_sweep",
            "production_seed": 42,
            "note": "동일 N100 창에서 seed 변화 시 ge3 변동은 --seed-sweep 결과 병기",
        },
        "conclusions": {
            "mid_collapse": False,
            "primary_period": "early",
            "km_explains_pin_gap": False,
            "kn_explains_pin_gap": False,
            "quota_alone_explains_pin_gap": False,
            "next_patch_candidates": [
                "early-period 안정화 조사(윈도/학습 warm-up)",
                "FULL-first 게이트(I2)",
                "quota/stat0% A/B는 I1 후(I7) — solo markov도 pin 미달 전제",
                "I3 B1 feature 로그(가중0) 병행",
            ],
            "forbid": ["ultra_wire", "engine_wire_without_GO", "auto_tune"],
        },
        "early_vs_full_note": {
            "early_minus_overall_ge3": gap_early_excess,
        },
    }


def _run_seed_once(seed_base: int) -> dict[str, Any]:
    from app.testlotto.brains import coordinator as coord_mod
    from app.testlotto.brains.coordinator import (
        PREDICT_TAGS,
        run_coordinated_prediction,
    )
    from app.testlotto.brains.markov_brain import learn as markov_learn
    from app.testlotto.brains.markov_brain import predict as markov_predict
    from app.testlotto.brains.review_brain import predict as review_predict
    from app.testlotto.brains.stat_brain import predict as stat_predict
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db
    from tools._k_future_wire_revalidate import (
        _actual_nums,
        _issued_best,
        reset_backtest_tables,
    )
    from tools.bench_quick_gate import enrich_metrics

    stat_predict.HINT_WEIGHT = 0.15
    markov_predict.HINT_WEIGHT = 0.15
    review_predict.HINT_WEIGHT = 0.15
    markov_learn.LEARN_WIRED = True
    coord_mod.AUX_1TO1_ENABLED = True
    coord_mod.MARKOV_WIRE_ENABLED = True
    coord_mod.BUCKET_SELECT_MODE = "aux_hint_native"
    coord_mod.BENCH_FIXED_QUOTA = None
    coord_mod.BRAIN_RNG_SEED_BASE = int(seed_base)

    reset_backtest_tables()
    lo, hi = 1135, 1234
    conn = get_lotto_db()
    draw_rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (lo, hi),
    ).fetchall()
    conn.close()

    bests: list[int] = []
    quota: Counter[str] = Counter()
    for idx, row in enumerate(draw_rows):
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = _actual_nums(row)
        random.seed(seed_base + draw_no)
        result = run_coordinated_prediction(draw_no)
        if result.get("error"):
            continue
        set_learn_as_of(draw_no)
        conn = get_lotto_db()
        try:
            best = _issued_best(conn, draw_no, actual)
            for r in conn.execute(
                "SELECT brain_tag FROM lotto_predictions WHERE target_draw_no=?",
                (draw_no,),
            ).fetchall():
                quota[str(dict(r).get("brain_tag") or "")] += 1
        finally:
            conn.close()
        bests.append(best)
        if (idx + 1) % 25 == 0:
            print(f"  seed={seed_base} [{idx+1}/{len(draw_rows)}] best={best}", flush=True)

    n = len(bests)
    ge3_c = sum(1 for b in bests if b >= 3)
    mean_m = sum(bests) / n if n else 0.0
    m = enrich_metrics(ge3_c, n, mean_m, gate_mode="full", eval_mode="best_of_5")
    qt = sum(quota.values()) or 1
    # restore module default
    coord_mod.BRAIN_RNG_SEED_BASE = 42
    return {
        "seed_base": seed_base,
        "n_eval": n,
        "draw_range": [lo, hi],
        "ge3_rate": m["ge3_rate"],
        "ge3_count": ge3_c,
        "mean": round(mean_m, 4),
        "delta_ge3_vs_pin": round(float(m["ge3_rate"]) - PIN, 4),
        "delta_ge3_vs_ref_n100_seed42": round(float(m["ge3_rate"]) - N100_GE3, 4),
        "quota_avg_pct": {t: round(100 * quota[t] / qt, 2) for t in PREDICT_TAGS},
    }


def run_seed_sweep(seeds: list[int]) -> dict[str, Any]:
    rows = []
    for s in seeds:
        print(f"=== seed sweep base={s} N100 ===", flush=True)
        rows.append(_run_seed_once(s))
    ge3s = [float(r["ge3_rate"]) for r in rows]
    ref42 = next((float(r["ge3_rate"]) for r in rows if r["seed_base"] == 42), None)
    return {
        "status": "done",
        "window": "N100 1135~1234",
        "seeds": seeds,
        "runs": rows,
        "ge3_min": min(ge3s) if ge3s else None,
        "ge3_max": max(ge3s) if ge3s else None,
        "ge3_range": round(max(ge3s) - min(ge3s), 4) if ge3s else None,
        "seed42_ge3": ref42,
        "sensitive": bool(ge3s) and (max(ge3s) - min(ge3s) >= 0.02),
        "interpretation": (
            "N100에서 seed에 따라 ge3가 크게 변하면(범위≥0.02) "
            "n100 PASS(0.15)·소표본 성적은 seed=42 운에 민감. "
            "단 FULL pin갭(Δ−0.0263)은 seed=42 고정 FULL 결과이므로 "
            "「다른 seed면 pin 회복」은 미검증 — FULL multi-seed는 별도 GO."
        ),
    }


def write_report(payload: dict[str, Any]) -> str:
    pin = payload["references"]
    per = payload["period_decomposition"]
    br = payload["brain_contribution"]
    seed = payload.get("seed_sensitivity") or {}
    lines = [
        "# K-PIN-GAP-DIAG — FUTURE-WIRE FULL pin갭 진단",
        "",
        f"HEAD 시점 진단 · `{payload['ts']}` · **READ-ONLY 1차(JSON)**"
        + (" · seed 스윕 포함" if seed.get("status") == "done" else ""),
        "",
        "## 0. 한 줄",
        "",
        f"FULL ge3 **{pin['full_ge3']}** vs pin **{pin['wire_pin_ge3']}** (Δ**{pin['delta_full_vs_pin']}**). "
        f"주원인은 **early 구간 약세(n=394)** + **n100→FULL 붕괴** + "
        f"**markov80% 고착(solo도 pin 미달)**. "
        f"**mid 붕괴 아님** · **K-M≈0 기여** · **K-N 주성분 미입증**.",
        "",
        "## 1. 기간별 분해 (FULL thirds · n=각 394)",
        "",
        "| 구간 | n | ge3 | vs pin | vs null5 |",
        "|------|---|-----|--------|----------|",
    ]
    for k, v in per["by_period"].items():
        lines.append(
            f"| {k} | {v['n']} | **{v['ge3_rate']}** | {v['delta_ge3_vs_pin']:+.4f} | {v['delta_ge3_vs_null']:+.4f} |"
        )
    lines.extend(
        [
            "",
            f"- pin 대비 최악: **{per['worst_vs_pin']['period']}** "
            f"(Δ{per['worst_vs_pin']['delta_ge3_vs_pin']})",
            f"- mid−early ge3 = **{per['mid_vs_early_ge3']:+.4f}** → mid 붕괴 주장 **기각**",
            f"- 보조 N100(25/25/50): late가 pin 최약 — FULL과 창이 다름",
            "",
            "## 2. 뇌·쿼터 기여 (markov 80% 고착)",
            "",
            f"| 항목 | 값 |",
            f"|------|-----|",
            f"| quota FULL | markov {br['quota_avg_pct_full']['markov']}% · "
            f"review {br['quota_avg_pct_full']['review']}% · stat {br['quota_avg_pct_full']['stat']}% |",
            f"| solo ge3 ref | markov {SOLO['markov']} · review {SOLO['review']} · stat {SOLO['stat']} |",
            f"| 선형혼합 기대 | **{br['linear_blend_ge3']}** |",
            f"| FULL fused | **{br['full_fused_ge3']}** |",
            f"| vs markov solo | **{br['dilution_vs_markov_solo']:+.4f}** |",
            f"| markov solo vs pin | **{br['markov_solo_vs_pin']:+.4f}** |",
            "",
            br["lockin_effect"]["interpretation"],
            "",
            "## 3. seed=42 고정 영향",
            "",
        ]
    )
    if seed.get("status") == "done":
        lines.extend(
            [
                f"- 창: {seed.get('window')} · seeds={seed.get('seeds')}",
                f"- ge3 min/max/range: **{seed.get('ge3_min')}** / **{seed.get('ge3_max')}** / **{seed.get('ge3_range')}**",
                f"- seed42 ge3(재측정): **{seed.get('seed42_ge3')}**",
                f"- 민감(≥0.02): **{seed.get('sensitive')}**",
                "",
                "| seed | ge3 | vs pin | vs ref0.15 |",
                "|------|-----|--------|------------|",
            ]
        )
        for r in seed.get("runs") or []:
            lines.append(
                f"| {r['seed_base']} | **{r['ge3_rate']}** | {r['delta_ge3_vs_pin']:+.4f} | "
                f"{r['delta_ge3_vs_ref_n100_seed42']:+.4f} |"
            )
        lines.append("")
        lines.append(seed.get("interpretation") or "")
    else:
        lines.append("- 이번 실행: JSON 분석만 · seed 스윕 미포함(`--seed-sweep` 필요)")
    lines.extend(
        [
            "",
            "## 4. K-M / K-N → pin갭 기여",
            "",
            "| ID | 판정 | 근거 |",
            "|----|------|------|",
            "| K-M | **negligible (~0)** | wΔ≈0.0018 · top5 멤버십 불일치 5% |",
            "| K-N | **low_indirect** | early≪late로 누적오인 주원인 불일치 · 직접계수 미분리 |",
            "",
            "## 5. 드라이버 순위 · 다음 패치 후보",
            "",
        ]
    )
    for d in payload["gap_drivers_ranked"]:
        lines.append(f"{d['rank']}. **{d['driver']}** — {d['evidence']} ({d['share_note']})")
    lines.extend(["", "### next_patch_candidates"])
    for c in payload["conclusions"]["next_patch_candidates"]:
        lines.append(f"- {c}")
    lines.extend(
        [
            "",
            "## 근거 파일",
            "",
            "- `docs/benchmarks/20260803_KFUTURE_WIRE_FULL.json`",
            "- `docs/benchmarks/20260803_KFUTURE_WIRE_N100.json`",
            "- `docs/benchmarks/20260803_KFUTURE_WIRE_QUICK200.json`",
            "- `reports/20260727_KM_KN_분산검정.md`",
            "- `docs/benchmarks/20260801_KHIGHWAY_BACKTEST_100.json` (solo ge3)",
            "",
            "## 금지 준수",
            "",
            "engine.py·coordinator wire 없음 · auto-tune 없음 · FINDINGS 무단 갱신 없음",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--seed-sweep",
        action="store_true",
        help="N100 창에서 seed 스윕(DB reset·재기입 · UI pred 영향)",
    )
    ap.add_argument(
        "--seeds",
        default="42,0,7",
        help="comma seeds for sweep (default 42,0,7)",
    )
    args = ap.parse_args()

    payload = analyze_from_json()
    if args.seed_sweep:
        seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
        payload["seed_sensitivity"] = run_seed_sweep(seeds)
        payload["mode"] = "json_readonly_plus_n100_seed_sweep"

    js = ROOT / "docs" / "benchmarks" / "20260804_KPIN_GAP_DIAG.json"
    md = ROOT / "reports" / "20260804_KPIN_GAP_DIAG.md"
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / md.name
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text = write_report(payload)
    md.write_text(text, encoding="utf-8")
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(f"Wrote {js}", flush=True)
    print(f"Wrote {md}", flush=True)
    print(
        "worst_period=",
        payload["period_decomposition"]["worst_vs_pin"],
        "seed=",
        payload["seed_sensitivity"].get("status"),
        flush=True,
    )


if __name__ == "__main__":
    main()
