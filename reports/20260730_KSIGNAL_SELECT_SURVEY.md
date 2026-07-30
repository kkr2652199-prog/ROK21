# K-SIGNAL-SELECT-01 — 신호셋트 선별 축 survey (READ-ONLY live WF)

날짜 2026-07-30 · elapsed 18.1s · **PASS** · seed=42 · n=200 · gate=quick

개념: 3뇌×10 pool (survey 2-pass) → 통합 5 신호셋트 · window hint=w4_zone_mix@α=0.1 (K-WINDOW best).

## SUMMARY (BENCH_PROTOCOL §6)
| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) | 비고 |
|-------|----------|------|----------|-----|--------------|-------------|-------------|------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | E[match]=6×6/45 |
| **WIRE-V2 pin** | stored | 1.7504 | 0.1447 | ✓ | +0.0310 | — | — | PINNED |
| **set_no_asc (control)** | WF live | **1.68** | **0.08** | — | -0.0337 | -0.0647 | 0.952412 | V2 quota baseline |
| **best selector** | WF live | **1.715** | **0.145** | — | +0.0313 | +0.0003 | 0.102441 | `combined` · PASS |

## selectors (ge3 내림)
| selector | mean | ge3_rate | ge3_cnt | Δpin | Δnull | p | verdict |
|----------|-----:|---------:|--------:|-----:|------:|--:|---------|
| combined | 1.715 | 0.145 | 29 | +0.0003 | +0.0313 | 0.102441 | PASS |
| bin_match | 1.68 | 0.115 | 23 | -0.0297 | +0.0013 | 0.509824 | FAIL |
| jaccard_div | 1.595 | 0.115 | 23 | -0.0297 | +0.0013 | 0.509824 | FAIL |
| set_no_asc | 1.68 | 0.08 | 16 | -0.0647 | -0.0337 | 0.952412 | FAIL |
| window_overlap | 1.64 | 0.08 | 16 | -0.0647 | -0.0337 | 0.952412 | FAIL |

## Verdict
- **gate (quick):** any selector ge3>0.1137 and p<0.15 (QUICK exploration) → **PASS**
- **best selector:** `combined` ge3=0.145 p=0.102441
- **recommended_next:** K-SIGNAL-SELECT-FULL

## 팩트체크
| 항목 | JSON | 보고서 |
|------|------|--------|
| n_eval | 200 | 200 |
| baseline ge3 | 0.08 | 0.08 |
| best ge3 | 0.145 | 0.145 |
| pass_gate | True | True |
| coordinator_modified | False | False |
