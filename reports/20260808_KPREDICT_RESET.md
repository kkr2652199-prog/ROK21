# K-PREDICT-RESET — 3뇌 예측 산출물 리셋

- 생성 2026-08-08T08:07:05.148450+00:00 · 대상 `data/lotto_testlotto.db` 단독
- 실제 적용: **True** · 백업: **없음 (형 지시)**

## 0. 형 지시

> 로또테스트에 백테스트한 모든 db 에 잇는 3뇌 예측을 삭제해줘

테스트로또 DB 단독 · 백업 없음. 회차·당첨정보 같은 **원천 데이터는 보존**하고,
회차에서 기계적으로 파생되는 기록도 3뇌 예측이 아니므로 남겼다.

## 1. 삭제 대상

|테이블|삭제 행수|사유|
|---|---|---|
|`testlotto_evolve_log`|3549|회차·뇌별 pool/repack 채점 로그|
|`hit_warrant_log`|1134|적중 명분 로그 (예측 대조 산출)|
|`lotto_predictions`|1000|3뇌 예측 세트 (brain_tag)|
|`testlotto_backtest_draw_results`|800|백테스트 회차별 결과|
|`testlotto_pool_view_cache`|600|10세트 pool·몰아주기 캐시|
|`testlotto_backtest_runs`|4|백테스트 실행 헤더|
|`testlotto_brain_learn_state`|3|뇌별 누적 학습상태 (3행=3뇌)|
|`testlotto_brain_weights`|3|뇌별 가중치|
|`testlotto_evolve_auto_state`|1|evolve 자동화 상태|
|`lotto_analysis`|0|prediction_feedback 등 예측 채점 결과|
|`testlotto_brain_review`|0|복기뇌 산출|
|**합계**|**7094**||

## 2. 보존 (건드리지 않음)

|테이블|행수|사유|
|---|---|---|
|`testlotto_draw_prize_tiers`|6170|등위별 당첨정보 (원천)|
|`testlotto_brain_page`|3698|뇌 소개 문구 (UI)|
|`lotto_draws`|1235|회차 당첨번호 (원천 · 재수집 필요)|
|`testlotto_rare_bundle_hits`|1235|희귀묶음 적중 (회차 파생 · 3뇌 예측 아님)|
|`testlotto_draw_features`|1234|회차 자체 특성 (회차 파생)|
|`testlotto_draw_detail`|1234|회차 상세 (원천)|
|`transition_log`|1134|회차 이행 기록 (회차 파생 · 3뇌 예측 아님)|
|`testlotto_rare_bundle_catalog`|213|희귀묶음 카탈로그 (원천)|
|`sqlite_sequence`|7|SQLite 내부|
|`testlotto_draw_win_stores`|0|당첨판매점 (원천)|

## 3. 뇌 태그를 가진 테이블 (판정 근거)

추측이 아니라 스키마로 확인한 목록이다.

- `lotto_predictions` — 컬럼 ['brain_tag'] · **삭제**
- `testlotto_brain_learn_state` — 컬럼 ['brain_tag'] · **삭제**
- `testlotto_brain_page` — 컬럼 ['brain_tag'] · **보존**
- `testlotto_brain_review` — 컬럼 ['brain_tag'] · **삭제**
- `testlotto_brain_weights` — 컬럼 ['brain_tag'] · **삭제**
- `testlotto_evolve_log` — 컬럼 ['brain_tag'] · **삭제**
- `testlotto_pool_view_cache` — 컬럼 ['brain'] · **삭제**

## 4. 적용 결과

|테이블|삭제됨|삭제 후|
|---|---|---|
|`testlotto_evolve_log`|3549|0|
|`hit_warrant_log`|1134|0|
|`lotto_predictions`|1000|0|
|`testlotto_backtest_draw_results`|800|0|
|`testlotto_pool_view_cache`|600|0|
|`testlotto_backtest_runs`|4|0|
|`testlotto_brain_learn_state`|3|0|
|`testlotto_brain_weights`|3|3|
|`testlotto_evolve_auto_state`|1|1|
|`lotto_analysis`|0|0|
|`testlotto_brain_review`|0|0|

- DB 파일 크기 51.98 MB → **34.43 MB** (VACUUM 포함)

## 5. 다음에 해야 할 일

리셋만으로는 예측이 다시 생기지 않는다. 새 배선(뇌별 성적표 · 신호 상위 세트 ·
뇌 간 RNG 독립)으로 백테스트를 다시 돌려야 기록이 채워진다.

## 6. 주의

- 이 DB 는 git 추적 대상(약 51MB)이다. **리셋 결과는 커밋하지 않는다** (레포 위생)
- 미분류 테이블: 없음
