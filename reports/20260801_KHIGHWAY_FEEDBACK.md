# K-HIGHWAY-FEEDBACK — coordinator 자동 피드백 루프

📅 2026-08-01 · **PASS** · `coordinator.py` 단독 · 형 GO

## 목적

예측 실행(`run_coordinated_prediction`) 진입 시 **직전 회차(prev)** 예측·정답을 자동 채점해 `apply_feedback` → `learn_state` 갱신. walk-forward 백테스트와 동일한 복습 고리를 **live 경로**에 연결.

## 변경 파일

| 파일 | 변경 |
|------|------|
| `app/testlotto/brains/coordinator.py` | `_auto_feedback` · `_detect_missed_patterns` 신규 · deprecated import 3줄 삭제 |

## 신규 함수

### `_detect_missed_patterns(pred_nums, actual_nums, draws_before=None)`

| 패턴 | 조건 |
|------|------|
| `carry_over` | 직전 회차 번호∩정답 이월분이 있는데 예측이 하나도 못 담음 |
| `ending_digit` | 정답·예측 끝수 집합 symmetric_difference ≥ **3** |
| `overdue` | 정답에 gap≥**30** 미출 번호 있는데 예측에 없음 |

`draws_before`는 `_get_draws_before(prev_draw_no)` — carry/overdue용 · `_get_draws_before` **미수정**.

### `_auto_feedback(target_draw_no, conn)`

1. `prev_draw_no = target - 1` · `lotto_draws` 정답 없으면 return
2. `lotto_predictions`에서 `target_draw_no=prev` 전체 로드
3. 3뇌(stat/markov/review) 각각 best row(matched_count·confidence) 선택
4. `last_draw_no >= prev_draw_no` → skip (중복 방지)
5. `apply_feedback(tag, prev_draw_no, matched_count, missed)` 호출

### `run_coordinated_prediction`

- `init_lotto_db()` · `conn` 직후 **`_auto_feedback(target_draw_no, conn)`** 1줄 추가
- 생성→채점→저장 흐름 **불변**

## 삭제

```python
# from app.testlotto.brains import predict_flow_shaman, predict_review_king, predict_stat_fairy
```

PREDICT_MODULES(stat/markov/review_brain) **미변경**.

## 검증

| 항목 | 결과 |
|------|------|
| `from app.testlotto.brains.coordinator import run_coordinated_prediction` | **OK** |
| `apply_feedback` import | **OK** |
| random.choices · _get_draws_before · BOOST_CAPS | **미수정** |

## 다음

- **K-HIGHWAY-REFEREE** — 형 GO 대기 (자동 착수 금지)
- K-NEW-ENGINE-MARKOV-A1 — 별도 트랙 · 형 GO 대기
