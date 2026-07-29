# K-AUX-WEIGHT-SURVEY — 4보조 AUX_WEIGHTS 13조합 live walk-forward

📅 2026-07-29 · **FAIL** · coordinator **미수정** · `db_code_write=false`

## 요약

live pipeline(3뇌 `predict_sets` + `_aux_score_with_weights` + `apply_markov_wire_quota`)으로 13조합 walk-forward.  
**13조합 전부 동일** ge3=**0.1100** · mean=**1.7191** · baseline_live **pin 불일치**(0.1447).  
best=A(균등) · Δ=**-0.0347** · p=**0.669622** → **FAIL** · NEXT=**K-ATTACK-HOLD**.

근거: `docs/benchmarks/20260729_KAUX_WEIGHT_survey.json`

---

## 전제

| 항목 | 값 |
|------|-----|
| n_eval | **1182** (draw 53~1234) |
| wire pin | ge3=**0.1447** · mean=**1.7504** |
| null_ge3 | 0.1137 |
| seed | 42 |
| SETS_PER_PREDICT_BRAIN | 5 (total 15) |
| 쿼터 | markov×3 + stat×1 + review×1 (set_no_asc) |
| pipeline | live 재생성 · stored pool **금지** |

---

## STEP1 — baseline_live

| 항목 | 값 |
|------|-----|
| weights | [0.25, 0.25, 0.25, 0.25] |
| ge3_rate | **0.1100** |
| mean | **1.7191** |
| ge4_rate | 0.0059 |
| ge3_count | 130 |
| Δ vs pin | **-0.0347** |
| pin_match | **false** (stored pin 0.1447과 live 불일치) |

※ STAT-WIRE 교훈 재현: stored pin ≠ live pipeline. V2 set_no 쿼터는 confidence 무관 → 가중 변경해도 발권 동일.

---

## STEP2 — 13조합 전체

| combo | weights (miss/pattern/balance/referee) | mean | ge3_rate | ge4_rate | ge3_count |
|-------|----------------------------------------|------|----------|----------|-----------|
| A | 0.25/0.25/0.25/0.25 | 1.7191 | 0.1100 | 0.0059 | 130 |
| B | 0.40/0.20/0.20/0.20 | 1.7191 | 0.1100 | 0.0059 | 130 |
| C | 0.20/0.40/0.20/0.20 | 1.7191 | 0.1100 | 0.0059 | 130 |
| D | 0.20/0.20/0.40/0.20 | 1.7191 | 0.1100 | 0.0059 | 130 |
| E | 0.20/0.20/0.20/0.40 | 1.7191 | 0.1100 | 0.0059 | 130 |
| F | 0.10/0.40/0.40/0.10 | 1.7191 | 0.1100 | 0.0059 | 130 |
| G | 0.10/0.30/0.30/0.30 | 1.7191 | 0.1100 | 0.0059 | 130 |
| H | 0.40/0.30/0.20/0.10 | 1.7191 | 0.1100 | 0.0059 | 130 |
| I | 0.10/0.20/0.40/0.30 | 1.7191 | 0.1100 | 0.0059 | 130 |
| J | 0.30/0.30/0.30/0.10 | 1.7191 | 0.1100 | 0.0059 | 130 |
| K | 0.00/0.40/0.40/0.20 | 1.7191 | 0.1100 | 0.0059 | 130 |
| L | 0.40/0.40/0.10/0.10 | 1.7191 | 0.1100 | 0.0059 | 130 |
| M | 0.10/0.10/0.40/0.40 | 1.7191 | 0.1100 | 0.0059 | 130 |

**관측:** 13조합 ge3·mean·ge4 **완전 동일** — V2 set_no_asc 쿼터가 confidence/AUX 가중과 무관하게 동일 5장 발권.

---

## STEP3 — top-5 (ge3 내림차순 · 전부 동률)

| combo | ge3_rate | Δ vs pin | p_value | verdict |
|-------|----------|----------|---------|---------|
| A | 0.1100 | -0.0347 | 0.669622 | FAIL |
| B | 0.1100 | -0.0347 | 0.669622 | FAIL |
| C | 0.1100 | -0.0347 | 0.669622 | FAIL |
| D | 0.1100 | -0.0347 | 0.669622 | FAIL |
| E | 0.1100 | -0.0347 | 0.669622 | FAIL |

---

## best_combo / gates

| 항목 | 값 |
|------|-----|
| best_combo | **A** [0.25,0.25,0.25,0.25] |
| best ge3 | **0.1100** |
| Δ vs pin | **-0.0347** |
| p_value | **0.669622** |
| any_ge3_gt_pin | **false** |
| gates.pass | **false** |
| recommended_next | **K-ATTACK-HOLD** |

---

## Verdict / NEXT

**FAIL → `K-ATTACK-HOLD`**  
AUX_WEIGHTS 격자는 V2 set_no 경로에서 **실레버 아님**(티켓 불변). coordinator `AUX_WEIGHTS` 배선 **금지**.  
다음 공격축 형 결정 대기 · 승인필요=**예**.

---

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/NEXT |
|------|------|--------|-------------|
| n_eval | 1182 | 1182 | 1182 |
| baseline_live ge3 | 0.11 | 0.1100 | 0.1100 |
| best_combo | A | A | A |
| best ge3 | 0.11 | 0.1100 | 0.1100 |
| Δ vs pin | -0.0347 | -0.0347 | -0.0347 |
| p_value | 0.669622 | 0.669622 | 0.669622 |
| 13조합 동일 | true | true | true |
| gates.pass | false | false | false |
| recommended_next | K-ATTACK-HOLD | K-ATTACK-HOLD | K-ATTACK-HOLD |

ASCII `-` 구분 · 숫자 SSOT=`docs/benchmarks/20260729_KAUX_WEIGHT_survey.json`
