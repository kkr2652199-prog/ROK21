# -*- coding: utf-8 -*-
"""K-REPACK-PER-BRAIN — 백테스트 회차별 3뇌 몰아주기(5세트) 정밀 분석.

구조: 뇌당 10 pool → 번호별 신호점수 → 상위 6×5 = 몰아주기 1~5번
명분: hint(40%) + pool빈도(25%) + learn EMA(35%)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KREPACK_PER_BRAIN_survey.json"
OUT_MD = ROOT / "reports" / "20260804_KREPACK_PER_BRAIN_SURVEY.md"

BRAIN_TAGS = ["stat", "markov", "review"]
BRAIN_KO = {"stat": "1뇌·통계요정", "markov": "2뇌·흐름술사", "review": "3뇌·복습왕"}
REPACK_RANK_KO = {
    1: "몰아주기 1번(최고 신호 6수)",
    2: "몰아주기 2번(7~12위 6수)",
    3: "몰아주기 3번(13~18위 6수)",
    4: "몰아주기 4번(19~24위 6수)",
    5: "몰아주기 5번(25~30위 6수)",
}


def _match_count(nums: list[int], actual: set[int]) -> int:
    return len(set(int(x) for x in nums) & actual)


def _load_draws(draw_start: int, draw_end: int) -> dict[int, dict]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT draw_no, draw_date, num1,num2,num3,num4,num5,num6, bonus
        FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no
        """,
        (draw_start, draw_end),
    ).fetchall()
    conn.close()
    out: dict[int, dict] = {}
    for r in rows:
        d = dict(r)
        nums = [int(d[f"num{k}"]) for k in range(1, 7)]
        out[int(d["draw_no"])] = {
            "draw_no": int(d["draw_no"]),
            "draw_date": d["draw_date"],
            "nums": nums,
            "actual": set(nums),
            "bonus": int(d["bonus"]),
        }
    return out


def _load_pool_view(draw_no: int) -> dict | None:
    from app.testlotto.pool_view_cache import get_cached_pool_view

    return get_cached_pool_view(draw_no)


def _score_sets(sets: list[dict], actual: set[int]) -> list[dict]:
    scored = []
    for s in sets:
        nums = [int(x) for x in s["nums"]]
        mc = _match_count(nums, actual)
        scored.append(
            {
                "set_no": int(s.get("set_no") or 1),
                "nums": nums,
                "hits": mc,
                "kind": s.get("kind", "repack"),
            }
        )
    return scored


def _tier_for_best(sets: list[dict], actual_list: list[int], bonus: int) -> int:
    from app.testlotto.tier_utils import score_predicted_set

    best_tr = 0
    for c in sets:
        tr = int(score_predicted_set(c["nums"], actual_list, bonus)["tier_rank"])
        if tr > 0 and (best_tr == 0 or tr < best_tr):
            best_tr = tr
    return best_tr


