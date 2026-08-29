# K-REVIEW-TIER1-CONSEC-TIGHTEN

시각: 2026-08-29T13:17:42+09:00 · **APPLY_OK** · APPLY=함 · 1237아님 · hits 클레임 금지
목적=tier1 연번 기준 연번<4 → 연번<3 (2연속까지 허용, 3연속 이상 탈락).

## S0) 변경 전

변경 전 임계=**4** (3연속 통과=True · 4연속 통과=False · 2연속 통과=True).
변경 후 기대 임계=**3** (2연속 통과=True · 3연속 통과=False · 4연속 통과=False).
나머지=합80–210 · 홀수1–5 · 구간2+. 2번×0.75 · 4번 RUN_NEUTRAL=False · prize표 미접촉.

## S1) 패치

`REVIEW_TIER1_CONSEC_MAX` 기본 **3**. 롤백 키=`REVIEW_TIER1_CONSEC_MAX=4`.
파일 MAX=3=True · MAX=4=False · 라이브=3.

## S2) 게이트 1137–1236 n100 before(MAX=4)↔after(MAX=3)

peek=0 · n=100 · size_bad=0 · bonus_in=0 · seed=42.

| 축 | before(<4) | after(<3) | Δ |
|----|------------|-----------|---|
| run2 | 0.675 | 0.612 | -0.063 |
| run3 | 0.043 | 0 | -0.043 |
| prize | 0.022583 | 0.022954 | 0.000371 |
| struct | 0.036781 | 0.035348 | -0.001433 |

통과: run3감소=True · run2비증가=True · prize비악화=True · size_bad0=True.
struct 급락(Δ<−0.005)=False. pred_1237=0 · pred_1239=0 · MAX=1238.

## 판정

**APPLY_OK**. 게이트 통과 · 라이브 MAX=3.
2번/4번/prize표/`random.choices`/몰아주기/kweon 미수정.

## 롤백

`REVIEW_TIER1_CONSEC_MAX=4`

