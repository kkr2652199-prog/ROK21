# K-FUTURE-WIRE — QUICK n=200 재검증 (리셋 후 재기입)

📅 2026-08-03 · **PASS** · draw 1035~1234

근거: `20260803_KFUTURE_WIRE_QUICK200.json`

## SUMMARY

| ge3_rate | **0.1350** (27/200) |
| mean_match | **1.7150** |
| vs n100 0.1500 | **-0.0150** |
| vs wire pin 0.1447 | **-0.0097** |
| patch gate (>0.09) | **PASS** |
| QUICK enrich (ge3>null·p<0.15) | **FAIL** (p=0.1986) |
| late(100) ge3 | **0.1500** (= n100 구간) |
| BUCKET_SELECT_MODE | **aux_hint_native** |

## reset

- lotto_predictions / learn_state / brain_review / weights / pool cache **삭제 후 재기입**
- lotto_draws(당첨) **유지**

## quota avg %

- stat: **0.0%**
- markov: **80.0%**
- review: **20.0%**

## by_period

- early: ge3=0.1200 n=50
- mid: ge3=0.1200 n=50
- late: ge3=0.1500 n=100