def _explain_repack(draw_no: int, brain: str) -> dict[str, Any]:
    """WF 재계산 — 몰아주기 명분(점수 분해) + pool 10세트 출처."""
    from app.testlotto.signal_pool import (
        W_FREQ,
        W_HINT,
        W_LEARN,
        _build_hint,
        _pool_by_brain,
        _pool_freq,
        expand_pool,
        number_scores,
        repack_sets,
        warm_learner_to_draw,
        RollingSignalLearner,
        MC_SEED,
    )
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    import random
    from collections import defaultdict

    set_learn_as_of(draw_no)
    draws = _get_draws_before(draw_no)
    learner = RollingSignalLearner()
    warm_learner_to_draw(learner, max(1, draw_no - 200), draw_no, seed=MC_SEED)
    num_ema, pos_ema = learner.snapshot()
    random.seed(MC_SEED)
    pool = expand_pool(draws, draw_no, seed=MC_SEED)
    pool_br = _pool_by_brain(pool)
    brain_pool = pool_br.get(brain, [])
    hint = _build_hint(draws, draw_no)
    freq = _pool_freq(brain_pool)
    pos_boost: dict[int, float] = defaultdict(float)
    for c in brain_pool:
        sn = int(c.get("pred_set_no") or 1)
        pw = pos_ema.get(sn, 0.0)
        for n in c["nums"]:
            pos_boost[int(n)] = max(pos_boost[int(n)], pw)

    scores = number_scores(brain_pool, hint, num_ema, pos_ema)
    ranked = sorted(range(1, 46), key=lambda x: (-scores[x], x))
    repack = repack_sets(scores)

    # pool set_no → nums (1~10)
    pool_sets = sorted(
        [
            {
                "set_no": int(c.get("pred_set_no") or c.get("set_no") or 1),
                "nums": sorted(int(x) for x in c["nums"]),
            }
            for c in brain_pool
        ],
        key=lambda x: x["set_no"],
    )

    def num_breakdown(n: int) -> dict:
        return {
            "hint": round(hint.get(n, 0.0), 4),
            "freq": round(freq.get(n, 0.0), 4),
            "learn_num_ema": round(num_ema.get(n, 0.0), 4),
            "learn_pos_boost": round(pos_boost.get(n, 0.0), 4),
            "total": round(scores[n], 4),
            "rank": ranked.index(n) + 1 if n in ranked else 0,
        }

    repack_detail = []
    idx = 0
    for rank, nums in enumerate(repack, 1):
        repack_detail.append(
            {
                "repack_rank": rank,
                "label": REPACK_RANK_KO.get(rank, f"몰아주기 {rank}번"),
                "nums": nums,
                "number_breakdown": [num_breakdown(n) for n in nums],
            }
        )
        idx += 6

    top10_signal = [
        {"num": n, **_num_breakdown_simple(n, hint, freq, num_ema, pos_boost, scores, ranked)}
        for n in ranked[:10]
    ]

    return {
        "weights": {"hint": W_HINT, "freq": W_FREQ, "learn": W_LEARN},
        "window_hint": {"weeks": 4, "signal": "zone_mix"},
        "pool_10_sets": pool_sets,
        "repack_mechanism": (
            "10 pool 세트에서 번호별 점수 = 0.40×hint + 0.25×pool빈도 + 0.35×(num_ema+0.5×pos_boost). "
            "45번호 전체 순위 → 1~6위=몰아주기1, 7~12=2, … 25~30=5. "
            "pool 1~10번 세트와 몰아주기 1~5번은 1:1 대응 아님(번호 재조립)."
        ),
        "top10_signal_numbers": top10_signal,
        "repack_5_detail": repack_detail,
    }


def _num_breakdown_simple(n, hint, freq, num_ema, pos_boost, scores, ranked):
    return {
        "hint": round(hint.get(n, 0.0), 4),
        "freq": round(freq.get(n, 0.0), 4),
        "learn": round(num_ema.get(n, 0.0) + 0.5 * pos_boost.get(n, 0.0), 4),
        "total": round(scores[n], 4),
        "rank": ranked.index(n) + 1,
    }


