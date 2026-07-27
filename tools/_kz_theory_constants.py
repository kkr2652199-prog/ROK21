# -*- coding: utf-8 -*-
"""K-Z READ-ONLY: C(45,6) 이론값 전수 + 현행 상수 대조 + 교체 가정 시뮬(적용 금지)."""
from __future__ import annotations

import json
import os
import random
import sqlite3
import sys
from collections import Counter
from itertools import combinations
from math import comb
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260727_KZ_theory_constants.json"
SEED = 20260727
N = comb(45, 6)  # 8145060


def ac_value(nums: tuple[int, ...] | list[int]) -> int:
    s = sorted(nums)
    diffs = {s[j] - s[i] for i in range(len(s)) for j in range(i + 1, len(s))}
    return max(0, len(diffs) - (len(s) - 1))


def consec_pairs(nums) -> int:
    s = sorted(nums)
    return sum(1 for i in range(5) if s[i + 1] - s[i] == 1)


def zone_lmh(nums) -> tuple[int, int, int]:
    """balance_aux 정의: 1-15 / 16-30 / 31-45."""
    l = sum(1 for n in nums if 1 <= n <= 15)
    m = sum(1 for n in nums if 16 <= n <= 30)
    h = 6 - l - m
    return l, m, h


def decade_counts(nums) -> tuple[int, ...]:
    """1-9,10-19,20-29,30-39,40-45."""
    bins = [0] * 5
    for n in nums:
        if n <= 9:
            bins[0] += 1
        elif n <= 19:
            bins[1] += 1
        elif n <= 29:
            bins[2] += 1
        elif n <= 39:
            bins[3] += 1
        else:
            bins[4] += 1
    return tuple(bins)


