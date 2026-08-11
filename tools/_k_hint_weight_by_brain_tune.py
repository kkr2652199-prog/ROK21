# -*- coding: utf-8 -*-
"""K-HINT-WEIGHT-BY-BRAIN-TUNE — aux HINT_WEIGHT 뇌별 스윕.

I-AUX-HINT-WEIGHT 후속. base=0.15. ge3미사용.
  markov: prefer↑ · |Δ|≥0.005 · prize iso(|drift|<0.005) · split both+
  review: prize↓(더음수) · |Δ|≥0.005 · prefer iso · split both−
  stat:   top15_hit ≥ base−0.01 · prefer/prize iso
wire 측정 → 통과 뇌만 APPLY.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KHINT_WEIGHT_BY_BRAIN_TUNE_v2.json"
OUT_MD = ROOT / "reports" / "20260811_KHINT_WEIGHT_BY_BRAIN_TUNE_v2.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
# v2: pick_score 배선 후 재측정 (DEAD_WIRE 해소). seed3 유지 · cand 축소로 시간↓
SEEDS = [0, 42, 123]
WARM_BACK = 80
ABS_THR = 0.005
ISO_THR = 0.005
STAT_SLACK = 0.01
BASE_W = 0.15
CANDS = [0.05, 0.15, 0.25, 0.35]


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _patch(brain: str, w: float):
    from app.testlotto.brains.shared import aux_hint as ah
    from app.testlotto.brains.markov_brain import predict as mk
    from app.testlotto.brains.review_brain import predict as rv
    from app.testlotto.brains.stat_brain import predict as st

    saved = {
        "by": dict(ah.HINT_WEIGHT_BY_BRAIN),
        "mk": mk.HINT_WEIGHT,
        "rv": rv.HINT_WEIGHT,
        "st": st.HINT_WEIGHT,
    }
    ah.HINT_WEIGHT_BY_BRAIN[brain] = float(w)
    if brain == "markov":
        mk.HINT_WEIGHT = float(w)
    elif brain == "review":
        rv.HINT_WEIGHT = float(w)
    else:
        st.HINT_WEIGHT = float(w)

    def restore() -> None:
        ah.HINT_WEIGHT_BY_BRAIN.clear()
        ah.HINT_WEIGHT_BY_BRAIN.update(saved["by"])
        mk.HINT_WEIGHT = saved["mk"]
        rv.HINT_WEIGHT = saved["rv"]
        st.HINT_WEIGHT = saved["st"]

    return restore


def _run(seed: int, brain: str, w: float) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy, _top15

    restore = _patch(brain, w)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer: list[tuple[int, float]] = []
        prize: list[tuple[int, float]] = []
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
            prefer.append((dno, mean(fw[n] for n in _top15(scores["markov"])) - all_mean))
            prize.append((dno, mean(fw[n] for n in _top15(scores["review"])) - all_mean))
            act = _actual(dno)
            hits.append(len(set(_top15(scores["stat"])) & act) / 6.0)
            learner.update_from_pool(pool_br, act)
        mid = (LO + HI) // 2
        pref_lo = [v for d, v in prefer if d <= mid]
        pref_hi = [v for d, v in prefer if d > mid]
        prize_lo = [v for d, v in prize if d <= mid]
        prize_hi = [v for d, v in prize if d > mid]
        return {
            "seed": seed,
            "n": len(prefer),
            "prefer": round(mean(v for _, v in prefer), 6) if prefer else None,
            "prize": round(mean(v for _, v in prize), 6) if prize else None,
            "stat_hit": round(mean(hits), 6) if hits else None,
            "prefer_lo": round(mean(pref_lo), 6) if pref_lo else None,
            "prefer_hi": round(mean(pref_hi), 6) if pref_hi else None,
            "prize_lo": round(mean(prize_lo), 6) if prize_lo else None,
            "prize_hi": round(mean(prize_hi), 6) if prize_hi else None,
        }
    finally:
        restore()


def _agg_markov(w: float, by: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    split = mean(d["prefer_lo"] for d in by) > 0 and mean(d["prefer_hi"] for d in by) > 0
    if base is None:
        return {
            "brain": "markov",
            "w": w,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "gate_pass": prefer > 0 and split,
            "gate_detail": {"is_baseline": True, "split": split},
            "per_seed": by,
        }
    dpref = prefer - base["prefer"]
    drift = abs(prize - base["prize"])
    detail = {
        "prefer_pos": prefer > 0,
        "split": split,
        "improve": prefer > base["prefer"],
        "abs": abs(dpref) >= ABS_THR,
        "iso": drift < ISO_THR,
        "dprefer": round(dpref, 6),
        "drift": round(drift, 6),
    }
    return {
        "brain": "markov",
        "w": w,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "gate_pass": all(detail[k] for k in ("prefer_pos", "split", "improve", "abs", "iso")),
        "gate_detail": detail,
        "per_seed": by,
    }


def _agg_review(w: float, by: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    split = mean(d["prize_lo"] for d in by) < 0 and mean(d["prize_hi"] for d in by) < 0
    if base is None:
        return {
            "brain": "review",
            "w": w,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "gate_pass": prize < 0 and split,
            "gate_detail": {"is_baseline": True, "split": split},
            "per_seed": by,
        }
    dprize = prize - base["prize"]
    drift = abs(prefer - base["prefer"])
    detail = {
        "prize_neg": prize < 0,
        "split": split,
        "improve": prize < base["prize"],
        "abs": abs(dprize) >= ABS_THR,
        "iso": drift < ISO_THR,
        "dprize": round(dprize, 6),
        "drift": round(drift, 6),
    }
    return {
        "brain": "review",
        "w": w,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "gate_pass": all(detail[k] for k in ("prize_neg", "split", "improve", "abs", "iso")),
        "gate_detail": detail,
        "per_seed": by,
    }


def _agg_stat(w: float, by: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    hit = mean(d["stat_hit"] for d in by if d["stat_hit"] is not None)
    if base is None:
        return {
            "brain": "stat",
            "w": w,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "stat_hit": round(hit, 6),
            "gate_pass": True,
            "gate_detail": {"is_baseline": True},
            "per_seed": by,
        }
    dhit = hit - base["stat_hit"]
    detail = {
        "stat_ok": hit >= base["stat_hit"] - STAT_SLACK,
        "improve": dhit >= ABS_THR,
        "prefer_iso": abs(prefer - base["prefer"]) < ISO_THR,
        "prize_iso": abs(prize - base["prize"]) < ISO_THR,
        "dhit": round(dhit, 6),
    }
    return {
        "brain": "stat",
        "w": w,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "stat_hit": round(hit, 6),
        "gate_pass": all(
            detail[k] for k in ("stat_ok", "improve", "prefer_iso", "prize_iso")
        ),
        "gate_detail": detail,
        "per_seed": by,
    }


def _apply(chosen: dict[str, float]) -> None:
    path = ROOT / "app" / "testlotto" / "brains" / "shared" / "aux_hint.py"
    text = path.read_text(encoding="utf-8")
    block = (
        "HINT_WEIGHT_BY_BRAIN: dict[str, float] = {\n"
        f'    "stat": {chosen["stat"]},\n'
        f'    "markov": {chosen["markov"]},\n'
        f'    "review": {chosen["review"]},\n'
        "}"
    )
    text2, n = re.subn(
        r"HINT_WEIGHT_BY_BRAIN: dict\[str, float\] = \{[^}]+\}",
        block,
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError("HINT_WEIGHT_BY_BRAIN block replace failed")
    path.write_text(text2, encoding="utf-8")
    # sync module-level aliases in predict files (import-time values)
    for tag, rel in (
        ("stat", "stat_brain/predict.py"),
        ("markov", "markov_brain/predict.py"),
        ("review", "review_brain/predict.py"),
    ):
        p = ROOT / "app" / "testlotto" / "brains" / rel
        # HINT_WEIGHT is derived at import from BY_BRAIN — re-write BY_BRAIN is enough
        # after process restart; for live modules update now:
        pass
    from app.testlotto.brains.shared import aux_hint as ah
    from app.testlotto.brains.markov_brain import predict as mk
    from app.testlotto.brains.review_brain import predict as rv
    from app.testlotto.brains.stat_brain import predict as st

    ah.HINT_WEIGHT_BY_BRAIN.clear()
    ah.HINT_WEIGHT_BY_BRAIN.update(chosen)
    mk.HINT_WEIGHT = float(chosen["markov"])
    rv.HINT_WEIGHT = float(chosen["review"])
    st.HINT_WEIGHT = float(chosen["stat"])


def main() -> None:
    from app.testlotto.brains.shared import aux_hint as ah

    results: dict[str, list[dict]] = {"markov": [], "review": [], "stat": []}
    bases: dict[str, dict] = {}

    for brain, agg in (
        ("markov", _agg_markov),
        ("review", _agg_review),
        ("stat", _agg_stat),
    ):
        print(f"== {brain} base={BASE_W} ==", flush=True)
        base_rows = [_run(s, brain, BASE_W) for s in SEEDS]
        if brain == "stat":
            base = _agg_stat(BASE_W, base_rows, None)
        elif brain == "markov":
            base = _agg_markov(BASE_W, base_rows, None)
        else:
            base = _agg_review(BASE_W, base_rows, None)
        bases[brain] = base
        results[brain].append(base)
        for w in CANDS:
            if abs(w - BASE_W) < 1e-12:
                continue
            print(f"  run {brain} w={w} ...", flush=True)
            rows = [_run(s, brain, w) for s in SEEDS]
            if brain == "stat":
                results[brain].append(
                    _agg_stat(
                        w,
                        rows,
                        {
                            "prefer": base["prefer"],
                            "prize": base["prize"],
                            "stat_hit": base["stat_hit"],
                        },
                    )
                )
            elif brain == "markov":
                results[brain].append(
                    _agg_markov(
                        w, rows, {"prefer": base["prefer"], "prize": base["prize"]}
                    )
                )
            else:
                results[brain].append(
                    _agg_review(
                        w, rows, {"prefer": base["prefer"], "prize": base["prize"]}
                    )
                )

    chosen = {
        "stat": BASE_W,
        "markov": BASE_W,
        "review": BASE_W,
    }
    picks: dict[str, Any] = {}
    for brain in ("markov", "review", "stat"):
        passers = [r for r in results[brain] if r["gate_pass"] and abs(r["w"] - BASE_W) > 1e-12]
        if brain == "markov":
            best = max(passers, key=lambda r: r["prefer"]) if passers else None
        elif brain == "review":
            best = min(passers, key=lambda r: r["prize"]) if passers else None
        else:
            best = max(passers, key=lambda r: r["stat_hit"]) if passers else None
        picks[brain] = best
        if best:
            chosen[brain] = float(best["w"])

    any_apply = any(abs(chosen[b] - BASE_W) > 1e-12 for b in chosen)
    if any_apply:
        _apply(chosen)
        verdict = "APPLY"
    else:
        verdict = "NO_IMPROVE_HOLD"

    out = {
        "id": "K-HINT-WEIGHT-BY-BRAIN-TUNE",
        "ts": _now(),
        "range": [LO, HI],
        "seeds": SEEDS,
        "base_w": BASE_W,
        "cands": CANDS,
        "live_before": dict(ah.HINT_WEIGHT_BY_BRAIN),
        "results": results,
        "picks": {k: (v and {"w": v["w"], "gate": v["gate_pass"]}) for k, v in picks.items()},
        "chosen": chosen,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "note": "I-AUX-HINT-WEIGHT · 1237아님 · signal_union 전제",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-HINT-WEIGHT-BY-BRAIN-TUNE",
        "",
        f"시각: {out['ts']} · {LO}~{HI} · seeds={SEEDS}",
        "",
        f"## 판정 **{verdict}** · chosen=`{chosen}`",
        "",
    ]
    for brain in ("markov", "review", "stat"):
        lines.append(f"### {brain}")
        lines.append("| w | prefer | prize | hit | gate |")
        lines.append("|---|--------|-------|-----|------|")
        for r in results[brain]:
            hit = r.get("stat_hit", "")
            lines.append(
                f"| {r['w']} | {r.get('prefer')} | {r.get('prize')} | {hit} | {r['gate_pass']} |"
            )
        lines.append("")
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print("VERDICT", verdict, "chosen", chosen)
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
