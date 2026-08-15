# K-STAT-EVOLVE-DIAG-LOG APPLY

시각: 2026-08-15T14:18:53+09:00 · **APPLY_OK** · stat만 · 1237아님 · hits/tier 클레임 금지
목적=캐시 채점 append. 예측 불변. EVOLVE_AUTO/FEATURE_LAMBDA OFF.

HARD=통과. write ok=200 skip=0 fail=0.

## 1) census

| 항목 | 전 | 후 |
|------|----|----|
| evolve 행 | 0 | 200 |
| evolve 뇌 | None | {'stat': 200} |
| 원장 | {'stat': 3000} | {'stat': 3000} |
| 캐시 | {'markov': 200, 'review': 200, 'stat': 200} | {'markov': 200, 'review': 200, 'stat': 200} |
| predictions | 0 | 0 |
| pred_1237 | 0 | 0 |
| draws MAX | 1236 | 1236 |

## 2) HARD

| 항 | 값 |
|----|-----|
| peek as_of>=draw | 0 |
| brain 전부 stat | True |
| markov/review 행 | 0 |
| 원장 3000 불변 | True |
| predictions 불변 | True |
| pred_1237 | 0 |
| draws MAX | 1236 |
| EVOLVE_AUTO | False |
| FEATURE_LAMBDA | False |

## 3) prefer/prize (캐시 불변 증명 · 모니터)

| 축 | 전 | 후 | Δ |
|----|----|----|---|
| prefer | 1.009444 | 1.009444 | 0.0 |
| prize | 1.004395 | 1.004395 | 0.0 |

예측 세트를 다시 뽑지 않음. Δ≠0이면 캐시가 바뀐 것(실패).

## 4) 롤백

`write_evolve_diag_stat` 호출 제거 + `DELETE FROM testlotto_evolve_log WHERE brain_tag='stat'`. 원장·예측 불변.
