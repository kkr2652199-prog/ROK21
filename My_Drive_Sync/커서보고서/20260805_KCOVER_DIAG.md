# K-COVER-DIAG — 세트 중복 + cold-free 보강 (2026-08-05)

- **판정:** `NORMAL` · wire=`False` · n=200

## overlap

| 지표 | 실측 | 기대 |
|------|------|------|
| avg Jaccard | **0.108252** | 0.122 |
| avg unique/draw | **20.73** | 26.5 |
| bias_rate_ge2 | 0.563833 | — |
| verdict | **NORMAL** | — |

- unique hist: `{'17': 1, '18': 9, '19': 29, '20': 44, '21': 67, '22': 26, '23': 19, '24': 5}`

## cold_free_replace

```json
{
  "n_replaced_draws": 160,
  "n_skip_no_candidate": 0,
  "cold_k": 5,
  "before": {
    "avg_jaccard": 0.108252,
    "avg_unique": 20.73,
    "avg_ge3": 0.135
  },
  "after": {
    "avg_jaccard": 0.083498,
    "avg_unique": 22.715,
    "avg_ge3": 0.165
  },
  "delta_ge3": 0.03,
  "delta_unique": 1.985,
  "verdict": "IMPROVE",
  "note": "대체 후보=pool_view_cache repack cold-free · 발권 재생성 아님"
}
```

## by_period

| period | Jaccard | unique | ge3 |
|--------|---------|--------|-----|
| early_1036_1115 | 0.108019 | 20.875 | 0.1375 |
| mid_1116_1175 | 0.110303 | 20.416667 | 0.15 |
| late_1176_1235 | 0.10651 | 20.85 | 0.116667 |

## implication

```json
{
  "cover_wire_viable": false,
  "cold_free_add_viable": true,
  "recommended_next": "cold-free replace wire GO 후보 · 형 승인 후"
}
```

- tool: `tools/_k_cover_diag.py`
- JSON: `docs/benchmarks/20260805_KCOVER_DIAG.json`
