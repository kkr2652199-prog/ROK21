# -*- coding: utf-8 -*-
"""K-V 중복제거 검증 — READ 위주 + 메모리 발권 (DB 대량쓰기 없음)."""
from __future__ import annotations

import hashlib
import json
import os
import random
import sqlite3
import sys
import time
from collections import Counter
from itertools import combinations
from math import comb
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260727_KV_dedup_verify.json"

TOTAL = 8_145_060
N_SIM = 1000
SEED = 20260727
BRAINS = ("stat", "markov", "review")


def load_review_packs() -> dict[int, list[dict]]:
    con = sqlite3.connect(str(DB))
    rows = con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json FROM testlotto_brain_review "
        "WHERE draw_no >= (SELECT MAX(draw_no)-99 FROM lotto_draws) "
        "ORDER BY draw_no, brain_tag"
    ).fetchall()
    con.close()
    by: dict[int, list[dict]] = {}
    for draw_no, tag, js in rows:
        for s in json.loads(js):
            by.setdefault(int(draw_no), []).append(
                {
                    "nums": sorted(int(x) for x in s["nums"]),
                    "brain_tag": tag,
                    "method": tag,
                    "confidence": float(s.get("confidence") or 50),
                    "reasoning": "review_cache",
                    "source_draw": int(draw_no),
                }
            )
    return by


def assemble_100_off(packs: dict[int, list[dict]], rng: random.Random) -> list[dict]:
    draws = list(packs.keys())
    chosen: list[dict] = []
    while len(chosen) < 100:
        d = rng.choice(draws)
        pack = list(packs[d])
        rng.shuffle(pack)
        for t in pack:
            chosen.append(dict(t))
            if len(chosen) >= 100:
                break
    return chosen


def brain_counts(tickets: list[dict]) -> dict[str, int]:
    c = Counter(str(t.get("brain_tag")) for t in tickets)
    return {b: int(c.get(b, 0)) for b in BRAINS}


def unique_k(tickets: list[dict]) -> int:
    from app.testlotto.ticket_dedup import combo_key

    return len({combo_key(t["nums"]) for t in tickets})


def make_regen(target_draw_no: int):
    from app.testlotto.brains.coordinator import PREDICT_MODULES, _apply_aux_scoring
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    set_learn_as_of(int(target_draw_no))
    draws = _get_draws_before(target_draw_no)

    def regen(brain_tag: str, seen: set[tuple[int, ...]], replace_of=None):
        mod = PREDICT_MODULES.get(brain_tag)
        if mod is None or not draws:
            return None
        raw = mod.predict_sets(draws, 1)
        if not raw:
            return None
        return _apply_aux_scoring(raw, draws, target_draw_no)[0]

    return regen


def sim_1000(packs: dict[int, list[dict]], dedup_on: bool, collect_n: int = 50) -> dict:
    from app.testlotto.ticket_dedup import dedup_ticket_list

    os.environ["ROK21_DEDUP"] = "1" if dedup_on else "0"
    rng = random.Random(SEED)
    ks = []
    unresolved_total = 0
    dup_events_total = 0
    retries_total = 0
    counts_acc = Counter()
    all_sets: list[list[int]] = []
    target = max(packs.keys())
    regen = make_regen(target) if dedup_on else (lambda *a, **k: None)

    t0 = time.perf_counter()
    for i in range(N_SIM):
        batch = assemble_100_off(packs, rng)
        if dedup_on:
            batch, st = dedup_ticket_list(batch, regenerate=regen)
            unresolved_total += int(st["unresolved_count"])
            dup_events_total += int(st["dup_events"])
            retries_total += int(st["retries_used"])
        ks.append(unique_k(batch))
        counts_acc.update(brain_counts(batch))
        if i < collect_n:
            for t in batch:
                all_sets.append(list(t["nums"]))
        if (i + 1) % 200 == 0:
            print(f"  sim {i+1}/{N_SIM} dedup={dedup_on} mean_k={np.mean(ks):.4f}", flush=True)
    elapsed = time.perf_counter() - t0
    return {
        "dedup_on": dedup_on,
        "n_sim": N_SIM,
        "E_k": float(np.mean(ks)),
        "k_min": int(np.min(ks)),
        "k_max": int(np.max(ks)),
        "k_std": float(np.std(ks)),
        "k_all_100": bool(np.all(np.asarray(ks) == 100)),
        "unresolved_total": unresolved_total,
        "dup_events_total": dup_events_total,
        "retries_total": retries_total,
        "brain_counts_sum": dict(counts_acc),
        "brain_counts_mean_per_100": {b: counts_acc[b] / N_SIM for b in BRAINS},
        "elapsed_sec": elapsed,
        "elapsed_per_100_sec": elapsed / N_SIM,
        "sample_sets": all_sets,
    }


