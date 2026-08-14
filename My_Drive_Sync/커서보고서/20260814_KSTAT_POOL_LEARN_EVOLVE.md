# K-STAT-POOL-LEARN-EVOLVE — 과거학습 1~5 진화 배선

시각: 2026-08-14T21:20:14+09:00 · **WIRE_OK_HOLD_KNOB** · ge3미클레임 · 1237아님

## 0) 한 줄

논문·기존핀: **장당 적중 평균을 올리는 튜닝은 안 된다**(이론 0.80). 이번엔 비어 있던 **1~5 학습 고리**(brain_review → CUTOFF → overdue/ending/carry)를 풀 확정 경로에 연결했다. 1~5 번호가 달라진 회차 **196**/200. prize Δ=-0.00037 prefer Δ=0.000451 (게이트·모니터).

## 1) 문헌 (배울 것 / 안 배울 것)

- 초기하 E[맞힌개수]=6×6/45=**0.80**. 공정 추첨이면 과거로 이 값을 못 올린다.
- Clotfelter–Cook 1993: 방금 나온 번호를 피하고 안 나온 번호를 쫓음 = **도박사의 오류**. 군중도 그렇게 한다.
- Thaler–Ziemba 1988: 바꿀 수 있는 것은 **당첨금 분배(비인기 번호 EV)** 이지 P(당첨)이 아니다.
- Wheeling/covering: 여러 장의 **최소 보장**이지 예측이 아니다.
- 이미 HOLD: WIN_1Y · HINT_WEIGHT 0.15 · ASSOC OFF. 동결: boost 상한.

## 2) 크로스체크 갭

- skill_homework persist = 재계산과 동일 → 1~5를 바꾸지 않음.
- 이번 200회는 발권 0 → brain_review 0 → learn boost 전부 0.
- 어제 발권 경로 stat mean 0.828 은 learn이 쌓인 경로. 오늘은 그 고리가 꺼져 0.798.
- ON 후 hit mean **0.83** ≈ 어제 발권 0.828. **같은 고리를 채운 것**이지 새 예측력이 아니다 (K-O).
- 200회 후 boost가 **상한에 붙음** (carry 0.2 / ending 0.3 / overdue 0.2). 더 돌려도 가중은 안 커짐. overdue 상한 = 문헌의 도박사오류와 같은 방향 → prize 게이트 미달.

## 3) 배선

`STAT_POOL_LEARN_WIRE` · `write_stat_pool_learn` · skill 1~5 **mean**(K-N) · as_of<target.
최종 플래그=**True** · apply=True

## 4) BT200 (1037~1236 · stat만)

| | OFF | ON | Δ |
|--|-----|----|---|
| n | 200 | 200 | |
| prefer (모니터·인기) | 0.00748 | 0.007931 | 0.000451 |
| prize (비인기 EV축) | 0.003368 | 0.002998 | -0.00037 |
| hit mean_all (모니터) | 0.798 | 0.83 | 0.032 |
| hit mean_best (모니터) | 1.705 | 1.81 | |
| peek | 0 | 0 | |

- 1~5 번호 다른 회차: **196**
- boost as_of<1237: `{"review_count": 200, "last_draw_no": 1236, "recent_avg_match": 0.8667, "adjustments": {"carry_over_boost": 0.2, "ending_digit_boost": 0.3, "overdue_boost": 0.2}, "miss_counts": {"carry_over": 74, "ending_digit": 192, "overdue": 18}}`
- census: `{"draws_max": 1236, "pred": 0, "pred_1237": 0, "brain_review": 200, "review_stat": 200, "learn_state": 0, "skill_hw": 600, "role_hw": 1200, "ledger": 3000}`

## 5) 판정

- hard_ok=True · wire_alive=True · prize_gate=False · prefer_not_worse=True
- verdict=**WIRE_OK_HOLD_KNOB** · APPLY=prize≥+0.005 이고 인기 폭증 아님.
- ge3/등수 클레임 금지. 다음=형 1건(markov 또는 유지).

