# -*- coding: utf-8 -*-
"""뇌 감사 + 비인기 신호 검증 — READ-ONLY 정찰 (DB 쓰기 금지)."""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.registry import AUX_BRAINS, PREDICT_BRAINS, SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.features.draw_features import sorted_nums  # noqa: E402
from app.testlotto.filters import tier1_filter  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from app.testlotto.set_diversity import avg_pairwise_jaccard  # noqa: E402
from tools.run_set_picker_wf import _load_tagged_sets  # noqa: E402

DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260726_뇌감사_비인기검증"
SEED = 20260726


def mean_std(xs: list[float]) -> tuple[float, float]:
    n = len(xs)
    if not n:
        return 0.0, 0.0
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / n
    return m, math.sqrt(v)


def bootstrap_mean_ci(xs: list[float], n_boot: int = 3000, seed: int = SEED) -> list[float]:
    rng = random.Random(seed)
    n = len(xs)
    if n == 0:
        return [0.0, 0.0]
    boots = []
    for _ in range(n_boot):
        s = sum(xs[rng.randrange(n)] for _ in range(n)) / n
        boots.append(s)
    boots.sort()
    return [round(boots[int(0.025 * n_boot)], 6), round(boots[int(0.975 * n_boot)], 6)]


def jaccard(a: set[int], b: set[int]) -> float:
    return len(a & b) / max(1, len(a | b))


def load_draws() -> list[dict]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM lotto_draws ORDER BY draw_no")]
    finally:
        conn.close()


def hit_mean(sets: list[list[int]], actual: list[int]) -> float:
    if not sets:
        return 0.0
    return sum(len(set(s) & set(actual)) for s in sets) / len(sets)


def audit_brains_static() -> dict[str, Any]:
    predict = []
    for b in PREDICT_BRAINS:
        entry = {
            **b,
            "sets_per_draw": SETS_PER_PREDICT_BRAIN,
            "module": {
                "stat": "app/testlotto/brains/predict_stat_fairy.py::predict_sets",
                "markov": "app/testlotto/brains/predict_flow_shaman.py::predict_sets",
                "review": "app/testlotto/brains/predict_review_king.py::predict_sets",
            }[b["tag"]],
            "engine_impl": {
                "stat": "predict_statistical._statistical_predict",
                "markov": "predict_markov._markov_predict",
                "review": "predict_review_king.predict_sets (inline)",
            }[b["tag"]],
        }
        predict.append(entry)
    aux = []
    for b in AUX_BRAINS:
        mod = {
            "miss_aux": "brains/aux_miss_detective.py::score_set",
            "pattern_aux": "brains/aux_pattern_spotlight.py::score_set",
            "balance_aux": "brains/aux_balance_keeper.py::score_set",
            "referee_aux": "brains/aux_referee.py::score_set",
        }[b["tag"]]
        aux.append(
            {
                **b,
                "module": mod,
                "role_detail": "채점/가중 (새 세트 생성 안 함). coordinator._apply_aux_scoring",
            }
        )
    return {
        "predict_brains": predict,
        "aux_brains": aux,
        "contribution_nominal": "각 예측뇌 5장 → 합 15장. 보조뇌 0장.",
        "coordinator": "app/testlotto/brains/coordinator.py::run_coordinated_prediction",
    }