def chi2_gof(obs, exp):
    obs = np.asarray(obs, dtype=float)
    exp = np.asarray(exp, dtype=float)
    mask = exp > 0
    obs, exp = obs[mask], exp[mask]
    chi2 = float(np.sum((obs - exp) ** 2 / exp))
    df = max(1, len(obs) - 1)
    p = float(stats.chi2.sf(chi2, df))
    return {"chi2": chi2, "df": df, "p": p}


def theory_combo_features():
    cache = ROOT / "docs" / "benchmarks" / "_c45_6_theory_cache.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    from collections import Counter as C

    sum_c, odd_c, zone_c, consec_c, end_c = C(), C(), C(), C(), C()
    N = comb(45, 6)
    print("enumerating C(45,6)...", flush=True)
    for combo in combinations(range(1, 46), 6):
        sum_c[sum(combo)] += 1
        odd = sum(1 for x in combo if x % 2 == 1)
        odd_c[odd] += 1
        l = sum(1 for x in combo if x <= 15)
        m = sum(1 for x in combo if 16 <= x <= 30)
        h = 6 - l - m
        zone_c[str((l, m, h))] += 1
        sc = sorted(combo)
        consec = sum(1 for i in range(5) if sc[i + 1] - sc[i] == 1)
        consec_c[consec] += 1
        for x in combo:
            end_c[x % 10] += 1
    out = {
        "N": N,
        "sum": {str(k): v for k, v in sum_c.items()},
        "odd": {str(k): v for k, v in odd_c.items()},
        "zone": dict(zone_c),
        "consec": {str(k): v for k, v in consec_c.items()},
        "ending": {str(k): v for k, v in end_c.items()},
    }
    cache.write_text(json.dumps(out), encoding="utf-8")
    return out


def feats_from_sets(sets: list[list[int]]):
    sums, odds, zones, consecs = [], [], [], []
    endings = Counter()
    for s in sets:
        sc = sorted(s)
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


