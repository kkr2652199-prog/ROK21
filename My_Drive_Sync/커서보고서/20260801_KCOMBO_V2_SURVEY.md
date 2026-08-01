# K-COMBO-V2 — 번호 steering(배제+신호 boost) survey

날짜 2026-08-01 · elapsed 18.9s · **FAIL** · seed=42 · n=200 · gate=quick

baseline_combined ge3=**0.145** · avg_excluded=6.09 · B3_coverage=1.0

## §6 baseline표
| label | ge3_rate | mean | p | Δpin |
|-------|--------:|-----:|--:|-----:|
| null | 0.1137 | 0.80 | — | — |
| pin | 0.1447 | 1.7504 | — | — |
| baseline_combined | 0.145 | 1.715 | 0.102441 | +0.0003 |

## §7 전략 비교표
| strategy | ge3 | ge3_cnt | mean | p | Δbaseline | avg_excl | B3_cov | verdict |
|----------|----:|--------:|-----:|--:|----------:|---------:|-------:|---------|
| baseline_combined | 0.145 | 29 | 1.715 | 0.102441 | +0.0000 | 6.09 | 1.0 | FAIL |
| exclude_only | 0.145 | 29 | 1.695 | 0.102441 | +0.0000 | 6.09 | 1.0 | FAIL |
| signal_only | 0.14 | 28 | 1.705 | 0.144964 | -0.0050 | 6.09 | 1.0 | FAIL |
| combo_v2 | 0.125 | 25 | 1.695 | 0.338657 | -0.0200 | 6.09 | 1.0 | FAIL |

## Verdict
- **QUICK PASS:** best > baseline(0.145) AND p<0.15 AND avg_excl≤8 → **False**
- **best_strategy:** `baseline_combined`
- **recommended_next:** K-ATTACK-HOLD

*JSON:* `D:\ROK21\docs\benchmarks\20260801_KCOMBO_V2_survey.json`
