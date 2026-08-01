# K-HIGHWAY-REFEREE — aux_referee score_set 실동작

📅 2026-08-01 · **PASS** · `aux_referee.py` 단독 · 형 GO

## 목적

심판관(`aux_referee`) `score_set()`이 항상 0.5(무동작)이던 문제를 해결. `get_referee_weights()`의 **brain_tag별 recent_avg_match** 정규화 가중을 0~1 채점 점수로 반영.

## 변경 파일

| 파일 | 변경 |
|------|------|
| `app/testlotto/brains/aux_referee.py` | `score_set()` — referee 가중 기반 점수 |

## score_set() 로직

```python
normalized_weight = referee_weights.get(brain_tag, 1/3)
return min(1.0, max(0.0, 0.5 + (normalized_weight - 1/3) * 1.5))
```

| 조건 | 반환 |
|------|------|
| `brain_tag` 있음 · 가중치 정상 | 0.0~1.0 (균등 1/3이면 **0.5**) |
| `brain_tag` None | **0.5** (폴백) |
| 예외 | **0.5** (폴백) |

## get_referee_weights() 확인

`learn_state.get_referee_weights()` — `recent_avg_match` 기반:

- `weights[tag] = 1.0 + avg * 0.15` → 합=1 정규화
- `get_predict_brain_weights()` 시그니처 **변경 없음** (delegate 유지)

## 검증

| 테스트 | 결과 |
|--------|------|
| `from app.testlotto.brains.aux_referee import score_set` | **OK** |
| `score_set(..., brain_tag='stat')` | **0.5** ∈ [0,1] |
| `score_set(..., brain_tag=None)` | **0.5** |

## 동결 준수

- `random.choices` · `_get_draws_before` · `BOOST_CAPS` — **미수정**

## 선행·연계

- **K-HIGHWAY-FEEDBACK** — `_auto_feedback` → `apply_feedback` → `recent_avg_match` 갱신 경로

## 다음

- **K-HIGHWAY-QUOTA** — 형 GO 대기 (자동 착수 금지)