def kt_vs_theory(sets: list[list[int]], theo: dict) -> dict:
    n = len(sets)
    N = theo["N"]
    f = feats_from_sets(sets)
    sum_keys = sorted(int(k) for k in theo["sum"])
    theo_pmf = np.array([theo["sum"][str(k)] / N for k in sum_keys])
    cdf = np.cumsum(theo_pmf)
    xs = np.array(sum_keys, dtype=float)

    def theo_cdf(x):
        idx = np.searchsorted(xs, x, side="right") - 1
        out = np.zeros_like(x, dtype=float)
        out[idx < 0] = 0.0
        m = (idx >= 0) & (idx < len(cdf))
        out[m] = cdf[idx[m]]
        out[idx >= len(cdf)] = 1.0
        return out

    ks = stats.kstest(f["sums"], theo_cdf)
    odd_obs = np.bincount(f["odds"], minlength=7).astype(float)
    odd_exp = np.array([theo["odd"].get(str(k), 0) / N * n for k in range(7)])
    zone_obs = Counter(f["zones"])
    obs_l, exp_l = [], []
    other_o = other_e = 0.0
    for k, cnt in theo["zone"].items():
        e = cnt / N * n
        key = eval(k)  # noqa: S307
        o = zone_obs.get(key, 0)
        if e >= 5:
            obs_l.append(o)
            exp_l.append(e)
        else:
            other_o += o
            other_e += e
    if other_e > 0:
        obs_l.append(other_o)
        exp_l.append(other_e)
    consec_obs = np.bincount(f["consecs"], minlength=6).astype(float)
    consec_exp = np.array([theo["consec"].get(str(k), 0) / N * n for k in range(6)])
    end_obs = np.array([f["endings"].get(d, 0) for d in range(10)], dtype=float)
    end_exp = np.array([theo["ending"].get(str(d), 0) / N * n for d in range(10)])

    out = {
        "n_sets": n,
        "sum_mean": float(f["sums"].mean()),
        "sum_theo": 138.0,
        "sum_ks_p": float(ks.pvalue),
        "odd_chi2": chi2_gof(odd_obs, odd_exp),
        "zone_chi2": chi2_gof(obs_l, exp_l),
        "consec_chi2": chi2_gof(consec_obs, consec_exp),
        "ending_chi2": chi2_gof(end_obs, end_exp),
    }
    ps = {
        "sum_ks_p": out["sum_ks_p"],
        "odd_chi2_p": out["odd_chi2"]["p"],
        "zone_chi2_p": out["zone_chi2"]["p"],
        "consec_chi2_p": out["consec_chi2"]["p"],
        "ending_chi2_p": out["ending_chi2"]["p"],
    }
    out["p_values"] = ps
    out["any_p_lt_0_01"] = any(p < 0.01 for p in ps.values())
    return out


def two_sample_off_on(off_sets, on_sets) -> dict:
    """dedup 왜곡 본검정: OFF vs ON 이표본 (뇌 가중 산출물은 이론 GOF 절대부합 불가)."""
    fo, fn = feats_from_sets(off_sets), feats_from_sets(on_sets)
    sum_ks = stats.ks_2samp(fo["sums"], fn["sums"])
    # odd contingency 2 x 7
    odd_o = np.bincount(fo["odds"], minlength=7)
    odd_n = np.bincount(fn["odds"], minlength=7)
    odd_tbl = np.vstack([odd_o, odd_n])
    # remove zero columns
    odd_tbl = odd_tbl[:, odd_tbl.sum(axis=0) > 0]
    odd_chi = stats.chi2_contingency(odd_tbl)
    zone_keys = sorted(set(fo["zones"]) | set(fn["zones"]))
    z_o = np.array([fo["zones"].count(k) for k in zone_keys], float)
    z_n = np.array([fn["zones"].count(k) for k in zone_keys], float)
    # merge rare
    mask = (z_o + z_n) >= 5
    if (~mask).any():
        z_o = np.concatenate([z_o[mask], [z_o[~mask].sum()]])
        z_n = np.concatenate([z_n[mask], [z_n[~mask].sum()]])
    zone_tbl = np.vstack([z_o, z_n])
    zone_tbl = zone_tbl[:, zone_tbl.sum(axis=0) > 0]
    zone_chi = stats.chi2_contingency(zone_tbl)
    c_o = np.bincount(fo["consecs"], minlength=6)
    c_n = np.bincount(fn["consecs"], minlength=6)
    c_tbl = np.vstack([c_o, c_n])
    c_tbl = c_tbl[:, c_tbl.sum(axis=0) > 0]
    consec_chi = stats.chi2_contingency(c_tbl)
    e_o = np.array([fo["endings"].get(d, 0) for d in range(10)], float)
    e_n = np.array([fn["endings"].get(d, 0) for d in range(10)], float)
    e_tbl = np.vstack([e_o, e_n])
    e_tbl = e_tbl[:, e_tbl.sum(axis=0) > 0]
    end_chi = stats.chi2_contingency(e_tbl)

    ps = {
        "sum_ks2_p": float(sum_ks.pvalue),
        "odd_chi2_p": float(odd_chi.pvalue),
        "zone_chi2_p": float(zone_chi.pvalue),
        "consec_chi2_p": float(consec_chi.pvalue),
        "ending_chi2_p": float(end_chi.pvalue),
    }
    return {
        "p_values": ps,
        "any_p_lt_0_01": any(p < 0.01 for p in ps.values()),
        "sum_mean_off": float(fo["sums"].mean()),
        "sum_mean_on": float(fn["sums"].mean()),
        "note": (
            "절대 이론 GOF는 뇌 가중 산출물에서 OFF/ON 모두 기각됨(대표본). "
            "dedup 왜곡 판정은 OFF vs ON 이표본 p>=0.01 유지 여부."
        ),
    }


