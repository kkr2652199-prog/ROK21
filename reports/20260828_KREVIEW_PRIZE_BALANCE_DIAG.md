# K-REVIEW-PRIZE-BALANCE-DIAG

시각: 2026-08-29T12:34:57+09:00 · **SPEC_OK** · READ-ONLY · APPLY **없음** · 1237아님 · hits 클레임 금지
목적=금액뇌 1순위 prize_table vs 패치(1·2·3·4) 밸런스. 특히 4번 저울이 prize를 깎는지·연속쌍을 늘리는지.

## S0) prize_table 구성

W_CROWD review=**0.8** · W_STRUCT review=**0.2** · BLEND review=**0.85** · PRIZE_WIRE=True.
표 = 0.80×crowd_unpopular(1/√first_winners) + 0.20×structural_unpopular(고번호·끝 0/8/9).
라이브 4번 WIRE=True (파일 True, 측정 중 메모리만 토글 후 복원).
게이트 1137–1236 n=100 peek=0 seed=42.

| 축 | OFF | ON | Δ(ON−OFF) |
|----|-----|-----|-----------|
| prefer | 0.011283 | 0.011306 | 2.3e-05 |
| prize | 0.024503 | 0.022583 | -0.00192 |
| struct | 0.042302 | 0.036781 | -0.005521 |

4번이 prize를 깎나: **예(Δprize<0)**.

## S1) 연속쌍·고번호 (장당 평균)

| 지표 | OFF | ON | Δ(ON−OFF) |
|------|-----|-----|-----------|
| run2 연속쌍 | 0.667 | 0.675 | 0.008 |
| run3 줄 수 | 0.046 | 0.043 | -0.003 |
| hi32(32+) | 2.252 | 2.186 | -0.066 |

4번 ON이 연속쌍을 늘리나: **예**. 고번호를 늘리나: **아니오**.

## S2) 격리 시뮬 (미적용)

OFF로 만든 10장을 고정한 뒤 `keep_set_by_hist`만 후필터. 발권 RNG 재분기 없음.
n=100 · 전량탈락 skip=0 · 생존장 평균=7.43.
Δprize(kept−all) 평균=-0.000538 · |Δ|평균=0.003736 · |평균|<0.005=True.
0 수렴이면 저울은 같은 장 묶음 안에서 prize를 거의 안 고른다. 발권 ON−OFF Δ는 시드 갈라짐이 섞일 수 있음.

## 판정

**SPEC_OK**. APPLY 없음. 몰아주기 미접촉. 동결토큰 미수정. pred_1237=0 · pred_1239=0 · MAX=1238.

## 금지 확인

코드/플래그/DB write 없음. kweon 미접촉. 1237/1239 예측 없음.

