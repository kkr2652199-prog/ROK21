# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-MARKOV-WIRE-V2 PASS · NEXT=K-MARKOV-TUNE

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| MARKOV-WIRE-V2 | **PASS** · set_no 쿼터 ON |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-MARKOV-WIRE-V2** | set_no 쿼터 | **PASS** |
| **K-MARKOV-WIRE** | conf 쿼터 | FAIL→롤백 |
| **K-SETCOUNT-NULL** | 장수 vs 실력 | PASS(E) |

---

## 2) V2 핵심

| 항목 | 값 |
|------|-----|
| method | set_no_asc |
| mean / ge3 | **1.7504 / 0.1447** |
| p vs null 0.1137 | **0.000679** |
| vs V1 ge3 | 0.121 → **0.1447** |
| MARKOV_WIRE_ENABLED | **True** |

근거: `docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json`

---

## 3) 다음

`K-MARKOV-TUNE` — 세부 파라미터/쿼터 미세조정 (승인 필요)

---

## 4) 산출물

- `app/testlotto/brains/coordinator.py` (set_no quota · ENABLED=True)
- `tools/_k_markov_wire_v2_verify.py`
- `docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json`
- `reports/20260729_KMARKOV_WIRE_V2.md`
