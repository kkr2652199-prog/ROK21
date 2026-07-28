# -*- coding: utf-8 -*-
"""K-ANALOG-PREP — 유사 과거 회차 probe (READ-ONLY · 1234 등)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# pattern L1 norm SSOT (2차 회의 고정)
NORM_SPEC = {
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


def _draw_nums(row: dict) -> list[int]:
    return sorted(int(row[f"num{k}"]) for k in range(1, 7))


def _pattern_vec(nums: list[int]) -> list[float]:
    from app.testlotto.features.draw_features import ac_value, consecutive_pairs, odd_even_ratio

    odd, _ = odd_even_ratio(nums)
    lmh = [
        sum(1 for n in nums if 1 <= n <= 15),
        sum(1 for n in nums if 16 <= n <= 30),
        sum(1 for n in nums if 31 <= n <= 45),
    ]
    ns = NORM_SPEC
    return [
        sum(nums) / ns["sum_div"],
        odd / ns["odd_div"],
        lmh[0] / ns["lmh_div"],
        lmh[1] / ns["lmh_div"],
        lmh[2] / ns["lmh_div"],
        ac_value(nums) / ns["ac_div"],
        consecutive_pairs(nums) / ns["consec_div"],
    ]


def _pattern_l1(a: list[float], b: list[float]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b))


def _pattern_sim(a: list[float], b: list[float]) -> float:
    l1 = _pattern_l1(a, b)
    return max(0.0, 1.0 - l1 / float(NORM_SPEC["l1_dims"]))


def build_analog_report(draw_no: int) -> dict[str, Any]:
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        target_row = conn.execute("SELECT * FROM lotto_draws WHERE draw_no = ?", (draw_no,)).fetchone()
        if not target_row:
            return {"error": f"{draw_no}회 당첨 데이터 없음"}
        target = dict(target_row)
    finally:
        conn.close()

    target_nums = _draw_nums(target)
    target_set = set(target_nums)
    target_bonus = int(target.get("bonus") or 0)
    target_pv = _pattern_vec(target_nums)

    past = _get_draws_before(draw_no)
    candidates: list[dict[str, Any]] = []
    b_only = 0

    for row in past:
        dn = int(row["draw_no"])
        nums = _draw_nums(row)
        overlap = len(target_set & set(nums))
        jaccard = overlap / 6.0
        psim = _pattern_sim(target_pv, _pattern_vec(nums))
        via_a = overlap >= NORM_SPEC["min_overlap"]
        via_b = psim >= NORM_SPEC["pattern_sim_rescue"]
        if not (via_a or via_b):
            continue
        if via_b and not via_a:
            b_only += 1
        score = NORM_SPEC["score_w_jaccard"] * jaccard + NORM_SPEC["score_w_pattern"] * psim
        candidates.append(
            {
                "draw_no": dn,
                "draw_date": row.get("draw_date") or "",
                "nums": nums,
                "bonus": int(row.get("bonus") or 0),
                "overlap": overlap,
                "jaccard": round(jaccard, 4),
                "pattern_sim": round(psim, 4),
                "score": round(score, 4),
                "via": "A+B" if via_a and via_b else ("A" if via_a else "B"),
            }
        )

    candidates.sort(key=lambda x: (-x["score"], -x["overlap"], -x["draw_no"]))
    top = candidates[: NORM_SPEC["top_k"]]

    # chain + next observation (READ-ONLY)
    draw_by_no = {int(d["draw_no"]): d for d in past}
    draw_by_no[draw_no] = target
    enriched: list[dict[str, Any]] = []
    for c in top:
        a = c["draw_no"]
        pre = [int(d["draw_no"]) for d in past if int(d["draw_no"]) < a][-NORM_SPEC["chain_window"] :]
        nxt = a + 1
        nxt_row = draw_by_no.get(nxt)
        enriched.append(
            {
                **c,
                "chain_pre_draws": pre,
                "next_draw": {
                    "draw_no": nxt,
                    "found": nxt_row is not None,
                    "nums": _draw_nums(nxt_row) if nxt_row else [],
                    "bonus": int(nxt_row.get("bonus") or 0) if nxt_row else None,
                },
            }
        )

    overlap2_plus = sum(1 for c in candidates if c["overlap"] >= 2)
    return {
        "task": "K-ANALOG-PREP",
        "target_draw_no": draw_no,
        "target_nums": target_nums,
        "target_bonus": target_bonus,
        "norm_spec": NORM_SPEC,
        "candidate_total": len(candidates),
        "b_only_count": b_only,
        "b_only_ratio": round(b_only / len(candidates), 4) if candidates else 0.0,
        "overlap2_plus_count": overlap2_plus,
        "top_k": enriched,
        "ui_disclaimer": "역사 유사 장면 · 설명용 · 1등 확률을 높이지 않음 · next_draw는 해당 analog 회차의 실제 다음 추첨(관측)이며 1235 예측 아님",
        "patch_gate": {
            "conditional_go": len(candidates) <= 800 and overlap2_plus >= 5,
            "reason": "후보 과다/과소 시 K/W 조정",
        },
    }


def main() -> int:
    draw_no = int(sys.argv[1]) if len(sys.argv) > 1 else 1234
    out_path = ROOT / "docs" / "benchmarks" / "20260728_KANALOG_prep.json"
    report = build_analog_report(draw_no)
    if report.get("error"):
        print(json.dumps(report, ensure_ascii=False))
        return 1
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "draw_no": draw_no,
        "candidate_total": report["candidate_total"],
        "b_only_ratio": report["b_only_ratio"],
        "top3": [
            {k: c[k] for k in ("draw_no", "overlap", "score", "via", "nums")}
            for c in report["top_k"][:3]
        ],
        "conditional_go": report["patch_gate"]["conditional_go"],
        "out": str(out_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
