# K-SETCOUNT-NULL — 장수효과 vs 실력 분리 (READ-ONLY)

📅 2026-07-29 · `db_code_write=false` · MC seed=42 · trials=**10000**

## 요약

**PASS → `K-MARKOV-WIRE`.**  
n=10·15 mixed는 null과 동등(**장수효과**).  
5장 중 **E markov×3+stat×1+review×1** 이 best (p=0.0007).  
→ SETCOUNT 장수 확장 WIRE **기각** · markov 배합 5장 WIRE 후보.

근거: `docs/benchmarks/20260729_KSETCOUNT_null.json`

---

## STEP1 — null MC 기준선

샘플 draw 100개(53~1234 균등) × 10000 trials.

| n | null_mean | null_ge3 | null_ge3_std | null_ge4 | KTRUST ref |
|---|-----------|----------|--------------|----------|------------|
| 5 | **1.7281** | **0.1137** | 0.0317 | 0.0070 | mean1.726 / ge3 0.116 |
| 10 | **2.0829** | **0.2145** | 0.0416 | 0.0140 | — |
| 15 | **2.2690** | **0.3034** | 0.0458 | 0.0208 | mean2.283 / ge3 0.313 |

이론 1장 E=0.80. best-of-N은 MC·KTRUST와 정합.

---

## STEP2 — 실측 vs null (n_eval=1182)

| ID | 구성 | mean | ge3 | null_ge3 | Δge3 | p (>) | 판정 |
|----|------|------|-----|----------|------|-------|------|
| A | RR 5장 | 1.7428 | 0.1337 | 0.1137 | +0.020 | **0.019** | **실력** |
| B | mixed best-10 | 2.1024 | 0.2284 | 0.2145 | +0.014 | 0.129 | 장수효과 |
| C | mixed best-15 | 2.2487 | 0.3088 | 0.3034 | +0.005 | 0.354 | 장수효과 |
| D | markov×5 | 1.7098 | 0.1362 | 0.1137 | +0.023 | **0.010** | **실력** |
| **E** | **markov×3+2** | **1.7504** | **0.1447** | 0.1137 | **+0.031** | **0.0007** | **실력** |
| F | stat×5 | 1.7124 | 0.1091 | 0.1137 | −0.005 | 0.702 | 장수효과 |

실측 pin = `20260729_KSETCOUNT_survey.json` · 이항검정 one-sided greater.

---

## STEP3 — WIRE 후보

| 후보 | 비고 |
|------|------|
| **E_markov3mix2** | best_5 · p 최소 |
| D_markov5 | markov 단독도 실력 |
| A_n5_rr | RR 자체도 null 대비 실력 |
| ~~B/C~~ | 10·15 **기각** |

`step3_wire_candidates`: A, D, E

---

## 비용·EV 메모

| 장수 | 판정 | 함의 |
|------|------|------|
| 5 | 실력 (E) | **동일 비용**에서 null 초과 → WIRE 후보 |
| 10·15 | 장수효과 | 비용 2~3× · ge3↑는 null 설명 → **확장 금지** |

---

## Gates

| gate | 결과 |
|------|------|
| any_5set_skill | **true** |
| any_10set_skill | false |
| any_15set_skill | false |
| best_5set_config | **E_markov3mix2** |

## Verdict / recommended_next

**PASS → K-MARKOV-WIRE**  
SETCOUNT 장수 확장 기각. markov 중심 5장 배합(특히 top1_3) 배선 검토.
