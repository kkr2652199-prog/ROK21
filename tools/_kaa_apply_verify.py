# -*- coding: utf-8 -*-
"""K-AA VERIFY: consec wiring · 단위구현 · 회귀게이트 · (A거리는 관측만)."""
from __future__ import annotations

import hashlib
import json
import os
import random
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260727_KAA_apply_verify.json"
DB = ROOT / "data" / "lotto_testlotto.db"
SEED = 20260727
AS_OF = 1234


def load_draws():
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    con.close()
    out = []
    for r in rows:
        d = {"draw_no": int(r[0])}
        for i in range(1, 7):
            d[f"num{i}"] = int(r[i])
        out.append(d)
    return out


def step2_wiring():
    """consec 점수 변화가 top15·aux 합성에 반영되는지. 무변화면 배선결함."""
    from app.testlotto.brains import aux_balance_keeper, aux_miss_detective, aux_pattern_spotlight, aux_referee
    from app.testlotto.brains.coordinator import (
        AUX_MODULES,
        AUX_WEIGHTS,
        PREDICT_MODULES,
        _apply_aux_scoring,
        _aux_composite_score,
    )
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import clear_history_cache, set_learn_as_of

    os.environ.pop("ROK21_LEARN_CUTOFF", None)  # default ON
    clear_history_cache()
    set_learn_as_of(AS_OF)
    draws = _get_draws_before(AS_OF)

    # 1) 모듈 단위: consec만 다른 두 세트 → pattern 점수·composite 차이
    # AC·합 비슷하게: consec=0 vs consec=2
    set0 = [1, 3, 5, 10, 20, 30]  # no consecutive
    set2 = [1, 2, 3, 10, 20, 30]  # consec pairs: (1,2)(2,3) = 2

    from app.testlotto.features.draw_features import combo_features

    f0 = combo_features(set0, draws)
    f2 = combo_features(set2, draws)
    pat0 = aux_pattern_spotlight.score_set(set0, draws, AS_OF)
    pat2 = aux_pattern_spotlight.score_set(set2, draws, AS_OF)
    miss0 = aux_miss_detective.score_set(set0, draws, AS_OF)
    miss2 = aux_miss_detective.score_set(set2, draws, AS_OF)
    bal0 = aux_balance_keeper.score_set(set0, draws, AS_OF)
    bal2 = aux_balance_keeper.score_set(set2, draws, AS_OF)
    ref0 = aux_referee.score_set(set0, draws, AS_OF)
    ref2 = aux_referee.score_set(set2, draws, AS_OF)
    comp0 = _aux_composite_score(set0, draws, AS_OF)
    comp2 = _aux_composite_score(set2, draws, AS_OF)

    pattern_delta = pat0 - pat2
    composite_delta = comp0 - comp2
    # 다른 aux도 세트에 반응하므로, pattern 기여만 분리: Δcomp = 0.25*ΣΔmod
    expected_comp_delta = 0.25 * (
        (miss0 - miss2) + pattern_delta + (bal0 - bal2) + (ref0 - ref2)
    )
    composite_identity_ok = abs(composite_delta - expected_comp_delta) < 1e-12
    pattern_share_of_comp_delta = (
        abs(0.25 * pattern_delta / composite_delta) if abs(composite_delta) > 1e-15 else None
    )

    # 2) top15: consec 점수표 평탄화 ablation → 멤버십 변화 필수(후보 consec 다양 시)
    random.seed(SEED)
    cands = []
    def _tag_seed(tag: str) -> int:
        return SEED + int(hashlib.md5(tag.encode()).hexdigest()[:8], 16) % 10007

    for tag, mod in PREDICT_MODULES.items():
        random.seed(_tag_seed(tag))
        cands.extend(mod.predict_sets(draws, 20))

    scored = _apply_aux_scoring(cands, draws, AS_OF)
    scored_sorted = sorted(scored, key=lambda x: -x["confidence"])
    top15 = [tuple(sorted(c["nums"])) for c in scored_sorted[:15]]
    consec_hist = Counter(
        combo_features(list(t), draws)["consecutive"] for t in top15
    )

    orig = dict(aux_pattern_spotlight._CONSEC_SCORE)
    try:
        for k in list(aux_pattern_spotlight._CONSEC_SCORE):
            aux_pattern_spotlight._CONSEC_SCORE[k] = 0.5
        scored_flat = _apply_aux_scoring(cands, draws, AS_OF)
        top15_flat = [
            tuple(sorted(c["nums"]))
            for c in sorted(scored_flat, key=lambda x: -x["confidence"])[:15]
        ]
        # conf 분포도 비교 (표시정밀도 0.1)
        conf_new = [round(c["confidence"], 1) for c in sorted(scored, key=lambda x: -x["confidence"])[:15]]
        conf_flat = [round(c["confidence"], 1) for c in sorted(scored_flat, key=lambda x: -x["confidence"])[:15]]
    finally:
        aux_pattern_spotlight._CONSEC_SCORE.clear()
        aux_pattern_spotlight._CONSEC_SCORE.update(orig)

    sa, sb = set(top15), set(top15_flat)
    mem_delta = 1.0 - len(sa & sb) / max(len(sa | sb), 1)
    conf_changed = conf_new != conf_flat
    feature_ok = f0["consecutive"] != f2["consecutive"]
    cand_consec = [combo_features(c["nums"], draws)["consecutive"] for c in cands]
    varied = len(set(cand_consec)) > 1

    # 배선 PASS: feature→pattern점수→composite 항등식 → (다양시) ablation이 top15/conf 변경
    if not feature_ok or abs(pattern_delta) < 1e-15:
        wiring_ok = False
        halt_note = "pattern consec 점수 무반응"
    elif not composite_identity_ok:
        wiring_ok = False
        halt_note = "composite 항등식 붕괴 — _aux_composite_score 경로 이상"
    elif varied and mem_delta == 0 and not conf_changed:
        wiring_ok = False
        halt_note = "consec ablation 무변화 — 정렬 미반영(K-D/K-Y 교차)"
    else:
        wiring_ok = True
        halt_note = None

    path = {
        "score_set_pattern": "aux_pattern_spotlight.score_set uses _CONSEC_SCORE[consec]",
        "composite": "_aux_composite_score = Σ w_i * mod.score_set · pattern w=0.25",
        "apply": "_apply_aux_scoring → final_conf = base*0.5*bw + aux*40 + base*0.1",
        "sort": "scored.sort by confidence (coordinator)",
        "AUX_WEIGHTS": list(AUX_WEIGHTS),
        "pattern_module": "app.testlotto.brains.aux_pattern_spotlight",
        "pattern_index": 1,
        "K-D_note": "AUX_WEIGHTS [0.25]*4 hardcode — fusion 미배선이나 pattern 항은 소거되지 않음(가중 0.25 유지)",
    }

    return {
        "feature_consec_set0": f0["consecutive"],
        "feature_consec_set2": f2["consecutive"],
        "feature_ok": feature_ok,
        "pattern_score_set0": pat0,
        "pattern_score_set2": pat2,
        "pattern_delta": pattern_delta,
        "composite_set0": comp0,
        "composite_set2": comp2,
        "composite_delta": composite_delta,
        "expected_composite_delta": expected_comp_delta,
        "composite_identity_ok": composite_identity_ok,
        "pattern_share_of_comp_delta": pattern_share_of_comp_delta,
        "pattern_weight_in_composite": 0.25,
        "top15_consec_hist": {str(k): v for k, v in sorted(consec_hist.items())},
        "consec_ablation_membership_delta": mem_delta,
        "consec_ablation_conf_changed": conf_changed,
        "candidate_consec_varied": varied,
        "wiring_ok": wiring_ok,
        "halt_note": halt_note,
        "path_trace": path,
        "verdict": "PASS" if wiring_ok else "FAIL_WIRING - stop and cross-ref K-D/K-Y",
    }


