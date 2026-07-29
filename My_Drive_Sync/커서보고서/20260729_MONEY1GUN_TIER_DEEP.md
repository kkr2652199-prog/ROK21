# 1군(MONEY lol) 1~5등 당첨·예측과정·컷닝 정밀 분석 (READ-ONLY)

> **작성**: 2026-07-29  
> **DB**: `D:\MONEY lol\My_Library\data\lotto.db` (SQLite `mode=ro`)  
> **코드**: `D:\MONEY lol\My_Library\app\lotto\`  
> **비교**: ROK21 testlotto (`D:\ROK21\app\testlotto\`, `data/lotto_testlotto.db`) — **가상추첨기 제외**  
> **금지 준수**: DB 쓰기·백테 재실행·커밋 없음

---

## 0. 한 줄 결론

| 항목 | 판정 |
|------|------|
| **당첨번호(draws) 컷오프** | **없음(정직)** — `_get_draws_before`: `draw_no < target` |
| **target 당첨번호가 번호 생성에 유입** | **없음** — 생성 후 INSERT 직전·사후 채점에만 사용 |
| **부분 누수(보조 경로)** | **있음** — fusion DB 가중치·LSTM 체크포인트·LLM feedback 요약(전역 최근 20건) |
| **형 “컷닝 없다” 믿음** | **핵심(번호 생성)은 맞음** · **엄격 walk-forward 백테 기준으론 부분 누수 인정** |

---

## 1. DB 실측 — 1~5등 (6뇌: stat/markov/llm/lstm/fusion/hyena)

**집계 조건**: `brain_tag IN ('stat','markov','llm','llm_fallback','lstm','fusion','hyena')` · `miss_analysis`/`snake` 제외 · `matched_count >= 0` (채점 완료)

### 1.1 범위·규모

| 항목 | 값 |
|------|-----|
| `lotto_draws` MAX | **1234** |
| 예측 회차 범위 | target **2 ~ 1235** (distinct **1206**) |
| 채점 완료 회차 | **1205** (미채점 30행·1회차) |
| 6뇌 예측 행 합계 | **36,170** (채점 36,140 / 미채점 30) |
| 회차당 평균 세트 | **≈30** (6뇌×5세트) |

### 1.2 등급별 **행(row)** 수 — 세트 단위

| 등급 | 조건 | 행 수 |
|------|------|------:|
| 1등 | 6+bonus 불필요(6개 일치) | **10** |
| 2등 | 5 + bonus | **3** |
| 3등 | 5 (bonus 없음) | **167** |
| 4등 | 4 | **1,341** |
| 5등 | 3 | **4,311** |

### 1.3 등급별 **회차(draw)** 수 — 해당 등급 이상 1세트라도 적중한 회차

| 등급 | distinct `target_draw_no` |
|------|-------------------------:|
| 1등 | **9** |
| 2등 | **3** |
| 3등 | **113** |
| 4등 | **598** |
| 5등 | **1,080** |

### 1.4 회차별 **최고 적중** 분포 (1205 채점 회차)

| 최고 적중 | 회차 수 |
|-----------|--------:|
| 6 (1등급) | **9** |
| 5+bonus (2등) | **3** |
| 5 (3등) | **106** |
| 4 | **501** |
| 3 | **481** |
| 3 미만 | **105** |

→ 3등 “회차 113” vs “최고 3등 106”: **7회차**는 3등 세트와 더 높은 등급 세트가 **동시** 존재.

### 1.5 1등 회차 목록 (9회차)

`57, 198, 310, 725, 774, 800, 1037, 1040, 1122`

### 1.6 brain_tag별 1~3등 **행** 수

| brain_tag | 1등 | 2등 | 3등 |
|-----------|----:|----:|----:|
| fusion | 7 | 1 | 57 |
| hyena | 2 | 1 | 79 |
| lstm | 1 | 1 | 30 |
| llm | 0 | 0 | 1 |
| markov | 0 | 0 | 0 |
| stat | 0 | 0 | 0 |

※ hyena: `ENABLE_HYENA_BRAIN=False`(현재 비활성)이나 **DB에 과거 백필 데이터 잔존**.

### 1.7 대표 사례 (상위 등급)

| 등급 | draw | brain_tag | nums | confidence | created_at |
|------|-----:|-----------|------|------------|------------|
| 1등 | 1122 | fusion | 3,6,21,30,34,35 | 99.9 | 2026-04-26 23:51:57 |
| 1등 | 1040 | fusion | 8,16,26,29,31,36 | 99.9 | 2026-04-26 22:57:00 |
| 1등 | 1037 | fusion | 2,14,15,22,27,33 | 99.9 | 2026-04-26 22:55:02 |
| 1등 | 1037 | hyena | 2,14,15,22,27,33 | 92.2 | 2026-04-26 22:55:02 |
| 2등 | 743 | fusion | 10,15,21,34,41,44 | 99.9 | 2026-04-26 13:53:03 |
| 2등 | 523 | lstm | 1,4,7,37,38,45 | 99.9 | 2026-04-26 05:23:40 |
| 3등 | 1219 | lstm | 1,2,15,17,28,45 | 99.9 | 2026-04-27 11:53:32 |

**참고 — lead1(7뇌 1등가자)** 별도: 1~2등 **0** · 3등 1 · 4등 41 · 5등 342 (총 5,575행). 본 절 6뇌 집계와 **분리**.

---

## 2. 1군 예측 과정 (코드 경로)

### 2.1 진입

```
POST /api/lotto/predict/{target}  →  routes.py:api_predict
  →  run_prediction(target)       →  engine.py:252
  →  (옵션) _invoke_brain7_safe   →  predict_brain7 lead1
