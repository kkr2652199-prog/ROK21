# -*- coding: utf-8 -*-
"""K-LIVE-QUICK200 — 예측DB 리셋 후 live 스택 n=200 백테 분석.

- 1236 대기 불필요 · 확정구간(기본 1036~1235) walk-forward · 컨닝 없음
- 예측 관련 테이블 삭제 후 재기입
- Path A: coordinator fusion (FUTURE-WIRE+V2)
- Path B: signal_pool build_pool_and_repack (hybrid hy_p45_r123)
- rare annotate는 진단 집계만 (WIRE OFF)

Usage:
  python tools/_k_live_quick200_reset_bench.py
  python tools/_k_live_quick200_reset_bench.py --start 1035 --end 1234
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.bench_quick_gate import (  # noqa: E402
    MC_SEED,
    NULL_GE3,
    WIRE_PIN_GE3,
    enrich_metrics,
)

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KLIVE_QUICK200_RESET.json"
OUT_MD = ROOT / "reports" / "20260805_KLIVE_QUICK200_RESET.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
BRAINS = ("stat", "markov", "review")


def reset_all_prediction_dbs() -> dict[str, int]:
    """예측·캐시·학습상태 리셋. lotto_draws·evolve_log 유지."""
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    deleted: dict[str, int] = {}
    try:
        for sql, key in [
            ("DELETE FROM lotto_predictions", "lotto_predictions"),
            ("DELETE FROM testlotto_pool_view_cache", "testlotto_pool_view_cache"),
            ("DELETE FROM testlotto_brain_learn_state", "testlotto_brain_learn_state"),
            ("DELETE FROM testlotto_brain_review", "testlotto_brain_review"),
        ]:
            cur = conn.execute(sql)
            deleted[key] = int(cur.rowcount if cur.rowcount is not None and cur.rowcount >= 0 else 0)
        conn.execute(
            """
            UPDATE testlotto_brain_weights SET
                current_weight=1.0, recent_avg_match=0,
                total_predictions=0, total_matches=0, last_updated_draw=0
            """
        )
        deleted["testlotto_brain_weights_reset"] = 1
        conn.commit()
    finally:
        conn.close()
    return deleted


def _ge3_block(bests: list[int], *, gate_mode: str = "quick") -> dict[str, Any]:
    n = len(bests)
    g = sum(1 for x in bests if x >= 3)
    mm = mean(bests) if bests else 0.0
    return {
        **enrich_metrics(g, n, mm, gate_mode=gate_mode),
        "mean_best": round(mm, 4),
        "n": n,
        "ge3_count": g,
    }


def _apply_flags() -> None:
    from app.testlotto.brains import coordinator as coord_mod
    from app.testlotto.brains.markov_brain import learn as markov_learn
    from app.testlotto.brains.markov_brain import predict as markov_predict
    from app.testlotto.brains.review_brain import predict as review_predict
    from app.testlotto.brains.stat_brain import predict as stat_predict

    stat_predict.HINT_WEIGHT = 0.15
    markov_predict.HINT_WEIGHT = 0.15
    review_predict.HINT_WEIGHT = 0.15
    markov_learn.LEARN_WIRED = True
    coord_mod.AUX_1TO1_ENABLED = True
    coord_mod.MARKOV_WIRE_ENABLED = True
    coord_mod.BUCKET_SELECT_MODE = "aux_hint_native"
    coord_mod.BENCH_FIXED_QUOTA = None


def run_fusion(lo: int, hi: int) -> dict[str, Any]:
    from app.testlotto.brains.coordinator import PREDICT_TAGS, run_coordinated_prediction
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db

    _apply_flags()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (lo, hi),
    ).fetchall()
    conn.close()

    bests: list[int] = []
    quota: Counter[str] = Counter()
    per_draw: list[dict[str, Any]] = []
    total = len(rows)
    for idx, raw in enumerate(rows):
        row = dict(raw)
        dno = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        random.seed(MC_SEED + dno)
        set_learn_as_of(dno)
        result = run_coordinated_prediction(dno)
        if result.get("error"):
            per_draw.append({"draw_no": dno, "error": result["error"]})
            continue
        conn = get_lotto_db()
        try:
            preds = conn.execute(
                "SELECT brain_tag, num1,num2,num3,num4,num5,num6,matched_count "
                "FROM lotto_predictions WHERE target_draw_no=?",
                (dno,),
            ).fetchall()
        finally:
            conn.close()
        best = 0
        for p in preds:
            pd = dict(p)
            quota[str(pd.get("brain_tag") or "")] += 1
            if pd.get("matched_count") is not None and int(pd["matched_count"]) >= 0:
                mc = int(pd["matched_count"])
            else:
                nums = [int(pd[f"num{k}"]) for k in range(1, 7)]
                mc = len(set(nums) & actual)
            best = max(best, mc)
        bests.append(best)
        per_draw.append({"draw_no": dno, "best_hits": best, "n_preds": len(preds)})
        if (idx + 1) % 25 == 0 or idx + 1 == total:
            print(f"  [fusion {idx + 1}/{total}] draw={dno} best={best}", flush=True)

    qt = sum(quota.values()) or 1
    return {
        "path": "coordinator_fusion",
        "draw_range": [lo, hi],
        "n_eval": len(bests),
        "overall": _ge3_block(bests),
        "quota_pct": {t: round(100 * quota[t] / qt, 2) for t in PREDICT_TAGS},
        "per_draw_tail20": per_draw[-20:],
    }


def run_hybrid_pool(lo: int, hi: int) -> dict[str, Any]:
    """live build_pool_and_repack · 뇌별 repack5 best/mean/ge3 · 캐시 재저장."""
    from app.testlotto.models import get_lotto_db
    from app.testlotto.pool_view_cache import save_pool_view_cache
    from app.testlotto.rare_annotate import annotate_set
    from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE, build_pool_and_repack

    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT draw_no, num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (lo, hi),
    ).fetchall()
    conn.close()

    brain_bests: dict[str, list[int]] = {b: [] for b in BRAINS}
    brain_means: dict[str, list[float]] = {b: [] for b in BRAINS}
    rare_tag_c: Counter[str] = Counter()
    ultra_c = 0
    set_n = 0
    total = len(rows)
    for idx, raw in enumerate(rows):
        row = dict(raw)
        dno = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        built = build_pool_and_repack(dno, seed=MC_SEED)
        if not built.get("ok"):
            print(f"  [hybrid WARN] draw={dno} {built.get('error')}", flush=True)
            continue
        save_pool_view_cache(dno, built)
        for tag in BRAINS:
            repack = built.get("repack_by_brain", {}).get(tag) or []
            hits = [len(set(int(x) for x in s["nums"]) & actual) for s in repack]
            if not hits:
                continue
            brain_bests[tag].append(max(hits))
            brain_means[tag].append(mean(hits))
            for s in repack:
                set_n += 1
                ann = annotate_set(s["nums"])
                for t in ann["rare_tags"]:
                    rare_tag_c[t] += 1
                if ann.get("is_ultra_rare_tag"):
                    ultra_c += 1
        if (idx + 1) % 25 == 0 or idx + 1 == total:
            print(f"  [hybrid {idx + 1}/{total}] draw={dno}", flush=True)

    by_brain = {}
    for tag in BRAINS:
        b = brain_bests[tag]
        by_brain[tag] = {
            **_ge3_block(b),
            "mean_of_mean_hits": round(mean(brain_means[tag]), 4) if brain_means[tag] else 0.0,
        }
    return {
        "path": "signal_pool_hybrid",
        "FEATURE_LAMBDA_WIRE": FEATURE_LAMBDA_WIRE,
        "assemble": "hy_p45_r123 (stat/review) · markov baseline",
        "draw_range": [lo, hi],
        "n_eval": total,
        "by_brain": by_brain,
        "rare_diag": {
            "sets_scored": set_n,
            "ultra_tagged_sets": ultra_c,
            "ultra_rate": round(ultra_c / set_n, 4) if set_n else 0.0,
            "tag_counts_top": dict(rare_tag_c.most_common(15)),
            "wire": False,
            "note": "진단 집계만 · RARE_ANNOTATE_WIRE=False · 발권 미변경",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1036, help="eval start (default 1036)")
    ap.add_argument("--end", type=int, default=1235, help="eval end inclusive (default 1235)")
    ap.add_argument("--skip-hybrid", action="store_true")
    ap.add_argument("--skip-fusion", action="store_true")
    args = ap.parse_args()
    lo, hi = int(args.start), int(args.end)
    n_expect = hi - lo + 1

    print("K-LIVE-QUICK200 reset prediction DBs…", flush=True)
    deleted = reset_all_prediction_dbs()
    print(f"  deleted={deleted}", flush=True)

    from app.testlotto.brains import coordinator as coord_mod
    from app.testlotto.pair_cover import PAIR_COVER_WIRE
    from app.testlotto.rare_annotate import RARE_ANNOTATE_WIRE
    from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE
    from app.testlotto.structure_cover import STRUCTURE_COVER_WIRE

    payload: dict[str, Any] = {
        "id": "K-LIVE-QUICK200-RESET",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "draw_range": [lo, hi],
        "n_expect": n_expect,
        "seed": MC_SEED,
        "reset_deleted": deleted,
        "kept": ["lotto_draws", "testlotto_evolve_log", "testlotto_rare_bundle_*"],
        "stack": {
            "FEEDBACK_MATCH_MODE": getattr(coord_mod, "FEEDBACK_MATCH_MODE", None),
            "FEATURE_LAMBDA_WIRE": FEATURE_LAMBDA_WIRE,
            "STRUCTURE_COVER_WIRE": STRUCTURE_COVER_WIRE,
            "PAIR_COVER_WIRE": PAIR_COVER_WIRE,
            "RARE_ANNOTATE_WIRE": RARE_ANNOTATE_WIRE,
            "hybrid": "hy_p45_r123",
        },
        "refs": {
            "null_ge3_best5": NULL_GE3,
            "wire_pin_ge3": WIRE_PIN_GE3,
            "post_evolve_full_ge3": 0.1184,
            "future_wire_quick_ge3": 0.1350,
        },
        "note": "1236 미대기 · 확정회차만 WF · 예측DB 리셋 후 재기입 · 당첨P↑ 비약속",
    }

    if not args.skip_fusion:
        print(f"FUSION walk-forward {lo}~{hi}…", flush=True)
        payload["fusion"] = run_fusion(lo, hi)
    if not args.skip_hybrid:
        print(f"HYBRID pool/repack walk-forward {lo}~{hi}…", flush=True)
        payload["hybrid"] = run_hybrid_pool(lo, hi)

    # verdict: fusion ge3 vs null (informational)
    fus = (payload.get("fusion") or {}).get("overall") or {}
    ge3 = float(fus.get("ge3_rate") or 0)
    payload["verdict"] = {
        "fusion_ge3": ge3,
        "vs_null": round(ge3 - NULL_GE3, 4),
        "vs_pin": round(ge3 - WIRE_PIN_GE3, 4),
        "patch_pass_gt_0_09": ge3 > 0.09,
        "label": "MEASURED",
    }
    payload["pass"] = True

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-LIVE-QUICK200-RESET",
        "",
        f"📅 {payload['ts'][:10]} · **MEASURED** · n≈{n_expect} · range **{lo}~{hi}**",
        "",
        "## 리셋",
        "",
        f"- deleted: `{json.dumps(deleted, ensure_ascii=False)}`",
        "- kept: lotto_draws · evolve_log · rare_bundle",
        "",
        "## 스택 (wire)",
        "",
        f"- mean feedback = `{payload['stack']['FEEDBACK_MATCH_MODE']}`",
        f"- λ/cover/rare annotate = **False**",
        f"- hybrid assemble = `{payload['stack']['hybrid']}`",
        "",
    ]
    if payload.get("fusion"):
        o = payload["fusion"]["overall"]
        lines.extend(
            [
                "## Path A — fusion (coordinator)",
                "",
                f"- ge3 = **{o.get('ge3_rate')}** (count={o.get('ge3_count')}/{o.get('n')})",
                f"- mean_best = **{o.get('mean_best')}**",
                f"- vs null = {payload['verdict']['vs_null']} · vs pin = {payload['verdict']['vs_pin']}",
                f"- quota% = {payload['fusion'].get('quota_pct')}",
                "",
            ]
        )
    if payload.get("hybrid"):
        lines.extend(["## Path B — hybrid pool/repack (3뇌)", ""])
        for tag, row in (payload["hybrid"].get("by_brain") or {}).items():
            lines.append(
                f"- **{tag}** ge3=**{row.get('ge3_rate')}** mean_best={row.get('mean_best')} "
                f"mean_hits={row.get('mean_of_mean_hits')}"
            )
        rd = payload["hybrid"].get("rare_diag") or {}
        lines.extend(
            [
                "",
                "### rare 진단 (발권 미적용)",
                "",
                f"- ultra_tagged_sets = {rd.get('ultra_tagged_sets')}/{rd.get('sets_scored')} "
                f"(rate={rd.get('ultra_rate')})",
                f"- top tags = `{rd.get('tag_counts_top')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## 해석",
            "",
            "- 1236을 기다릴 필요 없음 · 1~1235 확정분으로 군/엔진 관측 가능",
            "- 본 백테는 **운송·발권 성적 관측**이지 당첨확률 부스트 증명이 아님",
            "- 극소수 필터는 진단층만 · R4 정책 wire는 별도 형 GO",
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
                "fusion_ge3": ge3,
                "out": OUT_JSON.name,
                "range": [lo, hi],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
