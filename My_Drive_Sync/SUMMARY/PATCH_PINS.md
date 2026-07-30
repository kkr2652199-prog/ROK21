# PATCH_PINS — 테스트로또 패치 마감 체크리스트

📅 2026-07-30 · ROK21 testlotto UI/DB

패치를 닫기 전 **브라우저 + DB** 로 아래 5항목을 확인한다.

---

## PIN checklist (testlotto 패치 종료 전)

| # | 항목 | 확인 방법 | PASS 기준 |
|---|------|-----------|-----------|
| 1 | **예측 버튼 단일** | 테스트로또 탭 → `.testlotto-actions-bar` | **`🎯 3뇌 예측` 1개만** · `🧠 두뇌 예측` 없음 |
| 2 | **백테스트 구간 pool 표시** | 회차 **1136 · 1200 · 1234** 선택 | pool/repack 카드 또는 백테스트 요약 · **「데이터 없음」 금지** |
| 3 | **비백테스트 회차** | 백테스트 범위 밖 회차 (예: **1034**) | pool 없음 OK · **「3뇌 예측」 클릭 전 빈 상태** |
| 4 | **백테스트 패널** | 「신호 백테스트 기록」 펼치기 | run 목록 · repack+combined · run_id 표시 |
| 5 | **tier hero ↔ cards** | hero 적중 등수 vs 세트 카드 | 동일 회차에서 **등수 불일치 없음** |

---

## 코드 PIN (주석)

`app/static/js/testlotto.js`:

```javascript
// PIN: single 3뇌 predict button — no 두뇌 duplicate
```

- `testlottoRunPoolPredict()` = 유일한 예측 진입점
- `testlottoPredict()` = 레거시 · `testlottoRunPoolPredict()` 로 위임만

---

## 백테스트 ↔ pool 캐시

| 시점 | 동작 |
|------|------|
| tail/backtest WF 실행 | `import_k_signal_backtest.py` 가 회차별 **pool_view_cache** 저장 |
| reset 후 | `tools/backfill_pool_cache_from_backtest.py --draw-start 1135 --draw-end 1234` |
| UI GET | 백테스트 회차 cache miss → API가 **자동 WF 1회** 후 캐시 |

---

## 관련 파일

- `app/testlotto/pool_view_cache.py` — `resolve_pool_view_for_ui`
- `tools/backfill_pool_cache_from_backtest.py`
- `reports/20260730_TESTLOTTO_BACKTEST_DATA_PIN.md`
