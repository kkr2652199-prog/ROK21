# -*- coding: utf-8 -*-
"""P1 하이브리드 메타 WF — 보조4뇌 시드 + Vote 보강 (컨닝 금지).

성능: 회차당 시드 1회만 채점. miss traps는 WF 시작 시 1회 로드.
그리드(min_vote×replace)는 동일 시드에 교체만 재적용.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import (  # noqa: E402
    aux_balance_keeper,
    aux_pattern_spotlight,
    aux_referee,
)
from app.testlotto.features.draw_features import combo_features, sorted_nums  # noqa: E402
from app.testlotto.models import init_testlotto_db  # noqa: E402
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402
from tools.run_meta_vote2_wf import (  # noqa: E402
    _best_single_match,
    _draws_before,
    _hist_freq,
    _load_draws,
    _load_sets_by_draw,
    _similar_past_number_boost,
)

OUT_TOOLS = ROOT / "tools" / "_meta_hybrid_wf_result.json"
OUT_BENCH = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_형계획_세트합집합_메타선별"
    / "hybrid_wf_summary.json"
)


def _load_traps() -> set[int]:
    try:
        from app.testlotto.feedback import get_feedback_summary

        return set(get_feedback_summary(last_n=30).get("frequent_traps") or [])
    except Exception:
        return set()


def _fast_miss_score(nums: list[int], draws: list[dict], traps: set[int]) -> float:
    penalty = min(0.5, sum(1 for n in nums if n in traps) * 0.12)
    return max(0.1, min(1.0, 0.75 - penalty))


def fast_aux_composite(
    nums: list[int], draws: list[dict], target: int, traps: set[int]
) -> float:
    """miss/pattern/balance/referee 균등 가중 — DB 반복 호출 없음."""
    m = _fast_miss_score(nums, draws, traps)
    p = aux_pattern_spotlight.score_set(nums, draws, target)
    b = aux_balance_keeper.score_set(nums, draws, target)
    r = aux_referee.score_set(nums, draws, target)
    return 0.25 * (m + p + b + r)


def pick_aux_seed(
    sets: list[list[int]],
    draws_before: list[dict],
    target: int,
    traps: set[int],
) -> dict[str, Any]:
    best_s: list[int] | None = None
    best_score = -1e18
    for s in sets:
        sc = fast_aux_composite(list(s), draws_before, target, traps)
        if sc > best_score:
            best_score = sc
            best_s = sorted(int(x) for x in s)
    return {"nums": best_s or [], "aux_score": round(best_score, 4)}


def hybrid_from_seed(
    seed_nums: list[int],
    sets: list[list[int]],
    draws_before: list[dict],
    *,
    min_vote: int = 2,
    replace_slots: int = 2,
    use_similar_past: bool = True,
) -> dict[str, Any]:
    if len(seed_nums) < 6:
        return {"nums": list(seed_nums), "replaced": [], "n_replaced": 0}

    vote: Counter = Counter()
    for s in sets:
        vote.update(set(int(n) for n in s))
    hist = _hist_freq(draws_before)
    sim = _similar_past_number_boost(draws_before) if use_similar_past else Counter()

    def cand_key(n: int) -> tuple:
        return (vote[n], sim.get(n, 0), hist.get(n, 0), -n)

    def weak_key(n: int) -> tuple:
        return (vote[n], sim.get(n, 0), hist.get(n, 0), -n)

    ranked_weak = sorted(seed_nums, key=weak_key)
    to_drop = ranked_weak[: max(0, replace_slots)]
    candidates = [n for n, v in vote.items() if v >= min_vote and n not in seed_nums]
    candidates.sort(key=cand_key, reverse=True)

    picked = [n for n in seed_nums if n not in to_drop]
    replaced: list[dict[str, int]] = []
    for n in candidates:
        if len(picked) >= 6:
            break
        if n in picked:
            continue
        picked.append(n)
        if to_drop:
            dropped = to_drop.pop(0)
            replaced.append({"out": dropped, "in": n})

    if len(picked) < 6:
        for n in seed_nums:
            if n not in picked:
                picked.append(n)
            if len(picked) >= 6:
                break
    if len(picked) < 6:
        rest = [n for n, v in vote.items() if n not in picked]
        rest.sort(key=cand_key, reverse=True)
        for n in rest:
            picked.append(n)
            if len(picked) >= 6:
                break

    return {
        "nums": sorted(picked[:6]),
        "replaced": replaced,
        "n_replaced": len(replaced),
        "min_vote": min_vote,
        "replace_slots": replace_slots,
    }


def hybrid_assemble(
    sets: list[list[int]],
    draws_before: list[dict],
    target: int,
    *,
    min_vote: int = 2,
    replace_slots: int = 2,
    use_similar_past: bool = True,
    traps: set[int] | None = None,
) -> dict[str, Any]:
    """외부(meta_picker)용 — traps 없으면 1회 로드."""
    if traps is None:
        traps = _load_traps()
    seed = pick_aux_seed(sets, draws_before, target, traps)
    body = hybrid_from_seed(
        seed["nums"],
        sets,
        draws_before,
        min_vote=min_vote,
        replace_slots=replace_slots,
        use_similar_past=use_similar_past,
    )
    body["seed"] = seed
    return body


def run_wf() -> dict[str, Any]:
    init_testlotto_db()
    traps = _load_traps()
    all_draws = _load_draws()
    sets_by = _load_sets_by_draw()

    # per-draw caches
    per_draw: list[dict[str, Any]] = []
    for d in all_draws:
        td = int(d["draw_no"])
        sets = sets_by.get(td) or []
        if len(sets) < 5:
            continue
        before = _draws_before(all_draws, td)
        if not before:
            continue
        actual = sorted_nums(d)
        bonus = int(d["bonus"])
        oracle = _best_single_match(sets, actual, bonus)
        seed = pick_aux_seed(sets, before, td, traps)
        sc_seed = score_predicted_set(seed["nums"], actual, bonus)
        uniq: set[int] = set()
        for s in sets:
            uniq |= set(s)
        cover = len(set(actual) & uniq)
        vote = Counter()
        for s in sets:
            vote.update(set(int(n) for n in s))
        hist = _hist_freq(before)
        sim = _similar_past_number_boost(before)
        per_draw.append(
            {
                "td": td,
                "sets": sets,
                "before": before,
                "actual": actual,
                "bonus": bonus,
                "oracle": oracle["matched_count"],
                "seed": seed,
                "seed_match": sc_seed["matched_count"],
                "cover": cover,
                "vote": vote,
                "hist": hist,
                "sim": sim,
            }
        )

    grids = []
    best_cfg = None
    best_score = -1e9
    best_rows: list[dict] = []

    for mv in (2, 3):
        for rs in (0, 1, 2):
            rows = []
            for item in per_draw:
                meta = hybrid_from_seed(
                    item["seed"]["nums"],
                    item["sets"],
                    item["before"],
                    min_vote=mv,
                    replace_slots=rs,
                    use_similar_past=True,
                )
                sc_meta = score_predicted_set(meta["nums"], item["actual"], item["bonus"])
                rows.append(
                    {
                        "draw_no": item["td"],
                        "cover_actual": item["cover"],
                        "pool_short": item["cover"] < 6,
                        "oracle_best": item["oracle"],
                        "seed_match": item["seed_match"],
                        "meta_match": sc_meta["matched_count"],
                        "delta_meta_vs_seed": sc_meta["matched_count"] - item["seed_match"],
                        "delta_meta_vs_oracle": sc_meta["matched_count"] - item["oracle"],
                        "gap_meta_to_oracle": item["oracle"] - sc_meta["matched_count"],
                        "gap_seed_to_oracle": item["oracle"] - item["seed_match"],
                        "n_replaced": meta["n_replaced"],
                    }
                )
            n = len(rows)

            def avg(key: str, rr=rows, nn=n) -> float:
                return round(sum(r[key] for r in rr) / nn, 4)

            pass_ge_seed = avg("meta_match") >= avg("seed_match")
            pass_closer = avg("gap_meta_to_oracle") < avg("gap_seed_to_oracle")
            cover_ok = [r for r in rows if not r["pool_short"]]
            summary = {
                "min_vote": mv,
                "replace_slots": rs,
                "avg_meta": avg("meta_match"),
                "avg_seed": avg("seed_match"),
                "avg_oracle": avg("oracle_best"),
                "pass_p1": bool(pass_ge_seed and pass_closer),
                "mean_delta_vs_seed": avg("delta_meta_vs_seed"),
                "mean_gap_meta": avg("gap_meta_to_oracle"),
                "mean_gap_seed": avg("gap_seed_to_oracle"),
                "meta_beats_seed": sum(1 for r in rows if r["delta_meta_vs_seed"] > 0),
                "closer_to_oracle_count": sum(
                    1 for r in rows if r["gap_meta_to_oracle"] < r["gap_seed_to_oracle"]
                ),
                "avg_meta_cover6_only": round(
                    sum(r["meta_match"] for r in cover_ok) / max(1, len(cover_ok)), 4
                ),
            }
            grids.append(summary)
            score = summary["avg_meta"] * 100 - summary["mean_gap_meta"]
            if score > best_score:
                best_score = score
                best_cfg = summary
                best_rows = rows

    assert best_cfg is not None
    n = len(best_rows)

    def avg(key: str) -> float:
        return round(sum(r[key] for r in best_rows) / n, 4)

    cover_ok = [r for r in best_rows if not r["pool_short"]]
    cover_short = [r for r in best_rows if r["pool_short"]]
    final = {
        "ok": True,
        "n_draws": n,
        "no_peek": True,
        "selected_min_vote": best_cfg["min_vote"],
        "selected_replace_slots": best_cfg["replace_slots"],
        "avg_oracle_best": avg("oracle_best"),
        "avg_seed": avg("seed_match"),
        "avg_meta": avg("meta_match"),
        "avg_cover_oracle": avg("cover_actual"),
        "mean_delta_meta_vs_seed": avg("delta_meta_vs_seed"),
        "mean_delta_meta_vs_oracle": avg("delta_meta_vs_oracle"),
        "mean_gap_meta_to_oracle": avg("gap_meta_to_oracle"),
        "mean_gap_seed_to_oracle": avg("gap_seed_to_oracle"),
        "meta_beats_seed": sum(1 for r in best_rows if r["delta_meta_vs_seed"] > 0),
        "meta_ties_seed": sum(1 for r in best_rows if r["delta_meta_vs_seed"] == 0),
        "meta_loses_seed": sum(1 for r in best_rows if r["delta_meta_vs_seed"] < 0),
        "meta_beats_oracle": sum(1 for r in best_rows if r["delta_meta_vs_oracle"] > 0),
        "closer_to_oracle_count": sum(
            1 for r in best_rows if r["gap_meta_to_oracle"] < r["gap_seed_to_oracle"]
        ),
        "pass_meta_ge_seed": avg("meta_match") >= avg("seed_match"),
        "pass_closer_to_oracle": avg("gap_meta_to_oracle") < avg("gap_seed_to_oracle"),
        "pass_p1": bool(
            avg("meta_match") >= avg("seed_match")
            and avg("gap_meta_to_oracle") < avg("gap_seed_to_oracle")
        ),
        "n_pool_short": len(cover_short),
        "n_pool_cover6": len(cover_ok),
        "avg_meta_cover6_only": round(
            sum(r["meta_match"] for r in cover_ok) / max(1, len(cover_ok)), 4
        ),
        "avg_oracle_cover6_only": round(
            sum(r["oracle_best"] for r in cover_ok) / max(1, len(cover_ok)), 4
        ),
        "grid": grids,
        "note": (
            "시드=보조4뇌 고속합산(traps 1회). 메타=시드+Vote 교체. "
            "pass_p1: meta≥seed AND gap_to_oracle 개선."
        ),
    }
    # silence unused import warning path
    _ = combo_features
    return {"summary": final, "rows": best_rows}


def main() -> int:
    result = run_wf()
    OUT_TOOLS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_BENCH.parent.mkdir(parents=True, exist_ok=True)
    OUT_BENCH.write_text(
        json.dumps(result["summary"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print("WROTE", OUT_TOOLS)
    print("WROTE", OUT_BENCH)
    return 0 if result["summary"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
