# K-BLEND-STRENGTH-SWEEP

📅 2026-08-10 KST · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_blend_strength_sweep.py`  
선행: `20260810_KGENSPARK_IDEA_CHECK.json` pass=True

## 사전확인
- BLEND_STRENGTH 코드값=0.55 (기대 0.55) → OK
- SCORE_WEIGHTS_BY_BRAIN=cand_A → OK

## 스윕
- range: [0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75]
- seeds: [0, 42, 123, 999, 7]
- draws: [1100, 1235] (n=136)
- base prize@0.55: **-0.059526**

## 결과표

| blend | prizeΔ mean | preferΔ mean | cn_rate | gate | c1/c2/c3 | |Δprize| |
|------:|------------:|-------------:|--------:|:----:|:--------:|--------:|
| 0.35 | -0.058030 | +0.242663 | 1.00 | N | False/True/False | 0.0015 |
| 0.40 | -0.061405 | +0.242167 | 1.00 | N | True/True/False | 0.0019 |
| 0.45 | -0.061062 | +0.246657 | 1.00 | N | True/True/False | 0.0015 |
| 0.50 | -0.058862 | +0.247192 | 1.00 | N | False/True/False | 0.0007 |
| 0.55 | -0.059526 | +0.245772 | 1.00 | Y | True/True/True | 0.0000 |
| 0.60 | -0.055858 | +0.247077 | 1.00 | N | False/True/False | 0.0037 |
| 0.65 | -0.057743 | +0.245713 | 1.00 | N | False/True/False | 0.0018 |
| 0.70 | -0.060304 | +0.245323 | 1.00 | N | True/True/False | 0.0008 |
| 0.75 | -0.059823 | +0.249420 | 1.00 | N | True/True/False | 0.0003 |

## 판정
- **best_blend** = `None`
- **verdict** = **NO_IMPROVE**
- reason: 게이트 통과 개선 후보 없음

## 커서 의견
1. **best_blend = null** · **verdict = NO_IMPROVE** · 현재 **0.55 유지**.
2. 0.55 대비 prize가 더 음수인 점(0.40/−0.0614, 0.45/−0.0611)은 있으나 **|Δ|≤0.0019 ≪ 0.01** → noise 임계 미달. **바로 APPLY 금지**.
3. prefer·cn_rate는 전 구간 건강(prefer≈+0.24~0.25, cn=1.0). ROLLBACK 아님.
4. 추가 검증 불필요(스윕 자체가 다seed 5×9). 다음 확대(뇌별 W·stat)는 **HOLD** — 단일 BLEND로는 더 먹을 여지 없음.

## 금지 준수
coordinator/engine/random.choices/_get_draws_before/SCORE_WEIGHTS/ge3/DB쓰기 — 미접촉.
