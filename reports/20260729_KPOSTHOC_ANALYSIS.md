# K-POSTHOC-ANALYSIS — 200시드 역추적 분석

날짜 2026-07-29 · elapsed 6956.4s · **신호발견**

## 전제
| 항목 | 값 |
|------|-----|
| 시드 수 | 200 |
| draw 범위 | 53~1234 (200회) |
| wire pin ge3 | 0.1447 |
| null ge3 | 0.1137 |
| 쿼터 | markov×3 + stat×1 + review×1 |
| pipeline | live predict_sets → apply_coordinator_scoring → apply_markov_wire_quota |

## 시드별 ge3 분포
| 지표 | 값 |
|------|-----|
| mean | **0.1116** |
| std | 0.0221 |
| median | 0.11 |
| min | 0.045 |
| max | 0.18 |
| best seed | #101 ge3=0.18 p=0.003679 |

## 상위 10% vs 하위 10% 비교

### 뇌별 ge3 (선택된 세트)
| 뇌 | top 10% | bot 10% | Δ |
|------|---:|---:|---:|
| markov | 0.0343 | 0.0152 | +0.0191 |
| stat | 0.032 | 0.0145 | +0.0175 |
| review | 0.0288 | 0.0205 | +0.0083 |

### 뇌별 mean (선택된 세트)
| 뇌 | top 10% | bot 10% | Δ |
|------|---:|---:|---:|
| markov | 0.8203 | 0.7751 | +0.0452 |
| stat | 0.8283 | 0.8057 | +0.0226 |
| review | 0.7542 | 0.757 | -0.0028 |

### 선택 vs 비선택 ge3
| 그룹 | selected ge3 | non-selected ge3 |
|------|---:|---:|
| top 10% | 0.0327 | 0.023 |
| bot 10% | 0.0161 | 0.0228 |

### 적중 회차 특성 (≥3 적중 시)
| 특성 | top 10% | bot 10% | Δ |
|------|---:|---:|---:|
| 합계 평균 | 143.2 | 146.1 | -2.9 |
| 홀수 비율 | 0.494 | 0.503 | -0.009 |
| 연속번호 비율 | 0.512 | 0.55 | -0.038 |
| AC값 평균 | 8.06 | 8.05 | 0.01 |

## 신호 판정
**신호 발견:** markov ge3 top/bot=0.0343/0.0152 (×2.26) · stat ge3 top/bot=0.032/0.0145 (×2.21) · review ge3 top/bot=0.0288/0.0205 (×1.40) · sum top-bot diff=-2.9 · AC top-bot diff=0.01 · consec top-bot diff=-0.038 · odd_ratio top-bot diff=-0.009

## Verdict / NEXT
**→ `K-POSTHOC-WIRE`**

발견된 신호를 기반으로 live 격자 탐색 가능 (형 승인 필요).

---

## 팩트체크
| 항목 | JSON | 보고서 |
|------|------|------|
| n_seeds | 200 | 200 |
| draw_range | [53, 1234] | 53~1234 |
| overall mean_ge3 | 0.1116 | 0.1116 |
| best seed ge3 | 0.18 | 0.18 |
| best seed p | 0.003679 | 0.003679 |
| signal_detected | True | 신호발견 |

ASCII `-` 구분 · 숫자 SSOT=`docs/benchmarks/20260729_KPOSTHOC_analysis.json`
