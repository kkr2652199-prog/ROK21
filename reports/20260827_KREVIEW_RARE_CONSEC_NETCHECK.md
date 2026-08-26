# K-REVIEW-RARE-CONSEC-NETCHECK (2026-08-27)

- **판정:** `HOLD_NO_WIRE` · S0 READ-ONLY · PASS_WIRE 켜지 않음 · 몰아주기 미접촉
- 시각: 2026-08-27T04:36:35+09:00
- 형: 5-세분 STEP1이 5-바탕과 동일 집합인지 net 확인 후 배선 여부.
- 근거: `20260827_KREVIEW_RARE_CONSEC_NETCHECK.json`

## S0 순수증분

- 5-바탕(rare_pass) `21245` · 5-세분 STEP1 `1600` · 클래스 `11` · sig `{'5+1': 1560, '6': 40}`
- 겹침(이미 포함) `1600` · net(세분-바탕) `0` · 바탕만 `19645`
- 세분 ⊆ 바탕 `True`
- net 당첨 1–1238 `0` (net=0이면 공집합)
- pred_1237 `0` · pred_1239 `0` · MAX `1238`

## S0 가상 추가 패스 1137–1236 n100

- peek `0` n_ok `100` sets `1000` bonus_in `0`
- 출력에 rare_pass `0` · consec STEP1 `0` · 둘다 `0`
- **추가 패스**(consec이고 rare_pass 아님) `0` · 비율 `0.0`
- 라이브 PASS_WIRE `False`
- elapsed `19.7`s

## S1 판정

- `HOLD_NO_WIRE`
- 사유: net=0 (STEP1 1600이 rare_pass에 전부 포함) · 추가 패스 0. 라이브 배선 금지. 읽기(세분 라벨)만 유지.
- S2 배선 **안 함**. `REVIEW_CONSEC_PASS_WIRE` 유지 False. `REVIEW_CONSEC_KB_READ` 유지 True(모니터).

## 롤백

- PASS: 이미 False · READ: `REVIEW_CONSEC_KB_READ=False`

## 파일

- `20260827_KREVIEW_RARE_CONSEC_NETCHECK.json` · `20260827_KREVIEW_RARE_CONSEC_NETCHECK.md`
