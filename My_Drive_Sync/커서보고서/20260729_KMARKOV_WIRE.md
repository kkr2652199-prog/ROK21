# K-MARKOV-WIRE — markov 배합 배선 검증

📅 2026-07-29 · **FAIL** · `MARKOV_WIRE_ENABLED=False` 롤백

## 요약

confidence 내림차순 쿼터(markov3+stat1+review1) 발권은  
**ge3=0.121 · p=0.227** → PASS 조건(ge3≥0.1362 ∧ p<0.05) **미달**.  
E(set_no 고정 markov×3+…) 실력(0.1447)과 **불일치** — AUX confidence 정렬이 배합을 왜곡.

근거: `docs/benchmarks/20260729_KMARKOV_WIRE_verify.json`

---

## 변경

| 파일 | 내용 |
|------|------|
| `coordinator.py` | `MARKOV_WIRE_*` 상수 + `apply_markov_wire_quota` · 발권 직전 적용 |
| | **ENABLED=False** (FAIL 롤백 · 상수 유지) |
| `tools/_k_markov_wire_verify.py` | brain_review→AUX→quota WF 검증 |

생성 `SETS_PER_PREDICT_BRAIN=5`(15후보) 유지 · AUX_WEIGHTS 미변경.

---

## 검증 결과 (n_eval=1182)

| 지표 | WIRE(conf 쿼터) | E set_no (NULL) | D markov5 | null_n5 |
|------|-----------------|-----------------|-----------|---------|
| mean | **1.7157** | 1.7504 | 1.7098 | 1.7281 |
| ge3 | **0.1210** | **0.1447** | 0.1362 | 0.1137 |
| Δge3 vs null | +0.0073 | +0.031 | +0.023 | — |
| p (>) | **0.227** | 0.0007 | 0.010 | — |

| PASS 조건 | 결과 |
|-----------|------|
| ge3 ≥ 0.1362 | **FAIL** (0.121) |
| p < 0.05 | **FAIL** (0.227) |

---

## 원인 메모

- E 실력 = **세트 순서(set_no) 고정 쿼터** (brain_review 저장 순)
- WIRE = **confidence 정렬 후 쿼터** → 고confidence 편향으로 markov 상위 3이 E와 다름
- 배선 재시도 시: set_no/원점수 기준 쿼터 또는 뇌내 순위 고정 검토

---

## Verdict / NEXT

**FAIL** → `MARKOV_WIRE_ENABLED=False` · **K-ATTACK-HOLD**  
코드 상수·함수는 유지(플래그만 OFF) — 재시도 시 ENABLED만 True.
