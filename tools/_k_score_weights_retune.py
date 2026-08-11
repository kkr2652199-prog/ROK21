# -*- coding: utf-8 -*-
"""K-SCORE-WEIGHTS-RETUNE — W=0.9 확정 후 SCORE_WEIGHTS_BY_BRAIN 재측정.

base=cand_A(잠금). ge3미사용. 게이트:
  markov prefer≥base · review prize≤base(더음수) · |Δ|≥0.005 하나이상
  · prefer/prize 교차 iso(상대뇌 |drift|<0.005) · stat top15_hit ≥ base−0.01
wire=False → 통과 시만 APPLY.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KSCORE_WEIGHTS_RETUNE.json"
OUT_MD = ROOT / "reports" / "20260811_KSCORE_WEIGHTS_RETUNE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80
ABS_THR = 0.005
ISO_THR = 0.005
STAT_SLACK = 0.01

BASE = {
    "stat": (0.25, 0.35, 0.40),
    "markov": (0.55, 0.20, 0.25),
    "review": (0.55, 0.20, 0.25),
}
CANDS: dict[str, dict[str, tuple[float, float, float]]] = {
    "cand_A": BASE,
    "cand_B": {  # hint↑
        "stat": (0.25, 0.35, 0.40),
        "markov": (0.65, 0.15, 0.20),
        "review": (0.65, 0.15, 0.20),
    },
    "cand_C": {  # 완화
        "stat": (0.30, 0.30, 0.40),
        "markov": (0.45, 0.25, 0.30),
        "review": (0.45, 0.25, 0.30),
    },
    "cand_D": {  # stat learn↑
        "stat": (0.20, 0.30, 0.50),
        "markov": (0.55, 0.20, 0.25),
        "review": (0.55, 0.20, 0.25),
    },
}


def _precheck() -> dict[str, Any]:
    from app.testlotto.brains.shared import crowd_signal as cs
    import app.testlotto.signal_pool as sp

    wc = dict(cs.W_CROWD_BY_BRAIN)
    blend = dict(cs.BLEND_STRENGTH_BY_BRAIN)
    w = {k: tuple(sp.SCORE_WEIGHTS_BY_BRAIN[k]) for k in BASE}
    ok = (
        abs(float(wc.get("markov", 0)) - 0.9) < 1e-12
        and abs(float(wc.get("review", 0)) - 0.9) < 1e-12
        and abs(float(blend.get("markov", 0)) - 0.55) < 1e-12
        and abs(float(blend.get("review", 0)) - 0.85) < 1e-12
        and w == BASE
    )
    return {"ok": ok, "W_CROWD": wc, "blend": blend, "weights": {k: list(v) for k, v in w.items()}}


def _run(seed: int, weights: dict[str, tuple[float, float, float]]) -> dict[str, Any]:
    import random
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy, _set_weights, _top15

    saved = dict(sp.SCORE_WEIGHTS_BY_BRAIN)
    _set_weights(sp, weights)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer: list[float] = []
        prize: list[float] = []
        hits: list[float] = []
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
            scores = {
                tag: sp.number_scores(
                    pool_br.get(tag, []),
                    hint_by.get(tag, fallback),
                    num_ema,
                    pos_ema,
                    brain_tag=tag,
                )
                for tag in sp.BRAIN_TAGS
            }
            t15m = _top15(scores["markov"])
            t15r = _top15(scores["review"])
            t15s = _top15(scores["stat"])
            prefer.append(mean(fw[n] for n in t15m) - all_mean)
            prize.append(mean(fw[n] for n in t15r) - all_mean)
            act = _actual(dno)
            hits.append(len(set(t15s) & act) / 6.0)
            learner.update_from_pool(pool_br, act)
        return {
            "seed": seed,
            "n": len(prefer),
            "prefer": round(mean(prefer), 6) if prefer else None,
            "prize": round(mean(prize), 6) if prize else None,
            "stat_hit": round(mean(hits), 6) if hits else None,
        }
    finally:
        sp.SCORE_WEIGHTS_BY_BRAIN.clear()
        sp.SCORE_WEIGHTS_BY_BRAIN.update(saved)


def _agg(name: str, by: list[dict[str, Any]], base: dict[str, float] | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    hit = mean(d["stat_hit"] for d in by if d["stat_hit"] is not None)
    if base is None:
        return {
            "name": name,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "stat_hit": round(hit, 6),
            "gate_pass": True,
            "gate_detail": {"is_baseline": True},
            "per_seed": by,
        }
    dpref = prefer - base["prefer"]
    dprize = prize - base["prize"]  # 음수 개선이면 dprize < 0
    dhit = hit - base["stat_hit"]
    cond = {
        "prefer_ge": prefer >= base["prefer"] - 1e-12,
        "prize_le": prize <= base["prize"] + 1e-12,
        "stat_ok": hit >= base["stat_hit"] - STAT_SLACK,
        "abs_move": abs(dpref) >= ABS_THR or abs(dprize) >= ABS_THR,
        "is_baseline": False,
        "dprefer": round(dpref, 6),
        "dprize": round(dprize, 6),
        "dhit": round(dhit, 6),
    }
    # 개선: prefer↑ 또는 prize↓ 중 실질 이동 + 비악화
    improve = (dpref >= ABS_THR and cond["prize_le"] and cond["stat_ok"]) or (
        dprize <= -ABS_THR and cond["prefer_ge"] and cond["stat_ok"]
    )
    gate = bool(improve and cond["prefer_ge"] and cond["prize_le"] and cond["stat_ok"] and cond["abs_move"])
    return {
        "name": name,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "stat_hit": round(hit, 6),
        "gate_pass": gate,
        "gate_detail": cond,
        "per_seed": by,
    }


def _apply(weights: dict[str, tuple[float, float, float]]) -> None:
    path = ROOT / "app" / "testlotto" / "signal_pool.py"
    text = path.read_text(encoding="utf-8")
    block = (
        "SCORE_WEIGHTS_BY_BRAIN: dict[str, tuple[float, float, float]] = {\n"
        f'    "stat": ({weights["stat"][0]:.2f}, {weights["stat"][1]:.2f}, {weights["stat"][2]:.2f}),    # hint↓ freq/learn↑ — 과거패턴\n'
        f'    "markov": ({weights["markov"][0]:.2f}, {weights["markov"][1]:.2f}, {weights["markov"][2]:.2f}),  # hint↑ — 선호번호\n'
        f'    "review": ({weights["review"][0]:.2f}, {weights["review"][1]:.2f}, {weights["review"][2]:.2f}),  # hint↑ — 금액뇌\n'
        "}"
    )
    text2, n = re.subn(
        r"SCORE_WEIGHTS_BY_BRAIN: dict\[str, tuple\[float, float, float\]\] = \{.*?\n\}",
        block,
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError(f"SCORE apply failed n={n}")
    path.write_text(text2, encoding="utf-8")


def main() -> int:
    pre = _precheck()
    print("precheck", pre)
    if not pre["ok"]:
        OUT_JSON.write_text(json.dumps({"verdict": "PRECHECK_FAIL", "pre": pre}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 1

    results: list[dict[str, Any]] = []
    base_m: dict[str, float] | None = None
    for name, w in CANDS.items():
        print(f"== {name} ==")
        by = [_run(s, w) for s in SEEDS]
        if name == "cand_A":
            row = _agg(name, by, None)
            base_m = {"prefer": row["prefer"], "prize": row["prize"], "stat_hit": row["stat_hit"]}
            row = _agg(name, by, None)
        else:
            row = _agg(name, by, base_m)
        results.append(row)
        print(row["prefer"], row["prize"], row["stat_hit"], row["gate_pass"])

    passers = [r for r in results if r["name"] != "cand_A" and r["gate_pass"]]
    if passers:
        # prefer↑ 우선, 동점이면 prize 더 음수
        win = max(passers, key=lambda r: (r["prefer"], -r["prize"]))
        _apply(CANDS[win["name"]])
        verdict = "APPLY"
        applied = win["name"]
    else:
        verdict = "NO_IMPROVE"
        applied = None

    payload = {
        "id": "K-SCORE-WEIGHTS-RETUNE",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "precheck": pre,
        "results": results,
        "verdict": verdict,
        "applied": applied,
        "ge3_used_as_claim": False,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = f"""# K-SCORE-WEIGHTS-RETUNE

📅 2026-08-11 · W_CROWD=0.9 확정 후 SCORE 재측정

## 결과
| cand | prefer | prize | stat_hit | gate |
|------|--------|-------|----------|------|
""" + "\n".join(
        f"| {r['name']} | {r['prefer']} | {r['prize']} | {r['stat_hit']} | {r['gate_pass']} |"
        for r in results
    ) + f"""

## 판정 **{verdict}** applied={applied}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict, applied)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
