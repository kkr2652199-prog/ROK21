# K-FUTURE-WIRE — 독립뇌 미래예측 배선 n=100

📅 2026-08-03 · **PASS** · draw 1135~1234

근거: `20260803_KFUTURE_WIRE_N100.json`

## SUMMARY

| ge3_rate | **0.1500** (15/100) |
| mean_match | **1.7000** |
| vs V2 baseline 0.09 | **+0.0600** |
| BUCKET_SELECT_MODE | **aux_hint_native** |
| BRAIN_RNG_SEED_BASE | **42** (뇌마다 시드 리셋) |
| verdict | **PASS** (gate > 0.09) |

## quota avg %

- stat: **0.0%**
- markov: **80.0%**
- review: **20.0%**

## by_period

- early: ge3=0.2000 n=25
- mid: ge3=0.0800 n=25
- late: ge3=0.1600 n=50

## design (해결점)

1. **뿌리 원인:** 융합 시 stat→markov→review 순서로 `random`을 공유해, markov 번호가 solo(0.13)와 달라짐 → fused 천장 0.09
2. **핵심 패치:** `_seed_independent_brain(draw)` — 각 예측뇌 generate 직전 `seed(42+draw)` 리셋
3. **구조 정합:** 독립뇌 `aux_hint_score`·`native_confidence` 보존 · 발권=aux_hint_native (set_no_asc 폐기)
4. **유지:** V2 SOLO_GE3_PRIORS quota (4/0/1) · 표시용 aux confidence 재작성은 발권 키와 분리

## live

- `coordinator.BUCKET_SELECT_MODE=aux_hint_native`
- per-brain RNG isolate **ON**
- smoke 1230~1234 **PASS**
