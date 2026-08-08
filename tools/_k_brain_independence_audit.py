# -*- coding: utf-8 -*-
"""K-BRAIN-INDEPENDENCE-AUDIT — 3뇌 독립·10세트 완전성 버그 사냥 (READ-ONLY).

형 지시 (20260808): 「각 뇌별 독립적으로 예측번호 공유 X · 각 독립적으로 뇌별
몰아주기 · 각 뇌가 10세트 예측하는지 한번 더 버그를 찾아보자」

성적을 재지 않는다. **구조가 깨졌는지**만 본다.

검사 항목
  A 10세트 완전성
    A1 뇌별 pool 세트 수가 정확히 10 인가
    A2 set_no 가 1~10 빠짐없이 붙었는가
    A3 세트마다 번호 6개 · 1~45 · 세트 내 중복 없음
    A4 **뇌별 10세트 안에 똑같은 세트가 있는가** — pass0/pass1 은 시드만 다르므로
       뇌가 난수를 안 쓰면 두 pass 가 동일해져 10세트가 실은 5세트가 된다
    A5 뇌별 몰아주기가 정확히 5세트인가 · 5세트 안에 중복이 없는가
  B 뇌 간 번호 공유
    B1 서로 다른 뇌가 **완전히 같은 세트**를 낸 횟수 (pool)
    B2 같은 것 (몰아주기)
    B3 뇌 간 번호 겹침 정도 — 우연 기대치와 비교
  C 독립성
    C1 한 뇌만 단독 실행해도 합동 실행과 같은가 (RNG 오염)
    C2 한 뇌의 결과만 학습에 먹였을 때 **다른 뇌 성적표가 안 변하는가**
  D 학습 상태
    D1 뇌별 learn_state 가 분리되어 있는가

Usage
  python tools/_k_brain_independence_audit.py
  K_BA_LO=1226 K_BA_HI=1235 python tools/_k_brain_independence_audit.py
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

AUDIT_ID = "K-BRAIN-INDEPENDENCE-AUDIT"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KBRAIN_INDEP_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260808_KBRAIN_INDEP_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

DEFAULT_LO = 1216
WARM_BACK = 200
EXPECT_POOL = 10
EXPECT_REPACK = 5
SEP3 = "|---|---|---|"
SEP4 = "|---|---|---|---|"


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    return int(v) if v else default


def _max_draw_no() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    row = conn.execute("SELECT MAX(draw_no) AS m FROM lotto_draws").fetchone()
    conn.close()
    return int(dict(row)["m"])


def _key(nums: Any) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def _pool_and_repack(dno: int, seed: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp

    learner = sp.RollingSignalLearner()
    sp.warm_learner_to_draw(learner, max(1, dno - WARM_BACK), dno, seed=seed)
    num_all, pos_all = learner.snapshot()

    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    random.seed(seed)
    pool_br = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))
    hint = sp._build_hint(draws, dno)
    rows = sp.repack_by_brain(pool_br, hint, num_all, pos_all, target_draw_no=dno)
    rp_br: dict[str, list[dict]] = {}
    for r in rows:
        rp_br.setdefault(str(r.get("brain_tag") or ""), []).append(r)
    return {"pool_br": pool_br, "repack_br": rp_br, "num_all": num_all, "pos_all": pos_all}


def _audit_completeness(pool_br: dict, rp_br: dict, tags: list[str]) -> dict[str, Any]:
    """A1~A5 — 세트 수·번호 형식·중복."""
    out: dict[str, Any] = {}
    for tag in tags:
        pool = pool_br.get(tag, [])
        keys = [_key(c["nums"]) for c in pool]
        sns = sorted(int(c.get("pred_set_no") or 0) for c in pool)
        bad_form = [
            k
            for k in keys
            if len(k) != 6 or len(set(k)) != 6 or min(k) < 1 or max(k) > 45
        ]
        dup_pool = len(keys) - len(set(keys))

        rp = rp_br.get(tag, [])
        rp_keys = [_key(r["nums"]) for r in rp]
        out[tag] = {
            "n_pool": len(pool),
            "pool_count_ok": len(pool) == EXPECT_POOL,
            "set_nos": sns,
            "set_nos_ok": sns == list(range(1, EXPECT_POOL + 1)),
            "bad_form_count": len(bad_form),
            "dup_sets_in_pool10": dup_pool,
            "n_unique_pool_sets": len(set(keys)),
            "n_repack": len(rp),
            "repack_count_ok": len(rp) == EXPECT_REPACK,
            "dup_sets_in_repack5": len(rp_keys) - len(set(rp_keys)),
            "pass0_equals_pass1": (
                sorted(keys[:5]) == sorted(keys[5:]) if len(keys) == 10 else None
            ),
        }
    return out


def _audit_cross_share(pool_br: dict, rp_br: dict, tags: list[str]) -> dict[str, Any]:
    """B1~B3 — 뇌 간 세트 동일·번호 겹침."""
    pool_keys = {t: {_key(c["nums"]) for c in pool_br.get(t, [])} for t in tags}
    rp_keys = {t: {_key(r["nums"]) for r in rp_br.get(t, [])} for t in tags}
    pool_nums = {t: {n for k in pool_keys[t] for n in k} for t in tags}

    pairs: dict[str, Any] = {}
    for i, a in enumerate(tags):
        for b in tags[i + 1 :]:
            inter_n = pool_nums[a] & pool_nums[b]
            union_n = pool_nums[a] | pool_nums[b]
            pairs[f"{a}|{b}"] = {
                "identical_pool_sets": len(pool_keys[a] & pool_keys[b]),
                "identical_repack_sets": len(rp_keys[a] & rp_keys[b]),
                "number_jaccard": round(len(inter_n) / len(union_n), 6) if union_n else 0.0,
                "n_numbers_a": len(pool_nums[a]),
                "n_numbers_b": len(pool_nums[b]),
            }
    return pairs


def _audit_repack_provenance(pool_br: dict, rp_br: dict, tags: list[str]) -> dict[str, Any]:
    """B3 — 몰아주기 세트의 번호가 **자기 뇌 pool** 에서 왔는가.

    `number_scores` 는 1~45 전체에 점수를 매기므로, 자기 뇌 pool 에 한 번도 안 나온
    번호가 점수 상위에 올라 발권될 수 있다. 그 유입 경로 중 하나가 `hint` 이고
    hint 는 **3뇌 공유**다. 즉 이 비율이 낮으면 「예측번호 공유」가 실제로 일어난다.
    """
    out: dict[str, Any] = {}
    score_nums: dict[str, set[int]] = {}
    for tag in tags:
        own = {int(n) for c in pool_br.get(tag, []) for n in c["nums"]}
        rows = rp_br.get(tag, [])
        stat, sc = _one_brain_provenance(rows, own)
        score_nums[tag] = sc
        out[tag] = {**stat, "n_own_pool_numbers": len(own)}
    return {
        "by_brain": out,
        "score_set_overlap": _pairwise_overlap(score_nums, tags),
    }


def _one_brain_provenance(
    rows: list[dict], own: set[int]
) -> tuple[dict[str, Any], set[int]]:
    """한 뇌의 몰아주기 5세트에서 자기 pool 출신 번호 비율. (통계, 점수세트 번호집합)"""
    # pool 통째보존 세트는 당연히 자기 pool → 점수조립 세트를 따로 본다
    all_nums: list[int] = []
    sc_nums: list[int] = []
    n_pool_src = 0
    for r in rows:
        nums = [int(x) for x in r["nums"]]
        all_nums += nums
        if str(r.get("source") or "score_repack") == "pool":
            n_pool_src += 1
        else:
            sc_nums += nums

    tot, tot_sc = len(all_nums), len(sc_nums)
    inside = sum(1 for n in all_nums if n in own)
    inside_sc = sum(1 for n in sc_nums if n in own)
    sc = set(sc_nums)
    return (
        {
            "own_pool_ratio_all": round(inside / tot, 6) if tot else 0.0,
            "own_pool_ratio_score_sets": round(inside_sc / tot_sc, 6) if tot_sc else None,
            "n_numbers_all": tot,
            "n_numbers_score_sets": tot_sc,
            "n_rows_from_pool": n_pool_src,
            "n_rows_from_score": len(rows) - n_pool_src,
        },
        sc,
    )


def _pairwise_overlap(nums_by_tag: dict[str, set[int]], tags: list[str]) -> dict[str, Any]:
    """점수조립 세트의 번호가 뇌 간에 얼마나 겹치는가 (공유 hint 의 실제 영향)."""
    ov: dict[str, Any] = {}
    for i, a in enumerate(tags):
        for b in tags[i + 1 :]:
            sa, sb = nums_by_tag[a], nums_by_tag[b]
            u = sa | sb
            ov[f"{a}|{b}"] = {
                "score_num_jaccard": round(len(sa & sb) / len(u), 6) if u else 0.0,
                "n_shared": len(sa & sb),
                "n_a": len(sa),
                "n_b": len(sb),
            }
    return ov


def _expected_jaccard(n_a: int, n_b: int, universe: int = 45) -> dict[str, float]:
    """무작위로 골랐다면 기대되는 겹침. 45개 중 n_a·n_b 개를 독립으로 고를 때."""
    exp_shared = n_a * n_b / universe
    denom = n_a + n_b - exp_shared
    return {
        "expected_shared": round(exp_shared, 4),
        "expected_jaccard": round(exp_shared / denom, 6) if denom else 0.0,
    }


def _score_numbers(dno: int, seed: int, tags: list[str], *, kill_hint: bool) -> dict[str, set[int]]:
    """점수조립 세트가 쓰는 번호 집합. kill_hint=True 면 hint 가중치를 0 으로 둔다."""
    import app.testlotto.signal_pool as sp

    saved = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    try:
        if kill_hint:
            # hint 를 빼고 남은 두 축(freq·learn)의 상대비를 유지하며 재정규화
            for t, (_wh, wf, wl) in saved.items():
                s = wf + wl
                sp.SCORE_WEIGHTS_BY_BRAIN[t] = (0.0, wf / s, wl / s) if s else (0.0, 0.5, 0.5)
        st = _pool_and_repack(dno, seed)
        out: dict[str, set[int]] = {}
        for t in tags:
            nums: set[int] = set()
            for r in st["repack_br"].get(t, []):
                if str(r.get("source") or "score_repack") != "pool":
                    nums |= {int(x) for x in r["nums"]}
            out[t] = nums
        return out
    finally:
        sp.SCORE_WEIGHTS_BY_BRAIN.clear()
        sp.SCORE_WEIGHTS_BY_BRAIN.update(saved)


def _audit_hint_attribution(dno: int, seed: int, tags: list[str]) -> dict[str, Any]:
    """B5 — 뇌 간 번호 겹침이 **공유 hint 때문인가**를 절제(ablation)로 가른다.

    hint 가중치만 0 으로 두고 다시 조립해 겹침이 떨어지는지 본다. 성적을 재는 게
    아니라 **원인을 지목하는** 측정이므로 R38 게이트 대상이 아니다.
    """
    with_hint = _score_numbers(dno, seed, tags, kill_hint=False)
    no_hint = _score_numbers(dno, seed, tags, kill_hint=True)

    def _pairs(d: dict[str, set[int]]) -> dict[str, Any]:
        r: dict[str, Any] = {}
        for i, a in enumerate(tags):
            for b in tags[i + 1 :]:
                u = d[a] | d[b]
                sh = len(d[a] & d[b])
                exp = _expected_jaccard(len(d[a]), len(d[b]))
                r[f"{a}|{b}"] = {
                    "shared": sh,
                    "jaccard": round(sh / len(u), 6) if u else 0.0,
                    **exp,
                }
        return r

    pw, pn = _pairs(with_hint), _pairs(no_hint)
    drops = [pw[k]["jaccard"] - pn[k]["jaccard"] for k in pw]
    return {
        "draw_no": dno,
        "with_hint": pw,
        "hint_weight_zero": pn,
        "jaccard_drop_mean": round(mean(drops), 6) if drops else 0.0,
        "hint_is_main_driver": bool(drops and mean(drops) > 0.05),
        "note_ko": (
            "무작위 기대치(expected_jaccard)보다 관측 겹침이 크고, hint 를 끄면 "
            "겹침이 내려간다면 공유 hint 가 뇌 간 번호 공유의 원인이다"
        ),
    }


def _audit_config_liveness(dno: int, seed: int, tags: list[str]) -> dict[str, Any]:
    """B6 — 뇌별 설정 dict 가 **실제로 읽히는가** (죽은 배선 탐지).

    값을 바꿨는데 결과가 그대로면 그 설정은 어디서도 조회되지 않는다는 뜻이다.
    `repack_by_brain` 이 `number_scores` 에 `brain_tag` 를 안 넘겨 뇌별 가중치가
    조용히 무시됐던 버그(K-REPACK-BRAINTAG-DEAD-WIRE)를 잡은 검사다.
    """
    import app.testlotto.signal_pool as sp

    def _fingerprint() -> str:
        st = _pool_and_repack(dno, seed)
        return "|".join(
            f"{t}:" + ",".join(str(_key(r["nums"])) for r in st["repack_br"].get(t, []))
            for t in tags
        )

    base = _fingerprint()
    out: dict[str, Any] = {}

    saved_w = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    try:
        for t in tags:
            sp.SCORE_WEIGHTS_BY_BRAIN[t] = (0.0, 0.0, 1.0)
        out["SCORE_WEIGHTS_BY_BRAIN"] = {"live": _fingerprint() != base}
    finally:
        sp.SCORE_WEIGHTS_BY_BRAIN.clear()
        sp.SCORE_WEIGHTS_BY_BRAIN.update(saved_w)

    saved_s = dict(sp.POOL_SLOTS_BY_BRAIN)
    try:
        for t in tags:
            sp.POOL_SLOTS_BY_BRAIN[t] = 5
        out["POOL_SLOTS_BY_BRAIN"] = {"live": _fingerprint() != base}
    finally:
        sp.POOL_SLOTS_BY_BRAIN.clear()
        sp.POOL_SLOTS_BY_BRAIN.update(saved_s)

    saved_h = dict(sp.HINT_SPEC_BY_BRAIN)
    try:
        # 뇌마다 다른 (창, 신호) 를 줘서 hint 축이 실제로 갈라지는지 본다
        alt = [(4, "odd_even"), (12, "sum_band"), (52, "miss_pattern")]
        for i, t in enumerate(tags):
            sp.HINT_SPEC_BY_BRAIN[t] = alt[i % len(alt)]
        out["HINT_SPEC_BY_BRAIN"] = {
            "live": _fingerprint() != base,
            "shared_flag_flips": not sp.hint_shared_across_brains(),
        }
    finally:
        sp.HINT_SPEC_BY_BRAIN.clear()
        sp.HINT_SPEC_BY_BRAIN.update(saved_h)

    saved_e = dict(sp.LEARN_EMA_BY_BRAIN)
    try:
        for t in tags:
            sp.LEARN_EMA_BY_BRAIN[t] = 0.99
        out["LEARN_EMA_BY_BRAIN"] = {"live": _fingerprint() != base}
    finally:
        sp.LEARN_EMA_BY_BRAIN.clear()
        sp.LEARN_EMA_BY_BRAIN.update(saved_e)

    # 원상복구 확인 — 되돌린 뒤 지문이 처음과 같아야 한다
    out["restored_ok"] = _fingerprint() == base
    out["all_live"] = all(v["live"] for k, v in out.items() if isinstance(v, dict))
    return out


def _audit_learner_isolation(dno: int, seed: int, tags: list[str]) -> dict[str, Any]:
    """C2 — 한 뇌 결과만 학습에 먹였을 때 다른 뇌 성적표가 안 변하는가."""
    import app.testlotto.signal_pool as sp
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    row = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?", (dno,)
    ).fetchone()
    conn.close()
    d = dict(row)
    actual = {int(d[f"num{k}"]) for k in range(1, 7)}

    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    random.seed(seed)
    pool_br = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))

    out: dict[str, Any] = {}
    for fed in tags:
        learner = sp.RollingSignalLearner()
        learner.update_from_pool({fed: pool_br.get(fed, [])}, actual)
        _, pos = learner.snapshot()
        others_changed = [
            t for t in tags if t != fed and any(v > 0 for v in (pos.get(t) or {}).values())
        ]
        fed_changed = any(v > 0 for v in (pos.get(fed) or {}).values())
        out[fed] = {
            "fed_brain_updated": bool(fed_changed),
            "other_brains_leaked": others_changed,
            "isolated": not others_changed,
        }
    return out


def _audit_rng_independence(dno: int, seed: int, tags: list[str]) -> dict[str, Any]:
    """C1 — 단독 실행 == 합동 실행."""
    import app.testlotto.signal_pool as sp
    from tools._k_window_signal_survey import PREDICT_MODULES

    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    joint = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))

    out: dict[str, Any] = {}
    for tag in tags:
        mod = PREDICT_MODULES.get(tag)
        if mod is None:
            continue
        solo: list[tuple[int, ...]] = []
        for pass_idx in range(2):
            random.seed(sp._pass_seed(seed, dno, pass_idx))
            solo += [_key(c["nums"]) for c in mod.predict_sets(draws, sp.SETS_PER_PREDICT_BRAIN)]
        got = [
            _key(c["nums"])
            for c in sorted(joint.get(tag, []), key=lambda x: int(x.get("pred_set_no") or 0))
        ]
        out[tag] = {"solo_equals_joint": solo == got, "n_solo": len(solo), "n_joint": len(got)}
    return out


def _audit_learn_state(tags: list[str]) -> dict[str, Any]:
    """D1 — learn_state 가 뇌별로 분리되어 있는가 (리셋 후엔 비어 있는 게 정상)."""
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    rows = [
        dict(r)
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) AS n FROM testlotto_brain_learn_state GROUP BY brain_tag"
        )
    ]
    conn.close()
    by_tag = {str(r["brain_tag"]): int(r["n"]) for r in rows}
    return {
        "rows_by_brain": by_tag,
        "table_empty": not by_tag,
        "note_ko": (
            "K-PREDICT-RESET 로 비운 상태가 정상. 값이 있으면 뇌별 1행씩이어야 한다"
        ),
        "one_row_per_brain": all(by_tag.get(t, 0) <= 1 for t in tags),
    }


def run(lo: int, hi: int, seed: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp

    tags = list(sp.BRAIN_TAGS)
    per_draw: list[dict[str, Any]] = []
    for dno in range(lo, hi + 1):
        st = _pool_and_repack(dno, seed)
        per_draw.append(
            {
                "draw_no": dno,
                "completeness": _audit_completeness(st["pool_br"], st["repack_br"], tags),
                "cross_share": _audit_cross_share(st["pool_br"], st["repack_br"], tags),
                "provenance": _audit_repack_provenance(st["pool_br"], st["repack_br"], tags),
            }
        )
        print(f"  {dno} ok", flush=True)

    return {
        "tags": tags,
        "per_draw": per_draw,
        "aggregate": _aggregate(per_draw, tags),
        "b5_hint_attribution": _audit_hint_attribution(hi, seed, tags),
        "b6_config_liveness": _audit_config_liveness(hi, seed, tags),
        "c1_rng_independence": _audit_rng_independence(hi, seed, tags),
        "c2_learner_isolation": _audit_learner_isolation(hi, seed, tags),
        "d1_learn_state": _audit_learn_state(tags),
    }


def _aggregate(per_draw: list[dict], tags: list[str]) -> dict[str, Any]:
    comp: dict[str, Any] = {}
    for tag in tags:
        recs = [d["completeness"][tag] for d in per_draw if tag in d["completeness"]]
        if not recs:
            continue
        comp[tag] = {
            "n_draws": len(recs),
            "pool_count_all_ok": all(r["pool_count_ok"] for r in recs),
            "set_nos_all_ok": all(r["set_nos_ok"] for r in recs),
            "bad_form_total": sum(r["bad_form_count"] for r in recs),
            "dup_in_pool10_total": sum(r["dup_sets_in_pool10"] for r in recs),
            "draws_with_dup_pool": sum(1 for r in recs if r["dup_sets_in_pool10"] > 0),
            "unique_pool_sets_mean": round(mean(r["n_unique_pool_sets"] for r in recs), 4),
            "repack_count_all_ok": all(r["repack_count_ok"] for r in recs),
            "dup_in_repack5_total": sum(r["dup_sets_in_repack5"] for r in recs),
            "pass0_equals_pass1_count": sum(1 for r in recs if r["pass0_equals_pass1"]),
        }

    pair_names = list(per_draw[0]["cross_share"].keys()) if per_draw else []
    cross: dict[str, Any] = {}
    for p in pair_names:
        recs = [d["cross_share"][p] for d in per_draw]
        cross[p] = {
            "identical_pool_sets_total": sum(r["identical_pool_sets"] for r in recs),
            "draws_with_identical_pool": sum(1 for r in recs if r["identical_pool_sets"] > 0),
            "identical_repack_sets_total": sum(r["identical_repack_sets"] for r in recs),
            "draws_with_identical_repack": sum(
                1 for r in recs if r["identical_repack_sets"] > 0
            ),
            "number_jaccard_mean": round(mean(r["number_jaccard"] for r in recs), 6),
        }

    prov: dict[str, Any] = {}
    for tag in tags:
        recs = [d["provenance"]["by_brain"][tag] for d in per_draw]
        sc = [r["own_pool_ratio_score_sets"] for r in recs if r["own_pool_ratio_score_sets"] is not None]
        prov[tag] = {
            "own_pool_ratio_all_mean": round(mean(r["own_pool_ratio_all"] for r in recs), 6),
            "own_pool_ratio_score_sets_mean": round(mean(sc), 6) if sc else None,
            "rows_from_pool_mean": round(mean(r["n_rows_from_pool"] for r in recs), 4),
            "rows_from_score_mean": round(mean(r["n_rows_from_score"] for r in recs), 4),
            "own_pool_numbers_mean": round(mean(r["n_own_pool_numbers"] for r in recs), 4),
        }
    sc_ov: dict[str, Any] = {}
    for p in (per_draw[0]["provenance"]["score_set_overlap"].keys() if per_draw else []):
        recs = [d["provenance"]["score_set_overlap"][p] for d in per_draw]
        sc_ov[p] = {
            "score_num_jaccard_mean": round(mean(r["score_num_jaccard"] for r in recs), 6),
            "n_shared_mean": round(mean(r["n_shared"] for r in recs), 4),
        }
    return {
        "completeness": comp,
        "cross_share": cross,
        "provenance": prov,
        "score_set_overlap": sc_ov,
    }


def _checks_a(comp: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """A군 — 10세트 완전성."""
    checks: dict[str, dict[str, Any]] = {}
    checks["A1_뇌별_10세트"] = {
        "pass": all(v["pool_count_all_ok"] for v in comp.values()),
        "detail_ko": f"3뇌 모두 매 회차 정확히 {EXPECT_POOL}세트",
    }
    checks["A2_set_no_1~10"] = {
        "pass": all(v["set_nos_all_ok"] for v in comp.values()),
        "detail_ko": "set_no 가 1~10 빠짐없이 붙었다",
    }
    checks["A3_번호형식"] = {
        "pass": all(v["bad_form_total"] == 0 for v in comp.values()),
        "detail_ko": "세트마다 1~45 범위의 서로 다른 번호 6개",
    }
    dup_total = sum(v["dup_in_pool10_total"] for v in comp.values())
    checks["A4_10세트내_중복없음"] = {
        "pass": dup_total == 0,
        "detail_ko": (
            "10세트가 전부 서로 다르다"
            if dup_total == 0
            else f"**중복 {dup_total}건** — pass0/pass1 이 같은 세트를 냈다 "
            "= 실제로는 10세트가 아니다"
        ),
        "dup_total": dup_total,
        "by_brain": {t: v["dup_in_pool10_total"] for t, v in comp.items()},
        "unique_mean": {t: v["unique_pool_sets_mean"] for t, v in comp.items()},
    }
    checks["A5_몰아주기_5세트"] = {
        "pass": all(
            v["repack_count_all_ok"] and v["dup_in_repack5_total"] == 0
            for v in comp.values()
        ),
        "detail_ko": f"3뇌 모두 {EXPECT_REPACK}세트 · 5세트 안에 중복 없음",
    }
    return checks


def _checks_b(res: dict[str, Any], agg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """B군 — 뇌 간 공유·출처·설정 생존."""
    cross = agg["cross_share"]
    checks: dict[str, dict[str, Any]] = {}
    checks["B1_뇌간_동일세트_없음"] = {
        "pass": all(v["identical_pool_sets_total"] == 0 for v in cross.values()),
        "detail_ko": "서로 다른 뇌가 완전히 같은 세트를 낸 적 없다",
        "by_pair": {k: v["identical_pool_sets_total"] for k, v in cross.items()},
    }
    checks["B2_몰아주기_동일세트_없음"] = {
        "pass": all(v["identical_repack_sets_total"] == 0 for v in cross.values()),
        "detail_ko": "뇌 간 몰아주기 세트가 겹치지 않는다",
        "by_pair": {k: v["identical_repack_sets_total"] for k, v in cross.items()},
    }
    prov = agg["provenance"]
    checks["B3_몰아주기_pool슬롯_확보"] = {
        "pass": all(v["rows_from_pool_mean"] > 0 for v in prov.values()),
        "detail_ko": "3뇌 모두 자기 pool 세트를 통째로 보존한 자리가 있다",
        "by_brain": {t: v["rows_from_pool_mean"] for t, v in prov.items()},
    }
    checks["B4_점수세트_pool외_번호유입"] = {
        # 통과/실패가 아니라 **수치를 드러내는** 항목. 1.0 이면 자기 pool 안에서만 골랐다는 뜻
        "pass": True,
        "detail_ko": (
            "점수조립 세트의 번호 중 자기 pool 출신 비율 — "
            + " · ".join(
                f"{t} {v['own_pool_ratio_score_sets_mean']}"
                for t, v in prov.items()
                if v["own_pool_ratio_score_sets_mean"] is not None
            )
            + " (1.0 미만이면 공유 hint 등 pool 밖 경로로 번호가 들어왔다)"
        ),
        "by_brain": {t: v["own_pool_ratio_score_sets_mean"] for t, v in prov.items()},
        "cross_brain_score_num_jaccard": agg["score_set_overlap"],
        "is_informational": True,
    }
    ha = res["b5_hint_attribution"]
    _pw = ha["with_hint"]
    _obs = mean(v["jaccard"] for v in _pw.values()) if _pw else 0.0
    _exp = mean(v["expected_jaccard"] for v in _pw.values()) if _pw else 0.0
    checks["B5_겹침원인_공유hint"] = {
        "pass": True,
        "detail_ko": (
            f"관측 겹침 {_obs:.4f} vs 무작위 기대 {_exp:.4f} · "
            f"hint 가중치 0 으로 두면 {ha['jaccard_drop_mean']:+.4f} 변화 → "
            + ("**공유 hint 가 주원인**" if ha["hint_is_main_driver"] else "hint 단독 원인은 아님")
        ),
        "observed_jaccard_mean": round(_obs, 6),
        "expected_by_chance_mean": round(_exp, 6),
        "jaccard_drop_when_hint_off": ha["jaccard_drop_mean"],
        "hint_is_main_driver": ha["hint_is_main_driver"],
        "is_informational": True,
    }
    cl = res["b6_config_liveness"]
    checks["B6_뇌별설정_살아있음"] = {
        "pass": bool(cl["all_live"] and cl["restored_ok"]),
        "detail_ko": (
            "뇌별 설정 dict 를 바꾸면 결과가 바뀐다 (죽은 배선 아님) — "
            + " · ".join(
                f"{k} {'O' if v['live'] else '**X**'}"
                for k, v in cl.items()
                if isinstance(v, dict)
            )
        ),
        "by_config": {k: v for k, v in cl.items() if isinstance(v, dict)},
        "restored_ok": cl["restored_ok"],
    }
    return checks


def _checks_cd(res: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """C·D군 — 독립성·학습상태."""
    checks: dict[str, dict[str, Any]] = {}
    checks["C1_RNG독립"] = {
        "pass": all(v["solo_equals_joint"] for v in res["c1_rng_independence"].values()),
        "detail_ko": "단독 실행이 합동 실행과 같다 (뇌 간 난수 오염 없음)",
    }
    checks["C2_학습_교차오염없음"] = {
        "pass": all(v["isolated"] for v in res["c2_learner_isolation"].values()),
        "detail_ko": "한 뇌 결과만 먹이면 그 뇌 성적표만 바뀐다",
        "by_brain": res["c2_learner_isolation"],
    }
    checks["D1_learn_state_뇌별"] = {
        "pass": bool(res["d1_learn_state"]["one_row_per_brain"]),
        "detail_ko": "learn_state 가 뇌별 1행 이하 (리셋 후 비어 있음이 정상)",
    }
    return checks


def verdict(res: dict[str, Any]) -> dict[str, Any]:
    agg = res["aggregate"]
    checks: dict[str, dict[str, Any]] = {
        **_checks_a(agg["completeness"]),
        **_checks_b(res, agg),
        **_checks_cd(res),
    }

    n_pass = sum(1 for v in checks.values() if v["pass"])
    fails = [k for k, v in checks.items() if not v["pass"]]
    return {
        "checks": checks,
        "n_pass": n_pass,
        "n_total": len(checks),
        "all_pass": not fails,
        "failed": fails,
        "code": "INDEPENDENCE_OK" if not fails else "BUG_FOUND",
    }


def build_md(p: dict[str, Any]) -> str:
    v = p["verdict"]
    agg = p["result"]["aggregate"]
    L = [
        f"# {AUDIT_ID} — 3뇌 독립·10세트 완전성 감사",
        "",
        f"- 생성 {p['generated_at']} · 회차 {p['range'][0]}~{p['range'][1]} · seed {p['seed']}",
        f"- **{v['code']}** · {v['n_pass']}/{v['n_total']} 통과",
        "",
        "## 0. 이 감사는 성적을 재지 않는다",
        "",
        "형 지시 「각 뇌별 독립적으로 예측번호 공유 X · 각 독립적으로 뇌별 몰아주기 ·",
        "각 뇌가 10세트 예측하는지 한번 더 버그를 찾아보자」에 대한 구조 점검이다.",
        "",
        "## 1. 검사 결과",
        "",
        "|검사|통과|내용|",
        SEP3,
    ]
    for k, c in v["checks"].items():
        L.append(f"|{k}|{'O' if c['pass'] else '**X**'}|{c['detail_ko']}|")

    L += [
        "",
        "## 2. 10세트 완전성 — 뇌별",
        "",
        "|뇌|회차|10세트|set_no|형식오류|10세트내 중복|고유세트 평균|몰아주기 5|",
        "|---|---|---|---|---|---|---|---|",
    ]
    for t, a in agg["completeness"].items():
        L.append(
            f"|{t}|{a['n_draws']}|{'O' if a['pool_count_all_ok'] else 'X'}|"
            f"{'O' if a['set_nos_all_ok'] else 'X'}|{a['bad_form_total']}|"
            f"**{a['dup_in_pool10_total']}**|{a['unique_pool_sets_mean']}|"
            f"{'O' if a['repack_count_all_ok'] else 'X'}|"
        )

    L += [
        "",
        "## 3. 뇌 간 공유 — 쌍별",
        "",
        "|뇌 쌍|동일 pool 세트|동일 몰아주기 세트|번호 겹침(Jaccard)|",
        SEP4,
    ]
    for k, c in agg["cross_share"].items():
        L.append(
            f"|{k}|{c['identical_pool_sets_total']}|"
            f"{c['identical_repack_sets_total']}|{c['number_jaccard_mean']:.4f}|"
        )
    L += [
        "",
        "번호 겹침은 **0이 될 수 없다.** 3뇌가 같은 45개 번호에서 고르므로 겹치는 게",
        "정상이다. 문제가 되는 것은 **세트가 통째로 같아지는 경우**(위 두 열)다.",
        "",
        "## 3b. 몰아주기 번호의 출처 — 공유 hint 의 실제 영향",
        "",
        "|뇌|pool 통째보존 자리|점수조립 자리|점수세트 번호의 자기 pool 출신 비율|",
        SEP4,
    ]
    for t, a in agg["provenance"].items():
        L.append(
            f"|{t}|{a['rows_from_pool_mean']}|{a['rows_from_score_mean']}|"
            f"**{a['own_pool_ratio_score_sets_mean']}**|"
        )
    L += [
        "",
        "|뇌 쌍|점수세트 번호 겹침(Jaccard)|공유 번호 개수|",
        SEP3,
    ]
    for k, a in agg["score_set_overlap"].items():
        L.append(f"|{k}|{a['score_num_jaccard_mean']:.4f}|{a['n_shared_mean']}|")
    L += [
        "",
        "마지막 열이 **1.0 이면 자기 뇌 pool 안에서만 골랐다**는 뜻이다. 1.0 보다 작으면",
        "`hint` 같은 pool 밖 경로로 번호가 들어왔다는 뜻이고, hint 는 3뇌 공유이므로",
        "그만큼 **뇌 간에 같은 번호가 밀려들어간다.**",
        "",
        "## 3c. 겹침의 원인 — hint 절제(ablation)",
        "",
        "겹침이 우연인지 공유 hint 때문인지 가른다. hint 가중치만 0 으로 두고 다시",
        "조립해 겹침이 내려가는지 본다. 성적이 아니라 **원인**을 재는 것이다.",
        "",
        "|뇌 쌍|관측 겹침|무작위 기대|hint 끈 뒤|",
        SEP4,
    ]
    ha = p["result"]["b5_hint_attribution"]
    for k, a in ha["with_hint"].items():
        off = ha["hint_weight_zero"][k]["jaccard"]
        L.append(f"|{k}|**{a['jaccard']:.4f}**|{a['expected_jaccard']:.4f}|{off:.4f}|")
    L += [
        "",
        f"- hint 를 끄면 겹침이 평균 **{ha['jaccard_drop_mean']:+.4f}** 변한다",
        f"- 판정: {'**공유 hint 가 주원인**' if ha['hint_is_main_driver'] else 'hint 단독 원인은 아님'}",
        "",
        "## 4. 한계",
        "",
        "- 구조 점검이며 적중률과 무관하다",
        "- `hint` 는 여전히 3뇌 공유다 (설계상 알려진 미해결 · 별도 튜닝 과제)",
        "",
    ]
    return "\n".join(L)


def main() -> None:
    import app.testlotto.signal_pool as sp

    hi = _env_int("K_BA_HI", 0) or _max_draw_no()
    lo = _env_int("K_BA_LO", 0) or DEFAULT_LO
    seed = _env_int("K_BA_SEED", sp.MC_SEED)

    print(f"[{AUDIT_ID}] {lo}~{hi} · seed {seed}", flush=True)
    res = run(lo, hi, seed)
    v = verdict(res)

    payload = {
        "id": AUDIT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "range": [lo, hi],
        "seed": seed,
        "policy": {"measures_performance": False, "read_only": True, "db_write": False},
        "config": {
            "ASSEMBLE_MODE": sp.ASSEMBLE_MODE,
            "POOL_SLOTS_BY_BRAIN": dict(sp.POOL_SLOTS_BY_BRAIN),
            "HINT_SPEC_BY_BRAIN": {t: list(v) for t, v in sp.HINT_SPEC_BY_BRAIN.items()},
            "HINT_SHARED_ACROSS_BRAINS": sp.hint_shared_across_brains(),
        },
        "verdict": v,
        "result": {k: val for k, val in res.items() if k != "per_draw"},
        "per_draw": res["per_draw"],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = build_md(payload)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")

    print(f"\n=== {AUDIT_ID} ===")
    for k, c in v["checks"].items():
        print(f"  [{'O' if c['pass'] else 'X'}] {k} — {c['detail_ko']}")
    print()
    for t, a in res["aggregate"]["completeness"].items():
        print(
            f"  {t:7s} 10세트={a['pool_count_all_ok']} 중복={a['dup_in_pool10_total']} "
            f"고유평균={a['unique_pool_sets_mean']} pass0==pass1={a['pass0_equals_pass1_count']}"
        )
    for k, c in res["aggregate"]["cross_share"].items():
        print(
            f"  {k:16s} 동일pool={c['identical_pool_sets_total']} "
            f"동일몰아={c['identical_repack_sets_total']} "
            f"겹침={c['number_jaccard_mean']:.4f}"
        )
    print("\n  [출처] 점수세트 번호의 자기 pool 출신 비율")
    for t, a in res["aggregate"]["provenance"].items():
        print(
            f"  {t:7s} pool자리={a['rows_from_pool_mean']} 점수자리={a['rows_from_score_mean']} "
            f"자기pool비율={a['own_pool_ratio_score_sets_mean']}"
        )
    for k, a in res["aggregate"]["score_set_overlap"].items():
        print(f"  {k:16s} 점수세트 번호겹침={a['score_num_jaccard_mean']:.4f} 공유={a['n_shared_mean']}")
    print(f"\n{v['code']} · {v['n_pass']}/{v['n_total']}")
    if v["failed"]:
        print(f"실패: {v['failed']}")
    print(f"-> {OUT_JSON.relative_to(ROOT)}\n-> {OUT_MD.relative_to(ROOT)}")
    sys.exit(0 if v["all_pass"] else 1)


if __name__ == "__main__":
    main()
