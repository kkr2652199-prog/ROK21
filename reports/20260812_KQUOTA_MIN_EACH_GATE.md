# K-QUOTA-MIN-EACH-GATE

시각: 2026-08-12T07:25:29+09:00 · 단계⑧

## 판정 **APPLY_OK**

| | min_each=0 | min_each=1 (live) |
|--|------------|-------------------|
| quota | `{'stat': 0, 'markov': 4, 'review': 1}` | `{'stat': 1, 'markov': 3, 'review': 1}` |

### 케이스
| name | min0 | min1 | all≥1 |
|------|------|------|-------|
| live | `{'stat': 0, 'markov': 4, 'review': 1}` | `{'stat': 1, 'markov': 3, 'review': 1}` | True |
| flat | `{'stat': 2, 'markov': 2, 'review': 1}` | `{'stat': 2, 'markov': 2, 'review': 1}` | True |
| dom_markov | `{'stat': 0, 'markov': 4, 'review': 1}` | `{'stat': 1, 'markov': 3, 'review': 1}` | True |

## 코드
- `QUOTA_ADAPTIVE_MIN_EACH=1`
- dominance 분기에서도 min_each 이체 보정
