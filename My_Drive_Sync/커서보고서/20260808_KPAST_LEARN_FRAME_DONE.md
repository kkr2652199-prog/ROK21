# K-PAST-LEARN-FRAME-DONE — 기본 틀 잠금 (2026-08-08)

- **판정:** `FRAME_LOCKED` · smoke_ok=`True`

## 초보용 요약

1. **끝난 것(틀):** 과거학습 뇌가 돌아가는 길 + 엔진 기본값 win**26**/mix**0.8**
2. **아직 안 함(세부):** decay·더 미세한 가중 조절
3. **안 건드림:** markov / review · transition OFF · ASSOC OFF
4. **전체 발권:** fusion ge3 **0.135** 그대로(APPLY 때 확인)

## 잠긴 기본값

- engine: `{'V2_SHORT_WIN': 26, 'V2_SHORT_MIX': 0.8, 'V2_LONG_DECAY': 0.005, 'V2_SHORT_DECAY': 0.05, 'rollback_win_mix': [52, 0.6]}`
- pipe: `transition(OFF) → engine(v2) → aux → past_learn soft → diversity`
- 롤백 win/mix: `[52, 0.6]`

- 다음: `K-PAST-LEARN-DETAIL-TUNE (decay 등) · 형 GO`
- tool: `tools/_k_past_learn_frame_done.py`
