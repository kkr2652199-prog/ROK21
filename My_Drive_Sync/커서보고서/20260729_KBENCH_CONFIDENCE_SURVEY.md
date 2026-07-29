# K-BENCH-02 — confidence/AUX 정렬 vs set_no_asc (READ-ONLY live)

📅 2026-07-29 · **FAIL** · coordinator **미수정** · `db_code_write=false`

## 요약

live WF(3뇌 `predict_sets` + 4보조 AUX + variant 선택) 5축 비교.  
**baseline set_no_asc가 최고** ge3=**0.1100** · confidence/AUX 정렬 4축 **전부 하회**(0.0990~0.1024).  
pin 0.1447 **미달** · p=**0.669622** → **FAIL** · NEXT=**K-ATTACK-HOLD** · V2 pin 유지.

근거: `docs/benchmarks/20260729_KBENCH_CONFIDENCE_survey.json`

---

## SUMMARY (BENCH_PROTOCOL §6)

| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) | verdict |
|-------|----------|------|----------|-----|--------------|-------------|-------------|---------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | null-check |
| **WIRE-V2 pin** | stored | 1.7504 | 0.1447 | ✓ | +0.0310 | — | — | PINNED |
| baseline_set_no_asc | WF live | 1.7191 | **0.1100** | — | −0.0037 | −0.0347 | 0.669622 | FAIL |
| confidence_desc | WF live | 1.6997 | 0.1024 | — | −0.0113 | −0.0423 | 0.899894 | FAIL |
| aux_quota | WF live | 1.6878 | 0.1007 | — | −0.0130 | −0.0440 | 0.929290 | FAIL |
| confidence_quota | WF live | 1.6760 | 0.0998 | — | −0.0139 | −0.0449 | 0.941286 | FAIL |
| aux_total_desc | WF live | 1.6853 | 0.0990 | — | −0.0147 | −0.0457 | 0.951647 | FAIL |

- **pipeline=WF live** · n_eval=**1182** (draw 53~1234) · seed=42 · SETS_PER_PREDICT_BRAIN=5
- PASS 기준: any variant ge3 > 0.1447 AND p < 0.05 vs null → **미충족**

---

## 전제

| 항목 | 값 |
|------|-----|
| n_eval | **1182** |
| wire pin | ge3=**0.1447** · mean=**1.7504** |
| null_ge3 | 0.1137 |
| 쿼터(baseline) | markov×3 + stat×1 + review×1 (set_no_asc) |
| elapsed | 122.1s |
| 도구 | `tools/_k_bench_confidence_survey.py` |

---

## variant 상세 (ge3 내림차순)

| variant | mean | ge3_rate | ge4_rate | ge3_count | Δ vs pin | p (null) | verdict |
|---------|------|----------|----------|-----------|----------|----------|---------|
| baseline_set_no_asc | 1.7191 | **0.1100** | 0.0059 | 130 | −0.0347 | 0.669622 | FAIL |
| confidence_desc | 1.6997 | 0.1024 | 0.0017 | 121 | −0.0423 | 0.899894 | FAIL |
| aux_quota | 1.6878 | 0.1007 | 0.0017 | 119 | −0.0440 | 0.929290 | FAIL |
| confidence_quota | 1.6760 | 0.0998 | 0.0008 | 118 | −0.0449 | 0.941286 | FAIL |
| aux_total_desc | 1.6853 | 0.0990 | 0.0025 | 117 | −0.0457 | 0.951647 | FAIL |

**관측:** confidence/AUX 정렬은 set_no_asc baseline **대비 ge3 하락** (−0.0076~−0.0110). AUX·confidence는 발권 레버가 **아님**(역효과).

---

## tier 피벗 (BENCH_PROTOCOL §7 · baseline_set_no_asc)

| brain | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |
|-------|----------|----|----|----|----|----|-----|--------|
| markov | WF live | 0 | 0 | 0 | 5 | 75 | 80 | 3546 |
| stat | WF live | 0 | 0 | 0 | 2 | 28 | 30 | 1182 |
| review | WF live | 0 | 0 | 0 | 0 | 29 | 29 | 1182 |

### confidence_desc (참고 — review 거의 미발권)

| brain | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |
|-------|----------|----|----|----|----|----|-----|--------|
| markov | WF live | 0 | 0 | 0 | 1 | 42 | 43 | 2038 |
| stat | WF live | 0 | 0 | 0 | 1 | 86 | 87 | 3820 |
| review | WF live | 0 | 0 | 0 | 0 | 0 | 0 | 52 |

---

## Gates / Verdict

| gate | 결과 |
|------|------|
| any_ge3_gt_pin | **false** |
| any_pass (ge3>pin AND p<0.05) | **false** |
| best_variant | **baseline_set_no_asc** ge3=0.1100 |
| recommended_next | **K-ATTACK-HOLD** |

**FAIL → `K-ATTACK-HOLD`**  
confidence/AUX 정렬은 V2 set_no_asc **대체 불가** · coordinator `apply_markov_wire_quota` 수정 **금지**.  
K-BENCH-02-WIRE **불필요** · 형 결정 대기.

---

## 팩트체크

| 항목 | JSON | 보고서 |
|------|------|--------|
| n_eval | 1182 | 1182 |
| baseline ge3 | 0.11 | 0.1100 |
| best variant | baseline_set_no_asc | baseline_set_no_asc |
| confidence_desc ge3 | 0.1024 | 0.1024 |
| gates.pass | false | false |
| recommended_next | K-ATTACK-HOLD | K-ATTACK-HOLD |

ASCII `-` 구분 · SSOT=`docs/benchmarks/20260729_KBENCH_CONFIDENCE_survey.json`
