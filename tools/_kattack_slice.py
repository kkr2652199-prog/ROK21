# -*- coding: utf-8 -*-
"""K-ATTACK-SLICE — LMH 구간 구조로 5세트 중 승격 정책 비교 (READ-ONLY).

정책:
  baseline     — DB best_set (현행)
  oracle_zone  — 실제 당첨 LMH와 가장 가까운 세트 (치트 천장)
  prev_zone    — 직전회 LMH에 가장 가까운 세트 (맹목)
  bal_222      — 2:2:2에 가장 가까운 세트 (맹목·명분)
  recent20_mode— 최근20회 LMH 최빈값에 가까운 세트 (맹목)

산출: docs/benchmarks/20260729_KATTACK_slice.json
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KATTACK_slice.json"


def lmh(nums: list[int]) -> tuple[int, int, int]:
    l = sum(1 for n in nums if 1 <= n <= 15)
    m = sum(1 for n in nums if 16 <= n <= 30)
    h = sum(1 for n in nums if 31 <= n <= 45)
    return l, m, h


def lmh_dist(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def oe(nums: list[int]) -> tuple[int, int]:
    o = sum(1 for n in nums if n % 2)
    return o, len(nums) - o


def pick_closest(sets: list[dict], target: tuple[int, int, int]) -> dict:
    best = None
    best_d = 99
    for s in sets:
        d = lmh_dist(lmh(s["nums"]), target)
        if d < best_d or (
            d == best_d
            and best is not None
            and s.get("confidence", 0) > best.get("confidence", 0)
        ):
            best_d = d
            best = s
        elif best is None:
            best = s
            best_d = d
    return best or sets[0]


def summarize(ms: list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {"n": 0}
    return {
        "n": n,
        "mean": round(sum(ms) / n, 4),
        "ge3": sum(1 for x in ms if x >= 3),
        "ge3_rate": round(sum(1 for x in ms if x >= 3) / n, 4),
        "ge4": sum(1 for x in ms if x >= 4),
        "ge4_rate": round(sum(1 for x in ms if x >= 4) / n, 4),
        "ge5": sum(1 for x in ms if x >= 5),
        "ge6": sum(1 for x in ms if x >= 6),
    }


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    draws = con.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN 1 AND 1234 ORDER BY draw_no"
    ).fetchall()
    actuals = {
        int(r[0]): sorted(int(r[i]) for i in range(1, 7)) for r in draws
    }
    prev_lmh = {}
    hist_lmh = []
    for dno in sorted(actuals):
        z = lmh(actuals[dno])
        if hist_lmh:
            prev_lmh[dno] = hist_lmh[-1]
        hist_lmh.append(z)

    # recent20 mode per draw
    recent_mode = {}
    buf: list[tuple[int, int, int]] = []
    for dno in sorted(actuals):
        if len(buf) >= 1:
            recent_mode[dno] = Counter(buf[-20:]).most_common(1)[0][0]
        buf.append(lmh(actuals[dno]))

    rows = con.execute(
        "SELECT draw_no, brain_tag, predicted_sets_json, best_set_no, matched_count "
        "FROM testlotto_brain_review WHERE draw_no BETWEEN 2 AND 1234"
    ).fetchall()
    con.close()

    policies = ["baseline", "oracle_zone", "prev_zone", "bal_222", "recent20_mode"]
    by_pol: dict[str, dict[str, list[int]]] = {
        p: defaultdict(list) for p in policies
    }
    # also zone_match rate of chosen set vs actual
    zone_hit: dict[str, dict[str, list[int]]] = {
        p: defaultdict(list) for p in policies
    }

    for r in rows:
        d = int(r["draw_no"])
        tag = r["brain_tag"]
        act = actuals.get(d)
        if not act:
            continue
        act_z = lmh(act)
        try:
            raw = json.loads(r["predicted_sets_json"] or "[]")
        except Exception:
            continue
        sets = []
        for s in raw:
            nums = [int(x) for x in (s.get("nums") or [])]
            if len(nums) != 6:
                continue
            sets.append(
                {
                    "nums": nums,
                    "set_no": int(s.get("set_no") or 0),
                    "confidence": float(s.get("confidence") or 0),
                    "matched": int(s.get("matched_count") or len(set(nums) & set(act))),
                }
            )
        if len(sets) < 3:
            continue

        chosen = {}
        # baseline
        bsn = int(r["best_set_no"] or 1)
        base = next((s for s in sets if s["set_no"] == bsn), sets[0])
        chosen["baseline"] = base
        chosen["oracle_zone"] = pick_closest(sets, act_z)
        if d in prev_lmh:
            chosen["prev_zone"] = pick_closest(sets, prev_lmh[d])
        else:
            chosen["prev_zone"] = base
        chosen["bal_222"] = pick_closest(sets, (2, 2, 2))
        if d in recent_mode:
            chosen["recent20_mode"] = pick_closest(sets, recent_mode[d])
        else:
            chosen["recent20_mode"] = base

        for pol, s in chosen.items():
            m = len(set(s["nums"]) & set(act))
            by_pol[pol][tag].append(m)
            zone_hit[pol][tag].append(1 if lmh(s["nums"]) == act_z else 0)

    results = {}
    for pol in policies:
        results[pol] = {
            "all": summarize([m for tag in by_pol[pol] for m in by_pol[pol][tag]]),
            "by_brain": {tag: summarize(ms) for tag, ms in sorted(by_pol[pol].items())},
            "zone_match_rate_all": round(
                sum(x for tag in zone_hit[pol] for x in zone_hit[pol][tag])
                / max(1, sum(len(zone_hit[pol][tag]) for tag in zone_hit[pol])),
                4,
            ),
        }

    base_all = results["baseline"]["all"]
    deltas = {
        pol: {
            "mean_delta": round(
                results[pol]["all"]["mean"] - base_all["mean"], 4
            ),
            "ge3_rate_delta": round(
                results[pol]["all"]["ge3_rate"] - base_all["ge3_rate"], 4
            ),
            "ge4_rate_delta": round(
                results[pol]["all"]["ge4_rate"] - base_all["ge4_rate"], 4
            ),
        }
        for pol in policies
        if pol != "baseline"
    }

    # AI extras: oracle OE+zone combined
    # already have oracle_zone; note ceiling
    blind_best = max(
        (p for p in ("prev_zone", "bal_222", "recent20_mode")),
        key=lambda p: (results[p]["all"]["mean"], results[p]["all"]["ge4_rate"]),
    )

    payload = {
        "id": "K-ATTACK-SLICE",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "window": [2, 1234],
        "pattern1_ref": {
            "tier4_zone_match": 0.3548,
            "control_zone_match": 0.05,
        },
        "policies": results,
        "deltas_vs_baseline": deltas,
        "verdict": {
            "oracle_ceiling_mean": results["oracle_zone"]["all"]["mean"],
            "best_blind_policy": blind_best,
            "best_blind_mean": results[blind_best]["all"]["mean"],
            "baseline_mean": base_all["mean"],
            "promote_wire": bool(
                results[blind_best]["all"]["mean"] >= base_all["mean"] + 0.02
                or results[blind_best]["all"]["ge4_rate"]
                >= base_all["ge4_rate"] + 0.003
            ),
        },
        "hyung_idea_note": (
            "뇌내 몰아주기=기회 실측·선별난제(관측고정). "
            "구간 승격=PATTERN-1 신호의 사전 적용 시도."
        ),
        "ai_ideas_applied": [
            "oracle zone ceiling vs blind policies",
            "prev-draw LMH carry (structure Markov without claiming ball prediction)",
            "2:2:2 balance warrant alignment",
            "recent20 empirical mode",
        ],
    }
    if payload["verdict"]["promote_wire"]:
        payload["next"] = "K-ATTACK-SLICE-WIRE 형GO — 맹목 정책 승격 배선"
    else:
        payload["next"] = (
            "SLICE 관측유지 · NEXT=K-ATTACK-BAYES(3뇌 동적가중) 또는 K-AWAIT 대기"
        )

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    for pol in policies:
        a = results[pol]["all"]
        print(
            pol,
            "mean",
            a["mean"],
            "ge3",
            a["ge3_rate"],
            "ge4",
            a["ge4_rate"],
            "zone%",
            results[pol]["zone_match_rate_all"],
        )
    print("deltas", deltas)
    print("verdict", payload["verdict"], "->", payload["next"])


if __name__ == "__main__":
    main()
