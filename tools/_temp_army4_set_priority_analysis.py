# -*- coding: utf-8
"""4군 v13 — 뇌×세트(1~5) 독립 적중 + 적중 좋은 세트 우선 조합 분석 (READ-ONLY)."""
from __future__ import annotations

import itertools
import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from pathlib import Path

DB = Path(r"d:\ROK21\data\lotto4.db")
OUT_DIR = Path(r"d:\MONEY lol\My_Drive_Sync\커서보고서")
OUT_MD = OUT_DIR / "20260718_4군_v13_뇌셋트_독립적중_우선조합_분석.md"
OUT_JSON = OUT_DIR / "20260718_4군_v13_뇌셋트_독립적중_우선조합_분석.json"

SEVEN_BRAINS = (
    "v13_struct",
    "v13_seq",
    "v13_diversity",
    "v13_evolution",
    "v13_gap",
    "v13_ev",
    "v13_ensemble",
)
BRAIN_LABEL = {
    "v13_struct": "📐 구조예측",
    "v13_seq": "🧬 시퀀스",
    "v13_diversity": "🌈 다양성",
    "v13_evolution": "🧬 진화",
    "v13_gap": "📉 갭분석",
    "v13_ev": "💎 기대값",
    "v13_ensemble": "🧠 앙상블",
}
N_DRAWS = 20
EXAMPLE_DRAW = 1232


def tier(matched: int, bonus_hit: bool) -> str:
    if matched == 6:
        return "1등"
    if matched == 5 and bonus_hit:
        return "2등"
    if matched == 5:
        return "3등"
    if matched == 4:
        return "4등"
    if matched == 3:
        return "5등"
    return "낙첨"


def set_no_from_conf(conf: float) -> int:
    return int(round((conf - 0.5) / 0.01)) + 1


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    return conn


def eligible_draws(conn: sqlite3.Connection, n: int) -> list[int]:
    rows = conn.execute(
        """
        SELECT p.target_draw_no AS dn, p.brain_tag, COUNT(*) AS c
        FROM lotto_predictions_army4 p
        INNER JOIN lotto_draws d ON d.draw_no = p.target_draw_no
        WHERE p.brain_tag IN ({tags})
        GROUP BY p.target_draw_no, p.brain_tag
        HAVING c >= 5
        """.format(tags=",".join("?" * len(SEVEN_BRAINS))),
        SEVEN_BRAINS,
    ).fetchall()
    by: dict[int, set[str]] = defaultdict(set)
    for r in rows:
        by[int(r["dn"])].add(str(r["brain_tag"]))
    full = sorted(dn for dn, tags in by.items() if tags >= set(SEVEN_BRAINS))
    return full[-n:]


def load_win(conn: sqlite3.Connection, draw_no: int) -> tuple[set[int], int]:
    r = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=?",
        (draw_no,),
    ).fetchone()
    return {int(r[i]) for i in range(6)}, int(r["bonus"])


def load_brain_sets(conn: sqlite3.Connection, draw_no: int) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {b: [] for b in SEVEN_BRAINS}
    rows = conn.execute(
        """
        SELECT brain_tag, num1,num2,num3,num4,num5,num6,
               confidence, matched_count, bonus_matched, reasoning
        FROM lotto_predictions_army4
        WHERE target_draw_no=? AND brain_tag IN ({tags})
        ORDER BY brain_tag, confidence
        """.format(tags=",".join("?" * len(SEVEN_BRAINS))),
        (draw_no, *SEVEN_BRAINS),
    ).fetchall()
    for r in rows:
        tag = str(r["brain_tag"])
        nums = tuple(sorted(int(r[f"num{i}"]) for i in range(1, 7)))
        out[tag].append(
            {
                "set_no": set_no_from_conf(float(r["confidence"] or 0.5)),
                "nums": nums,
                "confidence": float(r["confidence"] or 0),
                "matched_count": int(r["matched_count"]) if r["matched_count"] is not None else -1,
                "bonus_matched": int(r["bonus_matched"] or 0),
            }
        )
    return out


def score_nums(nums: tuple[int, ...], win: set[int], bonus: int) -> tuple[int, bool, str]:
    matched = len(set(nums) & win)
    bonus_hit = bonus in nums
    return matched, bonus_hit, tier(matched, bonus_hit)


