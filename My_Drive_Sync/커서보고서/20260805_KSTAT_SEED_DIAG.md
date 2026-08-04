# K-STAT-SEED-DIAG — 뇌 seed 안정성 진단 (2026-08-05)

- **판정(stat):** `HIGH_SENSITIVITY` · wire=`False` · n=100 (1136~1235)
- seeds: `[42, 0, 7, 99, 1]` · eval=best_of_5 · path=signal_pool hybrid/repack (DB 미쓰기)

## 뇌별 ge3 (시드)

### stat · sensitivity=**HIGH_SENSITIVITY** · range=0.14

| seed | ge3 | mean | ge3_count |
|------|-----|------|-----------|
| 42 | 0.23 | 1.82 | 23 |
| 0 | 0.14 | 1.82 | 14 |
| 7 | 0.12 | 1.76 | 12 |
| 99 | 0.09 | 1.61 | 9 |
| 1 | 0.17 | 1.86 | 17 |
| **mean/std** | **0.15** / 0.047749 | min=0.09 max=0.23 | |

### markov · sensitivity=**HIGH_SENSITIVITY** · range=0.1

| seed | ge3 | mean | ge3_count |
|------|-----|------|-----------|
| 42 | 0.16 | 1.88 | 16 |
| 0 | 0.09 | 1.81 | 9 |
| 7 | 0.17 | 1.87 | 17 |
| 99 | 0.07 | 1.79 | 7 |
| 1 | 0.08 | 1.83 | 8 |
| **mean/std** | **0.114** / 0.042237 | min=0.07 max=0.17 | |

### review · sensitivity=**STABLE** · range=0.03

| seed | ge3 | mean | ge3_count |
|------|-----|------|-----------|
| 42 | 0.13 | 1.78 | 13 |
| 0 | 0.15 | 1.73 | 15 |
| 7 | 0.14 | 1.69 | 14 |
| 99 | 0.12 | 1.76 | 12 |
| 1 | 0.15 | 1.87 | 15 |
| **mean/std** | **0.138** / 0.011662 | min=0.12 max=0.15 | |

## pool_diversity (stat · seed42 vs seed0)

```json
{
  "stat_seed42": {
    "top3_rate": 0.112,
    "sum_mean": 133.02,
    "sum_std": 48.012911,
    "entropy": 5.408944,
    "slot_entropy": 4.541414,
    "detail": {
      "n_sets": 500,
      "top3_nums": [
        {
          "num": 13,
          "count": 118
        },
        {
          "num": 6,
          "count": 109
        },
        {
          "num": 44,
          "count": 109
        }
      ],
      "top3_rate": 0.112,
      "sum_mean": 133.02,
      "sum_std": 48.012911,
      "sum_min": 35,
      "sum_max": 243,
      "entropy": 5.408944,
      "slot_entropy": 4.541414,
      "biased": false
    }
  },
  "stat_seed0": {
    "top3_rate": 0.129667,
    "sum_mean": 132.294,
    "sum_std": 46.004952,
    "entropy": 5.366229,
    "slot_entropy": 4.504772,
    "detail": {
      "n_sets": 500,
      "top3_nums": [
        {
          "num": 7,
          "count": 161
        },
        {
          "num": 16,
          "count": 121
        },
        {
          "num": 35,
          "count": 107
        }
      ],
      "top3_rate": 0.129667,
      "sum_mean": 132.294,
      "sum_std": 46.004952,
      "sum_min": 31,
      "sum_max": 246,
      "entropy": 5.366229,
      "slot_entropy": 4.504772,
      "biased": false
    }
  },
  "diversity_gap": 0.042715,
  "verdict": "DIVERSE"
}
```

## cross_compare

```json
{
  "most_stable_brain": "review",
  "most_sensitive_brain": "stat",
  "stat_vs_markov_range_diff": 0.04,
  "note": "hybrid solo best_of_5 · QUOTA-D-WIRE 괴리 가설(stat seed 민감) 검증용 · 발권 ge3 약속 금지"
}
```

## implication

```json
{
  "quota_increase_safe": false,
  "recommended_next": "pool 안정화 선행 (seed 민감) · quota 증가 HOLD"
}
```

- tool: `tools/_k_stat_seed_diag.py`
- JSON: `docs/benchmarks/20260805_KSTAT_SEED_DIAG.json`
