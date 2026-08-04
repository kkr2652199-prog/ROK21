# K-PATTERN-OWN-V1 — ROK21 독자 패턴

📅 2026-08-04 · **MEASURED_PARTIAL** · wire=**False** · n=1235

교과서 L1/PMI/EMA와 별도 · **1~1235 당첨 시계열 안에서만** 관측되는 구조.

## A — 출현 간격 가속도

- Δgap summary: `{'n': 7275, 'mean': -0.002062, 'median': 0.0, 'p10': -11.0, 'p90': 11.0, 'min': -72.0, 'max': 71.0}`
- bins: `{'accel_neg': 3402, 'accel_zero': 502, 'accel_pos': 3371}`
- 당첨세트 accel_score: `{'n': 1235, 'mean': -0.007773, 'median': 0.0, 'p10': -5.166667, 'p90': 5.166667, 'min': -13.666667, 'max': 15.333333}`
- contrast: frac_neg=0.491498 · frac_pos=0.48502 · median=0.0

## D — 슬롯 위치 편향

- bias_hits(0~6) summary: `{'n': 1235, 'mean': 3.625911, 'median': 4.0, 'p10': 2.0, 'p90': 5.0, 'min': 1.0, 'max': 6.0}`
- hist: `{4: 315, 2: 208, 3: 286, 5: 252, 1: 72, 6: 102}`
- contrast frac≥4=0.5417 · frac≤1=0.0583

### 슬롯 top5 (요약)

- slot1: 1,3,2,4,6
- slot2: 7,10,12,11,8
- slot3: 19,18,20,13,15
- slot4: 27,31,26,30,33
- slot5: 34,39,37,38,33
- slot6: 45,44,43,42,40

## E — carry 연속성

- carry summary: `{'n': 1234, 'mean': 0.82577, 'median': 1.0, 'p10': 0.0, 'p90': 2.0, 'min': 0.0, 'max': 4.0}` · hist=`{0: 477, 1: 523, 2: 208, 3: 24, 4: 2}`
- zero-run: `{'n': 296, 'mean': 1.611486, 'median': 1.0, 'p10': 1.0, 'p90': 3.0, 'min': 1.0, 'max': 6.0}`
- ge2-run: `{'n': 193, 'mean': 1.212435, 'median': 1.0, 'p10': 1.0, 'p90': 2.0, 'min': 1.0, 'max': 4.0}`
- prior_K5: `{'n': 1233, 'mean': 0.825588, 'median': 0.8, 'p10': 0.4, 'p90': 1.2, 'min': 0.0, 'max': 2.2}`
- contrast Δmean(high−low prior) = **-0.004668** (actual carry mean high=0.86875 low=0.873418)

## F — sum 회귀

- sum summary: `{'n': 1235, 'mean': 138.247773, 'median': 138.0, 'p10': 98.0, 'p90': 177.0, 'min': 48.0, 'max': 238.0}`
- tier rates: `{'high': 0.260729, 'mid': 0.45668, 'low': 0.282591}`
- high→low wait: `{'n': 236, 'mean': 3.207627, 'median': 2.0, 'p10': 1.0, 'p90': 7.0, 'min': 1.0, 'max': 13.0}`
- after high_streak≥2 next: `{'high': 0.244186, 'low': 0.325581, 'mid': 0.430233}`
- after low_streak≥2 next: `{'high': 0.252427, 'low': 0.31068, 'mid': 0.436893}`

## B·C — 설계만 (미측정)

- B: 회차별 odd_k/zone/sum_tier 기록 → 동일 구조 연속 N 분포 → 전환 직전 N = next_transition_signal
- C: PMI top20 페어 · 회차당 동시 포함 cluster_count → cluster≥2 비율 · (나중) 고/저 cluster 세트 ge3 대비

## 성공 체크

- `{'A_has_dist': True, 'D_has_dist': True, 'E_has_contrast_delta': True, 'F_has_contrast': True, 'note': '당첨회차 내부 신호 유/무 대비 · 발권 ge3 클레임 금지'}`

비고: 본 대비는 **당첨 회차 시계열 진단**이다. 발권 ge3↑·당첨P↑ 클레임 금지 · wire 별도 GO.

근거: `20260805_KPATTERN_OWN_V1.json`
