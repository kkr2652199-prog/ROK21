# K-STRUCTURE-COVER — 구조 질량 covering survey

📅 2026-08-04 · **HOLD** · wire=**False** · n=**200** (1035~1234)

## 0) 한 줄

명분(합·존·홀짝·연속)으로 5장이 **구조키를 넓게 덮도록** 재선정. 1등확률 보증 아님 · 현행 repack 대비 ge3만 대조.

## 1) 결과

| 뇌 | baseline ge3 | cover ge3 | Δ | uniq키 base→cover |
|----|-------------:|----------:|---:|------------------:|
| stat | 0.1650 | 0.1450 | -0.0200 | 4.90→5.00 |
| markov | 0.1300 | 0.0850 | -0.0450 | 4.89→5.00 |
| review | 0.1350 | 0.0850 | -0.0500 | 4.88→5.00 |

## 2) 설계 요지 (`structure_cover.py`)

- 축: sum_bucket / odd / zone_key / has_consec
- 질량 가점: 홀짝 2~4 · 합 100~180 · 존 혼합 · **연속 감점 없음**
- 극단(0·6홀, 존≥5) 감점
- 탐욕: 새 구조키 + 부분축 다양성 + 질량
- `STRUCTURE_COVER_WIRE=False` 고정(이번 패치)

## 3) 판정 **HOLD**

- wire 후보 뇌: 없음
- 다음: STRUCTURE_COVER HOLD · 설계모듈 유지 · 형 다음축/AUTO설계

근거: `20260805_KSTRUCTURE_COVER_survey.json` · 명분 `20260805_KMATH_PATTERN_WARRANT.json`
