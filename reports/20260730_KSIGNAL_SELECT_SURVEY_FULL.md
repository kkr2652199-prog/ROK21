# K-SIGNAL-SELECT-FULL — 신호셋트 선별 축 survey (전체 검증(1182회) · READ-ONLY live WF)

날짜 2026-07-30 · elapsed 86.7s · **FAIL** · seed=42 · n=1182 · gate=full

개념: 3뇌×10 pool (survey 2-pass) → 통합 5 신호셋트 · window hint=w4_zone_mix@α=0.1 (K-WINDOW best).

## SUMMARY (BENCH_PROTOCOL §6)
| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) | 비고 |
|-------|----------|------|----------|-----|--------------|-------------|-------------|------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | E[match]=6×6/45 |
| **WIRE-V2 pin** | stored | 1.7504 | 0.1447 | ✓ | +0.0310 | — | — | PINNED |
| **set_no_asc (control)** | WF live | **1.7005** | **0.1091** | — | -0.0046 | -0.0356 | 0.702489 | V2 quota baseline |
| **best selector** | WF live | **1.7377** | **0.1218** | — | +0.0081 | -0.0229 | 0.200997 | `combined` · FAIL |

## selectors (ge3 내림)
| selector | mean | ge3_rate | ge3_cnt | Δpin | Δnull | p | verdict |
|----------|-----:|---------:|--------:|-----:|------:|--:|---------|
| combined | 1.7377 | 0.1218 | 144 | -0.0229 | +0.0081 | 0.200997 | FAIL |
| set_no_asc | 1.7005 | 0.1091 | 129 | -0.0356 | -0.0046 | 0.702489 | FAIL |
| bin_match | 1.7098 | 0.1058 | 125 | -0.0389 | -0.0079 | 0.817137 | FAIL |
| window_overlap | 1.681 | 0.1041 | 123 | -0.0406 | -0.0096 | 0.862645 | FAIL |
| jaccard_div | 1.6041 | 0.1024 | 121 | -0.0423 | -0.0113 | 0.899894 | FAIL |

## Verdict
- **gate (full):** any selector ge3>0.1447 and p<0.05 → **FAIL**
- **best selector:** `combined` ge3=0.1218 p=0.200997
- **recommended_next:** K-ATTACK-HOLD

## 팩트체크
| 항목 | JSON | 보고서 |
|------|------|--------|
| n_eval | 1182 | 1182 |
| baseline ge3 | 0.1091 | 0.1091 |
| best ge3 | 0.1218 | 0.1218 |
| pass_gate | False | False |
| coordinator_modified | False | False |
