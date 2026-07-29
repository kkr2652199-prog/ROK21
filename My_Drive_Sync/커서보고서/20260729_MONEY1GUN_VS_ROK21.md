# 1군(MONEY lol) vs ROK21 testlotto — 아키텍처 비교 (READ-ONLY)

> **작성**: 2026-07-29 · **근거**: 코드 실측만 · 미확인은 「미확인」 표기  
> **범위**: 1군=`D:\MONEY lol\My_Library\app\lotto\` · 4군=`D:\ROK21\app\testlotto\`  
> **R34**: 본 문서는 사용자 논의용 비교 참고. ROK21 STATUS/BOOT 미반영.

---

## 1. 한 줄 요약

| | 1군 (MONEY lol) | ROK21 testlotto |
|---|----------------|-----------------|
| **철학** | 6예측뇌 + 퓨전 + (옵션)하이에나/1등가자 — **다양한 생성기 병렬** | 3예측뇌 + 4보조뇌 코디네이터 — **생성·채점 분리** |
| **활성 클릭 경로** | `engine.run_prediction` → 6뇌 각 5세트 + fusion + hyena(플래그) | `coordinator.run_coordinated_prediction` → 3뇌×5 + AUX 채점 |
| **최종 발권** | confidence 정렬 · top5 응답 (뇌별 5세트 유지) | AUX 재점수 → dedup → **markov wire 쿼터 5세트** (markov3+stat1+review1) |
| **DB** | `lotto.db` · `lotto_brain_weights` | `lotto_testlotto.db` · + `testlotto_draw_features/review/learn_state/brain_page` 등 |
| **재현성** | `honesty_flags` + `deterministic_sets` (결정론 top-k) | `random.choices` 유지(동결) · dedup·쿼터로 발권만 제어 |

---

## 2. 비교 표

### 2.1 예측 생성기 (Prediction generators)

| 항목 | 1군 | ROK21 |
|------|-----|-------|
| **예측 뇌 수** | 6 (+옵션 hyena, +lead1) | 3 (stat/markov/review) |
| **알고리즘** | stat, markov, **llm**, **lstm**, **fusion**(벡터앙상블), hyena(메타합의) | stat_fairy, flow_shaman(markov), review_king |
| **레지스트리** | `engine.BRAIN_REGISTRY` 6+1 | `brains/registry.py` PREDICT_BRAINS 3 + AUX 4 |
| **fusion 경로** | **활성** — `_vector_fusion_predict` in `run_prediction` | **미배선** — `engine.py` 주석 K-D: fusion 미호출 |
| **LLM/LSTM** | live 생성·DB 저장 | 파일 존재(`predict_llm.py`, `predict_lstm.py`) · coordinator 미등록 |
| **hyena** | 코드完整 · `ENABLE_HYENA_BRAIN=False` (기본 OFF) | 코드 존재 · `ENABLE_SPECIAL_BRAINS=False` · 미호출 |
| **lead1(7뇌)** | `predict_brain7.py` — 6뇌 READ-ONLY → F1_V2_STRICT 5세트 | 동일 파일 계열 · `_invoke_brain7_safe` 호출 · UI 탭 없음 |
| **세트 조립** | `deterministic_sets.build_weighted_topk_sets` (플래그 ON) | stat/markov: `random.choices` · review: 가중 샘플링 |

**근거 파일**
- 1군: `My_Library/app/lotto/engine.py` L27-37, L327-402
- ROK21: `app/testlotto/brains/registry.py`, `app/testlotto/brains/coordinator.py` L20-34, `app/testlotto/engine.py` L274-282

### 2.2 세트 수 / 최종 출력

| 항목 | 1군 | ROK21 |
|------|-----|-------|
| **뇌당 세트** | `SETS_PER_BRAIN = 5` | `SETS_PER_PREDICT_BRAIN = 5` |
| **생성 총량** | 6×5=30 (+hyena 5, +lead1 5) | 3×5=15 (coordinator) |
| **DB 저장** | 뇌별 DELETE+INSERT · 전 세트 | 3뇌 세트 전부 INSERT (AUX는 DB 행 없음) |
| **UI top5** | confidence 상위 5 (hyena/lead1 제외 필터) | predict 3뇌만 필터 후 top5 |
| **발권 쿼터** | 없음 (confidence 정렬) | `MARKOV_WIRE_BRAIN_QUOTA` markov3+stat1+review1=**5세트** |
| **중복 제거** | 없음 | `ticket_dedup.py` (기본 ON) |

**근거**
- 1군: `engine.py` L37, L471-477
- ROK21: `coordinator.py` L36-44, L206-215, `ticket_dedup.py`

### 2.3 선택·쿼터 (Selection / quota)

| | 1군 | ROK21 |
|---|-----|-------|
| **1차 선택** | 각 뇌 내부 top-k 결정론 또는 tier1_filter | oversample → `set_diversity.diversify_pick` |
| **2차 융합** | fusion 벡터 가중 + entropy (+옵션 cluster) | **없음** (fusion 미사용) |
| **3차 메타** | hyena 합의 점수 (OFF) | 4보조 composite + referee brain 가중 |
| **4차 발권** | confidence DESC | dedup → **set_no ASC 쿼터** (confidence 무관) |

### 2.4 보조(AUX) vs 신호(signal)

| | 1군 | ROK21 |
|---|-----|-------|
| **보조 뇌** | **없음** (별도 AUX 모듈 미확인) | 4개: miss_detective, pattern_spotlight, balance_keeper, referee |
| **역할** | fusion/hyena가 앙상블·메타 | AUX=**채점만** · nums 불변 (`apply_coordinator_scoring`) |
| **가중** | `lotto_brain_weights` → fusion VECTOR_WEIGHTS | `AUX_WEIGHTS` 균등 0.25 + `get_referee_weights()` |
| **신호 실험** | postmortem 패턴 DB (hook OFF) | K-BENCH/AUX-SIGNAL survey 축 · coordinator 미배선 |

### 2.5 DB 스키마·저장·재사용

| 테이블/기능 | 1군 (`lotto.db`) | ROK21 (`lotto_testlotto.db`) |
|-------------|------------------|------------------------------|
| `lotto_draws` | O | O (동형) |
| `lotto_predictions` | O · brain_tag, matched_count | O (동형) |
| `lotto_analysis` | O | O |
| brain_weights | `lotto_brain_weights` (stat/markov/llm/lstm/hyena 시드) | `testlotto_brain_weights` (stat/markov/**review** 시드) |
| draw_features | **없음** | `testlotto_draw_features` (carry, AC, gap, 814rank 등) |
| brain_review | **없음** | `testlotto_brain_review` (회차×뇌 복습) |
| learn_state | **없음** | `testlotto_brain_learn_state` + cutoff 재구성 |
| brain_page | **없음** | `testlotto_brain_page` (상세 UI 스냅샷) |
| prize/detail | **없음** (1군 models) | `testlotto_draw_prize_tiers`, `draw_detail`, `win_stores` |
| pattern DB | `lotto_patterns.db` (postmortem, pattern_store) | `lotto_patterns_testlotto.db` (동계열) |
| **캐시 재사용** | 동일 회차 brain_filter 없으면 DB 반환 (1회 실행 원칙) | 3 predict tag 모두 있으면 캐시 반환 |

**근거**: `My_Library/app/lotto/models.py` vs `app/testlotto/models.py`

### 2.6 학습·진화·피드백

| | 1군 | ROK21 |
|---|-----|-------|
| **피드백 분석** | `feedback.analyze_prediction_feedback` | 동계열 `feedback.py` |
| **가중치 갱신** | Hedge `update_brain_weights` (eta=1.5) · 5뇌+hyena | `maybe_update_brain_weights_after_scoring` · 3뇌 위주 |
| **trap/hit 반영** | `ENABLE_FEEDBACK_TRAP_HIT=False` (stat/markov live boost OFF) | stat `predict_statistical.py`에서 **활성** (as_of cutoff) |
| **walk-forward 학습** | **없음** (API/모듈 없음) | `walkforward.py` — review_loop, apply_feedback, learn_state |
| **learn cutoff** | **없음** | `learn_state_cutoff.py` · `ROK21_LEARN_CUTOFF` 기본 ON |
| **오답 패턴 boost** | honesty_flags로 대부분 OFF | carry/ending/overdue 상한 0.2~0.3 (동결 규칙) |

### 2.7 백테스트·walk-forward

| | 1군 | ROK21 |
|---|-----|-------|
| **백테 API** | `POST /api/lotto/predict/backtest` → `run_backtest` | `POST /api/testlotto/predict/backtest` (동형) |
| **백테 루프** | 회차별 `run_prediction` + feedback + update_brain_weights | 동형 (coordinator 경유) |
| **walk-forward API** | **없음** | `/walkforward/review`, `/progress`, `/future` |
| **회차별 feature 저장** | **없음** | `draw_analysis.upsert_draw_features` |
| **벤치 인프라** | tools/ 일회성 스크립트 다수 | `docs/benchmarks/`, BENCH_PROTOCOL, survey 도구 |

### 2.8 패턴·특징 (slot, gap, position 등)

| | 1군 | ROK21 |
|---|-----|-------|
| **예측 입력 feature** | stat/markov 내부 (gap, pair, recency) | `features/draw_features.py` 공유 + brain wrapper |
| **회차 feature DB** | **없음** | `testlotto_draw_features` |
| **postmortem** | `postmortem_engine/position/structure` · hook **OFF** | 동계열 코드 · scoring 후 **무조건 호출** |
| **position/slot** | `postmortem_position.py` (별도 patterns DB) | 동명 모듈 (testlotto) |
| **pattern_store** | `lotto_patterns.db` READ-ONLY | `lotto_patterns_testlotto.db` |
| **AUX 패턴 채점** | 없음 | pattern_spotlight (AC, consecutive PMF, pair norm) |

### 2.9 UI

| | 1군 | ROK21 |
|---|-----|-------|
| **프론트** | `app/static/js/lotto.js` · `/api/lotto/*` | `testlotto.js` · `/api/testlotto/*` |
| **뇌 탭** | 7개: stat~hyena + lead1 | 3개: 통계요정/흐름술사/복습왕 |
| **엘리트 필터** | brain elite-tags | 동형 |
| **상세 분석** | 기본 예측 UI 중심 | `testlotto-detail.html` · brain_page API |
| **warrant 패널** | **미확인** (1군 lotto.js 내 warrant UI 없음) | warrant-dashboard + 명분 라벨 |
| **walk-forward UI** | **없음** | API 존재 · UI 연동 **미확인** |

---

## 3. 1군만 있는 것 / ROK21만 있는 것

### 3.1 1군 ⊃ ROK21 lacks

| 기능 | 설명 | 근거 |
|------|------|------|
| **결정론 세트 빌더** | `deterministic_sets.py` — top-k 조합, random.choices 대체 | 1군 only |
| **honesty_flags** | 15항 정직화 플래그 (markov 결정론, hyena OFF 등) | 1군 only |
| **LLM/LSTM live** | 6뇌 중 2개 — API 호출·DB 저장 | coordinator 미등록 |
| **벡터 fusion live** | DB 가중치 동적 로드 + entropy/cluster | ROK21 fusion 미배선 |
| **hyena 메타뇌** | 25세트 합의 재조합 (플래그 OFF) | 코드만 양쪽 |
| **UI 6+1 탭** | LLM/LSTM/퓨전/하이에나/1등가자 탭 | testlotto 3탭 |

### 3.2 ROK21 ⊃ 1군 lacks

| 기능 | 설명 | 근거 |
|------|------|------|
| **3+4 coordinator** | 예측3 + 보조4 분업 | `brains/coordinator.py` |
| **복습왕(review) 뇌** | repeat_rate walk-forward 학습형 | `predict_review_king.py` |
| **walk-forward 루프** | review→learn→future API | `walkforward.py` |
| **learn_state + cutoff** | 오답 패턴 누적·컨닝 방지 재구성 | `learn_state.py`, `learn_state_cutoff.py` |
| **발권 dedup + wire 쿼터** | K-V dedup, K-MARKOV-WIRE-V2 | `ticket_dedup.py`, `coordinator.py` |
| **draw_features/review/page DB** | 회차·뇌별 분석 그릇 | `models.py` |
| **set_diversity** | Jaccard 패널티 다양성 | `set_diversity.py` |
| **warrant/benchmark 체계** | K-BENCH, WARRANT.md, survey JSON | docs/benchmarks, warrant_dashboard |
| **당첨 상세 DB** | lt645 prize tiers, win stores | `models.py` testlotto_draw_* |

### 3.3 양쪽 공통·레거시 불일치 (ROK21)

- `predict_brain7.py`(lead1), `postmortem_*`, `pattern_store.py`, `fusion.py`, `predict_*` 대부분 **파일 계열 공유**
- ROK21 `data_service.maybe_generate_army1_next_predictions`는 여전히 **6뇌+lead1** 기대 · live `run_prediction`은 **3뇌 coordinator** → auto N+1과 클릭 경로 **불일치** (코드 실측)

---

## 4. Top 5 구조적 차이 (쉬운 말)

1. **뇌 개수·종류**: 1군은 통계·마르코프·LLM·LSTM·퓨전·(하이에나) **6개 생성기**; ROK21은 **통계·마르코프·복습 3개**만 실제로 돌린다.
2. **융합 방식**: 1군은 **퓨전 벡터 앙상블**이 클릭 경로 중심; ROK21은 퓨전을 끊고 **4보조뇌 채점 + 심판관**으로 confidence만 바꾼다.
3. **최종 5장 발권**: 1군은 **신뢰도 순**; ROK21은 **markov 3 + stat 1 + review 1** 고정 쿼터(set_no 순)로 5장만 낸다.
4. **재현성**: 1군은 **결정론 top-k**(같은 입력→같은 세트); ROK21은 **random.choices 동결** + dedup/쿼터로만 제어.
5. **학습 루프**: 1군은 백테+ Hedge 가중치; ROK21은 **walk-forward 복습·learn_state·회차 feature DB**까지 있다.

---

## 5. 「가상 로또 머신 + 패턴 규칙」 비전에 1군이 더 나은 점

| 관점 | 1군 강점 |
|------|----------|
| **머신 다층 구조** | 생성기 6종 + fusion + hyena + lead1 = **여러 "축"을 동시에 돌리는 설계**가 이미 있음 |
| **규칙 기반 재현** | `deterministic_sets` + `honesty_flags` = **패턴 규칙 ON/OFF**를 플래그로 실험 가능 |
| **벡터 합성** | fusion이 stat/markov/llm/lstm 가중 합 → **"가상 머신 레이어"** 개념에 가까움 |
| **lead1(1등가자)** | 5뇌 합집합 READ-ONLY → wheel/카피회피 **조합 규칙 레이어** |
| **postmortem/pattern_store** | slot·position·structure 사후 분석 (hook만 OFF) |

ROK21은 **실험·검증·컨닝 방지(walk-forward cutoff)** 에 강하고, 1군은 **다양한 생성기+결정론 조립**에 가깝다.

---

## 6. ROK21 실험실 추천 차용 목록 (코드만 근거)

| 우선순위 | 차용 대상 | 출처 (1군) | ROK21 적용 아이디어 |
|----------|-----------|------------|---------------------|
| P1 | `deterministic_sets.py` | `My_Library/app/lotto/` | stat/markov/review **결정론 모드** 실험 (random 동결 유지·플래그 분기) |
| P1 | `honesty_flags.py` 패턴 | 동일 | 실험실 전용 `testlotto_lab_flags.py` — 규칙 ON/OFF SSOT |
| P2 | fusion live 배선 | `fusion.py` + `engine.run_prediction` | coordinator **옵션 경로**로 벡터 fusion A/B (현재 미배선) |
| P2 | lead1 F1_V2_STRICT | `predict_brain7.py` | 3뇌 15세트 READ-ONLY → **조합 wheel 레이어** (이미 코드 있음·활성화 검토) |
| P3 | LLM/LSTM 모듈 | `predict_llm.py`, `predict_lstm.py` | registry **실험 뇌**로 등록 (coordinator brain_filter) |
| P3 | hyena (플래그 OFF 상태) | `predict_hyena.py` | 15세트 합의 메타 — **신호 실험 E2/E3** 후보 |
| — | **차용 비추** | 1군 `random.choices` 레거시 경로 | ROK21 동결 규칙과 충돌 |
| — | **이미 ROK21이 앞섬** | walk-forward, AUX, dedup, wire | 1군에서 가져올 필요 낮음 |

---

## 7. 증거 파일 경로 (절대)

### 1군 (MONEY lol)
- `D:\MONEY lol\My_Library\app\lotto\engine.py`
- `D:\MONEY lol\My_Library\app\lotto\models.py`
- `D:\MONEY lol\My_Library\app\lotto\fusion.py`
- `D:\MONEY lol\My_Library\app\lotto\honesty_flags.py`
- `D:\MONEY lol\My_Library\app\lotto\deterministic_sets.py`
- `D:\MONEY lol\My_Library\app\lotto\feedback.py`
- `D:\MONEY lol\My_Library\app\lotto\routes.py`
- `D:\MONEY lol\My_Library\app\static\js\lotto.js`
- `D:\MONEY lol\My_Library\app\lotto\postmortem_engine.py`

### ROK21 (testlotto)
- `D:\ROK21\app\testlotto\brains\coordinator.py`
- `D:\ROK21\app\testlotto\brains\registry.py`
- `D:\ROK21\app\testlotto\engine.py`
- `D:\ROK21\app\testlotto\models.py`
- `D:\ROK21\app\testlotto\walkforward.py`
- `D:\ROK21\app\testlotto\learn_state.py`
- `D:\ROK21\app\testlotto\ticket_dedup.py`
- `D:\ROK21\app\testlotto\routes.py`
- `D:\ROK21\app\static\js\testlotto.js`

---

## 8. 미확인

- 1군·ROK21 **실제 DB row count / ge3 등 성능 수치** — 본 분석 DB 미조회
- 1군 LLM/LSTM **운영 env에서 실제 호출 성공률** — 코드만 확인
- ROK21 walk-forward **UI 버튼 연동** — API만 확인
- MONEY lol **배포 포트·HEAD** — 본 작업 ROK21 SSOT만 사용

---

*END — commit 없음 (형 미요청)*
