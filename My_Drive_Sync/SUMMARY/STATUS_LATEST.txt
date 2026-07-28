# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-SETNO-HITMAP FAIL · NEXT=HOLD · V2 배선 유지 · WIRE금지

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| SETNO-HITMAP | **FAIL** · best Δge3=+0.0034 < 0.005 · WIRE금지 |
| WIRE-V2 | ENABLED=**True** (유지) |
| SETPACK-TOP6 | FAIL (직전) |
| TUNE | FAIL |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-SETNO-HITMAP** | V2쿼터 고정·뇌내 set_no 재배치 관측 | **FAIL** (의미임계) |
| **K-ATTACK-NEXT-AXIS** | HOLD하 다음축 선정=SETNO | 선정·관측 완료 |
| **K-SETPACK-TOP6** | 출현횟수 top6 → set1 재조립 | **FAIL** |
| **K-MARKOV-TUNE** | decay/steps/top 27격자 | FAIL |
| **K-MARKOV-WIRE-V2** | set_no 쿼터 | PASS |

---

## 2) SETNO-HITMAP 핵심

| 항목 | 값 |
|------|-----|
| 풀 | testlotto_brain_review · draw 53~1234 · n=1182 |
| V2 pin ge3 / mean | **0.1447** / 1.7504 |
| grid best | markov{1,2,3} + **stat set3** + review1 |
| best ge3 / mean | **0.1481** / **1.7623** |
| Δ ge3 vs V2 | **+0.0034** |
| Δ mean vs V2 | +0.0119 |
| ge4 (V2→best) | 0.0102 → **0.0135** |
| binom p vs null (best) | **0.000197** |
| 의미임계 Δge3≥0.005 | **미달** |
| recommended_next | **없음** (HOLD·V2유지) |

근거: docs/benchmarks/20260729_KSETNO_hitmap.json

### 후보 기각 (선정 과정)

| 후보 | 기각 |
|------|------|
| K-STATP | pattern/STRUCT 재탕 위험 |
| K-MARKOV-LEARN | PROBVEC boost≈null |
| K-ZONE-SLICE | SLICE/COVER 재탕 |

---

## 3) 다음

K-ATTACK-HOLD — SETNO WIRE금지·재탕금지 · V2 유지 · 형·커서 다음 축 1건 재선정 (승인 필요)

---

## 4) 산출물

- tools/_k_setno_hitmap_survey.py
- docs/benchmarks/20260729_KSETNO_hitmap.json
- reports/20260729_KATTACK_NEXT_AXIS.md
- My_Drive_Sync/커서보고서/20260729_KATTACK_NEXT_AXIS.md
