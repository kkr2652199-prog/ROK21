# K-STAT-COVER-OUTSIDE-UNION — S1 stat cover 선택

시각: 2026-08-14T21:58:27+09:00 · **APPLY** · APPLY=True · ge3미클레임 · 1237아님
창 게이트 1137~1236 n100 · 스모크 1234~1236 · 뇌=stat · 1~5 불변

## 0) 한 줄

6~8 cover를 Jaccard 최저 대신 **1~5가 안 쓴 번호가 많은 장**을 고르게 했다. HARD=통과 · 배선=살아있음 · prefer/prize iso=True · 설계이동=True. 라이브 모드=`outside_union` (롤백 `COVER_SELECT_MODE='jaccard'`).

## 1) 게이트

| 축 | OFF(jaccard) | ON(outside) | Δ |
|----|--------------|-------------|---|
| prefer (cover3) | 0.012046 | 0.006505 | -0.005541 |
| prize (cover3) | 0.00467 | 0.001839 | -0.002831 |
| union10 | 30.05 | 31.72 | 모니터 |
| cover 밖번호 mean | 2.3267 | 3.0067 | 모니터 |
| cover-skill Jaccard | 0.102 | 0.0799 | 모니터 |

- skill 1~5 동일 100/100 · cover 변경 99
- peek=0 err=0 size=0 n_ok=100
- ON source `{"cover_r3_outside_union": 300}`
- iso thr=0.005 · smoke_hard=True

## 2) 판정 규칙

- APPLY: HARD + cover변경>0 + prefer/prize **비악화**(Δprefer<0.005 · Δprize<0.005) + 설계이동
- HOLD_ISO_FAIL: 인기↑ 또는 몫EV악화가 0.005 이상
- DEAD_WIRE: cover 번호가 안 바뀜 → 기본 jaccard
- |Δ| 대칭 iso는 타뇌 독립성용. EV가 좋아진 음수 Δ를 실패로 치지 않음.
- 등수·적중 mean으로 성공 금지.

## 3) 다음

S2 shape 합의 코어 (APPLY일 때). HOLD면 리스트 재검토. 1237아님.