def enumerate_theory():
    print(f"enumerating C(45,6)={N} ...", flush=True)
    sum_c = Counter()
    odd_c = Counter()
    ac_c = Counter()
    consec_c = Counter()
    zone_lmh_c = Counter()
    decade_c = Counter()
    uniq_end_c = Counter()
    # for moments
    sum_sq = 0.0
    ac_sum = 0.0

    for combo in combinations(range(1, 46), 6):
        s = sum(combo)
        sum_c[s] += 1
        sum_sq += s * s
        odd = sum(1 for x in combo if x % 2 == 1)
        odd_c[odd] += 1
        ac = ac_value(combo)
        ac_c[ac] += 1
        ac_sum += ac
        consec_c[consec_pairs(combo)] += 1
        zone_lmh_c[zone_lmh(combo)] += 1
        decade_c[decade_counts(combo)] += 1
        uniq_end_c[len({x % 10 for x in combo})] += 1

    # sum stats via full pmf
    sums_sorted = sorted(sum_c)
    # expand for percentiles: use cumulative
    cdf = []
    cum = 0
    for k in sums_sorted:
        cum += sum_c[k]
        cdf.append((k, cum))

    def quantile(p):
        thr = p * N
        for k, c in cdf:
            if c >= thr:
                return k
        return sums_sorted[-1]

    mean_sum = sum(k * sum_c[k] for k in sum_c) / N
    var_sum = sum_sq / N - mean_sum**2
    mode_sum = max(sum_c, key=sum_c.get)

    # odd: hypergeometric closed form check
    # P(K=k)=C(23,k)*C(22,6-k)/C(45,6) for k with 0<=6-k<=22
    odd_closed = {}
    for k in range(7):
        if 0 <= k <= 23 and 0 <= 6 - k <= 22:
            odd_closed[k] = comb(23, k) * comb(22, 6 - k) / N
        else:
            odd_closed[k] = 0.0

    return {
        "N": N,
        "method": "전수 열거 itertools.combinations(1..45,6); 홀수는 초기하 닫힌형 교차검증",
        "sum": {
            "mean": mean_sum,
            "std": var_sum**0.5,
            "mode": mode_sum,
            "mode_count": sum_c[mode_sum],
            "q05": quantile(0.05),
            "q50": quantile(0.50),
            "q95": quantile(0.95),
            "min": min(sums_sorted),
            "max": max(sums_sorted),
            "pmf_top10": [
                {"sum": k, "count": sum_c[k], "p": sum_c[k] / N}
                for k in sorted(sum_c, key=lambda x: -sum_c[x])[:10]
            ],
        },
        "odd_count": {
            "pmf_enum": {str(k): odd_c[k] / N for k in range(7)},
            "pmf_hypergeometric": {str(k): odd_closed[k] for k in range(7)},
            "counts": {str(k): odd_c[k] for k in range(7)},
            "mode": max(range(7), key=lambda k: odd_c[k]),
            "match_closed": all(
                abs(odd_c[k] / N - odd_closed[k]) < 1e-15 for k in range(7)
            ),
        },
        "ac": {
            "pmf": {str(k): ac_c[k] / N for k in sorted(ac_c)},
            "counts": {str(k): ac_c[k] for k in sorted(ac_c)},
            "mode": max(ac_c, key=ac_c.get),
            "mean": ac_sum / N,
            "current_ac_target": 7,
            "ac_target_is_mode": max(ac_c, key=ac_c.get) == 7,
        },
        "consecutive_pairs": {
            "pmf": {str(k): consec_c[k] / N for k in range(6)},
            "counts": {str(k): consec_c[k] for k in range(6)},
            "mode": max(range(6), key=lambda k: consec_c[k]),
            "current_score_table": {"0": 0.7, "1": 0.7, "2": 0.5, "3+": 0.3},
            "note": "점수표는 확률의 단조변환이 아님(0과1에 동일점수). 최빈과 점수 최댓값 정렬만 대조",
        },
        "zone_lmh_balance_def": {
            "mode": list(max(zone_lmh_c, key=zone_lmh_c.get)),
            "mode_p": max(zone_lmh_c.values()) / N,
            "top10": [
                {"zone": list(z), "count": c, "p": c / N}
                for z, c in zone_lmh_c.most_common(10)
            ],
            "E_max_zone": sum(max(z) * c for z, c in zone_lmh_c.items()) / N,
        },
        "decade_1_9_bands": {
            "mode": list(max(decade_c, key=decade_c.get)),
            "mode_p": max(decade_c.values()) / N,
            "top10": [
                {"decade": list(z), "count": c, "p": c / N}
                for z, c in decade_c.most_common(10)
            ],
            "labels": ["1-9", "10-19", "20-29", "30-39", "40-45"],
        },
        "unique_endings": {
            "pmf": {str(k): uniq_end_c[k] / N for k in sorted(uniq_end_c)},
            "counts": {str(k): uniq_end_c[k] for k in sorted(uniq_end_c)},
            "mode": max(uniq_end_c, key=uniq_end_c.get),
        },
    }


def load_draws_feat():
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    con.close()
    draws = []
    for r in rows:
        d = {"draw_no": int(r[0])}
        for i in range(1, 7):
            d[f"num{i}"] = int(r[i])
        draws.append(d)
    return draws


def current_balance_targets(draws):
    from app.testlotto.brains.aux_balance_keeper import _historical_targets

    return _historical_targets(draws)


def pattern_score_theory(nums, ac_target, consec_table, pair_norm=0.5):
    """pair 항은 역사쌍이라 시뮬에서 중립 고정(0.5) — 교체는 ac/consec/sum/odd 중심."""
    ac = ac_value(nums)
    ac_score = 1.0 - min(1.0, abs(ac - ac_target) / 10.0)
    consec = consec_pairs(nums)
    if consec in (0, 1):
        consec_score = consec_table.get(0, 0.7)  # same for 0 and 1 in current
    elif consec == 2:
        consec_score = consec_table.get(2, 0.5)
    else:
        consec_score = consec_table.get("else", 0.3)
    # use same 0/1 score
    if consec in (0, 1):
        consec_score = consec_table.get("01", consec_table.get(0, 0.7))
    return max(0.1, min(1.0, 0.4 * pair_norm + 0.35 * ac_score + 0.25 * consec_score))


