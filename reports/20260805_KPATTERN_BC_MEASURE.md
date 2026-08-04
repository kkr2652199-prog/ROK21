# K-PATTERN-BC-MEASURE — B·C 패턴 실측 (2026-08-05)

- **판정:** `MEASURED` · wire=`False` · n=1235
- **범위:** draw 1~1235
- **금지:** 발권 ge3 클레임 · engine wire · 당첨P↑ 주장

## 요약

| 축 | 신호(진단) |
|----|------------|
| B 구조전환 | **MODERATE** |
| C PMI클러스터 | **STRONG** |
| C top/bottom mean비 | **6.574746** |

> 당첨회차 내부 진단 · 발권 ge3 클레임 금지 · zone은 6번호가 저/중/고 2구역 이상이면 mix → 대부분 mix라 런이 매우 김

## B — 구조 전환 사이클

> **zone 주의:** 정의상 2구역 이상 포함=mix. 6번호 당첨은 거의 항상 mix → 런 mean/max가 비정상적으로 큼. odd_k·sum_tier가 전환 신호의 주 축.

| 레이블 | run mean | median | p90 | max | thr(p90) | current@1235 | 임박 |
|--------|----------|--------|-----|-----|----------|--------------|------|
| odd_k | 1.351204 | 1.0 | 2.0 | 8 | 2 | 1 | 미임박 |
| zone | 176.428571 | 73 | 115.0 | 965 | 115 | 73 | 미임박 |
| sum_tier | 1.614379 | 1 | 3.0 | 10 | 3 | 5 | 임박 |

- 1235 레이블: `{'odd_k': 5, 'zone': 'mix', 'sum_tier': 'mid'}`
- success: `{'B_has_run_dist': True, 'B_has_threshold': True, 'B_has_current': True}`

### 런 hist

- **odd_k:** `{'1': 698, '2': 150, '3': 41, '4': 16, '5plus': 9}`
- **zone:** `{'1': 3, '2': 0, '3': 0, '4': 0, '5plus': 4}`
- **sum_tier:** `{'1': 494, '2': 167, '3': 59, '4': 25, '5plus': 20}`

## C — PMI 클러스터

- top20 pairs used: 20
- cluster mean/median/p90: 0.463158 / 0 / 1.0
- frac_ge2=0.069636 · frac_zero=0.615385
- hist: `{'0': 760, '1': 389, '2': 75, '3plus': 11}`

### 전이 (예측 클레임 금지)

- after_high(n=86): `{'0': 0.639535, '1': 0.313953, 'ge2': 0.046512}`
- after_low(n=759): `{'0': 0.629776, '1': 0.299078, 'ge2': 0.071146}`

### bottom10 대조

- mean=0.070445 · frac_ge2=0.001619
- hist: `{'0': 1150, '1': 83, '2': 2, '3plus': 0}`
- note: top20 vs bottom10 · PMI 가설 교차검증
- success: `{'C_has_cluster_dist': True, 'C_has_transition': True, 'C_has_bottom_contrast': True}`

## 산출물

- JSON: `docs/benchmarks/20260805_KPATTERN_BC_MEASURE.json`
- tool: `tools/_k_pattern_bc_measure.py`
