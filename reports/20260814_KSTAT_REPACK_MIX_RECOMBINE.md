# K-STAT-REPACK-MIX-RECOMBINE — S4 stat 몰아주기 보완조합

시각: 2026-08-14T22:11:32+09:00 · **APPLY** · APPLY=True · ge3미클레임 · 1237아님
창 게이트 1137~1236 n100 · 스모크 1234~1236 · 뇌=stat · pool 1~10·복사4 불변

## 0) 한 줄

몰아주기 5번째 장을 **복사 4장에 없는 고점수 6개**로 바꿨다. HARD=통과 · 배선=살아있음 · 비악화=True · 설계=True. 라이브 MODE=`complement` (롤백 `REPACK_RECOMBINE_MODE="top6"`).

## 1) 게이트

| 축 | OFF(top6) | ON(complement) | Δ |
|----|-----------|----------------|---|
| prefer (repack5) | 0.015031 | 0.011637 | -0.003394 |
| prize (repack5) | 0.007247 | 0.004816 | -0.002431 |
| 재조합 vs 복사4 Jaccard | 0.287264 | 0.0 | 모니터 |
| union_repack | 17.69 | 22.66 | 모니터 |

- pool동일 100/100 · 복사4동일 100 · 5장변경 100
- 보완∩복사 mean 0 (설계상 0에 가까움)
- peek=0 err=0 · self_check=True

## 2) 판정

- APPLY: HARD + 5장변경>0 + prefer/prize 비악화 + Jaccard↓또는 union_repack↑
- 등수·적중 mean으로 성공 금지.
- |Δ| 대칭 iso는 타뇌 독립성용. EV가 좋아진 음수 Δ를 실패로 치지 않음.

## 3) 다음

S5 리셋+stat 200회 (APPLY일 때). HOLD면 MODE=top6. 1237아님.