def balance_score_theory(nums, tgt_odd, tgt_sum, zone_mode="spread"):
    from app.testlotto.brains.aux_balance_keeper import _zone_counts
    from app.testlotto.features.draw_features import odd_even_ratio, sum_range

    odd, even = odd_even_ratio(nums)
    s = sum_range(nums)
    low, mid, high = _zone_counts(nums)
    zone_spread = max(low, mid, high) - min(low, mid, high)
    odd_score = 1.0 - min(1.0, abs(odd - tgt_odd) / 3)
    sum_score = 1.0 - min(1.0, abs(s - tgt_sum) / 60)
    zone_score = 1.0 - min(1.0, zone_spread / 4)
    return max(0.1, min(1.0, 0.35 * odd_score + 0.35 * sum_score + 0.30 * zone_score))


def feats_sets(sets):
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
    }


def ks_d(a, b):
    return float(stats.ks_2samp(a, b).statistic)


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


def distances(fB, fA):
    zk = sorted(set(fB["zones"]) | set(fA["zones"]))
    return {
        "sum_KS": ks_d(fB["sums"], fA["sums"]),
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
    }


def mean_dist(d):
    return float(np.mean(list(d.values())))


def simulate_replacement(theo, draws):
    """이론값 교체 가정 시뮬 — 프로덕션 코드 미수정."""
    from app.testlotto.brains import aux_balance_keeper, aux_miss_detective, aux_pattern_spotlight, aux_referee
    from app.testlotto.brains.coordinator import PREDICT_MODULES, AUX_WEIGHTS
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state import get_referee_weights
    from app.testlotto.learn_state_cutoff import set_learn_as_of, clear_history_cache
    from app.testlotto.features.draw_features import build_pair_freq, pair_set, combo_features

    os.environ.pop("ROK21_LEARN_CUTOFF", None)
    clear_history_cache()
    set_learn_as_of(1234)
    random.seed(SEED)
    draws_before = _get_draws_before(1234)
    cands = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(SEED + hash(tag) % 10007)
        cands.extend(mod.predict_sets(draws_before, 20))

    ref = get_referee_weights()
    pair_freq = build_pair_freq(draws_before)
    hist_tgt = current_balance_targets(draws_before)

    ac_mode = theo["ac"]["mode"]
    consec_mode = theo["consecutive_pairs"]["mode"]
    # theory-aligned consec table: mode highest, then decay by rarity
    pmf = {int(k): v for k, v in theo["consecutive_pairs"]["pmf"].items()}
    # score = 0.3 + 0.4 * (p / p_mode) clipped
    pmode = pmf[consec_mode]
    theo_consec_score = {
        k: float(0.3 + 0.4 * (pmf.get(k, 0) / pmode)) for k in range(6)
    }

    def score_pattern_current(nums):
        feats = combo_features(nums, draws_before)
        pairs = pair_set(nums)
        pair_norm = min(1.0, sum(pair_freq.get(p, 0) for p in pairs) / 30.0)
        ac = feats["ac"]
        ac_score = 1.0 - min(1.0, abs(ac - 7) / 10.0)
        consec = feats["consecutive"]
        consec_score = 0.7 if consec in (0, 1) else (0.5 if consec == 2 else 0.3)
        return max(0.1, min(1.0, 0.4 * pair_norm + 0.35 * ac_score + 0.25 * consec_score))

    def score_pattern_theory(nums):
        feats = combo_features(nums, draws_before)
        pairs = pair_set(nums)
        pair_norm = min(1.0, sum(pair_freq.get(p, 0) for p in pairs) / 30.0)  # pair scale 유지
        ac = feats["ac"]
        ac_score = 1.0 - min(1.0, abs(ac - ac_mode) / 10.0)
        consec = feats["consecutive"]
        consec_score = theo_consec_score.get(consec, 0.3)
        return max(0.1, min(1.0, 0.4 * pair_norm + 0.35 * ac_score + 0.25 * consec_score))

    def score_balance_current(nums):
        return aux_balance_keeper.score_set(nums, draws_before, 1234)

    def score_balance_theory(nums):
        return balance_score_theory(
            nums, tgt_odd=float(theo["odd_count"]["mode"]), tgt_sum=float(theo["sum"]["mean"])
        )

    def final_conf(c, pat_fn, bal_fn):
        base = float(c.get("confidence", 60))
        bw = ref.get(c.get("brain_tag", ""), 1 / 3)
        aux = (
            0.25 * aux_miss_detective.score_set(c["nums"], draws_before, 1234)
            + 0.25 * pat_fn(c["nums"])
            + 0.25 * bal_fn(c["nums"])
            + 0.25 * 0.5
        )
        return min(99.5, base * 0.5 * bw + aux * 40 + base * 0.1)

    def top15(pat_fn, bal_fn):
        scored = sorted(
            cands, key=lambda c: -final_conf(c, pat_fn, bal_fn)
        )
        return [tuple(sorted(c["nums"])) for c in scored[:15]]

    cur = top15(score_pattern_current, score_balance_current)
    new = top15(score_pattern_theory, score_balance_theory)
    sa, sb = set(cur), set(new)
    mem_delta = 1.0 - len(sa & sb) / max(len(sa | sb), 1)

    A_sets = [
        sorted(int(d[f"num{i}"]) for i in range(1, 7)) for d in draws
    ]
    fA = feats_sets(A_sets)
    f_cur = feats_sets([list(x) for x in cur])
    f_new = feats_sets([list(x) for x in new])
    d_cur = distances(f_cur, fA)
    d_new = distances(f_new, fA)

    # side effect: ending / decade
    def ending_prop(sets):
        e = Counter()
        for s in sets:
            for n in s:
                e[n % 10] += 1
        tot = sum(e.values()) or 1
        return [e.get(d, 0) / tot for d in range(10)]

    ep_c, ep_n = ending_prop(cur), ending_prop(new)
    ending_l1 = float(sum(abs(a - b) for a, b in zip(ep_c, ep_n)))

    return {
        "n_candidates": len(cands),
        "membership_delta_top15": mem_delta,
        "overlap": len(sa & sb),
        "theory_params_used": {
            "ac_target": ac_mode,
            "odd_target": theo["odd_count"]["mode"],
            "sum_target": theo["sum"]["mean"],
            "consec_score_by_count": theo_consec_score,
            "pair_scale_unchanged": 30,
        },
        "current_hist_targets": hist_tgt,
        "distance_to_A_before": d_cur,
        "distance_to_A_after": d_new,
        "mean_distance_before": mean_dist(d_cur),
        "mean_distance_after": mean_dist(d_new),
        "closer_to_A": mean_dist(d_new) < mean_dist(d_cur) - 1e-9,
        "ending_prop_L1_before_after": ending_l1,
        "ending_prop_before": ep_c,
        "ending_prop_after": ep_n,
        "disclaimer": (
            "이 교체는 1등 확률을 올리지 않는다. 조합불변이다. "
            "얻는 것은 '왜 이 번호인가'에 답할 수 있는 명분뿐이다."
        ),
    }


