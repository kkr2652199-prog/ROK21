# K-PROCESS-STRUCTURE-QUERY

📅 2026-08-10 KST · **READ-ONLY** · wire=False · 코드/DB 수정 없음  
목적: 젠스파크 흐름 오해 정정 · 코드 실측 설명

---

## 질문 1: 예측 생성 흐름

### UI → 서버
`lotto4.js` `runPredict()` (약 L2757)  
→ `POST /api/testlotto/predict/{d}` (`d` = UI 선택 회차 = **target**)

### 서버 호출 사슬
```
routes.api_predict(target_draw_no)
  → engine.run_prediction(target_draw_no)
    → coordinator.run_coordinated_prediction(target_draw_no)
       ① _auto_feedback(target)          # 직전회(target-1) 채점 시도
       ② set_learn_as_of(target)         # 학습 컷오프 = target (미만만)
       ③ 캐시 있으면면 return
       ④ draws = _get_draws_before(target)  # 재료 = 1..(target-1)
       ⑤ 3뇌 predict_sets(draws, 5)
       ⑥ aux 채점 · dynamic_brain_quota → 보통 5장 발권
       ⑦ lotto_predictions INSERT
  → (후) click_feedback.apply_feedback_after_predict(target)
       = apply_draw_result_feedback(target-1)
```

| 단계 | 파일 | 함수 | 인자 |
|------|------|------|------|
| HTTP | `routes.py` L402 | `api_predict` | `target_draw_no` |
| 래퍼 | `engine.py` L274 | `run_prediction` | `target_draw_no` |
| 본체 | `coordinator.py` L470 | `run_coordinated_prediction` | `target_draw_no` |
| 재료 | `data_service._get_draws_before` | — | **draw_no < target** |
| 학습컷 | `learn_state_cutoff.set_learn_as_of` | — | `as_of = target` (미만만 사용) |

### as_of / target 관계 (핵심)
- **예측 대상** = `target` (예: 1237)
- **재료(당첨번호 이력)** = `_get_draws_before(target)` → **최대 target−1까지**
- **학습상태 컷오프** = `set_learn_as_of(target)` → learn 로드 시 **target 미만**만
- 따라서 **재료 as_of 상한 = target−1**. target 당첨번호를 생성에 쓰지 않음(컨닝 방지).

### 젠스파크 오해 지적
- ❌ “예측 생성 = engine.py가 메인” → 실제 메인은 **coordinator**. `engine.run_prediction`은 위임만.
- ❌ “as_of = target 당첨 포함” → **포함 안 함**. target 미만만.

---

## 질문 2: feedback / 채점 흐름

### 언제 도는가? (자동 트리거 3곳)

```
A) 예측 클릭 시 (자동)
   run_coordinated_prediction(N)
     → _auto_feedback(N)  # N-1 채점 (coordinator L476)
   api_predict 후
     → apply_feedback_after_predict(N)  # N-1 채점 (routes L412)

B) 최신회차 수집 시 (자동)
   POST /fetch-latest 성공
     → apply_draw_result_feedback(수집된 draw_no)  # 그 회차 채점 (routes L133)

C) evolve_auto / walkforward / 검증스크립트 (수동·배치)
```

수동으로도 `apply_draw_result_feedback(N)` 호출 가능.

### 두 함수 차이

| 함수 | 파일 | 채점 회차 |
|------|------|-----------|
| `apply_feedback_after_predict(N)` | `click_feedback.py` L259 | **N−1** |
| `apply_draw_result_feedback(N)` | `click_feedback.py` L126 | **N** |

```
apply_feedback_after_predict(N) → apply_draw_result_feedback(N-1)
```

내부 공통:
1. `lotto_draws`에 해당 회차 없으면 SKIP (`guard_future`)
2. `lotto_predictions`에 그 회차 예측 없으면 SKIP (`no_predictions`)
3. 뇌별 mean(또는 best) hits + miss 패턴 → `learn_state.apply_feedback(brain, draw, matched, missed)`
4. `evolve_log` note에 `K-KK-FEEDBACK` 마크 (weight_applied=0.0)
5. 이미 마크면 SKIP (`guard_duplicate`)

### 젠스파크 오해 지적
- ❌ `apply_feedback_after_predict(1236)` = 1236 채점  
  → **틀림. 1235를 채점함.**
- 1236 채점 올바른 호출:
  - `apply_draw_result_feedback(1236)`  
  - 또는 `apply_feedback_after_predict(1237)` (1237 예측 클릭의 부수효과)

