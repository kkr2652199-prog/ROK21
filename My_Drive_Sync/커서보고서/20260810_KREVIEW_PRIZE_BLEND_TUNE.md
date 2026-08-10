# K-REVIEW-PRIZE-BLEND-TUNE

📅 2026-08-10 KST · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_review_prize_blend_tune.py`  
원칙: **공유=lotto_draws만** · review BLEND만 스윕 · markov BLEND 고정 0.55

## 사전확인
- BY_BRAIN markov/review=0.55/0.55 → OK
- SCORE_WEIGHTS=cand_A → OK

## 스윕
- review_blend: [0.4, 0.5, 0.55, 0.65, 0.75, 0.85]
- seeds: [0, 42, 123]
- draws: [1137, 1236]
- base prize@0.55: **-0.063355**
- base prefer@0.55: **+0.244449** (독립성 기준)

## 결과표

| review_blend | prizeΔ | preferΔ(모니터) | |Δprefer| | cn | gate | neg/↑/|Δ|/iso |
|-------------:|-------:|----------------:|---------:|---:|:----:|:---------------:|
| 0.40 | -0.067840 | +0.244449 | 0.0000 | 1.00 | N | True/True/False/True |
| 0.50 | -0.066233 | +0.244449 | 0.0000 | 1.00 | N | True/True/False/True |
| 0.55 | -0.063355 | +0.244449 | 0.0000 | 1.00 | Y | True/True/True/True |
| 0.65 | -0.066151 | +0.244449 | 0.0000 | 1.00 | N | True/True/False/True |
| 0.75 | -0.070156 | +0.244449 | 0.0000 | 1.00 | N | True/True/False/True |
| 0.85 | -0.074379 | +0.244449 | 0.0000 | 1.00 | Y | True/True/True/True |

## 판정
- **best_review_blend** = `0.85`
- **verdict** = **APPLY** (코드 반영 완료)
- reason: prize 최음수=0.85 (prize=-0.074379, prefer_drift=0.0) · |Δprize|=0.011024≥0.01

## 커서 의견
best=0.85 APPLY. `BLEND_STRENGTH_BY_BRAIN['review']=0.85` · markov=0.55 HOLD. prefer_drift=0 독립성 OK. 다음=③ stat 패턴 단독.
