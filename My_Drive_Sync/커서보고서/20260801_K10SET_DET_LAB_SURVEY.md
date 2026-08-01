# K-10SET-DET-LAB-COMBO — 10pool × deterministic top-k survey

날짜 2026-08-01 · elapsed 63.6s · **PASS** · seed=42 · n=200 · gate=quick

## 1. 📋 선생님이 준 숙제
| 항목 | 내용 |
|------|------|
| **ID** | K-10SET-DET-LAB-COMBO |
| **질문** | SETS=10 pool + det top-k 선별이 pin(0.1447)을 넘는가? |
| **PASS** | best ge3 > 0.1447 AND p < 0.15 |
| **금지** | coordinator·predict_* 수정 · wire |

## 2. 🔧 학생이 한 일
| 항목 | 값 |
|------|-----|
| 도구 | `tools/_k_10set_det_lab_survey.py` |
| det lab | 1군 `build_weighted_topk_sets` 로직 survey 내부 복사 |
| coordinator_modified | false |

## 3. 📊 풀이 (§6 baseline + §7 전략)
| label | ge3_rate | mean | p | Δpin |
|-------|--------:|-----:|--:|-----:|
| null | 0.1137 | 0.80 | — | — |
| pin | 0.1447 | 1.7504 | — | — |
| baseline_combined | 0.115 | 1.7 | 0.509824 | -0.0297 |
| pool10_combined | 0.145 | 1.715 | 0.102441 | +0.0003 |
| pool5_det_topk | 0.095 | 1.69 | 0.826954 | -0.0497 |
| pool10_det_topk | 0.105 | 1.7 | 0.683286 | -0.0397 |

## 4. ✅/❌ 맞은·틀린 것
- QUICK PASS (ge3>0.1447 AND p<0.15): **True** (pool10_combined만)
- **det_topk** pool5=0.095 · pool10=0.105 → **FAIL** (선별 교체 무효)
- baseline pool5 combined=0.115 → pool10 확장이 핵심 (+0.03p)
- best_strategy: `pool10_combined` ge3=0.145 (SELECT-01 QUICK와 동일 수준)

## 5. 📝 복습
- recommended_next: **K-10SET-DET-LAB-FULL**

## 6. 📎 근거
- JSON: `D:\ROK21\docs\benchmarks\20260801_K10SET_DET_LAB_survey.json`
- n_eval=200 · seed=42 · elapsed=63.6s
