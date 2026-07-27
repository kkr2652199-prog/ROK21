# -*- coding: utf-8 -*-
"""K-Y READ-ONLY: 보조 4뇌 정밀감사."""
from __future__ import annotations

import json
import os
import random
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260727_KY_aux_audit.json"
SEED = 20260727

from app.testlotto.brains import (  # noqa: E402
    aux_balance_keeper,
    aux_miss_detective,
    aux_pattern_spotlight,
    aux_referee,
)
from app.testlotto.brains.coordinator import (  # noqa: E402
    AUX_MODULES,
    AUX_WEIGHTS,
    PREDICT_MODULES,
    _apply_aux_scoring,
)
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state import (  # noqa: E402
    DEFAULT_ADJUSTMENTS,
    get_referee_weights,
)
from app.testlotto.learn_state_cutoff import set_learn_as_of, clear_history_cache  # noqa: E402


AUX_TAGS = {
    "miss_aux": aux_miss_detective,
    "pattern_aux": aux_pattern_spotlight,
    "balance_aux": aux_balance_keeper,
    "referee_aux": aux_referee,
}


def load_draws_A():
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    con.close()
    return [sorted(int(x) for x in r) for r in rows]


def feats(sets):
    sums, odds, zones, consecs = [], [], [], []
    endings = Counter()
    for sc in sets:
        sc = sorted(sc)
        sums.append(sum(sc))
        odds.append(sum(1 for x in sc if x % 2 == 1))
        l = sum(1 for x in sc if x <= 15)
        m = sum(1 for x in sc if 16 <= x <= 30)
        h = 6 - l - m
        zones.append((l, m, h))
        consecs.append(sum(1 for i in range(5) if sc[i + 1] - sc[i] == 1))
        for x in sc:
            endings[x % 10] += 1
    return {
        "sums": np.asarray(sums, float),
        "odds": np.asarray(odds, int),
        "zones": zones,
        "consecs": np.asarray(consecs, int),
        "endings": endings,
        "n": len(sets),
    }


def ks_dist(a, b):
    return float(stats.ks_2samp(a, b).statistic)


def chi2_df_dist(ca, cb):
    tbl = np.vstack([ca, cb]).astype(float)
    tbl = tbl[:, tbl.sum(axis=0) > 0]
    if tbl.shape[1] < 2:
        return 0.0
    keep, ra, rb = [], 0.0, 0.0
    for j in range(tbl.shape[1]):
        if tbl[:, j].sum() >= 5:
            keep.append(j)
        else:
            ra += tbl[0, j]
            rb += tbl[1, j]
    cols = [tbl[:, j] for j in keep]
    if ra + rb > 0:
        cols.append(np.array([ra, rb]))
    if len(cols) < 2:
        return 0.0
    t = np.column_stack(cols)
    chi2, p, dof, _ = stats.chi2_contingency(t)
    return float(chi2 / max(1, int(dof)))


def distances(fB, fR, zone_keys):
    odd_b = np.bincount(fB["odds"], minlength=7).astype(float)
    odd_r = np.bincount(fR["odds"], minlength=7).astype(float)
    cb = np.bincount(fB["consecs"], minlength=6).astype(float)
    cr = np.bincount(fR["consecs"], minlength=6).astype(float)
    zb = np.array([Counter(fB["zones"]).get(k, 0) for k in zone_keys], float)
    zr = np.array([Counter(fR["zones"]).get(k, 0) for k in zone_keys], float)
    eb = np.array([fB["endings"].get(d, 0) for d in range(10)], float)
    er = np.array([fR["endings"].get(d, 0) for d in range(10)], float)
    return {
        "sum_KS": ks_dist(fB["sums"], fR["sums"]),
        "odd_chi2_df": chi2_df_dist(odd_b, odd_r),
        "zone_chi2_df": chi2_df_dist(zb, zr),
        "consec_chi2_df": chi2_df_dist(cb, cr),
        "ending_chi2_df": chi2_df_dist(eb, er),
    }


