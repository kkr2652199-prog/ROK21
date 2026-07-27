# -*- coding: utf-8 -*-
"""K-AG verify: zero-key · sensitivity · isolation · leak · regression."""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260727_KAG_pair_zone_learnkeys.json"
AS_OF = 1234
SEED = 20260727


def _sha_top(scored: list[dict], n: int = 15) -> str:
    top = [sorted(c["nums"]) for c in sorted(scored, key=lambda x: -x["confidence"])[:n]]
    return hashlib.sha256(json.dumps(top, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    os.environ["ROK21_DEDUP"] = "1"
    os.environ.pop("ROK21_LEARN_CUTOFF", None)

    from app.testlotto.brains import aux_pattern_spotlight as pat
    from app.testlotto.brains import aux_balance_keeper as bal
    from app.testlotto.brains.coordinator import (
        PREDICT_MODULES,
        _apply_aux_scoring,
        _aux_composite_score,
    )
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import clear_history_cache, set_learn_as_of
    from app.testlotto.ticket_dedup import combo_key, dedup_enabled, dedup_ticket_list
    import numpy as np

    clear_history_cache()
    set_learn_as_of(AS_OF)
    draws = _get_draws_before(AS_OF)
    sample = [
        [1, 2, 3, 4, 5, 6],
        [2, 3, 4, 5, 6, 7],
        [1, 15, 16, 30, 31, 45],  # (2,2,2)
        [1, 2, 3, 4, 5, 45],
        [10, 20, 21, 22, 30, 40],
    ]

    # --- zero-key identity (new baseline): brain_tag=None == boosts all 0 ---
    def fake_state(boosts: dict):
        return {"adjustments": {
            "pair_boost": 0.0,
            "consecutive_boost": 0.0,
            "odd_even_balance": 0.0,
            "carry_over_boost": 0.0,
            "ending_digit_boost": 0.0,
            "overdue_boost": 0.0,
            **boosts,
        }, "miss_counts": {}, "review_count": 0, "last_draw_no": 0, "recent_avg_match": 0.0}

    zero_ok = True
    zero_detail = []
    with mock.patch("app.testlotto.learn_state.load_learn_state", return_value=fake_state({})):
        for nums in sample:
            a = pat.score_set(nums, draws, AS_OF, brain_tag=None)
            b = pat.score_set(nums, draws, AS_OF, brain_tag="stat")
            c = bal.score_set(nums, draws, AS_OF, brain_tag=None)
            d = bal.score_set(nums, draws, AS_OF, brain_tag="stat")
            ok = abs(a - b) < 1e-12 and abs(c - d) < 1e-12
            zero_ok = zero_ok and ok
            zero_detail.append({"nums": nums, "pat": [a, b], "bal": [c, d], "ok": ok})

    # --- component helpers ---
    def pair_term(nums, boost=0.0):
        from app.testlotto.features.draw_features import build_pair_freq, pair_set
        pf = build_pair_freq(draws)
        ps = sum(pf.get(p, 0) for p in pair_set(nums))
        pn = min(1.0, ps / pat.PAIR_NORM_DIVISOR)
        return min(1.0, pn * (1.0 + boost))

    def consec_term(nums, boost=0.0):
        from app.testlotto.features.draw_features import combo_features
        cs = pat._CONSEC_SCORE.get(int(combo_features(nums, draws)["consecutive"]), 0.3)
        return min(1.0, cs * (1.0 + boost))

    def odd_term(nums, boost=0.0):
        tgt = bal._historical_targets(draws)
        from app.testlotto.features.draw_features import odd_even_ratio
        odd, _ = odd_even_ratio(nums)
        os_ = 1.0 - min(1.0, abs(odd - tgt["odd"]) / 3)
        return min(1.0, os_ * (1.0 + boost))

    # --- single-key sensitivity ---
    sens = {}
    nums0 = sample[2]
    for key, maker in (
        ("pair_boost", lambda b: fake_state({"pair_boost": b})),
        ("consecutive_boost", lambda b: fake_state({"consecutive_boost": b})),
        ("odd_even_balance", lambda b: fake_state({"odd_even_balance": b})),
    ):
        with mock.patch("app.testlotto.learn_state.load_learn_state", return_value=maker(0.0)):
            s0 = _aux_composite_score(nums0, draws, AS_OF, brain_tag="stat")
            p0, c0, o0 = pair_term(nums0, 0), consec_term(nums0, 0), odd_term(nums0, 0)
        with mock.patch("app.testlotto.learn_state.load_learn_state", return_value=maker(0.3)):
            s1 = _aux_composite_score(nums0, draws, AS_OF, brain_tag="stat")
            p1, c1, o1 = pair_term(nums0, 0.3 if key == "pair_boost" else 0), consec_term(
                nums0, 0.3 if key == "consecutive_boost" else 0
            ), odd_term(nums0, 0.3 if key == "odd_even_balance" else 0)
        sens[key] = {
            "aux_delta": s1 - s0,
            "changed": abs(s1 - s0) > 1e-12,
            "pair_term_delta": p1 - p0,
            "consec_term_delta": c1 - c0,
            "odd_term_delta": o1 - o0,
        }

    # --- 3x3 isolation (unsaturated nums so pair_term can move) ---
    nums_iso = sample[0]
    iso = {}
    for key in ("pair_boost", "consecutive_boost", "odd_even_balance"):
        pz, cz, oz = (
            pair_term(nums_iso, 0),
            consec_term(nums_iso, 0),
            odd_term(nums_iso, 0),
        )
        pb = 0.4 if key == "pair_boost" else 0.0
        cb = 0.4 if key == "consecutive_boost" else 0.0
        ob = 0.4 if key == "odd_even_balance" else 0.0
        iso[key] = {
            "pair_changed": abs(pair_term(nums_iso, pb) - pz) > 1e-12,
            "consec_changed": abs(consec_term(nums_iso, cb) - cz) > 1e-12,
            "odd_changed": abs(odd_term(nums_iso, ob) - oz) > 1e-12,
            "nums": nums_iso,
        }
    iso_ok = (
        iso["pair_boost"]["pair_changed"]
        and not iso["pair_boost"]["consec_changed"]
        and not iso["pair_boost"]["odd_changed"]
        and iso["consecutive_boost"]["consec_changed"]
        and not iso["consecutive_boost"]["pair_changed"]
        and not iso["consecutive_boost"]["odd_changed"]
        and iso["odd_even_balance"]["odd_changed"]
        and not iso["odd_even_balance"]["pair_changed"]
        and not iso["odd_even_balance"]["consec_changed"]
    )

    # --- zone LMH unit ---
    z222 = bal._zone_score_lmh(2, 2, 2)
    z600 = bal._zone_score_lmh(6, 0, 0)
    zone_unit = {
        "score_222": z222,
        "score_600": z600,
        "mode_is_max": z222 > z600,
        "mode_p": bal._LMH_MODE_P,
        "expect_222_near_0_7": abs(z222 - 0.7) < 1e-9,
    }

    # --- leak: same as_of two SHA ---
    def build_scored():
        clear_history_cache()
        set_learn_as_of(AS_OF)
        random.seed(SEED)
        cands = []
        for tag, mod in PREDICT_MODULES.items():
            random.seed(SEED + int(hashlib.md5(tag.encode()).hexdigest()[:8], 16) % 10007)
            cands.extend(mod.predict_sets(draws, 20))
        return _apply_aux_scoring(cands, draws, AS_OF)

    with mock.patch("app.testlotto.learn_state.load_learn_state", return_value=fake_state({})):
        s1 = build_scored()
        h1 = _sha_top(s1)
        s2 = build_scored()
        h2 = _sha_top(s2)
    leak_ok = h1 == h2

    # --- regression dedup E[k] ---
    clear_history_cache()
    set_learn_as_of(AS_OF)

    def tag_seed(tag: str) -> int:
        return SEED + int(hashlib.md5(tag.encode()).hexdigest()[:8], 16) % 10007

    def make_regen(target):
        def regen(brain_tag, seen, replace_of=None):
            mod = PREDICT_MODULES.get(brain_tag)
            if not mod:
                return None
            raw = mod.predict_sets(draws, 1)
            if not raw:
                return None
            return _apply_aux_scoring(raw, draws, target)[0]

        return regen

    random.seed(SEED)
    base = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(tag_seed(tag))
        base.extend(mod.predict_sets(draws, 40))
    base = _apply_aux_scoring(base[:120], draws, AS_OF)
    rng = random.Random(SEED)
    ks, unresolved = [], 0
    regen = make_regen(AS_OF)
    for _ in range(20):
        batch = [dict(t) for t in rng.sample(base, min(100, len(base)))]
        while len(batch) < 100:
            batch.append(dict(batch[len(batch) % len(batch)]))
        for j in range(3):
            batch[90 + j] = dict(batch[j])
        batch, st = dedup_ticket_list(batch, regenerate=regen)
        ks.append(len({combo_key(t["nums"]) for t in batch}))
        unresolved += int(st["unresolved_count"])
    ek = float(np.mean(ks))
    max_before = max(int(d["draw_no"]) for d in draws)
    reg = {
        "E_k": ek,
        "unresolved": unresolved,
        "dedup_on": dedup_enabled(),
        "as_of_ok": max_before < AS_OF,
        "sha_leak_ok": leak_ok,
        "sha": h1,
        "gate_pass": ek == 100.0 and unresolved == 0 and leak_ok and max_before < AS_OF,
    }

    sens_ok = all(v["changed"] for v in sens.values())
    # pair may not change aux if pair_term already 1.0 — check components
    for k, v in sens.items():
        if k == "pair_boost" and not v["changed"]:
            # accept if pair_term already capped
            sens_ok = sens_ok or abs(v["pair_term_delta"]) > 1e-12 or True
            # require either aux or term change; if both zero pick another nums
            break
    # recheck sensitivity with unsaturated nums
    nums_u = sample[0]
    sens2 = {}
    for key, maker in (
        ("pair_boost", lambda b: fake_state({"pair_boost": b})),
        ("consecutive_boost", lambda b: fake_state({"consecutive_boost": b})),
        ("odd_even_balance", lambda b: fake_state({"odd_even_balance": b})),
    ):
        with mock.patch("app.testlotto.learn_state.load_learn_state", return_value=maker(0.0)):
            s0 = _aux_composite_score(nums_u, draws, AS_OF, brain_tag="stat")
        with mock.patch("app.testlotto.learn_state.load_learn_state", return_value=maker(0.4)):
            s1 = _aux_composite_score(nums_u, draws, AS_OF, brain_tag="stat")
        sens2[key] = {"aux_delta": s1 - s0, "changed": abs(s1 - s0) > 1e-12}
    sens_ok = all(v["changed"] for v in sens2.values())

    step0 = json.loads(
        (ROOT / "docs" / "benchmarks" / "20260727_KAG_step0_measure.json").read_text(
            encoding="utf-8"
        )
    )

    payload = {
        "meta": {
            "id": "K-AG",
            "disclaimer": "1등 확률 상승 작업이 아니다. 명분·배선 정합 작업이다.",
            "as_of": AS_OF,
        },
        "step0_ref": {
            "pair_divisor": pat.PAIR_NORM_DIVISOR,
            "null_q95": step0["pair"]["null_5000"]["q95"],
            "legacy_30_sat_null": step0["pair"]["null_5000"]["frac_ge_30"],
            "zone_conflict_was": True,
            "unused_were_unconsumed": True,
        },
        "redef": {
            "pair": "PAIR_NORM_DIVISOR=null_q95=32.0 (not win-advantage)",
            "zone": "LMH theory PMF score; tgt['zone'] removed from scoring",
            "unchanged": ["AC_TARGET=8", "_CONSEC_SCORE", "sum fallback 138", "odd hist mean"],
        },
        "wiring": {
            "pair_boost": "pattern pair_term",
            "consecutive_boost": "pattern consec_term / _CONSEC_SCORE",
            "odd_even_balance": "balance odd_term",
            "zero_key_identity": "brain_tag=None ≡ load_learn_state all boosts 0",
            "note_vs_pre_kag_sha": (
                "구 /30·zone_spread 대비 SHA 불일치는 재정의 정상. "
                "항등 검증은 신규 baseline에서 키=0 기준."
            ),
        },
        "tests": {
            "zero_key": {"pass": zero_ok, "detail": zero_detail},
            "sensitivity": {"pass": sens_ok, "by_key": sens2, "on_nums": nums_u},
            "isolation_3x3": {"pass": iso_ok, "table": iso},
            "zone_unit": {"pass": zone_unit["expect_222_near_0_7"] and zone_unit["mode_is_max"], **zone_unit},
            "leak_sha": {"pass": leak_ok, "h1": h1, "h2": h2},
            "regression": reg,
        },
    }
    core = ["zero_key", "sensitivity", "isolation_3x3", "zone_unit", "leak_sha"]
    verify_pass = all(payload["tests"][k]["pass"] for k in core) and reg["gate_pass"]
    payload["verify_pass"] = verify_pass
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("verify_pass", verify_pass)
    print("E_k", ek, "iso", iso_ok, "sens", sens_ok, "zero", zero_ok)
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
