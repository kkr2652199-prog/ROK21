# K-STAT-SHAPE-CONSENSUS-CORE — S2 stat shape 코어

시각: 2026-08-14T22:02:42+09:00 · **HOLD_ISO_FAIL** · APPLY=False · ge3미클레임 · 1237아님
창 게이트 1137~1236 n100 · 스모크 1234~1236 · 뇌=stat · 1~5·cover 불변 · T-NB1

## 0) 한 줄

9~10 shape 코어를 1번 세트 복제가 아니라 **1~5에서 2회 이상 나온 번호**로 잡았다. HARD=통과 · 배선=살아있음 · 비악화=False · 설계(J↓)=True. 라이브 모드=`set1` (롤백 `SHAPE_CORE_MODE='set1'`).

## 1) 게이트

| 축 | OFF(set1) | ON(consensus) | Δ |
|----|-----------|---------------|---|
| prefer (shape2) | 0.000322 | 0.012491 | 0.012169 |
| prize (shape2) | 0.001694 | -0.007896 | -0.00959 |
| shape vs set1 Jaccard | 0.7143 | 0.2856 | 모니터 |

- skill동일 100/100 · cover동일 100 · shape변경 100
- peek=0 err=0 T-NB1=True
- ON source `{"shape_r2_consensus": 200}`

## 2) 판정

- APPLY: HARD + shape변경>0 + prefer/prize 비악화 + Jaccard↓
- 등수·적중 mean으로 성공 금지.

## 3) 다음

S2는 **HOLD**(인기 Δ+0.012 ≥ 0.005). 코드는 플래그로 남아 있고 라이브는 `set1`.  
캠페인 다음=**S3 몰아주기 역할쿼터**(S2 APPLY 비의존). 1237아님.
