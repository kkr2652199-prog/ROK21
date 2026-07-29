# K-COVER-SURVEY — 세트 커버리지 최대화 시뮬 (READ-ONLY)

📅 2026-07-29 · DB/코드 배선 수정 없음 · `db_code_write=false`

## 요약

F1_V2_STRICT `_wheel_pick` 계수·`WHEEL_POOL` 격자 전부 **ge3 ≤ RR(0.1337)** → **FAIL(관측종료)**.  
mean은 RR(1.7428)을 소폭 상회(추가 표기). spearman(union, best) **0.0253 ≤ 0.03**.  
→ **WIRE 금지** · `recommended_next=없음` · NEXT=`K-ATTACK-HOLD`.

## SUMMARY (K-BENCH-05 baseline 행)

| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | p (vs null) | 비고 |
|-------|----------|------|----------|-----|--------------|-------------|------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | E[match]=6×6/45 |
| RR (best-of-5) | WF live | 1.7428 | 0.1337 | — | +0.0200 | — | n_eval=1182 |
| combo A baseline | WF live | 1.7614 | 0.1277 | — | +0.0140 | — | pool=25 |
| best pool=40 | WF live | 1.7970 | 0.1320 | — | +0.0183 | — | ge3<RR |

## 전제

| 항목 | 값 |
|------|-----|
| 풀 | testlotto 3뇌 `stat/markov/review` × 5세트 (`brain_review`) |
| 지시서 5뇌+lead1 | DB에 llm/lstm/fusion/lead1 WF 없음 → **3뇌 적응** (구조 유지) |
| 평가 | wheel 5세트 **best-of-5** matched (RR best_set과 동일 층) |
| n_eval | **1182** (draw 53~1234) |
| RR | mean=**1.7428** · ge3=**0.1337** |
| 도구 | `tools/_k_cover_survey.py` · `predict_brain7.py` 미수정 |

근거: `docs/benchmarks/20260729_KCOVER_survey.json`

---

## STEP1 — baseline (combo A · pool=25)

| 지표 | 값 |
|------|-----|
| mean_union_size | **25.8519** |
| mean (best-of-5) | **1.7614** |
| mean_matched_allsets | (JSON step1) |
| ge3_rate | **0.1277** |

---

## STEP2 — `_wheel_pick` 계수 격자 (pool=25)

| combo | new_cov_w | score_w | avg_ov_w | mean | ge3_rate | union |
|-------|-----------|---------|----------|------|----------|-------|
| A (현재) | 12 | 1.0 | 4 | 1.7614 | 0.1277 | 25.8519 |
| B | 18 | 1.0 | 2 | **1.7623** | 0.1277 | 25.8519 |
| C | 24 | 0.5 | 1 | 1.7623 | 0.1277 | 25.8519 |
| D | 12 | 1.0 | 8 | 1.7614 | 0.1277 | 25.8519 |
| E | 15 | 1.0 | 3 | 1.7614 | 0.1277 | 25.8519 |

**best_combo = B** (ge3 동일 · mean 미세↑). 계수 변경이 union/ge3에 **거의 무영향**.

---

## STEP3 — `WHEEL_POOL` 격자 (combo B 고정)

| pool | mean | ge3_rate | union |
|------|------|----------|-------|
| 15 | 1.7699 | 0.1277 | 25.1692 |
| 25 | 1.7623 | 0.1277 | 25.8519 |
| **40** | **1.7970** | **0.1320** | 26.3917 |
| 60 | 1.8037 | 0.1303 | 26.8384 |

**best_pool = 40** (ge3 최근접·최고). 여전히 ge3 **0.1320 < 0.1337**.

---

## STEP4 — 커버리지 vs 적중

| 항목 | 값 |
|------|-----|
| spearman_r (union vs best) | **0.0253** |
| 게이트 (>0.03) | **FAIL** |

양의 상관 미확인. 커버리지↑ ≠ ge3↑ 증거 부족.

---

## Gates

| gate | 결과 |
|------|------|
| any_combo_ge3_gt_rr | **false** |
| any_combo_mean_gt_rr | **true** (추가 표기) |
| coverage_corr_gt0 | **false** |

## Verdict

**FAIL(관측종료).** wheel 계수·pool 격자로 RR ge3 돌파 실패. mean>RR만 성립·corr 약함 → **K-COVER-WIRE 금지**.

## recommended_next

**없음** → NEXT_ACTIONS: `K-ATTACK-HOLD` (형·동생 재논의)
