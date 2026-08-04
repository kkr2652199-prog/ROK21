# K-COLD-EXCLUDE-DIAG — cold 번호 제외 진단 (2026-08-05)

- **판정:** `MARGINAL` · wire=`False` · n=200
- EMA H=8 · α=0.2222 · 사후필터(lotto_predictions SELECT-ONLY)

## cold_sets

| k | contam | clean_n | clean_ge3 | all_ge3 | Δ | verdict |
|---|--------|---------|-----------|---------|---|---------|
| cold_k3 | 0.187 | 813 | 0.03567 | 0.03 | +0.0057 | **MARGINAL** |
| cold_k5 | 0.331 | 669 | 0.037369 | 0.03 | +0.0074 | **MARGINAL** |
| cold_k7 | 0.452 | 548 | 0.032847 | 0.03 | +0.0028 | **NOT_VIABLE** |

## by_period

### early_1036_1115
| k | clean_ge3 | all_ge3 | Δ |
|---|-----------|---------|---|
| cold_k3 | 0.036697 | 0.03 | +0.0067 |
| cold_k5 | 0.035088 | 0.03 | +0.0051 |
| cold_k7 | 0.033058 | 0.03 | +0.0031 |

### mid_1116_1175
| k | clean_ge3 | all_ge3 | Δ |
|---|-----------|---------|---|
| cold_k3 | 0.043307 | 0.036667 | +0.0066 |
| cold_k5 | 0.053398 | 0.036667 | +0.0167 |
| cold_k7 | 0.041667 | 0.036667 | +0.0050 |

### late_1176_1235
| k | clean_ge3 | all_ge3 | Δ |
|---|-----------|---------|---|
| cold_k3 | 0.025862 | 0.023333 | +0.0025 |
| cold_k5 | 0.022472 | 0.023333 | -0.0009 |
| cold_k7 | 0.021739 | 0.023333 | -0.0016 |

## best

```json
{
  "cold_k": 5,
  "delta": 0.007369,
  "viable": false,
  "verdict": "MARGINAL",
  "clean_ge3": 0.037369,
  "all_ge3": 0.03
}
```

- tool: `tools/_k_cold_exclude_diag.py`
- JSON: `docs/benchmarks/20260805_KCOLD_EXCLUDE_DIAG.json`
