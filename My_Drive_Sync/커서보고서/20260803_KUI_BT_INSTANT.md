# K-UI-BT-INSTANT — 백테 DB 저장 후 페이지 즉시 반응

📅 2026-08-03 · **DONE**

## 문제

재검증 리셋으로 pool 캐시·pred가 비면, 백테 회차 브라우즈 GET이 **자동 WF(~15초/회)** 를 돌려 로딩이 멈춘 것처럼 보임.

## 변경

| 파일 | 내용 |
|------|------|
| `pool_view_cache.resolve_pool_view_for_ui` | 브라우즈 GET: 캐시 hit 또는 **backtest_only 요약 즉시** · 자동 WF **금지** |
| `routes` pool-view | docstring 정합 · compute/refresh만 계산 |
| `testlotto.js` + `?v=20260803a` | backtest_only 즉시 렌더 · mem cache 포함 |
| `_k_future_wire_revalidate` | pool 캐시 삭제 금지 · WF pred **유지** |

## 검증

| API | 결과 |
|-----|------|
| GET pool-view/1100 (캐시無·백테有) | **86ms** · `backtest_only=true` · summaries=2 |
| GET pool-view/1234 (캐시有) | **7ms** · ok |

상세 pool 10+5는 「🎯 3뇌 예측」(`compute=1`)만.