def step3_unit_impl():
    """목표값=코드가 최적화하는 값 단위 증명."""
    from app.testlotto.brains import aux_balance_keeper, aux_pattern_spotlight
    from app.testlotto.features.draw_features import ac_value

    # --- AC: empty draws so pair_norm≈0; vary AC ---
    # Craft numbers with known AC around 8
    # Use synthetic: fix pair path with draws=[]
    draws_empty: list = []

    # Build combos with different AC by scanning a small grid
    ac_rows = []
    # Representative sets for AC 5..10 (hand-picked / searched)
    probes = {
        # We search systematically among combinations of small sets
    }
    from itertools import combinations

    found: dict[int, list[int]] = {}
    for combo in combinations(range(1, 46), 6):
        ac = ac_value(combo)
        if ac not in found and 4 <= ac <= 10:
            found[ac] = list(combo)
        if len(found) >= 7:
            break
    for ac in range(4, 11):
        nums = found.get(ac)
        if not nums:
            continue
        sc = aux_pattern_spotlight.score_set(nums, draws_empty, AS_OF)
        ac_rows.append({"ac": ac, "nums": nums, "pattern_score": sc})

    # Pure ac_score component
    ac_component = []
    for ac in range(0, 11):
        ac_score = 1.0 - min(1.0, abs(ac - 8) / 10.0)
        ac_component.append({"ac": ac, "ac_score": ac_score})
    ac_peak_at_8 = max(ac_component, key=lambda r: r["ac_score"])["ac"] == 8
    # Monotone away from 8 on component
    left = [r["ac_score"] for r in ac_component if r["ac"] <= 8]
    right = [r["ac_score"] for r in ac_component if r["ac"] >= 8]
    ac_mono = left == sorted(left) and right == sorted(right, reverse=True)

    # Full pattern score peak: among found, max at ac=8 (pair=0 when draws empty)
    if ac_rows:
        best = max(ac_rows, key=lambda r: r["pattern_score"])
        pattern_peak_ac = best["ac"]
    else:
        pattern_peak_ac = None
    ac_pass = ac_peak_at_8 and ac_mono and pattern_peak_ac == 8

    # --- sum target 138 with empty draws (fallback) ---
    # Fix odd=3, zone=(2,2,2), vary sum
    def make_sum_approx(target_sum: int, odd=3) -> list[int] | None:
        """Find a 6-set with sum≈target, odd count, prefer LMH (2,2,2)."""
        best = None
        best_err = 10**9
        for combo in combinations(range(1, 46), 6):
            if sum(1 for x in combo if x % 2) != odd:
                continue
            l = sum(1 for x in combo if x <= 15)
            m = sum(1 for x in combo if 16 <= x <= 30)
            h = 6 - l - m
            if (l, m, h) != (2, 2, 2):
                continue
            err = abs(sum(combo) - target_sum)
            if err < best_err:
                best_err = err
                best = list(combo)
                if err == 0:
                    break
        return best

    sum_targets = [100, 120, 138, 160, 180]
    sum_rows = []
    for ts in sum_targets:
        nums = make_sum_approx(ts)
        if nums is None:
            continue
        sc = aux_balance_keeper.score_set(nums, draws_empty, AS_OF)
        sum_rows.append(
            {
                "target_probe": ts,
                "actual_sum": sum(nums),
                "nums": nums,
                "balance_score": sc,
                "dist_to_138": abs(sum(nums) - 138),
            }
        )
    # Sort by dist to 138 — scores should be nonincreasing as dist increases
    sum_rows_sorted = sorted(sum_rows, key=lambda r: r["dist_to_138"])
    scores_by_dist = [r["balance_score"] for r in sum_rows_sorted]
    sum_mono = all(
        scores_by_dist[i] >= scores_by_dist[i + 1] - 1e-12
        for i in range(len(scores_by_dist) - 1)
    )
    # Peak at closest to 138
    peak = max(sum_rows, key=lambda r: r["balance_score"]) if sum_rows else None
    sum_peak_ok = peak is not None and peak["dist_to_138"] == min(
        r["dist_to_138"] for r in sum_rows
    )
    fallback = aux_balance_keeper._historical_targets([])
    fallback_ok = fallback["sum"] == 138.0 and fallback["odd"] == 3.0
    sum_pass = sum_mono and sum_peak_ok and fallback_ok

    # --- LMH (2,2,2) highest zone among fixed sum≈138 odd=3 ---
    zone_probes = []
    patterns = [(2, 2, 2), (3, 2, 1), (3, 1, 2), (4, 1, 1), (1, 1, 4), (0, 3, 3), (5, 1, 0)]
    for pat in patterns:
        found_z = None
        for combo in combinations(range(1, 46), 6):
            if sum(1 for x in combo if x % 2) != 3:
                continue
            if abs(sum(combo) - 138) > 2:
                continue
            l = sum(1 for x in combo if x <= 15)
            m = sum(1 for x in combo if 16 <= x <= 30)
            h = 6 - l - m
            if (l, m, h) == pat:
                found_z = list(combo)
                break
        if found_z is None:
            continue
        sc = aux_balance_keeper.score_set(found_z, draws_empty, AS_OF)
        low, mid, high = aux_balance_keeper._zone_counts(found_z)
        spread = max(low, mid, high) - min(low, mid, high)
        zone_score = 1.0 - min(1.0, spread / 4)
        zone_probes.append(
            {
                "lmh": list(pat),
                "nums": found_z,
                "sum": sum(found_z),
                "balance_score": sc,
                "zone_score_component": zone_score,
                "spread": spread,
            }
        )
    if zone_probes:
        best_z = max(zone_probes, key=lambda r: r["balance_score"])
        best_comp = max(zone_probes, key=lambda r: r["zone_score_component"])
        zone_pass = best_z["lmh"] == [2, 2, 2] and best_comp["lmh"] == [2, 2, 2]
    else:
        zone_pass = False

    # consec score table monotonic with pmf
    cs = aux_pattern_spotlight._CONSEC_SCORE
    consec_scores = [cs[k] for k in range(6)]
    consec_mono = all(consec_scores[i] >= consec_scores[i + 1] for i in range(5))
    consec_01_untied = cs[0] > cs[1]
    consec_in_band = all(0.3 <= cs[k] <= 0.7 for k in range(6))

    return {
        "ac": {
            "component_table": ac_component,
            "pattern_probe_rows": ac_rows,
            "peak_component_at_8": ac_peak_at_8,
            "component_monotone_away_from_8": ac_mono,
            "pattern_peak_ac": pattern_peak_ac,
            "pass": ac_pass,
        },
        "sum": {
            "fallback_targets": fallback,
            "fallback_ok": fallback_ok,
            "probe_rows": sum_rows_sorted,
            "monotone_vs_dist_to_138": sum_mono,
            "peak_at_nearest_138": sum_peak_ok,
            "pass": sum_pass,
        },
        "zone_lmh": {
            "probe_rows": zone_probes,
            "pass": zone_pass,
            "note": "zone_score=1-spread/4 → spread0 only at (2,2,2) among partitions of 6",
        },
        "consec_table": {
            "scores": {str(k): cs[k] for k in range(6)},
            "monotone_decreasing": consec_mono,
            "untied_0_gt_1": consec_01_untied,
            "in_band_0_3_to_0_7": consec_in_band,
            "pass": consec_mono and consec_01_untied and consec_in_band,
        },
        "pattern_aux_impl_pass": ac_pass and consec_mono and consec_01_untied,
        "balance_aux_impl_pass": sum_pass and zone_pass,
    }


