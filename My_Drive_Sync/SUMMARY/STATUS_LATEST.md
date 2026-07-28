# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-MARKOV-TUNE FAIL · NEXT=HOLD · V2 배선 유지

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| TUNE | **FAIL** · 파라미터 교체 실익 없음 |
| WIRE-V2 | ENABLED=**True** (유지) |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-MARKOV-TUNE** | decay/steps/top 27격자 | **FAIL** |
| **K-MARKOV-WIRE-V2** | set_no 쿼터 | PASS |
| **K-SETCOUNT-NULL** | 장수 vs 실력 | PASS(E) |

---

## 2) TUNE 핵심

| 항목 | 값 |
|------|-----|
| best | decay**0.01** / steps**50** / top**35** |
| best ge3 / mean | **0.1404** / 1.7386 |
| vs wire 0.1447 | **−0.0043** |
| current regen (0.02/80/25) | ge3 0.1193 (rank17) |
| any > wire | **false** |

근거: `docs/benchmarks/20260729_KMARKOV_TUNE_survey.json`

---

## 3) 다음

`K-ATTACK-HOLD` — V2 배선·현행 markov 파라미터 유지 · 새 축 재선정 (승인 필요)

---

## 4) 산출물

- `tools/_k_markov_tune_survey.py`
- `docs/benchmarks/20260729_KMARKOV_TUNE_survey.json`
- `reports/20260729_KMARKOV_TUNE_SURVEY.md`
