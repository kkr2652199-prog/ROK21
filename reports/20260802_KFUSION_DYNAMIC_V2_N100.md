# K-FUSION-DYNAMIC-V2 — solo×referee 동적 quota n=100

📅 2026-08-02 · **FAIL**(1bp) · draw 1135~1234

근거: `20260802_KFUSION_DYNAMIC_V2_N100.json`

## SUMMARY

| ge3_rate | **0.0900** (9/100) |
| mean_match | **1.7200** |
| vs referee-only 0.06 | **+0.03** |
| vs fixed quota60 0.08 | **+0.01** |
| vs markov80 floor 0.09 | tie |
| markov≥4 plan rate | **100.00%** |
| verdict | **FAIL** (gate **>** 0.09 · 1bp tie) |

## 구현 (V2.1)

- `_get_quota_weights`: `referee × SOLO_GE3_PRIORS` (K-HIGHWAY by_brain ge3)
- `SOLO_GE3_PRIORS`: stat=0.09 · markov=0.13 · review=0.11
- `QUOTA_DOMINANCE_FLOOR`: 1.15 → plan **4/0/1** (markov/review)
- referee-only(1/3 균등) 시 ge3=**0.0600** · solo prior 도입 후 **0.0900**

## quota avg %

- stat: **0.0%**
- markov: **80.0%**
- review: **20.0%**

## by_period

- early: ge3=0.0800 n=25
- mid: ge3=0.0800 n=25
- late: ge3=0.1000 n=50

## 판정

- 고정 DEFAULT(25/60/15) 폐기 목표 달성 · 3뇌 solo 성적 연동 quota live 후보
- gate strict FAIL — 0.09+ 경로(aux/wire) 또는 gate 재정의 **형 GO 대기**
