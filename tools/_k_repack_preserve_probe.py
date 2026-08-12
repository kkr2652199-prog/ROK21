# -*- coding: utf-8 -*-
"""K-REPACK-PRESERVE-PROBE — LIST_V3 L9.

union/slots 소형 스윕 · 신호 없으면 HOLD (기본 knobs 유지).
축: prefer/prize 비악화 + pool적중번호→repack 보존비 / pool>repack 모니터.
ge3 클레임 금지 · 1237아님 · 강제BT/S1 미포함.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KREPACK_PRESERVE_PROBE.json"
OUT_MD = ROOT / "reports" / "20260812_KREPACK_PRESERVE_PROBE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80
# 소형 그리드: base=(2,4) + 주변 4셀
CONFIGS: list[tuple[str, int, int]] = [
    ("base_s2_c4", 2, 4),
    ("cand_s2_c3", 2, 3),
    ("cand_s2_c5", 2, 5),
    ("cand_s3_c4", 3, 4),
    ("cand_s1_c4", 1, 4),
]
PREF_EPS = 0.005
PRIZE_EPS = 0.005
PRESERVE_DELTA = 0.01
LOSS_DELTA = 3.0  # pool>repack 평균 횟수 감소


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _apply_cfg(sp: Any, slots: int, cap: int) -> None:
    for t in sp.BRAIN_TAGS:
        sp.POOL_SLOTS_BY_BRAIN[t] = int(slots)
        sp.POOL_UNION_CAP_BY_BRAIN[t] = int(cap)
    sp.POOL_SLOTS_PER_BRAIN = int(slots)
    sp.POOL_UNION_CAP = int(cap)


def _run_one(seed: int, slots: int, cap: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy

    saved_slots = dict(sp.POOL_SLOTS_BY_BRAIN)
    saved_cap = dict(sp.POOL_UNION_CAP_BY_BRAIN)
    saved_ps = sp.POOL_SLOTS_PER_BRAIN
    saved_pc = sp.POOL_UNION_CAP
    _apply_cfg(sp, slots, cap)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer: list[float] = []
        prize: list[float] = []
        preserve: list[float] = []
        loss = Counter()
        n_ok = 0
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
            rows = sp.repack_by_brain(
                pool_br,
                fallback,
                num_ema,
                pos_ema,
                target_draw_no=dno,
                hint_by_brain=hint_by,
            )
            by: dict[str, list[list[int]]] = {t: [] for t in sp.BRAIN_TAGS}
            for r in rows:
                by.setdefault(str(r["brain_tag"]), []).append([int(x) for x in r["nums"]])
            act = _actual(dno)
            # preserve: 뇌평균 (pool적중번호 ∩ repack) / pool적중
            pres_brain: list[float] = []
            for tag in sp.BRAIN_TAGS:
                psets = [[int(x) for x in c["nums"]] for c in pool_br.get(tag, [])]
                rsets = by.get(tag) or []
                if not psets or not rsets:
                    continue
                p_hit = {n for s in psets for n in s} & act
                r_hit = {n for s in rsets for n in s} & act
                if p_hit:
                    pres_brain.append(len(p_hit & r_hit) / len(p_hit))
                ph = max(len(set(s) & act) for s in psets)
                rh = max(len(set(s) & act) for s in rsets)
                if ph > rh:
                    loss[tag] += 1
            if pres_brain:
                preserve.append(mean(pres_brain))
            mnums = [n for s in by.get("markov", []) for n in s]
            rnums = [n for s in by.get("review", []) for n in s]
            if mnums:
                prefer.append(mean(fw[n] for n in mnums) - all_mean)
            if rnums:
                prize.append(mean(fw[n] for n in rnums) - all_mean)
            learner.update_from_pool(pool_br, act)
            n_ok += 1
        return {
            "seed": seed,
            "slots": slots,
            "cap": cap,
            "n": n_ok,
            "prefer": round(mean(prefer), 6) if prefer else None,
            "prize": round(mean(prize), 6) if prize else None,
            "preserve": round(mean(preserve), 6) if preserve else None,
            "pool_gt_repack": {t: int(loss[t]) for t in sp.BRAIN_TAGS},
            "pool_gt_repack_sum": int(sum(loss.values())),
        }
    finally:
        sp.POOL_SLOTS_BY_BRAIN.clear()
        sp.POOL_SLOTS_BY_BRAIN.update(saved_slots)
        sp.POOL_UNION_CAP_BY_BRAIN.clear()
        sp.POOL_UNION_CAP_BY_BRAIN.update(saved_cap)
        sp.POOL_SLOTS_PER_BRAIN = saved_ps
        sp.POOL_UNION_CAP = saved_pc


def _agg(runs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "prefer": round(mean(r["prefer"] for r in runs if r["prefer"] is not None), 6),
        "prize": round(mean(r["prize"] for r in runs if r["prize"] is not None), 6),
        "preserve": round(mean(r["preserve"] for r in runs if r["preserve"] is not None), 6),
        "pool_gt_repack_sum": round(
            mean(r["pool_gt_repack_sum"] for r in runs), 2
        ),
        "per_seed": runs,
    }


def main() -> int:
    import app.testlotto.signal_pool as sp

    live = {
        "ASSEMBLE_MODE": sp.ASSEMBLE_MODE,
        "POOL_SLOTS_BY_BRAIN": dict(sp.POOL_SLOTS_BY_BRAIN),
        "POOL_UNION_CAP_BY_BRAIN": dict(sp.POOL_UNION_CAP_BY_BRAIN),
        "ROLE_SLOTS_WIRE": bool(sp.ROLE_SLOTS_WIRE),
        "LEDGER_SIGNAL_WIRE": bool(sp.LEDGER_SIGNAL_WIRE),
        "LEDGER_BLEND": float(sp.LEDGER_BLEND),
    }
    assert sp.ASSEMBLE_MODE == "signal_union"

    by_cfg: dict[str, dict[str, Any]] = {}
    for name, slots, cap in CONFIGS:
        print(f"== {name} slots={slots} cap={cap} ==", flush=True)
        runs = []
        for s in SEEDS:
            r = _run_one(s, slots, cap)
            print(
                f"  seed={s} prefer={r['prefer']} prize={r['prize']} "
                f"preserve={r['preserve']} loss_sum={r['pool_gt_repack_sum']}",
                flush=True,
            )
            runs.append(r)
        by_cfg[name] = {"slots": slots, "cap": cap, **_agg(runs)}

    base = by_cfg["base_s2_c4"]
    winners: list[dict[str, Any]] = []
    for name, row in by_cfg.items():
        if name.startswith("base"):
            continue
        d_pref = row["prefer"] - base["prefer"]
        d_prize = row["prize"] - base["prize"]  # more negative is better for prize axis
        d_pres = row["preserve"] - base["preserve"]
        d_loss = base["pool_gt_repack_sum"] - row["pool_gt_repack_sum"]  # + = improved
        health = row["prefer"] > 0 and row["prize"] < 0
        non_worse = d_pref >= -PREF_EPS and d_prize <= PRIZE_EPS
        signal = d_pres >= PRESERVE_DELTA or d_loss >= LOSS_DELTA
        ok = health and non_worse and signal
        detail = {
            "name": name,
            "slots": row["slots"],
            "cap": row["cap"],
            "d_prefer": round(d_pref, 6),
            "d_prize": round(d_prize, 6),
            "d_preserve": round(d_pres, 6),
            "d_loss_sum": round(d_loss, 2),
            "health": health,
            "non_worse": non_worse,
            "signal": signal,
            "pass": ok,
        }
        if ok:
            winners.append(detail)
        by_cfg[name]["gate"] = detail

    if winners:
        # 보존↑ 우선 · 동점이면 loss↓ · prefer
        best = max(
            winners,
            key=lambda w: (w["d_preserve"], w["d_loss_sum"], w["d_prefer"]),
        )
        verdict = "PROBE_SIGNAL"
        apply = False  # L9는 프로브 · APPLY는 형 GO 후 (신호만 보고)
        next_note = f"신호후보={best['name']} · 형 GO 전 APPLY 금지 · 다음 L10"
    else:
        best = None
        verdict = "HOLD"
        apply = False
        next_note = "신호없음 HOLD · knobs 불변(slots2·cap4) · 다음 L10"

    # 안전: 라이브 knobs 복원 확인
    _apply_cfg(sp, 2, 4)

    payload = {
        "id": "K-REPACK-PRESERVE-PROBE",
        "list": "LIST_V3",
        "step": "L9",
        "status": verdict,
        "ts": _now(),
        "wire": False,
        "apply": apply,
        "ge3_used_as_claim": False,
        "range": [LO, HI],
        "seeds": SEEDS,
        "live": live,
        "configs": by_cfg,
        "base": "base_s2_c4",
        "winners": winners,
        "best": best,
        "thresholds": {
            "PREF_EPS": PREF_EPS,
            "PRIZE_EPS": PRIZE_EPS,
            "PRESERVE_DELTA": PRESERVE_DELTA,
            "LOSS_DELTA": LOSS_DELTA,
        },
        "next": {"step": "L10", "id": "K-TICKET-COVER-LITE"},
        "force_bt": False,
        "s1": False,
        "note": next_note + " · 1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-REPACK-PRESERVE-PROBE — LIST_V3 L9",
        "",
        f"시각: {payload['ts']} · **{verdict}** · apply=**{apply}** · **1237아님** · ge3미클레임",
        f"구간: {LO}~{HI} seeds={SEEDS} · assemble=signal_union",
        f"다음: **L10** K-TICKET-COVER-LITE",
        "",
        "## base (slots=2 · cap=4)",
        "",
        f"| prefer | prize | preserve | pool>repack_sum |",
        f"|--------|-------|----------|-----------------|",
        f"| {base['prefer']} | {base['prize']} | {base['preserve']} | {base['pool_gt_repack_sum']} |",
        "",
        "## cands",
        "",
    ]
    for name, row in by_cfg.items():
        if name.startswith("base"):
            continue
        g = row.get("gate") or {}
        lines.append(
            f"- `{name}` s{row['slots']}/c{row['cap']}: "
            f"Δpref={g.get('d_prefer')} Δprize={g.get('d_prize')} "
            f"Δpres={g.get('d_preserve')} Δloss={g.get('d_loss_sum')} "
            f"pass={g.get('pass')}"
        )
    lines += [
        "",
        f"best: `{best}`" if best else "best: null",
        "",
        f"판정: **{verdict}** — {next_note}",
        "",
        f"벤치: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"status": verdict, "best": best, "winners": len(winners)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
