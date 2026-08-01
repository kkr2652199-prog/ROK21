# K-COMBO-SIGNAL-01 — miss_pattern AND w4_zone_mix AND gate survey

날짜 2026-08-01 · elapsed 18.6s · **PASS** · seed=42 · n=200 · gate=quick

개념: signal_A(miss_pattern α=0.2 · stat/review overlap≥2) **AND** signal_B(w4 zone_hint Δ≤1.0) → 3전략 live WF.

## §6 baseline표 (BENCH_PROTOCOL §6)
| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) |
|-------|----------|-----:|---------:|-----:|-------------:|------------:|------------:|
| **theory_baseline** | — | 0.8000 | 0.1137 | — | — | — | — |
| **WIRE-V2 pin** | stored | 1.7504 | 0.1447 | ✓ | — | — | — |
| baseline_combined | WF live | 1.715 | 0.145 | — | +0.0313 | +0.0003 | 0.102441 |

## §7 전략 비교표
| strategy | ge3_rate | ge3_cnt | mean | ge4_rate | p | Δpin | AB_cov | AB_hit | verdict |
|----------|--------:|--------:|-----:|---------:|--:|-----:|-------:|-------:|---------|
| baseline_combined | 0.145 | 29 | 1.715 | 0.005 | 0.102441 | +0.0003 | 0.0 | — | PASS |
| signal_AB_filter | 0.08 | 16 | 1.68 | 0.01 | 0.952412 | -0.0647 | 0.0 | — | FAIL |
| signal_AB_boost | 0.115 | 23 | 1.765 | 0.01 | 0.509824 | -0.0297 | 0.0 | — | FAIL |

## signal coverage 분석
| signal | True 비율 | True 회차 |
|--------|----------:|----------:|
| signal_A (miss_pattern) | 0.0 | 0 |
| signal_B (w4 zone) | 0.3 | 60 |
| **signal_AB (AND)** | **0.0** | **0** |

## Verdict
- **QUICK PASS:** ge3 > 0.1447 AND p < 0.15 → **True** (baseline_combined만 해당)
- **주의:** signal_A **0%** · signal_AB **0%** — AND 게이트 미발화 · PASS=기존 combined QUICK와 동일
- **best_strategy:** `baseline_combined` ge3=0.145 p=0.102441
- **recommended_next:** K-COMBO-SIGNAL-FULL (단, signal_A 조건 재검토 권고)

## 팩트체크
| 항목 | JSON |
|------|------|
| n_eval | 200 |
| pass_gate | True |
| coordinator_modified | False |

*JSON:* `D:\ROK21\docs\benchmarks\20260801_KCOMBO_SIGNAL_survey.json`
