# K-MARKOV-WIRE-V2 — set_no 쿼터 배선

📅 2026-07-29 · **PASS** · `MARKOV_WIRE_ENABLED=True` 유지

## 요약

set_no 오름차순 쿼터(markov×3+stat×1+review×1)가 **E_markov3mix2를 재현**.  
ge3=**0.1447** · p=**0.000679** → PASS (ge3≥0.1362 ∧ p<0.05).  
V1(conf 정렬) FAIL(0.121) 대비 **Δge3 +0.024**.

근거: `docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json`

---

## 변경

| 항목 | V1 | V2 |
|------|----|----|
| 선택 기준 | confidence 내림차순 후 쿼터 | **뇌별 set_no 오름차순** 쿼터 |
| ENABLED | False(롤백) | **True** |
| pred_set_no | 없음 | 생성 시 stamp |

`AUX_WEIGHTS`·`SETS_PER_PREDICT_BRAIN` 미변경.

---

## V1 vs V2 vs E

| 구성 | mean | ge3 | p vs null | 판정 |
|------|------|-----|-----------|------|
| V1 conf | 1.7157 | 0.1210 | 0.227 | FAIL |
| **V2 set_no** | **1.7504** | **0.1447** | **0.0007** | **PASS** |
| E (NULL pin) | 1.7504 | 0.1447 | 0.0007 | 실력 |
| null_n5 | 1.7281 | 0.1137 | — | — |

---

## Verdict / NEXT

**PASS → `K-MARKOV-TUNE`**  
배선 유지. 다음: markov 세부 파라미터·쿼터 미세 조정 여부 검토.
