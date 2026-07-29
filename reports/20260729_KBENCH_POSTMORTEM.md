# K-BENCH-01 — postmortem 진단 (READ-ONLY live WF)

날짜 2026-07-29 · elapsed 212.1s · **SIGNAL_FOUND** · seed=42

## SUMMARY (BENCH_PROTOCOL §6)
| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | p (vs null) | 비고 |
|-------|----------|------|----------|-----|--------------|-------------|------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | E[match]=6×6/45 |
| **WIRE-V2 pin** | stored | 1.7504 | 0.1447 | ✓ | — | — | PINNED |
| **K-BENCH-01 WF** | WF live | **1.7191** | **0.11** | — | -0.0037 | 0.6696 | n_eval=1182 · selected best-of-5 |

## tier 피벗 (BENCH_PROTOCOL §7 · WF live)

### 선택 5장 (set_no_asc 쿼터)
| scope | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |
|-------|----------|----|----|----|----|----|-----|--------|
| selected_5 | WF live | 0 | 0 | 0 | 7 | 132 | 139 | 5910 |

### 전체 15장
| scope | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |
|-------|----------|----|----|----|----|----|-----|--------|
| all_15 | WF live | 0 | 0 | 1 | 18 | 398 | 417 | 17730 |

### 뇌별 tier (선택 5 · quota별)
| brain | r3 | r4 | r5 | ge3 | n_sets |
|-------|----|----|----|-----|--------|
| markov | 0 | 5 | 75 | 80 | 3546 |
| stat | 0 | 2 | 28 | 30 | 1182 |
| review | 0 | 0 | 29 | 29 | 1182 |

## 집계
- **쿼터 갭:** 516/1182 (43.6%) — 15중 best > 선택5 best
- **갭 평균(놓친 회차):** 1.188
- **15중 best-hit 뇌 비율:**
  - markov: 52.5%
  - stat: 29.9%
  - review: 17.5%

### ge3+ vs ge3- draw_features
| feature | ge3+ mean | ge3- mean | Δ |
|---------|----------:|----------:|--:|
| sum | 139.2 | 138.063 | 1.137 |
| odd_count | 2.954 | 3.084 | -0.13 |
| ac | 8.023 | 7.993 | 0.03 |
| consecutive | 0.638 | 0.657 | -0.019 |

### AUX ↔ hit_count 상관 (15×n_eval 세트)
| axis | spearman ρ | p | n |
|------|----------:|--:|--:|
| aux_total | -0.0003 | 0.973305 | 17730 |
| miss | null | null | 17730 |
| pattern | 0.0045 | 0.551585 | 17730 |
| balance | -0.0035 | 0.643513 | 17730 |
| referee | null | null | 17730 |

### AUX total 사분위 bin
| bin | n | aux_total_mean | hit_mean |
|-----|--:|---------------:|---------:|
| Q1_low | 4432 | 0.6898 | 0.7996 |
| Q2 | 4432 | 0.7254 | 0.8093 |
| Q3 | 4432 | 0.744 | 0.8057 |
| Q4_high | 4434 | 0.7651 | 0.7894 |

## 발견 패턴
- 쿼터 갭: 43.6% 회차에서 15중 best > 선택5 best (평균 gap=1.188)
- 뇌 지배: markov가 15중 best 52.5%

## 다음 피드백 축 후보 (코드 수정 없음 · 제안만)
- 쿼터 대안 survey: set_no_asc 대신 뇌 내 AUX/confidence top-1 유지 + 쿼터 (K-BENCH-02 재확인 — baseline 우수 시 HOLD)
- 뇌별 quota 재검토: markov best-hit 52.5% — quota≠실력 가능
- ge3+ 회차 draw_features bin별 stratify (K-BENCH-04 후보)

## Verdict / NEXT
- **verdict:** `SIGNAL_FOUND`
- **→ `K-BENCH-01-WIRE`** (형 GO 필요 · coordinator 수정 금지)

*진단 survey — ge3 PASS/FAIL 아님. pin 대비 ge3는 참고용.*

---

## 팩트체크
| 항목 | JSON | 보고서 |
|------|------|------|
| n_eval | 1182 | 1182 |
| ge3_rate | 0.11 | 0.11 |
| quota_missed_rate | 0.4365 | 0.4365 |
| verdict | SIGNAL_FOUND | SIGNAL_FOUND |
| seed | 42 | 42 |

ASCII `-` 구분 · SSOT=`docs/benchmarks/20260729_KBENCH_POSTMORTEM.json`
