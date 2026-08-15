# K-STAT-COOCCUR-PREFER + EVOLVE-DIAG — 논의 (APPLY 없음)

시각: 2026-08-15T14:00:08+09:00 · **DISCUSS_OK** · READ-ONLY · 1237아님 · ge3/mean 클레임 금지
범위=요청A 2뇌 브리핑 + 요청B 추천1·2 실측. 코드 APPLY 없음.

## 0) 한 줄 의견

**추천1(궁합·이웃·연번 → prefer 회피)은 가능하되, 번호가중(`blend_weights`/`number_scores`)에 넣으면 안 된다.** 세트 단위 annotate만. **추천2는 새 테이블이 아니라 이미 있는 `testlotto_evolve_log`를 진단으로 재정의**하는 쪽이 맞다. 둘 다 지금 APPLY 하지 말 것.

---

## A) markov / review 구조 브리핑

라이브 진입점: `tools/_k_window_signal_survey.py` `PREDICT_MODULES` = `predict_markov_brain` / `predict_stat_brain` / `predict_review_brain`.
`predict_review_king.py` · `predict_flow_shaman.py` 는 **DEPRECATED** (구특성·군중신호 미적용).

라이브 플래그: `{"ROLE_TIER_LEARN_WIRE": true, "ROLE_TIER_LEARN_BRAINS": ["stat"], "STAT_POOL_LEARN_WIRE": true, "HINT_SPEC_BY_BRAIN": {"stat": [52, "miss_pattern"], "markov": [null, "crowd_prefer"], "review": [null, "crowd_prize"]}, "SCORE_WEIGHTS_BY_BRAIN": {"stat": [0.25, 0.35, 0.4], "markov": [0.65, 0.15, 0.2], "review": [0.65, 0.15, 0.2]}, "markov_LEARN_WIRED": true, "review_has_apply_learn_boost": false, "PREFER_WIRE": true, "PRIZE_WIRE": true, "PREFER_BDAY_STRENGTH": 0.0, "PRIZE_SHAPE_STRENGTH": 1.0, "BLEND_STRENGTH_BY_BRAIN": {"markov": 0.55, "review": 0.85}, "EVOLVE_AUTO": false, "FEATURE_LAMBDA_WIRE": false, "stat_calls_annotate_prefer": false}`

### A1) markov = 선호번호뇌

| 항 | 코드 실측 |
|----|-----------|
| 스킬 | 연속회차 **전이행렬** + 최근 6개에서 **random walk** 방문빈도 → 상위25 가중추출. `engine.py` `build_transition_matrix` / `markov_random_walk` / `generate` |
| 군중 | `prefer_on()`이면 `prefer_table`(1등 당첨자 많은 회 번호 + 생일대 사전)을 `blend_weights`로 **방문가중치에 곱함** → 번호선택에 이미 들어감 |
| 동반 | `learn.apply_learn_boost`의 `pair_boost`가 `build_pair_freq` 상위20쌍 번호를 가중. `predict.py`는 동반쌍 개수를 reasoning만 |
| 보조 | `aux_pattern_spotlight` (쌍·연번·AC). HINT 0.15 |
| 학습 | `LEARN_WIRED=True`. `apply_learn_boost` 소비. `learn_state('markov')` overdue/ending/carry/pair |
| 숙제 소비 | 라이브 `ROLE_TIER_LEARN_BRAINS={stat}` → markov **6~10 역할숙제 OFF** (코드는 보존) |
| 몰아주기 점수 | SCORE (0.65, 0.15, 0.20) · hint=`crowd_prefer` |
| 게이트 축 | prefer (인기). L11b `PREFER_BDAY_STRENGTH=0.0` HOLD |

필터: 합 80~210 · 홀짝 양극 금지 · 구간≤1 금지 · **연번 최대≥4 금지** (`engine.py` 194–201행).

### A2) review = 금액뇌

| 항 | 코드 실측 |
|----|-----------|
| 스킬 | `repeat_rate_after_draw`(직전 나온 뒤 다음에도 나온 비율) + 직전 6개 **×1.8 이월** · 나머지 ×0.85 · **끝수 질량 균등**(K-P3) |
| 군중 | `prize_on()`이면 `prize_table`(1등 적은 회 + 고번호 비선호)을 `blend_weights` → 번호선택에 들어감 |
| 보조 | `aux_miss_detective`. HINT 0.15 |
| 학습 | `apply_learn_boost` **함수 없음**. `load_learn_state('review')`의 `carry_over_boost`만 가중·문구 |
| 숙제 소비 | 라이브 markov와 같이 **역할숙제 OFF** |
| 몰아주기 점수 | SCORE (0.65, 0.15, 0.20) · hint=`crowd_prize` |
| 게이트 축 | prize (몫). L11 `PRIZE_SHAPE_STRENGTH=1.0` 유지 |