def wf_best_sets(
    history: dict[int, dict[str, list[dict]]],
    history_wins: dict[int, tuple[set[int], int]],
    brain: str,
    prior_draws: list[int],
    top_n: int = 2,
) -> list[int]:
    """과거 세트별 평균 적중 상위 top_n 세트 번호(1~5) 반환."""
    if not prior_draws:
        return [1]
    sums = {i: 0.0 for i in range(1, 6)}
    cnts = {i: 0 for i in range(1, 6)}
    for dn in prior_draws:
        win, bonus = history_wins[dn]
        for s in history[dn][brain]:
            sn = s["set_no"]
            m, _, _ = score_nums(s["nums"], win, bonus)
            sums[sn] += m
            cnts[sn] += 1
    avgs = [(sn, sums[sn] / cnts[sn] if cnts[sn] else 0) for sn in range(1, 6)]
    avgs.sort(key=lambda x: (-x[1], -x[0]))
    return [sn for sn, _ in avgs[:top_n]]


def pick_numbers_from_sets(
    sets: list[dict],
    good_set_nos: list[int],
    k_per_set: int,
    win: set[int] | None = None,
    oracle: bool = False,
) -> list[int]:
    """좋은 세트에서만 k개씩 번호 추출."""
    picked: list[int] = []
    by_set = {s["set_no"]: s for s in sets}
    for sn in good_set_nos:
        s = by_set.get(sn)
        if not s:
            continue
        nums = s["nums"]
        if oracle and win is not None:
            ordered = sorted(nums, key=lambda n: (1 if n in win else 0, n), reverse=True)
        else:
            ordered = list(nums)
        for n in ordered[:k_per_set]:
            if n not in picked:
                picked.append(n)
    return picked


def best_six_from_pool(pool: list[int], win: set[int], bonus: int) -> tuple[int, bool, str]:
    if len(pool) <= 6:
        matched = len(set(pool) & win)
        bonus_hit = bonus in pool
        return matched, bonus_hit, tier(matched, bonus_hit)
    best = (0, False, "낙첨")
    for comb in itertools.combinations(pool, 6):
        m = len(set(comb) & win)
        bh = bonus in comb
        t = tier(m, bh)
        if m > best[0] or (m == best[0] and bh and not best[1]):
            best = (m, bh, t)
    return best


def format_nums(nums: tuple[int, ...]) -> str:
    return " ".join(f"{n:02d}" for n in nums)


