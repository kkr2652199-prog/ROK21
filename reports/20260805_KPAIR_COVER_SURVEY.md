# K-PAIR-COVER — 저출현쌍 covering survey

📅 2026-08-04 · **HOLD** · wire=**False** · n=**200** (1035~1234)

## 0) 한 줄

as_of 쌍빈도로 희소쌍을 많이·다양하게 담는 5장 재선정. 컨닝 없음 · 1등확률 보증 아님.

## 1) 결과

| 뇌 | baseline | pair_cover | Δ | mean n_rare |
|----|----------:|-----------:|---:|------------:|
| stat | 0.1650 | 0.1550 | -0.0100 | 2.15 |
| markov | 0.1300 | 0.1050 | -0.0250 | 2.20 |
| review | 0.1350 | 0.1150 | -0.0200 | 2.25 |

## 2) 설계 (`pair_cover.py`)

- 쌍빈도: `draw < target` only
- rare = 기대출현 대비 deficit 상위 80쌍
- 탐욕: 새 희소쌍 커버 + 세트 희소점수
- `PAIR_COVER_WIRE=False`

## 3) 판정 **HOLD**

- wire 후보: 없음
- 다음: PAIR_COVER HOLD · AUTO설계문서 또는 다른축 · 형 GO

근거: `20260805_KPAIR_COVER_survey.json`
