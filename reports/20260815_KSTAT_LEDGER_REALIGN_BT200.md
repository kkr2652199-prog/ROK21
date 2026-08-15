# K-STAT-LEDGER-REALIGN-BT200 — 원장 맞춤. 새 knob 없음

시각: 2026-08-15T12:24:18+09:00 · **PASS** · ge3미클레임 · 1237아님
창 1037~1236 · 뇌=stat만 · S1~S4 라이브(S2 HOLD set1) · 리셋 후 원장·숙제 재적재

## 0) 한 줄

markov 잔여 원장을 지운 뒤 S1~S4 라이브로 과거학습만 200회 다시 채웠다. HARD=통과. 새 knob 없음. 등수·평균·prefer/prize는 모니터만.

## 1) 플래그

`{"ROLE_SLOTS_WIRE": true, "ROLE_TIER_LEARN_WIRE": true, "ROLE_TIER_LEARN_BRAINS": ["stat"], "COVER_MIN_HITS": 3, "STAT_POOL_LEARN_WIRE": true, "COVER_SELECT_MODE": "outside_union", "SHAPE_CORE_MODE": "set1", "REPACK_ROLE_QUOTA_WIRE": true, "REPACK_RECOMBINE_MODE": "complement"}`

## 2) 칸별 모니터 (이론 1장 0.80 · 클레임금지)

| 칸 | mean_all | mean_best | 회차최고≥3(모니터) |
|----|----------|-----------|-------------------|
| 1~5 실력 | 0.83 | 1.81 | 34 |
| 6~8 덮기 | 0.74 | 1.4 | 9 |
| 9~10 모양 | 0.8575 | 1.07 | 11 |
| 몰아주기5 | 0.798 | 1.73 | 27 |

## 3) prefer / prize / 기하 (모니터)

| 축 | 값 |
|----|----|
| prefer (repack5) | 0.009443 |
| prize (repack5) | 0.004396 |
| union10 | 31.55 |
| union_repack | 22.685 |
| 재조합 vs 복사4 Jaccard | 0.0 |

## 4) 등수 (고유조합 / 회차최고 · 모니터)

| 등수 | 고유조합 | 회차최고 |
|------|----------|----------|
| 1등 | **0** | 0 |
| 2등 | **0** | 0 |
| 3등 | **0** | 0 |
| 4등 | **12** | 8 |
| 5등 | **55** | 42 |
| 등수 있는 회차 | — | 50 / 200 |

pool 역할별 고유 4·5등 (복사 중복 제외 · 모니터):
- skill `{"1등": 0, "2등": 0, "3등": 0, "4등": 6, "5등": 29}`
- cover `{"1등": 0, "2등": 0, "3등": 0, "4등": 0, "5등": 9}`
- shape `{"1등": 0, "2등": 0, "3등": 0, "4등": 4, "5등": 11}`

- peek=0 · err=0 · size_bad=0 · skill_n_bad=0 · n_ok=200
- census `{"draws_max": 1236, "pred": 0, "pred_1237": 0, "cache": 600, "ledger": 3000, "ledger_by_brain": {"stat": 3000}, "ledger_stat": 3000, "ledger_other": 0, "role_hw": 1200, "skill_hw": 600, "brain_review": 200, "review_stat": 200}`

## 5) 금지

- ge3/등수/mean으로 성적 향상 클레임 금지. 발권 0. DB 파일 커밋 금지. 새 knob 없음.

## 6) 다음

다음=#2 K-STAT-PROCESS-AUDIT-S5LIVE (READ). 1237아님.
