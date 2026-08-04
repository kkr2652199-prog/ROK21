# K-EARLY-DIAG — early 취약성 진단 (2026-08-05)

- **판정:** `STRUCTURAL` · wire=`False`
- root_cause: early vs mid: entropyΔ=-0.013956, coldΔ갭=0.011643, sum_meanΔ=8.46 · late ge3=0.116667가 더 낮아 'early만 붕괴' 아님
- wire_implication: early 단독 wire 근거 약함 · cold-free는 mid에서 더 유리(prior VIABLE) · early 전용 패치보다 전구간 cold-free/neighbor 쪽이 우선

## by_period 요약

| period | ge3 | sum_mean | cold_contam | coldΔ | pool_H | top3_rate |
|--------|-----|----------|-------------|-------|--------|-----------|
| early_1036_1115 | 0.1375 | 142.0125 | 0.2875 | +0.0051 | 5.429417 | 0.116204 |
| mid_1116_1175 | 0.15 | 133.55 | 0.313333 | +0.0167 | 5.415461 | 0.110432 |
| late_1176_1235 | 0.116667 | 136.2 | 0.406667 | -0.0009 | 5.438224 | 0.104938 |

## early sum_tier × ge3

`{'low': {'n': 15, 'ge3': 0.2}, 'mid': {'n': 41, 'ge3': 0.146341}, 'high': {'n': 24, 'ge3': 0.083333}}`

## early ge3 hit vs miss 프로파일

- hit: `{'n': 11, 'sum_dist': {'mean': 137.818182, 'std': 31.027314, 'min': 99, 'max': 209}, 'odd_k_dist': {'2': 1, '3': 6, '4': 4}, 'zone_dist': {'mix': 11}, 'sum_tier_dist': {'mid': 6, 'high': 2, 'low': 3}}`
- miss: `{'n': 69, 'sum_dist': {'mean': 142.681159, 'std': 26.839022, 'min': 68, 'max': 193}, 'odd_k_dist': {'0': 2, '1': 5, '2': 23, '3': 19, '4': 17, '5': 3}, 'zone_dist': {'mix': 69}, 'sum_tier_dist': {'mid': 35, 'low': 12, 'high': 22}}`

- tool: `tools/_k_early_diag.py`
- JSON: `docs/benchmarks/20260805_KEARLY_DIAG.json`
