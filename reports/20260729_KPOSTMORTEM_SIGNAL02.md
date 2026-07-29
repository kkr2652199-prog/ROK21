# K-POSTMORTEM-SIGNAL-02 — ge3+ draw_features bin stratification

날짜 2026-07-29 · READ-ONLY · source=`20260729_KBENCH_POSTMORTEM.json`

전체 n=**1182** · ge3+ draws=**130** · overall ge3_rate=**0.11**

## Highlights (축별 best bin · lift vs overall)

| axis | best bin | ge3_rate | n | lift | worst bin | worst ge3 |
|------|----------|---------:|--:|-----:|-----------|----------:|
| sum_band | mid(120-155) | 0.1137 | 510 | +0.0037 | high(>155) | 0.1066 |
| odd_count | odd=2 | 0.1412 | 262 | +0.0312 | odd=4 | 0.0871 |
| ac | ac>=9 | 0.1206 | 423 | +0.0106 | ac7-8 | 0.1005 |
| consecutive | cons=1 | 0.114 | 465 | +0.0040 | cons>=2 | 0.0979 |

## sum_band

| bin | total | ge3+ | ge3_rate | % of all |
|-----|------:|-----:|---------:|---------:|
| mid(120-155) | 510 | 58 | 0.1137 | 0.4315 |
| low(<120) | 325 | 35 | 0.1077 | 0.275 |
| high(>155) | 347 | 37 | 0.1066 | 0.2936 |

## odd_count

| bin | total | ge3+ | ge3_rate | % of all |
|-----|------:|-----:|---------:|---------:|
| odd=2 | 262 | 37 | 0.1412 | 0.2217 |
| odd=3 | 419 | 48 | 0.1146 | 0.3545 |
| odd=6 | 19 | 2 | 0.1053 | 0.0161 |
| odd=5 | 93 | 9 | 0.0968 | 0.0787 |
| odd=1 | 79 | 7 | 0.0886 | 0.0668 |
| odd=4 | 310 | 27 | 0.0871 | 0.2623 |

## ac

| bin | total | ge3+ | ge3_rate | % of all |
|-----|------:|-----:|---------:|---------:|
| ac>=9 | 423 | 51 | 0.1206 | 0.3579 |
| ac<=6 | 182 | 21 | 0.1154 | 0.154 |
| ac7-8 | 577 | 58 | 0.1005 | 0.4882 |

## consecutive

| bin | total | ge3+ | ge3_rate | % of all |
|-----|------:|-----:|---------:|---------:|
| cons=1 | 465 | 53 | 0.114 | 0.3934 |
| cons=0 | 574 | 63 | 0.1098 | 0.4856 |
| cons>=2 | 143 | 14 | 0.0979 | 0.121 |

## 판정
- K-BENCH-01 ge3+ 특성 **bin lift는 미약** — E3 hint 설계 시 단일 bin 의존 비권장
- 쿼터갭(43.6%)·markov dominance가 ge3+ 주요 레버 (K-BENCH-01 본문)

SSOT=`docs/benchmarks/20260729_KPOSTMORTEM_SIGNAL02.json`