def verdicts(theo, hist_tgt):
    ac_mode = theo["ac"]["mode"]
    rows = []
    # ac_target
    rows.append(
        {
            "const": "pattern.ac_target",
            "current": 7,
            "theory": ac_mode,
            "delta": 7 - ac_mode,
            "verdict": "유지 가능" if ac_mode == 7 else "교체 필요",
            "note": "이론 최빈과 일치 여부",
        }
    )
    rows.append(
        {
            "const": "pattern.pair_norm_divisor",
            "current": 30,
            "theory": None,
            "delta": None,
            "verdict": "판단보류",
            "note": "이론 단일 스케일 없음(역사 쌍빈도). 재보정은 별도 벤치",
        }
    )
    # consec table vs mode
    mode_c = theo["consecutive_pairs"]["mode"]
    rows.append(
        {
            "const": "pattern.consec_score_table",
            "current": {"0/1": 0.7, "2": 0.5, "else": 0.3},
            "theory_mode": mode_c,
            "theory_pmf": theo["consecutive_pairs"]["pmf"],
            "delta": "0·1 동점 vs 최빈=" + str(mode_c),
            "verdict": "교체 필요" if mode_c not in (0, 1) else "유지 가능(부분)",
            "note": "0과 1에 동일 최고점 — 최빈이 0이면 부분 정합. 확률비례 점수로 재설계 여지",
        }
    )
    rows.append(
        {
            "const": "balance.sum_target_rolling80",
            "current": hist_tgt["sum"],
            "theory": theo["sum"]["mean"],
            "delta": hist_tgt["sum"] - theo["sum"]["mean"],
            "verdict": "유지 가능" if abs(hist_tgt["sum"] - theo["sum"]["mean"]) < 1.0 else "교체 필요",
            "note": "현 롤링값이 이론평균에 매우 근접(우연히/수렴)",
        }
    )
    rows.append(
        {
            "const": "balance.sum_default_empty",
            "current": 150.0,
            "theory": theo["sum"]["mean"],
            "delta": 150.0 - theo["sum"]["mean"],
            "verdict": "교체 필요",
            "note": "빈 draws 폴백 합150 vs 이론138 — 명확 오차",
        }
    )
    rows.append(
        {
            "const": "balance.odd_target_rolling80",
            "current": hist_tgt["odd"],
            "theory_mode": theo["odd_count"]["mode"],
            "delta": hist_tgt["odd"] - theo["odd_count"]["mode"],
            "verdict": "유지 가능" if abs(hist_tgt["odd"] - theo["odd_count"]["mode"]) < 0.2 else "교체 필요",
            "note": "이론 최빈=3",
        }
    )
    rows.append(
        {
            "const": "balance.zone_target_max_avg",
            "current": hist_tgt["zone"],
            "theory_E_max_zone": theo["zone_lmh_balance_def"]["E_max_zone"],
            "theory_mode_lmh": theo["zone_lmh_balance_def"]["mode"],
            "delta": hist_tgt["zone"] - theo["zone_lmh_balance_def"]["E_max_zone"],
            "verdict": "판단보류",
            "note": "코드는 max(zone) 평균을 목표로 씀 — 이론 최빈 패턴(l,m,h)과 목표 정의가 다름",
        }
    )
    return rows


