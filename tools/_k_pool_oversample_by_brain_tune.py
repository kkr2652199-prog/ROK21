# -*- coding: utf-8 -*-
"""K-POOL-OVERSAMPLE-BY-BRAIN-TUNE — pool 후보 배수(oversample) 뇌별 스윕.

노브: diversity.OVERSAMPLE_MULT_BY_BRAIN (기본 3).
축(풀 세트 nums · ge3미사용) — jaccard 툴과 동일. review는 base prize≥0이면
절대음수 조건 면제(상대 improve만).
통과 뇌만 APPLY.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KPOOL_OVERSAMPLE_BY_BRAIN_TUNE.json"
OUT_MD = ROOT / "reports" / "20260811_KPOOL_OVERSAMPLE_BY_BRAIN_TUNE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80
ABS_THR = 0.005
ISO_THR = 0.005
STAT_SLACK = 0.01
BASE_M = 3
CANDS = [3, 4, 5, 6]


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _patch(brain: str, m: int):
    from app.testlotto.brains.shared import diversity as div

    saved = dict(div.OVERSAMPLE_MULT_BY_BRAIN)
    div.OVERSAMPLE_MULT_BY_BRAIN[brain] = int(m)

    def restore() -> None:
        div.OVERSAMPLE_MULT_BY_BRAIN.clear()
        div.OVERSAMPLE_MULT_BY_BRAIN.update(saved)

    return restore


def _run(seed: int, brain: str, m: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy

    restore = _patch(brain, m)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer: list[tuple[int, float]] = []
        prize: list[tuple[int, float]] = []
        hits: list[float] = []
        hit_mon: dict[str, list[float]] = {t: [] for t in sp.BRAIN_TAGS}
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
                prefer.append((dno, mean(fw[n] for n in mnums) - all_mean))
            if rnums:
                prize.append((dno, mean(fw[n] for n in rnums) - all_mean))
            ssets = [[int(x) for x in c["nums"]] for c in pool_br.get("stat", [])]
            if ssets:
                hits.append(max(len(set(s) & act) for s in ssets) / 6.0)
            for tag in sp.BRAIN_TAGS:
                psets = [[int(x) for x in c["nums"]] for c in pool_br.get(tag, [])]
                if psets:
                    hit_mon[tag].append(max(len(set(s) & act) for s in psets) / 6.0)
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
            "pool_hit_mon": {
                t: round(mean(vs), 6) if vs else None for t, vs in hit_mon.items()
            },
        }
    finally:
        restore()


def _mon(by: list[dict]) -> dict[str, float]:
    return {
        t: round(
            mean(d["pool_hit_mon"][t] for d in by if d["pool_hit_mon"].get(t) is not None),
            6,
        )
        for t in ("stat", "markov", "review")
    }


def _agg_markov(m: int, by: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    split = mean(d["prefer_lo"] for d in by) > 0 and mean(d["prefer_hi"] for d in by) > 0
    if base is None:
        return {
            "brain": "markov",
            "m": m,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "pool_hit_mon": _mon(by),
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
        "m": m,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "pool_hit_mon": _mon(by),
        "gate_pass": all(detail[k] for k in ("prefer_pos", "split", "improve", "abs", "iso")),
        "gate_detail": detail,
        "per_seed": by,
    }


def _agg_review(m: int, by: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    # pool nums는 top15 대비 덜 음수일 수 있음 → base≥0이면 절대음수 면제
    split_neg = mean(d["prize_lo"] for d in by) < 0 and mean(d["prize_hi"] for d in by) < 0
    if base is None:
        ok = (prize < 0 and split_neg) or prize >= 0
        return {
            "brain": "review",
            "m": m,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "pool_hit_mon": _mon(by),
            "gate_pass": ok,
            "gate_detail": {
                "is_baseline": True,
                "split_neg": split_neg,
                "pool_prize_nonneg_waive": prize >= 0,
            },
            "per_seed": by,
        }
    dprize = prize - base["prize"]
    drift = abs(prefer - base["prefer"])
    need_neg = base["prize"] < 0
    detail = {
        "prize_ok": (prize < 0) if need_neg else True,
        "improve": prize < base["prize"],
        "abs": abs(dprize) >= ABS_THR,
        "iso": drift < ISO_THR,
        "dprize": round(dprize, 6),
        "drift": round(drift, 6),
        "need_neg": need_neg,
    }
    return {
        "brain": "review",
        "m": m,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "pool_hit_mon": _mon(by),
        "gate_pass": all(detail[k] for k in ("prize_ok", "improve", "abs", "iso")),
        "gate_detail": detail,
        "per_seed": by,
    }


def _agg_stat(m: int, by: list[dict], base: dict | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    hit = mean(d["stat_hit"] for d in by if d["stat_hit"] is not None)
    if base is None:
        return {
            "brain": "stat",
            "m": m,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "stat_hit": round(hit, 6),
            "pool_hit_mon": _mon(by),
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
        "m": m,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "stat_hit": round(hit, 6),
        "pool_hit_mon": _mon(by),
        "gate_pass": all(
            detail[k] for k in ("stat_ok", "improve", "prefer_iso", "prize_iso")
        ),
        "gate_detail": detail,
        "per_seed": by,
    }


def _apply(chosen: dict[str, int]) -> None:
    path = ROOT / "app" / "testlotto" / "brains" / "shared" / "diversity.py"
    text = path.read_text(encoding="utf-8")
    block = (
        "OVERSAMPLE_MULT_BY_BRAIN: dict[str, int] = {\n"
        f'    "stat": {int(chosen["stat"])},\n'
        f'    "markov": {int(chosen["markov"])},\n'
        f'    "review": {int(chosen["review"])},\n'
        "}"
    )
    text2, n = re.subn(
        r"OVERSAMPLE_MULT_BY_BRAIN: dict\[str, int\] = \{[^}]+\}",
        block,
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError("OVERSAMPLE_MULT_BY_BRAIN block replace failed")
    path.write_text(text2, encoding="utf-8")
    from app.testlotto.brains.shared import diversity as div

    div.OVERSAMPLE_MULT_BY_BRAIN.clear()
    div.OVERSAMPLE_MULT_BY_BRAIN.update({k: int(v) for k, v in chosen.items()})


def main() -> None:
    from app.testlotto.brains.shared import diversity as div

    results: dict[str, list[dict]] = {"markov": [], "review": [], "stat": []}

    for brain, agg in (
        ("markov", _agg_markov),
        ("review", _agg_review),
        ("stat", _agg_stat),
    ):
        print(f"== {brain} base={BASE_M} ==", flush=True)
        base_rows = [_run(s, brain, BASE_M) for s in SEEDS]
        base = agg(BASE_M, base_rows, None)
        results[brain].append(base)
        for m in CANDS:
            if m == BASE_M:
                continue
            print(f"  run {brain} m={m} ...", flush=True)
            rows = [_run(s, brain, m) for s in SEEDS]
            if brain == "stat":
                results[brain].append(
                    agg(
                        m,
                        rows,
                        {
                            "prefer": base["prefer"],
                            "prize": base["prize"],
                            "stat_hit": base["stat_hit"],
                        },
                    )
                )
            else:
                results[brain].append(
                    agg(m, rows, {"prefer": base["prefer"], "prize": base["prize"]})
                )

    chosen = {"stat": BASE_M, "markov": BASE_M, "review": BASE_M}
    picks: dict[str, Any] = {}
    for brain in ("markov", "review", "stat"):
        passers = [
            r for r in results[brain] if r["gate_pass"] and int(r["m"]) != BASE_M
        ]
        if brain == "markov":
            best = max(passers, key=lambda r: r["prefer"]) if passers else None
        elif brain == "review":
            best = min(passers, key=lambda r: r["prize"]) if passers else None
        else:
            best = max(passers, key=lambda r: r["stat_hit"]) if passers else None
        picks[brain] = best
        if best:
            chosen[brain] = int(best["m"])

    any_apply = any(int(chosen[b]) != BASE_M for b in chosen)
    if any_apply:
        _apply(chosen)
        verdict = "APPLY"
    else:
        verdict = "NO_IMPROVE_HOLD"

    out = {
        "id": "K-POOL-OVERSAMPLE-BY-BRAIN-TUNE",
        "ts": _now(),
        "range": [LO, HI],
        "seeds": SEEDS,
        "base_m": BASE_M,
        "cands": CANDS,
        "live_before": dict(div.OVERSAMPLE_MULT_BY_BRAIN),
        "results": results,
        "picks": {
            k: (v and {"m": v["m"], "gate": v["gate_pass"]}) for k, v in picks.items()
        },
        "chosen": chosen,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "note": "양산前 pool품질 · jaccard HOLD 후속 · 1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-POOL-OVERSAMPLE-BY-BRAIN-TUNE",
        "",
        f"시각: {out['ts']} · {LO}~{HI} · seeds={SEEDS}",
        "",
        f"## 판정 **{verdict}** · chosen=`{chosen}`",
        "",
        "노브: `OVERSAMPLE_MULT_BY_BRAIN`",
        "",
    ]
    for brain in ("markov", "review", "stat"):
        lines.append(f"### {brain}")
        lines.append("| m | prefer | prize | hit | gate |")
        lines.append("|---|--------|-------|-----|------|")
        for r in results[brain]:
            hit = r.get("stat_hit", "")
            lines.append(
                f"| {r['m']} | {r.get('prefer')} | {r.get('prize')} | {hit} | {r['gate_pass']} |"
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
