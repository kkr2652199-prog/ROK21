# K-MARKOV-ROLE-TIER-LEARN-WIRE — markov 6~8/9~10 원장복습 소비

시각: 2026-08-14T22:29:15+09:00 · **WIRE_OK** · APPLY=True · ge3미클레임 · 1237아님
창 게이트 1137~1236 n100 · 스모크 1234~1236 · stat 소비 유지

## 0) 한 줄

markov도 stat과 같이 **6~8/9~10 원장 숙제표**를 읽게 했다. 1~5는 그대로. HARD=통과 · 배선=살아있음 · 비악화=True. 라이브 BRAINS=`['markov', 'stat']` (롤백 `ROLE_TIER_LEARN_BRAINS=frozenset({"stat"})`).

## 1) 게이트

| 축 | OFF(stat만) | ON(stat+markov) | Δ |
|----|-------------|-----------------|---|
| prefer (markov 6~10) | 0.018957 | 0.017147 | -0.00181 |
| prize (markov 6~10) | 0.01193 | 0.00929 | -0.00264 |
| markov cover 변경 | 0 | 0 | 모니터 |
| markov shape 변경 | 0 | 100 | 모니터 |

- stat pool동일 100/100 · review동일 100 · markov 1~5동일 100
- cover source `{"cover_r3_role_hw": 300}`
- shape source `{"shape_r2_role_hw": 200}`
- peek=0 err=0 T-NB1=True

## 2) 판정

- WIRE_OK: HARD + markov 6~10 변경>0 + prefer/prize 비악화 + 타뇌·1~5 불변
- COVER_SELECT/몰아주기 S1~S4를 markov에 복사하지 않음.
- 등수·적중 mean으로 성공 금지.

## 3) 다음

WIRE_OK면 markov만 리셋+200회 소비 누적. HOLD면 BRAINS={stat}. 1237아님.
