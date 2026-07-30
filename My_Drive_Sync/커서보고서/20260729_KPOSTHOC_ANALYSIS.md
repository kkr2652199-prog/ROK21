# K-POSTHOC-ANALYSIS — 200시드 역추적 분석

날짜 2026-07-30 · elapsed 36301.7s · **신호발견**

## 전제
| 항목 | 값 |
|------|-----|
| 시드 수 | 200 |
| draw 범위 | 53~1234 (1182회) |
| wire pin ge3 | 0.1447 |
| null ge3 | 0.1137 |
| 쿼터 | markov×3 + stat×1 + review×1 |
| pipeline | live predict_sets → apply_coordinator_scoring → apply_markov_wire_quota |

## 시드별 ge3 분포
| 지표 | 값 |
|------|-----|
| mean | **0.1134** |
| std | 0.0094 |
| median | 0.1134 |
| min | 0.0871 |
| max | 0.1413 |
| best seed | #19 ge3=0.1413 p=0.002116 |

## 상위 10% vs 하위 10% 비교

### 뇌별 ge3 (선택된 세트)
| 뇌 | top 10% | bot 10% | Δ |
|------|---:|---:|---:|
| markov | 0.0267 | 0.0203 | +0.0064 |
| stat | 0.0276 | 0.0212 | +0.0064 |
| review | 0.0296 | 0.0215 | +0.0081 |

### 뇌별 mean (선택된 세트)
| 뇌 | top 10% | bot 10% | Δ |
|------|---:|---:|---:|
| markov | 0.8054 | 0.7916 | +0.0138 |
| stat | 0.8057 | 0.7928 | +0.0129 |
| review | 0.8173 | 0.7997 | +0.0176 |

### 선택 vs 비선택 ge3
| 그룹 | selected ge3 | non-selected ge3 |
|------|---:|---:|
| top 10% | 0.0275 | 0.0243 |
| bot 10% | 0.0207 | 0.0237 |

### 적중 회차 특성 (≥3 적중 시)
| 특성 | top 10% | bot 10% | Δ |
|------|---:|---:|---:|
| 합계 평균 | 137.9 | 138.9 | -1.0 |
| 홀수 비율 | 0.499 | 0.5 | -0.001 |
| 연속번호 비율 | 0.511 | 0.499 | 0.012 |
| AC값 평균 | 8.05 | 8.03 | 0.02 |

## 신호 판정
**신호 발견:** markov ge3 top/bot=0.0267/0.0203 (×1.32) · stat ge3 top/bot=0.0276/0.0212 (×1.30) · review ge3 top/bot=0.0296/0.0215 (×1.38) · sum top-bot diff=-1.0 · AC top-bot diff=0.02 · consec top-bot diff=0.012 · odd_ratio top-bot diff=-0.001

## Verdict / NEXT
**→ `K-POSTHOC-WIRE`**

발견된 신호를 기반으로 live 격자 탐색 가능 (형 승인 필요).

---

## 팩트체크
| 항목 | JSON | 보고서 |
|------|------|------|
| n_seeds | 200 | 200 |
| draw_range | [53, 1234] | 53~1234 |
| overall mean_ge3 | 0.1134 | 0.1134 |
| best seed ge3 | 0.1413 | 0.1413 |
| best seed p | 0.002116 | 0.002116 |
| signal_detected | True | 신호발견 |

ASCII `-` 구분 · 숫자 SSOT=`docs/benchmarks/20260729_KPOSTHOC_analysis.json`
