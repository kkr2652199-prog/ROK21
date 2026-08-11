# -*- coding: utf-8 -*-
"""K-REPACK-UNION-GATE — P1/P2 signal_union 게이트 (repack 세트 축).

base=signal_top(slots2) · cand=signal_union(slots2·cap4).
축(발권 repack nums · ge3미사용):
  markov prefer = repack번호 fw평균 − 전체평균 (비악화)
  review prize  = 동상 (더음수 또는 비악화)
  stat hit      = repack best |∩actual|/6 (base−0.01 이상)
부가 모니터: pool>repack 횟수 감소 (클레임 아님).
통과 시 ASSEMBLE_MODE=signal_union 유지 · 실패 시 signal_top 롤백.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KREPACK_UNION_GATE.json"
OUT_MD = ROOT / "reports" / "20260811_KREPACK_UNION_GATE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80
STAT_SLACK = 0.01
ABS_THR = 0.005


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _set_mode(sp: Any, mode: str) -> None:
    sp.ASSEMBLE_MODE = mode


def _run(seed: int, mode: str) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy

    saved = sp.ASSEMBLE_MODE
    _set_mode(sp, mode)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer: list[float] = []
        prize: list[float] = []
        hits: list[float] = []
        loss = Counter()
        win = Counter()
        tie = Counter()
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
                by.setdefault(r["brain_tag"], []).append([int(x) for x in r["nums"]])
            act = _actual(dno)
            # pool best vs repack best (모니터)
            for tag in sp.BRAIN_TAGS:
                psets = [
                    [int(x) for x in c["nums"]]
                    for c in pool_br.get(tag, [])
                ]
                rsets = by.get(tag) or []
                if not psets or not rsets:
                    continue
                ph = max(len(set(s) & act) for s in psets)
                rh = max(len(set(s) & act) for s in rsets)
                if ph > rh:
                    loss[tag] += 1
                elif rh > ph:
                    win[tag] += 1
                else:
                    tie[tag] += 1
            mnums = [n for s in by.get("markov", []) for n in s]
            rnums = [n for s in by.get("review", []) for n in s]
            if mnums:
                prefer.append(mean(fw[n] for n in mnums) - all_mean)
            if rnums:
                prize.append(mean(fw[n] for n in rnums) - all_mean)
            ssets = by.get("stat") or []
            if ssets:
                hits.append(max(len(set(s) & act) for s in ssets) / 6.0)
            learner.update_from_pool(pool_br, act)
        return {
            "seed": seed,
            "mode": mode,
            "n": len(prefer),
            "prefer": round(mean(prefer), 6) if prefer else None,
            "prize": round(mean(prize), 6) if prize else None,
            "stat_hit": round(mean(hits), 6) if hits else None,
            "pool_gt_repack": dict(loss),
            "repack_gt_pool": dict(win),
            "tie": dict(tie),
        }
    finally:
        _set_mode(sp, saved)


def _agg(name: str, by: list[dict[str, Any]], base: dict[str, float] | None) -> dict[str, Any]:
    prefer = mean(d["prefer"] for d in by if d["prefer"] is not None)
    prize = mean(d["prize"] for d in by if d["prize"] is not None)
    hit = mean(d["stat_hit"] for d in by if d["stat_hit"] is not None)
    loss_sum = {
        t: int(mean(d["pool_gt_repack"].get(t, 0) for d in by))
        for t in ("stat", "markov", "review")
    }
    if base is None:
        return {
            "name": name,
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "stat_hit": round(hit, 6),
            "pool_gt_repack_mean": loss_sum,
            "gate_pass": True,
            "gate_detail": {"is_baseline": True},
            "per_seed": by,
        }
    dpref = prefer - base["prefer"]
    dprize = prize - base["prize"]
    dhit = hit - base["stat_hit"]
    loss_base = base["pool_gt_repack_mean"]
    loss_improve = sum(loss_sum[t] for t in loss_sum) < sum(loss_base[t] for t in loss_base)
    cond = {
        "prefer_ge": prefer >= base["prefer"] - 1e-12,
        "prize_le": prize <= base["prize"] + 1e-12,
        "stat_ok": hit >= base["stat_hit"] - STAT_SLACK,
        "loss_improve": loss_improve,
        "abs_or_loss": abs(dpref) >= ABS_THR or abs(dprize) >= ABS_THR or loss_improve,
        "dprefer": round(dpref, 6),
        "dprize": round(dprize, 6),
        "dhit": round(dhit, 6),
        "is_baseline": False,
    }
    # 통과: 축 비악화 + (실질이동 또는 손실모니터 개선)
    gate = bool(
        cond["prefer_ge"]
        and cond["prize_le"]
        and cond["stat_ok"]
        and cond["abs_or_loss"]
    )
    return {
        "name": name,
        "prefer": round(prefer, 6),
        "prize": round(prize, 6),
        "stat_hit": round(hit, 6),
        "pool_gt_repack_mean": loss_sum,
        "gate_pass": gate,
        "gate_detail": cond,
        "per_seed": by,
    }


def _apply_or_rollback(pass_: bool) -> str:
    import app.testlotto.signal_pool as sp

    path = ROOT / "app" / "testlotto" / "signal_pool.py"
    text = path.read_text(encoding="utf-8")
    target = "signal_union" if pass_ else "signal_top"
    old = (
        'ASSEMBLE_MODE: str = "signal_union"'
        if 'ASSEMBLE_MODE: str = "signal_union"' in text
        else 'ASSEMBLE_MODE: str = "signal_top"'
    )
    new = f'ASSEMBLE_MODE: str = "{target}"'
    if old in text and old != new:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
    sp.ASSEMBLE_MODE = target
    return target


def main() -> None:
    import app.testlotto.signal_pool as sp

    base_rows = [_run(s, "signal_top") for s in SEEDS]
    cand_rows = [_run(s, "signal_union") for s in SEEDS]
    base = _agg("signal_top", base_rows, None)
    cand = _agg(
        "signal_union",
        cand_rows,
        {
            "prefer": base["prefer"],
            "prize": base["prize"],
            "stat_hit": base["stat_hit"],
            "pool_gt_repack_mean": base["pool_gt_repack_mean"],
        },
    )
    applied = _apply_or_rollback(bool(cand["gate_pass"]))
    result = {
        "id": "K-REPACK-UNION-GATE",
        "ts": _now(),
        "range": [LO, HI],
        "seeds": SEEDS,
        "live_before": getattr(sp, "ASSEMBLE_MODE", None),
        "cand_params": {
            "ASSEMBLE_MODE": "signal_union",
            "POOL_SLOTS": 2,
            "POOL_UNION_CAP": 4,
        },
        "base": base,
        "cand": cand,
        "verdict": "APPLY" if cand["gate_pass"] else "ROLLBACK_HOLD",
        "applied_mode": applied,
        "ge3_used_as_claim": False,
        "note": "P1/P2 union · repack축 게이트 · 1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-REPACK-UNION-GATE — P1/P2 signal_union",
        "",
        f"시각: {result['ts']} · {LO}~{HI} · seeds={SEEDS}",
        "",
        f"## 판정 **{result['verdict']}** · applied=`{applied}`",
        f"- ge3클레임금지 · 1237아님",
        "",
        "| mode | prefer | prize | stat_hit | pool>repack | gate |",
        "|------|--------|-------|----------|-------------|------|",
        (
            f"| signal_top | {base['prefer']} | {base['prize']} | {base['stat_hit']} | "
            f"{base['pool_gt_repack_mean']} | base |"
        ),
        (
            f"| signal_union | {cand['prefer']} | {cand['prize']} | {cand['stat_hit']} | "
            f"{cand['pool_gt_repack_mean']} | {cand['gate_pass']} |"
        ),
        "",
        f"## gate_detail `{cand['gate_detail']}`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print("VERDICT", result["verdict"], "applied", applied)
    print("base", base["prefer"], base["prize"], base["stat_hit"], base["pool_gt_repack_mean"])
    print("cand", cand["prefer"], cand["prize"], cand["stat_hit"], cand["pool_gt_repack_mean"], cand["gate_pass"])
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