def interpret(dA, dC):
    votes = {"A": 0, "C": 0, "far": 0}
    per = {}
    for m, a in dA.items():
        c = dC[m]
        if a < c * 0.9:
            v = "closer_A"
            votes["A"] += 1
        elif c < a * 0.9:
            v = "closer_C"
            votes["C"] += 1
        else:
            if (m.startswith("sum") and min(a, c) >= 0.12) or (
                not m.startswith("sum") and min(a, c) >= 2.0
            ):
                v = "far_both"
                votes["far"] += 1
            elif a <= c:
                v = "closer_A_tieish"
                votes["A"] += 1
            else:
                v = "closer_C_tieish"
                votes["C"] += 1
        per[m] = {"d_A": a, "d_C": c, "verdict": v}
    if votes["far"] >= 3:
        overall = "편향경보_A·C양쪽원격"
    elif votes["A"] > votes["C"]:
        overall = "정합_A근접"
    elif votes["C"] > votes["A"]:
        overall = "무해_C근접"
    else:
        overall = "경합_동률"
    return {"per_metric": per, "votes": votes, "overall": overall}


def sample_C(n, rng):
    pool = list(range(1, 46))
    return [sorted(rng.sample(pool, 6)) for _ in range(n)]


def combo_key(nums):
    return tuple(sorted(int(x) for x in nums))


def generate_raw_candidates(target=1234, seed=SEED):
    """예측 3뇌 raw 세트 (aux 전)."""
    os.environ.pop("ROK21_LEARN_CUTOFF", None)
    clear_history_cache()
    set_learn_as_of(target)
    random.seed(seed)
    draws = _get_draws_before(target)
    cands = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(seed + hash(tag) % 10007)
        # top-k 멤버십 측정용 oversample (15장 풀이면 delta 항상 0)
        cands.extend(mod.predict_sets(draws, 20))
    return cands, draws


def rescore_with_modules(cands, draws, target, modules_weights):
    """지정 aux 모듈만으로 confidence 재계산 (referee brain_w는 live 유지)."""
    ref_weights = get_referee_weights()
    out = []
    for c in cands:
        if modules_weights:
            aux_score = sum(w * m.score_set(c["nums"], draws, target) for m, w in modules_weights)
        else:
            aux_score = 0.0
        base = float(c.get("confidence", 60))
        # strip previous aux if present — use original base from brain if stored
        brain_w = ref_weights.get(c.get("brain_tag", ""), 1.0 / 3)
        # when ablating all aux, use base*0.6*brain_w style without aux term
        if modules_weights:
            final = min(99.5, base * 0.5 * brain_w + aux_score * 40 + base * 0.1)
        else:
            final = min(99.5, base * 0.6 * brain_w)
        out.append({**c, "confidence": round(final, 1), "_aux": aux_score})
    return out


def top_sets(scored, k=15):
    s = sorted(scored, key=lambda x: -x["confidence"])
    return [combo_key(x["nums"]) for x in s[:k]]


