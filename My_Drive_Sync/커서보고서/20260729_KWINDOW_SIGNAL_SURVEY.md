# K-WINDOW-SIGNAL-01 — DHLOTTERY 기간창 hint survey (READ-ONLY live WF)

날짜 2026-07-30 · elapsed 7094.1s · **FAIL** · seed=42 · n=1182

개념: 동행복권 4/8/12/52주(+all) 창 내 draws→45차 hint (odd_even·zone_mix·sum_band·miss_pattern) → 3뇌 predict `w[n]*=(1+α·hint[n])` · V2 set_no_asc 유지.

## SUMMARY (BENCH_PROTOCOL §6)
| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) | 비고 |
|-------|----------|------|----------|-----|--------------|-------------|-------------|------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | E[match]=6×6/45 |
| **WIRE-V2 pin** | stored | 1.7504 | 0.1447 | ✓ | +0.0310 | — | — | PINNED |
| **baseline (AUX score)** | WF live | **1.7318** | **0.1108** | — | -0.0029 | -0.0339 | 0.6355 | 채점 유지 · control |
| **best signal** | WF live | **1.7453** | **0.1328** | — | +0.0191 | -0.0119 | 0.0232 | w4_zone_mix@α=0.1 · FAIL |

## variants (window × signal × α · ge3 내림)
| window | signal | α | mean | ge3_rate | ge3_cnt | Δpin | p | verdict |
|--------|--------|--:|-----:|---------:|--------:|-----:|--:|---------|
| w4 | zone_mix | 0.1 | 1.7453 | 0.1328 | 157 | -0.0119 | 0.0232 | FAIL |
| w4 | sum_band | 0.2 | 1.72 | 0.1311 | 155 | -0.0136 | 0.034676 | FAIL |
| w8 | miss_pattern | 0.2 | 1.7081 | 0.1303 | 154 | -0.0144 | 0.041989 | FAIL |
| w4 | miss_pattern | 0.05 | 1.7335 | 0.1269 | 150 | -0.0178 | 0.0847 | FAIL |
| w12 | odd_even | 0.05 | 1.7487 | 0.1261 | 149 | -0.0186 | 0.099356 | FAIL |
| w12 | zone_mix | 0.05 | 1.7217 | 0.1261 | 149 | -0.0186 | 0.099356 | FAIL |
| wall | odd_even | 0.05 | 1.7183 | 0.1261 | 149 | -0.0186 | 0.099356 | FAIL |
| w4 | sum_band | 0.05 | 1.7411 | 0.1252 | 148 | -0.0195 | 0.115819 | FAIL |
| w4 | odd_even | 0.1 | 1.7377 | 0.1244 | 147 | -0.0203 | 0.13417 | FAIL |
| w52 | zone_mix | 0.1 | 1.7014 | 0.1227 | 145 | -0.0220 | 0.176742 | FAIL |
| wall | zone_mix | 0.1 | 1.7284 | 0.1218 | 144 | -0.0229 | 0.200997 | FAIL |
| w8 | sum_band | 0.2 | 1.7343 | 0.1201 | 142 | -0.0246 | 0.255289 | FAIL |
| w8 | zone_mix | 0.05 | 1.7259 | 0.1193 | 141 | -0.0254 | 0.285154 | FAIL |
| w52 | miss_pattern | 0.1 | 1.7124 | 0.1193 | 141 | -0.0254 | 0.285154 | FAIL |
| w52 | sum_band | 0.05 | 1.7217 | 0.1184 | 140 | -0.0263 | 0.316656 | FAIL |
| w52 | sum_band | 0.1 | 1.7098 | 0.1184 | 140 | -0.0263 | 0.316656 | FAIL |
| w8 | miss_pattern | 0.05 | 1.7318 | 0.1176 | 139 | -0.0271 | 0.349617 | FAIL |
| w12 | odd_even | 0.1 | 1.7318 | 0.1176 | 139 | -0.0271 | 0.349617 | FAIL |
| w52 | zone_mix | 0.2 | 1.7098 | 0.1176 | 139 | -0.0271 | 0.349617 | FAIL |
| wall | zone_mix | 0.2 | 1.7343 | 0.1159 | 137 | -0.0288 | 0.419039 | FAIL |
| w52 | odd_even | 0.1 | 1.7183 | 0.1159 | 137 | -0.0288 | 0.419039 | FAIL |
| wall | sum_band | 0.2 | 1.7115 | 0.1159 | 137 | -0.0288 | 0.419039 | FAIL |
| w12 | sum_band | 0.05 | 1.6963 | 0.1159 | 137 | -0.0288 | 0.419039 | FAIL |
| w8 | zone_mix | 0.1 | 1.736 | 0.1151 | 136 | -0.0296 | 0.454991 | FAIL |
| w4 | zone_mix | 0.2 | 1.7225 | 0.1151 | 136 | -0.0296 | 0.454991 | FAIL |
| … | … | … | … | … | … | … | … | (+35 more in JSON) |

## 창별 best (signal·α)
| window | best label | ge3 | p | verdict |
|--------|------------|-----|---|---------|
| w4 | w4_zone_mix@α=0.1 | 0.1328 | 0.0232 | FAIL |
| w8 | w8_miss_pattern@α=0.2 | 0.1303 | 0.041989 | FAIL |
| w12 | w12_odd_even@α=0.05 | 0.1261 | 0.099356 | FAIL |
| w52 | w52_zone_mix@α=0.1 | 0.1227 | 0.176742 | FAIL |
| wall | wall_odd_even@α=0.05 | 0.1261 | 0.099356 | FAIL |

## tier 피벗 (best signal · BENCH_PROTOCOL §7)
| scope | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |
|-------|----|----|----|----|----|-----|--------|
| selected_5 | 0 | 0 | 1 | 6 | 162 | 169 | 5910 |

## Verdict
- **PASS gate:** ge3 > pin 0.1447 AND p < 0.05 → **False**
- **best signal:** `w4_zone_mix@α=0.1` ge3=0.1328 p=0.0232
- **→ `K-ATTACK-HOLD`** · E3 PATTERN-HINT-03 또는 다른 축

## 팩트체크
| 항목 | JSON | 보고서 |
|------|------|--------|
| n_eval | 1182 | 1182 |
| baseline ge3 | 0.1108 | 0.1108 |
| best signal ge3 | 0.1328 | 0.1328 |
| pass_gate | False | False |
| seed | 42 | 42 |
| coordinator_modified | False | False |

SSOT=`docs/benchmarks/20260729_KWINDOW_SIGNAL_survey.json` · inject=survey random.choices wrapper only
