# K-REPACK-HYBRID — pool+몰아주기 조립 ablation

`2026-08-04T03:08:24+00:00` · n=200 · 1035~1234 · **wire 없음**

## 0. 한 줄

뇌별 권고 hybrid(`hy_brain_rec`) vs 현행 몰아주기 Δge3: 1뇌·통계요정 **+0.0400** · 2뇌·흐름술사 **+0.0000** · 3뇌·복습왕 **+0.0300**

- 배포가능 전략이 baseline을 이긴 뇌 존재: **True**
- null5=0.1137 · pin=0.1447

## 1. 전략 정의

| ID | 내용 | 배포 |
|----|------|------|
| `baseline_repack` | 현행 몰아주기 rank1~5 | OK |
| `pool_asc_1_5` | pool set 1~5 그대로 | OK |
| `pool_late_6_10` | pool set 6~10 그대로 | OK |
| `hy_freq2_r123` | freq상위 pool2 + 몰1~3 | OK |
| `hy_freq2_r145` | freq상위 pool2 + 몰1/4/5 | OK |
| `hy_freq2_r13_r2` | freq상위 pool2 + 몰1/2/3 (몰5 제외) | OK |
| `hy_p45_r123` | pool4+5 + 몰1~3 | OK |
| `hy_p89_r145` | pool8+9 + 몰1/4/5 | OK |
| `hy_freq3_r12` | freq상위 pool3 + 몰1~2 | OK |
| `hy_brain_rec` | 뇌별 권고 조립(stat/review=p45+r123, markov=p89+r145) | OK |
| `oracle_best_pool5` | pool 적중순 상위5 (상한·배포금지) | 금지 |

## 2. 뇌×전략 ge3_rate

| 전략 | stat | markov | review |
|------|-----:|-------:|-------:|
| `baseline_repack` | **0.1250** | **0.1300** | **0.1050** |
| `hy_brain_rec` | 0.1650 (+0.0400) | 0.1300 (+0.0000) | 0.1350 (+0.0300) |
| `hy_freq2_r123` | 0.1100 (-0.0150) | 0.1050 (-0.0250) | 0.1150 (+0.0100) |
| `hy_freq2_r145` | 0.1100 (-0.0150) | 0.1200 (-0.0100) | 0.0950 (-0.0100) |
| `hy_p45_r123` | 0.1650 (+0.0400) | 0.1000 (-0.0300) | 0.1350 (+0.0300) |
| `hy_p89_r145` | 0.1450 (+0.0200) | 0.1300 (+0.0000) | 0.1000 (-0.0050) |
| `hy_freq3_r12` | 0.0950 (-0.0300) | 0.1000 (-0.0300) | 0.1150 (+0.0100) |
| `pool_asc_1_5` | 0.1500 (+0.0250) | 0.0800 (-0.0500) | 0.1300 (+0.0250) |
| `pool_late_6_10` | 0.1300 (+0.0050) | 0.1150 (-0.0150) | 0.1200 (+0.0150) |
| `oracle_best_pool5` | 0.2450 (+0.1200) | 0.1900 (+0.0600) | 0.2050 (+0.1000) |

## 3. 뇌별 승자 (배포가능)

### 1뇌·통계요정
- baseline **0.125** → best `hy_brain_rec` **0.165**
  - `hy_brain_rec` ge3=0.165 Δ=+0.0400
  - `hy_p45_r123` ge3=0.165 Δ=+0.0400
  - `pool_asc_1_5` ge3=0.15 Δ=+0.0250

### 2뇌·흐름술사
- baseline **0.13** → best `baseline_repack` **0.13**
  - `baseline_repack` ge3=0.13 Δ=+0.0000
  - `hy_brain_rec` ge3=0.13 Δ=+0.0000
  - `hy_p89_r145` ge3=0.13 Δ=+0.0000

### 3뇌·복습왕
- baseline **0.105** → best `hy_brain_rec` **0.135**
  - `hy_brain_rec` ge3=0.135 Δ=+0.0300
  - `hy_p45_r123` ge3=0.135 Δ=+0.0300
  - `pool_asc_1_5` ge3=0.13 Δ=+0.0250

## 4. 해석 · 다음 wire 후보

| 뇌 | 권고 | Δ vs baseline | 비고 |
|----|------|---------------|------|
| stat | **hy_p45_r123 wire GO** | **+0.0400** → ge3 0.165 | pin(0.1447) 상회 |
| review | **hy_p45_r123 wire GO** | **+0.0300** → ge3 0.135 | null 상회 |
| markov | **baseline 유지** | 0.0000 | hybrid 동률 · fusion 80%라 무리 교체 비권고 |

- oracle_best_pool5는 **상한** — 선택기 없이는 달성 불가
- 다음 지시서 후보: `K-REPACK-HYBRID-WIRE` — signal_pool 조립만(stat/review) · markov 현행 · coordinator 미수정 · QUICK→FULL
- fusion 5장(markov4+review1)에 review 슬롯만 hybrid 적용하는 A/B도 가능

## 근거

- PER_BRAIN / DECOMPOSE / PIN-GAP 진단
- pool_view_cache · coordinator wire 없음
