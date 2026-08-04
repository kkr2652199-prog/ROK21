# K-REVIEW-QUOTA-SIM — review quota live 경로 시뮬 (2026-08-05)

- **판정:** `BEST_SCENARIO: A_stat0_markov80_review20` · wire=`False`
- path: `live coordinator BENCH_FIXED_QUOTA · brains.predict_sets → aux → dedup → quota (in-memory · no DB write)`
- range: [1036, 1235] n=200 · seeds=[42, 0, 7]
- rollback_confirmed=**True**

## baseline A

```json
{
  "label": "A_stat0_markov80_review20",
  "slots": {
    "stat": 0,
    "markov": 4,
    "review": 1
  },
  "by_seed": {
    "42": {
      "ge3": 0.135,
      "mean": 1.715
    },
    "0": {
      "ge3": 0.115,
      "mean": 1.72
    },
    "7": {
      "ge3": 0.135,
      "mean": 1.705
    }
  },
  "avg_ge3": 0.128333,
  "range_ge3": 0.02
}
```

## scenarios

| 시나리오 | slots | avg_ge3 | range | Δ vs A | verdict |
|----------|-------|---------|-------|--------|---------|
| B_markov70_review30 | `{'stat': 0, 'markov': 3, 'review': 2}` | **0.126667** | 0.02 | -0.0017 | NO_GAIN |
| C_markov60_review40 | `{'stat': 0, 'markov': 3, 'review': 2}` | **0.126667** | 0.02 | -0.0017 | NO_GAIN |
| D_markov50_review50 | `{'stat': 0, 'markov': 2, 'review': 3}` | **0.123333** | 0.045 | -0.0050 | NO_GAIN |
| E_stat10_markov50_review40 | `{'stat': 1, 'markov': 2, 'review': 2}` | **0.118333** | 0.05 | -0.0100 | DEGRADED |

## best

```json
{
  "label": "A_stat0_markov80_review20",
  "avg_ge3": 0.128333,
  "delta_vs_baseline": 0.0,
  "slots": {
    "stat": 0,
    "markov": 4,
    "review": 1
  },
  "note": "테스트 시나리오 전부 baseline 미상회"
}
```

- note: C 슬롯은 B와 동일(0/3/2) · 정수 배분 한계
- tool: `tools/_k_review_quota_sim.py`
- JSON: `docs/benchmarks/20260805_KREVIEW_QUOTA_SIM.json`
