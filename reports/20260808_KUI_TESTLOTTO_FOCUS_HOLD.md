# K-UI-TESTLOTTO-FOCUS-HOLD (2026-08-08)

- **판정:** `HOLD_ON`
- 형 요청: 전략X·4군 예측 번호 혼동 방지 · **테스트로또만** 진행

## 동작

| 항목 | 내용 |
|------|------|
| 숨김 탭 | `predict`(두뇌예측) · `strategy-x` · `hyodo` |
| 기본 화면 | `testlotto` |
| 자동로드 OFF | 페이지 진입 시 `syncPredictionsForCurrentDraw` 미호출 → 1236 등 번호 안 뜸 |
| 복원 | `lotto4.js` 의 `ROK21_TESTLOTTO_FOCUS_HOLD = false` |

## 파일

- `app/static/js/lotto4.js`
- `app/static/index.html`
- `app/static/css/lotto4.css`
