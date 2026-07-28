# -*- coding: utf-8 -*-
"""K-ATTACK-COVER — 정직 1등 확률 · 15장 커버 효율 (READ-ONLY 1차).

산출: docs/benchmarks/20260729_KATTACK_cover.json
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KATTACK_cover.json"

C45_6 = math.comb(45, 6)  # 8_145_060
P1 = 1.0 / C45_6


def p_at_least_one_first(n_tickets: int, n_draws: int) -> float:
    """Independent draws · n distinct random tickets/draw (approx if tickets unique)."""
    # P(miss one draw) ≈ (1-p)^n for n random tickets (with replacement approx ok for n<<C)
    miss1 = (1.0 - P1) ** n_tickets
    hit1 = 1.0 - miss1
    miss_all = (1.0 - hit1) ** n_draws
    return 1.0 - miss_all


def expected_draws_to_first(n_tickets: int) -> float:
    hit1 = 1.0 - (1.0 - P1) ** n_tickets
    if hit1 <= 0:
        return float("inf")
    return 1.0 / hit1


def mc_pool_ge(k: int, n_sets: int, trials: int = 3000, seed: int = 7) -> dict:
    rng = random.Random(seed + k * 17 + n_sets)
    hit = 0
    bests = []
    for _ in range(trials):
        actual = set(rng.sample(range(1, 46), 6))
        best = 0
        for _s in range(n_sets):
            pred = set(rng.sample(range(1, 46), 6))
            best = max(best, len(pred & actual))
        bests.append(best)
        if best >= k:
            hit += 1
    return {
        "n_sets": n_sets,
        "k": k,
        "trials": trials,
        "rate_best_ge_k": round(hit / trials, 4),
        "best_mean": round(sum(bests) / len(bests), 4),
    }


def observed_pool_from_db() -> dict:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT draw_no, brain_tag, predicted_sets_json
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN 2 AND 1234
        """
    ).fetchall()
    actuals = {
        int(r[0]): set(int(r[i]) for i in range(1, 7))
        for r in con.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no BETWEEN 2 AND 1234"
        )
    }
    by_draw: dict[int, list] = {}
    for r in rows:
        by_draw.setdefault(int(r["draw_no"]), []).append(r)

    ge3 = ge4 = ge5 = ge6 = 0
    bests = []
    uniques = []
    n = 0
    for d, brs in by_draw.items():
        if len(brs) < 3:
            continue
        act = actuals.get(d)
        if not act:
            continue
        pool_ms = []
        union = set()
        for r in brs:
            try:
                sets = json.loads(r["predicted_sets_json"] or "[]")
            except Exception:
                sets = []
            for s in sets:
                nums = [int(x) for x in (s.get("nums") or [])]
                union |= set(nums)
                pool_ms.append(len(set(nums) & act))
        if not pool_ms:
            continue
        b = max(pool_ms)
        bests.append(b)
        uniques.append(len(union))
        n += 1
        if b >= 3:
            ge3 += 1
        if b >= 4:
            ge4 += 1
        if b >= 5:
            ge5 += 1
        if b >= 6:
            ge6 += 1
    con.close()
    return {
        "draws": n,
        "pool_best_mean": round(sum(bests) / n, 4) if n else 0,
        "ge3_rate": round(ge3 / n, 4) if n else 0,
        "ge4_rate": round(ge4 / n, 4) if n else 0,
        "ge5_rate": round(ge5 / n, 4) if n else 0,
        "ge6_rate": round(ge6 / n, 4) if n else 0,
        "ge6_count": ge6,
        "unique_nums_mean": round(sum(uniques) / n, 2) if n else 0,
    }


def main() -> None:
    obs = observed_pool_from_db()
    scenarios = []
    for n in (5, 15, 50, 100, 500, 1000, 8145):
        scenarios.append(
            {
                "tickets_per_draw": n,
                "p_first_one_draw": round(1.0 - (1.0 - P1) ** n, 12),
                "expected_draws_to_first": round(expected_draws_to_first(n), 1),
                "p_first_in_100_draws": round(p_at_least_one_first(n, 100), 8),
                "p_first_in_1233_draws": round(p_at_least_one_first(n, 1233), 8),
                "p_first_in_520_draws_10y": round(p_at_least_one_first(n, 520), 8),
            }
        )

    mc = {
        "random15_ge3": mc_pool_ge(3, 15),
        "random15_ge4": mc_pool_ge(4, 15),
        "random15_ge5": mc_pool_ge(5, 15),
        "random50_ge4": mc_pool_ge(4, 50),
        "random100_ge4": mc_pool_ge(4, 100),
        "random100_ge5": mc_pool_ge(5, 100),
    }

    payload = {
        "id": "K-ATTACK-COVER",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "constants": {
            "C_45_6": C45_6,
            "p_first_one_ticket": P1,
            "note": "fair independent draws assumed",
        },
        "observed_rok21_3x5_pool": obs,
        "honest_first_prize_scenarios": scenarios,
        "null_mc_cover_proxy": mc,
        "interpretation": [
            "1등 확률은 장수·회차에 선형에 가깝게 쌓임 — '뇌 점수'로 분모를 줄이지 못함",
            "관측 pool15 ge6_count는 JSON 참고 — 0이면 아직 1등 샘플 없음(기대도 극소)",
            "다음 공학: covering design으로 ge3/ge4 rate를 null MC 대비 끌어올리기 (1등 경로=장수×시간 정직)",
            "구독가치=정직확률 대시보드+커버링 엔진+WF 재현 — 예언 마케팅 금지",
        ],
        "next": "K-ATTACK-COVER-2 wheel/covering constructive OR K-ATTACK-SLICE zone filter",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print("obs", obs)
    for s in scenarios:
        if s["tickets_per_draw"] in (15, 100, 1000):
            print(s)


if __name__ == "__main__":
    main()
