# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-BAND-SELECT FAIL · NEXT=HOLD · V2 배선 유지 · WIRE금지 · BAND-SELECT재탕금지

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-BAND-SELECT | **FAIL** · hit 전게이트 false · WIRE금지 |
| WIRE-V2 | ENABLED=**True** (유지) |
| EV-POP | FAIL (직전) |
| SETNO-HITMAP | FAIL |
| SETPACK-TOP6 | FAIL |
| TUNE | FAIL |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-BAND-SELECT** | V2쿼터 고정·티켓 LMH 번호대역 슬롯 재선택 | **FAIL** |
| **K-EV-POP** | V2쿼터 고정·저인기(EV) 슬롯 재선택 | FAIL |
| **K-SETNO-HITMAP** | V2쿼터 고정·뇌내 set_no 재배치 | FAIL (의미임계) |
| **K-SETPACK-TOP6** | 출현횟수 top6 → set1 재조립 | FAIL |
| **K-MARKOV-TUNE** | decay/steps/top 27격자 | FAIL |
| **K-MARKOV-WIRE-V2** | set_no 쿼터 | PASS |

---

## 2) K-BAND-SELECT 핵심

| 항목 | 값 |
|------|-----|
| 풀 | testlotto_brain_review · draw 53~1234 · n=**1182** |
| V2 pin ge3 / mean / mean_lmh | **0.1447** / **1.7504** / **0.5505** |
| best hit vs V2 | **없음** (전 정책 ge3 ≤ V2) |
| 최근접 | all_lmh_diverse · ge3=**0.1387** · Δ=**-0.0060** · mean=**1.7538** |
| all_lmh_high | ge3=**0.1303** · Δ=**-0.0144** · mean_lmh=**0.6150** |
| spearman(lmh,matched) @v2 | **0.0114** (p=**0.379017**) |
| hit_WIRE (Δge3≥0.005 · p&lt;0.05) | **FAIL** |
| recommended_next | **없음** (HOLD·V2유지·BAND-SELECT재탕금지) |

근거: docs/benchmarks/20260729_KBAND_select.json

### 후보 기각 (선정 과정)

| 후보 | 기각 |
|------|------|
| K-DIV-V2 | COVER/GATHER 다양성 인접 |
| K-AUX-THRESH | conf-quota 구WIRE 인접 |
| K-ATTACK-SEARCH | 재예측↑ · GATHER/SETPACK 인접 |

### 재탕금지 (누적)

SETPACK-TOP6 · MARKOV-TUNE · SETNO-HITMAP · EV-POP · conf-quota구WIRE · HISIM/STRUCT/COVER wheel · GATHER전면 · **BAND-SELECT**

---

## 3) 다음

K-ATTACK-HOLD — BAND-SELECT WIRE금지·재탕금지 · V2 유지 · 형·커서 다음 축 1건 재선정 (승인 필요)

---

## 4) 산출물

- tools/_k_band_select_survey.py
- docs/benchmarks/20260729_KBAND_select.json
- reports/20260729_KBAND_SELECT.md
- My_Drive_Sync/커서보고서/20260729_KBAND_SELECT.md
