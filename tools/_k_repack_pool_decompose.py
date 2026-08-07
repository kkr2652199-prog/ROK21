# -*- coding: utf-8 -*-
"""K-REPACK-DECOMPOSE — pool 10세트↔몰아주기 5세트 출처·적중·중복 정밀 분해.

- pool set 1~10 회차별 적중 분포 (0~6)
- 몰아주기 번호가 pool 어느 set_no에서 왔는지 역추적
- 세트 간 번호 중복·freq 분포 vs 몰아주기 선택 vs 당첨
- 개선 counterfactual (set_no 가중·rank mix)
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KREPACK_DECOMPOSE_survey.json"
OUT_MD = ROOT / "reports" / "20260804_KREPACK_DECOMPOSE_SURVEY.md"

BRAIN_TAGS = ["stat", "markov", "review"]
BRAIN_KO = {"stat": "1뇌·과거학습", "markov": "2뇌·흐름술사", "review": "3뇌·복습왕"}


def _hits(nums: list[int], actual: set[int]) -> int:
    return len(set(nums) & actual)


def _load_draws(lo: int, hi: int) -> dict[int, dict]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT draw_no, num1,num2,num3,num4,num5,num6, bonus FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (lo, hi),
    ).fetchall()
    conn.close()
    out = {}
    for r in rows:
        d = dict(r)
        nums = [int(d[f"num{k}"]) for k in range(1, 7)]
        out[int(d["draw_no"])] = {"actual": set(nums), "nums": nums, "bonus": int(d["bonus"])}
    return out


def _num_to_pool_sets(pool_sets: list[dict]) -> dict[int, list[int]]:
    """번호 → pool set_no 목록 (1~10)."""
    m: dict[int, list[int]] = defaultdict(list)
    for ps in pool_sets:
        sn = int(ps["set_no"])
        for n in ps["nums"]:
            m[int(n)].append(sn)
    return dict(m)


def _pool_overlap_stats(pool_sets: list[dict]) -> dict[str, Any]:
    """10세트 번호 중복 분포."""
    cnt: Counter[int] = Counter()
    all_nums: set[int] = set()
    for ps in pool_sets:
        for n in ps["nums"]:
            cnt[int(n)] += 1
            all_nums.add(int(n))
    freq_dist = Counter(cnt.values())  # 몇 개 세트에 등장했는지
    return {
        "unique_numbers": len(all_nums),
        "total_slots": sum(len(ps["nums"]) for ps in pool_sets),
        "appear_in_n_sets": {str(k): v for k, v in sorted(freq_dist.items())},
        "max_overlap": max(cnt.values()) if cnt else 0,
        "hot_numbers_ge3sets": sorted([n for n, c in cnt.items() if c >= 3]),
    }


def _trace_repack_sources(
    repack_sets: list[dict],
    num_to_sets: dict[int, list[int]],
) -> list[dict]:
    """몰아주기 각 rank별 번호 → pool set_no 출처."""
    out = []
    for rs in repack_sets:
        rank = int(rs["set_no"])
        traced = []
        set_contrib: Counter[int] = Counter()
        for n in rs["nums"]:
            sources = num_to_sets.get(int(n), [])
            traced.append({"num": int(n), "from_pool_sets": sources, "n_sources": len(sources)})
            for sn in sources:
                set_contrib[sn] += 1
        out.append(
            {
                "repack_rank": rank,
                "nums": rs["nums"],
                "hits": rs.get("hits", 0),
                "numbers_traced": traced,
                "pool_set_contribution": dict(sorted(set_contrib.items())),
                "dominant_pool_set": set_contrib.most_common(1)[0][0] if set_contrib else None,
            }
        )
    return out


def _wf_scores(draw_no: int, brain: str) -> dict[str, Any]:
    """WF 점수·ranked 목록 (몰아주기 기준 재현)."""
    import random
    from collections import defaultdict

    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.signal_pool import (
        MC_SEED,
        RollingSignalLearner,
        _build_hint,
        _pool_by_brain,
        _pool_freq,
        expand_pool,
        number_scores,
        warm_learner_to_draw,
    )

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
    scores = number_scores(brain_pool, hint, num_ema, pos_ema)
    ranked = sorted(range(1, 46), key=lambda x: (-scores[x], x))
    return {"scores": scores, "ranked": ranked, "freq": freq, "hint": hint, "num_ema": num_ema, "pos_ema": pos_ema}


def run_decompose(draw_start: int, draw_end: int) -> dict[str, Any]:
    from app.testlotto.pool_view_cache import get_cached_pool_view
    from tools.bench_quick_gate import enrich_metrics, null_for_eval_mode

    draws = _load_draws(draw_start, draw_end)
    null5 = null_for_eval_mode("best_of_5")["null_ge3"]

    # accumulators per brain
    pool_hits_by_setno: dict[str, dict[int, list[int]]] = {b: {i: [] for i in range(1, 11)} for b in BRAIN_TAGS}
    repack_hits_by_rank: dict[str, dict[int, list[int]]] = {b: {i: [] for i in range(1, 6)} for b in BRAIN_TAGS}
    pool_hit_hist: dict[str, Counter[int]] = {b: Counter() for b in BRAIN_TAGS}  # 0~6 hits count
    repack_source_setno_when_ge3: dict[str, Counter[int]] = {b: Counter() for b in BRAIN_TAGS}
    repack_winning_rank: dict[str, Counter[int]] = {b: Counter() for b in BRAIN_TAGS}
    overlap_unique: dict[str, list[int]] = {b: [] for b in BRAIN_TAGS}
    # 번호 pool 등장횟수(1~10) vs 몰아주기 선택 vs 당첨
    freq_bucket_repack_selected: dict[str, Counter[int]] = {b: Counter() for b in BRAIN_TAGS}
    freq_bucket_actual_in_repack: dict[str, Counter[int]] = {b: Counter() for b in BRAIN_TAGS}
    # counterfactual: repack if took numbers only from highest-hit pool set
    cf_best_pool_set: dict[str, list[int]] = {b: [] for b in BRAIN_TAGS}
    cf_set_no_asc_first5: dict[str, list[int]] = {b: [] for b in BRAIN_TAGS}
    cf_score_top30_split5: dict[str, list[int]] = {b: [] for b in BRAIN_TAGS}  # current
    cf_mixed_rank2345_only: dict[str, list[int]] = {b: [] for b in BRAIN_TAGS}  # skip rank1

    n_eval = 0
    for dno in range(draw_start, draw_end + 1):
        if dno not in draws:
            continue
        pv = get_cached_pool_view(dno)
        if not pv or not pv.get("ok"):
            continue
        actual = draws[dno]["actual"]
        n_eval += 1

        for brain in BRAIN_TAGS:
            pool_raw = pv.get("pool_by_brain", {}).get(brain, [])
            repack_raw = pv.get("repack_by_brain", {}).get(brain, [])
            pool_sets = [
                {"set_no": int(s.get("set_no") or 1), "nums": [int(x) for x in s["nums"]]}
                for s in pool_raw
            ]
            pool_sets.sort(key=lambda x: x["set_no"])
            repack_scored = [
                {
                    "set_no": int(s.get("set_no") or 1),
                    "nums": [int(x) for x in s["nums"]],
                    "hits": _hits([int(x) for x in s["nums"]], actual),
                }
                for s in repack_raw
            ]

            num_to_sets = _num_to_pool_sets(pool_sets)
            overlap = _pool_overlap_stats(pool_sets)
            overlap_unique[brain].append(overlap["unique_numbers"])

            # pool set 1~10 hits
            pool_hit_list = []
            for ps in pool_sets:
                h = _hits(ps["nums"], actual)
                pool_hits_by_setno[brain][ps["set_no"]].append(h)
                pool_hit_hist[brain][h] += 1
                pool_hit_list.append((ps["set_no"], h))

            best_pool_sn, best_pool_h = max(pool_hit_list, key=lambda x: x[1])
            cf_best_pool_set[brain].append(best_pool_h)

            # repack rank hits
            best_repack_h = 0
            best_repack_rank = 1
            for rs in repack_scored:
                repack_hits_by_rank[brain][rs["set_no"]].append(rs["hits"])
                if rs["hits"] > best_repack_h:
                    best_repack_h = rs["hits"]
                    best_repack_rank = rs["set_no"]
            repack_winning_rank[brain][best_repack_rank] += 1
            cf_score_top30_split5[brain].append(best_repack_h)

            if best_repack_h >= 3:
                traced = _trace_repack_sources(
                    [r for r in repack_scored if r["set_no"] == best_repack_rank],
                    num_to_sets,
                )
                if traced:
                    for sn, c in traced[0]["pool_set_contribution"].items():
                        repack_source_setno_when_ge3[brain][sn] += c

            # freq bucket: pool overlap count for numbers in repack vs winning numbers
            cnt_in_pool: Counter[int] = Counter()
            for ps in pool_sets:
                for n in ps["nums"]:
                    cnt_in_pool[n] += 1
            for rs in repack_scored:
                for n in rs["nums"]:
                    freq_bucket_repack_selected[brain][cnt_in_pool.get(n, 0)] += 1
                    if n in actual:
                        freq_bucket_actual_in_repack[brain][cnt_in_pool.get(n, 0)] += 1

            # CF: set_no asc first 5 pool sets as "repack"
            asc5 = pool_sets[:5]
            cf_set_no_asc_first5[brain].append(max(_hits(s["nums"], actual) for s in asc5) if asc5 else 0)

            # CF: mixed rank 2-5 only (skip rank1)
            r2345 = [r for r in repack_scored if r["set_no"] >= 2]
            cf_mixed_rank2345_only[brain].append(max((r["hits"] for r in r2345), default=0))

    def _summarize_hits(hits_by_key: dict[int, list[int]]) -> dict[str, Any]:
        out = {}
        for k, vals in hits_by_key.items():
            if not vals:
                continue
            ge3 = sum(1 for v in vals if v >= 3)
            out[str(k)] = {
                "mean": round(mean(vals), 4),
                "ge3_rate": round(ge3 / len(vals), 4),
                "ge3_count": ge3,
                "n": len(vals),
                "hit_histogram": dict(Counter(vals)),
            }
        return out

    def _cf_summary(cf_lists: dict[str, list[int]], label: str) -> dict[str, Any]:
        out = {}
        for brain in BRAIN_TAGS:
            vals = cf_lists[brain]
            ge3 = sum(1 for v in vals if v >= 3)
            out[brain] = {
                "label": label,
                "mean": round(mean(vals), 4) if vals else 0,
                "ge3_rate": round(ge3 / len(vals), 4) if vals else 0,
                "ge3_count": ge3,
            }
        return out

    brain_report: dict[str, Any] = {}
    for brain in BRAIN_TAGS:
        pool_sum = _summarize_hits(pool_hits_by_setno[brain])
        repack_sum = _summarize_hits(repack_hits_by_rank[brain])
        # best pool set_no by ge3
        best_pool_sn = max(pool_sum.items(), key=lambda x: x[1]["ge3_rate"])[0] if pool_sum else "?"
        brain_report[brain] = {
            "label": BRAIN_KO[brain],
            "pool_set_1_to_10": pool_sum,
            "repack_rank_1_to_5": repack_sum,
            "pool_hit_histogram_all_sets": dict(pool_hit_hist[brain]),
            "avg_unique_numbers_in_pool10": round(mean(overlap_unique[brain]), 2) if overlap_unique[brain] else 0,
            "repack_ge3_winning_rank_dist": dict(repack_winning_rank[brain]),
            "repack_ge3_pool_set_contribution": dict(repack_source_setno_when_ge3[brain]),
            "freq_in_pool_vs_repack_selection": dict(freq_bucket_repack_selected[brain]),
            "freq_in_pool_vs_actual_hits_in_repack": dict(freq_bucket_actual_in_repack[brain]),
            "best_pool_set_no_by_ge3": best_pool_sn,
        }

    counterfactuals = {
        "current_score_top30": _cf_summary(cf_score_top30_split5, "현행: 점수순 1~30위→몰1~5"),
        "best_single_pool_set": _cf_summary(cf_best_pool_set, "CF: pool 10중 최고적중 1세트만"),
        "set_no_asc_first5": _cf_summary(cf_set_no_asc_first5, "CF: pool set 1~5 그대로"),
        "repack_rank2345_only": _cf_summary(cf_mixed_rank2345_only, "CF: 몰2~5만(몰1 제외)"),
    }

    # 개선 제안 (데이터 기반)
    improvements = _build_improvements(brain_report, counterfactuals, null5)

    return {
        "id": "K-REPACK-DECOMPOSE-01",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "draw_range": [draw_start, draw_end],
        "n_eval": n_eval,
        "mechanism_precise": {
            "step1": "10 pool 세트 → 번호별 freq(25%) = pool 등장횟수/최대",
            "step2": "hint(40%) zone_mix 4주 · learn(35%) num_ema+0.5×pos_ema",
            "step3": "45번호 점수순 rank → 몰1=rank1~6, 몰2=7~12, … 몰5=25~30",
            "not": "pool set_no 1→몰1 매핑 아님 · 세트 번호와 무관하게 번호 단위 재조립",
            "trace": "몰아주기 각 번호는 pool 1~10세트 중 등장한 set_no로 역추적 가능",
        },
        "by_brain": brain_report,
        "counterfactuals": counterfactuals,
        "improvements": improvements,
        "null_ge3_best_of_5": null5,
    }


def _build_improvements(brain_report: dict, cf: dict, null5: float) -> list[dict]:
    items = []
    cur = cf["current_score_top30"]
    best_pool = cf["best_single_pool_set"]
    asc5 = cf["set_no_asc_first5"]
    r2345 = cf["repack_rank2345_only"]

    for brain in BRAIN_TAGS:
        c = cur[brain]
        bp = best_pool[brain]
        a5 = asc5[brain]
        r5 = r2345[brain]
        br = brain_report[brain]

        if bp["ge3_rate"] > c["ge3_rate"]:
            items.append(
                {
                    "brain": brain,
                    "priority": "P0",
                    "idea": "pool 10세트 oracle upper bound > 현행 몰아주기",
                    "detail": f"최고 pool 1세트 ge3={bp['ge3_rate']:.4f} vs 몰아주기 {c['ge3_rate']:.4f} — "
                    f"몰아주기가 pool 내 최적 세트를 놓침",
                    "action": "pool set_no별 pos_ema 가중 repack 또는 top-2 pool 세트 union",
                }
            )

        win_rank = br.get("repack_ge3_winning_rank_dist", {})
        if win_rank:
            top_rank = max(win_rank.items(), key=lambda x: x[1])[0]
            if top_rank != "1":
                items.append(
                    {
                        "brain": brain,
                        "priority": "P1",
                        "idea": f"ge3+ 최적 몰아주기 rank={top_rank} (몰1 아님)",
                        "detail": f"rank 분포 {win_rank}",
                        "action": "몰1 가중 축소 · rank3~5 샘플 비율 상향 또는 rank1 스kip ablation",
                    }
                )

        if r5["ge3_rate"] >= c["ge3_rate"] * 0.95:
            items.append(
                {
                    "brain": brain,
                    "priority": "P1",
                    "idea": "몰1 제외(CF) 성능 유지",
                    "detail": f"몰2~5 only ge3={r5['ge3_rate']:.4f} vs 전체 {c['ge3_rate']:.4f}",
                    "action": "hint top6 몰1 고정 폐기 · rank2~5 위주 발권 검토",
                }
            )

        freq_hit = br.get("freq_in_pool_vs_actual_hits_in_repack", {})
        freq_sel = br.get("freq_in_pool_vs_repack_selection", {})
        if freq_hit:
            # which overlap bucket hits most
            best_bucket = max(freq_hit.items(), key=lambda x: x[1])[0]
            items.append(
                {
                    "brain": brain,
                    "priority": "P2",
                    "idea": "pool 중복도와 적중 상관",
                    "detail": f"당첨번호가 repack에 있을 때 pool N세트중복 bucket={best_bucket} 최다",
                    "action": "freq 가중 25%→35% 또는 3+세트 overlap 번호 bonus",
                }
            )

    # global
    items.append(
        {
            "brain": "all",
            "priority": "P0",
            "idea": "뇌별 W_HINT/W_FREQ/W_LEARN 분리",
            "detail": "hint 3뇌 공통 → 뇌별 pool freq/learn 차별 소멸",
            "action": "grid: stat/markov/review 각 (0.3/0.35/0.35)~(0.5/0.2/0.3)",
        }
    )
    items.append(
        {
            "brain": "all",
            "priority": "P1",
            "idea": "repack 6번째 세트(rank31~36) 추가",
            "detail": "ge3+ 다수가 몰3~5에서 발생 — 30번호만으로 부족",
            "action": "best_of_6 per brain · null 재계산",
        }
    )
    items.append(
        {
            "brain": "all",
            "priority": "P2",
            "idea": "set_no_asc CF 비교",
            "detail": "; ".join(
                f"{b}: asc5={asc5[b]['ge3_rate']:.3f} cur={cur[b]['ge3_rate']:.3f}"
                for b in BRAIN_TAGS
            ),
            "action": "단순 set_no 선택은 inferior면 번호점수 유지·rank mix만 조정",
        }
    )
    return items


def _write_md(p: dict) -> None:
    lines = [
        "# K-REPACK-DECOMPOSE — pool 10세트↔몰아주기 출처·개선",
        "",
        f"eval **{p['n_eval']}**회 · {p['draw_range'][0]}~{p['draw_range'][1]}",
        "",
        "## 1. 몰아주기 정밀 기준 (현행)",
        "",
    ]
    for k, v in p["mechanism_precise"].items():
        lines.append(f"- **{k}:** {v}")

    lines.extend(["", "## 2. pool set 1~10 적중 (뇌별 mean · ge3_rate)", ""])
    for brain in BRAIN_TAGS:
        br = p["by_brain"][brain]
        lines.append(f"### {br['label']}")
        lines.append("| set_no | mean | ge3_rate | ge3 |")
        lines.append("|-------:|-----:|---------:|----:|")
        for sn in sorted(br["pool_set_1_to_10"].keys(), key=int):
            s = br["pool_set_1_to_10"][sn]
            lines.append(f"| {sn} | {s['mean']:.3f} | {s['ge3_rate']:.4f} | {s['ge3_count']}/{s['n']} |")
        lines.append(f"\n- pool 전체 적중 histogram: `{br['pool_hit_histogram_all_sets']}`")
        lines.append(f"- 10세트 unique 번호 평균: **{br['avg_unique_numbers_in_pool10']}** / 60 slots")
        lines.append("")

    lines.extend(["## 3. 몰아주기 rank 1~5 적중", ""])
    lines.append("| 뇌 | 몰1 | 몰2 | 몰3 | 몰4 | 몰5 | ge3+ 최빈 rank |")
    lines.append("|----|----:|----:|----:|----:|----:|--------------|")
    for brain in BRAIN_TAGS:
        br = p["by_brain"][brain]
        r = br["repack_rank_1_to_5"]
        wr = br.get("repack_ge3_winning_rank_dist", {})
        top = max(wr.items(), key=lambda x: x[1])[0] if wr else "?"
        lines.append(
            f"| {BRAIN_KO[brain]} | "
            + " | ".join(f"{r.get(str(i), {}).get('ge3_rate', 0):.3f}" for i in range(1, 6))
            + f" | **{top}** |"
        )

    lines.extend(["", "## 4. ge3+ 시 몰아주기 번호의 pool set_no 출처 (누적)", ""])
    for brain in BRAIN_TAGS:
        br = p["by_brain"][brain]
        contrib = br.get("repack_ge3_pool_set_contribution", {})
        lines.append(f"- **{BRAIN_KO[brain]}:** `{contrib}`")

    lines.extend(["", "## 5. pool 중복도 vs 몰아주기·당첨", ""])
    lines.append("*(bucket = 번호가 pool 10세트 중 몇 세트에 등장)*")
    for brain in BRAIN_TAGS:
        br = p["by_brain"][brain]
        lines.append(f"- {BRAIN_KO[brain]} 선택 `{br['freq_in_pool_vs_repack_selection']}` · "
                     f"당첨적중 `{br['freq_in_pool_vs_actual_hits_in_repack']}`")

    lines.extend(["", "## 6. Counterfactual (ge3_rate)", ""])
    lines.append("| 전략 | stat | markov | review |")
    lines.append("|------|-----:|-------:|-------:|")
    for key, cf in p["counterfactuals"].items():
        lines.append(
            f"| {cf['stat']['label'][:30]} | "
            f"{cf['stat']['ge3_rate']:.4f} | {cf['markov']['ge3_rate']:.4f} | {cf['review']['ge3_rate']:.4f} |"
        )

    lines.extend(["", "## 7. 개선 제안 (데이터 기반)", ""])
    for it in p["improvements"]:
        lines.append(f"- **[{it['priority']}] {it['brain']}** — {it['idea']}: {it['action']}")

    lines.append(f"\n*JSON:* `{OUT_JSON}`")
    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    (ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name).write_text(text, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draw-start", type=int, default=1035)
    ap.add_argument("--draw-end", type=int, default=1234)
    args = ap.parse_args()
    payload = run_decompose(args.draw_start, args.draw_end)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_md(payload)
    print(f"n_eval={payload['n_eval']}", flush=True)
    print(f"wrote {OUT_JSON}", flush=True)
    print(f"wrote {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()
