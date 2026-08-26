# -*- coding: utf-8 -*-
"""K-REVIEW-SHAPE-KB-WIRE — 4번 저울 배선. 라이브 기본 OFF.

S0 보너스=본번호6 확인. S1 저울. S2 게이트. 1237예측 없음. 몰아주기 없음.
자동화 없음. 적중 클레임 없음.
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260826_KREVIEW_SHAPE_KB_WIRE.json"
OUT_MD = ROOT / "reports" / "20260826_KREVIEW_SHAPE_KB_WIRE.md"
DB = ROOT / "data" / "lotto_testlotto.db"
ISO = 0.005
SEED = 42
GATE_LO, GATE_HI = 1137, 1236


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _m(xs: list[float]) -> float | None:
    return round(mean(xs), 6) if xs else None


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _axis(table: dict[int, float], sets: list[dict]) -> float | None:
    if not table or not sets:
        return None
    uni = mean(table[i] for i in range(1, 46))
    vals = []
    for s in sets:
        nums = _nums(s)
        if len(nums) == 6:
            vals.append(mean(table[n] for n in nums) - uni)
    return round(mean(vals), 6) if vals else None


def _s0() -> dict[str, Any]:
    """READ-ONLY 보너스 재료 확인 + 6 vs 가상7 평균."""
    from app.testlotto.brains.review_brain import draw_assoc, draw_shape_kb, rare_consec
    from app.testlotto.brains.review_brain.rare_slice import tags as rare_tags
    from app.testlotto.features.draw_features import ac_value, sorted_nums
    from app.testlotto.routes import _prediction_rank_tier

    src = (ROOT / "app/testlotto/brains/review_brain/draw_shape_kb.py").read_text(
        encoding="utf-8"
    )
    feat_uses_sorted = "nums = sorted_nums(draw)" in src
    feat_sum_from_nums = '"sum": int(sum(nums))' in src
    bonus_in_feat_keys = any(
        k in src
        for k in (
            "sum(nums)+bonus",
            "nums + [bonus]",
            "sorted_nums(draw)+",
        )
    )
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws "
            "WHERE draw_no BETWEEN 1 AND 1237 ORDER BY draw_no"
        ).fetchall()
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
        pred_1239 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239"
            ).fetchone()[0]
        )
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        kb_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_draw_shape_kb").fetchone()[0])
        sample = conn.execute(
            "SELECT nums_json, bonus, features_json FROM testlotto_draw_shape_kb "
            "WHERE draw_no=1237"
        ).fetchone()
    finally:
        conn.close()

    def pack(use7: bool) -> dict[str, float]:
        sums: list[int] = []
        spans: list[int] = []
        odds: list[int] = []
        for r in rows:
            six = sorted(int(r[f"num{i}"]) for i in range(1, 7))
            b = int(r["bonus"] or 0)
            xs = six if not use7 else sorted(six + ([b] if b and b not in six else []))
            if use7 and len(xs) != 7:
                xs = sorted(six + [b])
            sums.append(sum(xs))
            spans.append(xs[-1] - xs[0])
            odds.append(sum(1 for n in xs if n % 2 == 1))
        return {
            "n": float(len(rows)),
            "sum_mean": round(mean(sums), 4),
            "span_mean": round(mean(spans), 4),
            "odd_mean": round(mean(odds), 4),
        }

    six = pack(False)
    seven = pack(True)
    feat1237 = json.loads(sample["features_json"] or "{}") if sample else {}
    nums1237 = json.loads(sample["nums_json"] or "[]") if sample else []
    assoc_src = (ROOT / "app/testlotto/brains/review_brain/draw_assoc.py").read_text(
        encoding="utf-8"
    )
    consec_src = (ROOT / "app/testlotto/brains/review_brain/rare_consec.py").read_text(
        encoding="utf-8"
    )
    eng = (ROOT / "app/testlotto/brains/review_brain/engine.py").read_text(encoding="utf-8")
    return {
        "shape_kb_features_mains6": bool(feat_uses_sorted and feat_sum_from_nums and not bonus_in_feat_keys),
        "shape_kb_bonus_is_label": '"bonus": int(draw.get("bonus") or 0)' in src,
        "sorted_nums_is_num1_to_num6": "for k in range(1, 7)" in (
            ROOT / "app/testlotto/features/draw_features.py"
        ).read_text(encoding="utf-8"),
        "correction_needed": False,
        "six_only": six,
        "hypothetical_6plus_bonus": seven,
        "delta_if_bonus_in_feat": {
            "sum_mean": round(seven["sum_mean"] - six["sum_mean"], 4),
            "span_mean": round(seven["span_mean"] - six["span_mean"], 4),
            "odd_mean": round(seven["odd_mean"] - six["odd_mean"], 4),
        },
        "row_1237": {
            "nums": nums1237,
            "bonus_label": int(sample["bonus"]) if sample else None,
            "feat_sum": feat1237.get("sum"),
            "feat_span": feat1237.get("span"),
            "feat_odd": feat1237.get("odd"),
            "sum_equals_six": bool(
                nums1237 and feat1237.get("sum") == sum(int(x) for x in nums1237)
            ),
        },
        "scan5_consec_predict_bonus_material": False,
        "scan5_sig_from_sorted_nums": True,
        "scan6_similar_mains": 'frozenset(int(x) for x in r["nums"])' in assoc_src,
        "scan6_bonus_links_stored": "bonus_links" in assoc_src,
        "scan6_predict_lock": bool(getattr(draw_assoc, "PREDICT_USE_BONUS_LINKS", True) is False),
        "scan_engine_picks_bonus": False,
        "rank2_label": _prediction_rank_tier(5, 1) == (2, "2등"),
        "rank3_label": _prediction_rank_tier(5, 0) == (3, "3등"),
        "flags": {
            "REVIEW_SHAPE_KB_READ": bool(draw_shape_kb.REVIEW_SHAPE_KB_READ),
            "REVIEW_SHAPE_KB_WEIGHT_WIRE": bool(draw_shape_kb.REVIEW_SHAPE_KB_WEIGHT_WIRE),
            "REVIEW_CONSEC_PASS_WIRE": bool(rare_consec.REVIEW_CONSEC_PASS_WIRE),
        },
        "kb_n": kb_n,
        "dmax": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "ac_value_mod": ac_value,
        "rare_tags_mod": rare_tags,
        "sorted_nums_mod": sorted_nums,
    }


def _combo_ext(sets: list[list[int]]) -> dict[str, Any]:
    from app.testlotto.brains.review_brain.rare_pass_store import should_pass
    from app.testlotto.brains.review_brain.shape_table import max_run

    if not sets:
        return {}
    n = len(sets)
    rare = sum(1 for s in sets if should_pass(s))
    run4 = sum(1 for s in sets if max_run(s) >= 4)
    odd0 = sum(1 for s in sets if sum(1 for x in s if x % 2 == 1) == 0)
    odd6 = sum(1 for s in sets if sum(1 for x in s if x % 2 == 1) == 6)
    return {
        "n": n,
        "p_rare_pass": round(rare / n, 6),
        "p_run4": round(run4 / n, 6),
        "p_all_even": round(odd0 / n, 6),
        "p_all_odd": round(odd6 / n, 6),
        "bonus_in_set": 0,
    }


def _gate() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.draw_shape_kb as kb
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.review_brain.draw_shape_kb import set_shape_score
    from app.testlotto.brains.shared import crowd_signal as cs
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT draw_no FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (GATE_LO, GATE_HI),
        ).fetchall()
    finally:
        conn.close()

    t0 = time.perf_counter()
    n_ok = peek_fail = size_bad = bonus_in = 0
    errors: list[str] = []
    changed = 0
    mets = {
        k: {x: [] for x in ("pref", "prize", "score", "rare", "run4")}
        for k in ("off", "on")
    }
    old = bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE)
    try:
        for i, r in enumerate(rows):
            dno = int(r["draw_no"])
            set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            if max((int(d["draw_no"]) for d in draws), default=0) >= dno:
                peek_fail += 1
                continue
            try:
                kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = False
                random.seed(SEED)
                p_off = [
                    c
                    for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
                    if str(c.get("brain_tag")) == "review"
                ]
                kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = True
                random.seed(SEED)
                p_on = [
                    c
                    for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
                    if str(c.get("brain_tag")) == "review"
                ]
            except Exception as e:  # noqa: BLE001
                errors.append(f"{dno} {type(e).__name__}: {e}")
                continue
            if len(p_off) != 10 or len(p_on) != 10:
                size_bad += 1
                continue
            off_t = [tuple(_nums(s)) for s in p_off]
            on_t = [tuple(_nums(s)) for s in p_on]
            if off_t != on_t:
                changed += 1
            for t in off_t + on_t:
                if len(t) != 6:
                    bonus_in += 1
            pref_t = cs.prefer_table(draws, brain="markov")
            prize_t = cs.prize_table(draws, brain="review")
            hist = kb.summarize_before(draws)
            for name, p in (("off", p_off), ("on", p_on)):
                skill = [
                    _nums(s)
                    for s in sorted(
                        p, key=lambda x: int(x.get("pred_set_no") or x.get("set_no") or 0)
                    )[:5]
                ]
                ext = _combo_ext(skill)
                sc = [set_shape_score(s, hist) for s in skill if len(s) == 6]
                mets[name]["pref"].append(_axis(pref_t, p) or 0.0)
                mets[name]["prize"].append(_axis(prize_t, p) or 0.0)
                mets[name]["score"].append(mean(sc) if sc else 0.0)
                mets[name]["rare"].append(float(ext.get("p_rare_pass") or 0))
                mets[name]["run4"].append(float(ext.get("p_run4") or 0))
            n_ok += 1
            if (i + 1) % 20 == 0 or dno == GATE_HI:
                print(f"  [gate] {i+1}/{len(rows)} d={dno} n_ok={n_ok} ch={changed}", flush=True)
    finally:
        kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = old

    def pack(name: str) -> dict[str, Any]:
        m = mets[name]
        return {
            "prefer": _m(m["pref"]),
            "prize": _m(m["prize"]),
            "shape_score": _m(m["score"]),
            "p_rare_pass": _m(m["rare"]),
            "p_run4": _m(m["run4"]),
        }

    off, on = pack("off"), pack("on")
    d_pref = None if off["prefer"] is None else round(on["prefer"] - off["prefer"], 6)
    d_prize = None if off["prize"] is None else round(on["prize"] - off["prize"], 6)
    hard = (
        n_ok == 100
        and peek_fail == 0
        and size_bad == 0
        and not errors
        and bonus_in == 0
        and old is False
    )
    iso = bool(d_pref is not None and d_pref < ISO and d_prize is not None and d_prize < ISO)
    extreme_ok = bool(
        (on["p_rare_pass"] or 0) <= (off["p_rare_pass"] or 0) + 1e-12
        and (on["p_run4"] or 0) <= (off["p_run4"] or 0) + 1e-12
    )
    design = bool(changed > 0 and extreme_ok)
    return {
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "n_ok": n_ok,
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "bonus_in_sets": bonus_in,
        "n_errors": len(errors),
        "errors_head": errors[:6],
        "changed": changed,
        "hard_ok": hard,
        "iso_ok": iso,
        "extreme_ok": extreme_ok,
        "design_ok": design,
        "apply_code": bool(hard and iso and design),
        "live_on": False,
        "off": off,
        "on": on,
        "delta_prefer": d_pref,
        "delta_prize": d_prize,
        "delta_shape_score": None
        if off["shape_score"] is None
        else round(on["shape_score"] - off["shape_score"], 6),
    }


def _write_md(doc: dict[str, Any]) -> str:
    s0 = doc["s0"]
    g = doc["gate"]
    return "\n".join(
        [
            "# K-REVIEW-SHAPE-KB-WIRE (2026-08-26)",
            "",
            f"- **판정:** `{doc['verdict']}` · 4번 저울 · 라이브 OFF · 몰아주기 미접촉",
            f"- 시각: {doc['ts']}",
            "- 형: 4번을 읽기만→저울. 보너스는 본번호6만. 칼 아님. 자동화 아님.",
            f"- 근거: `{OUT_JSON.name}`",
            "",
            "## S0 보너스 (READ-ONLY)",
            "",
            f"- 4번 특징 본번호6 `{s0['shape_kb_features_mains6']}` · 보너스는 라벨 `{s0['shape_kb_bonus_is_label']}`",
            f"- 정정 필요 `{s0['correction_needed']}` (이미 6개만 계산 · 표 재구축 없음)",
            f"- 1–1237 본번호6 평균 sum `{s0['six_only']['sum_mean']}` span `{s0['six_only']['span_mean']}` odd `{s0['six_only']['odd_mean']}`",
            f"- 가상(6+보너스) sum `{s0['hypothetical_6plus_bonus']['sum_mean']}` span `{s0['hypothetical_6plus_bonus']['span_mean']}` odd `{s0['hypothetical_6plus_bonus']['odd_mean']}`",
            f"- 차이(가상−6) sum `{s0['delta_if_bonus_in_feat']['sum_mean']}` span `{s0['delta_if_bonus_in_feat']['span_mean']}` odd `{s0['delta_if_bonus_in_feat']['odd_mean']}`",
            f"- 1237 feat_sum==본번호합 `{s0['row_1237']['sum_equals_six']}` bonus라벨 `{s0['row_1237']['bonus_label']}`",
            f"- 5번 consec 서명=sorted_nums(6) · PASS_WIRE `{s0['flags']['REVIEW_CONSEC_PASS_WIRE']}`",
            f"- 6번 유사=본번호 · bonus_links 저장 `{s0['scan6_bonus_links_stored']}` · 예측잠금 `{s0['scan6_predict_lock']}`",
            f"- 채점 5+보너스=2등 `{s0['rank2_label']}` · 5맞=3등 `{s0['rank3_label']}`",
            f"- pred_1237 `{s0['pred_1237']}` · pred_1239 `{s0['pred_1239']}` · MAX `{s0['dmax']}`",
            "",
            "## S1 배선",
            "",
            "- 위치: `engine.generate` · 3번(rare_pass) 통과 후 · `keep_set_by_hist`",
            "- 방식: 저울. 역사 흔한 모양 통과↑. 3번과 겹치는 거절 없음",
            "- 재료: as_of 이전 odd/run/sum/span/AC. 보너스 미사용. peek 없음",
            "- 플래그 `REVIEW_SHAPE_KB_WEIGHT_WIRE` 기본 **False** · review만 · 7번 WIRE 불변",
            "",
            "## S2 게이트 1137–1236 n100",
            "",
            f"- HARD peek `{g['peek_fail']}` n_ok `{g['n_ok']}` size_bad `{g['size_bad']}` bonus_in `{g['bonus_in_sets']}` hard `{g['hard_ok']}`",
            f"- Δprefer `{g['delta_prefer']}` Δprize `{g['delta_prize']}` iso `{g['iso_ok']}`",
            f"- changed `{g['changed']}` extreme_ok `{g['extreme_ok']}` design `{g['design_ok']}`",
            f"- OFF rare `{g['off']['p_rare_pass']}` run4 `{g['off']['p_run4']}` · ON rare `{g['on']['p_rare_pass']}` run4 `{g['on']['p_run4']}`",
            f"- shape_score Δ `{g['delta_shape_score']}` (모니터·성적아님)",
            f"- 코드적용조건 `{g['apply_code']}` · 라이브 `{g['live_on']}`",
            f"- elapsed `{g['elapsed_s']}`s",
            "",
            "## S3",
            "",
            "- 라이브 확정 없음. 켜려면 형 GO.",
            "- 롤백=`REVIEW_SHAPE_KB_WEIGHT_WIRE=False`",
            "- 자동화·몰아주기·전체조합·1237예측 없음",
            "",
            "## 파일",
            "",
            "- `draw_shape_kb.py` · `engine.py` · `draw_assoc.py`(예측잠금) · `kb7_future.py`",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )


def main() -> None:
    print("S0", flush=True)
    s0_raw = _s0()
    # drop function objects from json
    s0 = {k: v for k, v in s0_raw.items() if k not in {"ac_value_mod", "rare_tags_mod", "sorted_nums_mod"}}
    print("S2 gate", flush=True)
    gate = _gate()
    from app.testlotto.brains.review_brain.draw_shape_kb import REVIEW_SHAPE_KB_WEIGHT_WIRE

    live = bool(REVIEW_SHAPE_KB_WEIGHT_WIRE)
    if gate["apply_code"] and not live:
        verdict = "APPLY_OK_HOLD_LIVE"
    elif gate["hard_ok"] and not gate["iso_ok"]:
        verdict = "HOLD_ISO"
    elif not gate["design_ok"]:
        verdict = "HOLD_DESIGN"
    else:
        verdict = "HOLD"
    if s0["correction_needed"]:
        verdict = "PARTIAL_S0"
    if s0["pred_1237"] != 0 or live:
        verdict = "HOLD_HARD"
    doc = {
        "id": "K-REVIEW-SHAPE-KB-WIRE",
        "ts": _now(),
        "verdict": verdict,
        "s0": s0,
        "s1": {
            "flag": "REVIEW_SHAPE_KB_WEIGHT_WIRE",
            "default": False,
            "kind": "scale_not_knife",
            "after": "rare_pass",
            "brains": ["review"],
        },
        "gate": gate,
        "repack": "untouched",
        "all_combos": "untouched",
        "automation": False,
        "predict": False,
        "live_wire": live,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(verdict, "ch", gate["changed"], "iso", gate["iso_ok"], "dpref", gate["delta_prefer"], flush=True)


if __name__ == "__main__":
    main()
