# -*- coding: utf-8 -*-
"""K-ANALOG — 유사 과거 회차 검색·archive-next 집계 (READ-ONLY)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.testlotto.features.draw_features import ac_value, consecutive_pairs, odd_even_ratio

# 2차 회의 norm_spec SSOT
NORM_SPEC: dict[str, float | int] = {
    "sum_div": 270,
    "odd_div": 6,
    "lmh_div": 6,
    "ac_div": 10,
    "consec_div": 3,
    "l1_dims": 7,
    "score_w_jaccard": 0.55,
    "score_w_pattern": 0.45,
    "min_overlap": 2,
    "pattern_sim_rescue": 0.85,
    "top_k": 15,
    "chain_window": 8,
}

UI_DISCLAIMER = (
    "역사 유사 장면 · 설명용 · 1등 확률을 높이지 않음 · "
    "next_draw는 analog 회차의 실제 다음 추첨(관측)이며 미래 예측 보장 없음"
)


def draw_nums(row: dict) -> list[int]:
    return sorted(int(row[f"num{k}"]) for k in range(1, 7))


def pattern_vec(nums: list[int]) -> list[float]:
    odd, _ = odd_even_ratio(nums)
    lmh = [
        sum(1 for n in nums if 1 <= n <= 15),
        sum(1 for n in nums if 16 <= n <= 30),
        sum(1 for n in nums if 31 <= n <= 45),
    ]
    ns = NORM_SPEC
    return [
        sum(nums) / float(ns["sum_div"]),
        odd / float(ns["odd_div"]),
        lmh[0] / float(ns["lmh_div"]),
        lmh[1] / float(ns["lmh_div"]),
        lmh[2] / float(ns["lmh_div"]),
        ac_value(nums) / float(ns["ac_div"]),
        consecutive_pairs(nums) / float(ns["consec_div"]),
    ]


def pattern_sim(a: list[int], b: list[int]) -> float:
    va, vb = pattern_vec(a), pattern_vec(b)
    l1 = sum(abs(x - y) for x, y in zip(va, vb))
    return max(0.0, 1.0 - l1 / float(NORM_SPEC["l1_dims"]))


def find_analogs(
    base_nums: list[int],
    past_rows: list[dict],
    *,
    top_k: int | None = None,
    min_overlap: int | None = None,
) -> list[dict[str, Any]]:
    """base_nums 와 유사한 과거 회차 (past_rows = draw_no < base)."""
    k = top_k if top_k is not None else int(NORM_SPEC["top_k"])
    mo = min_overlap if min_overlap is not None else int(NORM_SPEC["min_overlap"])
    base_set = set(base_nums)
    base_pv = pattern_vec(base_nums)
    rescue = float(NORM_SPEC["pattern_sim_rescue"])
    wj = float(NORM_SPEC["score_w_jaccard"])
    wp = float(NORM_SPEC["score_w_pattern"])

    candidates: list[dict[str, Any]] = []
    for row in past_rows:
        nums = draw_nums(row)
        overlap = len(base_set & set(nums))
        jaccard = overlap / 6.0
        psim = pattern_sim(base_nums, nums)
        via_a = overlap >= mo
        via_b = psim >= rescue
        if not (via_a or via_b):
            continue
        score = wj * jaccard + wp * psim
        candidates.append(
            {
                "draw_no": int(row["draw_no"]),
                "nums": nums,
                "overlap": overlap,
                "jaccard": round(jaccard, 4),
                "pattern_sim": round(psim, 4),
                "score": round(score, 4),
            }
        )
    candidates.sort(key=lambda x: (-x["score"], -x["overlap"], -x["draw_no"]))
    return candidates[:k]


def _next_row(draw_by_no: dict[int, dict], analog_no: int) -> dict | None:
    return draw_by_no.get(analog_no + 1)


def _pick_top6(counter: Counter, exclude: set[int] | None = None) -> list[int]:
    ex = exclude or set()
    nums = [n for n, _ in counter.most_common(45) if n not in ex]
    return sorted(nums[:6])


def predict_from_analogs(
    base_nums: list[int],
    analogs: list[dict[str, Any]],
    draw_by_no: dict[int, dict],
    method: str,
    *,
    target_draw_no: int,
) -> list[int]:
    """analog+1 관측으로 6개 예측 (보너스 제외). target_draw_no 미만만 사용."""
    obs: list[tuple[float, list[int]]] = []
    base_set = set(base_nums)
    for a in analogs:
        an = int(a["draw_no"])
        nxt_no = an + 1
        if nxt_no >= target_draw_no:
            continue
        nxt = _next_row(draw_by_no, an)
        if not nxt:
            continue
        nums = draw_nums(nxt)
        obs.append((float(a["score"]), nums))

    if not obs:
        return sorted(base_nums)  # fallback: base 그대로(진단용)

    if method == "M_freq":
        c: Counter = Counter()
        for _, nums in obs:
            c.update(nums)
        return _pick_top6(c)

    if method == "M_weighted":
        c = Counter()
        for sc, nums in obs:
            for n in nums:
                c[n] += sc
        return _pick_top6(c)

    if method == "M_overlap3":
        c = Counter()
        for a in analogs:
            if int(a["overlap"]) < 3:
                continue
            an = int(a["draw_no"])
            if an + 1 >= target_draw_no:
                continue
            nxt = _next_row(draw_by_no, an)
            if not nxt:
                continue
            sc = float(a["score"])
            for n in draw_nums(nxt):
                c[n] += sc
        if not c:
            return predict_from_analogs(base_nums, analogs, draw_by_no, "M_weighted", target_draw_no=target_draw_no)
        return _pick_top6(c)

    if method == "M_anchor_pair":
        c = Counter()
        for sc, nums in obs:
            for anchor in base_nums:
                for n in nums:
                    if n == anchor:
                        continue
                    if n in base_set:
                        continue
                    c[n] += sc
        return _pick_top6(c, exclude=set()) or _pick_top6(Counter(n for _, nums in obs for n in nums))

    if method == "M_positional":
        """정렬 자리별: base[j]와 analog[j] 같으면 analog+1[j] 가중."""
        c = Counter()
        base_s = sorted(base_nums)
        for a in analogs:
            an = int(a["draw_no"])
            if an + 1 >= target_draw_no:
                continue
            nxt = _next_row(draw_by_no, an)
            if not nxt:
                continue
            analog_s = sorted(a["nums"])
            nxt_s = draw_nums(nxt)
            sc = float(a["score"])
            for j in range(6):
                if analog_s[j] == base_s[j]:
                    c[nxt_s[j]] += sc
        picked = _pick_top6(c)
        if len(picked) >= 6:
            return picked
        # 부족하면 weighted로 채움
        return predict_from_analogs(base_nums, analogs, draw_by_no, "M_weighted", target_draw_no=target_draw_no)

    if method == "M_greedy_pair":
        """탐욕: 1위 번호 후 co-occur 쌍 가중 확장."""
        c = Counter()
        for sc, nums in obs:
            for n in nums:
                c[n] += sc
        if not c:
            return sorted(base_nums)
        first = c.most_common(1)[0][0]
        chosen = {first}
        while len(chosen) < 6:
            pc = Counter()
            for sc, nums in obs:
                if not any(n in chosen for n in nums):
                    continue
                for n in nums:
                    if n not in chosen:
                        pc[n] += sc
            if not pc:
                for n, _ in c.most_common():
                    if n not in chosen:
                        chosen.add(n)
                        if len(chosen) >= 6:
                            break
                break
            chosen.add(pc.most_common(1)[0][0])
        return sorted(chosen)

    if method == "M_overlap2":
        c = Counter()
        for a in analogs:
            if int(a["overlap"]) < 2:
                continue
            an = int(a["draw_no"])
            if an + 1 >= target_draw_no:
                continue
            nxt = _next_row(draw_by_no, an)
            if not nxt:
                continue
            sc = float(a["score"])
            for n in draw_nums(nxt):
                c[n] += sc
        if not c:
            return predict_from_analogs(
                base_nums, analogs, draw_by_no, "M_weighted", target_draw_no=target_draw_no
            )
        return _pick_top6(c)

    if method == "M_overlap4":
        c = Counter()
        for a in analogs:
            if int(a["overlap"]) < 4:
                continue
            an = int(a["draw_no"])
            if an + 1 >= target_draw_no:
                continue
            nxt = _next_row(draw_by_no, an)
            if not nxt:
                continue
            sc = float(a["score"])
            for n in draw_nums(nxt):
                c[n] += sc
        if not c:
            return predict_from_analogs(
                base_nums, analogs, draw_by_no, "M_overlap3", target_draw_no=target_draw_no
            )
        return _pick_top6(c)

    if method == "M_b_route":
        """pattern_sim≥0.85 구제 루트만 (2차 회의 B-only)."""
        c = Counter()
        rescue = float(NORM_SPEC["pattern_sim_rescue"])
        for a in analogs:
            if float(a["pattern_sim"]) < rescue:
                continue
            an = int(a["draw_no"])
            if an + 1 >= target_draw_no:
                continue
            nxt = _next_row(draw_by_no, an)
            if not nxt:
                continue
            sc = float(a["pattern_sim"])
            for n in draw_nums(nxt):
                c[n] += sc
        if not c:
            return predict_from_analogs(
                base_nums, analogs, draw_by_no, "M_weighted", target_draw_no=target_draw_no
            )
        return _pick_top6(c)

    if method == "M_ov_bucket":
        """겹침 tier별 2D: overlap 가중 × score."""
        c = Counter()
        for a in analogs:
            an = int(a["draw_no"])
            if an + 1 >= target_draw_no:
                continue
            nxt = _next_row(draw_by_no, an)
            if not nxt:
                continue
            ov = int(a["overlap"])
            w = float(a["score"]) * (ov / 6.0)
            for n in draw_nums(nxt):
                c[n] += w
        return _pick_top6(c)

    if method == "M_exclude_base":
        """base 번호 제외·신규 번호만 (AI: carry-out)."""
        c = Counter()
        for sc, nums in obs:
            for n in nums:
                if n not in base_set:
                    c[n] += sc
        picked = _pick_top6(c)
        if len(picked) >= 6:
            return picked
        return predict_from_analogs(
            base_nums, analogs, draw_by_no, "M_weighted", target_draw_no=target_draw_no
        )

    if method == "M_chain8":
        """W=8 직전 chain 패턴 유사도 가중 (3차원: analog×chain)."""
        c = Counter()
        base_no = target_draw_no - 1
        for a in analogs:
            an = int(a["draw_no"])
            if an + 1 >= target_draw_no:
                continue
            nxt = _next_row(draw_by_no, an)
            if not nxt:
                continue
            chain_w = _chain_pattern_sim(base_no, an, draw_by_no, window=8)
            w = float(a["score"]) * (0.5 + 0.5 * chain_w)
            for n in draw_nums(nxt):
                c[n] += w
        if not c:
            return predict_from_analogs(
                base_nums, analogs, draw_by_no, "M_weighted", target_draw_no=target_draw_no
            )
        return _pick_top6(c)

    if method == "M_ensemble":
        """freq+weighted+ov_bucket 다수결 2차 투표."""
        votes: Counter = Counter()
        for sub in ("M_freq", "M_weighted", "M_ov_bucket"):
            pred = predict_from_analogs(
                base_nums, analogs, draw_by_no, sub, target_draw_no=target_draw_no
            )
            for n in pred:
                votes[n] += 1
        return _pick_top6(votes)

    raise ValueError(f"unknown method: {method}")


def matched_count(pred: list[int], actual: list[int]) -> int:
    return len(set(pred) & set(actual))


def _chain_pattern_sim(
    base_draw_no: int,
    analog_draw_no: int,
    draw_by_no: dict[int, dict],
    *,
    window: int = 8,
) -> float:
    """base 직전 W회 vs analog 직전 W회 패턴 벡터 평균 유사도."""
    def _avg_vec(start: int) -> list[float] | None:
        acc = [0.0] * 7
        cnt = 0
        for d in range(start - window, start):
            row = draw_by_no.get(d)
            if not row:
                continue
            v = pattern_vec(draw_nums(row))
            for i, x in enumerate(v):
                acc[i] += x
            cnt += 1
        if cnt == 0:
            return None
        return [x / cnt for x in acc]

    vb = _avg_vec(base_draw_no)
    va = _avg_vec(analog_draw_no)
    if vb is None or va is None:
        return 0.0
    l1 = sum(abs(x - y) for x, y in zip(vb, va))
    return max(0.0, 1.0 - l1 / float(NORM_SPEC["l1_dims"]))


def _psim_bin(v: float) -> str:
    if v < 0.85:
        return "lt0.85"
    if v < 0.90:
        return "0.85-0.90"
    if v < 0.95:
        return "0.90-0.95"
    return "ge0.95"


def _conditional_hint(top1: dict | None, chain8: float) -> dict:
    """MULTIDIM 벤치 기반 UI 힌트 — 예측·확률↑ 아님."""
    if not top1:
        return {
            "tier": "none",
            "label": "유사 후보 없음",
            "note": "과거 데이터에서 norm_spec 조건을 만족하는 analog가 없습니다.",
        }
    ov = int(top1["overlap"])
    ps = float(top1["pattern_sim"])
    ps_bin = _psim_bin(ps)
    ch_hi = chain8 >= 0.85

    if ps >= 0.95 and ov < 4:
        return {
            "tier": "weak",
            "label": "패턴-only 주의",
            "note": "pattern_sim≥0.95 단독 구간은 735회 벤치에서 평균 적중 열위(0.69 vs random 0.78). B-only 함정.",
        }
    if ov >= 4 and ps_bin == "0.85-0.90" and ch_hi:
        return {
            "tier": "context",
            "label": "설명 강조 구간",
            "note": "겹침4 + pattern 0.85–0.90 + chain8≥0.85: 735회에서 archive-next 관측이 random보다 나을 가능성(n=144). 예측·확률↑ 아님.",
        }
    if ov >= 4:
        return {
            "tier": "neutral",
            "label": "겹침4 유사",
            "note": "TOP1 겹침4는 735회에서 analog 평균(0.816)이 random(0.799)에 근소 우위. 전체 예측 엔진으로는 미지지.",
        }
    return {
        "tier": "neutral",
        "label": "일반 유사",
        "note": "겹침3 이하 다수 구간은 random 대비 열위. analog+1은 관측·맥락 설명용.",
    }


BENCH_VERDICT = {
    "overall": "735회 walk-forward: analog 집계 6방법 모두 random(0.816) 평균 미달",
    "match_dist": "0·1·2개 적중이 98%+ — 3개+만 보면 random과 구분 안 됨",
    "use_case": "예측 엔진 No · 역사 유사 장면+analog+1 관측 설명 Yes",
    "source": "docs/benchmarks/20260728_KANALOG_multidim_500.json",
}


def build_analog_report(draw_no: int) -> dict[str, Any]:
    """K-ANALOG-1 — 유사 과거 회차 + analog+1 관측 (READ-ONLY)."""
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        target_row = conn.execute(
            "SELECT * FROM lotto_draws WHERE draw_no = ?", (draw_no,)
        ).fetchone()
        if not target_row:
            return {"error": f"{draw_no}회 당첨 데이터 없음", "draw_no": draw_no}
        target = dict(target_row)
        rows = conn.execute(
            "SELECT * FROM lotto_draws WHERE draw_no <= ? ORDER BY draw_no",
            (draw_no,),
        ).fetchall()
    finally:
        conn.close()

    draw_by_no = {int(dict(r)["draw_no"]): dict(r) for r in rows}
    target_nums = draw_nums(target)
    target_bonus = int(target.get("bonus") or 0)
    past = _get_draws_before(draw_no)

    candidates_raw = find_analogs(target_nums, past, top_k=10_000)
    b_only = sum(1 for c in candidates_raw if c["overlap"] < int(NORM_SPEC["min_overlap"]))
    overlap2_plus = sum(1 for c in candidates_raw if c["overlap"] >= 2)
    top = find_analogs(target_nums, past)

    chain_w = int(NORM_SPEC["chain_window"])
    enriched: list[dict[str, Any]] = []
    for c in top:
        a = int(c["draw_no"])
        pre = [
            int(d["draw_no"])
            for d in past
            if int(d["draw_no"]) < a
        ][-chain_w:]
        nxt_no = a + 1
        nxt_row = draw_by_no.get(nxt_no)
        chain8 = _chain_pattern_sim(draw_no, a, draw_by_no, window=chain_w)
        enriched.append(
            {
                **c,
                "draw_date": draw_by_no.get(a, {}).get("draw_date") or "",
                "bonus": int(draw_by_no.get(a, {}).get("bonus") or 0),
                "via": (
                    "A+B"
                    if c["overlap"] >= int(NORM_SPEC["min_overlap"])
                    and c["pattern_sim"] >= float(NORM_SPEC["pattern_sim_rescue"])
                    else (
                        "A"
                        if c["overlap"] >= int(NORM_SPEC["min_overlap"])
                        else "B"
                    )
                ),
                "chain_pre_draws": pre,
                "chain8_sim": round(chain8, 4),
                "next_draw": {
                    "draw_no": nxt_no,
                    "found": nxt_row is not None,
                    "nums": draw_nums(nxt_row) if nxt_row else [],
                    "bonus": int(nxt_row.get("bonus") or 0) if nxt_row else None,
                    "label": "해당 analog 회차의 실제 다음 추첨(관측)",
                },
            }
        )

    top1 = enriched[0] if enriched else None
    chain8_top = float(top1["chain8_sim"]) if top1 else 0.0

    return {
        "task": "K-ANALOG-1",
        "draw_no": draw_no,
        "target_nums": target_nums,
        "target_bonus": target_bonus,
        "norm_spec": dict(NORM_SPEC),
        "candidate_total": len(candidates_raw),
        "b_only_count": b_only,
        "b_only_ratio": round(b_only / len(candidates_raw), 4) if candidates_raw else 0.0,
        "overlap2_plus_count": overlap2_plus,
        "top_k": enriched,
        "top1_summary": (
            {
                "draw_no": top1["draw_no"],
                "overlap": top1["overlap"],
                "pattern_sim": top1["pattern_sim"],
                "chain8_sim": top1["chain8_sim"],
                "score": top1["score"],
            }
            if top1
            else None
        ),
        "conditional_hint": _conditional_hint(top1, chain8_top),
        "ui_disclaimer": UI_DISCLAIMER,
        "bench_verdict": BENCH_VERDICT,
        "patch_gate": {
            "conditional_go": len(candidates_raw) <= 800 and overlap2_plus >= 5,
            "reason": "후보 과다/과소 시 norm 조정",
        },
    }
