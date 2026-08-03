# K-FUTURE-WIRE — FULL n=1182 재검증 (리셋 후 재기입)

📅 2026-08-03 · **PASS** · draw 53~1234

근거: `20260803_KFUTURE_WIRE_FULL.json`

## SUMMARY

| ge3_rate | **0.1184** (140/1182) |
| mean_match | **1.6912** |
| vs n100 0.1500 | **-0.0316** |
| vs wire pin 0.1447 | **-0.0263** |
| patch gate (>0.09) | **PASS** |
| FULL enrich (ge3>pin·p<0.05) | **FAIL** |
| collapse n100→FULL | **−0.0316** (0.1500→0.1184) |
| BUCKET_SELECT_MODE | **aux_hint_native** |

## 판정 메모

- **패치 게이트(>0.09)**: PASS — V2 0.09·구 highway 0.06 대비 유지 이득
- **WIRE pin FULL 게이트**: FAIL — pin 0.1447·p 미달 (기존 C package FULL 0.1015 대비는 **+0.0169**)

## reset

- lotto_predictions / learn_state / brain_review / weights / pool cache **삭제 후 재기입**
- lotto_draws(당첨) **유지**

## quota avg %

- stat: **0.0%**
- markov: **80.0%**
- review: **20.0%**

## by_period

- early: ge3=0.0990 n=394
- mid: ge3=0.1320 n=394
- late: ge3=0.1244 n=394
