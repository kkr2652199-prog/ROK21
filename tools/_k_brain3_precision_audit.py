# -*- coding: utf-8 -*-
"""K-BRAIN3-PRECISION-AUDIT — 현행 패치 후 3뇌 정밀·버그사냥 (READ-ONLY).

형 요지: 독립구조·배선 완료 전제에서, 각 뇌 10세트가 좋아야 몰아주기가
극대화된다. 흩어진 적중번호를 모으려면 3뇌 pool이 핵심.
성적(ge3) 클레임 금지 · 1237아님 · 구조·배선·버그만.

검사군
  A 완전성: pool10 / repack5 / 번호형식 / 뇌내중복
  B 독립: 동일세트 교차0 · RNG단독=합동 · 학습교차오염0 · hint분리
  C 배선생존: SCORE/W_CROWD/BLEND/HINT_SPEC/HINT_WEIGHT/UNION/pick_score
  D 몰아주기 구조: assemble=signal_union · pool보존 · (정보) pool∩actual 포착
  E 컨닝: max_material < target
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KBRAIN3_PRECISION_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260811_KBRAIN3_PRECISION_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1216, 1236  # 최근 21회 · 정밀(시간)
SEED = 42
WARM_BACK = 80
BRAINS = ("stat", "markov", "review")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums: Any) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def _actual(dno: int) -> set[int]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    row = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?",
        (dno,),
    ).fetchone()
    conn.close()
    if not row:
        return set()
    r = dict(row)
    return {int(r[f"num{k}"]) for k in range(1, 7)}


def _live_knobs() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.shared import aux_hint as ah
    from app.testlotto.brains.shared import crowd_signal as cs
    from app.testlotto.brains.markov_brain import predict as mk
    from app.testlotto.brains.review_brain import predict as rv
    from app.testlotto.brains.stat_brain import predict as st

    return {
        "ASSEMBLE_MODE": sp.ASSEMBLE_MODE,
        "POOL_UNION_CAP": dict(sp.POOL_UNION_CAP_BY_BRAIN),
        "POOL_SLOTS": dict(sp.POOL_SLOTS_BY_BRAIN),
        "SCORE": {k: list(v) for k, v in sp.SCORE_WEIGHTS_BY_BRAIN.items()},
        "HINT_SPEC": {k: list(v) for k, v in sp.HINT_SPEC_BY_BRAIN.items()},
        "hint_shared": sp.hint_shared_across_brains(),
        "W_CROWD": dict(cs.W_CROWD_BY_BRAIN),
        "BLEND": dict(cs.BLEND_STRENGTH_BY_BRAIN),
        "HINT_WEIGHT_BY_BRAIN": dict(ah.HINT_WEIGHT_BY_BRAIN),
        "HINT_WEIGHT_modules": {
            "stat": st.HINT_WEIGHT,
            "markov": mk.HINT_WEIGHT,
            "review": rv.HINT_WEIGHT,
        },
        "FEATURE_LAMBDA_WIRE": bool(sp.FEATURE_LAMBDA_WIRE),
    }


def _build_one(dno: int, seed: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before

    learner = sp.RollingSignalLearner()
    sp.warm_learner_to_draw(learner, max(1, dno - WARM_BACK), dno, seed=seed)
    num_ema, pos_ema = learner.snapshot()
    sp.set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    max_mat = max(int(d["draw_no"]) for d in draws) if draws else 0
    random.seed(seed)
    pool = sp.expand_pool(draws, dno, seed=seed)
    pool_br = sp._pool_by_brain(pool)
    hint_by = sp.build_hint_by_brain(draws, dno)
    fallback = sp._build_hint(draws, dno)
    rows = sp.repack_by_brain(
        pool_br,
        fallback,
        num_ema,
        pos_ema,
        target_draw_no=dno,
        hint_by_brain=hint_by,
    )
    rp_br: dict[str, list[dict]] = {t: [] for t in BRAINS}
    for r in rows:
        rp_br.setdefault(str(r.get("brain_tag") or ""), []).append(r)
    act = _actual(dno)
    per: dict[str, Any] = {}
    for t in BRAINS:
        psets = pool_br.get(t) or []
        rsets = rp_br.get(t) or []
        pkeys = [_key(c["nums"]) for c in psets]
        rkeys = [_key(r["nums"]) for r in rsets]
        bad = [
            k
            for k in pkeys + rkeys
            if len(k) != 6 or len(set(k)) != 6 or min(k or [0]) < 1 or max(k or [0]) > 45
        ]
        pool_nums = {n for c in psets for n in c["nums"]}
        rp_nums = {n for r in rsets for n in r["nums"]}
        pool_hit_nums = sorted(pool_nums & act) if act else []
        rp_hit_nums = sorted(rp_nums & act) if act else []
        # pool에 있던 적중번호가 repack에 얼마나 보존됐는지 (구조 모니터)
        preserve = (
            len(set(pool_hit_nums) & set(rp_hit_nums)) / len(pool_hit_nums)
            if pool_hit_nums
            else None
        )
        sources = Counter(str(r.get("source") or "?") for r in rsets)
        assembles = Counter(str(r.get("assemble") or "?") for r in rsets)
        per[t] = {
            "n_pool": len(psets),
            "n_repack": len(rsets),
            "set_nos": sorted(int(c.get("pred_set_no") or 0) for c in psets),
            "dup_pool": len(pkeys) - len(set(pkeys)),
            "dup_repack": len(rkeys) - len(set(rkeys)),
            "bad_form": len(bad),
            "pool_hit_nums": pool_hit_nums,
            "repack_hit_nums": rp_hit_nums,
            "hit_preserve_ratio": round(preserve, 4) if preserve is not None else None,
            "sources": dict(sources),
            "assemble": dict(assembles),
            "pick_score_present_pool": sum(
                1 for c in psets if c.get("pick_score") is not None
            ),
        }
    # 교차 동일세트
    cross_pool = 0
    cross_rp = 0
    tags = list(BRAINS)
    for i, a in enumerate(tags):
        for b in tags[i + 1 :]:
            cross_pool += len(
                {_key(c["nums"]) for c in pool_br.get(a, [])}
                & {_key(c["nums"]) for c in pool_br.get(b, [])}
            )
            cross_rp += len(
                {_key(r["nums"]) for r in rp_br.get(a, [])}
                & {_key(r["nums"]) for r in rp_br.get(b, [])}
            )
    # hint top5 분리
    hint_tops = {
        t: sorted(
            range(1, 46),
            key=lambda n: (-float((hint_by.get(t) or {}).get(n, 0.0)), n),
        )[:5]
        for t in BRAINS
    }
    return {
        "draw": dno,
        "max_material": max_mat,
        "peek_ok": max_mat < dno,
        "per_brain": per,
        "cross_identical_pool": cross_pool,
        "cross_identical_repack": cross_rp,
        "hint_tops": hint_tops,
        "hint_tops_all_distinct": len({tuple(v) for v in hint_tops.values()}) == 3,
    }


def _rng_solo_vs_joint(dno: int, seed: int) -> dict[str, bool]:
    """C1: 뇌 단독 expand vs 합동 — 번호 집합 일치."""
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from tools._k_window_signal_survey import PREDICT_MODULES

    sp.set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    random.seed(seed)
    joint = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))
    out: dict[str, bool] = {}
    for tag in BRAINS:
        mod = PREDICT_MODULES[tag]
        solo_keys: list[tuple[int, ...]] = []
        for pass_idx in range(2):
            s = sp._pass_seed(seed, dno, pass_idx)
            random.seed(s)
            for i, c in enumerate(mod.predict_sets(draws, 5)):
                sn = int(c.get("rank") or i + 1) + pass_idx * 5
                solo_keys.append((_key(c["nums"]), sn))
        j_keys = sorted(
            (_key(c["nums"]), int(c.get("pred_set_no") or 0))
            for c in joint.get(tag, [])
        )
        out[tag] = sorted(solo_keys) == j_keys
    return out


def _wire_liveness(dno: int, seed: int) -> dict[str, Any]:
    """설정 dict를 잠깐 비틀면 결과가 바뀌는지."""
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.shared import aux_hint as ah
    from app.testlotto.brains.shared import crowd_signal as cs
    from app.testlotto.data_service import _get_draws_before

    def _sig(tag: str) -> tuple:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, dno - 40), dno, seed=seed)
        num_ema, pos_ema = learner.snapshot()
        sp.set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        random.seed(seed)
        pool_br = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))
        hint_by = sp.build_hint_by_brain(draws, dno)
        rows = sp.repack_by_brain(
            pool_br,
            sp._build_hint(draws, dno),
            num_ema,
            pos_ema,
            target_draw_no=dno,
            hint_by_brain=hint_by,
        )
        nums = tuple(
            sorted(
                _key(r["nums"])
                for r in rows
                if r.get("brain_tag") == tag
            )
        )
        pool_nums = tuple(
            sorted(_key(c["nums"]) for c in pool_br.get(tag, []))
        )
        return pool_nums, nums

    checks: dict[str, Any] = {}

    # SCORE markov
    base_m = _sig("markov")
    saved = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    sp.SCORE_WEIGHTS_BY_BRAIN["markov"] = (0.90, 0.05, 0.05)
    live_score = _sig("markov") != base_m
    sp.SCORE_WEIGHTS_BY_BRAIN.clear()
    sp.SCORE_WEIGHTS_BY_BRAIN.update(saved)
    checks["SCORE_markov"] = {"live": live_score, "restored": _sig("markov") == base_m}

    # HINT_WEIGHT markov (pick_score path)
    from app.testlotto.brains.markov_brain import predict as mk

    base_p = _sig("markov")
    saved_hw = ah.HINT_WEIGHT_BY_BRAIN["markov"]
    saved_mod = mk.HINT_WEIGHT
    ah.HINT_WEIGHT_BY_BRAIN["markov"] = 0.80
    mk.HINT_WEIGHT = 0.80
    live_hw = _sig("markov") != base_p
    ah.HINT_WEIGHT_BY_BRAIN["markov"] = saved_hw
    mk.HINT_WEIGHT = saved_mod
    checks["HINT_WEIGHT_markov"] = {
        "live": live_hw,
        "restored": _sig("markov") == base_p,
    }

    # W_CROWD markov (engine blend — pool 변화)
    base_w = _sig("markov")
    saved_w = dict(cs.W_CROWD_BY_BRAIN)
    saved_s = dict(cs.W_STRUCT_BY_BRAIN)
    cs.W_CROWD_BY_BRAIN["markov"] = 0.10
    cs.W_STRUCT_BY_BRAIN["markov"] = 0.90
    live_wc = _sig("markov") != base_w
    cs.W_CROWD_BY_BRAIN.clear()
    cs.W_CROWD_BY_BRAIN.update(saved_w)
    cs.W_STRUCT_BY_BRAIN.clear()
    cs.W_STRUCT_BY_BRAIN.update(saved_s)
    checks["W_CROWD_markov"] = {"live": live_wc, "restored": _sig("markov") == base_w}

    # UNION cap (repack only)
    base_u = _sig("stat")
    saved_cap = dict(sp.POOL_UNION_CAP_BY_BRAIN)
    sp.POOL_UNION_CAP_BY_BRAIN["stat"] = 2
    live_u = _sig("stat")[1] != base_u[1]  # repack half
    sp.POOL_UNION_CAP_BY_BRAIN.clear()
    sp.POOL_UNION_CAP_BY_BRAIN.update(saved_cap)
    checks["UNION_CAP_stat"] = {"live": live_u, "restored": _sig("stat") == base_u}

    # HINT_SPEC separation already structural
    checks["HINT_SPEC_separated"] = {
        "live": not __import__("app.testlotto.signal_pool", fromlist=["x"]).hint_shared_across_brains(),
        "restored": True,
    }
    return checks


def audit() -> dict[str, Any]:
    knobs = _live_knobs()
    rows = [_build_one(d, SEED) for d in range(LO, HI + 1)]
    rng = _rng_solo_vs_joint(HI, SEED)
    wire = _wire_liveness(HI, SEED)

    # aggregate A
    a_fail: list[str] = []
    for r in rows:
        if not r["peek_ok"]:
            a_fail.append(f"peek:{r['draw']}")
        for t, p in r["per_brain"].items():
            if p["n_pool"] != 10:
                a_fail.append(f"pool!=10:{r['draw']}:{t}")
            if p["n_repack"] != 5:
                a_fail.append(f"repack!=5:{r['draw']}:{t}")
            if p["set_nos"] != list(range(1, 11)):
                a_fail.append(f"set_nos:{r['draw']}:{t}")
            if p["dup_pool"] or p["dup_repack"] or p["bad_form"]:
                a_fail.append(f"dup/bad:{r['draw']}:{t}")

    cross_pool = sum(r["cross_identical_pool"] for r in rows)
    cross_rp = sum(r["cross_identical_repack"] for r in rows)
    hint_sep_rate = mean(1.0 if r["hint_tops_all_distinct"] else 0.0 for r in rows)

    preserve = {
        t: [
            r["per_brain"][t]["hit_preserve_ratio"]
            for r in rows
            if r["per_brain"][t]["hit_preserve_ratio"] is not None
        ]
        for t in BRAINS
    }
    preserve_mean = {t: round(mean(v), 4) if v else None for t, v in preserve.items()}

    assemble_ok = all(
        "signal_union" in (r["per_brain"][t]["assemble"] or {})
        for r in rows
        for t in BRAINS
    )
    # pick_score on pool: expand may strip — check via module path sample
    pick_in_pool = mean(
        mean(r["per_brain"][t]["pick_score_present_pool"] / 10 for t in BRAINS)
        for r in rows
    )

    pool_hit_n = {
        t: round(
            mean(len(r["per_brain"][t]["pool_hit_nums"]) for r in rows),
            3,
        )
        for t in BRAINS
    }
    rp_hit_n = {
        t: round(
            mean(len(r["per_brain"][t]["repack_hit_nums"]) for r in rows),
            3,
        )
        for t in BRAINS
    }

    checks = {
        "A_완전성_pool10_repack5": {
            "pass": not a_fail,
            "fail_sample": a_fail[:12],
            "n_fail": len(a_fail),
        },
        "B_교차동일세트0": {
            "pass": cross_pool == 0 and cross_rp == 0,
            "cross_pool": cross_pool,
            "cross_repack": cross_rp,
        },
        "B_hint테이블분리": {
            "pass": hint_sep_rate >= 0.99 and not knobs["hint_shared"],
            "distinct_rate": round(hint_sep_rate, 4),
            "hint_shared_flag": knobs["hint_shared"],
        },
        "C_RNG단독=합동": {"pass": all(rng.values()), "by_brain": rng},
        "C_배선생존_SCORE": {
            "pass": bool(wire["SCORE_markov"]["live"] and wire["SCORE_markov"]["restored"]),
            "detail": wire["SCORE_markov"],
        },
        "C_배선생존_HINT_WEIGHT": {
            "pass": bool(
                wire["HINT_WEIGHT_markov"]["live"] and wire["HINT_WEIGHT_markov"]["restored"]
            ),
            "detail": wire["HINT_WEIGHT_markov"],
            "note": "pick_score 경로",
        },
        "C_배선생존_W_CROWD": {
            "pass": bool(wire["W_CROWD_markov"]["live"] and wire["W_CROWD_markov"]["restored"]),
            "detail": wire["W_CROWD_markov"],
        },
        "C_배선생존_UNION_CAP": {
            "pass": bool(wire["UNION_CAP_stat"]["live"] and wire["UNION_CAP_stat"]["restored"]),
            "detail": wire["UNION_CAP_stat"],
        },
        "D_assemble_signal_union": {
            "pass": assemble_ok and knobs["ASSEMBLE_MODE"] == "signal_union",
            "mode": knobs["ASSEMBLE_MODE"],
        },
        "D_peek_ok": {"pass": all(r["peek_ok"] for r in rows)},
        "E_정보_pool적중번호포착": {
            "pass": True,
            "is_informational": True,
            "mean_pool_hit_nums": pool_hit_n,
            "mean_repack_hit_nums": rp_hit_n,
            "mean_preserve_pool_to_repack": preserve_mean,
            "note": "클레임아님 · 몰아주기 전 pool에 적중번호가 얼마나 있는지만 모니터",
        },
        "E_정보_pick_score_pool잔존": {
            "pass": True,
            "is_informational": True,
            "mean_fraction_in_pool_dicts": round(pick_in_pool, 4),
            "note": "expand 결과가 pick_score를 안 실을 수 있음(predict내부만 사용) — 0이어도 배선과 무관할 수 있음",
        },
    }

    hard = [k for k, v in checks.items() if not v.get("is_informational") and not v["pass"]]
    verdict = "AUDIT_OK" if not hard else "BUG_FOUND"
    bugs: list[dict[str, Any]] = []
    if not checks["C_배선생존_HINT_WEIGHT"]["pass"]:
        bugs.append(
            {
                "id": "HINT_WEIGHT_DEAD",
                "sev": "high",
                "msg": "HINT_WEIGHT 변경이 pool/repack에 반영 안 됨",
            }
        )
    if not checks["C_배선생존_SCORE"]["pass"]:
        bugs.append({"id": "SCORE_DEAD", "sev": "high", "msg": "SCORE_WEIGHTS 죽은 배선"})
    if not checks["A_완전성_pool10_repack5"]["pass"]:
        bugs.append(
            {
                "id": "SET_COUNT",
                "sev": "high",
                "msg": f"세트수/형식 실패 {checks['A_완전성_pool10_repack5']['n_fail']}건",
            }
        )
    if not checks["B_교차동일세트0"]["pass"]:
        bugs.append({"id": "CROSS_IDENTICAL", "sev": "medium", "msg": "뇌간 동일세트 발생"})
    if not checks["C_RNG단독=합동"]["pass"]:
        bugs.append({"id": "RNG_POLLUTION", "sev": "high", "msg": "뇌간 RNG 오염"})

    # 구조 관찰: pool 적중 > repack 적중이면 몰아주기가 번호를 버림 (이미 union으로 완화)
    loss_obs = {
        t: sum(
            1
            for r in rows
            if len(r["per_brain"][t]["pool_hit_nums"])
            > len(r["per_brain"][t]["repack_hit_nums"])
        )
        for t in BRAINS
    }

    return {
        "id": "K-BRAIN3-PRECISION-AUDIT",
        "ts": _now(),
        "range": [LO, HI],
        "n_draws": len(rows),
        "seed": SEED,
        "live_knobs": knobs,
        "checks": checks,
        "bugs": bugs,
        "wire_liveness": wire,
        "rng_solo_vs_joint": rng,
        "pool_hit_num_loss_draws": loss_obs,
        "verdict": verdict if not bugs else ("BUG_FOUND" if hard else verdict),
        "ge3_used_as_claim": False,
        "patch_summary_ko": [
            "뇌독립: HINT/SCORE/W/BLEND BY_BRAIN · 공유=lotto_draws만",
            "몰아주기: signal_union(slots2+cap4) · 뇌별 learner",
            "aux: pick_score→diversity.pick · HINT_WEIGHT 0.15 HOLD",
            "K-J: referee SSOT=live · DB미러",
            "tune_json 캐시 보존",
        ],
        "sample_draws": rows[:3] + rows[-2:],
    }


def write_md(r: dict[str, Any]) -> None:
    lines = [
        "# K-BRAIN3-PRECISION-AUDIT — 3뇌 정밀·버그사냥",
        "",
        f"시각: {r['ts']} · 회차 {r['range']} n={r['n_draws']} · seed={r['seed']}",
        "",
        f"## 판정 **{r['verdict']}** · bugs={len(r['bugs'])}",
        "- ge3클레임금지 · 1237아님 · READ-ONLY",
        "",
        "## 0. 현행 패치 (간략)",
    ]
    for s in r["patch_summary_ko"]:
        lines.append(f"- {s}")
    lines += ["", "## 1. live knobs", f"```json", json.dumps(r["live_knobs"], ensure_ascii=False, indent=2), "```", "", "## 2. 검사"]
    for k, c in r["checks"].items():
        mark = "PASS" if c["pass"] else "**FAIL**"
        info = " (정보)" if c.get("is_informational") else ""
        detail = {kk: vv for kk, vv in c.items() if kk != "pass"}
        lines.append(f"- `{k}`: {mark}{info}")
        lines.append(f"  - {detail}")
    lines += ["", "## 3. 버그", "```json", json.dumps(r["bugs"], ensure_ascii=False, indent=2), "```", ""]
    lines += [
        "## 4. 몰아주기 전제 (형 요지)",
        "- 각 뇌 **10세트**에 적중번호가 먼저 들어와야, 뇌별 몰아주기(5장)가 극대화된다.",
        f"- 모니터(클레임아님) mean pool적중번호수={r['checks']['E_정보_pool적중번호포착']['mean_pool_hit_nums']}",
        f"- mean repack적중번호수={r['checks']['E_정보_pool적중번호포착']['mean_repack_hit_nums']}",
        f"- pool→repack 번호보존비율={r['checks']['E_정보_pool적중번호포착']['mean_preserve_pool_to_repack']}",
        f"- pool적중>repack적중 회차수={r['pool_hit_num_loss_draws']}",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")


def main() -> None:
    r = audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(r)
    print("VERDICT", r["verdict"], "bugs", r["bugs"])
    for k, c in r["checks"].items():
        if not c.get("is_informational"):
            print(f"  {k}: {'PASS' if c['pass'] else 'FAIL'}")
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
