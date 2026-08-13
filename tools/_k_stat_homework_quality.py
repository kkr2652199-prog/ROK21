# -*- coding: utf-8 -*-
"""K-STAT-HOMEWORK-QUALITY — LIST_V3 L11c.

stat 숙제 잔여: past_learn.WIN_1Y (1yHot/Cold 창)만 스윕.
LOCKED 재탕 금지: HINT weeks=52 miss_pattern · HINT_WEIGHT=0.15 ·
Jaccard 0.85 · oversample×3 · ASSOC OFF · ENGINE win26/mix0.8.
게이트: stat_hit↑ |Δ|≥0.005 · prefer/prize iso(|drift|<0.005).
hit는 모니터+게이트축 · ge3 미클레임 · 1237아님.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260813_KSTAT_HOMEWORK_QUALITY.json"
OUT_MD = ROOT / "reports" / "20260813_KSTAT_HOMEWORK_QUALITY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80
ABS_THR = 0.005
ISO_THR = 0.005
BASE_W = 52
CANDS = [26, 39, 52, 78, 104]
LOCK_WEEKS = 52
LOCK_HINT_W = 0.15
LOCK_JACCARD = 0.85
LOCK_OVERSAMPLE = 3


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _precheck() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.shared import aux_hint as ah
    from app.testlotto.brains.shared import diversity as div
    from app.testlotto.brains.stat_brain import past_learn as pl

    spec = sp.HINT_SPEC_BY_BRAIN.get("stat")
    hw = float(ah.HINT_WEIGHT_BY_BRAIN.get("stat", -1))
    jac = float(div.JACCARD_PENALTY_BY_BRAIN.get("stat", -1))
    ov = int(div.OVERSAMPLE_MULT_BY_BRAIN.get("stat", -1))
    assoc = bool(pl.assoc_hint_on())
    return {
        "HINT_SPEC_stat": list(spec) if spec else None,
        "HINT_WEIGHT_stat": hw,
        "JACCARD_stat": jac,
        "OVERSAMPLE_stat": ov,
        "ASSOC": assoc,
        "WIN_1Y": int(pl.WIN_1Y),
        "lock_ok": (
            spec == (LOCK_WEEKS, "miss_pattern")
            and abs(hw - LOCK_HINT_W) < 1e-12
            and abs(jac - LOCK_JACCARD) < 1e-12
            and ov == LOCK_OVERSAMPLE
            and assoc is False
        ),
    }


def _patch(weeks: int):
    from app.testlotto.brains.stat_brain import past_learn as pl

    saved = int(pl.WIN_1Y)
    pl.WIN_1Y = int(weeks)

    def restore() -> None:
        pl.WIN_1Y = saved

    return restore


def _run(seed: int, weeks: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy

    restore = _patch(weeks)
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
            act = _actual(dno)
            mnums = [n for c in pool_br.get("markov", []) for n in c["nums"]]
            rnums = [n for c in pool_br.get("review", []) for n in c["nums"]]
            if mnums:
                prefer.append(mean(fw[n] for n in mnums) - all_mean)
            if rnums:
                prize.append(mean(fw[n] for n in rnums) - all_mean)
            ssets = [[int(x) for x in c["nums"]] for c in pool_br.get("stat", [])]
            if ssets:
                hits.append(max(len(set(s) & act) for s in ssets) / 6.0)
            learner.update_from_pool(pool_br, act)
        return {
            "seed": seed,
            "n": len(hits),
            "prefer": round(mean(prefer), 6) if prefer else None,
            "prize": round(mean(prize), 6) if prize else None,
            "stat_hit": round(mean(hits), 6) if hits else None,
        }
    finally:
        restore()


def _agg(w: int, runs: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in runs if d["prefer"] is not None)
    prize = mean(d["prize"] for d in runs if d["prize"] is not None)
    hit = mean(d["stat_hit"] for d in runs if d["stat_hit"] is not None)
    row: dict[str, Any] = {
        "win_1y": w,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "stat_hit": round(hit, 6),
        "per_seed": runs,
    }
    if base is None:
        row["gate"] = {"is_baseline": True, "pass": True}
        return row
    d_hit = hit - base["stat_hit"]
    d_pref = prefer - base["prefer"]
    d_prize = prize - base["prize"]
    improve = d_hit >= ABS_THR
    iso = abs(d_pref) < ISO_THR and abs(d_prize) < ISO_THR
    ok = improve and iso
    row["gate"] = {
        "d_stat_hit": round(d_hit, 6),
        "d_prefer": round(d_pref, 6),
        "d_prize": round(d_prize, 6),
        "improve": improve,
        "prefer_prize_iso": iso,
        "pass": ok,
    }
    return row


def main() -> int:
    from app.testlotto.brains.stat_brain import past_learn as pl

    pre = _precheck()
    if not pre["lock_ok"]:
        print("FAIL lock precheck", pre)
        return 1

    by: dict[str, dict[str, Any]] = {}
    order = [BASE_W] + [w for w in CANDS if w != BASE_W]
    base_row: dict[str, Any] | None = None
    for w in order:
        name = f"win1y_{w}"
        print(f"== {name} ==", flush=True)
        runs = []
        for seed in SEEDS:
            r = _run(seed, w)
            print(
                f"  seed={seed} prefer={r['prefer']} prize={r['prize']} "
                f"hit={r['stat_hit']}",
                flush=True,
            )
            runs.append(r)
        row = _agg(w, runs, None if w == BASE_W else base_row)
        by[name] = row
        if w == BASE_W:
            base_row = row

    assert base_row is not None
    winners: list[dict[str, Any]] = []
    for name, row in by.items():
        if int(row["win_1y"]) == BASE_W:
            continue
        g = row.get("gate") or {}
        if g.get("pass"):
            winners.append({"name": name, **g, "win_1y": row["win_1y"]})

    apply = False
    if winners:
        best = max(winners, key=lambda x: (x["d_stat_hit"], -abs(x["d_prefer"])))
        verdict = "APPLY_OK"
        apply = True
        path = ROOT / "app" / "testlotto" / "brains" / "stat_brain" / "past_learn.py"
        src = path.read_text(encoding="utf-8")
        src2, n = re.subn(
            r"WIN_1Y = \d+",
            f"WIN_1Y = {int(best['win_1y'])}",
            src,
            count=1,
        )
        if n != 1:
            raise SystemExit("APPLY patch failed")
        path.write_text(src2, encoding="utf-8")
        pl.WIN_1Y = int(best["win_1y"])
        note = (
            f"APPLY WIN_1Y={best['win_1y']} · d_hit={best['d_stat_hit']} · 다음 L12"
        )
    else:
        best = None
        verdict = "HOLD"
        note = "신호없음 HOLD · WIN_1Y=52 · HINT/Jaccard/oversample 불변 · 다음 L12"

    payload = {
        "id": "K-STAT-HOMEWORK-QUALITY",
        "list": "LIST_V3",
        "step": "L11c",
        "status": verdict,
        "ts": _now(),
        "wire": bool(apply),
        "apply": bool(apply),
        "ge3_used_as_claim": False,
        "locked_not_reswept": {
            "HINT_SPEC_BY_BRAIN.stat": [LOCK_WEEKS, "miss_pattern"],
            "HINT_WEIGHT_stat": LOCK_HINT_W,
            "JACCARD_stat": LOCK_JACCARD,
            "OVERSAMPLE_stat": LOCK_OVERSAMPLE,
            "ASSOC": False,
        },
        "precheck": pre,
        "range": [LO, HI],
        "seeds": SEEDS,
        "knob": "past_learn.WIN_1Y",
        "base": BASE_W,
        "cands": CANDS,
        "configs": by,
        "winners": winners,
        "best": best,
        "thresholds": {"ABS_THR": ABS_THR, "ISO_THR": ISO_THR},
        "live_after": {"WIN_1Y": int(pl.WIN_1Y)},
        "next": {"step": "L12", "id": "K-TICKET-POOL-UNIFY", "approval": True},
        "force_bt": False,
        "s1": False,
        "note": note + " · 1237아님",
    }
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# K-STAT-HOMEWORK-QUALITY — LIST_V3 L11c",
        "",
        f"시각: {payload['ts']} · **{verdict}** · apply=**{apply}** · **1237아님** · ge3미클레임",
        f"노브: `past_learn.WIN_1Y` (1yHot/Cold) · "
        f"LOCKED HINT52/WEIGHT0.15/J0.85/ov×3/ASSOC OFF **재탕안함**",
        f"구간: {LO}~{HI} seeds={SEEDS}",
        "",
        f"## base WIN_1Y={BASE_W}",
        "",
        "| prefer | prize | stat_hit(모니터·게이트) |",
        "|--------|-------|-------------------------|",
        f"| {base_row['prefer']} | {base_row['prize']} | {base_row['stat_hit']} |",
        "",
        "## cands",
        "",
    ]
    for name, row in by.items():
        if int(row["win_1y"]) == BASE_W:
            continue
        g = row.get("gate") or {}
        lines.append(
            f"- `{name}`: prefer={row['prefer']} prize={row['prize']} "
            f"hit={row['stat_hit']} · d_hit={g.get('d_stat_hit')} "
            f"d_prefer={g.get('d_prefer')} d_prize={g.get('d_prize')} · "
            f"pass=**{g.get('pass')}**"
        )
    lines += [
        "",
        f"판정: **{verdict}** — {note}",
        "",
        f"벤치: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        f"도구: `tools/_k_stat_homework_quality.py`",
        "",
        "다음: **L12** 발권↔10+5 통합 (형 승인)",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {"verdict": verdict, "apply": apply, "best": best},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
