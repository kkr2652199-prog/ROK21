# -*- coding: utf-8 -*-
"""K-EVOLVE-VIRTUAL — 확정회차 가상 생애주기 (분석스택 적용).

라이브: hybrid(hy_p45_r123) + FUTURE-WIRE 쿼터 + mean피드백경로
HOLD(미적용): FEATURE_LAMBDA / STRUCTURE_COVER / PAIR_COVER
weight=0 · 동결 토큰 미수정

Usage:
  python tools/_k_evolve_virtual_draw.py --draw 1235
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _actual_struct(draw_no: int) -> dict:
    from app.testlotto.evolve_log import set_features
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        row = conn.execute(
            """
            SELECT draw_no, num1,num2,num3,num4,num5,num6
            FROM lotto_draws WHERE draw_no=?
            """,
            (int(draw_no),),
        ).fetchone()
        prev = conn.execute(
            """
            SELECT num1,num2,num3,num4,num5,num6
            FROM lotto_draws WHERE draw_no=?
            """,
            (int(draw_no) - 1,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {"ok": False, "error": "lotto_draws 없음"}
    d = dict(row)
    nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
    feat = set_features(nums)
    consec_pairs = sum(
        1 for i in range(5) if nums[i + 1] == nums[i] + 1
    )
    carry = 0
    prev_nums = None
    if prev:
        prev_nums = sorted(int(prev[f"num{k}"]) for k in range(1, 7))
        carry = len(set(nums) & set(prev_nums))
    return {
        "ok": True,
        "draw_no": int(draw_no),
        "actual": nums,
        "prev_draw": int(draw_no) - 1 if prev_nums else None,
        "prev_nums": prev_nums,
        "features": feat,
        "warrant_view": {
            "consec_pairs": consec_pairs,
            "consec_ge1": consec_pairs >= 1,
            "carry": carry,
            "carry_ge1": carry >= 1,
            "odd": feat["odd"],
            "sum": feat["sum"],
            "zones": [feat["zone_low"], feat["zone_mid"], feat["zone_high"]],
            "span": feat["span"],
            "max_run": feat["max_run"],
            "note": "명분진단만 · covering/λ wire 아님",
        },
    }


def _snapshot_evolve(draw_no: int) -> list[dict]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        raw = conn.execute(
            """
            SELECT brain_tag, best_hits, mean_hits, assemble_mode,
                   features_json, miss_tags_json, note
            FROM testlotto_evolve_log WHERE draw_no=?
            ORDER BY brain_tag
            """,
            (int(draw_no),),
        ).fetchall()
    finally:
        conn.close()
    rows = []
    for r in raw:
        d = dict(r)
        rows.append(
            {
                "brain_tag": d["brain_tag"],
                "best_hits": d["best_hits"],
                "mean_hits": d["mean_hits"],
                "assemble_mode": d["assemble_mode"],
                "features": json.loads(d["features_json"] or "{}"),
                "miss_tags": json.loads(d["miss_tags_json"] or "[]"),
                "note": d.get("note") or "",
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draw", type=int, required=True, help="가상 진행 회차(확정번호 필요)")
    args = ap.parse_args()
    draw_no = int(args.draw)

    from app.testlotto.evolve_auto import (
        predict_and_cache,
        score_draw_from_cache,
        save_auto_state,
        _maybe_mean_feedback_after_score,
    )
    from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE
    from app.testlotto.feature_lambda import FEATURE_LAMBDA_BY_BRAIN
    from app.testlotto.structure_cover import STRUCTURE_COVER_WIRE
    from app.testlotto.pair_cover import PAIR_COVER_WIRE
    from app.testlotto.brains.coordinator import FEEDBACK_MATCH_MODE
    from app.testlotto.pool_view_cache import CACHE_SCHEMA_VERSION

    before = _snapshot_evolve(draw_no)
    actual = _actual_struct(draw_no)
    if not actual.get("ok"):
        print(json.dumps(actual, ensure_ascii=False), flush=True)
        return 1

    print(f"K-EVOLVE-VIRTUAL draw={draw_no} PREDICT…", flush=True)
    pred = predict_and_cache(draw_no)
    if not pred.get("ok"):
        print(json.dumps(pred, ensure_ascii=False), flush=True)
        return 1

    print(f"K-EVOLVE-VIRTUAL draw={draw_no} SCORE…", flush=True)
    scored = score_draw_from_cache(draw_no)
    if not scored.get("ok"):
        print(json.dumps(scored, ensure_ascii=False), flush=True)
        return 1

    # SCORE note 보강
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        conn.execute(
            """
            UPDATE testlotto_evolve_log
            SET note = ?, updated_at = datetime('now','localtime')
            WHERE draw_no = ?
            """,
            (
                "K-EVOLVE-VIRTUAL · live hybrid+mean · λ/cover OFF · weight=0",
                draw_no,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    fb = _maybe_mean_feedback_after_score(draw_no)
    after = _snapshot_evolve(draw_no)

    stack = {
        "hybrid_assemble": "hy_p45_r123 (stat/review) · markov baseline",
        "FEEDBACK_MATCH_MODE": FEEDBACK_MATCH_MODE,
        "CACHE_SCHEMA_VERSION": CACHE_SCHEMA_VERSION,
        "FEATURE_LAMBDA_WIRE": FEATURE_LAMBDA_WIRE,
        "FEATURE_LAMBDA_BY_BRAIN": dict(FEATURE_LAMBDA_BY_BRAIN),
        "STRUCTURE_COVER_WIRE": STRUCTURE_COVER_WIRE,
        "PAIR_COVER_WIRE": PAIR_COVER_WIRE,
        "weight_applied": 0,
        "applied_from_analysis": [
            "FUTURE-WIRE + V2 quota (live)",
            "repack hybrid hy_p45_r123",
            "mean feedback path (predictions 없으면 no-op)",
            "λ HOLD (full/tail 기각)",
            "structure/pair cover HOLD (ge3↓)",
            "warrant = 진단 라벨 only",
        ],
    }

    ge3 = {
        b["brain_tag"]: int(b.get("best_hits") or 0) >= 3 for b in (scored.get("brains") or [])
    }
    payload = {
        "id": "K-EVOLVE-VIRTUAL",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "draw_no": draw_no,
        "virtual": True,
        "stack": stack,
        "actual": actual,
        "predict": {
            "ok": pred.get("ok"),
            "cached": pred.get("cached"),
            "seed": pred.get("seed"),
            "hybrid": pred.get("hybrid"),
            "feature_lambda": pred.get("feature_lambda"),
        },
        "score": scored,
        "feedback": fb,
        "before_evolve": before,
        "after_evolve": after,
        "ge3_best": ge3,
        "pass": bool(pred.get("ok") and scored.get("ok") and len(after) >= 3),
        "verdict": "PASS",
        "note": "확정회차 가상 생애 · 회차번호는 스테이징 · 분석스택만 적용(실패축 OFF)",
    }
    if not payload["pass"]:
        payload["verdict"] = "FAIL"

    save_auto_state(
        phase="virtual_scored",
        last_error="",
        last_plan={"id": "K-EVOLVE-VIRTUAL", "draw_no": draw_no, "verdict": payload["verdict"]},
        last_completed_draw=draw_no,
    )

    out_json = ROOT / "docs" / "benchmarks" / f"20260805_KEVOLVE_VIRTUAL_{draw_no}.json"
    out_md = ROOT / "reports" / f"20260805_KEVOLVE_VIRTUAL_{draw_no}.md"
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / out_md.name
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    w = actual.get("warrant_view") or {}
    lines = [
        f"# K-EVOLVE-VIRTUAL draw={draw_no}",
        "",
        f"📅 {payload['ts'][:10]} · **{payload['verdict']}** · 확정회차 가상 생애(분석스택)",
        "",
        "## 적용 스택",
        "",
        f"- hybrid: `{stack['hybrid_assemble']}`",
        f"- feedback mode: **{stack['FEEDBACK_MATCH_MODE']}** (predictions 없으면 no-op)",
        f"- cache schema: **{stack['CACHE_SCHEMA_VERSION']}**",
        f"- λ wire: **{stack['FEATURE_LAMBDA_WIRE']}** · cover: struct={stack['STRUCTURE_COVER_WIRE']} pair={stack['PAIR_COVER_WIRE']}",
        f"- weight: **0**",
        "",
        "## 실제번호 · 명분진단",
        "",
        f"- actual = `{actual['actual']}`",
        f"- prev({actual.get('prev_draw')}) = `{actual.get('prev_nums')}`",
        f"- consec_pairs={w.get('consec_pairs')} · carry={w.get('carry')} · odd={w.get('odd')} · sum={w.get('sum')} · zones={w.get('zones')}",
        "",
        "## SCORE (재예측 후)",
        "",
    ]
    for b in scored.get("brains") or []:
        lines.append(
            f"- **{b['brain_tag']}** best={b['best_hits']} mean={b['mean_hits']} "
            f"assemble=`{b.get('assemble_mode')}` ge3={ge3.get(b['brain_tag'])}"
        )
    lines.extend(
        [
            "",
            "## before → after (best_hits)",
            "",
        ]
    )
    before_map = {r["brain_tag"]: r for r in before}
    for r in after:
        tag = r["brain_tag"]
        b0 = before_map.get(tag) or {}
        lines.append(
            f"- {tag}: {b0.get('best_hits')} → **{r.get('best_hits')}** "
            f"(mean {b0.get('mean_hits')} → {r.get('mean_hits')}) "
            f"assemble `{b0.get('assemble_mode')}` → `{r.get('assemble_mode')}`"
        )
    lines.extend(
        [
            "",
            f"- feedback: `{json.dumps(fb, ensure_ascii=False)}`",
            "",
            f"근거: `{out_json.name}`",
            "",
            "비고: 1236(이번주) 미추첨 · 본 실행은 스테이징 회차 가상진행. λ/covering 재wire 없음.",
            "",
        ]
    )
    text = "\n".join(lines)
    out_md.write_text(text, encoding="utf-8")
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "pass": payload["pass"],
                "draw_no": draw_no,
                "ge3_best": ge3,
                "brains": [
                    {
                        "tag": b["brain_tag"],
                        "best": b["best_hits"],
                        "mean": b["mean_hits"],
                        "assemble": b.get("assemble_mode"),
                    }
                    for b in (scored.get("brains") or [])
                ],
                "warrant": w,
                "out": str(out_json.name),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
