# K-TRANSITION-FULL 팩트체크 — 1234→1235 조·분석 vs rolling 벤치 (2026-08-05)

- **목적:** 형·조·분석(1234→1235)과 `K-TRANSITION-FULL` 산출물 일치 여부 검증
- **SSOT:** `docs/benchmarks/20260805_KTRANSITION_FULL.json` · `data/lotto_testlotto.db`
- wire=`False` · READ-ONLY

---

## 결론

| 구분 | 판정 |
|------|------|
| 패턴 아이디어 | ✅ 동일 — 유사 과거(2+ 겹침) → 다음 회차 빈도 + carry |
| 핵심 숫자 | ✅ carry 분포·1234→1235 `[15,43]`·유사 212건 일치 |
| 측정 방식 | ⚠️ 조·분석=단건·정성 / K-TRANSITION=rolling·top15·Δ판정 |
| 1234 단건 성과 | ⚠️ top15 hit=**2** (baseline 2.0) — “대박” 아님 |

---

## 일치 수치 (DB 재계산 = JSON)

### carry 전수 (draw 2~1235, n=1234)

| carry | 건수 |
|-------|------|
| 0 | 477 |
| 1 | 523 |
| 2 | 208 |
| 3 | 24 |
| 4 | 2 |

### 1234→1235

- 1234: `[1,15,19,31,35,43]`
- 1235: `[6,7,11,15,39,43]`
- carry: **2** · `[15, 43]`
- JSON: `current_1235_carry=2` · `carry_numbers_1235=[15,43]` ✅

### 유사 회차 (1234 기준 sim_k2)

- 과거 1..1233 중 2+ 공통: **212건** ✅
- top15 → 1235 hit_count: **2** (적중 7, 15)

---

## 불일치·주의

1. **top20 정성 vs top15 정량:** 조·분석에서 “6,7,15,39가 TOP에” → top15 기준은 **7,15만** 적중.
2. **STRONG 의미:** rolling mean_hit=**2.172** (Δ=+0.172) — 회차당 +0.17개 수준의 **미세 신호**.
3. **carry 전이 (1236):** carry=2 다음 최빈은 **1개(48.8%)**, 2개 연속은 **15.9%** — JSON `pred_1236_carry_dist`와 동일.

---

## 로드맵 위치

- **완료:** K-TRANSITION-FULL rolling (101~1235) · STRONG
- **진행:** 패턴 검증·형 확인 (본 문서 + 무작위 표본)
- **다음:** stat 뇌 교체 **설계** (형 GO 전 wire/auto-tune 금지)

- prior: `docs/benchmarks/20260805_KTRANSITION_FULL.json`