def live_pipeline_sets(target_draw_no: int, n_per_brain: int = 5) -> list[dict]:
    from app.testlotto.brains.coordinator import PREDICT_MODULES, _apply_aux_scoring
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.ticket_dedup import dedup_enabled, dedup_ticket_list

    set_learn_as_of(int(target_draw_no))
    draws = _get_draws_before(target_draw_no)
    candidates = []
    for tag in BRAINS:
        candidates.extend(PREDICT_MODULES[tag].predict_sets(draws, n_per_brain))
    scored = _apply_aux_scoring(candidates, draws, target_draw_no)
    scored.sort(key=lambda x: x["confidence"], reverse=True)
    if dedup_enabled():

        def regen(tag, seen, replace_of=None):
            raw = PREDICT_MODULES[tag].predict_sets(draws, 1)
            if not raw:
                return None
            return _apply_aux_scoring(raw, draws, target_draw_no)[0]

        scored, _ = dedup_ticket_list(scored, regenerate=regen)
    return scored


def sha_sets(tickets: list[dict]) -> str:
    from app.testlotto.ticket_dedup import combo_key

    blob = json.dumps(
        [{"b": t["brain_tag"], "n": list(combo_key(t["nums"]))} for t in tickets],
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def main():
    os.environ.setdefault("ROK21_LEARN_CUTOFF", "1")
    packs = load_review_packs()
    print("packs", len(packs), flush=True)

    print("=== OFF sim ===", flush=True)
    off = sim_1000(packs, dedup_on=False)
    off_sets = off.pop("sample_sets")
    print("OFF E[k]", off["E_k"], flush=True)

    print("=== ON sim ===", flush=True)
    on = sim_1000(packs, dedup_on=True)
    on_sets = on.pop("sample_sets")
    print("ON E[k]", on["E_k"], "unresolved", on["unresolved_total"], flush=True)

    theo = theory_combo_features()
    print("=== theory GOF OFF/ON ===", flush=True)
    kt_off = kt_vs_theory(off_sets, theo)
    kt_on = kt_vs_theory(on_sets, theo)
    print("theory_off", kt_off["p_values"], "sum", kt_off["sum_mean"], flush=True)
    print("theory_on", kt_on["p_values"], "sum", kt_on["sum_mean"], flush=True)

    print("=== two-sample OFF vs ON ===", flush=True)
    distort = two_sample_off_on(off_sets, on_sets)
    print(distort["p_values"], "broken", distort["any_p_lt_0_01"], flush=True)

    ratio = {
        "off_mean": off["brain_counts_mean_per_100"],
        "on_mean": on["brain_counts_mean_per_100"],
        "abs_diff": {
            b: abs(off["brain_counts_mean_per_100"][b] - on["brain_counts_mean_per_100"][b])
            for b in BRAINS
        },
        "max_abs_diff": max(
            abs(off["brain_counts_mean_per_100"][b] - on["brain_counts_mean_per_100"][b])
            for b in BRAINS
        ),
    }

    print("=== SHA ===", flush=True)
    os.environ["ROK21_DEDUP"] = "1"
    target = 1234
    random.seed(SEED)
    a = live_pipeline_sets(target, 5)
    random.seed(SEED)
    b = live_pipeline_sets(target, 5)
    sha_a, sha_b = sha_sets(a), sha_sets(b)
    os.environ["ROK21_DEDUP"] = "0"
    random.seed(SEED)
    off1 = live_pipeline_sets(target, 5)
    random.seed(SEED)
    off2 = live_pipeline_sets(target, 5)

    def time_one(dedup_on: bool) -> float:
        os.environ["ROK21_DEDUP"] = "1" if dedup_on else "0"
        from app.testlotto.ticket_dedup import dedup_ticket_list

        batch = assemble_100_off(packs, random.Random(SEED + 7))
        t0 = time.perf_counter()
        if dedup_on:
            dedup_ticket_list(batch, regenerate=make_regen(target))
        else:
            _ = list(batch)
        return time.perf_counter() - t0

    time_one(False)
    t_off = float(np.mean([time_one(False) for _ in range(20)]))
    t_on = float(np.mean([time_one(True) for _ in range(20)]))

    p_off = off["E_k"] / TOTAL
    p_on = 100.0 / TOTAL
    # Gate: E[k], unresolved0, two-sample no distort, brain ratio, sha
    # Theory absolute: report only — brains fail both OFF/ON (documented)
    gate = {
        "off_near_97": abs(off["E_k"] - 97.0615) < 1.0,
        "on_exact_100": bool(on["k_all_100"]) and abs(on["E_k"] - 100.0) < 1e-9,
        "unresolved_zero": on["unresolved_total"] == 0,
        "distort_ok_off_vs_on": not distort["any_p_lt_0_01"],
        "brain_ratio_unchanged": ratio["max_abs_diff"] < 1e-9,
        "sha_ok": sha_a == sha_b,
        "theory_note": (
            "절대이론 GOF는 OFF/ON 모두 대표본에서 기각(뇌 가중). "
            "왜곡게이트=이표본. theory_on.any_p_lt_0_01="
            f"{kt_on['any_p_lt_0_01']}"
        ),
    }
    gate["pass_step2"] = all(
        [
            gate["off_near_97"],
            gate["on_exact_100"],
            gate["unresolved_zero"],
            gate["distort_ok_off_vs_on"],
            gate["brain_ratio_unchanged"],
            gate["sha_ok"],
        ]
    )

    result = {
        "meta": {"seed": SEED, "n_sim": N_SIM, "total_combos": TOTAL},
        "step2_1": {"off": off, "on": on},
        "step2_2_theory_gof": {"off": kt_off, "on": kt_on},
        "step2_2_distort_off_vs_on": distort,
        "step2_3_brain_ratio": ratio,
        "step2_4_sha": {
            "on_run1": sha_a,
            "on_run2": sha_b,
            "on_match": sha_a == sha_b,
            "off_match": sha_sets(off1) == sha_sets(off2),
            "off_sha": sha_sets(off1),
        },
        "step2_5_timing": {
            "off_sec_mean20": t_off,
            "on_sec_mean20": t_on,
            "delta_sec": t_on - t_off,
            "over_2s": (t_on - t_off) > 2.0,
        },
        "step3_prob": {
            "k_off": off["E_k"],
            "k_on": 100.0,
            "p_off": p_off,
            "p_on": p_on,
            "ratio_100_over_k_off": 100.0 / off["E_k"],
            "p_on_explicit": "100/8145060",
            "p_off_explicit": f"{off['E_k']}/8145060",
            "p_on_via_scale": f"{p_off} * (100/{off['E_k']}) = {p_on}",
            "disclaimer": (
                "이 개선은 조합 낭비를 없앤 것이며, 예측력 향상이 아니다. "
                "단일 회차 1등 확률은 여전히 100/8,145,060 ≈ 1.23e-5 이다."
            ),
        },
        "gate": gate,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT, flush=True)
    print("GATE", gate, flush=True)


if __name__ == "__main__":
    main()
