# K-AUX-SIGNAL-01 — 4보조 신호벡터 survey (READ-ONLY live WF)

날짜 2026-07-29 · elapsed 1504.0s · **FAIL** · seed=42

개념: 4보조 score_set(채점) 대신 draws→45차 hint → 3뇌 predict 가중 `w[n]*=(1+α·hint[n])` · V2 set_no_asc 유지.

## SUMMARY (BENCH_PROTOCOL §6)
| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) | 비고 |
|-------|----------|------|----------|-----|--------------|-------------|-------------|------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | E[match]=6×6/45 |
| **WIRE-V2 pin** | stored | 1.7504 | 0.1447 | ✓ | +0.0310 | — | — | PINNED |
| **baseline (AUX score)** | WF live | **1.7259** | **0.1218** | — | +0.0081 | -0.0229 | 0.201 | 채점 유지 · control |
| **best signal** | WF live | **1.7301** | **0.1303** | — | +0.0166 | -0.0144 | 0.041989 | miss_pattern@α=0.2 · FAIL |

## variants (전체 · α grid)
| variant | α | mean | ge3_rate | ge3_cnt | Δpin | p | verdict |
|---------|--:|-----:|---------:|--------:|-----:|--:|---------|
| miss_pattern | 0.2 | 1.7301 | 0.1303 | 154 | -0.0144 | 0.041989 | FAIL |
| pattern_store_lite | 0.05 | 1.7191 | 0.1235 | 146 | -0.0212 | 0.154467 | FAIL |
| baseline | 0.0 | 1.7259 | 0.1218 | 144 | -0.0229 | 0.200997 | FAIL |
| pattern_store_lite | 0.1 | 1.7098 | 0.1176 | 139 | -0.0271 | 0.349617 | FAIL |
| miss_pattern | 0.1 | 1.7318 | 0.1142 | 135 | -0.0305 | 0.491394 | FAIL |
| combined_signal | 0.1 | 1.7318 | 0.1134 | 134 | -0.0313 | 0.527947 | FAIL |
| combined_signal | 0.2 | 1.6853 | 0.1125 | 133 | -0.0322 | 0.564346 | FAIL |
| pattern_store_lite | 0.2 | 1.709 | 0.1091 | 129 | -0.0356 | 0.702489 | FAIL |
| miss_pattern | 0.05 | 1.7217 | 0.1083 | 128 | -0.0364 | 0.733846 | FAIL |
| balance_hint | 0.1 | 1.692 | 0.1074 | 127 | -0.0373 | 0.763502 | FAIL |
| combined_signal | 0.05 | 1.6946 | 0.1066 | 126 | -0.0381 | 0.791304 | FAIL |
| balance_hint | 0.2 | 1.6794 | 0.1066 | 126 | -0.0381 | 0.791304 | FAIL |
| balance_hint | 0.05 | 1.6988 | 0.1024 | 121 | -0.0423 | 0.899894 | FAIL |

## tier 피벗 (BENCH_PROTOCOL §7 · WF live · best signal)
| scope | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |
|-------|----------|----|----|----|----|----|-----|--------|
| selected_5 | WF live | 0 | 0 | 0 | 8 | 160 | 168 | 5910 |

### 뇌별 tier (best signal · 선택 5)
| brain | r3 | r4 | r5 | ge3 | n_sets |
|-------|----|----|----|-----|--------|
| markov | 0 | 5 | 96 | 101 | 3546 |
| stat | 0 | 2 | 32 | 34 | 1182 |
| review | 0 | 1 | 32 | 33 | 1182 |

## Verdict
- **PASS gate:** ge3 > pin 0.1447 AND p < 0.05 → **False**
- **best:** `miss_pattern@α=0.2` ge3=0.1303 p=0.041989
- **→ `K-ATTACK-HOLD`** 또는 E2/E3 (`AUX_SIGNAL_PIVOT` §6)

## 팩트체크
| 항목 | JSON | 보고서 |
|------|------|--------|
| n_eval | 1182 | 1182 |
| baseline ge3 | 0.1218 | 0.1218 |
| best ge3 | 0.1303 | 0.1303 |
| pass_gate | False | False |
| seed | 42 | 42 |
| coordinator_modified | False | False |

SSOT=`docs/benchmarks/20260729_KAUX_SIGNAL_survey.json` · inject=survey random.choices wrapper only