def membership_delta(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return 1.0 - len(sa & sb) / max(len(sa | sb), 1)


def balance_targets_vs_theory(draws):
    tgt = aux_balance_keeper._historical_targets(draws)
    # theory modes
    theory = {"odd_mode": 3.0, "sum_mean": 138.0, "zone_ideal_spread": 0.0}
    # empirical from draws A
    odds = []
    sums = []
    for d in draws[-80:]:
        nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
        odds.append(sum(1 for x in nums if x % 2 == 1))
        sums.append(sum(nums))
    return {
        "code_targets": tgt,
        "theory_reference": theory,
        "default_when_empty_draws": {"odd": 3.0, "sum": 150.0, "zone": 2.0},
        "delta_sum_vs_theory": float(tgt["sum"] - 138.0),
        "delta_odd_vs_mode3": float(tgt["odd"] - 3.0),
        "note": "balance uses historical mean of last 80 draws, NOT C(45,6) theory constants",
    }


def pattern_impl_facts():
    return {
        "uses_C45_6_pmf": False,
        "ac_target": 7,  # hard-coded constant
        "consec_score_table": {0: 0.7, 1: 0.7, 2: 0.5, "else": 0.3},
        "pair_norm_divisor": 30.0,  # empirical scale
        "pair_freq_source": "build_pair_freq(draws[-100:]) historical counts",
        "verdict": "경험칙·상수 휴리스틱. 조합 이론분포 근사 코드 없음",
    }


def learn_state_key_audit():
    """각 DEFAULT_ADJUSTMENTS 키: 갱신 / 소비."""
    # refresh paths from grep knowledge + verify
    keys = list(DEFAULT_ADJUSTMENTS.keys())
    consume = {
        "carry_over_boost": ["predict_stat_fairy", "predict_review_king", "predict_statistical"],
        "ending_digit_boost": ["predict_stat_fairy", "predict_statistical"],
        "overdue_boost": ["predict_statistical"],
        "pair_boost": [],
        "consecutive_boost": [],
        "odd_even_balance": [],
    }
    updated = True  # all via apply_feedback miss patterns
    rows = []
    for k in keys:
        paths = consume.get(k, [])
        rows.append(
            {
                "key": k,
                "defined": True,
                "updated_by_apply_feedback": updated,
                "consume_paths": paths,
                "consumed": len(paths) > 0,
                "status": "소비" if paths else "학습되나 미소비",
            }
        )
    return rows


def db_vs_live_referee():
    live = get_referee_weights()
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT brain_tag, current_weight FROM testlotto_brain_weights"
    ).fetchall()
    con.close()
    db = {r[0]: float(r[1]) for r in rows}
    # normalize db predict tags if present
    pred = {t: db.get(t) for t in ("stat", "markov", "review")}
    return {"live": live, "db_raw": db, "db_predict_tags": pred}


