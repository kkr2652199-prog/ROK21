# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-SUM-SELECT FAIL · NEXT=HOLD · V2 배선 유지 · WIRE금지 · SUM-SELECT재탕금지

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-SUM-SELECT | **FAIL** · hit 전게이트 false · WIRE금지 |
| WIRE-V2 | ENABLED=**True** (유지) |
| BAND-SELECT | FAIL (직전) |
| EV-POP | FAIL |
| SETNO-HITMAP | FAIL |
| SETPACK-TOP6 | FAIL |
| TUNE | FAIL |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-SUM-SELECT** | V2쿼터 고정·티켓 합(이론138) 슬롯 재선택 | **FAIL** |
| **K-BAND-SELECT** | V2쿼터 고정·티켓 LMH 번호대역 슬롯 재선택 | FAIL |
| **K-EV-POP** | V2쿼터 고정·저인기(EV) 슬롯 재선택 | FAIL |
| **K-SETNO-HITMAP** | V2쿼터 고정·뇌내 set_no 재배치 | FAIL (의미임계) |
| **K-SETPACK-TOP6** | 출현횟수 top6 → set1 재조립 | FAIL |
| **K-MARKOV-TUNE** | decay/steps/top 27격자 | FAIL |
| **K-MARKOV-WIRE-V2** | set_no 쿼터 | PASS |

---

## 2) K-SUM-SELECT 핵심

| 항목 | 값 |
|------|-----|
| 풀 | testlotto_brain_review · draw 53~1234 · n=**1182** |
| V2 pin ge3 / mean / mean_sum | **0.1447** / **1.7504** / **137.1042** |
| best hit vs V2 | **없음** (전 정책 ge3 ≤ V2) |
| 최근접 | all_sum_far · ge3=**0.1404** · Δ=**-0.0043** · mean=**1.7174** |
| all_sum_near | ge3=**0.1277** · Δ=**-0.0170** · mean_sum_score=**0.8584** |
| spearman(sum_score,matched) @v2 | **0.0230** |
| hit_WIRE (Δge3≥0.005 · p<0.05) | **FAIL** |
| recommended_next | **없음** (HOLD·V2유지·SUM-SELECT재탕금지) |

근거: docs/benchmarks/20260729_KSUM_select.json

### 후보 기각 (선정 과정)

| 후보 | 기각 |
|------|------|
| K-ODD-SELECT | BAND `all_odd_bal` 부차정책으로 이미 FAIL |
| K-ACFORM-SELECT | STRUCT/pattern 인접 |
| K-ATTACK-SEARCH | 재예측↑ · GATHER/SETPACK 인접 |

### 재탕금지 (누적)

SETPACK-TOP6 · MARKOV-TUNE · SETNO-HITMAP · EV-POP · BAND-SELECT · conf-quota구WIRE · HISIM/STRUCT/COVER wheel · GATHER전면 · **SUM-SELECT**

---

## 3) 다음

K-ATTACK-HOLD — SUM-SELECT WIRE금지·재탕금지 · V2 유지 · 형·커서 다음 축 1건 재선정 (승인 필요)

---

## 4) 산출물

- tools/_k_sum_select_survey.py
- docs/benchmarks/20260729_KSUM_select.json
- reports/20260729_KSUM_SELECT.md
- My_Drive_Sync/커서보고서/20260729_KSUM_SELECT.md
