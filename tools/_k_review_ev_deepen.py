# -*- coding: utf-8 -*-
"""K-REVIEW-EV-DEEPEN — LIST_V3 L11.

review 금액축 잔여: annotate_prize shape 세기(PRIZE_SHAPE_STRENGTH)만 스윕.
LOCKED 재탕 금지: BLEND_review=0.85 · W_CROWD_review=0.90.
Stern-Cover/pick-marginal 금지 · ge3미클레임 · 1237아님.
게이트: prize↓ |Δ|≥0.005 · prefer iso(|drift|<0.005) · prize<0.
"""
from __future__ import annotations

import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KREVIEW_EV_DEEPEN.json"
OUT_MD = ROOT / "reports" / "20260812_KREVIEW_EV_DEEPEN.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80
ABS_THR = 0.005
ISO_THR = 0.005
BASE_S = 1.0
CANDS = [0.0, 0.5, 1.0, 1.5, 2.0]
LOCK_BLEND = 0.85
LOCK_WCROWD = 0.90


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _precheck() -> dict[str, Any]:
    from app.testlotto.brains.shared import crowd_signal as cs

    b = float(cs.BLEND_STRENGTH_BY_BRAIN.get("review", -1))
    w = float(cs.W_CROWD_BY_BRAIN.get("review", -1))
    return {
        "BLEND_review": b,
        "W_CROWD_review": w,
        "PRIZE_SHAPE_STRENGTH": float(cs.PRIZE_SHAPE_STRENGTH),
        "lock_ok": abs(b - LOCK_BLEND) < 1e-12 and abs(w - LOCK_WCROWD) < 1e-12,
        "stern_cover": False,
    }


def _patch(s: float):
    from app.testlotto.brains.shared import crowd_signal as cs

    saved = float(cs.PRIZE_SHAPE_STRENGTH)
    cs.PRIZE_SHAPE_STRENGTH = float(s)

    def restore() -> None:
        cs.PRIZE_SHAPE_STRENGTH = saved

    return restore


def _run(seed: int, shape_s: float) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy

    restore = _patch(shape_s)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer: list[float] = []
        prize: list[float] = []
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
            mnums = [n for c in pool_br.get("markov", []) for n in c["nums"]]
            rnums = [n for c in pool_br.get("review", []) for n in c["nums"]]
            if mnums:
                prefer.append(mean(fw[n] for n in mnums) - all_mean)
            if rnums:
                prize.append(mean(fw[n] for n in rnums) - all_mean)
            learner.update_from_pool(pool_br, _actual(dno))
        return {
            "seed": seed,
            "n": len(prize),
            "prefer": round(mean(prefer), 6) if prefer else None,
            "prize": round(mean(prize), 6) if prize else None,
        }
    finally:
        restore()


def _agg(s: float, runs: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in runs if d["prefer"] is not None)
    prize = mean(d["prize"] for d in runs if d["prize"] is not None)
    row: dict[str, Any] = {
        "shape_strength": s,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "per_seed": runs,
    }
    if base is None:
        row["gate"] = {"is_baseline": True, "pass": True}
        return row
    d_prize = prize - base["prize"]  # more negative better
    d_pref = prefer - base["prefer"]
    improve = d_prize <= -ABS_THR
    iso = abs(d_pref) < ISO_THR
    health = prize < 0 and prefer > 0
    ok = health and improve and iso
    row["gate"] = {
        "d_prize": round(d_prize, 6),
        "d_prefer": round(d_pref, 6),
        "improve": improve,
        "prefer_iso": iso,
        "health": health,
        "pass": ok,
    }
    return row