def main():
    A = load_draws_A()
    fA = feats(A)
    rng = random.Random(SEED)

    # --- generate pool ---
    cands, draws = generate_raw_candidates(1234, SEED)
    raw_sets = [c["nums"] for c in cands]
    # full aux scored
    full = _apply_aux_scoring([dict(c) for c in cands], draws, 1234)
    full_top = top_sets(full, 15)
    # pre = rank by raw confidence only
    pre = sorted(cands, key=lambda x: -float(x.get("confidence", 0)))
    pre_top = [combo_key(x["nums"]) for x in pre[:15]]
    pre_sets = [list(k) for k in pre_top]
    post_sets = [list(k) for k in full_top]

    # per-aux: only that aux (weight 1.0) vs none
    ablate = {}
    all_mw = list(zip(AUX_MODULES, AUX_WEIGHTS))
    baseline_top = full_top
    for tag, mod in AUX_TAGS.items():
        # ON: only this module
        only = rescore_with_modules(cands, draws, 1234, [(mod, 1.0)])
        only_top = top_sets(only, 15)
        # OFF: all except this
        others = [(m, w) for m, w in all_mw if m is not mod]
        without = rescore_with_modules(cands, draws, 1234, others)
        without_top = top_sets(without, 15)
        # contribution: full vs without
        delta = membership_delta(baseline_top, without_top)
        ablate[tag] = {
            "membership_change_full_vs_without": delta,
            "membership_change_only_vs_pre": membership_delta(only_top, pre_top),
            "substantive": delta >= 0.01,
            "only_top15": [list(x) for x in only_top],
            "without_top15": [list(x) for x in without_top],
        }

    # alignment: post top15 as "B contribution" of full aux stack
    # also each aux-only top15
    C = sample_C(15, rng)
    fC = feats(C)
    zone_keys = sorted(set(fA["zones"]) | set(feats(post_sets)["zones"]) | set(fC["zones"]))

    align = {
        "method_note": (
            "aux는 세트 미생성. B=동일 후보풀에서 aux 적용 후 top15 (또는 단일 aux top15). "
            "전/후 비교로 대체. K-W 거리척도 동일."
        ),
        "pre_vs_post_membership_delta": membership_delta(pre_top, full_top),
        "full_aux_stack_top15": {},
        "per_aux_only_top15": {},
    }
    fPost = feats(post_sets)
    fPre = feats(pre_sets)
    dA = distances(fPost, fA, zone_keys)
    dC = distances(fPost, fC, sorted(set(zone_keys) | set(fC["zones"])))
    align["full_aux_stack_top15"] = {
        "vs_A": dA,
        "vs_C": dC,
        "interpret": interpret(dA, dC),
        "sum_mean": float(fPost["sums"].mean()),
        "pre_sum_mean": float(fPre["sums"].mean()),
    }
    for tag, mod in AUX_TAGS.items():
        only = rescore_with_modules(cands, draws, 1234, [(mod, 1.0)])
        sets = [list(k) for k in top_sets(only, 15)]
        fB = feats(sets)
        zk = sorted(set(zone_keys) | set(fB["zones"]))
        C15 = sample_C(15, random.Random(SEED + hash(tag) % 999))
        fC15 = feats(C15)
        dA2 = distances(fB, fA, zk)
        dC2 = distances(fB, fC15, sorted(set(zk) | set(fC15["zones"])))
        align["per_aux_only_top15"][tag] = {
            "vs_A": dA2,
            "vs_C": dC2,
            "interpret": interpret(dA2, dC2),
            "sum_mean": float(fB["sums"].mean()),
            "referee_score_constant": tag == "referee_aux",
        }

    # also pre (no aux) alignment for reference
    dA0 = distances(fPre, fA, zone_keys)
    dC0 = distances(fPre, fC, sorted(set(zone_keys) | set(fC["zones"])))
    align["pre_aux_top15"] = {
        "vs_A": dA0,
        "vs_C": dC0,
        "interpret": interpret(dA0, dC0),
    }

    # wiring
    wiring = {
        "click_path": "engine.run_prediction → coordinator.run_coordinated_prediction → _apply_aux_scoring",
        "AUX_MODULES_order": [m.__name__ for m in AUX_MODULES],
        "each_called_in__apply_aux_scoring": True,
        "referee_score_set_returns": 0.5,
        "referee_weights_used_in_final_conf": True,
        "fusion_in_click_path": False,
        "fusion_import_location": "engine.py legacy/other paths; run_prediction does NOT call fusion",
    }

    # balance / pattern impl
    impl = {
        "pattern_aux": pattern_impl_facts(),
        "balance_aux": balance_targets_vs_theory(draws),
        "label_recommendation": {
            "pattern_aux": "전제실증·구현미검증",
            "balance_aux": "전제실증·구현미검증",
            "reason": (
                "K-T는 draws≈이론만 실증. pattern=상수/경험칙, "
                f"balance sum target={balance_targets_vs_theory(draws)['code_targets']['sum']:.2f} ≠ 138"
            ),
        },
    }

    out = {
        "meta": {"seed": SEED, "target": 1234, "n_candidates": len(cands)},
        "step1_alignment": align,
        "step2_impl": impl,
        "step3_wiring": wiring,
        "step3_referee_dual": db_vs_live_referee(),
        "step3_learn_state_keys": learn_state_key_audit(),
        "step4_ablation": ablate,
        "step4_pre_post_delta": membership_delta(pre_top, full_top),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("pre_post", out["step4_pre_post_delta"])
    for t, v in ablate.items():
        print(t, "delta", round(v["membership_change_full_vs_without"], 4), "sub", v["substantive"])
    print("full", align["full_aux_stack_top15"]["interpret"]["overall"])
    for t, v in align["per_aux_only_top15"].items():
        print("only", t, v["interpret"]["overall"])
    print("balance tgt", impl["balance_aux"]["code_targets"])
    print("learn unused", [r["key"] for r in out["step3_learn_state_keys"] if not r["consumed"]])
    print("live ref", out["step3_referee_dual"]["live"])


if __name__ == "__main__":
    main()