구파일 `predict_review_king.py`는 같은 이월 골격이나 crowd_signal 없음. **라이브 아님**.

### A3) stat과 겹침 / 독립

| | stat | markov | review |
|--|------|--------|--------|
| 번호 뽑기 | 빈도+감쇠(+past_learn v2) | 전이 walk | 이월 반복률 |
| 군중 blend | **없음** (`stat_brain`에 crowd_signal 호출 0) | prefer 추종 | prize 비선호 |
| hint | miss_pattern 창52 | crowd_prefer | crowd_prize |
| SCORE | (0.25, 0.35, 0.40) | (0.65, 0.15, 0.20) | 동좌 |
| apply_learn_boost | 있음 (carry/ending/overdue만, **pair 없음**) | 있음 (+pair) | **없음** |
| 역할숙제 소비 | **ON** | OFF | OFF |

공유 허용 실측: `lotto_draws` + 읽기 헬퍼(`draw_features`, `crowd_signal` 모듈). 노브는 `*_BY_BRAIN`. 테이블 `testlotto_brain_learn_state`는 brain_tag 행 분리.
**겹침 주의:** `crowd_signal.py` 한 파일 · `annotate_prefer`가 `brain="markov"` 고정. hint 변환 `_build_hint_for_spec`도 crowd_prefer→markov 표 / crowd_prize→review 표. 예측 과정 계수는 분리되어 있으나 **군중 원자료(first_winners)는 같은 회차 컬럼**.

### A4) 라이브 ON/OFF

- pool 생성: `expand_pool` 기본 3뇌 모두 생성 가능. 이번 캠페인 소비·튜닝은 **stat만**.
- 역할숙제 읽기: **stat만 ON**.
- STAT_POOL_LEARN: **ON** (stat 1~5).
- markov LEARN_WIRED: **True** (엔진 내부).
- EVOLVE_AUTO env: **OFF** (기본 0).
- PREFER_WIRE / PRIZE_WIRE: **True**.

---

## B) 추천 1+2 실현 가능성

DB 실측: draws **1236** · MAX **1236** · 1237 미사용.

### B1) 통계를 lotto_draws에서 뽑을 수 있나

**가능하다. 함수가 이미 있다.** 4군 `lotto_cooccur_*` 테이블을 가져오면 안 된다 (뇌독립·경로혼선).

| 신호 | 함수/위치 | 이번 실측 |
|------|-----------|-----------|
| 궁합(동반쌍) | `draw_features.build_pair_freq` · `data_service.analyze_pair_frequency` | 고유쌍 **990** · 특정쌍 이론P **0.015152** · window100 함수쌍 **785** |
| 연번 | `consecutive_pairs` · `analyze_consecutive` | 연번≥1 회 비율 **0.517** (639/1236) · 최근200 연번쌍 평균 **0.675** |
| 이웃(같은회 ±1) | 연번과 **동일** (\|a-b\|=1) | 같은회 이웃쌍 합 **817** |
| 이웃(다음회 n±1) | 전용 함수 **없음** · draws로 산출 가능 | 실측 **0.7757** · 이론(이웃≈10) **0.8007** → **널과 같음. 예측신호 아님** |

전구간 동반 상위5: `[{"pair": [11, 21], "count": 34, "exp": 18.73}, {"pair": [33, 40], "count": 33, "exp": 18.73}, {"pair": [6, 38], "count": 31, "exp": 18.73}, {"pair": [12, 24], "count": 31, "exp": 18.73}, {"pair": [37, 40], "count": 30, "exp": 18.73}]` — 기대횟수≈18.73. 상위가 기대보다 조금 높아 보여도 **번호선택 근거로 쓰지 말 것**(K-O·K-U).

최소 수정 부착점 (stat 독립):
1. **세트 점수만** — `stat_brain/predict.py`의 generate **이후**, `diversity.pick` **이전**. markov `annotate_prefer`를 호출하지 말 것.
2. 또는 진단만 — `evolve_log.set_features`에 pair/consec 필드 추가 (예측 불변).
3. `number_scores` / `blend_weights` / `engine.generate` 가중 — **금지** (freq·K-O).

### B2) prefer 축에만 연결 가능한가

**세트 단위라면 가능. 번호 테이블에 넣으면 불가능에 가깝다.**

- 게이트 prefer = `prefer_table`의 **번호 평균** (`set_crowd_score`). 궁합은 **쌍·세트** 속성.
- `prefer_table`에 쌍을 녹이면 번호 가중 → markov `blend_weights`와 stat `number_scores` hint가 같이 오염.
- stat 엔진은 지금 crowd_signal을 **안 부른다**. 새 `annotate_combo_unpopular(stat)`만 두면 1~5 `random.choices` 라인은 그대로.
- 다만 annotate는 oversample 후 `diversity.pick` 순서를 바꿔 **살아남는 5장**은 바뀐다. 그건 ‘가중치 테이블 수정’은 아니지만 **발권 구성 변경**이다. 게이트는 prefer/prize 비악화.
- 순수 모니터(점수만 기록, pick 불변)면 K-O와 충돌 없음. ‘인간기법 보강’ 효과는 없음.

