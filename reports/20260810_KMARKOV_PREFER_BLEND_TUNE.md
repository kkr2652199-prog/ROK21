# K-MARKOV-PREFER-BLEND-TUNE

📅 2026-08-10 KST · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_markov_prefer_blend_tune.py`  
원칙: **공유=lotto_draws만** · markov BLEND만 스윕 · review BLEND 고정 0.55

## 사전확인
- BLEND_STRENGTH_BY_BRAIN markov/review=0.55/0.55 → OK
- SCORE_WEIGHTS=cand_A → OK

## 스윕
- markov_blend: [0.4, 0.5, 0.55, 0.65, 0.75, 0.85]
- seeds: [0, 42, 123]
- draws: [1137, 1236] (n≈100)
- base prefer@0.55: **+0.244449**
- base prize@0.55: **-0.063355** (독립성 기준)

## 결과표

| markov_blend | preferΔ | prizeΔ(모니터) | |Δprize| | gate | pos/split/↑/|Δ|/iso |
|-------------:|--------:|---------------:|--------:|:----:|:--------------------:|
| 0.40 | +0.240827 | -0.063355 | 0.0000 | N | True/True/False/False/True |
| 0.50 | +0.242741 | -0.063355 | 0.0000 | N | True/True/False/False/True |
| 0.55 | +0.244449 | -0.063355 | 0.0000 | Y | True/True/True/True/True |
| 0.65 | +0.242816 | -0.063355 | 0.0000 | N | True/True/False/False/True |
| 0.75 | +0.243515 | -0.063355 | 0.0000 | N | True/True/False/False/True |
| 0.85 | +0.242633 | -0.063355 | 0.0000 | N | True/True/False/False/True |

## 판정
- **best_markov_blend** = `None`
- **verdict** = **NO_IMPROVE**
- reason: 게이트 통과 개선 후보 없음

## 커서 의견
개선 게이트 통과 후보 없음. markov BLEND=0.55 HOLD. 다음 권장: ② review prize BLEND 단독 스윕.

## 독립성
- review `BLEND_STRENGTH_BY_BRAIN['review']` 불변
- 게이트에 prize_iso(|Δprize|<0.005) 포함
- 동결: random.choices / _get_draws_before / boost상한 / ge3클레임 금지
