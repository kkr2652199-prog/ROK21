# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-MARKOV-WIRE FAIL · ENABLED=False · NEXT=HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| MARKOV-WIRE | **FAIL** · 플래그 OFF 롤백 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-MARKOV-WIRE** | conf 쿼터 발권 | **FAIL** 롤백 |
| **K-SETCOUNT-NULL** | null vs 실력 | PASS (E) |
| **K-SETCOUNT-SURVEY** | 세트수 격자 | PASS→장수기각 |

---

## 2) WIRE 검증 핵심

| 항목 | 값 |
|------|-----|
| mean / ge3 | 1.7157 / **0.1210** |
| p vs null 0.1137 | **0.227** |
| PASS (ge3≥0.1362 ∧ p<0.05) | **false** |
| E set_no ge3 (참고) | 0.1447 |
| MARKOV_WIRE_ENABLED | **False** |

근거: `docs/benchmarks/20260729_KMARKOV_WIRE_verify.json`

---

## 3) 다음

`K-ATTACK-HOLD` — conf≠set_no 원인 · 재배선 축 재선정 (승인 필요)

---

## 4) 산출물

- `app/testlotto/brains/coordinator.py` (quota+ENABLED=False)
- `tools/_k_markov_wire_verify.py`
- `docs/benchmarks/20260729_KMARKOV_WIRE_verify.json`
- `reports/20260729_KMARKOV_WIRE.md`
