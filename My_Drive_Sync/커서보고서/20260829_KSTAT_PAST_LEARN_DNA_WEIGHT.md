# K-STAT-PAST-LEARN-DNA-WEIGHT

시각: 2026-08-29T13:33:18+09:00 · **APPLY_OK** · APPLY=함 · stat만 · 1237아님 · hits 클레임 금지
목적=과거학습 DNA(1y빈도·미출30+)를 발권 가중 순위에 살림. 금액표·선호표·타뇌 미사용.

## S0) 프로세스·DNA 실측

파이프: `transition(OFF) → engine(v2) → aux → past_learn soft → weight_mix → diversity`.
WIRE past_learn=True · v2=True · ASSOC=False · transition=False.
learn adj 이월=0.2 끝수=0.3 미출=0.2 (0이면 boost 고리 비어 있음).
as_of1236 peekOK=True.
ρ 가중OFF↔1y률=0.5279 · ↔gap=-0.458.
ρ 가중ON↔1y률=0.8845 · ↔gap=-0.3296.
OFF에서 1y ρ가 낮으면 DNA는 soft 스티커에만 있고 뽑기 가중의 주인이 아님.

## S1) 패치

`STAT_PAST_LEARN_WEIGHT_WIRE` 기본 True · α=0.70 · 표=0.65×1y률+0.35×미출30+.
순위혼합은 `past_learn._mix_by_rank`(로컬). `prize_table`/`prefer_table` 호출 없음. `random.choices` 불변.
파일 WIRE True=True · False=False · 라이브=True.

## S2) 게이트 1137–1236 n100 OFF↔ON (stat pool10)

peek=0 · n=100 · size_bad=0 · bonus_in=0 · seed=42.

| 축 | OFF | ON | Δ |
|----|-----|-----|---|
| overdue(미출30+ 개수) | 0.014 | 0.069 | 0.055 |
| hot1y 개수 | 3.023 | 3.346 | 0.323 |
| rate1y 평균 | 0.145737 | 0.150077 | 0.00434 |
| gap 평균 | 4.4475 | 4.911167 | 0.463667 |
| prize(모니터) | 0.00127 | 0.001199 | -7.1e-05 |
| prefer(모니터) | 0.00564 | 0.005354 | -0.000286 |

통과: DNA상승=True · prize ISO(≥−0.005)=True · prefer ISO(≤+0.005)=True · size_bad0=True.
pred_1237=0 · pred_1239=0 · MAX=1238.

## 판정

**APPLY_OK**. 게이트 통과 · 라이브 WIRE True.
review/markov/prize표/choices/몰아주기/kweon 미수정. 엔진 독립 유지.

## 롤백

`STAT_PAST_LEARN_WEIGHT_WIRE=False`