def pair_overlap_last_n(tagged, draws, n: int = 100) -> dict[str, Any]:
    use = [d for d in draws if len(tagged.get(int(d["draw_no"]), [])) >= 5][-n:]
    pair_j = defaultdict(list)
    uniq_contrib = defaultdict(list)  # fraction of sets unique to brain (set equality)
    brain_set_counts = Counter()

    for d in use:
        td = int(d["draw_no"])
        by: dict[str, list[frozenset]] = defaultdict(list)
        for e in tagged[td]:
            by[e["brain"]].append(frozenset(e["nums"]))
            brain_set_counts[e["brain"]] += 1
        brains = ["stat", "markov", "review"]
        for a, b in combinations(brains, 2):
            sa, sb = by.get(a, []), by.get(b, [])
            if not sa or not sb:
                continue
            # mean jaccard across all set pairs between brains
            vals = [jaccard(set(x), set(y)) for x in sa for y in sb]
            pair_j[f"{a}_{b}"].append(sum(vals) / len(vals))
        # unique contribution: sets of brain not equal to any other brain's set
        all_others = {
            br: set(by[br]) for br in brains
        }
        for br in brains:
            mine = by.get(br, [])
            if not mine:
                continue
            others = set()
            for ob, ss in all_others.items():
                if ob != br:
                    others |= ss
            uniq = sum(1 for s in mine if s not in others)
            uniq_contrib[br].append(uniq / len(mine))

    def avg(xs):
        return round(sum(xs) / max(1, len(xs)), 6)

    return {
        "n_draws": len(use),
        "avg_cross_brain_set_jaccard": {k: avg(v) for k, v in pair_j.items()},
        "avg_unique_set_fraction": {k: avg(v) for k, v in uniq_contrib.items()},
        "sets_counted": dict(brain_set_counts),
        "note": "Jaccard=뇌 간 세트쌍 평균. unique=타 뇌와 완전동일 세트가 아닌 비율.",
    }


def ablation_last_n(tagged, draws, n: int = 100) -> dict[str, Any]:
    use = [d for d in draws if len(tagged.get(int(d["draw_no"]), [])) >= 5][-n:]
    configs = {
        "all3": ("stat", "markov", "review"),
        "no_stat": ("markov", "review"),
        "no_markov": ("stat", "review"),
        "no_review": ("stat", "markov"),
    }
    rows = {k: {"mean": [], "unique": [], "jaccard": []} for k in configs}

    for d in use:
        td = int(d["draw_no"])
        actual = sorted_nums(d)
        by = defaultdict(list)
        for e in tagged[td]:
            by[e["brain"]].append(e["nums"])
        for name, brains in configs.items():
            sets = []
            for b in brains:
                sets.extend(by.get(b, []))
            if len(sets) < 2:
                continue
            rows[name]["mean"].append(hit_mean(sets, actual))
            rows[name]["unique"].append(len(set().union(*[set(s) for s in sets])))
            rows[name]["jaccard"].append(avg_pairwise_jaccard(sets))

    table = []
    base_means = rows["all3"]["mean"]
    base_ci = bootstrap_mean_ci(base_means)
    for name, mets in rows.items():
        m, s = mean_std(mets["mean"])
        ci = bootstrap_mean_ci(mets["mean"], seed=SEED + hash(name) % 1000)
        u, _ = mean_std([float(x) for x in mets["unique"]])
        j, _ = mean_std(mets["jaccard"])
        # surplus if CI of (config_mean - all3_mean) includes 0 via overlap of CIs crudely
        # better: bootstrap diff
        if name == "all3":
            verdict = "기준"
            diff_ci = [0.0, 0.0]
        else:
            rng = random.Random(SEED + 11)
            diffs = []
            n0 = min(len(base_means), len(mets["mean"]))
            for _ in range(3000):
                idx = [rng.randrange(n0) for _ in range(n0)]
                diffs.append(
                    sum(mets["mean"][i] for i in idx) / n0
                    - sum(base_means[i] for i in idx) / n0
                )
            diffs.sort()
            diff_ci = [round(diffs[int(0.025 * 3000)], 6), round(diffs[int(0.975 * 3000)], 6)]
            if diff_ci[0] <= 0 <= diff_ci[1]:
                verdict = "잉여후보(mean변화 CI내 0)"
            elif diff_ci[1] < 0:
                verdict = "제거 시 mean 하락(유지 가치)"
            else:
                verdict = "제거 시 mean 상승(유해 가능)"
        table.append(
            {
                "config": name,
                "brains": list(configs[name]),
                "mean": round(m, 6),
                "mean_std": round(s, 6),
                "mean_ci95": ci,
                "delta_mean_vs_all3_ci95": diff_ci,
                "unique_nums": round(u, 4),
                "jaccard": round(j, 6),
                "n": len(mets["mean"]),
                "verdict": verdict,
            }
        )
    return {"n_draws": len(use), "table": table, "all3_mean_ci95": base_ci}


