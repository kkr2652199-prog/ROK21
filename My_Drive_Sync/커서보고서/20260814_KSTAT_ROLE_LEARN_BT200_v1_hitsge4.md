# K-STAT-ROLE-LEARN-BT200 — stat만 패치 엔진 200회

시각: 2026-08-14T20:34:41+09:00 · **PASS** · ge3미클레임 · 1237아님

## 0) 한 줄

리셋 후 **과거학습만** 6~8/9~10 원장복습 ON vs 구 Jaccard OFF. 1~5는 같아야 한다.

## 1) 리셋

`{"lotto_predictions": 1000, "lotto_analysis": 0, "testlotto_brain_review": 597, "testlotto_brain_learn_state": 3, "testlotto_brain_weights": 3, "testlotto_backtest_runs": 0, "testlotto_backtest_draw_results": 0, "testlotto_pool_view_cache": 603, "testlotto_evolve_log": 0, "testlotto_evolve_auto_state": 1, "testlotto_pool_hit_ledger": 9000, "testlotto_pool_hit_scatter": 1200, "testlotto_skill_homework": 600, "testlotto_role_homework": 6, "hit_warrant_log": 0}`

## 2) 스모크 1234~1236

hard=True n_ok=3 peek=0 skill_diff=0

## 3) 200회 모니터 (성적 아님)

n_ok=200 elapsed=232.4s
skill 1~5 동일 회차=200 / 다름=0
cover 번호 다른 회차=30
shape 번호 다른 회차=199
숙제 cover n_pos 평균=1

| 경로 | mean_all | mean_best | ge3_best(모니터) |
|------|----------|-----------|------------------|
| ON skill | 0.798 | 1.705 | 25 |
| OFF skill | 0.798 | 1.705 | 25 |
| ON cover | 0.7917 | 1.36 | 13 |
| OFF cover | 0.7833 | 1.385 | 13 |
| ON shape | 0.835 | 1.04 | 12 |
| OFF shape | 0.82 | 1.02 | 10 |
| ON 몰아주기 | 0.817 | 1.585 | 24 |
| OFF 몰아주기 | 0.808 | 1.555 | 23 |

이전 3뇌 BT200 stat solo mean_all **0.828** (1~5 경로 · 비교 참고).

census: {"lotto_draws_max": 1236, "predictions": 0, "pool_cache": 600, "ledger": 3000, "role_homework": 1200, "skill_homework": 0, "pred_1237": 0}
bugs: {}

## 4) 판정

hard_ok=True. 등수P 클레임 없음. DB 커밋 안 함.
