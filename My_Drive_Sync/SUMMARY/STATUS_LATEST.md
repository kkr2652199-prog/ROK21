# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-GENDIV FAIL · NEXT=HOLD · V2 배선 유지 · WIRE금지 · GENDIV재탕금지

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-GENDIV | **FAIL** · corr/Q1 전게이트 false · WIRE금지 |
| WIRE-V2 | ENABLED=**True** (유지) |
| SUM-SELECT | FAIL (직전) |
| BAND-SELECT | FAIL |
| EV-POP | FAIL |
| SETNO-HITMAP | FAIL |
| SETPACK-TOP6 | FAIL |
| TUNE | FAIL |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-GENDIV** | 생성15풀 Jaccard/union ↔ V2적중 (`diversify_pick` 레버) · **슬롯재선택 아님** | **FAIL** |
| **K-SUM-SELECT** | V2쿼터 고정·티켓 합(이론138) 슬롯 재선택 | FAIL |
| **K-BAND-SELECT** | V2쿼터 고정·티켓 LMH 번호대역 슬롯 재선택 | FAIL |
| **K-EV-POP** | V2쿼터 고정·저인기(EV) 슬롯 재선택 | FAIL |
| **K-SETNO-HITMAP** | V2쿼터 고정·뇌내 set_no 재배치 | FAIL (의미임계) |
| **K-SETPACK-TOP6** | 출현횟수 top6 → set1 재조립 | FAIL |
| **K-MARKOV-TUNE** | decay/steps/top 27격자 | FAIL |
| **K-MARKOV-WIRE-V2** | set_no 쿼터 | PASS |

---

## 2) K-GENDIV 핵심

| 항목 | 값 |
|------|-----|
| 풀 | testlotto_brain_review · draw 53~1234 · n=**1182** |
| 발권 | V2 set_no_asc **고정** (대체점수 픽 없음) |
| 코드앵커 | `set_diversity.diversify_pick` · penalty=**0.85** · oversample=`max(3n,n+5)` |
| mean V2 Jac / pool Jac | **0.0884** / **0.0921** |
| best corr | v2_jac vs best **r=−0.0135** (p=0.64) |
| Q1(저Jac) ge3 | **0.1224** · Δ=**−0.0223** |
| Q1−Q5 ge3 | **−0.0344** (다양↑ → ge3 열세) |
| PASS | **FAIL** |
| recommended_next | **없음** (HOLD·V2유지·GENDIV재탕금지) |

근거: docs/benchmarks/20260729_KGENDIV_survey.json

### 후보 기각 (선정 과정)

| 후보 | 기각 |
|------|------|
| K-AUX-BLEND | V2 conf 미사용 · conf-quota 인접 |
| K-SETS-MIX15 | brain_review 뇌당5 · SETCOUNT/재생성 인접 |
| K-STATP | PATTERN2/STRUCT 인접 |

### 재탕금지 (누적)

SETPACK-TOP6 · MARKOV-TUNE · SETNO-HITMAP · EV-POP · BAND-SELECT · SUM-SELECT · conf-quota구WIRE · HISIM/STRUCT/COVER wheel · GATHER전면 · **GENDIV**

---

## 3) 다음

K-ATTACK-HOLD — GENDIV WIRE금지·재탕금지 · V2 유지 · 형·커서 다음 축 1건 재선정 (승인 필요) · **슬롯재선택 계열 지양**

---

## 4) 산출물

- tools/_k_gendiv_survey.py
- docs/benchmarks/20260729_KGENDIV_survey.json
- reports/20260729_KGENDIV.md
- My_Drive_Sync/커서보고서/20260729_KGENDIV.md
