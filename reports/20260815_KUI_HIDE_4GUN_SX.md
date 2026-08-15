# K-UI-HIDE-4GUN-SX (2026-08-15)

- **판정:** `HOLD_ON`
- 형 요청: 4군·전략X 탭이 신뢰 불가 예측번호를 보여 혼란 → **보이지 않게**

## 동작

| 항목 | 내용 |
|------|------|
| 숨김 탭 | `predict`(두뇌예측=4군) · `strategy-x` |
| 유지 | 효도로또 · 대시보드 · 테스트로또 · 나머지 메뉴 |
| 기본 화면 | `testlotto` |
| 자동로드 OFF | 페이지 진입 시 `syncPredictionsForCurrentDraw` / 전략X 생성 **미호출** |
| 대시보드 | 전략X 5뇌 적중표도 같이 숨김 (`strategyXBrainPowerTable`) |
| 복원 | `app/static/js/lotto4.js` 의 `ROK21_TESTLOTTO_FOCUS_HOLD = false` |
| 코드/엔진 | **불변** · UI 플래그만 · 1237 예측 없음 |

## 파일

- `app/static/js/lotto4.js` — `ROK21_TESTLOTTO_FOCUS_HOLD=true` · `HOLD_HIDE_VIEWS={predict,strategy-x}`
- `app/static/index.html` — 배너 문구 · 캐시버스트 `?v=20260815hold`
- `app/static/css/lotto4.css` — `.ui-hold-hidden` 주석만

## 비고

- 2026-08-08 HOLD_ON → 2026-08-10 형 요청으로 HOLD_OFF → **이번 턴 재ON**.
- 이전 HOLD는 효도도 숨겼음. 이번은 형이 **4군·전략X만** 지정 → 효도 유지.
