# -*- coding: utf-8 -*-
"""K-TICKET-COVER-LITE — LIST_V3 L10.

발권5(dedup 이후 quota 선별) Jaccard/번호커버 소형 스윕.
부분당첨 기회 분산 · buy-the-pot 금지 · ge3 미클레임 · 1237아님.
게이트 PASS 시에만 TICKET_COVER_* 상수 APPLY.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KTICKET_COVER_LITE.json"
OUT_MD = ROOT / "reports" / "20260812_KTICKET_COVER_LITE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
# (name, enabled, penalty)
CONFIGS: list[tuple[str, bool, float]] = [
    ("base_off", False, 0.0),
    ("cover_p0.5", True, 0.5),
    ("cover_p1.0", True, 1.0),
    ("cover_p1.5", True, 1.5),
    ("cover_p2.0", True, 2.0),
]
PREF_EPS = 0.005
PRIZE_EPS = 0.005
JACCARD_DELTA = 0.015  # mean pairwise ↓
UNION_DELTA = 0.5  # unique nums ↑


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _pair_jaccard(sets: list[list[int]]) -> float:
    from app.testlotto.set_diversity import avg_pairwise_jaccard

    return float(avg_pairwise_jaccard(sets))


def _union_n(sets: list[list[int]]) -> float:
    u: set[int] = set()
    for s in sets:
        u |= set(int(x) for x in s)
    return float(len(u))


def _gen_scored(dno: int) -> list[dict]:
    from app.testlotto.brains.coordinator import (
        BRAIN_RNG_SEED_BASE,
        PREDICT_MODULES,
        PREDICT_TAGS,
        _apply_aux_scoring,
        _seed_independent_brain,
    )
    from app.testlotto.brains.registry import PREDICT_BRAINS, SETS_PER_PREDICT_BRAIN
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.ticket_dedup import dedup_enabled, dedup_ticket_list

    set_learn_as_of(int(dno))
    draws = _get_draws_before(int(dno))
    if len(draws) < 50:
        return []
    cands: list[dict] = []
    for brain in PREDICT_BRAINS:
        tag = brain["tag"]
        if tag not in PREDICT_TAGS:
            continue
        _seed_independent_brain(dno)
        try:
            sets = PREDICT_MODULES[tag].predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        except Exception:
            continue
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            cands.append({**s, "pred_set_no": sn, "set_no": sn, "brain_tag": tag})
    if not cands:
        return []
    scored = _apply_aux_scoring(cands, draws, dno)
    if dedup_enabled():

        def _regen(brain_tag: str, seen: set, replace_of=None):
            mod = PREDICT_MODULES.get(brain_tag)
            if mod is None:
                return None
            _seed_independent_brain(dno)
            try:
                raw = mod.predict_sets(draws, 1)
            except Exception:
                return None
            if not raw:
                return None
            row = {**raw[0], "brain_tag": brain_tag}
            return _apply_aux_scoring([row], draws, dno)[0]

        scored, _ = dedup_ticket_list(scored, regenerate=_regen)
    return scored


def _select(scored: list[dict], enabled: bool, pen: float) -> list[dict]:
    import app.testlotto.brains.coordinator as coord

    old_on = coord.TICKET_COVER_LITE
    old_pen = coord.TICKET_COVER_JACCARD_PENALTY
    coord.TICKET_COVER_LITE = bool(enabled)
    coord.TICKET_COVER_JACCARD_PENALTY = float(pen)
    try:
        return coord.dynamic_brain_quota(list(scored))
    finally:
        coord.TICKET_COVER_LITE = old_on
        coord.TICKET_COVER_JACCARD_PENALTY = old_pen


def _run_seed(seed: int) -> dict[str, dict[str, Any]]:
    from tools._k_brain_independent_tune import _actual, _fw_proxy
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    random.seed(seed)
    # per-config accumulators
    acc: dict[str, dict[str, list]] = {
        name: {
            "prefer": [],
            "prize": [],
            "jaccard": [],
            "union": [],
            "best_hits": [],
            "hit_union": [],
        }
        for name, _, _ in CONFIGS
    }
    n_ok = 0
    for dno in range(LO, HI + 1):
        random.seed(seed + dno)
        scored = _gen_scored(dno)
        if len(scored) < 5:
            continue
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        fw = _fw_proxy(draws)
        all_mean = mean(fw[n] for n in range(1, 46))
        if all_mean <= 1e-12:
            continue
        act = _actual(dno)
        for name, enabled, pen in CONFIGS:
            picked = _select(scored, enabled, pen)
            if len(picked) != 5:
                continue
            sets = [[int(x) for x in c["nums"]] for c in picked]
            acc[name]["jaccard"].append(_pair_jaccard(sets))
            acc[name]["union"].append(_union_n(sets))
            mnums = [
                n
                for c in picked
                if str(c.get("brain_tag")) == "markov"
                for n in c["nums"]
            ]
            rnums = [
                n
                for c in picked
                if str(c.get("brain_tag")) == "review"
                for n in c["nums"]
            ]
            if mnums:
                acc[name]["prefer"].append(mean(fw[int(n)] for n in mnums) - all_mean)
            if rnums:
                acc[name]["prize"].append(mean(fw[int(n)] for n in rnums) - all_mean)
            best_h = max(len(set(s) & act) for s in sets)
            acc[name]["best_hits"].append(float(best_h))
            hit_u = set()
            for s in sets:
                hit_u |= set(s) & act
            acc[name]["hit_union"].append(float(len(hit_u)))
        n_ok += 1
        if n_ok % 20 == 0:
            print(f"  seed={seed} n={n_ok} draw={dno}", flush=True)

    out: dict[str, dict[str, Any]] = {}
    for name, _, _ in CONFIGS:
        a = acc[name]
        out[name] = {
            "seed": seed,
            "n": n_ok,
            "prefer": round(mean(a["prefer"]), 6) if a["prefer"] else None,
            "prize": round(mean(a["prize"]), 6) if a["prize"] else None,
            "mean_jaccard": round(mean(a["jaccard"]), 6) if a["jaccard"] else None,
            "mean_union": round(mean(a["union"]), 4) if a["union"] else None,
            "mean_best_hits_monitor": round(mean(a["best_hits"]), 4)
            if a["best_hits"]
            else None,
            "mean_hit_union_monitor": round(mean(a["hit_union"]), 4)
            if a["hit_union"]
            else None,
        }
    return out


def _agg(per_seed: list[dict[str, Any]]) -> dict[str, Any]:
    def avg(key: str):
        vals = [r[key] for r in per_seed if r.get(key) is not None]
        return round(mean(vals), 6) if vals else None

    return {
        "prefer": avg("prefer"),
        "prize": avg("prize"),
        "mean_jaccard": avg("mean_jaccard"),
        "mean_union": avg("mean_union"),
        "mean_best_hits_monitor": avg("mean_best_hits_monitor"),
        "mean_hit_union_monitor": avg("mean_hit_union_monitor"),
        "per_seed": per_seed,
    }


def main() -> int:
    import app.testlotto.brains.coordinator as coord

    live = {
        "TICKET_COVER_LITE": bool(coord.TICKET_COVER_LITE),
        "TICKET_COVER_JACCARD_PENALTY": float(coord.TICKET_COVER_JACCARD_PENALTY),
        "QUOTA_ADAPTIVE_MIN_EACH": int(coord.QUOTA_ADAPTIVE_MIN_EACH),
        "MARKOV_WIRE_ENABLED": bool(coord.MARKOV_WIRE_ENABLED),
    }

    # seed → cfg → metrics, then pivot
    seed_tables: list[dict[str, dict[str, Any]]] = []
    for s in SEEDS:
        print(f"== seed {s} ==", flush=True)
        seed_tables.append(_run_seed(s))

    by_cfg: dict[str, dict[str, Any]] = {}
    for name, enabled, pen in CONFIGS:
        runs = [st[name] for st in seed_tables]
        by_cfg[name] = {
            "enabled": enabled,
            "penalty": pen,
            **_agg(runs),
        }

    base = by_cfg["base_off"]
    winners: list[dict[str, Any]] = []
    for name, row in by_cfg.items():
        if name == "base_off":
            continue
        d_pref = (row["prefer"] or 0) - (base["prefer"] or 0)
        d_prize = (row["prize"] or 0) - (base["prize"] or 0)
        d_j = (base["mean_jaccard"] or 0) - (row["mean_jaccard"] or 0)  # + = better
        d_u = (row["mean_union"] or 0) - (base["mean_union"] or 0)
        health = (row["prefer"] or 0) > 0 and (row["prize"] or 0) < 0
        non_worse = d_pref >= -PREF_EPS and d_prize <= PRIZE_EPS
        signal = d_j >= JACCARD_DELTA or d_u >= UNION_DELTA
        ok = health and non_worse and signal
        detail = {
            "name": name,
            "penalty": row["penalty"],
            "d_prefer": round(d_pref, 6),
            "d_prize": round(d_prize, 6),
            "d_jaccard": round(d_j, 6),
            "d_union": round(d_u, 4),
            "health": health,
            "non_worse": non_worse,
            "signal": signal,
            "pass": ok,
        }
        by_cfg[name]["gate"] = detail
        if ok:
            winners.append(detail)

    apply = False
    if winners:
        best = max(winners, key=lambda w: (w["d_jaccard"], w["d_union"], w["d_prefer"]))
        verdict = "APPLY_OK"
        apply = True
        # APPLY constants
        coord_path = ROOT / "app" / "testlotto" / "brains" / "coordinator.py"
        src = coord_path.read_text(encoding="utf-8")
        src2 = src.replace(
            "TICKET_COVER_LITE: bool = False",
            "TICKET_COVER_LITE: bool = True",
            1,
        )
        # replace default penalty line
        import re

        src2, npen = re.subn(
            r"TICKET_COVER_JACCARD_PENALTY: float = [0-9.]+",
            f"TICKET_COVER_JACCARD_PENALTY: float = {best['penalty']}",
            src2,
            count=1,
        )
        if "TICKET_COVER_LITE: bool = True" not in src2 or npen != 1:
            raise SystemExit("APPLY patch failed")
        coord_path.write_text(src2, encoding="utf-8")
        coord.TICKET_COVER_LITE = True
        coord.TICKET_COVER_JACCARD_PENALTY = float(best["penalty"])
        next_note = (
            f"APPLY cover pen={best['penalty']} · j↓{best['d_jaccard']} · "
            f"union↑{best['d_union']} · 다음 L11"
        )
    else:
        best = None
        verdict = "HOLD"
        next_note = "신호없음 HOLD · TICKET_COVER_LITE=False 유지 · 다음 L11"

    payload = {
        "id": "K-TICKET-COVER-LITE",
        "list": "LIST_V3",
        "step": "L10",
        "status": verdict,
        "ts": _now(),
        "wire": bool(apply),
        "apply": bool(apply),
        "ge3_used_as_claim": False,
        "buy_the_pot": False,
        "range": [LO, HI],
        "seeds": SEEDS,
        "live_before": live,
        "live_after": {
            "TICKET_COVER_LITE": bool(coord.TICKET_COVER_LITE),
            "TICKET_COVER_JACCARD_PENALTY": float(coord.TICKET_COVER_JACCARD_PENALTY),
        },
        "configs": by_cfg,
        "base": "base_off",
        "winners": winners,
        "best": best,
        "thresholds": {
            "PREF_EPS": PREF_EPS,
            "PRIZE_EPS": PRIZE_EPS,
            "JACCARD_DELTA": JACCARD_DELTA,
            "UNION_DELTA": UNION_DELTA,
        },
        "next": {"step": "L11", "id": "K-AXIS-DEEPEN-REST"},
        "force_bt": False,
        "s1": False,
        "note": next_note + " · 1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# K-TICKET-COVER-LITE — LIST_V3 L10",
        "",
        f"시각: {payload['ts']} · **{verdict}** · apply=**{apply}** · **1237아님** · ge3미클레임 · buy-the-pot금지",
        f"구간: {LO}~{HI} seeds={SEEDS} · 발권경로(dedup→quota)",
        f"다음: **L11** 축 심화 잔여",
        "",
        "## base (COVER off)",
        "",
        "| prefer | prize | mean_J | mean_union | best_hits(모니터) |",
        "|--------|-------|--------|------------|-------------------|",
        f"| {base['prefer']} | {base['prize']} | {base['mean_jaccard']} | {base['mean_union']} | {base['mean_best_hits_monitor']} |",
        "",
        "## cands",
        "",
    ]
    for name, row in by_cfg.items():
        if name == "base_off":
            continue
        g = row.get("gate") or {}
        lines.append(
            f"- `{name}` pen={row['penalty']}: J={row['mean_jaccard']} union={row['mean_union']} "
            f"prefer={row['prefer']} prize={row['prize']} · "
            f"dJ={g.get('d_jaccard')} dU={g.get('d_union')} · pass=**{g.get('pass')}**"
        )
    lines += [
        "",
        f"판정: **{verdict}** — {next_note}",
        "",
        f"벤치: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        f"도구: `tools/_k_ticket_cover_lite.py`",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "apply": apply, "best": best}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