```

### 2.2 단계별

| # | 단계 | 동작 | 근거 |
|---|------|------|------|
| 1 | **캐시 검사** | `lotto_predictions`에 해당 `target_draw_no` 행 있으면 **재생성 생략** · `refresh_prediction_scores_for_target_draw`로 채점만 갱신 | `engine.py:261-309` |
| 2 | **draws 로드** | `_get_draws_before(target)` → `WHERE draw_no < target` | `data_service.py:899-907` |
| 3 | **6뇌 생성** | stat → markov → llm → lstm → fusion 각 **5세트** | `engine.py:327-363` |
| 4 | **하이에나** | `ENABLE_HYENA_BRAIN=True`일 때만 stat~fusion 25세트 합의 → 5세트 | `honesty_flags.py:26` **현재 False** |
| 5 | **세트 조립** | `USE_DETERMINISTIC_SET_BUILD=True` → `deterministic_sets.build_weighted_topk_sets` (top-k 결정론) | `honesty_flags.py:11`, `deterministic_sets.py` |
| 6 | **INSERT 전 채점** | `lotto_draws`에 target 당첨 있으면 `matched_count`/`bonus_matched` 계산 · 없으면 **-1** | `engine.py:411-455` |
| 7 | **사후 채점** | 당첨 확정 후 `refresh_prediction_scores_for_target_draw` UPDATE | `engine.py:64-92` |
| 8 | **lead1** | 6뇌 commit 후 `ensure_brain7_for_draw` — 5뇌 READ-ONLY + walk-forward 신뢰도 | `engine.py:54-61`, `predict_brain7.py` |

### 2.3 `matched_count` 계산 시점

- **예측 시점에는 계산 안 함** (당첨 미공개 시 `-1`).
- **INSERT 직전**: target 당첨 DB에 **이미 있으면** 즉시 계산.
- **이후**: 당첨 수집·`refresh_*` 호출 시 UPDATE.
- → “미래 번호로 과거 예측 번호를 **다시 뽑지는 않음**”. 채점만 사후 반영.

### 2.4 DB 재사용(멱등)

- `run_prediction`: 동일 `target_draw_no`에 예측 존재 + `brain_filter` 충족 → **skip regeneration** (`engine.py:266-309`).
- `run_backtest`: 동일 — 캐시 hit 시 LSTM·fusion **미호출** (`engine.py:528-534` 주석).

### 2.5 `honesty_flags` / `deterministic_sets` 역할

| 플래그 | 값(현재) | 효과 |
|--------|----------|------|
| `USE_DETERMINISTIC_MARKOV` | True | Random Walk 대신 1-step 전이 집계 |
| `USE_DETERMINISTIC_SET_BUILD` | True | `random.choices` 대신 top-k 조합 |
| `ENABLE_FEEDBACK_TRAP_HIT` | **False** | stat/markov trap/hit 가중 **꺼짐** |
| `ENABLE_HYENA_BRAIN` | **False** | 신규 hyena 생성 **꺼짐** |
| `ENABLE_ARMY1_AUTO_NEXT_PRED` | False | N+1 자동 예측 **꺼짐** |
| `REJECT_FUTURE_DRAW_PREDICT` | False | POST 미래 회차 **수동 허용** |

---

## 3. 컷닝(누수) 감사

### 3.1 정직 경로 (누수 없음)

| 검증 | 결과 | 근거 |
|------|------|------|
| target 이전 draws만 생성 | **OK** | `_get_draws_before` `draw_no < ?` |
| target 당첨번호 생성 입력 | **없음** | 5뇌·fusion·lstm 모두 `draws` 인자만 |
| postmortem → 예측 역주입 | **없음** | `20260718_1군_postmortem실태` · predict*.py import 0건 |

### 3.2 부분 누수 / 전역 상태 (과거 보고서 + 현재 코드·DB 재확인)

| 경로 | target 컷오프 | 현재 상태 | 근거 |
|------|---------------|-----------|------|
| **fusion VECTOR_WEIGHTS** | **없음** | **활성** | `fusion.py:77` `_load_brain_weights_from_db()` · DB `last_updated_draw=1234` |
| **LSTM 체크포인트** | **없음** | **활성** | `lstm_lotto.pt` `last_trained_on=1226` · target=800 예측 시 재학습 조건 미충족 → **미래 학습 가중치 재사용** |
| **LLM feedback 요약** | **없음** | **활성** | `predict_llm.py:117-119` `get_feedback_summary(last_n=20)` — `ENABLE_FEEDBACK_TRAP_HIT` **미적용** |
| **stat/markov feedback** | **없음** | **꺼짐** | `ENABLE_FEEDBACK_TRAP_HIT=False` |
| **예측 캐시** | — | **잔존** | 과거(누수 가능) 예측 **재생성 안 함** |
| **백테스트 피드백 루프** | 부분 | 백테 시 | `run_backtest` → `update_brain_weights(draw_no)` — fusion이 **다음 회차부터** 전역 가중치 오염 가능 |

**LSTM DB vs walk-forward** (`20260710_LSTM_누수검증_walkforward.md`):

- DB cached AVG matched **1.92** vs WF clean **0.77** (무작위 ~0.80).
- 현재도 캐시·체크포인트 구조 **동일** → DB tier 통계는 **LSTM/fusion 기여분 inflate 가능**.

### 3.3 컷닝 판정

| 구분 | 판정 |
|------|------|
| **번호 생성(draws) 컷닝** | **없음** |
| **target 당첨번호 역류** | **없음** |
| **보조 학습·가중·체크포인트** | **부분 누수** |
| **종합** | **부분** — 핵심 파이프라인 정직 · 엄격 WF 백테·DB tier 숫자 해석 시 보조 경로 주의 |

### 3.4 형 믿음 대조

> “1군에 컷닝 없다”

- **맞는 부분**: `_get_draws_before`로 **당첨 draw 데이터가 target 예측 번호 생성에 들어가지 않음** — 코드·DB 채점 분리 확인.
- **틀리거나 불완전한 부분**: fusion 가중치·LSTM 모델·LLM feedback이 **target 무관 전역** · 20260710/20260718 보고서가 이미 기록.
- **실무 해석**: “번호 뽑을 때 정답지 안 본다” = **맞음**. “walk-forward 백테 100% 깨끗” = **아님(부분)**.

---

## 4. ROK21 testlotto vs 1군 (실존 기능만)

| 항목 | 1군 | ROK21 testlotto |
|------|-----|-----------------|
| **활성 경로** | `engine.run_prediction` → 6뇌×5 + fusion | `coordinator.run_coordinated_prediction` → 3뇌×5 + AUX4 채점 |
| **예측 뇌** | stat, markov, llm, lstm, fusion, (hyena) | stat, markov, review |
| **fusion.py** | **활성** | **미배선** (K-D) |
| **발권** | confidence 정렬 · 뇌별 5세트 유지 | AUX 재점수 → markov wire 쿼터 5세트 |
| **학습 컷오ff** | fusion weights·LSTM·LLM feedback **전역** | `learn_state_cutoff.set_learn_as_of(target)` **기본 ON** |
| **결정론** | `honesty_flags` + top-k | random 유지(동결) · dedup/쿼터만 |
| **DB** | `lotto.db` | `lotto_testlotto.db` |
| **예측 회차(채점)** | **1205** | **121** |
| **1~3등 행** | 10 / 3 / 167 | **0 / 0 / 0** |
| **4~5등 행** | 1341 / 4311 | **3 / 44** |
| **5등+ 회차** | 1080 | **33** |

### 4.1 1군만 있는 것 (ROK21 없음)

- LLM·LSTM·벡터 fusion·hyena(옵션)·lead1(7뇌)
- `lotto_brain_weights` 동적 fusion 가중
- `honesty_flags` / `deterministic_sets` 결정론화
- 6뇌×5 ≈30세트/회차 (대량 tier 표본)

### 4.2 ROK21만 있는 것 (1군 없음)

- 4보조뇌(AUX) 채점·referee 가중
- `learn_state_cutoff` walk-forward 학습 상태
- markov wire 쿼터 발권 · ticket dedup
- review_king 3번째 예측뇌

---

## 5. 참고 보고서 (MONEY lol)

| 일자 | 파일 | 관련 내용 |
|------|------|-----------|
| 20260710 | `LSTM_누수검증_walkforward.md` | LSTM 체크포인트·캐시 → DB tier inflate |
| 20260710 | `STEP1_6뇌_WF정직성적_측정.md` | walk-forward 측정 프레임 |
| 20260718 | `1군_정밀현황_백테검증_앱뇌규모.md` | draws 컷오프 OK · fusion/feedback 부분누수 |
| 20260718 | `1군_postmortem실태_정리후보목록.md` | postmortem 예측 미반영 |
| 20260729 | `ROK21/reports/20260729_MONEY1GUN_VS_ROK21.md` | 아키텍처 비교(본 문서 tier 보완) |

---

## 6. 미확인

- 2026-04-26 대량 백필 **당시** fusion/LSTM 내부 가중치 스냅샷(실행 로그 없음).
- `target_draw_no=1235` 미채점 30행 — `lotto_draws` MAX 1234와 일치(미래 1회차).

---

*근거: `tools/_temp_1gun_tier_query.py` · `tools/_temp_rok21_tier_query.py` READ-ONLY 실행 · 코드 직접 열람*
