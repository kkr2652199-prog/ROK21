# K-FUTURE-WIRE — FULL n=1182 재검증 (리셋 후 재기입)

📅 2026-08-03 · **PASS** · draw 53~1234

## POST-EVOLVE 비교

- FEEDBACK_MATCH_MODE = `mean`
- 구 FULL ge3 = **0.1184**
- 신 FULL ge3 = **0.1184**
- Δ = **0.0**

구 FULL JSON은 유지: `docs/benchmarks/20260803_KFUTURE_WIRE_FULL.json`

근거: `20260804_KFUTURE_FULL_POST_EVOLVE.json`

## SUMMARY

| ge3_rate | **0.1184** (140/1182) |
| mean_match | **1.6912** |
| vs n100 0.1500 | **-0.0316** |
| vs wire pin 0.1447 | **-0.0263** |
| patch gate (>0.09) | **PASS** |
| enrich_verdict | FAIL |
| BUCKET_SELECT_MODE | **aux_hint_native** |

## reset

- lotto_predictions / learn_state / brain_review / weights **삭제 후 재기입·유지**
- pool_view_cache · lotto_draws **유지** (페이지 즉시 반응)

## quota avg %

- stat: **0.0%**
- markov: **80.0%**
- review: **20.0%**

## by_period

- early: ge3=0.0990 n=394
- mid: ge3=0.1320 n=394
- late: ge3=0.1244 n=394