---

## 질문 3: 1236 / 1237 기준 (DB 실측 2026-08-10)

실측: `lotto_draws` max=**1236** · pred 1236=**10행**(3뇌) · pred 1237=**0** · evolve 1236=3뇌 · evolve 1237=없음.

### A. 1236 예측은 언제?
- 정상 설계: **1236 추첨 전**에 target=1236으로 생성 → 재료 as_of 상한=**1235**.
- 이번 VERIFY 세션: 1236이 이미 DB에 있는 뒤 `run_prediction(1236)`(+stat 보충)으로 생성됨.  
  그래도 생성 재료는 `_get_draws_before(1236)` → **여전히 1235까지**(번호 역산 없음).  
  (matched_count만 결과 대비 채점값이 붙음)

### B. 1236 결과로 채점하려면?
```
apply_draw_result_feedback(1236)
# 또는 UI에서 1237 예측 클릭 → after_predict(1237) → 1236 채점
```
전제: `lotto_predictions`에 target=1236 행 존재 + `lotto_draws`에 1236 존재.

### C. 1237 예측은 현재?
- **미생성** (pred count=0).
- 생성 시 재료 as_of 상한은 **반드시 1236까지** (`_get_draws_before(1237)`).

### D. 순서: 1236 채점 vs 1237 예측
**권장 순서**
```
1236 결과 DB 확정
  → (이미 있다면) 1236 예측 존재 확인
  → 1236 채점 (feedback)
  → 1237 예측 생성
```

`run_coordinated_prediction(1237)` 시작 시 `_auto_feedback(1237)`이 **먼저 1236을 채점**하므로,  
1236 결과가 DB에만 있으면 **1237 예측 클릭 한 번으로 채점→예측**이 이어짐.

**순서 역전 문제**
- 1236 결과 **없이** 1237 예측 → 1236 피드백 누락된 learn으로 1237 생성.
- 그 뒤 1236 채점만 하면 **이미 만든 1237 예측은 자동 갱신 안 됨** → 1237 **재예측** 필요.
- 1236 예측이 없는데 채점만 호출 → `no_predictions` SKIP.

### 젠스파크 오해 지적
- ❌ “1236 채점 = after_predict(1236)” → **1235 채점**.
- ❌ “결과 들어온 회차를 after_predict에 넣으면 그 회차가 채점된다” → **한 회차 밀림**.

---

## 질문 4: evolve_log 기록 시점

### 언제 쌓이는가?
**둘 다 가능 · 경로가 다름.**

| 시점 | 경로 | 내용 |
|------|------|------|
| 채점/백필 | `evolve_auto` → `evolve_log.upsert_evolve_row` | pool/repack hits · mean/best · weight=0 |
| 피드백 마크 | `click_feedback._mark_evolve_feedback` | note에 `K-KK-FEEDBACK` · weight=0 (기존행 UPDATE 또는 최소 INSERT) |
| 순수 예측 INSERT | `lotto_predictions`만 | **evolve_log 자동 기록 아님** |

즉: **예측 생성만으로는 evolve_log가 안 쌓일 수 있음.**  
evolve_auto 백필/스코어 또는 click_feedback 채점 마크가 있어야 함.

### weight_applied = 0.0 이 바뀌려면?
- 현재 `evolve_log.WEIGHT_APPLIED = 0.0` **Phase1 상수** (`evolve_log.py` L17).
- `click_feedback.WEIGHT_APPLIED = 0.0`도 동일 고정.
- 바꾸려면 **의도적 Phase2/K-M 설계**로 상수를 해제하고 referee·학습 가중을 evolve에 쓰도록 배선해야 함.  
  지금 피드백 연결(K-K)만으로는 **0.0 유지가 정상**.

### 젠스파크 오해 지적
- ❌ “feedback 연결되면 weight_applied가 바로 올라간다” → **아니요. Phase1 고정 0.**
- ❌ “예측 클릭 = evolve_log 기록” → **보장 안 됨.**

---

## 한 줄 요약 (젠스파크용)

```
예측(N): 재료·학습 = N 미만
채점(N): apply_draw_result_feedback(N)  ≡  after_predict(N+1)
weight_applied: Phase1=0 고정 · K-M 전 불변
지금: 1236 예측·채점 있음 / 1237 예측 없음 → 다음 정상클릭은 predict(1237)
```
