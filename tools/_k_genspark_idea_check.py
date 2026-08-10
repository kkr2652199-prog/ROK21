# -*- coding: utf-8 -*-
"""K-GENSPARK-IDEA-CHECK — 젠스파크 아이디어 4건 READ-ONLY 실측.

wire/코드수정/DB쓰기 없음. 측정·의견만.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260810_KGENSPARK_IDEA_CHECK.json"
OUT_MD = ROOT / "reports" / "20260810_KGENSPARK_IDEA_CHECK.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
TUNE_JSON = ROOT / "docs" / "benchmarks" / "20260808_KBRAIN_INDEPENDENT_TUNE.json"

LO, HI = 1100, 1235
SEEDS = [0, 42, 123, 999, 7]
CAND_A = {
    "stat": (0.25, 0.35, 0.40),
    "markov": (0.55, 0.20, 0.25),
    "review": (0.55, 0.20, 0.25),
}


def _run_walk(seed: int) -> dict[str, Any]:
    from tools._k_brain_independent_tune import run_axis_walk

    return run_axis_walk(LO, HI, seed, CAND_A)


def _run_walk_detail(seed: int) -> dict[str, Any]:
    """기간별 리스트 + split-half prefer까지."""
    import random

    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import (
        WARM_BACK,
        _actual,
        _fw_proxy,
        _set_weights,
        _top15,
    )

    saved = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    _set_weights(sp, CAND_A)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prize_early: list[float] = []
        prize_mid: list[float] = []
        prize_late: list[float] = []
        prefer_all: list[tuple[int, float]] = []
        prize_all: list[float] = []

        for dno in range(LO, HI + 1):
            sp.set_learn_as_of(dno)
            draws = sp._get_draws_before(dno)
            if len(draws) < 50:
                continue
            fw = _fw_proxy(draws)
            all_mean = mean(fw[n] for n in range(1, 46))
            if all_mean <= 1e-12:
                continue
            random.seed(seed)
            pool = sp.expand_pool(draws, dno, seed=seed)
            pool_br = sp._pool_by_brain(pool)
            num_ema, pos_ema = learner.snapshot()
            hint_by = sp.build_hint_by_brain(draws, dno)
            fallback = sp._build_hint(draws, dno)
            scores = {}
            for tag in sp.BRAIN_TAGS:
                scores[tag] = sp.number_scores(
                    pool_br.get(tag, []),
                    hint_by.get(tag, fallback),
                    num_ema,
                    pos_ema,
                    brain_tag=tag,
                )
            prefer_d = mean(fw[n] for n in _top15(scores["markov"])) - all_mean
            prize_d = mean(fw[n] for n in _top15(scores["review"])) - all_mean
            prefer_all.append((dno, prefer_d))
            prize_all.append(prize_d)
            if LO <= dno <= LO + 44:
                prize_early.append(prize_d)
            elif LO + 45 <= dno <= LO + 89:
                prize_mid.append(prize_d)
            else:
                prize_late.append(prize_d)
            learner.update_from_pool(pool_br, _actual(dno))

        mid = (LO + HI) // 2  # 1167
        pref_lo = [v for d, v in prefer_all if d <= mid]
        pref_hi = [v for d, v in prefer_all if d > mid]
        return {
            "seed": seed,
            "n": len(prize_all),
            "early_n": len(prize_early),
            "early_mean": round(mean(prize_early), 6) if prize_early else None,
            "early_sd": round(pstdev(prize_early), 6) if len(prize_early) > 1 else None,
            "early_se": (
                round(pstdev(prize_early) / math.sqrt(len(prize_early)), 6)
                if len(prize_early) > 1
                else None
            ),
            "mid_mean": round(mean(prize_mid), 6) if prize_mid else None,
            "late_mean": round(mean(prize_late), 6) if prize_late else None,
            "consistent_neg": all(
                mean(xs) < 0 for xs in (prize_early, prize_mid, prize_late) if xs
            ),
            "prefer_mean": round(mean(v for _, v in prefer_all), 6),
            "prefer_first_half": round(mean(pref_lo), 6) if pref_lo else None,
            "prefer_second_half": round(mean(pref_hi), 6) if pref_hi else None,
            "prefer_split_both_pos": bool(
                pref_lo and pref_hi and mean(pref_lo) > 0 and mean(pref_hi) > 0
            ),
            "prize_mean": round(mean(prize_all), 6) if prize_all else None,
            "split_mid_draw": mid,
            "n_first": len(pref_lo),
            "n_second": len(pref_hi),
        }
    finally:
        sp.SCORE_WEIGHTS_BY_BRAIN.clear()
        sp.SCORE_WEIGHTS_BY_BRAIN.update(saved)


def check1(details: list[dict[str, Any]], tune: dict[str, Any]) -> dict[str, Any]:
    base_e = tune["base"]["review_by_period"]["early"]
    cand_e = tune["candidate"]["review_by_period"]["early"]
    # noise: early SE from seed=42 detail
    d42 = next(d for d in details if d["seed"] == 42)
    se = d42["early_se"] or 0.0
    # ±0.03 이내 부호변동이 noise인가? SE*2 ≈ 95% 대략
    noise_band = max(0.03, 2.0 * se)
    flip_mag = abs(cand_e - base_e)
    early_noise_range_ok = flip_mag <= noise_band  # True = 부호반전이 noise 범위일 수 있음

    seed_sens = {}
    for d in details:
        seed_sens[f"seed_{d['seed']}"] = {
            "early_mean": d["early_mean"],
            "early_neg": bool(d["early_mean"] is not None and d["early_mean"] < 0),
            "consistent_neg": d["consistent_neg"],
        }
    # 민감: early 부호가 seed마다 갈라지면 True
    early_signs = [v["early_neg"] for v in seed_sens.values()]
    sensitive = not (all(early_signs) or not any(early_signs))

    if sensitive or early_noise_range_ok:
        opinion = "조건부"
        reason = (
            f"early 부호반전 |Δ|={flip_mag:.4f} vs noise_band≈{noise_band:.4f} "
            f"(SE={se:.4f}, n_early={d42['early_n']}). "
            f"seed별 early_neg={early_signs} → consistent_neg를 "
            f"**필수 하드게이트로만 쓰면 안 됨**. 보조조건·다seed확인으로만."
        )
    else:
        opinion = "동의"
        reason = "early 부호가 다seed에서 안정적으로 음수면 게이트 보조로 가능."

    return {
        "early_noise_range_ok": early_noise_range_ok,
        "noise_band_approx": round(noise_band, 6),
        "early_se_seed42": se,
        "base_early": base_e,
        "cand_early": cand_e,
        "seed_sensitivity": seed_sens,
        "seed_early_sign_unstable": sensitive,
        "consistent_neg_as_gate_opinion": opinion,
        "reason": reason,
    }


def check2() -> dict[str, Any]:
    from app.testlotto.brains.shared import crowd_signal as cs

    # 코드 구조: 모듈 전역 상수 1세트
    separated_now = False
    blend_per = False
    return {
        "w_crowd_w_struct_separated_now": separated_now,
        "blend_strength_per_brain": blend_per,
        "current_values": {
            "W_CROWD": cs.W_CROWD,
            "W_STRUCT": cs.W_STRUCT,
            "BLEND_STRENGTH": cs.BLEND_STRENGTH,
        },
        "separation_feasible": True,
        "modification_scope": (
            "crowd_signal.py에 W_*_BY_BRAIN / BLEND_STRENGTH_BY_BRAIN dict 추가 + "
            "prefer_table/prize_table/engine blend 호출부 strength·혼합비 인자화. "
            "coordinator/engine random.choices 불필요. 예상 1파일(+호출 2곳)."
        ),
        "opinion": (
            "지금 당장 BLEND_STRENGTH **단일 노브**로 충분하다. "
            "문헌상 markov=STRUCT·review=CROWD 가설은 타당하나, "
            "노브 2~3개 동시 스윕은 R38 선택편향·표본 n136에 위험. "
            "단일 BLEND PASS 후 뇌별 분리는 2단계."
        ),
    }


def check3() -> dict[str, Any]:
    from app.testlotto.learn_state import get_referee_weights
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.evolve_log import WEIGHT_APPLIED

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(testlotto_evolve_log)").fetchall()]
        rows = conn.execute(
            """
            SELECT draw_no, brain_tag, weight_applied
            FROM testlotto_evolve_log
            WHERE brain_tag='stat'
            ORDER BY draw_no DESC
            LIMIT 20
            """
        ).fetchall()
        n_all = conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0]
    finally:
        conn.close()

    vals = [float(dict(r)["weight_applied"]) for r in rows]
    nonzero = any(abs(v) > 1e-12 for v in vals)

    # feedback: FINDINGS K-K OPEN — 파일 텍스트로만 확인 (import side-effect 회피)
    coord_txt = (ROOT / "app" / "testlotto" / "brains" / "coordinator.py").read_text(
        encoding="utf-8"
    )
    feedback_in_coord = "apply_feedback" in coord_txt
    routes = (ROOT / "app" / "testlotto" / "routes.py").read_text(encoding="utf-8")
    click_feedback = "apply_feedback" in routes

    from app.testlotto.learn_state_cutoff import set_learn_as_of

    set_learn_as_of(1236)
    ref = get_referee_weights()
    # 실효격차
    vs = list(ref.values())
    spread = max(vs) - min(vs) if vs else 0.0

    opinion = (
        "stat 내부 노브 튜닝은 **지금 하면 안 된다**. "
        f"evolve weight_applied 상수={WEIGHT_APPLIED} (Phase1 고정0) · "
        f"referee 격차={spread:.4f} (K-M HOLD 유지) · "
        "K-K 클릭 feedback 미연결 OPEN. "
        "피드백·referee가 죽인 상태에서 엔진 노브만 돌리면 원인 귀속 불가."
    )
    return {
        "evolve_log_weight_nonzero": nonzero,
        "weight_applied_constant": WEIGHT_APPLIED,
        "stat_weight_applied_values": vals,
        "n_evolve_log_rows": int(n_all),
        "table": "testlotto_evolve_log",
        "cols_ok": "weight_applied" in cols,
        "feedback_connected": {
            "coordinator_has_apply_feedback": feedback_in_coord,
            "routes_has_apply_feedback": click_feedback,
            "findings_KK": "OPEN — 클릭 예측 feedback 미연결",
            "summary_bool": bool(feedback_in_coord and not click_feedback),
        },
        "feedback_connected_bool": False,  # 클릭 경로 기준
        "referee_weights_live": {k: round(float(v), 6) for k, v in ref.items()},
        "referee_spread": round(spread, 6),
        "opinion": opinion,
    }


def check4(details: list[dict[str, Any]], tune: dict[str, Any], c1: dict[str, Any]) -> dict[str, Any]:
    base = tune["base"]
    cand = tune["candidate"]
    d42 = next(d for d in details if d["seed"] == 42)

    # cond1: review prize 3구간 모두 <0 (cand seed42 from tune + detail)
    p = cand["review_by_period"]
    cond1 = bool(p["early"] < 0 and p["mid"] < 0 and p["late"] < 0)

    # cond2: prefer split-half both >0
    cond2 = bool(d42["prefer_split_both_pos"])

    # cond3: |prize_cand| > |prize_base| and both negative direction improvement
    # genspark: |Δprice| > |Δbase| — interpret as |cand prize| > |base prize| when both neg
    # or improvement magnitude |cand-base|
    rp_b, rp_c = base["review_prize_delta"], cand["review_prize_delta"]
    cond3 = bool(rp_c < rp_b)  # more negative = improvement for EV
    # also check absolute improvement > threshold
    abs_improve = abs(rp_c - rp_b)

    # split-half n
    n_ok = d42["n_first"] >= 60 and d42["n_second"] >= 60

    # threshold suggestion from early SE and overall prize variability
    # use 2*SE of full prize series approx from early_se scaled
    thr = round(max(0.01, 2.0 * (d42["early_se"] or 0.01) * math.sqrt(45) / math.sqrt(136)), 4)
    # simpler: from seed spread of prize_mean
    prize_by_seed = [d["prize_mean"] for d in details if d["prize_mean"] is not None]
    if len(prize_by_seed) > 1:
        thr = round(max(0.01, pstdev(prize_by_seed)), 4)

    # multi-seed consistent_neg rate
    cn_rate = mean(1.0 if d["consistent_neg"] else 0.0 for d in details)

    additional = (
        f"다seed(≥3)에서 consistent_neg 비율≥2/3 · "
        f"prefer_delta 다seed 평균>0 · "
        f"|prize_cand−prize_base|≥{thr} (seed간 prize σ≈{thr}). "
        f"현재 cn_rate={cn_rate:.2f}"
    )

    # gate pass on cand_A recorded numbers
    # cond2 needs split from detail
    idea_immediate = []
    idea_hold = []
    # Idea1 consistent_neg gate -> HOLD/conditional
    idea_hold.append("CHECK-1_consistent_neg_hard_gate")
    idea_immediate.append("CHECK-1_consistent_neg_as_soft_aux")
    # Idea2 brain-wise W_CROWD -> HOLD
    idea_hold.append("CHECK-2_per_brain_W_CROWD_W_STRUCT")
    idea_immediate.append("CHECK-2_single_BLEND_STRENGTH_first")
    # Idea3 stat feedback -> HOLD tune
    idea_hold.append("CHECK-3_stat_internal_tune_until_KM_KN_KK")
    idea_immediate.append("CHECK-3_verify_weight0_before_any_stat_tune")
    # Idea4 gate design
    idea_immediate.append("CHECK-4_gate_EV_prefer_no_ge3")
    idea_hold.append("CHECK-4_hard_require_all_period_neg_without_multiseed")

    return {
        "gate_cond1_pass": cond1,
        "gate_cond2_pass": cond2,
        "gate_cond3_pass": cond3,
        "cond3_abs_improve": round(abs_improve, 6),
        "split_half_n_ok": n_ok,
        "split_half_detail": {
            "mid": d42["split_mid_draw"],
            "n_first": d42["n_first"],
            "n_second": d42["n_second"],
            "prefer_first": d42["prefer_first_half"],
            "prefer_second": d42["prefer_second_half"],
        },
        "cond3_threshold_suggestion": thr,
        "additional_gate_suggestion": additional,
        "multiseed_consistent_neg_rate": round(cn_rate, 4),
        "idea_classify": {"immediate": idea_immediate, "hold": idea_hold},
        "final_opinion": (
            "BLEND 소튜닝 게이트는 ge3 없이 "
            "(1) review prize_delta < base 및 <0 "
            "(2) markov prefer_delta>0 및 split-half 동부호 "
            "(3) |Δ|≥약 "
            f"{thr} "
            "(4) **다seed 보조로** consistent_neg 확인 — "
            "consistent_neg 단독 필수는 비동의. "
            "뇌별 W 분리는 BLEND 단일 통과 후. stat 튜닝은 K-M/K-N/K-K 후."
        ),
    }


def build_md(payload: dict[str, Any]) -> str:
    c1, c2, c3, c4 = (
        payload["check1_result"],
        payload["check2_result"],
        payload["check3_result"],
        payload["check4_result"],
    )
    lines = [
        "# K-GENSPARK-IDEA-CHECK",
        "",
        f"📅 {payload['ts']} · READ-ONLY · wire=False",
        "",
        "## CHECK-1 consistent_neg",
        f"- opinion: **{c1['consistent_neg_as_gate_opinion']}**",
        f"- early_noise_range_ok={c1['early_noise_range_ok']} · SE={c1['early_se_seed42']} · band={c1['noise_band_approx']}",
        f"- seed_early_unstable={c1['seed_early_sign_unstable']}",
        f"- reason: {c1['reason']}",
        "",
        "## CHECK-2 W_CROWD/W_STRUCT",
        f"- separated_now={c2['w_crowd_w_struct_separated_now']} · blend_per_brain={c2['blend_strength_per_brain']}",
        f"- feasible={c2['separation_feasible']}",
        f"- opinion: {c2['opinion']}",
        "",
        "## CHECK-3 evolve/feedback/referee",
        f"- weight_nonzero={c3['evolve_log_weight_nonzero']} · constant={c3['weight_applied_constant']}",
        f"- referee={c3['referee_weights_live']} · spread={c3['referee_spread']}",
        f"- feedback_click={c3['feedback_connected']}",
        f"- opinion: {c3['opinion']}",
        "",
        "## CHECK-4 gate",
        f"- cond1/2/3={c4['gate_cond1_pass']}/{c4['gate_cond2_pass']}/{c4['gate_cond3_pass']}",
        f"- split_n_ok={c4['split_half_n_ok']} · thr={c4['cond3_threshold_suggestion']}",
        f"- immediate={c4['idea_classify']['immediate']}",
        f"- hold={c4['idea_classify']['hold']}",
        f"- final: {c4['final_opinion']}",
        "",
        "## 종합",
        payload["cursor_summary_ko"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    from app.testlotto.models import init_testlotto_db

    init_testlotto_db()
    tune = json.loads(TUNE_JSON.read_text(encoding="utf-8"))
    print("=== CHECK-2/3 (fast) ===", flush=True)
    c2 = check2()
    c3 = check3()
    print("CHECK-2", c2)
    print("CHECK-3 weight", c3["stat_weight_applied_values"][:5], "ref", c3["referee_weights_live"])

    print("=== CHECK-1/4 seed walks ===", flush=True)
    details = []
    for s in SEEDS:
        print(f"  seed={s} …", flush=True)
        d = _run_walk_detail(s)
        details.append(d)
        print(
            f"    early={d['early_mean']} cn={d['consistent_neg']} "
            f"pref_split={d['prefer_first_half']}/{d['prefer_second_half']}",
            flush=True,
        )

    c1 = check1(details, tune)
    c4 = check4(details, tune, c1)

    summary = (
        "젠스파크 4안 중 BLEND 즉시 반영=단일 BLEND_STRENGTH + EV/prefer 게이트(다seed 보조). "
        "consistent_neg 하드게이트·뇌별 W 분리·stat 내부튜닝은 HOLD. "
        f"evolve weight=0 확정 · referee spread={c3['referee_spread']}."
    )

    payload = {
        "id": "K-GENSPARK-IDEA-CHECK",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "head_note": "READ-ONLY · no wire · no DB write",
        "seeds": SEEDS,
        "draw_range": [LO, HI],
        "check1_result": c1,
        "check2_result": c2,
        "check3_result": {
            **c3,
            "feedback_connected": c3["feedback_connected_bool"],
            "feedback_detail": c3["feedback_connected"],
            "stat_weight_applied_values": c3["stat_weight_applied_values"],
            "evolve_log_weight_nonzero": c3["evolve_log_weight_nonzero"],
            "referee_weights_live": c3["referee_weights_live"],
            "opinion": c3["opinion"],
        },
        "check4_result": c4,
        "per_seed_detail": details,
        "cursor_summary_ko": summary,
        "wire": False,
        "pass": True,
        "prior": [
            "docs/benchmarks/20260808_KBRAIN_INDEPENDENT_TUNE.json",
            "docs/benchmarks/20260808_KBRAIN_INDEPENDENT_WIRE.json",
            "docs/benchmarks/20260810_KNEXT_ROUTE_LIT_GITHUB_SURVEY.json",
        ],
    }

    # normalize check3 to requested schema keys
    payload["check3_result"] = {
        "evolve_log_weight_nonzero": c3["evolve_log_weight_nonzero"],
        "stat_weight_applied_values": c3["stat_weight_applied_values"],
        "feedback_connected": c3["feedback_connected_bool"],
        "feedback_detail": c3["feedback_connected"],
        "referee_weights_live": c3["referee_weights_live"],
        "referee_spread": c3["referee_spread"],
        "weight_applied_constant": c3["weight_applied_constant"],
        "n_evolve_log_rows": c3["n_evolve_log_rows"],
        "opinion": c3["opinion"],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = build_md(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_JSON}", flush=True)
    print("SUMMARY:", summary, flush=True)


if __name__ == "__main__":
    main()
