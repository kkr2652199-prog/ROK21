# TESTLOTTO DB 초기화 + tail-200 백테스트 재실행

HEAD `fa9c2aa` · SSOT `D:\ROK21` · 포트 7021 · 2026-08-03

## 범위

- **대상:** `data/lotto_testlotto.db` 런타임 테이블만
- **보존:** `lotto_draws` (1235회)
- **미터치:** `lotto4.db`, `lotto_hyodo.db`

## 실행

1. testlotto_backtest_*, pool_view_cache, lotto_predictions, brain learn/review 삭제 · weights 초기화
2. `import_k_signal_backtest.py --n-eval 200 --which both` (~57s)
3. `backfill_pool_cache_from_backtest.py --draw-start 1035 --draw-end 1234`
4. `run_testlotto_pool_view_prewarm.py --draw 1235`

## 결과

| 항목 | 값 |
|------|-----|
| draw-index | n=**200**, 1035~1234 |
| pool-index | n=**200**, 1035~1234 |
| pool_view_cache | **201** distinct (1035~1235), 603 rows |
| backtest_draw_results | 800 (4 runs × 200) |
| 1210 pool | ok · cached · 10+5 |
| 1235 pool | ok · cached · 10+5 |
| lotto_predictions | 0 (UI는 pool_view_cache 기준) |

## 브라우저 확인 (형)

http://localhost:7021/ · Ctrl+F5 · 테스트로또 탭 · **1210** · **1235** — 3뇌 accordion + pool 10+5 + 「DB 캐시 · 저장됨」