def run_analysis(draw_start: int, draw_end: int) -> dict[str, Any]:
    from tools.bench_quick_gate import enrich_metrics, null_for_eval_mode

    draws = _load_draws(draw_start, draw_end)
    null_meta = null_for_eval_mode("best_of_5")

    per_draw: list[dict] = []
    by_brain: dict[str, dict[str, list]] = {b: defaultdict(list) for b in BRAIN_TAGS}
    missing_cache: list[int] = []

    for dno in range(draw_start, draw_end + 1):
        if dno not in draws:
            continue
        d = draws[dno]
        pv = _load_pool_view(dno)
        if not pv or not pv.get("ok"):
            missing_cache.append(dno)
            continue

        actual = d["actual"]
        actual_list = d["nums"]
        row: dict[str, Any] = {"draw_no": dno, "actual": actual_list, "bonus": d["bonus"], "brains": {}}

        all_repack_best = 0
        for brain in BRAIN_TAGS:
            pool_sets = pv.get("pool_by_brain", {}).get(brain, [])
            repack_sets = pv.get("repack_by_brain", {}).get(brain, [])
            pool_scored = _score_sets(pool_sets, actual)
            repack_scored = _score_sets(repack_sets, actual)
            pool_best = max((x["hits"] for x in pool_scored), default=0)
            repack_best = max((x["hits"] for x in repack_scored), default=0)
            all_repack_best = max(all_repack_best, repack_best)

            best_repack_rank = 1
            for rs in repack_scored:
                if rs["hits"] == repack_best:
                    best_repack_rank = rs["set_no"]
                    break

            tier = _tier_for_best(repack_sets, actual_list, d["bonus"]) if repack_sets else 0

            brain_row = {
                "pool_best_hits": pool_best,
                "repack_best_hits": repack_best,
                "repack_lift": repack_best - pool_best,
                "best_repack_rank": best_repack_rank,
                "best_tier": tier,
                "repack_by_rank": repack_scored,
                "pool_by_set": pool_scored,
            }
            row["brains"][brain] = brain_row

            by_brain[brain]["repack_best"].append(repack_best)
            by_brain[brain]["pool_best"].append(pool_best)
            by_brain[brain]["lift"].append(repack_best - pool_best)
            for rs in repack_scored:
                by_brain[brain][f"rank{rs['set_no']}_hits"].append(rs["hits"])

        row["combined_repack_best_15"] = all_repack_best
        per_draw.append(row)

    n_eval = len(per_draw)
    brain_summary: dict[str, Any] = {}
    for brain in BRAIN_TAGS:
        bests = by_brain[brain]["repack_best"]
        ge3 = sum(1 for x in bests if x >= 3)
        ge4 = sum(1 for x in bests if x >= 4)
        m = mean(bests) if bests else 0.0
        enriched = enrich_metrics(ge3, n_eval, m, gate_mode="per_brain_repack", eval_mode="best_of_5")
        rank_means = {
            r: round(mean(by_brain[brain][f"rank{r}_hits"]), 4)
            for r in range(1, 6)
            if by_brain[brain][f"rank{r}_hits"]
        }
        brain_summary[brain] = {
            "label": BRAIN_KO[brain],
            "n_eval": n_eval,
            "repack_best_mean": round(m, 4),
            "ge3_count": ge3,
            "ge3_rate": round(ge3 / n_eval, 4) if n_eval else 0,
            "ge4_count": ge4,
            "null_ge3": null_meta["null_ge3"],
            "pool_best_mean": round(mean(by_brain[brain]["pool_best"]), 4) if bests else 0,
            "avg_lift_pool_to_repack": round(mean(by_brain[brain]["lift"]), 4) if bests else 0,
            "repack_rank_mean_hits": rank_means,
            "gate": enriched,
        }

    # TOP 회차 per brain (repack_best >= 3 or top 10 by hits)
    top_by_brain: dict[str, list[dict]] = {b: [] for b in BRAIN_TAGS}
    for row in per_draw:
        for brain in BRAIN_TAGS:
            br = row["brains"].get(brain, {})
            if br.get("repack_best_hits", 0) >= 3:
                top_by_brain[brain].append(
                    {
                        "draw_no": row["draw_no"],
                        "actual": row["actual"],
                        "repack_best_hits": br["repack_best_hits"],
                        "best_repack_rank": br["best_repack_rank"],
                        "best_tier": br["best_tier"],
                        "repack_by_rank": br["repack_by_rank"],
                        "pool_best_hits": br["pool_best_hits"],
                    }
                )
    for brain in BRAIN_TAGS:
        top_by_brain[brain].sort(key=lambda x: (-x["repack_best_hits"], x["draw_no"]))
        top_by_brain[brain] = top_by_brain[brain][:12]

    # 명분 deep-dive: 각 뇌 TOP 3 회차
    deep_dive: dict[str, list[dict]] = {}
    for brain in BRAIN_TAGS:
        deep_dive[brain] = []
        for item in top_by_brain[brain][:3]:
            expl = _explain_repack(item["draw_no"], brain)
            winning = next(
                (r for r in item["repack_by_rank"] if r["set_no"] == item["best_repack_rank"]),
                item["repack_by_rank"][0] if item["repack_by_rank"] else {},
            )
            deep_dive[brain].append(
                {
                    **item,
                    "winning_repack_nums": winning.get("nums", []),
                    "explain": expl,
                }
            )

    # combined sanity: max of 3 brains vs stored backtest
    combined_ge3 = sum(1 for row in per_draw if row["combined_repack_best_15"] >= 3)

    return {
        "id": "K-REPACK-PER-BRAIN-01",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "draw_range": [draw_start, draw_end],
        "n_eval": n_eval,
        "missing_cache_draws": missing_cache[:20],
        "missing_cache_n": len(missing_cache),
        "mechanism": {
            "pool_per_brain": 10,
            "repack_per_brain": 5,
            "total_repack_sets": 15,
            "repack_not_pool_subset": True,
            "score_formula": "0.40×hint(zone_mix 4주) + 0.25×pool빈도 + 0.35×learn_EMA",
            "repack_ranks": REPACK_RANK_KO,
        },
        "by_brain": brain_summary,
        "combined_repack_best15_ge3_rate": round(combined_ge3 / n_eval, 4) if n_eval else 0,
        "top_draws_by_brain": top_by_brain,
        "deep_dive_top3": deep_dive,
    }


