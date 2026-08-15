# K-REVIEW-ROLE-TIER-LEARN-WIRE — review 6~8/9~10 원장복습 소비

시각: 2026-08-15T11:47:28+09:00 · **WIRE_OK** · APPLY=True · ge3미클레임 · 1237아님
창 게이트 1137~1236 n100 · 스모크 1234~1236 · stat·markov 소비 유지

## 0) 한 줄

review도 stat·markov와 같이 **6~8/9~10 원장 숙제표**를 읽게 했다. 1~5는 그대로. HARD=통과 · 배선=살아있음 · 비악화=True. 라이브 BRAINS=`['markov', 'review', 'stat']` (롤백 `ROLE_TIER_LEARN_BRAINS=frozenset({"stat","markov"})`).

## 1) 게이트

| 축 | OFF(stat+markov) | ON(+review) | Δ |
|----|------------------|-------------|---|
| prefer (review 6~10) | 0.006439 | 0.005182 | -0.001257 |
| prize (review 6~10) | 0.009268 | 0.006701 | -0.002567 |
| review cover 변경 | 0 | 0 | 모니터 |
| review shape 변경 | 0 | 100 | 모니터 |

- stat pool동일 100/100 · markov동일 100 · review 1~5동일 100
- cover source `{"cover_r3_role_hw": 300}`
- shape source `{"shape_r2_role_hw": 200}`
- peek=0 err=0 T-NB1=True

## 2) 판정

- WIRE_OK: HARD + review 6~10 변경>0 + prefer/prize 비악화 + 타뇌·1~5 불변
- COVER_SELECT/몰아주기 S1~S4를 review에 복사하지 않음.
- 등수·적중 mean으로 성공 금지.

## 3) 다음

WIRE_OK면 review만 리셋+200회 소비 누적. HOLD면 BRAINS={stat,markov}. 1237아님.
