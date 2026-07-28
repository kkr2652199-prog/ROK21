# -*- coding: utf-8 -*-
"""K-POS-TRACE — 정렬 자리1~6 + 보너스 회차→다음회 전이 (READ-ONLY).

산출: docs/benchmarks/20260729_KPOS_trace.json
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KPOS_trace.json"


def load_draws(con: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = con.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6, bonus
        FROM lotto_draws
        WHERE draw_no BETWEEN 1 AND 1234
        ORDER BY draw_no
        """
    ).fetchall()
    out = []
    for r in rows:
        nums = sorted(int(r[i]) for i in range(1, 7))
        out.append(
            {
                "draw": int(r[0]),
                "pos": nums,  # 0..5 = 자리1..6
                "bonus": int(r[7]),
            }
        )
    return out


def theoretical_pos_pmf() -> list[dict[int, float]]:
    """P(X_(k)=x) for k=1..6, x=1..45 under uniform C(45,6)."""
    den = math.comb(45, 6)
    pmfs: list[dict[int, float]] = []
    for k in range(1, 7):
        d: dict[int, float] = {}
        for x in range(1, 46):
            a = k - 1
            b = 6 - k
            if x - 1 < a or 45 - x < b:
                d[x] = 0.0
                continue
            d[x] = math.comb(x - 1, a) * math.comb(45 - x, b) / den
        pmfs.append(d)
    return pmfs


def chi2_uniform_rows(counts: dict[int, Counter], support: range) -> dict[str, Any]:
    """Per from-state row: chi2 vs uniform over observed next support (descriptive)."""
    # Better: for each position, flatten all transitions and compare next marginal to theory
    return {}


def analyze_window(draws: list[dict], lo: int, hi: int, n_mc: int = 2000) -> dict[str, Any]:
    seq = [d for d in draws if lo <= d["draw"] <= hi]
    seq.sort(key=lambda d: d["draw"])
    # transitions only consecutive draw_no
    by_no = {d["draw"]: d for d in seq}
    pairs = []
    for d in seq:
        nxt = by_no.get(d["draw"] + 1)
        if nxt and nxt["draw"] <= hi:
            pairs.append((d, nxt))

    # position k: Counter of (from -> to)
    trans: list[Counter] = [Counter() for _ in range(6)]
    next_marg: list[Counter] = [Counter() for _ in range(6)]
    from_marg: list[Counter] = [Counter() for _ in range(6)]
    bonus_trans: Counter = Counter()
    bonus_next: Counter = Counter()

    for a, b in pairs:
        for k in range(6):
            fr, to = a["pos"][k], b["pos"][k]
            trans[k][(fr, to)] += 1
            from_marg[k][fr] += 1
            next_marg[k][to] += 1
        bonus_trans[(a["bonus"], b["bonus"])] += 1
        bonus_next[b["bonus"]] += 1

    theory = theoretical_pos_pmf()
    # chi2 of next marginal vs theory for each position
    pos_fit = []
    for k in range(6):
        n = sum(next_marg[k].values())
        if n == 0:
            pos_fit.append({"pos": k + 1, "n": 0})
            continue
        chi2 = 0.0
        used = 0
        for x, p in theory[k].items():
            exp = p * n
            if exp < 5:
                continue
            obs = next_marg[k].get(x, 0)
            chi2 += (obs - exp) ** 2 / exp
            used += 1
        # top sticky: same number stays in same position
        sticky = sum(c for (fr, to), c in trans[k].items() if fr == to)
        # top transitions
        top = trans[k].most_common(8)
        pos_fit.append(
            {
                "pos": k + 1,
                "n_transitions": n,
                "chi2_vs_theory_marginal": round(chi2, 2),
                "chi2_bins_exp_ge5": used,
                "sticky_same_number_rate": round(sticky / n, 4) if n else 0,
                "top_transitions": [
                    {"from": fr, "to": to, "n": c} for (fr, to), c in top
                ],
                "next_mean": round(
                    sum(x * c for x, c in next_marg[k].items()) / n, 2
                )
                if n
                else 0,
                "theory_mean": round(sum(x * p for x, p in theory[k].items()), 2),
            }
        )

    # MC null: independent redraws — sticky rate distribution
    rng = random.Random(42 + lo)
    sticky_mc = [[] for _ in range(6)]
    for _ in range(n_mc):
        # sample two independent draws
        def sample_draw():
            return sorted(rng.sample(range(1, 46), 6))

        for _rep in range(50):  # batch inside to speed? actually just one pair per trial
            pass
        a = sample_draw()
        b = sample_draw()
        for k in range(6):
            sticky_mc[k].append(1 if a[k] == b[k] else 0)
    sticky_null = []
    for k in range(6):
        rate = sum(sticky_mc[k]) / len(sticky_mc[k])
        sticky_null.append({"pos": k + 1, "null_sticky_rate_mc": round(rate, 4)})

    # allow-range check: illegal positions count (should be 0)
    illegal = 0
    for d in seq:
        for k, x in enumerate(d["pos"]):
            # min for pos k+1 is k+1, max is 45-(6-k-1)=40+k
            lo_x, hi_x = k + 1, 40 + k
            if not (lo_x <= x <= hi_x):
                illegal += 1

    return {
        "range": [lo, hi],
        "n_draws": len(seq),
        "n_transition_pairs": len(pairs),
        "illegal_sorted_positions": illegal,
        "positions": pos_fit,
        "sticky_null_mc": sticky_null,
        "bonus": {
            "n": sum(bonus_next.values()),
            "top_transitions": [
                {"from": a, "to": b, "n": c}
                for (a, b), c in bonus_trans.most_common(8)
            ],
            "sticky_rate": round(
                sum(c for (a, b), c in bonus_trans.items() if a == b)
                / max(1, sum(bonus_trans.values())),
                4,
            ),
        },
    }