권고 배선: **stat 전용 세트 annotate + 플래그 OFF 기본**. `crowd_signal.prefer_table` 미수정. markov/review 파일 미수정.

### B3) 회차 완료 자기진단 로그

**새 파이프를 만들 필요 없다. 이미 있다.**

- 테이블 `testlotto_evolve_log` **존재** · 행 **0** (리셋 후 비어 있음 · 코드만 있음)
- `testlotto_backtest_runs` **0** (UI SOFT `backtest_runs=0`과 같은 축)
- 원장 `{"stat": 3000}`

쓰기 트리거 실측:
- `click_feedback` → learn_state + evolve_log 마크 (`K-KK-FEEDBACK`)
- `coordinator._auto_feedback` (다음 예측 시 직전 회 채점) + ledger/skill/role homework
- `evolve_auto` S2: 캐시→evolve_log 백필. **`EVOLVE_AUTO` 기본 OFF**

이미 있는 것 = (a) 예측 대비 적중 (`pool_hits_json`/`repack_hits_json`/`mean_hits`). `WEIGHT_APPLIED=0.0` · 학습 wire 없음 (Phase1).

없는 것:
- (b) drift χ²/KS **회차 1장** — 자리 없음. 기존 도구는 **창 단위** (`_k_past_learn_score_rule_diag`, `_k_math_pattern_warrant`). 회차 6개로 χ²를 돌리면 무의미. 넣을 거면 evolve_log에 **롤링 창(예 52회) 스냅샷**만.
- (c) boost 사후 귀속 — `features_json`에 구조특징만. carry/ending/overdue가 ‘이번 회에 도움’인지는 **인과가 아님**. 모니터 필드(이번 장에 이월 n개·끝수겹침)는 가능. APPLY 입력 금지.

끼움점: `click_feedback` / `_auto_feedback` 끝 또는 `evolve_auto` S2. 예측 산출물 아님.

### B4) 함정 3개 (형이 먼저)

1. **이미 들어가 있다.** 궁합·연번은 markov `pair_boost` + `aux_pattern_spotlight`에 번호/보조점수로 있음. 같은 신호를 stat freq에 넣으면 K-O. prefer 회피로 넣어도 markov는 같은 쌍빈도를 **추종** 중이라, 두 뇌가 `lotto_draws` 쌍통계를 반대로 쓰면 발권 혼합 시 효과가 상쇄될 수 있다.
2. **축 혼동.** prefer_table=번호 인기. 궁합=조합. 번호 테이블에 섞으면 `blend_weights`가 선택을 바꾼다. ‘prefer 계산에만’을 지키려면 **새 세트 점수**이거나 **로그 전용**이어야 한다.
3. **진단 유령.** evolve_log는 이미 쌓인다. 새 테이블을 만들면 `backtest_runs=0`과 같은 SOFT 공백이 하나 더 생긴다. 회차 χ²는 공정성 감시가 아니라 노이즈다. `FEATURE_LAMBDA_WIRE`는 라이브 **False** — evolve mean_hits를 예측에 넣지 말 것(K-O).

## 6) 합의 / 반박

| 문장 | 커서 |
|------|------|
| 인간기법은 이미 점수식에 대부분 있다 | **동의** (stat 0.25/0.35/0.40 + carry/ending/overdue) |
| 성능↑가 아니라 보강+진단 | **동의** (K-O) |
| 궁합을 prefer 회피에 연결 | **조건부 동의** · 세트 annotate만 · 표/freq 금지 |
| 이웃수 | **정의 필요**. 같은회 ±1=연번과 중복. 다음회 n±1은 전이기호(markov 영역) |
| 회차마다 자기진단 진화 | **로그 재정의에 동의** · 새 엔진/새 테이블 반박 · EVOLVE_AUTO 켜지 말 것 |
| χ²를 회차마다 | **반박** · 롤링 창만 |

## 7) 하지 말 것

- 본턴 코드 APPLY · 1237 · 등수/mean APPLY · 동결 3종 · 3뇌 동시
- lotto4 `lotto_cooccur_*` 를 stat에 연결
- `prefer_table` / markov `blend_weights` 수정
- EVOLVE_AUTO=1 · feature_lambda를 예측 입력으로 ON

## 8) 다음 (형 선택)

A. 추천1 SPEC만 (stat 세트 annotate · 플래그 OFF · 게이트 prefer/prize) — 별 GO
B. 추천2 SPEC만 (evolve_log 필드 확장 · 롤링 χ² 모니터 · WEIGHT 0 유지)
C. A+B SPEC (APPLY 아님)
D. 보류