def review_leak_trace() -> dict[str, Any]:
    # static code path evidence
    review_src = (ROOT / "app/testlotto/brains/predict_review_king.py").read_text(
        encoding="utf-8"
    )
    coord_src = (ROOT / "app/testlotto/brains/coordinator.py").read_text(encoding="utf-8")
    uses_draws_arg = "def predict_sets(draws" in review_src
    coord_cutoff = "_get_draws_before(target_draw_no)" in coord_src
    # review uses draws[-1] and repeat_rate_after_draw(draws) — depends on caller passing cutoff
    # compare stored mean last 100
    return {
        "predict_sets_signature_uses_draws_arg": uses_draws_arg,
        "coordinator_passes__get_draws_before": coord_cutoff,
        "review_uses_only_passed_draws": True,  # from code read: rates/prev from draws only
        "review_direct_db_query_in_predict_sets": (
            "get_lotto_db" in review_src or "sqlite" in review_src.lower()
        ),
        "learn_state_load": "load_learn_state(\"review\")" in review_src,
        "learn_state_leak_risk": "미확인 — learn_state가 미래 피드백으로 오염됐는지는 별도 감사 필요",
        "note": (
            "정상 경로: coordinator → _get_draws_before(target) → predict_sets(draws). "
            "predict_sets 자체는 DB에서 target 이후 draws를 읽지 않음(코드 정적)."
        ),
    }


def filter_audit(draws: list[dict], n_sets: int = 20000) -> dict[str, Any]:
    rng = random.Random(SEED)
    # use last 100 actuals, for each generate random tickets, split by tier1
    use = draws[-100:]
    pass_hits = []
    fail_hits = []
    for d in use:
        actual = sorted_nums(d)
        for _ in range(50):
            s = sorted(rng.sample(range(1, 46), 6))
            h = len(set(s) & set(actual))
            if tier1_filter(s):
                pass_hits.append(h)
            else:
                fail_hits.append(h)
    # also describe tier1
    filt_src = (ROOT / "app/testlotto/filters.py").read_text(encoding="utf-8")
    return {
        "filters_in_generation_path": [
            {
                "name": "tier1_filter",
                "file": "app/testlotto/filters.py",
                "used_in": "predict_statistical, predict_review_king (생성 중 거부)",
                "source_excerpt_present": "def tier1_filter" in filt_src,
            },
            {
                "name": "odd_even miss/boost",
                "file": "draw_analysis / learn_state",
                "used_in": "사후 miss 기록·boost (생성 필터 아님)",
            },
            {
                "name": "L_ending",
                "file": "meta hybrid ending",
                "used_in": "메타 1슬롯 교체 (생성 필터 아님)",
            },
            {
                "name": "sum/odd/range in statistical confidence",
                "file": "predict_statistical.py",
                "used_in": "신뢰도 가산 + tier1과 연계된 합·홀짝·구간",
            },
        ],
        "tier1_random_probe": {
            "n_pass": len(pass_hits),
            "n_fail": len(fail_hits),
            "mean_pass": round(sum(pass_hits) / max(1, len(pass_hits)), 6),
            "mean_fail": round(sum(fail_hits) / max(1, len(fail_hits)), 6)
            if fail_hits
            else None,
            "theory": 0.8,
            "note": "필터가 적중기댓값을 올리면 안 됨(상수). pass≈fail≈0.8이면 편향 없음.",
        },
        "popular_pattern_judgment": {
            "tier1_typical_mass_preferences": [
                "합계 대역",
                "홀짝 균형",
                "구간 분산",
                "과도 연속 제한(추정 — filters.py 본문 확인)",
            ],
            "pushes_popular_patterns": "정성: 예(대중 필터와 유사 가능) — 코드 본문 근거는 filters.py",
        },
    }


