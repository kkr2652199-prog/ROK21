# -*- coding: utf-8 -*-
"""K-BRAIN-INDEPENDENT-TUNE — 뇌별 SCORE_WEIGHTS 1노브 (축 전용 지표).

형 GO (WIRE_CONFORMS 후): 각 뇌 특성대로 몰아주기 점수축을 갈라 둔다.
ge3 를 통과 조건으로 쓰지 않는다.

축
  markov  prefer_delta = score_top15 fw평균 − 전체평균  (양수↑ = 인기방향 OK)
  review  prize_delta  = score_top15 fw평균 − 전체평균  (음수↓ = 비인기/EV OK)
  stat    top15_hit    = |score_top15 ∩ actual| / 6     (WF 적중재료 정렬)

후보 (합=1.0)
  base:    전뇌 (0.40, 0.25, 0.35)
  cand_A:  markov/review hint↑ · stat freq/learn↑
           stat   (0.25, 0.35, 0.40)
           markov (0.55, 0.20, 0.25)
           review (0.55, 0.20, 0.25)

적용 조건
  · markov prefer_delta(cand) ≥ base
  · review prize_delta(cand)  ≤ base   (더 음수)
  · stat top15_hit(cand)      ≥ base − 0.01  (큰 손해 없음)
  · 3구간 review consistent(음수) 유지
  · probe 회차 V1 hint 분리 유지 (spec 불변)

Usage
  python tools/_k_brain_independent_tune.py
  K_IT_LO=1190 K_IT_HI=1235 python tools/_k_brain_independent_tune.py
  K_IT_APPLY=1 python tools/_k_brain_independent_tune.py   # 게이트 PASS 시만 적용
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

TUNE_ID = "K-BRAIN-INDEPENDENT-TUNE"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KBRAIN_INDEPENDENT_TUNE.json"
OUT_MD = ROOT / "reports" / "20260808_KBRAIN_INDEPENDENT_TUNE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
PRIOR = ROOT / "docs" / "benchmarks" / "20260808_KBRAIN_INDEPENDENT_WIRE.json"

DEFAULT_LO = 1100
DEFAULT_HI = 1235
MC_SEED = 42
WARM_BACK = 80

BASE_W = {
    "stat": (0.40, 0.25, 0.35),
    "markov": (0.40, 0.25, 0.35),
    "review": (0.40, 0.25, 0.35),
}
CAND_A = {
    "stat": (0.25, 0.35, 0.40),
    "markov": (0.55, 0.20, 0.25),
    "review": (0.55, 0.20, 0.25),
}


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    return int(v) if v else default


def _env_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _nums_of(d: dict) -> list[int]:
    if d.get("nums"):
        return [int(x) for x in d["nums"]]
    return [int(d[f"num{k}"]) for k in range(1, 7)]


def _fw_proxy(draws: list[dict]) -> dict[int, float]:
    acc = {n: 0.0 for n in range(1, 46)}
    cnt = {n: 0 for n in range(1, 46)}
    for d in draws:
        fw = int(d.get("first_winners") or 0)
        if fw <= 0:
            continue
        for n in _nums_of(d):
            acc[n] += float(fw)
            cnt[n] += 1
    return {n: (acc[n] / cnt[n] if cnt[n] else 0.0) for n in range(1, 46)}


def _top15(scores: dict[int, float]) -> list[int]:
    return sorted(range(1, 46), key=lambda x: (-float(scores.get(x, 0.0)), x))[:15]


def _actual(dno: int) -> set[int]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    row = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?",
        (dno,),
    ).fetchone()
    conn.close()
    d = dict(row)
    return {int(d[f"num{k}"]) for k in range(1, 7)}


def _set_weights(sp: Any, wmap: dict[str, tuple[float, float, float]]) -> None:
    for t, w in wmap.items():
        sp.SCORE_WEIGHTS_BY_BRAIN[t] = w


def run_axis_walk(
    lo: int,
    hi: int,
    seed: int,
    weights: dict[str, tuple[float, float, float]],
) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp

    saved = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    _set_weights(sp, weights)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, lo - WARM_BACK), lo, seed=seed)

        prefer: list[float] = []
        prize: list[float] = []
        stat_hit: list[float] = []
        prize_early: list[float] = []
        prize_mid: list[float] = []
        prize_late: list[float] = []

        for dno in range(lo, hi + 1):
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

            scores_by: dict[str, dict[int, float]] = {}
            for tag in sp.BRAIN_TAGS:
                h = hint_by.get(tag, fallback)
                scores_by[tag] = sp.number_scores(
                    pool_br.get(tag, []),
                    h,
                    num_ema,
                    pos_ema,
                    brain_tag=tag,
                )

            m_top = _top15(scores_by["markov"])
            r_top = _top15(scores_by["review"])
            s_top = _top15(scores_by["stat"])
            prefer_d = mean(fw[n] for n in m_top) - all_mean
            prize_d = mean(fw[n] for n in r_top) - all_mean
            actual = _actual(dno)
            hit = len(set(s_top) & actual) / 6.0

            prefer.append(prefer_d)
            prize.append(prize_d)
            stat_hit.append(hit)
            if lo <= dno <= lo + 44:
                prize_early.append(prize_d)
            elif lo + 45 <= dno <= lo + 89:
                prize_mid.append(prize_d)
            else:
                prize_late.append(prize_d)

            learner.update_from_pool(pool_br, actual)
            if (dno - lo) % 30 == 0:
                print(f"    dno={dno}", flush=True)

        def _m(xs: list[float]) -> float | None:
            return round(mean(xs), 6) if xs else None

        pe, pm, pl = _m(prize_early), _m(prize_mid), _m(prize_late)
        period_vals = [v for v in (pe, pm, pl) if v is not None]
        return {
            "n": len(prize),
            "markov_prefer_delta": _m(prefer),
            "review_prize_delta": _m(prize),
            "stat_top15_hit": _m(stat_hit),
            "review_by_period": {
                "early": pe,
                "mid": pm,
                "late": pl,
                "consistent_neg": bool(period_vals) and all(v < 0 for v in period_vals),
            },
        }
    finally:
        sp.SCORE_WEIGHTS_BY_BRAIN.clear()
        sp.SCORE_WEIGHTS_BY_BRAIN.update(saved)


def decide(base: dict[str, Any], cand: dict[str, Any]) -> dict[str, Any]:
    mp_b, mp_c = base["markov_prefer_delta"], cand["markov_prefer_delta"]
    rp_b, rp_c = base["review_prize_delta"], cand["review_prize_delta"]
    sh_b, sh_c = base["stat_top15_hit"], cand["stat_top15_hit"]
    assert mp_b is not None and mp_c is not None
    assert rp_b is not None and rp_c is not None
    assert sh_b is not None and sh_c is not None

    markov_ok = mp_c >= mp_b - 1e-9
    review_ok = rp_c <= rp_b + 1e-9
    stat_ok = sh_c >= sh_b - 0.01
    consistent = bool(cand["review_by_period"]["consistent_neg"])

    apply = markov_ok and review_ok and stat_ok and consistent
    reasons = []
    if not markov_ok:
        reasons.append(f"markov prefer악화 {mp_b}->{mp_c}")
    if not review_ok:
        reasons.append(f"review prize악화(덜음수) {rp_b}->{rp_c}")
    if not stat_ok:
        reasons.append(f"stat hit 손해>0.01 {sh_b}->{sh_c}")
    if not consistent:
        reasons.append("review 3구간 consistent 실패")

    return {
        "markov_ok": markov_ok,
        "review_ok": review_ok,
        "stat_ok": stat_ok,
        "consistent_ok": consistent,
        "apply": apply,
        "deltas": {
            "markov_prefer": round(mp_c - mp_b, 6),
            "review_prize": round(rp_c - rp_b, 6),
            "stat_top15_hit": round(sh_c - sh_b, 6),
        },
        "reasons_block": reasons,
        "verdict": "APPLY" if apply else "KEEP_BASE",
    }


def apply_weights(wmap: dict[str, tuple[float, float, float]]) -> None:
    path = ROOT / "app" / "testlotto" / "signal_pool.py"
    text = path.read_text(encoding="utf-8")
    old = (
        "SCORE_WEIGHTS_BY_BRAIN: dict[str, tuple[float, float, float]] = dict.fromkeys(\n"
        "    BRAIN_TAGS, (W_HINT, W_FREQ, W_LEARN)\n"
        ")"
    )
    new = (
        "SCORE_WEIGHTS_BY_BRAIN: dict[str, tuple[float, float, float]] = {\n"
        f'    "stat": {wmap["stat"]},    # hint↓ freq/learn↑ — 과거패턴\n'
        f'    "markov": {wmap["markov"]},  # hint↑ — 선호번호\n'
        f'    "review": {wmap["review"]},  # hint↑ — 금액뇌\n'
        "}"
    )
    if old not in text:
        # already tuned? replace existing dict block if present
        import re

        pat = r"SCORE_WEIGHTS_BY_BRAIN: dict\[str, tuple\[float, float, float\]\] = \{[\s\S]*?\n\}"
        if not re.search(pat, text):
            raise RuntimeError("SCORE_WEIGHTS_BY_BRAIN block not found for apply")
        text = re.sub(pat, new.rstrip(), text, count=1)
    else:
        text = text.replace(old, new, 1)
    # comment update
    text = text.replace(
        "# **현재 값은 3뇌 전부 동일** = 성적 무변화. 값을 다르게 만드는 것은 성적 주장이\n"
        "# 필요한 튜닝이므로 R38 게이트를 통과한 뒤에 바꾼다.\n",
        "# K-BRAIN-INDEPENDENT-TUNE — 뇌별 점수축 분리 (축전용 지표 게이트 통과 후).\n"
        "# ge3 미사용 · markov prefer↑ / review prize↓ / stat hit 비악화.\n",
        1,
    )
    path.write_text(text, encoding="utf-8")


def build_md(payload: dict[str, Any]) -> str:
    b, c, d = payload["base"], payload["candidate"], payload["decision"]
    lines = [
        f"# {TUNE_ID}",
        "",
        f"📅 {payload['ts']} · verdict=`{d['verdict']}` · applied={payload['applied']}",
        "",
        f"range={payload['draw_range']} · n≈{b['n']} · seed={payload['seed']}",
        "",
        "## SCORE_WEIGHTS (hint, freq, learn)",
        "",
        f"- base: `{payload['weights']['base']}`",
        f"- cand_A: `{payload['weights']['cand_A']}`",
        "",
        "## 축 지표 (ge3 미사용)",
        "",
        "| 축 | base | cand | Δ |",
        "|---|---:|---:|---:|",
        f"| markov prefer_delta | {b['markov_prefer_delta']} | {c['markov_prefer_delta']} | {d['deltas']['markov_prefer']} |",
        f"| review prize_delta | {b['review_prize_delta']} | {c['review_prize_delta']} | {d['deltas']['review_prize']} |",
        f"| stat top15_hit | {b['stat_top15_hit']} | {c['stat_top15_hit']} | {d['deltas']['stat_top15_hit']} |",
        "",
        f"review 3구간 cand: `{c['review_by_period']}`",
        "",
        f"decision: **{d['verdict']}** · apply_flags={{{d['markov_ok']},{d['review_ok']},{d['stat_ok']},{d['consistent_ok']}}}",
        "",
    ]
    if d["reasons_block"]:
        lines.append("block: " + " · ".join(d["reasons_block"]))
        lines.append("")
    lines += [
        "prior: `docs/benchmarks/20260808_KBRAIN_INDEPENDENT_WIRE.json`",
        "tool: `tools/_k_brain_independent_tune.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    from app.testlotto.models import init_testlotto_db

    init_testlotto_db()
    if not PRIOR.is_file():
        raise SystemExit(f"prior missing: {PRIOR}")

    lo = _env_int("K_IT_LO", DEFAULT_LO)
    hi = _env_int("K_IT_HI", DEFAULT_HI)
    seed = _env_int("K_IT_SEED", MC_SEED)
    do_apply = _env_on("K_IT_APPLY")

    print(f"=== {TUNE_ID} {lo}~{hi} seed={seed} apply_flag={do_apply} ===", flush=True)
    print("BASE walk…", flush=True)
    base = run_axis_walk(lo, hi, seed, BASE_W)
    print(f"  base={base}", flush=True)
    print("CAND_A walk…", flush=True)
    cand = run_axis_walk(lo, hi, seed, CAND_A)
    print(f"  cand={cand}", flush=True)

    decision = decide(base, cand)
    print(f"decision={decision}", flush=True)

    applied = False
    if decision["apply"] and do_apply:
        apply_weights(CAND_A)
        applied = True
        print("APPLIED SCORE_WEIGHTS_BY_BRAIN=cand_A", flush=True)
    elif decision["apply"] and not do_apply:
        # 기본: 게이트 PASS 면 이번 턴에서 적용 (형 GO 받은 튜닝 단계)
        apply_weights(CAND_A)
        applied = True
        print("APPLIED (default on PASS)", flush=True)
    else:
        print("KEEP_BASE — no code weight change", flush=True)

    payload: dict[str, Any] = {
        "id": TUNE_ID,
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "draw_range": [lo, hi],
        "seed": seed,
        "weights": {"base": BASE_W, "cand_A": CAND_A},
        "base": base,
        "candidate": cand,
        "decision": decision,
        "applied": applied,
        "verdict": decision["verdict"],
        "pass": bool(decision["apply"]),
        "ge3_used": False,
        "metric_note_ko": (
            "몰아주기 number_scores top15 기준. "
            "hint 테이블 자체는 불변 — SCORE_WEIGHTS만 뇌별 차별."
        ),
        "rollback": "SCORE_WEIGHTS_BY_BRAIN 를 (0.40,0.25,0.35) 동일로 복원",
        "prior": "docs/benchmarks/20260808_KBRAIN_INDEPENDENT_WIRE.json",
        "tool": "tools/_k_brain_independent_tune.py",
        "forbid": [
            "ge3 as pass metric",
            "coordinator modify",
            "random.choices modify",
            "_get_draws_before modify",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = build_md(payload)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_JSON}", flush=True)
    print(f"VERDICT={payload['verdict']} applied={applied}", flush=True)
    raise SystemExit(0 if decision["apply"] else 2)


if __name__ == "__main__":
    main()
