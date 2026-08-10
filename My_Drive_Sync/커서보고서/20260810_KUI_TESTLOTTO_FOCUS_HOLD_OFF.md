# K-UI-TESTLOTTO-FOCUS-HOLD-OFF

📅 2026-08-10 KST · **HOLD_OFF** · HEAD(작업)=`0c4f640`

형: 「홀딩시켜놓은 챕들 다시 풀어줘」

## 변경

| 항목 | 값 |
|------|-----|
| `ROK21_TESTLOTTO_FOCUS_HOLD` | `true` → **`false`** (`app/static/js/lotto4.js`) |
| 복원 탭 | 두뇌예측(`predict`) · 전략 X(`strategy-x`) · 효도로또(`hyodo`) |
| HOLD 배너 | `#rok21HoldBanner` 기본 `hidden` 유지 |
| 진입 | 예측 자동로드 복원 (`syncPredictionsForCurrentDraw`) |

## 종료체크 정정

- 본 작업일이 **2026-08-10** 인데 초기에 `20260808_*` 파일명으로 잘못 기록됨 → **본 파일·벤치로 교체**
- 구 오명: `reports/20260808_KUI_TESTLOTTO_FOCUS_HOLD_OFF.md` (삭제)

## 파일

- `docs/benchmarks/20260810_KUI_TESTLOTTO_FOCUS_HOLD_OFF.json`
- `My_Drive_Sync/커서보고서/20260810_KUI_TESTLOTTO_FOCUS_HOLD_OFF.md` (동기)
- 선행 HOLD_ON: `docs/benchmarks/20260808_KUI_TESTLOTTO_FOCUS_HOLD.json`
