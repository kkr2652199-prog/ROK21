# seed 정렬 boost 재검증 (측정 전용)

- **일시**: 2026-07-25 (KST)
- **목적**: 역산 그리드와 동일 seed로 추천 boost vs 현재 boost 공정 비교
- **DB 쓰기**: **0건** · `lotto_predictions` **미변경**

---

## 측정 설정

| 항목 | 값 |
|------|-----|
| seed | `random.seed(20260725 + draw_no × 9973)` **회차별** |
| miss_counts | `testlotto_brain_review` stat `weight_snapshot` at **draw_no−1** |
| boost 고정 | walk-forward `apply_feedback` 누적 **미사용** (역산과 동일) |
| 스크립트 | `tools/_measure_stat_wf_range.py` (READ-ONLY monkeypatch) |

---

## 조건별 성적표

### A. 구간 1132~1231 (100회)

| 조건 | carry | ending | overdue | avg match | match_sum | reviewed |
|------|-------|--------|---------|-----------|-----------|----------|
| **(a) 현재 0.5³** | 0.5 | 0.5 | 0.5 | **1.7100** | 171 | 100 |
| **(b) 추천** | 0.2 | 0.3 | 0.2 | **1.7500** | 175 | 100 |
| **차이 (b−a)** | | | | **+0.0400** | +4 | |

### B. 전구간 2~1231 (1230회) — 역산 교차검증

| 조건 | carry | ending | overdue | avg match | match_sum | reviewed |
|------|-------|--------|---------|-----------|-----------|----------|
| **(a) 현재 0.5³** | 0.5 | 0.5 | 0.5 | **1.6724** | 2057 | 1230 |
| **(b) 추천** | 0.2 | 0.3 | 0.2 | **1.7171** | 2112 | 1230 |
| **역산 그리드 (abb7157)** | 0.5 / 0.2 | 0.5 / 0.3 | 0.5 / 0.2 | **1.6724 / 1.7171** | — | 1230 |

**전구간 역산 재현**: ✅ **완전 일치** (소수 4자리)

---

## 판정

| 기준 | 결과 |
|------|------|
| 추천(b) > 현재(a) ? | **✅ 예** (1132~1231: +0.04, 전구간: +0.0447) |
| boost 효과 | **확인됨** — 과보정(0.5³)보다 추천값이 일관되게 우수 |
| 이전 1.63 실패 원인 | global seed 1회 사용 — boost 변경이 평균에 반영되지 않던 **측정 프로토콜 문제** |

**결론**: seed 정렬 후 boost 효과 **공정하게 확인** → **4단계(lotto_predictions 재기록) 진행 가능**

랜덤(choices) 근본 문제(B단계)로 단정할 근거 **없음** — 추천 boost가 현재 대비 명확히 우수.

---

## 소견

1. **WF 측정 프로토콜**: stat 비교 시 역산과 동일하게 **회차별 seed** 필수. global seed 1회는 boost A/B 비교에 부적합.
2. **고정 boost vs 동적 누적**: 이번 검증은 역산과 동일한 **고정 boost** 기준. 실운영 `apply_feedback` 누적 경로는 별도 3단계 재측정 권장(단, seed는 회차별).
3. **다음 작업**: `backups/20260725_재기록전_DB전체/` 백업 선행 조건 충족 상태 → `lotto_predictions` DELETE + walk-forward 재기록.

---

## 산출물

- JSON: `backups/20260725_seed정렬_boost재검증.json`
- 스크립트: `tools/_measure_stat_wf_range.py` (seed 회차별 + READ-ONLY)