def main() -> None:
    con = sqlite3.connect(DB)
    draws = load_draws(con)
    con.close()

    windows = {
        "full_2_1234": analyze_window(draws, 2, 1234, n_mc=3000),
        "recent_200": analyze_window(draws, 1035, 1234, n_mc=2000),
        "recent_100": analyze_window(draws, 1135, 1234, n_mc=2000),
    }

    # verdict: compare sticky vs null
    full = windows["full_2_1234"]
    sticky_vs_null = []
    for p, ninfo in zip(full["positions"], full["sticky_null_mc"]):
        sticky_vs_null.append(
            {
                "pos": p["pos"],
                "obs_sticky": p["sticky_same_number_rate"],
                "null_sticky": ninfo["null_sticky_rate_mc"],
                "delta": round(
                    p["sticky_same_number_rate"] - ninfo["null_sticky_rate_mc"], 4
                ),
            }
        )

    payload = {
        "id": "K-POS-TRACE",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "definition": {
            "position": "sorted ascending nums → seat 1..6",
            "transition": "draw t seat k value → draw t+1 seat k value",
            "bonus": "separate chain",
            "note": "descriptive + null-check · not a jackpot claim",
        },
        "windows": windows,
        "sticky_vs_null_full": sticky_vs_null,
        "interpretation": [
            "자리 허용범위(정렬) 위반 0이어야 정상",
            "sticky≈null 이면 자리 고정 번호 관성 없음",
            "chi2는 다음자리 주변분포 vs 순서통계 이론 — 크면 표본/편향 점검",
            "몰아주기 입력: 자리별 허용구간 + (유의한 전이만) 가중 후보 — 전역 예측 레버 아님",
        ],
        "next": "K-SCATTER-1",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print("illegal", full["illegal_sorted_positions"], "pairs", full["n_transition_pairs"])
    for row in sticky_vs_null:
        print("sticky", row)
    for p in full["positions"]:
        print(
            f"pos{p['pos']} chi2={p['chi2_vs_theory_marginal']} "
            f"mean={p['next_mean']} th={p['theory_mean']} sticky={p['sticky_same_number_rate']}"
        )


if __name__ == "__main__":
    main()