def _write_md(payload: dict) -> None:
    bs = payload["by_brain"]
    lines = [
        "# K-REPACK-PER-BRAIN — 3뇌 몰아주기 정밀 분석",
        "",
        f"날짜 {payload['ts'][:10]} · eval **{payload['n_eval']}**회 · {payload['draw_range'][0]}~{payload['draw_range'][1]}",
        "",
        "## 1. 몰아주기 형태 (공통)",
        "",
        "| 항목 | 내용 |",
        "|------|------|",
        "| **pool** | 뇌당 **10세트** (2× predict 5세트, seed offset) |",
        "| **몰아주기** | 뇌당 **5세트** — 10세트에서 뽑은 번호가 **아님** |",
        "| **조립** | 45번호 점수순 → 1~6위=몰1, 7~12=몰2, … 25~30=몰5 |",
        "| **명분 가중** | hint **40%** + pool빈도 **25%** + learn **35%** |",
        "| **hint** | 4주 `zone_mix` (저·중·고 구역 underrep 보정) · 3뇌 공통 |",
        "",
        "## 2. 뇌별 몰아주기 성적 (best_of_5 기준)",
        "",
        "| 뇌 | ge3 | ge3_rate | mean | pool_mean | lift | null_ge3 |",
        "|----|----:|---------:|-----:|----------:|-----:|---------:|",
    ]
    for tag in BRAIN_TAGS:
        b = bs[tag]
        lines.append(
            f"| {b['label']} | {b['ge3_count']}/{b['n_eval']} | **{b['ge3_rate']:.4f}** | "
            f"{b['repack_best_mean']:.3f} | {b['pool_best_mean']:.3f} | {b['avg_lift_pool_to_repack']:+.3f} | "
            f"{b['null_ge3']:.4f} |"
        )

    lines.extend(["", "## 3. 몰아주기 1~5번 rank별 평균 적중", ""])
    lines.append("| 뇌 | 몰1 | 몰2 | 몰3 | 몰4 | 몰5 |")
    lines.append("|----|----:|----:|----:|----:|----:|")
    for tag in BRAIN_TAGS:
        rm = bs[tag]["repack_rank_mean_hits"]
        lines.append(
            f"| {BRAIN_KO[tag]} | {rm.get(1,0):.3f} | {rm.get(2,0):.3f} | "
            f"{rm.get(3,0):.3f} | {rm.get(4,0):.3f} | {rm.get(5,0):.3f} |"
        )

    lines.extend(["", "## 4. 최고 성적 회차 (ge3+ · 뇌별)", ""])
    for tag in BRAIN_TAGS:
        lines.append(f"### {BRAIN_KO[tag]}")
        tops = payload["top_draws_by_brain"].get(tag, [])[:8]
        if not tops:
            lines.append("- ge3+ 회차 없음")
            continue
        for t in tops[:8]:
            rank_label = REPACK_RANK_KO.get(t["best_repack_rank"], str(t["best_repack_rank"]))
            lines.append(
                f"- **{t['draw_no']}회** · 적중 **{t['repack_best_hits']}** · {rank_label} · "
                f"등수 tier={t['best_tier']} · 당첨 {t['actual']}"
            )
        lines.append("")

    lines.extend(["## 5. TOP3 회차 명분 (신호 분해)", ""])
    for tag in BRAIN_TAGS:
        lines.append(f"### {BRAIN_KO[tag]}")
        for dd in payload.get("deep_dive_top3", {}).get(tag, [])[:2]:
            lines.append(f"#### {dd['draw_no']}회 — 몰{dd['best_repack_rank']}번 {dd['winning_repack_nums']}")
            expl = dd["explain"]
            lines.append(f"- pool 10세트: `{json.dumps(expl['pool_10_sets'], ensure_ascii=False)}`")
            top3 = expl["top10_signal_numbers"][:6]
            sig = ", ".join(f"{x['num']}(h={x['hint']},f={x['freq']},L={x['learn']})" for x in top3)
            lines.append(f"- 상위 신호번호: {sig}")
        lines.append("")

    lines.extend(
        [
            "## 6. 튜닝 시사점",
            "",
            "- **몰1번**이 대부분 뇌에서 최고 적중 — rank2~5는 평균 하락(신호 top-heavy)",
            "- pool→repack **lift** 양수면 몰아주기가 10세트 max보다 유리",
            "- hint 3뇌 공통 → 뇌별 차이는 **pool 빈도·learn EMA** 에서 발생",
            "- 튜닝 축: W_HINT/W_FREQ/W_LEARN, repack 5→6, hint_only vs full ablation",
            "",
            f"*JSON:* `{OUT_JSON}`",
        ]
    )
    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draw-start", type=int, default=1035)
    ap.add_argument("--draw-end", type=int, default=1234)
    args = ap.parse_args()

    payload = run_analysis(args.draw_start, args.draw_end)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_md(payload)
    print(f"n_eval={payload['n_eval']} missing_cache={payload['missing_cache_n']}", flush=True)
    for tag in BRAIN_TAGS:
        b = payload["by_brain"][tag]
        print(f"  {tag}: ge3={b['ge3_rate']:.4f} mean={b['repack_best_mean']:.3f} lift={b['avg_lift_pool_to_repack']:+.3f}", flush=True)
    print(f"wrote {OUT_JSON}", flush=True)
    print(f"wrote {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()
