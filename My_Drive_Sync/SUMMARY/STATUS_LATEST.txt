# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-EV-POP FAIL · NEXT=HOLD · V2 배선 유지 · WIRE금지 · EV-POP재탕금지

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-EV-POP | **FAIL** · hit/ev_preserve 모두 false · WIRE금지 |
| WIRE-V2 | ENABLED=**True** (유지) |
| SETNO-HITMAP | FAIL (직전) |
| SETPACK-TOP6 | FAIL |
| TUNE | FAIL |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-EV-POP** | V2쿼터 고정·저인기(EV) 슬롯 재선택 | **FAIL** |
| **K-SETNO-HITMAP** | V2쿼터 고정·뇌내 set_no 재배치 | FAIL (의미임계) |
| **K-SETPACK-TOP6** | 출현횟수 top6 → set1 재조립 | FAIL |
| **K-MARKOV-TUNE** | decay/steps/top 27격자 | FAIL |
| **K-MARKOV-WIRE-V2** | set_no 쿼터 | PASS |

---

## 2) K-EV-POP 핵심

| 항목 | 값 |
|------|-----|
| 풀 | testlotto_brain_review · draw 53~1234 · n=**1182** |
| V2 pin ge3 / mean / mean_pop | **0.1447** / **1.7504** / **6.261** |
| best hit vs V2 | **없음** (전 정책 ge3 ≤ V2) |
| 최근접 ev | markov_low_others_asc · ge3=**0.1421** · Δ=**-0.0026** · mean_pop=**5.1053** |
| all_low_pop | ge3=**0.1362** · Δ=**-0.0085** · mean_pop=**3.1518** (pop↓49.7%·ge3 과손실) |
| spearman(pop,matched) @v2 | **0.0134** (p=**0.303**) |
| hit_WIRE (Δge3≥0.005 · p&lt;0.05) | **FAIL** |
| ev_preserve (ge3≥-0.002 · pop↓≥5%) | **FAIL** |
| recommended_next | **없음** (HOLD·V2유지) |

근거: docs/benchmarks/20260729_KEV_pop.json

### 후보 기각 (선정 과정)

| 후보 | 기각 |
|------|------|
| K-STATP | pattern/STRUCT 재탕 위험 |
| K-ATTACK-SEARCH | 재예측↑ · GATHER/SETPACK 인접 |
| K-ZONE-SLICE | SLICE/COVER 재탕 |

---

## 3) 다음

K-ATTACK-HOLD — EV-POP WIRE금지·재탕금지 · V2 유지 · 형·커서 다음 축 1건 재선정 (승인 필요)

---

## 4) 산출물

- tools/_k_ev_pop_survey.py
- docs/benchmarks/20260729_KEV_pop.json
- reports/20260729_KEV_POP.md
- My_Drive_Sync/커서보고서/20260729_KEV_POP.md
