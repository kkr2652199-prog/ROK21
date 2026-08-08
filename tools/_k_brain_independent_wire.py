# -*- coding: utf-8 -*-
"""K-BRAIN-INDEPENDENT-WIRE — hint 뇌별 분리 검증 + EV프록시 소구간 게이트.

형 지시 (20260808):
  각 3뇌 독립. 공유=lotto_draws만. hint·성적표·pool·RNG는 뇌별.
  [A] hint 분리 패치 검증 V1~V5
  [B] 금액뇌 EV프록시 게이트 (ge3 금지 · first_winners 축)

Usage
  python tools/_k_brain_independent_wire.py
  K_IW_EV_LO=1100 K_IW_EV_HI=1235 python tools/_k_brain_independent_wire.py
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WIRE_ID = "K-BRAIN-INDEPENDENT-WIRE"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KBRAIN_INDEPENDENT_WIRE.json"
OUT_MD = ROOT / "reports" / "20260808_KBRAIN_INDEPENDENT_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
PRIOR = ROOT / "docs" / "benchmarks" / "20260808_KBRAIN_CROWD_RESTRUCTURE.json"

PROBE_DNO = 1235
MC_SEED = 42
WARM_BACK = 80
EV_LO_DEFAULT = 1100
EV_HI_DEFAULT = 1235


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    return int(v) if v else default


def _top_n(hint: dict[int, float], n: int = 5) -> list[int]:
    return sorted(range(1, 46), key=lambda x: (-float(hint.get(x, 0.0)), x))[:n]


def _nums_of(d: dict) -> list[int]:
    if d.get("nums"):
        return [int(x) for x in d["nums"]]
    return [int(d[f"num{k}"]) for k in range(1, 7)]


def _fw_proxy_by_number(draws: list[dict]) -> dict[int, float]:
    """번호별 연관 first_winners 평균 (과거 draws만 · 컨닝 없음)."""
    acc = {n: 0.0 for n in range(1, 46)}
    cnt = {n: 0 for n in range(1, 46)}
    for d in draws:
        fw = int(d.get("first_winners") or 0)
        if fw <= 0:
            continue
        for n in _nums_of(d):
            acc[n] += float(fw)
            cnt[n] += 1
    out: dict[int, float] = {}
    for n in range(1, 46):
        out[n] = (acc[n] / cnt[n]) if cnt[n] else 0.0
    return out


def check_v1_hint_separated(dno: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp

    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    hb = sp.build_hint_by_brain(draws, dno)
    tops = {t: _top_n(hb[t], 5) for t in sp.BRAIN_TAGS}
    pairs_diff = {
        "stat|markov": tops["stat"] != tops["markov"],
        "stat|review": tops["stat"] != tops["review"],
        "markov|review": tops["markov"] != tops["review"],
    }
    return {
        "separated": not sp.hint_shared_across_brains(),
        "hint_shared_flag": sp.hint_shared_across_brains(),
        "spec": {t: list(v) for t, v in sp.HINT_SPEC_BY_BRAIN.items()},
        "stat_hint_top5": tops["stat"],
        "markov_hint_top5": tops["markov"],
        "review_hint_top5": tops["review"],
        "pairs_different": pairs_diff,
        "all_different": all(pairs_diff.values()),
        "pass": (not sp.hint_shared_across_brains()) and all(pairs_diff.values()),
    }


def check_v2_dead_wire(dno: int, seed: int) -> dict[str, Any]:
    """HINT_SPEC 값을 바꾸면 몰아주기 지문이 바뀌는지 (죽은 배선 탐지)."""
    import app.testlotto.signal_pool as sp

    def _fp() -> str:
        st = sp.build_pool_and_repack(dno, seed=seed, learner_warm_start=max(1, dno - WARM_BACK))
        parts = []
        for t in sp.BRAIN_TAGS:
            rows = st.get("repack_by_brain", {}).get(t, [])
            parts.append(
                f"{t}:"
                + ",".join(
                    ",".join(str(x) for x in r["nums"]) for r in rows
                )
            )
        return "|".join(parts)

    base = _fp()
    saved = dict(sp.HINT_SPEC_BY_BRAIN)
    try:
        # review 축만 완전히 다른 신호로 교체
        sp.HINT_SPEC_BY_BRAIN["review"] = (4, "odd_even")
        mutated = _fp()
        live = mutated != base
    finally:
        sp.HINT_SPEC_BY_BRAIN.clear()
        sp.HINT_SPEC_BY_BRAIN.update(saved)
    restored = _fp() == base
    return {
        "live": live,
        "restored_ok": restored,
        "pass": live and restored,
        "detail_ko": (
            "HINT_SPEC 변경→결과 변경 (배선 살아있음)"
            if live and restored
            else "죽은 배선 또는 복원 실패"
        ),
    }


def check_v3_signal_top_per_brain(dno: int, seed: int) -> dict[str, Any]:
    """몰아주기 score_repack 번호가 각 뇌 hint 상위와 겹치는 비율(뇌별)."""
    import app.testlotto.signal_pool as sp

    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    hb = sp.build_hint_by_brain(draws, dno)
    st = sp.build_pool_and_repack(dno, seed=seed, learner_warm_start=max(1, dno - WARM_BACK))
    per: dict[str, Any] = {}
    ok = True
    for tag in sp.BRAIN_TAGS:
        hint_top15 = set(_top_n(hb[tag], 15))
        # 다른 뇌 top15
        other_tops = set()
        for ot in sp.BRAIN_TAGS:
            if ot != tag:
                other_tops |= set(_top_n(hb[ot], 15))
        score_nums: set[int] = set()
        for r in st.get("repack_by_brain", {}).get(tag, []):
            if r.get("source") == "score_repack" or r.get("assemble") == "baseline_repack":
                score_nums |= set(int(x) for x in r["nums"])
            # signal_top pool 보존 세트도 포함하되, 점수 조립 위주 측정
        if not score_nums:
            for r in st.get("repack_by_brain", {}).get(tag, []):
                score_nums |= set(int(x) for x in r["nums"])
        own_hit = len(score_nums & hint_top15)
        foreign_only = len(score_nums & other_tops - hint_top15)
        # 자기 hint 겹침이 타뇌 전용 겹침보다 크거나 같으면 OK
        brain_ok = own_hit >= foreign_only
        per[tag] = {
            "own_hint_top15_overlap": own_hit,
            "foreign_only_overlap": foreign_only,
            "n_repack_nums": len(score_nums),
            "ok": brain_ok,
        }
        ok = ok and brain_ok
    return {"by_brain": per, "pass": ok}


def check_v4_rng_independent(dno: int, seed: int) -> dict[str, Any]:
    from tools._k_repack_signal_wire_verify import check_rng_independent

    r = check_rng_independent(dno, seed)
    return {
        "all_independent": bool(r.get("all_independent")),
        "by_brain": r.get("by_brain"),
        "pass": bool(r.get("all_independent")),
    }


def check_v5_draws_shared(dno: int) -> dict[str, Any]:
    """3뇌가 같은 lotto_draws 원본을 읽는지 (공유 허용 확인)."""
    import app.testlotto.signal_pool as sp
    from tools._k_window_signal_survey import PREDICT_MODULES

    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    assert draws, "draws empty"
    last = int(draws[-1]["draw_no"])
    n = len(draws)
    # 동일 draws 객체 길이·마지막 회차가 3뇌 입력으로 쓰임
    ids = []
    for tag, mod in PREDICT_MODULES.items():
        random.seed(seed_for := 42 + dno)
        out = mod.predict_sets(draws, 1)
        ids.append((tag, len(out) == 1, seed_for))
    return {
        "draws_len": n,
        "draws_last": last,
        "target": dno,
        "no_peek": last < dno,
        "brains_ran": {t: ok for t, ok, _ in ids},
        "pass": last < dno and n > 0 and all(ok for _, ok, _ in ids),
        "shared_allowed_ko": "lotto_draws 원본 공유 유지 (형 명시 허용)",
    }


def run_ev_proxy_gate(lo: int, hi: int) -> dict[str, Any]:
    """금액뇌(review) hint top15 의 first_winners 프록시 vs 전체 평균.

    prize_proxy_delta < 0 → 비인기 방향 (EV↑ 의도)
    ge3 미사용.
    """
    import app.testlotto.signal_pool as sp

    deltas: list[float] = []
    by_period: dict[str, list[float]] = {"early": [], "mid": [], "late": []}
    n_ok = 0
    for dno in range(lo, hi + 1):
        sp.set_learn_as_of(dno)
        draws = sp._get_draws_before(dno)
        if len(draws) < 50:
            continue
        fw = _fw_proxy_by_number(draws)
        all_mean = mean(fw[n] for n in range(1, 46))
        if all_mean <= 1e-12:
            continue
        hb = sp.build_hint_by_brain(draws, dno)
        top15 = _top_n(hb["review"], 15)
        rev_mean = mean(fw[n] for n in top15)
        delta = rev_mean - all_mean
        deltas.append(delta)
        if lo <= dno <= lo + 44:
            by_period["early"].append(delta)
        elif lo + 45 <= dno <= lo + 89:
            by_period["mid"].append(delta)
        else:
            by_period["late"].append(delta)
        n_ok += 1
        if n_ok % 30 == 0:
            print(f"  EV progress {dno} n={n_ok}", flush=True)

    def _pm(xs: list[float]) -> float | None:
        return round(mean(xs), 6) if xs else None

    early_m = _pm(by_period["early"])
    mid_m = _pm(by_period["mid"])
    late_m = _pm(by_period["late"])
    overall = round(mean(deltas), 6) if deltas else 0.0
    period_vals = [v for v in (early_m, mid_m, late_m) if v is not None]
    consistent = bool(period_vals) and all(v < 0 for v in period_vals)

    if overall < -0.5:
        verdict = "STRONG"
    elif overall <= 0.0:
        verdict = "MARGINAL"
    else:
        verdict = "NOISE"

    return {
        "draw_range": [lo, hi],
        "n_draws": len(deltas),
        "prize_proxy_delta": overall,
        "by_period": {
            "early": early_m,
            "mid": mid_m,
            "late": late_m,
            "consistent": consistent,
            "bins_ko": f"early={lo}~{lo+44} / mid={lo+45}~{lo+89} / late={lo+90}~{hi}",
        },
        "verdict": verdict,
        "metric_ko": "review hint top15 번호의 과거 first_winners평균 − 전체45 평균 (음수=비인기)",
        "ge3_used": False,
    }


def build_md(payload: dict[str, Any]) -> str:
    hs = payload["hint_separation"]
    wc = payload["wire_checks"]
    ev = payload["ev_proxy_gate"]
    lines = [
        f"# {WIRE_ID}",
        "",
        f"📅 {payload['ts']} · verdict=`{payload['verdict']}` · pass={payload['pass']}",
        "",
        "## [A] hint 뇌별 분리",
        "",
        f"- shared_flag={hs['hint_shared_flag']} (False 여야 분리)",
        f"- all_different top5={hs['all_different']}",
        f"- stat top5={hs['stat_hint_top5']}",
        f"- markov top5={hs['markov_hint_top5']}",
        f"- review top5={hs['review_hint_top5']}",
        f"- spec={hs['spec']}",
        "",
        "## wire_checks",
        "",
        "| check | pass |",
        "|---|---|",
    ]
    for k in (
        "V1_hint_separated",
        "V2_dead_wire_clear",
        "V3_signal_top_per_brain",
        "V4_rng_independent",
        "V5_draws_shared",
    ):
        lines.append(f"| {k} | {wc[k]} |")
    lines += [
        "",
        f"passed={wc['passed']}",
        "",
        "## [B] EV 프록시 게이트 (금액뇌 · ge3 미사용)",
        "",
        f"- range={ev['draw_range']} · n={ev['n_draws']}",
        f"- prize_proxy_delta={ev['prize_proxy_delta']}",
        f"- by_period={ev['by_period']}",
        f"- verdict={ev['verdict']}",
        "",
        f"rollback: `{payload['rollback']}`",
        "",
        f"prior: `{payload['prior']}`",
        f"tool: `{payload['tool']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    import app.testlotto.signal_pool as sp
    from app.testlotto.models import init_testlotto_db

    init_testlotto_db()
    if not PRIOR.is_file():
        raise SystemExit(f"prior missing: {PRIOR}")

    ev_lo = _env_int("K_IW_EV_LO", EV_LO_DEFAULT)
    ev_hi = _env_int("K_IW_EV_HI", EV_HI_DEFAULT)
    dno = _env_int("K_IW_PROBE", PROBE_DNO)
    seed = _env_int("K_IW_SEED", MC_SEED)

    print(f"=== {WIRE_ID} probe={dno} EV={ev_lo}~{ev_hi} ===", flush=True)
    print(f"HINT_SPEC={sp.HINT_SPEC_BY_BRAIN}", flush=True)
    print(f"shared={sp.hint_shared_across_brains()}", flush=True)

    v1 = check_v1_hint_separated(dno)
    print(f"V1 pass={v1['pass']} tops={v1['stat_hint_top5']}/{v1['markov_hint_top5']}/{v1['review_hint_top5']}", flush=True)
    v2 = check_v2_dead_wire(dno, seed)
    print(f"V2 pass={v2['pass']} live={v2['live']}", flush=True)
    v3 = check_v3_signal_top_per_brain(dno, seed)
    print(f"V3 pass={v3['pass']} {v3['by_brain']}", flush=True)
    v4 = check_v4_rng_independent(dno, seed)
    print(f"V4 pass={v4['pass']}", flush=True)
    v5 = check_v5_draws_shared(dno)
    print(f"V5 pass={v5['pass']} draws_last={v5['draws_last']}", flush=True)

    print("EV proxy gate…", flush=True)
    ev = run_ev_proxy_gate(ev_lo, ev_hi)
    print(
        f"EV delta={ev['prize_proxy_delta']} verdict={ev['verdict']} "
        f"consistent={ev['by_period']['consistent']}",
        flush=True,
    )

    checks = {
        "V1_hint_separated": bool(v1["pass"]),
        "V2_dead_wire_clear": bool(v2["pass"]),
        "V3_signal_top_per_brain": bool(v3["pass"]),
        "V4_rng_independent": bool(v4["pass"]),
        "V5_draws_shared": bool(v5["pass"]),
    }
    n_pass = sum(1 for v in checks.values() if v)
    checks["passed"] = f"{n_pass}/5"
    checks["detail"] = {
        "V2": v2,
        "V3": v3,
        "V4": v4,
        "V5": v5,
    }

    wire_ok = n_pass == 5
    # PARTIAL: hint 분리 OK 이나 EV NOISE 또는 V 일부 실패
    if wire_ok and ev["verdict"] in ("STRONG", "MARGINAL"):
        verdict = "WIRE_CONFORMS"
    elif v1["pass"] and n_pass >= 3:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    payload: dict[str, Any] = {
        "id": WIRE_ID,
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "verdict": verdict,
        "wire": True,
        "hint_separation": {
            "separated": bool(v1["separated"]),
            "hint_shared_flag": v1["hint_shared_flag"],
            "spec": v1["spec"],
            "stat_hint_top5": v1["stat_hint_top5"],
            "markov_hint_top5": v1["markov_hint_top5"],
            "review_hint_top5": v1["review_hint_top5"],
            "all_different": bool(v1["all_different"]),
        },
        "wire_checks": checks,
        "ev_proxy_gate": ev,
        "rollback": "K_CROWD_PREFER=0 K_PRIZE_EV=0",
        "pass": verdict == "WIRE_CONFORMS",
        "tool": "tools/_k_brain_independent_wire.py",
        "prior": "docs/benchmarks/20260808_KBRAIN_CROWD_RESTRUCTURE.json",
        "forbid": [
            "lotto_draws share removal",
            "coordinator modify",
            "random.choices modify",
            "_get_draws_before modify",
            "ge3 as EV metric",
        ],
        "predict_modules": "stat_brain/markov_brain/review_brain (live packages)",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = build_md(payload)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_JSON}", flush=True)
    print(f"wrote {OUT_MD}", flush=True)
    print(f"VERDICT={verdict} pass={payload['pass']}", flush=True)
    raise SystemExit(0 if payload["pass"] else 1)


if __name__ == "__main__":
    main()