def main() -> int:
    from app.testlotto.brains.shared import crowd_signal as cs

    pre = _precheck()
    if not pre["lock_ok"]:
        print("FAIL lock precheck", pre)
        return 1

    by: dict[str, dict[str, Any]] = {}
    # base 먼저
    order = [BASE_S] + [s for s in CANDS if abs(s - BASE_S) >= 1e-12]
    base_row: dict[str, Any] | None = None
    for s in order:
        name = f"shape_{s:.1f}"
        print(f"== {name} ==", flush=True)
        runs = []
        for seed in SEEDS:
            r = _run(seed, s)
            print(f"  seed={seed} prefer={r['prefer']} prize={r['prize']}", flush=True)
            runs.append(r)
        row = _agg(s, runs, None if abs(s - BASE_S) < 1e-12 else base_row)
        by[name] = row
        if abs(s - BASE_S) < 1e-12:
            base_row = row

    assert base_row is not None
    winners: list[dict[str, Any]] = []
    for name, row in by.items():
        if abs(row["shape_strength"] - BASE_S) < 1e-12:
            continue
        g = row.get("gate") or {}
        if g.get("pass"):
            winners.append({"name": name, **g, "shape_strength": row["shape_strength"]})

    apply = False
    if winners:
        # prize 더 음수( d_prize 최소 ) 우선
        best = min(winners, key=lambda w: (w["d_prize"], -abs(w["d_prefer"])))
        verdict = "APPLY_OK"
        apply = True
        path = ROOT / "app" / "testlotto" / "brains" / "shared" / "crowd_signal.py"
        src = path.read_text(encoding="utf-8")
        src2, n = re.subn(
            r"PRIZE_SHAPE_STRENGTH: float = [0-9.]+",
            f"PRIZE_SHAPE_STRENGTH: float = {best['shape_strength']}",
            src,
            count=1,
        )
        if n != 1:
            raise SystemExit("APPLY patch failed")
        path.write_text(src2, encoding="utf-8")
        cs.PRIZE_SHAPE_STRENGTH = float(best["shape_strength"])
        note = (
            f"APPLY PRIZE_SHAPE_STRENGTH={best['shape_strength']} · "
            f"d_prize={best['d_prize']} · 다음 L11b markov"
        )
    else:
        best = None
        verdict = "HOLD"
        note = "신호없음 HOLD · PRIZE_SHAPE_STRENGTH=1.0 · BLEND/W_CROWD 불변 · 다음 L11b markov"

    payload = {
        "id": "K-REVIEW-EV-DEEPEN",
        "list": "LIST_V3",
        "step": "L11",
        "status": verdict,
        "ts": _now(),
        "wire": bool(apply),
        "apply": bool(apply),
        "ge3_used_as_claim": False,
        "stern_cover": False,
        "locked_not_reswept": {
            "BLEND_STRENGTH_BY_BRAIN.review": LOCK_BLEND,
            "W_CROWD_BY_BRAIN.review": LOCK_WCROWD,
        },
        "precheck": pre,
        "range": [LO, HI],
        "seeds": SEEDS,
        "knob": "PRIZE_SHAPE_STRENGTH",
        "base": BASE_S,
        "cands": CANDS,
        "configs": by,
        "winners": winners,
        "best": best,
        "thresholds": {"ABS_THR": ABS_THR, "ISO_THR": ISO_THR},
        "live_after": {"PRIZE_SHAPE_STRENGTH": float(cs.PRIZE_SHAPE_STRENGTH)},
        "next": {"step": "L11b", "id": "K-MARKOV-PREFER-ALIGN"},
        "force_bt": False,
        "s1": False,
        "note": note + " · 1237아님",
    }
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# K-REVIEW-EV-DEEPEN — LIST_V3 L11",
        "",
        f"시각: {payload['ts']} · **{verdict}** · apply=**{apply}** · **1237아님** · ge3미클레임 · Stern-Cover금지",
        f"노브: `PRIZE_SHAPE_STRENGTH` (annotate_prize 고번호·합 보너스) · LOCKED BLEND={LOCK_BLEND}/W_CROWD={LOCK_WCROWD} **재탕안함**",
        f"구간: {LO}~{HI} seeds={SEEDS}",
        "",
        f"## base shape={BASE_S}",
        "",
        f"| prefer | prize |",
        f"|--------|-------|",
        f"| {base_row['prefer']} | {base_row['prize']} |",
        "",
        "## cands",
        "",
    ]
    for name, row in by.items():
        if abs(row["shape_strength"] - BASE_S) < 1e-12:
            continue
        g = row.get("gate") or {}
        lines.append(
            f"- `{name}`: prefer={row['prefer']} prize={row['prize']} · "
            f"d_prize={g.get('d_prize')} d_prefer={g.get('d_prefer')} · pass=**{g.get('pass')}**"
        )
    lines += [
        "",
        f"판정: **{verdict}** — {note}",
        "",
        f"벤치: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        f"도구: `tools/_k_review_ev_deepen.py`",
        "",
        "다음: **L11b** K-MARKOV-PREFER-ALIGN",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "apply": apply, "best": best}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
