# K-STAT-PATTERN-TUNE

📅 2026-08-10 KST · **APPLY** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_stat_pattern_hint_tune.py`  
원칙: **공유=lotto_draws만** · stat HINT 창만 스윕 · markov/review 고정

## 사전확인
- HINT_SPEC stat=(26, miss_pattern) → OK
- SCORE_WEIGHTS=cand_A → OK
- BLEND_BY_BRAIN: {'markov': 0.55, 'review': 0.85}

## 스윕
- weeks: [13, 20, 26, 39, 52]
- seeds: [0, 42, 123]
- draws: [1137, 1236]
- base hit@26: **0.306667**
- ABS_THR=0.005 · ISO_THR=0.005

## 결과표

| weeks | top15_hit | preferΔ | prizeΔ | drift p/z | gate | ↑/|Δ|/iso |
|------:|----------:|--------:|-------:|----------:|:----:|:---------:|
| 13 | 0.311667 | +0.244449 | -0.074379 | 0.0000/0.0000 | N | True/False/True/True |
| 20 | 0.308333 | +0.244449 | -0.074379 | 0.0000/0.0000 | N | True/False/True/True |
| 26 | 0.306667 | +0.244449 | -0.074379 | 0.0000/0.0000 | Y | True/True/True/True |
| 39 | 0.316667 | +0.244449 | -0.074379 | 0.0000/0.0000 | Y | True/True/True/True |
| 52 | 0.319444 | +0.244449 | -0.074379 | 0.0000/0.0000 | Y | True/True/True/True |

## 판정
- **best_weeks** = `52`
- **verdict** = **APPLY** (코드 반영 완료)
- reason: hit 최대 weeks=52 (hit=0.319444, prefer_drift=0.0, prize_drift=0.0) · |Δhit|=0.012777≥0.005

## 커서 의견
`HINT_SPEC_BY_BRAIN['stat']=(52, miss_pattern)` APPLY. markov/review HINT·BLEND 불변 · prefer/prize drift=0. 다음=④합동 smoke.
