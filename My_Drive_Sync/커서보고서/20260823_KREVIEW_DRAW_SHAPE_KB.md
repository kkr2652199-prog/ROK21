# K-REVIEW-DRAW-SHAPE-KB (2026-08-23)

- **판정:** `APPLY_OK` · 금액뇌 읽기만 · 전체조합 미반영 · 몰아주기 미접촉
- 시각: 2026-08-23T11:46:31+09:00
- 형: 로또조회 1회~당첨회 특징을 회차마다 저장. 전체조합은 다음. 패치적용 전 지식.
- 근거: `20260823_KREVIEW_DRAW_SHAPE_KB.json`

## 1번째 오더

- 저장 `1238` / fail `0` · 구간 1–1238 · src `1238`
- DB draws_max `1238` · kb `1238` (1–1238)
- 구 draw_features `1238` (1237·1238 빈칸 채움)
- 읽기 요약 as_of `1238` n `1238` span평균 `32.6979`
- 1236 발권 동일 `True` (가중·거절 변경 없음)
- pred_1237 `0`

## 엔진

- `summarize_before(draws)` · as_of=타깃 이전
- `REVIEW_SHAPE_KB_READ=True` · 생성 공식 불변
- 전체조합 탭 코드 불변

## 파일

- `app/testlotto/brains/review_brain/draw_shape_kb.py` · `engine.py` · `models.py`
- `20260823_KREVIEW_DRAW_SHAPE_KB.json` · `20260823_KREVIEW_DRAW_SHAPE_KB.md`
