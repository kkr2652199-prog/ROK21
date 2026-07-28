# K-SETCOUNT-SURVEY — 세트 수 확장 시뮬 (READ-ONLY)

📅 2026-07-29 · `db_code_write=false`

## 요약

**PASS → `K-SETCOUNT-WIRE`.**  
n=10·15 best-of-N ge3가 RR(0.1337)을 상회. markov 단독·STEP3 콤보도 ge3 PASS.  
단 **n=15 ge3=0.3088 ≈ null MC best-of-15(0.3132)** — 실력 신호보다 **발권수(초기하) 효과** 가능성이 큼 (K-08).

근거: `docs/benchmarks/20260729_KSETCOUNT_survey.json`

## 전제

| 항목 | 값 |
|------|-----|
| 풀 | brain_review 3×5=**15** (stat/markov/review) |
| wheel | combo_B (18/1/2) · F1 재생성 없음 |
| 평가 | best-of-N matched |
| n_eval | **1182** (53~1234) |
| RR | mean=1.7428 · ge3=0.1337 |

---

## STEP1 — 세트 수 격자

| n_sets | mean | ge3_rate | ge4_rate | union | vs RR ge3 |
|--------|------|----------|----------|-------|-----------|
| 5 | 1.7521 | 0.1151 | 0.0085 | 25.63 | 미달 |
| **10** | **2.1024** | **0.2284** | 0.0169 | 35.79 | **PASS** |
| **15** | **2.2487** | **0.3088** | 0.0245 | 37.46 | **PASS** |
| 20 | — | — | — | — | 풀 부족 스킵 |

**best_n = 15**

### 발권비용 메모 (mean × 장수)

| n | mean(best) | 장당 기대적중(참고·mean/n 아님) | 비용배수 vs 5장 |
|---|------------|--------------------------------|----------------|
| 5 | 1.75 | best-of-5 | 1× |
| 10 | 2.10 | best-of-10 | **2×** |
| 15 | 2.25 | best-of-15 | **3×** |

best mean↑는 장수↑에 따른 천장 접근(null best15≈2.28). **장당 효율·EV는 별도 검정 필요** — WIRE 시 SETS만 늘리지 말고 비용·null 대비 Δ를 명시할 것.

---

## STEP2 — 뇌별 단독

| 구성 | mean | ge3_rate | vs RR |
|------|------|----------|-------|
| stat×5 | 1.7124 | 0.1091 | 미달 |
| **markov×5** | 1.7098 | **0.1362** | **PASS** |
| review×5 | 1.7030 | 0.1227 | 미달 |
| mixed 3×5 | 2.2487 | 0.3088 | PASS (장수) |

**best_solo = markov** (ge3 기준). mean은 세 뇌 유사(~1.71 < RR mean).

---

## STEP3 — 최강뇌 조합 (markov 기준)

| combo | config | mean | ge3 |
|-------|--------|------|-----|
| top1_5 | markov×5 | 1.7098 | 0.1362 |
| top1_3 | markov×3 + 타뇌×1×2 | 1.7504 | **0.1447** |
| balanced | 3×5 | 2.2487 | 0.3088 |

**best_combo = combo_balanced** (장수 효과). 동일 5장 내에서는 **top1_3(0.1447) > top1_5(0.1362)**.

---

## Gates

| gate | 결과 |
|------|------|
| any_ge3 > 0.1337 | **true** |
| any_mean > 1.7428 | **true** |
| step1 | PASS → SETCOUNT-WIRE |
| step2 solo | PASS (markov) |
| step3 | PASS |

## Verdict

**PASS → K-SETCOUNT-WIRE.**  
세트 수 10·15에서 ge3·mean 상승은 재현되나 null MC와 거의 동일 → **배선 전 ‘장수 효과 vs 실력’ 분리 검증** 권고.  
부수: markov 단독 ge3 PASS · 5장 한정 시 top1_3이 top1_5보다 ge3 유리.

## recommended_next

**K-SETCOUNT-WIRE** (우선순위: STEP1 PASS)
