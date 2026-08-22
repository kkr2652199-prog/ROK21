# K-ARMY4-SX-BRAIN-REMOVE (2026-08-22)

- **판정:** `REMOVE_OK`
- 형 요청: 4군·전략X **뇌만** 삭제 · 테스트로또와 독립 · 공통기능 유지 · 이후 패치

## 삭제

| 항목 | 삭제 전 | 삭제 후 |
|------|---------|---------|
| v13_* 예측 | 4830 | 0 |
| strategy_x_* 예측 | 24410 | 0 |
| 그 외 army4 예측 | 0 | 0 |
| lotto_draws | 1237 (MAX 1237) | 1237 (MAX 1237) |

## 유지 (테스트로또·공통)

- `combinadic.py` · 로또 조회 · 전체 조합 · 데이터수집 · 효도 · 테스트로또 · 테스트 대시보드
- `lotto_testlotto.db` **미접촉**
- 뇌 소스 파일은 디스크에 남김(공통 import 붕괴 방지). 생성 API는 `removed` 반환.

## UI 숨김

- 4군 대시보드 · 두뇌예측 · 전략 X · 명예의전당 · 두뇌상태

- 1237 예측 생성 **없음**. APPLY 테스트로또 패치는 별 GO.

## 파일

- `app/lotto4/army4_brains_removed.py`
- `app/lotto4/v13_routes.py` · `app/static/js/lotto4.js` · `app/static/index.html`
- `tools/_k_army4_sx_brain_remove.py`
