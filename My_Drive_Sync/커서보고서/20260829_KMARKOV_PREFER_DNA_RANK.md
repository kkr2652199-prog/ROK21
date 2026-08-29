# K-MARKOV-PREFER-DNA-RANK

시각: 2026-08-29T13:37:21+09:00 · **APPLY_OK** · APPLY=함 · markov만 · 1237아님 · hits 클레임 금지
목적=선호번호 DNA(prefer_table=인기회+생일대)를 발권 순위에 살림. 금액표·1y표 미사용.

## S0) 프로세스·DNA 실측

파이프: `transition walk → learn → prefer mix → top25 choices → aux → diversity`.
PREFER_WIRE=True · W_CROWD markov=0.9 · W_STRUCT=0.1 · BLEND=0.55.
as_of1236 peekOK=True.
ρ 가중OFF(곱셈블렌드)↔prefer=0.2248 · ON(순위혼합)↔prefer=0.9266.
OFF ρ가 낮으면 전이 방문횟수가 선호표를 눌러 DNA가 순위 주인이 아님.

## S1) 패치

`MARKOV_PREFER_RANK_MIX` 기본 True · α=0.70 · `mix_by_rank(visit, prefer_table)`.
`random.choices` 불변. prize_table/stat 1y 미호출. markov W_CROWD/W_STRUCT 불변.
파일 MIX True=True · False=False · 라이브=True.

## S2) 게이트 1137–1236 n100 OFF↔ON (markov pool10)

peek=0 · n=100 · size_bad=0 · bonus_in=0 · seed=42.

| 축 | OFF(곱셈) | ON(순위) | Δ |
|----|-----------|----------|---|
| prefer | 0.019451 | 0.054215 | 0.034764 |
| bday(≤31 개수) | 4.211 | 4.322 | 0.111 |
| hi32 모니터 | 1.789 | 1.678 | -0.111 |
| prize 모니터 | 0.008838 | 0.021716 | 0.012878 |

통과: prefer상승=True · prize ISO(≥−0.005)=True · size_bad0=True.
pred_1237=0 · pred_1239=0 · MAX=1238.

## 판정

**APPLY_OK**. 게이트 통과 · 라이브 MIX True.
review/stat/prize표/choices/몰아주기/kweon 미수정. 엔진 독립 유지.

## 롤백

`MARKOV_PREFER_RANK_MIX=False`

