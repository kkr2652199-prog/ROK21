# K-M-REFEREE-WEIGHT

📅 2026-08-10 KST · **3뇌 테스트/개발** · 샘플 n=100 (1137~1236)

## 판정: **PATCHED**

## 패치
- `get_referee_weights`: `1+avg×0.15` → `max(floor, 1+GAIN×(avg−0.8))` 정규화
- GAIN=**2.5** · baseline=**0.8**

## 예측 DB 리셋
- lotto_predictions → **0**
- evolve_log → **0**
- draws 보존: **1236**

## 100회 복습
- reviewed=100 · skipped=0

## referee 실측 (as_of=1237)
| | legacy | new |
|--|-------:|----:|
| spread | 0.007453 | 0.142882 |
| weights | `{'stat': 0.33681171861144765, 'markov': 0.32935867457723605, 'review': 0.33382960681131624}` | `{'stat': 0.40001714236736097, 'markov': 0.25713551041398813, 'review': 0.34284734721865096}` |
| avgs | `{'stat': 0.8667, 'markov': 0.7, 'review': 0.8}` | |
| quota_5 | `{'stat': 2, 'markov': 1, 'review': 2}` | |

## unit (avg 0.7/0.8/0.9)
spread legacy=0.008929 → new=0.166667 · ok=True

## FINDINGS
K-M → **PATCHED**

## 커서 의견
예측 DB 리셋 후 1137~1236 mean-복습으로 학습 재축적. referee spread legacy=0.007453 → new=0.142882. 다음=1237 예측 생성(개발) 또는 정지.