def main() -> None:
    conn = connect()
    draws = eligible_draws(conn, N_DRAWS)

    history: dict[int, dict[str, list[dict]]] = {}
    wins: dict[int, tuple[set[int], int]] = {}
    for dn in draws:
        history[dn] = load_brain_sets(conn, dn)
        wins[dn] = load_win(conn, dn)

    # ── 1) brain×set 집계 ──
    bs_stats: dict[str, dict] = {}
    for b in SEVEN_BRAINS:
        for sn in range(1, 6):
            key = f"{b}|set{sn}"
            bs_stats[key] = {"hits": [], "tiers": Counter()}

    per_draw_detail: list[dict] = []

    for dn in draws:
        win, bonus = wins[dn]
        draw_entry = {"draw_no": dn, "win": sorted(win), "bonus": bonus, "brains": {}}
        for b in SEVEN_BRAINS:
            brain_rows = []
            for s in history[dn][b]:
                m, bh, t = score_nums(s["nums"], win, bonus)
                key = f"{b}|set{s['set_no']}"
                bs_stats[key]["hits"].append(m)
                bs_stats[key]["tiers"][t] += 1
                brain_rows.append(
                    {
                        "set_no": s["set_no"],
                        "nums": list(s["nums"]),
                        "matched": m,
                        "tier": t,
                        "bonus_hit": bh,
                    }
                )
            draw_entry["brains"][b] = brain_rows
        per_draw_detail.append(draw_entry)

    ranking = []
    for b in SEVEN_BRAINS:
        for sn in range(1, 6):
            key = f"{b}|set{sn}"
            hits = bs_stats[key]["hits"]
            ranking.append(
                {
                    "brain": b,
                    "label": BRAIN_LABEL[b],
                    "set_no": sn,
                    "avg_match": round(statistics.mean(hits), 3),
                    "max_match": max(hits),
                    "dist": Counter(hits),
                    "tiers": dict(bs_stats[key]["tiers"]),
                    "prize_plus": sum(
                        bs_stats[key]["tiers"].get(t, 0) for t in ("5등", "4등", "3등", "2등", "1등")
                    ),
                }
            )
    ranking.sort(key=lambda x: (-x["avg_match"], -x["prize_plus"]))

    # 뇌별 최고 세트
    brain_best_set: dict[str, dict] = {}
    for b in SEVEN_BRAINS:
        rows = [r for r in ranking if r["brain"] == b]
        brain_best_set[b] = max(rows, key=lambda x: (x["avg_match"], x["prize_plus"]))

    # ── 2) 조합 전략 비교 ──
    strategies = [
        "naive_set1_1each",
        "smart_wf_top1_1each",
        "smart_wf_top2_1each",
        "smart_wf_top1_2each",
        "smart_wf_top2_1each_oracle",
        "pool_top2_all_oracle6",
    ]
    combo_log: dict[str, list[dict]] = {s: [] for s in strategies}

    for idx, dn in enumerate(draws):
        win, bonus = wins[dn]
        prior = draws[:idx]
        wf1 = {b: wf_best_sets(history, wins, b, prior, 1) for b in SEVEN_BRAINS}
        wf2 = {b: wf_best_sets(history, wins, b, prior, 2) for b in SEVEN_BRAINS}

        # naive: 각 뇌 set1에서 1개(정렬 첫번째)
        pool_naive = []
        for b in SEVEN_BRAINS:
            s1 = next(x for x in history[dn][b] if x["set_no"] == 1)
            pool_naive.append(s1["nums"][0])
        m, bh, t = best_six_from_pool(pool_naive, win, bonus)
        combo_log["naive_set1_1each"].append({"draw_no": dn, "matched": m, "tier": t, "pool": pool_naive})

        # smart top1 set, 1 num each
        pool_s1 = []
        for b in SEVEN_BRAINS:
            picked = pick_numbers_from_sets(history[dn][b], wf1[b], 1)
            pool_s1.extend(picked)
        m, bh, t = best_six_from_pool(pool_s1, win, bonus)
        combo_log["smart_wf_top1_1each"].append({"draw_no": dn, "matched": m, "tier": t, "pool": pool_s1})

        # smart top2 sets, 1 num each (max 14 nums → pick 6)
        pool_s2 = []
        for b in SEVEN_BRAINS:
            pool_s2.extend(pick_numbers_from_sets(history[dn][b], wf2[b], 1))
        m, bh, t = best_six_from_pool(pool_s2, win, bonus)
        combo_log["smart_wf_top2_1each"].append({"draw_no": dn, "matched": m, "tier": t, "pool": pool_s2})

        # smart top1 set, 2 nums each
        pool_2 = []
        for b in SEVEN_BRAINS:
            pool_2.extend(pick_numbers_from_sets(history[dn][b], wf1[b], 2))
        m, bh, t = best_six_from_pool(pool_2, win, bonus)
        combo_log["smart_wf_top1_2each"].append({"draw_no": dn, "matched": m, "tier": t, "pool": pool_2})

        # oracle from top2 sets
        pool_o = []
        for b in SEVEN_BRAINS:
            pool_o.extend(pick_numbers_from_sets(history[dn][b], wf2[b], 1, win, oracle=True))
        m, bh, t = best_six_from_pool(pool_o, win, bonus)
        combo_log["smart_wf_top2_1each_oracle"].append({"draw_no": dn, "matched": m, "tier": t, "pool": pool_o})

        # pool: top2 sets all nums (up to 12 per brain...) - use top2 sets, all 6 nums, oracle pick 6
        pool_all = []
        for b in SEVEN_BRAINS:
            for s in history[dn][b]:
                if s["set_no"] in wf2[b]:
                    pool_all.extend(s["nums"])
        pool_all = list(dict.fromkeys(pool_all))
        m, bh, t = best_six_from_pool(pool_all, win, bonus)
        combo_log["pool_top2_all_oracle6"].append({"draw_no": dn, "matched": m, "tier": t, "pool_size": len(pool_all)})

    combo_summary = []
    labels = {
        "naive_set1_1each": "단순: 매뇌 set1에서 1개씩",
        "smart_wf_top1_1each": "우선: 과거 최고 세트1개×뇌당1번호",
        "smart_wf_top2_1each": "우선: 과거 상위2세트×뇌당1번호",
        "smart_wf_top1_2each": "우선: 최고세트×뇌당2번호",
        "smart_wf_top2_1each_oracle": "우선+오라클(상위2세트)",
        "pool_top2_all_oracle6": "상위2세트 번호풀→6개 최적",
    }
    for key in strategies:
        rows = combo_log[key]
        ms = [r["matched"] for r in rows]
        tc = Counter(r["tier"] for r in rows)
        combo_summary.append(
            {
                "key": key,
                "label": labels[key],
                "avg_match": round(statistics.mean(ms), 3),
                "prize_rate": round(sum(1 for m in ms if m >= 3) / len(ms), 3),
                "tier_counts": dict(tc),
            }
        )
    combo_summary.sort(key=lambda x: (-x["avg_match"], -x["prize_rate"]))

    conn.close()

    # ── 1232 예시 블록 ──
    ex = next(d for d in per_draw_detail if d["draw_no"] == EXAMPLE_DRAW)
    win_ex = set(ex["win"])
    bonus_ex = ex["bonus"]

    payload = {
        "draws": draws,
        "example_draw": EXAMPLE_DRAW,
        "ranking_top20": ranking[:20],
        "brain_best_set": brain_best_set,
        "combo_summary": combo_summary,
        "per_draw_detail": per_draw_detail,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 4군 v13 — 뇌×세트(1~5) 독립 적중 + 적중 좋은 세트 우선 조합",
        "",
        f"- 분석: **{draws[0]}~{draws[-1]}** ({len(draws)}회) · DB `lotto4.db` READ-ONLY",
        f"- 7뇌×5세트=**35세트/회차** · 각 세트 6번호를 **당첨번호와 독립 비교**",
        "",
        "---",
        "",
        f"## 📌 예시 {EXAMPLE_DRAW}회 (형이 준 형식)",
        "",
        f"🎰 당첨: **{'/'.join(f'{n:02d}' for n in sorted(win_ex))}** · 보너스 **{bonus_ex:02d}**",
        "",
    ]
    for b in SEVEN_BRAINS:
        lines.append(f"### {BRAIN_LABEL[b]}")
        lines.append("")
        for row in ex["brains"][b]:
            sn = row["set_no"]
            nums = format_nums(tuple(row["nums"]))
            lines.append(
                f"- **{sn}셋트** `{nums}` → **{row['matched']}개 적중** ({row['tier']})"
            )
        lines.append("")

    lines += [
        "---",
        "",
        "## 1. 뇌×세트별 20회 평균 적중 TOP 15",
        "",
        "| 순위 | 뇌 | 세트 | 평균 | 최대 | 5등+ | 0|1|2|3|4|5|6 |",
        "|------|-----|------|------|------|------|------------|",
    ]
    for i, r in enumerate(ranking[:15], 1):
        d = r["dist"]
        dist_str = "|".join(str(d.get(x, 0)) for x in range(7))
        lines.append(
            f"| {i} | {r['label']} | set{r['set_no']} | {r['avg_match']} | {r['max_match']} "
            f"| {r['prize_plus']} | {dist_str} |"
        )

    lines += [
        "",
        "## 2. 뇌별 — 20회 중 가장 잘 맞는 세트",
        "",
        "| 뇌 | 최고세트 | 평균적중 | 5등+ 횟수 |",
        "|-----|---------|---------|----------|",
    ]
    for b in SEVEN_BRAINS:
        r = brain_best_set[b]
        lines.append(f"| {r['label']} | set{r['set_no']} | {r['avg_match']} | {r['prize_plus']} |")

    lines += [
        "",
        "## 3. 조합 전략 — 「잘 맞는 세트 번호 우선」 vs 단순",
        "",
        "| 전략 | 설명 | 평균적중 | 5등+ |",
        "|------|------|---------|------|",
    ]
    for s in combo_summary:
        tc = s["tier_counts"]
        p = sum(tc.get(t, 0) for t in ("5등", "4등", "3등", "2등", "1등"))
        lines.append(f"| {s['label']} | | {s['avg_match']} | {p}/{len(draws)} ({s['prize_rate']*100:.0f}%) |")

    naive = next(s for s in combo_summary if s["key"] == "naive_set1_1each")
    smart = next(s for s in combo_summary if s["key"] == "smart_wf_top2_1each")
    lines += [
        "",
        f"- **단순(set1)** vs **우선(상위2세트)**: {naive['avg_match']} → {smart['avg_match']} (Δ {smart['avg_match']-naive['avg_match']:+.3f})",
        "",
        "## 4. 해석",
        "",
        "- **각 셋트 6번호 full 채점** = 형 예시와 동일 (1~6개 적중, 3+=5등 이상)",
        "- **우선 전략** = 5세트 전부 쓰지 않고, **과거 적중 좋았던 1~2세트**에서만 1~2개 번호 추출 후 7뇌 조합",
        "- 오라클(사후 최적 선택) 제외 시 실제 규칙으로는 5등+ 거의 없음 → **세트 선별도 단기 재현 어려움**",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: {OUT_MD}")
    print(f"OK: {OUT_JSON}")


if __name__ == "__main__":
    main()
