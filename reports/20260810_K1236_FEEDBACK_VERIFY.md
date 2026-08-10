# K-1236-FEEDBACK-VERIFY

📅 2026-08-10 KST · wire=**False** · ge3=미사용 · 단건 서열화 금지

## 판정: **VERIFY_OK**

## STEP0 draw_1236
- numbers: **[12, 18, 21, 29, 34, 38]**
- bonus: **10**
- first_winners: **11**
- in_db: True

## 발권 전제
예측이 없어 `run_prediction(1236)` 실행(재료=`_get_draws_before(1236)` · 1236 번호 미사용).  
pred_count=10 · ran=True

## API 주의
`apply_feedback_after_predict(1236)` → **1235** 채점.  
1236 채점 = `apply_draw_result_feedback(1236)` ≡ `after_predict(1237)`.

## feedback_1236
| brain | mean_hits | best_hits | weight | ok |
|-------|----------:|----------:|-------:|:--:|
| stat | 1.0 | 1.0 | 0.0 | True |
| markov | 0.0 | 0.0 | 0.0 | True |
| review | 0.0 | 0.0 | 0.0 | True |

duplicate_skip_ok=True

## score_1236 (단건 참고 · 서열화 불가)
baseline E[hits]=0.8 · stat=1.0 · markov=0.0 · review=0.0

## ev_check_1236 (단건 방향 · 통계 클레임 금지)
- review top15 ∩ actual = **3** /6
- markov top15 ∩ actual = **2** /6
- review_hint_top15: [40, 37, 45, 39, 34, 38, 43, 44, 20, 42, 27, 18, 33, 15, 35]
- markov_hint_top15: [12, 7, 3, 13, 18, 27, 1, 6, 11, 4, 10, 17, 19, 8, 20]
- first_winners: 11

## 다음
**K-N-MEAN-INPUT-FIX**

## 커서 의견
1236 경로 실전 확인됨(발권→feedback→evolve마크·weight0·중복SKIP). 단건 mean/hint적중은 참고만·서열화 금지. K-N-MEAN-INPUT-FIX **바로 진행 가능**(피드백 입력이 살아 있음이 전제).
