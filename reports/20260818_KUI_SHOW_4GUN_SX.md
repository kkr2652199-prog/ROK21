# K-UI-SHOW-4GUN-SX (2026-08-18)

- **판정:** `HOLD_OFF`
- 형 요청: 4군·전략X **모두 보이게** 풀어 달라

## 동작

| 항목 | 내용 |
|------|------|
| 다시 보임 | `predict`(두뇌예측=4군) · `strategy-x` |
| 유지 | 테스트 대시보드 탭 · 효도 · 기존 대시보드 |
| 플래그 | `ROK21_TESTLOTTO_FOCUS_HOLD=false` |
| 자동로드 | HOLD_OFF라 두뇌예측/전략X 번호 **다시 로드** (혼동 주의) |
| 엔진/DB | **불변** · 1237 예측 없음 |

## 파일

- `app/static/js/lotto4.js`
- `app/static/index.html` — 캐시버스트 `?v=20260818holdoff`
