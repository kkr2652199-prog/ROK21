# K-STAT-REPACK-ROLE-QUOTA — S3 stat 몰아주기 역할쿼터

시각: 2026-08-14T22:07:58+09:00 · **APPLY** · APPLY=True · ge3미클레임 · 1237아님
창 게이트 1137~1236 n100 · 스모크 1234~1236 · 뇌=stat · pool 1~10 불변

## 0) 한 줄

몰아주기 4장 복사에 **cover 최소 1 · shape 최대 1 · skill 최소 1**을 넣었다. HARD=통과 · 배선=살아있음 · 비악화=True · 설계=True. 라이브 WIRE=`True` (롤백 `REPACK_ROLE_QUOTA_WIRE=False`).

## 1) 게이트

| 축 | OFF | ON | Δ |
|----|-----|----|---|
| prefer (repack5) | 0.014541 | 0.015031 | 0.00049 |
| prize (repack5) | 0.007575 | 0.007247 | -0.000328 |
| cover 복사 비율 | 0.112 | 0.212 | 모니터 |
| shape 복사 비율 | 0.254 | 0.16 | 모니터 |

- pool동일 100/100 · 몰아주기변경 94 · cover0장회 OFF 49 ON 0
- copy OFF `{"cover": 56, "skill": 217, "recombine": 100, "shape": 127}`
- copy ON `{"skill": 214, "cover": 106, "recombine": 100, "shape": 80}`
- peek=0 err=0

## 2) 판정

- APPLY: HARD + 몰아주기변경>0 + cover 0장회=0 + prefer/prize 비악화 + cover비율↑또는 shape비율↓
- 등수·적중 mean으로 성공 금지.

## 3) 다음

S4 몰아주기 5번째 장 보완조합 (APPLY일 때). HOLD면 플래그 False. 1237아님.
