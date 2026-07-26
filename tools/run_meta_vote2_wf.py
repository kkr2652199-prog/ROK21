"""Vote≥2 메타 프로토타입 — walk-forward vs best 단일세트 (컨닝 금지).

규칙:
- 예측 세트는 DB에 저장된 과거 산출물을 사용 (이미 target 이전 draws로 생성된 것)
- 메타 선별·유사과거 가중은 오직 draw_no < target 인 lotto_draws 만 사용
- random.choices 수정 없음

출력:
  tools/_meta_vote2_wf_result.json
  docs/benchmarks/20260726_형계획_세트합집합_메타선별/vote2_wf_summary.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import (  # noqa: E402
    ending_digits,
    odd_even_ratio,
    sorted_nums,
    sum_range,
)
from app.testlotto.models import get_lotto_db, init_testlotto_db  # noqa: E402
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402

OUT_TOOLS = ROOT / "tools" / "_meta_vote2_wf_result.json"
OUT_BENCH = (
    ROOT
    / "docs"
    / "benchmarks"
    / "20260726_형계획_세트합집합_메타선별"
    / "vote2_wf_summary.json"
)
BRAINS = ("stat", "markov", "review")


def _parse_sets(js: str | None) -> list[list[int]]:
    if not js:
        return []
    try:
        data = json.loads(js)
    except json.JSONDecodeError:
        return []
    out: list[list[int]] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "nums" in item:
                out.append([int(x) for x in item["nums"]])
            elif isinstance(item, list) and len(item) >= 6:
                out.append([int(x) for x in item[:6]])
    return out


def _load_sets_by_draw() -> dict[int, list[list[int]]]:
    """target_draw_no -> list of predicted 6-number sets (up to 15)."""
    init_testlotto_db()
    conn = get_lotto_db()
    by: dict[int, list[list[int]]] = defaultdict(list)
    try:
        draw_nos = {r[0] for r in conn.execute("SELECT draw_no FROM lotto_draws")}
        for r in conn.execute(
            """
            SELECT target_draw_no, brain_tag, num1,num2,num3,num4,num5,num6
            FROM lotto_predictions
            WHERE brain_tag IN ('stat','markov','review')
            ORDER BY target_draw_no, brain_tag, id
            """
        ):
            td = int(r["target_draw_no"])
            if td not in draw_nos:
                continue
            by[td].append(
                [int(r["num1"]), int(r["num2"]), int(r["num3"]),
                 int(r["num4"]), int(r["num5"]), int(r["num6"])]
            )

        # fill gaps from review predicted_sets_json
        for r in conn.execute(
            """
            SELECT draw_no, brain_tag, predicted_sets_json
            FROM testlotto_brain_review
            WHERE brain_tag IN ('stat','markov','review')
            """
        ):
            td = int(r["draw_no"])
            if td not in draw_nos:
                continue
            # crude: if already >=5 sets for this brain from predictions, skip add
            # we don't track per-brain here; only top up if total < 5
            if len(by[td]) >= 15:
                continue
            for s in _parse_sets(r["predicted_sets_json"]):
                if len(by[td]) >= 15:
                    break
                by[td].append(s)
    finally:
        conn.close()
    return dict(by)


def _load_draws() -> list[dict[str, Any]]:
    conn = get_lotto_db()
    try:
        rows = conn.execute("SELECT * FROM lotto_draws ORDER BY draw_no").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _draws_before(all_draws: list[dict], target: int) -> list[dict]:
    """컨닝 금지: target 미만만."""
    return [d for d in all_draws if int(d["draw_no"]) < target]


def _hist_freq(draws_before: list[dict]) -> Counter:
    c: Counter = Counter()
    for d in draws_before:
        c.update(sorted_nums(d))
    return c


def _structure_vec(nums: list[int]) -> tuple:
    odd, _ = odd_even_ratio(nums)
    s = sum_range(nums)
    ends = tuple(sorted(set(ending_digits(nums))))
    low = sum(1 for n in nums if n <= 15)
    mid = sum(1 for n in nums if 16 <= n <= 30)
    high = sum(1 for n in nums if n >= 31)
    return (odd, s // 10, low, mid, high, ends[:4])  # coarse


def _similar_past_number_boost(
    draws_before: list[dict],
    *,
    k: int = 25,
) -> Counter:
    """직전 회차 구조와 비슷한 과거 당첨에서 나온 번호 가산 (target 이전만)."""
    boost: Counter = Counter()
    if len(draws_before) < 3:
        return boost
    prev = sorted_nums(draws_before[-1])
    prev_v = _structure_vec(prev)
    scored: list[tuple[float, list[int]]] = []
    for d in draws_before[:-1]:
        nums = sorted_nums(d)
        v = _structure_vec(nums)
        # simple distance
        dist = (
            abs(v[0] - prev_v[0])
            + abs(v[1] - prev_v[1])
            + abs(v[2] - prev_v[2])
            + abs(v[3] - prev_v[3])
            + abs(v[4] - prev_v[4])
            + (0 if v[5] == prev_v[5] else 1)
        )
        scored.append((dist, nums))
    scored.sort(key=lambda x: x[0])
    for _dist, nums in scored[:k]:
        boost.update(nums)
    return boost


def assemble_vote2(
    sets: list[list[int]],
    draws_before: list[dict],
    *,
    min_vote: int = 2,
    use_similar_past: bool = True,
) -> dict[str, Any]:
    """Vote≥min_vote 후보에서 6수 조립. 부족하면 vote1으로 보충."""
    vote: Counter = Counter()
    for s in sets:
        vote.update(set(int(n) for n in s))  # per-set unique

    hist = _hist_freq(draws_before)
    sim = _similar_past_number_boost(draws_before) if use_similar_past else Counter()

    def rank_key(n: int) -> tuple:
        return (vote[n], sim.get(n, 0), hist.get(n, 0), -n)

    primary = [n for n, v in vote.items() if v >= min_vote]
    primary.sort(key=rank_key, reverse=True)

    picked: list[int] = []
    for n in primary:
        if len(picked) >= 6:
            break
        picked.append(n)

    if len(picked) < 6:
        secondary = [n for n, v in vote.items() if v == 1 and n not in picked]
        secondary.sort(key=rank_key, reverse=True)
        for n in secondary:
            if len(picked) >= 6:
                break
            picked.append(n)

    # still short: fill by hist among 1..45 not picked (rare)
    if len(picked) < 6:
        rest = [n for n in range(1, 46) if n not in picked]
        rest.sort(key=lambda n: (hist.get(n, 0), sim.get(n, 0)), reverse=True)
        for n in rest:
            if len(picked) >= 6:
                break
            picked.append(n)

    return {
        "nums": sorted(picked[:6]),
        "vote_ge2_count": len(primary),
        "vote_hist": {str(k): int(v) for k, v in sorted(vote.items(), key=lambda x: -x[1])[:20]},
        "used_similar_past": use_similar_past,
    }


def _best_single_match(sets: list[list[int]], actual: list[int], bonus: int) -> dict[str, Any]:
    best = {"matched_count": -1, "bonus_matched": 0, "nums": []}
    for s in sets:
        sc = score_predicted_set(s, actual, bonus)
        if sc["matched_count"] > best["matched_count"] or (
            sc["matched_count"] == best["matched_count"]
            and sc["bonus_matched"] > best["bonus_matched"]
        ):
            best = {**sc, "nums": sorted(s)}
    return best


def run_wf(*, min_vote: int = 2) -> dict[str, Any]:
    all_draws = _load_draws()
    sets_by = _load_sets_by_draw()
    rows: list[dict[str, Any]] = []

    for d in all_draws:
        td = int(d["draw_no"])
        sets = sets_by.get(td) or []
        if len(sets) < 5:
            continue
        # 컨닝 금지
        before = _draws_before(all_draws, td)
        if not before:
            continue

        actual = sorted_nums(d)
        bonus = int(d["bonus"])
        best = _best_single_match(sets, actual, bonus)

        meta_plain = assemble_vote2(sets, before, min_vote=min_vote, use_similar_past=False)
        meta_sim = assemble_vote2(sets, before, min_vote=min_vote, use_similar_past=True)
        sc_plain = score_predicted_set(meta_plain["nums"], actual, bonus)
        sc_sim = score_predicted_set(meta_sim["nums"], actual, bonus)

        uniq = set()
        for s in sets:
            uniq |= set(s)
        cover = len(set(actual) & uniq)

        rows.append(
            {
                "draw_no": td,
                "n_sets": len(sets),
                "pool_unique": len(uniq),
                "cover_actual": cover,
                "best_match": best["matched_count"],
                "best_bonus": best["bonus_matched"],
                "vote2_match": sc_plain["matched_count"],
                "vote2_bonus": sc_plain["bonus_matched"],
                "vote2_sim_match": sc_sim["matched_count"],
                "vote2_sim_bonus": sc_sim["bonus_matched"],
                "vote_ge2_pool": meta_plain["vote_ge2_count"],
                "delta_vs_best": sc_plain["matched_count"] - best["matched_count"],
                "delta_sim_vs_best": sc_sim["matched_count"] - best["matched_count"],
            }
        )

    n = len(rows)
    if n == 0:
        return {"ok": False, "error": "no rows", "n": 0}

    def avg(key: str) -> float:
        return round(sum(r[key] for r in rows) / n, 4)

    summary = {
        "ok": True,
        "n_draws": n,
        "min_vote": min_vote,
        "no_peek": True,
        "avg_best_single": avg("best_match"),
        "avg_vote2": avg("vote2_match"),
        "avg_vote2_similar_past": avg("vote2_sim_match"),
        "avg_cover_oracle": avg("cover_actual"),
        "vote2_beats_best": sum(1 for r in rows if r["delta_vs_best"] > 0),
        "vote2_ties_best": sum(1 for r in rows if r["delta_vs_best"] == 0),
        "vote2_loses_best": sum(1 for r in rows if r["delta_vs_best"] < 0),
        "vote2_sim_beats_best": sum(1 for r in rows if r["delta_sim_vs_best"] > 0),
        "vote2_ge3": sum(1 for r in rows if r["vote2_match"] >= 3),
        "best_ge3": sum(1 for r in rows if r["best_match"] >= 3),
        "vote2_ge4": sum(1 for r in rows if r["vote2_match"] >= 4),
        "best_ge4": sum(1 for r in rows if r["best_match"] >= 4),
        "mean_delta_vs_best": avg("delta_vs_best"),
        "mean_delta_sim_vs_best": avg("delta_sim_vs_best"),
        "avg_vote_ge2_pool_size": avg("vote_ge2_pool"),
        "window_1132_1234": _window_stats(rows, 1132, 1234),
        "note": (
            "메타는 오라클 합집합(cover)이 아님. Vote≥2+역사빈도(+유사과거)로 6수 조립. "
            "유사과거는 target 이전 당첨 구조만 사용."
        ),
    }
    return {"summary": summary, "rows": rows}


def _window_stats(rows: list[dict], start: int, end: int) -> dict[str, Any]:
    w = [r for r in rows if start <= r["draw_no"] <= end]
    if not w:
        return {"n": 0}
    n = len(w)
    return {
        "n": n,
        "avg_best": round(sum(r["best_match"] for r in w) / n, 4),
        "avg_vote2": round(sum(r["vote2_match"] for r in w) / n, 4),
        "avg_vote2_sim": round(sum(r["vote2_sim_match"] for r in w) / n, 4),
        "mean_delta": round(sum(r["delta_vs_best"] for r in w) / n, 4),
        "mean_delta_sim": round(sum(r["delta_sim_vs_best"] for r in w) / n, 4),
    }


def main() -> int:
    result = run_wf(min_vote=2)
    OUT_TOOLS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_BENCH.parent.mkdir(parents=True, exist_ok=True)
    OUT_BENCH.write_text(
        json.dumps(result.get("summary", result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result.get("summary", result), ensure_ascii=False, indent=2))
    print("WROTE", OUT_TOOLS)
    print("WROTE", OUT_BENCH)
    return 0 if result.get("summary", {}).get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