def read_tier1_body() -> str:
    return (ROOT / "app/testlotto/filters.py").read_text(encoding="utf-8")


def unpopular_data_availability() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        draw_cols = [r[1] for r in conn.execute("PRAGMA table_info(lotto_draws)")]
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )]
        fw_nonnull = conn.execute(
            "SELECT COUNT(*) FROM lotto_draws WHERE first_winners IS NOT NULL AND first_winners>0"
        ).fetchone()[0]
        fw_total = conn.execute("SELECT COUNT(*) FROM lotto_draws").fetchone()[0]
        tier_info = {}
        if "lotto_prize_tiers" in tables or "prize_tiers" in tables:
            tname = "lotto_prize_tiers" if "lotto_prize_tiers" in tables else "prize_tiers"
        else:
            # find
            tname = None
            for t in tables:
                if "prize" in t.lower() or "tier" in t.lower():
                    tname = t
                    break
        if tname:
            cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{tname}")')]
            # counts by tier
            try:
                by_tier = conn.execute(
                    f"""
                    SELECT tier_rank, COUNT(*), SUM(CASE WHEN winner_count>0 THEN 1 ELSE 0 END),
                           AVG(winner_count), AVG(prize_per_game)
                    FROM "{tname}" GROUP BY tier_rank ORDER BY tier_rank
                    """
                ).fetchall()
                tier_info = {
                    "table": tname,
                    "cols": cols,
                    "by_tier": [
                        {
                            "tier": int(r[0]),
                            "rows": int(r[1]),
                            "rows_with_winners": int(r[2] or 0),
                            "avg_winner_count": round(float(r[3] or 0), 4),
                            "avg_prize_per_game": round(float(r[4] or 0), 2),
                        }
                        for r in by_tier
                    ],
                }
            except Exception as e:
                tier_info = {"table": tname, "error": str(e), "cols": cols}
        # archive?
        arch = {}
        for t in tables:
            if "archive" in t or "detail" in t:
                cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{t}")')]
                if any("winner" in c.lower() for c in cols):
                    arch[t] = cols
    finally:
        conn.close()

    # also lotto4
    lotto4 = ROOT / "data" / "lotto4.db"
    l4 = {}
    if lotto4.exists():
        c4 = sqlite3.connect(f"file:{lotto4.as_posix()}?mode=ro", uri=True)
        try:
            t4 = [r[0] for r in c4.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            l4["tables_prize_like"] = [t for t in t4 if "prize" in t.lower() or "tier" in t.lower() or "winner" in t.lower()]
            if "lotto_draws" in t4:
                cols = [r[1] for r in c4.execute("PRAGMA table_info(lotto_draws)")]
                l4["lotto_draws_cols"] = cols
                l4["first_winners_gt0"] = c4.execute(
                    "SELECT COUNT(*) FROM lotto_draws WHERE IFNULL(first_winners,0)>0"
                ).fetchone()[0]
        finally:
            c4.close()

    collect_hint = {
        "api_path_in_code": "app/testlotto/data_service.py fetch — firstPrzwnerCo → first_winners",
        "detail_tiers": "draw_archive / prize_tiers 수집 경로 존재",
        "execute_collection": "금지(이번 지시 READ-ONLY)",
    }
    return {
        "testlotto_lotto_draws_cols": draw_cols,
        "first_winners_positive_rows": int(fw_nonnull),
        "first_winners_total_draws": int(fw_total),
        "prize_tier_info": tier_info,
        "archive_tables_with_winner_cols": arch,
        "lotto4": l4,
        "collection_hint": collect_hint,
    }


def unpopular_signal_if_available(avail: dict) -> dict[str, Any]:
    """3등 winner_count 가용 시 상관 분석. 없으면 stop."""
    info = avail.get("prize_tier_info") or {}
    by = {r["tier"]: r for r in info.get("by_tier", [])}
    # need tier 3 with data
    t3 = by.get(3) or by.get(4)
    if not info.get("table") or not by:
        return {
            "status": "STOP",
            "reason": "prize tier 테이블/집계 없음 또는 비어 있음",
            "signal_vars_significant": None,
        }
    # check enough rows with winners for tier 3
    tier3_ok = (by.get(3) or {}).get("rows_with_winners", 0) >= 30
    tier1_ok = (by.get(1) or {}).get("rows_with_winners", 0) >= 30
    if not tier3_ok and not tier1_ok:
        return {
            "status": "STOP",
            "reason": f"당첨자수 표본 부족 — tier별 rows_with_winners={ {k: v.get('rows_with_winners') for k,v in by.items()} }",
            "by_tier": list(by.values()),
            "signal_vars_significant": [],
        }

    # load join draw features × log(winner_count)
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        tname = info["table"]
        prefer_tier = 3 if tier3_ok else 1
        rows = conn.execute(
            f"""
            SELECT d.draw_no, d.num1,d.num2,d.num3,d.num4,d.num5,d.num6,
                   t.winner_count, t.prize_per_game
            FROM lotto_draws d
            JOIN "{tname}" t ON t.draw_no = d.draw_no AND t.tier_rank = ?
            WHERE IFNULL(t.winner_count,0) > 0
            ORDER BY d.draw_no
            """,
            (prefer_tier,),
        ).fetchall()
    finally:
        conn.close()

    if len(rows) < 30:
        return {
            "status": "STOP",
            "reason": f"join 후 n={len(rows)} < 30",
            "prefer_tier": prefer_tier,
            "signal_vars_significant": [],
        }

    # features vs log winners
    import math as _m

    ys = []
    feats = {
        "n_le31": [],
        "n_le12": [],
        "consec_pairs": [],
        "odd_count": [],
        "sum_nums": [],
        "carry_from_prev": [],
    }
    prev = None
    for r in rows:
        nums = sorted(int(x) for x in r[1:7])
        wc = int(r[7])
        ys.append(_m.log(wc))
        feats["n_le31"].append(sum(1 for x in nums if x <= 31))
        feats["n_le12"].append(sum(1 for x in nums if x <= 12))
        consec = sum(1 for i in range(5) if nums[i + 1] == nums[i] + 1)
        feats["consec_pairs"].append(consec)
        feats["odd_count"].append(sum(1 for x in nums if x % 2))
        feats["sum_nums"].append(sum(nums))
        if prev is None:
            feats["carry_from_prev"].append(0)
        else:
            feats["carry_from_prev"].append(len(set(nums) & set(prev)))
        prev = nums

    def pearson(a: list[float], b: list[float]) -> float:
        n = len(a)
        ma, mb = sum(a) / n, sum(b) / n
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        da = math.sqrt(sum((x - ma) ** 2 for x in a))
        db = math.sqrt(sum((y - mb) ** 2 for y in b))
        if da == 0 or db == 0:
            return 0.0
        return num / (da * db)

    # rough significance: |r| > 1.96/sqrt(n-3) approx for large n
    n = len(ys)
    thresh = 1.96 / math.sqrt(max(1, n - 3))
    corrs = {}
    sig = []
    for name, xs in feats.items():
        r = pearson([float(x) for x in xs], ys)
        corrs[name] = {
            "r": round(r, 6),
            "abs_r": round(abs(r), 6),
            "approx_sig_threshold": round(thresh, 6),
            "significant_rough": abs(r) > thresh,
        }
        if abs(r) > thresh:
            sig.append(name)

    # effect size if any sig: top vs bottom quintile of predicted popularity proxy
    effect = None
    if sig:
        # use strongest |r| feature
        best = max(sig, key=lambda k: abs(corrs[k]["r"]))
        xs = feats[best]
        paired = sorted(zip(xs, [int(r[7]) for r in rows], [float(r[8] or 0) for r in rows]))
        q = max(1, len(paired) // 5)
        low = paired[:q]  # low feature
        high = paired[-q:]
        # if r>0, high feature = more winners = popular
        rsign = corrs[best]["r"]
        if rsign > 0:
            unpop, pop = low, high
        else:
            unpop, pop = high, low
        avg_prize_unpop = sum(p for _, _, p in unpop) / len(unpop)
        avg_prize_pop = sum(p for _, _, p in pop) / len(pop)
        avg_w_unpop = sum(w for _, w, _ in unpop) / len(unpop)
        avg_w_pop = sum(w for _, w, _ in pop) / len(pop)
        effect = {
            "feature": best,
            "r": corrs[best]["r"],
            "unpop_avg_winners": round(avg_w_unpop, 4),
            "pop_avg_winners": round(avg_w_pop, 4),
            "unpop_avg_prize_per_game": round(avg_prize_unpop, 2),
            "pop_avg_prize_per_game": round(avg_prize_pop, 2),
            "prize_ratio_unpop_over_pop": round(
                avg_prize_unpop / avg_prize_pop, 4
            )
            if avg_prize_pop > 0
            else None,
        }

    return {
        "status": "OK",
        "prefer_tier": prefer_tier,
        "n": n,
        "correlations": corrs,
        "signal_vars_significant": sig,
        "effect": effect,
        "note": "유의는 |r|>1.96/sqrt(n-3) 근사. 다중비교 보정 없음.",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    init_testlotto_db()
    tagged = _load_tagged_sets()
    draws = load_draws()

    A1 = audit_brains_static()
    A2 = pair_overlap_last_n(tagged, draws, 100)
    A3 = ablation_last_n(tagged, draws, 100)
    A4 = review_leak_trace()
    # mean by brain last 100 for leak suspicion
    use = [d for d in draws if len(tagged.get(int(d["draw_no"]), [])) >= 5][-100:]
    brain_means = defaultdict(list)
    for d in use:
        actual = sorted_nums(d)
        by = defaultdict(list)
        for e in tagged[int(d["draw_no"])]:
            by[e["brain"]].append(e["nums"])
        for b, ss in by.items():
            brain_means[b].append(hit_mean(ss, actual))
    A4["mean_last100_by_brain"] = {
        b: {
            "mean": round(mean_std(v)[0], 6),
            "ci95": bootstrap_mean_ci(v),
            "n": len(v),
        }
        for b, v in brain_means.items()
    }
    A4["review_higher_than_stat_markov"] = (
        A4["mean_last100_by_brain"].get("review", {}).get("mean", 0)
        > max(
            A4["mean_last100_by_brain"].get("stat", {}).get("mean", 0),
            A4["mean_last100_by_brain"].get("markov", {}).get("mean", 0),
        )
    )

    A5 = filter_audit(draws)
    A5["tier1_source"] = read_tier1_body()

    B0 = unpopular_data_availability()
    B1 = unpopular_signal_if_available(B0)

    payload = {
        "ok": True,
        "readonly": True,
        "A1_brain_inventory": A1,
        "A2_overlap": A2,
        "A3_ablation": A3,
        "A4_review_leak": A4,
        "A5_filters": {
            k: v for k, v in A5.items() if k != "tier1_source"
        },
        "A5_tier1_source": A5["tier1_source"],
        "B0_data_availability": B0,
        "B1_signal": B1,
    }
    OUT.joinpath("audit_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # compact print without huge source
    compact = dict(payload)
    compact.pop("A5_tier1_source", None)
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    print("WROTE", OUT / "audit_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
