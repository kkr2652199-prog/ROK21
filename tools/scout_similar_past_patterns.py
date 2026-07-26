# -*- coding: utf-8 -*-
"""
유사 과거 회차 스카우트 (컨닝 금지).

목표(형):
  '지금의 패턴의 번호는 몇 회차에 비슷하게 존재했다'
  → target 이전 draws만 보고 구조 유사 회차를 찾고,
  그 회차들의 당첨 번호 분포를 요약한다.

유사 정의(프로토):
  - odd_even 일치
  - high_low 일치
  - sum 차이 ≤ 12
  - AC 차이 ≤ 2

출력: docs/benchmarks/.../similar_past_scout.json
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260726_형계획_세트합집합_메타선별" / "similar_past_scout.json"


def feats(nums: list[int]) -> dict:
    s = sorted(nums)
    odd = sum(1 for n in s if n % 2)
    high = sum(1 for n in s if n >= 23)
    gaps = [s[i + 1] - s[i] for i in range(5)]
    ac = len({abs(s[j] - s[i]) for i in range(6) for j in range(i + 1, 6)}) - 5
    return {
        "sum": sum(s),
        "odd_even": f"{odd}:{6 - odd}",
        "high_low": f"{high}:{6 - high}",
        "ac": ac,
        "gap_mean": sum(gaps) / 5.0,
    }


def similar(a: dict, b: dict) -> bool:
    return (
        a["odd_even"] == b["odd_even"]
        and a["high_low"] == b["high_low"]
        and abs(a["sum"] - b["sum"]) <= 12
        and abs(a["ac"] - b["ac"]) <= 2
    )


def main() -> None:
    conn = sqlite3.connect(str(DB))
    rows = conn.execute(
        "SELECT draw_no, num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
    ).fetchall()
    conn.close()
    draws = [(int(r[0]), [int(x) for x in r[1:7]]) for r in rows]

    # 최근 20회: 각 target의 '직전 회차 패턴'으로 유사과거 찾기 (예측일 시점 프록시)
    # 실제 운영에서는 예측 직전까지의 확정 패턴/후보 구조를 넣는다.
    samples = []
    recent = draws[-20:]
    for i, (dn, nums) in enumerate(draws):
        if dn < recent[0][0]:
            continue
        if i == 0:
            continue
        # 컨닝 금지: 유사검색은 target 이전만. 패턴 기준은 직전 확정 회차.
        prev_dn, prev_nums = draws[i - 1]
        pat = feats(prev_nums)
        before = draws[:i]  # target 이전 (+직전 포함하되 자기자신 제외는 prev만 기준으로 검색)
        hits = []
        for pdn, pnums in before:
            if pdn == prev_dn:
                continue
            if similar(pat, feats(pnums)):
                hits.append({"draw_no": pdn, "nums": pnums})
        # 유사 과거들의 '다음 회차 당첨'이 있으면 그 분포도(학습용 힌트, target 자체는 제외)
        next_answers: list[list[int]] = []
        by_dn = {d: n for d, n in draws}
        for h in hits:
            nxt = h["draw_no"] + 1
            if nxt < dn and nxt in by_dn:  # target 이전의 다음회만
                next_answers.append(by_dn[nxt])
        freq = Counter(n for ans in next_answers for n in ans)
        samples.append(
            {
                "target_draw": dn,
                "pattern_source_draw": prev_dn,
                "pattern": pat,
                "similar_past_count": len(hits),
                "similar_past_sample": hits[:8],
                "past_next_answer_count": len(next_answers),
                "past_next_top15": freq.most_common(15),
                "actual_target": nums,  # 평가용(리포트). 운영 예측 시점에는 미사용
                "overlap_top15_vs_actual": len(set(n for n, _ in freq.most_common(15)) & set(nums)),
            }
        )

    # 요약 통계 (평가용 — 과거 숙제)
    overlaps = [s["overlap_top15_vs_actual"] for s in samples]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "no_peek_rule": "유사검색·past_next는 target 이전만. actual_target은 숙제 평가용 필드.",
        "n_samples": len(samples),
        "avg_similar_past_count": round(sum(s["similar_past_count"] for s in samples) / max(1, len(samples)), 2),
        "avg_overlap_top15_vs_actual": round(sum(overlaps) / max(1, len(overlaps)), 4) if overlaps else None,
        "samples": samples,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in payload if k != "samples"}, ensure_ascii=False, indent=2))
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
