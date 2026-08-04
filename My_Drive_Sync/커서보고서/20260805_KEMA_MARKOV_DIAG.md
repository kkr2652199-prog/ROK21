# K-EMA-MARKOV-DIAG — L2 EMA 다중 반감기 진단 (2026-08-05)

- **판정:** `NOISE` · wire=`False` · draws 1~1235
- H=[8, 26, 78] · α=2/(H+1) · init=6/45 · warm from draw 79

## 1235 스냅샷 top5/bottom5

### H8
- top5: `[{'num': 15, 'ema': 0.51051326}, {'num': 43, 'ema': 0.40020193}, {'num': 7, 'ema': 0.3571301}, {'num': 31, 'ema': 0.29885869}, {'num': 19, 'ema': 0.29800488}]`
- bottom5: `[{'num': 21, 'ema': 0.01551679}, {'num': 33, 'ema': 0.01211827}, {'num': 10, 'ema': 0.0056206}, {'num': 23, 'ema': 0.00253638}, {'num': 5, 'ema': 0.00164139}]`

### H26
- top5: `[{'num': 15, 'ema': 0.30265915}, {'num': 31, 'ema': 0.23983091}, {'num': 19, 'ema': 0.20307878}, {'num': 28, 'ema': 0.19716436}, {'num': 13, 'ema': 0.18864644}]`
- bottom5: `[{'num': 10, 'ema': 0.06332905}, {'num': 33, 'ema': 0.06297642}, {'num': 21, 'ema': 0.0567288}, {'num': 23, 'ema': 0.04684316}, {'num': 5, 'ema': 0.04020054}]`

### H78
- top5: `[{'num': 15, 'ema': 0.21882056}, {'num': 28, 'ema': 0.19170975}, {'num': 31, 'ema': 0.18825626}, {'num': 27, 'ema': 0.18596496}, {'num': 19, 'ema': 0.16398374}]`
- bottom5: `[{'num': 14, 'ema': 0.09744921}, {'num': 23, 'ema': 0.09724854}, {'num': 10, 'ema': 0.09342197}, {'num': 21, 'ema': 0.08990034}, {'num': 5, 'ema': 0.08402168}]`

## signal_test (top15 → next-draw hits · expect 2.0)

| H | mean_hit | Δ vs rand | p | ge3_rate | verdict |
|---|----------|-----------|---|----------|---------|
| H8 | 2.013829 | +0.0138 | 0.33576883 | 0.330164 | **NOISE** |
| H26 | 1.995678 | -0.0043 | 0.55291237 | 0.327571 | **NOISE** |
| H78 | 1.964564 | -0.0354 | 0.86793816 | 0.299049 | **NOISE** |

## divergence

```json
{
  "dist": {
    "mean": 0.17159,
    "std": 0.030426,
    "p10": 0.135119,
    "p90": 0.2123,
    "median": 0.169199,
    "n": 1235
  },
  "contrast": {
    "definition": "div_score(t)>median vs ≤median → next draw hit≥3 into EMA8 top15 (절대0 분할 폐기: 당첨세트 평균 divergence가 거의 항상 +)",
    "n_pos": 568,
    "n_neg": 589,
    "div_pos_ge3_rate": 0.332746,
    "div_neg_ge3_rate": 0.327674,
    "delta": 0.005072,
    "usable_groups": true
  },
  "verdict": "NOISE"
}
```

## ensemble_top15 @1235

`[{'num': 15, 'score': 0.38981849, 'rank': 1}, {'num': 43, 'score': 0.272115, 'rank': 2}, {'num': 31, 'score': 0.25902987, 'rank': 3}, {'num': 7, 'score': 0.25659801, 'rank': 4}, {'num': 19, 'score': 0.24272282, 'rank': 5}, {'num': 6, 'score': 0.2047489, 'rank': 6}, {'num': 39, 'score': 0.19181171, 'rank': 7}, {'num': 1, 'score': 0.18545586, 'rank': 8}, {'num': 35, 'score': 0.1789575, 'rank': 9}, {'num': 11, 'score': 0.17362876, 'rank': 10}, {'num': 13, 'score': 0.17014323, 'rank': 11}, {'num': 22, 'score': 0.16809747, 'rank': 12}, {'num': 37, 'score': 0.16113722, 'rank': 13}, {'num': 25, 'score': 0.15409673, 'rank': 14}, {'num': 28, 'score': 0.15014649, 'rank': 15}]`

## implication

```json
{
  "markov_pool_rescore_viable": false,
  "recommended_next": "L2 EMA 예측력 약함 · 다른 방향 탐색 또는 설계 재검토"
}
```

- tool: `tools/_k_ema_markov_diag.py`
- JSON: `docs/benchmarks/20260805_KEMA_MARKOV_DIAG.json`
