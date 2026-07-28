# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-AUX-BLEND FAIL · NEXT=HOLD · V2 배선 유지 · WIRE금지 · AUX-BLEND재탕금지

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-AUX-BLEND | **FAIL** · 전 blend/성분 상관 게이트 false · WIRE금지 |
| WIRE-V2 | ENABLED=**True** (유지) |
| GENDIV | FAIL (직전) |
| SUM-SELECT | FAIL |
| BAND-SELECT | FAIL |
| EV-POP | FAIL |
| SETNO-HITMAP | FAIL |
| SETPACK-TOP6 | FAIL |
| TUNE | FAIL |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-AUX-BLEND** | 발권전 AUX_WEIGHTS·`aux_score*40` 점수↔적중 · **슬롯재선택 아님** | **FAIL** |
| **K-GENDIV** | 생성15풀 Jaccard/union ↔ V2적중 (`diversify_pick` 레버) | FAIL |
| **K-SUM-SELECT** | V2쿼터 고정·티켓 합(이론138) 슬롯 재선택 | FAIL |
| **K-BAND-SELECT** | V2쿼터 고정·티켓 LMH 번호대역 슬롯 재선택 | FAIL |
| **K-EV-POP** | V2쿼터 고정·저인기(EV) 슬롯 재선택 | FAIL |
| **K-SETNO-HITMAP** | V2쿼터 고정·뇌내 set_no 재배치 | FAIL (의미임계) |
| **K-SETPACK-TOP6** | 출현횟수 top6 → set1 재조립 | FAIL |
| **K-MARKOV-TUNE** | decay/steps/top 27격자 | FAIL |
| **K-MARKOV-WIRE-V2** | set_no 쿼터 | PASS |

---

## 2) K-AUX-BLEND 핵심

| 항목 | 값 |
|------|-----|
| 풀 | testlotto_brain_review · draw 53~1234 · n=**1182** · pool=**17730** |
| 발권 | V2 set_no_asc **고정** (대체점수 픽 없음) |
| 코드앵커 | `coordinator.AUX_WEIGHTS=[0.25]*4` · `aux_score*40` |
| live 상관 | r=**0.0134** · p=0.075 |
| best blend | pattern_heavy r=**0.0152** · p=0.043 (|r|<0.03) |
| V2티켓 live aux | r=**0.0272** · p=0.037 (|r|<0.03) |
| miss/referee | **constant** (본 표본) |
| Q4/Q5 live ge3 | **0.1780** / **0.1561** (비단조) |
| PASS | **FAIL** |
| recommended_next | **없음** (HOLD·V2유지·AUX-BLEND재탕금지) |

근거: docs/benchmarks/20260729_KAUX_BLEND_survey.json

### 후보 기각 (선정 과정)

| 후보 | 기각 |
|------|------|
| K-SETS-MIX15 | brain_review 뇌당5 · SETCOUNT/재생성 인접 · V2 trunc 시 티켓동일 |
| K-AUX-THRESH | 슬롯재선택=금지 · BAND 기각 |
| K-STATP | PATTERN2/STRUCT 인접 |

### 재탕금지 (누적)

SETPACK-TOP6 · MARKOV-TUNE · SETNO-HITMAP · EV-POP · BAND-SELECT · SUM-SELECT · conf-quota구WIRE · HISIM/STRUCT/COVER wheel · GATHER전면 · GENDIV · **AUX-BLEND**

---

## 3) 다음

K-ATTACK-HOLD — AUX-BLEND WIRE금지·재탕금지 · V2 유지 · 형·커서 다음 직교축 1건 재선정 (승인 필요) · **슬롯재선택·GENDIV·AUX점수 재탕 지양**

---

## 4) 산출물

- tools/_k_aux_blend_survey.py
- docs/benchmarks/20260729_KAUX_BLEND_survey.json
- reports/20260729_KAUX_BLEND.md
- My_Drive_Sync/커서보고서/20260729_KAUX_BLEND.md
