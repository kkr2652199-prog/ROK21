# K-10SET-DET-LAB-FULL — 10pool combined survey (전체1182)

날짜 2026-08-01 · elapsed 156.1s · **FAIL** · seed=42 · n=1182 · gate=full

## 1. 📋 선생님이 준 숙제
| 항목 | 내용 |
|------|------|
| **ID** | K-10SET-DET-LAB-FULL |
| **질문** | pool10_combined FULL pin(0.1447) 초과? |
| **PASS** | pool10 ge3 > 0.1447 AND p < 0.05 |
| **금지** | coordinator·predict_* · wire |

## 2. 🔧 학생이 한 일
| 항목 | 값 |
|------|-----|
| 도구 | `tools/_k_10set_det_lab_survey.py` |
| mode | --full n=1182 |
| coordinator_modified | false |

## 3. 📊 풀이
| label | ge3_rate | mean | p | Δpin |
|-------|--------:|-----:|--:|-----:|
| null | 0.1137 | 0.80 | — | — |
| pin | 0.1447 | 1.7504 | — | — |
| baseline_combined | 0.1168 | 1.7352 | 0.383825 | -0.0279 |
| pool10_combined | 0.1218 | 1.7377 | 0.200997 | -0.0229 |

## tier 피벗 (BENCH §7 · pool10_combined)
| scope | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |
|-------|----|----|----|----|----|----|--------|
| pool10_combined | 0 | 0 | 0 | 6 | 147 | 153 | 5910 |

## 4. ✅/❌ 맞은·틀린 것
- pass_gate: **False** · best `pool10_combined`

## 5. 📝 복습
- SELECT-FULL 전례: QUICK 0.145 → FULL 0.1218 · **과장 해석 금지**
- recommended_next: **K-ATTACK-HOLD**

## 6. 📎 근거
- JSON: `D:\ROK21\docs\benchmarks\20260801_K10SET_DET_LAB_survey_full.json`
- n=1182 · seed=42 · elapsed=156.1s