def main():
    theo = enumerate_theory()
    draws = load_draws_feat()
    hist_tgt = current_balance_targets(draws)
    cmp_rows = verdicts(theo, hist_tgt)
    print("simulating replacement (no apply)...", flush=True)
    sim = simulate_replacement(theo, draws)

    mix_options = {
        "full_theory": {
            "ratio": "이론 100%",
            "rationale": "명분 회복·재현성. 롤링 드리프트 제거",
            "risk": "단기 분포 변화 시 경험 추적 상실",
        },
        "blend_50_50": {
            "ratio": "이론 50% + 롤링80 50%",
            "rationale": "합·홀이 이미 이론 근접 — 급변 완화. 기본값150은 이론으로 즉시 교체",
            "risk": "이중 목표로 해석 모호",
        },
        "theory_anchor_rolling_shrink": {
            "ratio": "이론 고정 + 롤링을 prior로만 문서화(점수 미사용)",
            "rationale": "점수 경로는 이론만 — 감사/표시용으로 롤링 병기",
            "risk": "구현 단순·명분 최대",
        },
    }

    out = {
        "meta": {"N": N, "seed": SEED, "apply": False},
        "theory": theo,
        "current_vs_theory": cmp_rows,
        "current_rolling80": hist_tgt,
        "simulation": sim,
        "mix_options": mix_options,
        "warrant_note": (
            "이번 턴 WARRANT 라벨 변경 없음. "
            "이론값 교체 적용·구현검증 후에야 pattern/balance '실증' 복귀 가능."
        ),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("sum mean/mode/q50", theo["sum"]["mean"], theo["sum"]["mode"], theo["sum"]["q50"])
    print("odd mode", theo["odd_count"]["mode"], "closed_match", theo["odd_count"]["match_closed"])
    print("ac mode/mean", theo["ac"]["mode"], theo["ac"]["mean"], "target7_is_mode", theo["ac"]["ac_target_is_mode"])
    print("consec mode", theo["consecutive_pairs"]["mode"], theo["consecutive_pairs"]["pmf"])
    print("zone mode", theo["zone_lmh_balance_def"]["mode"], "E_max", theo["zone_lmh_balance_def"]["E_max_zone"])
    print("uniq end mode", theo["unique_endings"]["mode"], theo["unique_endings"]["pmf"])
    print("sim mem_delta", sim["membership_delta_top15"], "closer", sim["closer_to_A"])
    print("dist before/after", sim["mean_distance_before"], sim["mean_distance_after"])


if __name__ == "__main__":
    main()
