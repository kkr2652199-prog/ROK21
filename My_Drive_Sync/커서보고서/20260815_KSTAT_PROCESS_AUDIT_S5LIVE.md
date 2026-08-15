# K-STAT-PROCESS-AUDIT-S5LIVE — S5라이브 프로세스 감사

시각: 2026-08-15T12:42:27+09:00 · **PASS** · READ-ONLY · ge3미클레임 · 1237아님
창 1037~1236 · 뇌=stat만 · S1 outside_union · S2 HOLD set1 · S3 쿼터 · S4 보완

## 0) 한 줄

원장맞춤 직후 DB와 라이브 expand(쓰기없음)를 대조했다. HARD=통과. 역할 5+3+2 · S1/S3/S4 라벨·번호 규칙 · 숙제 n_pos를 다시 셌다. 등수 클레임 없음.

## 1) 플래그·센서스

`{"ROLE_SLOTS_WIRE": true, "ROLE_TIER_LEARN_WIRE": true, "ROLE_TIER_LEARN_BRAINS": ["stat"], "COVER_MIN_HITS": 3, "STAT_POOL_LEARN_WIRE": true, "COVER_SELECT_MODE": "outside_union", "SHAPE_CORE_MODE": "set1", "REPACK_ROLE_QUOTA_WIRE": true, "REPACK_RECOMBINE_MODE": "complement"}`

`{"draws_max": 1236, "pred": 0, "pred_1237": 0, "cache": 600, "ledger": 3000, "ledger_stat": 3000, "ledger_other": 0, "role_hw": 1200, "skill_hw": 600, "brain_review": 200, "review_stat": 200, "bt_runs": 0}`

## 2) 원장 역할 5+3+2

- 회차 **200**/200 · 번호무효 **0** · 역할불일치 **0**
- pool10결손 **0** · repack5결손 **0**
- 역할 `{"skill_native": 1000, "cover_r3": 600, "shape_r2": 400, "focus_r1": 1000}`

## 3) S1 cover source (라이브)

- 라이브 `{"cover_r3_outside_union": 600}`
- shape `{"shape_core5_vary6": 2, "shape_r2_role_hw": 398}`
- 캐시 pool source `{"": 2000}`
- 캐시는 pool source 미저장. 라이브 expand가 S1 라벨 SSOT.

## 4) S3 몰아주기 쿼터 (캐시 복사4)

- copy4 실패 **0** · 쿼터실패 **0**
- 복사 역할합 `{"skill": 421, "cover": 220, "shape": 159}`
- 기대: skill>=1 cover>=1 shape<=1 per draw ×4 copies

## 5) S4 보완조합 (캐시 5번째)

- 캐시 repack source `{"pool": 800, "score_repack": 200}`
- 라이브 `{"pool": 800, "score_repack": 200}`
- 재조합 vs 복사4 Jaccard mean **0.0** · 0아닌회 **0**
- 보완1장 source=score_repack (complement 문자열 아님·SOFT). 번호 Jaccard=0이 S4 증거.

## 6) 숙제 n_pos

| 키 | n | mean | min | max | 초반10 | 후반10 |
|----|---|------|-----|-----|--------|--------|
| markov|cover_r3 | 200 | 0 | 0 | 0 | 0 | 0 |
| markov|shape_r2 | 200 | 30.19 | 26 | 35 | 32.8 | 30.1 |
| review|cover_r3 | 200 | 0 | 0 | 0 | 0 | 0 |
| review|shape_r2 | 200 | 30.19 | 26 | 35 | 32.8 | 30.1 |
| stat|cover_r3 | 200 | 21.035 | 3 | 30 | 3 | 26.3 |
| stat|shape_r2 | 200 | 30.19 | 26 | 35 | 32.8 | 30.1 |

- as_of n=200 min=1037 max=1236 peek≥1237=0

## 7) 라이브↔캐시

- n_ok **200** · peek **0** · 역할불량 **0** · 번호불일치 **0** · 46.8s

## 8) HARD / SOFT

- HARD (0): `[]`
- SOFT: `["UI backtest_runs=0 (원장≠강제백테표)"]`

## 9) 금지

- ge3/등수/mean 성적클레임 금지. 코드 APPLY 없음. DB 쓰기 없음. 1237아님.

## 10) 다음

리스트 #3 K-A-STALE-DOC (FINDINGS K-A 구표본 표시). 1237아님.