def step4_regression(draws_all):
    from app.testlotto.brains.coordinator import PREDICT_MODULES, _apply_aux_scoring
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import clear_history_cache, set_learn_as_of
    from app.testlotto.ticket_dedup import combo_key, dedup_enabled, dedup_ticket_list

    os.environ["ROK21_DEDUP"] = "1"
    os.environ.pop("ROK21_LEARN_CUTOFF", None)
    clear_history_cache()
    set_learn_as_of(AS_OF)
    draws = _get_draws_before(AS_OF)

    def make_regen(target_draw_no: int):
        def regen(brain_tag, seen, replace_of=None):
            mod = PREDICT_MODULES.get(brain_tag)
            if mod is None or not draws:
                return None
            raw = mod.predict_sets(draws, 1)
            if not raw:
                return None
            return _apply_aux_scoring(raw, draws, target_draw_no)[0]

        return regen

    # 100장 조립: 60후보 + 중복 주입 → dedup 후 unique=100 목표
    # K-V 회귀: 소규모 반복(20회)로 E[k]=100 유지 확인 (전수 1000은 K-V에서 완료)
    random.seed(SEED)
    base = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(SEED + int(hashlib.md5(tag.encode()).hexdigest()[:8], 16) % 10007)
        base.extend(mod.predict_sets(draws, 40))
    base = _apply_aux_scoring(base[:120], draws, AS_OF)

    rng = random.Random(SEED)
    ks = []
    unresolved_total = 0
    t0 = time.perf_counter()
    regen = make_regen(AS_OF)
    for _ in range(20):
        # 100장: base에서 샘플 + 의도적 중복 약간
        batch = [dict(t) for t in rng.sample(base, min(100, len(base)))]
        while len(batch) < 100:
            batch.append(dict(batch[len(batch) % len(batch)]))
        # inject 3 dups
        for j in range(3):
            batch[90 + j] = dict(batch[j])
        batch, st = dedup_ticket_list(batch, regenerate=regen)
        ks.append(len({combo_key(t["nums"]) for t in batch}))
        unresolved_total += int(st["unresolved_count"])
    dt_dedup = time.perf_counter() - t0
    ek = float(np.mean(ks))
    dedup_ok = (
        dedup_enabled()
        and abs(ek - 100.0) < 1e-9
        and unresolved_total == 0
        and all(k == 100 for k in ks)
    )

    cutoff_on = os.environ.get("ROK21_LEARN_CUTOFF") not in ("0", "false", "OFF", "off")
    # env unset → default ON (K-S)
    if "ROK21_LEARN_CUTOFF" not in os.environ:
        cutoff_on = True

    def run_hash():
        clear_history_cache()
        set_learn_as_of(AS_OF)
        random.seed(SEED)
        cands = []
        for tag, mod in PREDICT_MODULES.items():
            random.seed(SEED + int(hashlib.md5(tag.encode()).hexdigest()[:8], 16) % 10007)
            cands.extend(mod.predict_sets(draws, 20))
        t1 = time.perf_counter()
        scored = _apply_aux_scoring(cands, draws, AS_OF)
        scored.sort(key=lambda x: -x["confidence"])
        top = [sorted(c["nums"]) for c in scored[:15]]
        elapsed = time.perf_counter() - t1
        payload = json.dumps(top, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest(), elapsed, top

    h1, e1, top1 = run_hash()
    h2, e2, top2 = run_hash()
    sha_ok = h1 == h2

    def feats(sets):
        sums, odds, zones, consecs, endings = [], [], [], [], Counter()
        for sc in sets:
            sc = sorted(sc)
            sums.append(sum(sc))
            odds.append(sum(1 for x in sc if x % 2))
            l = sum(1 for x in sc if x <= 15)
            m = sum(1 for x in sc if 16 <= x <= 30)
            zones.append((l, m, 6 - l - m))
            consecs.append(sum(1 for i in range(5) if sc[i + 1] - sc[i] == 1))
            for x in sc:
                endings[x % 10] += 1
        return {
            "sums": np.asarray(sums, float),
            "odds": np.asarray(odds, int),
            "zones": zones,
            "consecs": np.asarray(consecs, int),
            "endings": endings,
        }

    A = [sorted(int(d[f"num{i}"]) for i in range(1, 7)) for d in draws_all]
    fA, fB = feats(A), feats(top1)

    def chi2_df(ca, cb):
        tbl = np.vstack([ca, cb]).astype(float)
        tbl = tbl[:, tbl.sum(0) > 0]
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
        chi2, p, dof, _ = stats.chi2_contingency(np.column_stack(cols))
        return float(chi2 / max(1, int(dof)))

    zk = sorted(set(fB["zones"]) | set(fA["zones"]))
    kw_obs = {
        "sum_KS": float(stats.ks_2samp(fB["sums"], fA["sums"]).statistic),
        "odd_chi2_df": chi2_df(
            np.bincount(fB["odds"], minlength=7).astype(float),
            np.bincount(fA["odds"], minlength=7).astype(float),
        ),
        "zone_chi2_df": chi2_df(
            np.array([Counter(fB["zones"]).get(k, 0) for k in zk], float),
            np.array([Counter(fA["zones"]).get(k, 0) for k in zk], float),
        ),
        "consec_chi2_df": chi2_df(
            np.bincount(fB["consecs"], minlength=6).astype(float),
            np.bincount(fA["consecs"], minlength=6).astype(float),
        ),
        "ending_chi2_df": chi2_df(
            np.array([fB["endings"].get(d, 0) for d in range(10)], float),
            np.array([fA["endings"].get(d, 0) for d in range(10)], float),
        ),
        "note": "관측만 — 게이트 아님 (K-AA STEP0)",
    }

    gate_ok = dedup_ok and cutoff_on and sha_ok
    return {
        "dedup_enabled": dedup_enabled(),
        "n_sim": 20,
        "E_k": ek,
        "k_all_100": all(k == 100 for k in ks),
        "unresolved_total": unresolved_total,
        "dedup_ok": dedup_ok,
        "dedup_batch_seconds": dt_dedup,
        "cutoff_default_on": cutoff_on,
        "sha256_run1": h1,
        "sha256_run2": h2,
        "sha_ok": sha_ok,
        "scoring_seconds_run1": e1,
        "scoring_seconds_run2": e2,
        "kw_distance_observation_only": kw_obs,
        "gate_pass": gate_ok,
    }


def main():
    print("STEP2 wiring...", flush=True)
    s2 = step2_wiring()
    print("wiring:", s2["verdict"], "mem_delta", s2["consec_ablation_membership_delta"], flush=True)
    if not s2["wiring_ok"]:
        out = {
            "meta": {"seed": SEED, "as_of": AS_OF, "halted": True},
            "step2_wiring": s2,
            "halt_reason": "consec 무변화/배선결함 — STEP3+중단",
        }
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print("HALTED", OUT)
        return 2

    print("STEP3 unit...", flush=True)
    s3 = step3_unit_impl()
    print(
        "pattern_pass",
        s3["pattern_aux_impl_pass"],
        "balance_pass",
        s3["balance_aux_impl_pass"],
        flush=True,
    )

    print("STEP4 regression...", flush=True)
    draws = load_draws()
    s4 = step4_regression(draws)
    print("gate", s4["gate_pass"], "Ek", s4["E_k"], "sha", s4["sha_ok"], flush=True)

    # Warrant decisions
    pattern_label = (
        "실증" if s3["pattern_aux_impl_pass"] and s2["wiring_ok"] else "전제실증·구현미검증"
    )
    balance_label = (
        "실증" if s3["balance_aux_impl_pass"] and s4["gate_pass"] else "전제실증·구현미검증"
    )

    out = {
        "meta": {
            "seed": SEED,
            "as_of": AS_OF,
            "disclaimer": (
                "이 교체는 1등 확률을 올리지 않는다. 조합불변이다. "
                "얻는 것은 '왜 이 번호인가'에 답할 수 있는 명분뿐이다. A 정합도 개선도 아니다."
            ),
            "judgment_axis": "조합론 참값 일치 단일축 (K-W A거리=관측)",
        },
        "constants_applied": {
            "balance_fallback_sum": 138.0,
            "ac_target": 8,
            "consec_scores": {str(k): v for k, v in __import__(
                "app.testlotto.brains.aux_pattern_spotlight", fromlist=["_CONSEC_SCORE"]
            )._CONSEC_SCORE.items()},
            "untouched": ["pair/30", "zone_target_rolling", "zone_fallback=2"],
        },
        "step2_wiring": s2,
        "step3_unit_impl": s3,
        "step4_regression": s4,
        "warrant_decision": {
            "pattern_aux": pattern_label,
            "balance_aux": balance_label,
            "rollback_required": not s4["gate_pass"],
        },
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    return 0 if s4["gate_pass"] and s2["wiring_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
