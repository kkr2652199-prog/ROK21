# K-MARKOV-LEARN-SURVEY — markov learn_state 배선 QUICK survey

날짜 2026-08-01 · elapsed 55.7s · **FAIL** · seed=42 · n=200 · gate=quick

## 1. 📋 선생님이 준 숙제
| 항목 | 내용 |
|------|------|
| **ID** | K-MARKOV-LEARN-SURVEY |
| **질문** | markov visit_count에 learn_state(carry/ending/overdue) 배선 시 live WF ge3가 live baseline(0.1218)을 넘는가? |
| **PASS** | markov_learn_wired ge3 > 0.1218 AND p < 0.15 |
| **금지** | random.choices · _get_draws_before · boost cap · coordinator quota · DB reset |

## 2. 🔧 학생이 한 일
| 항목 | 값 |
|------|-----|
| 도구 | `tools/_k_markov_learn_survey.py` |
| 배선 | `predict_flow_shaman.apply_markov_learn_boost` (survey용 · **FAIL 후 롤백**) |
| n_eval | 200 · draw [1035, 1234] · seed=42 |
| coordinator_modified | false |

## 3. 📊 풀이
| strategy | pipeline | ge3_rate | mean | p | Δlive_base | Δpin |
|----------|----------|--------:|-----:|--:|-----------:|-----:|
| baseline_markov_old | stored review | 0.165 | 1.845 | 0.018508 | 0.0432 | 0.0203 |
| **markov_learn_wired** | live WF wired | **0.105** | **1.715** | **0.683286** | **-0.0168** | **-0.0397** |

## 4. ✅/❌ 맞은·틀린 것
- pass_gate: **False** · criterion: ge3>0.1218 p<0.15
- wired ge3=0.105 p=0.683286
- recommended_next: **K-ATTACK-HOLD**

## 5. 📝 복습
- K-F: markov learn_state 소비 경로 추가 (K-ARCHITECTURE-REVIEW 미작동 항목)
- stored baseline vs live wired 비교 — pin(0.1447)과 live baseline(0.1218) 혼동 금지

## 6. 📎 근거 (null · live_baseline · pin)
| label | ge3 | mean | 출처 |
|-------|----:|-----:|------|
| null | **0.1137** | 0.8000 | theory E[match] |
| live_baseline | **0.1218** | — | K-10SET-DET-LAB-FULL collapse |
| pin (WIRE-V2) | **0.1447** | **1.7504** | stored verify FULL1182 |
| JSON | `D:\ROK21\docs\benchmarks\20260801_KMARKOV_LEARN_survey.json` | | |

## 7. before / after (K-F 배선)
| | ge3_rate | mean | p |
|---|--------:|-----:|--:|
| before (stored markov old) | 0.165 | 1.845 | 0.018508 |
| after (markov_learn_wired) | 0.105 | 1.715 | 0.683286 |
| Δge3 | **-0.06** | — | — |
