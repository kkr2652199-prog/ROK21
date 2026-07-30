# TESTLOTTO 클릭 예측 + 재시작 로딩 금지 (20260730)

> **숙제형 보고** · 형 요구: 페이지/회차 전환 시 자동 WF 계산 금지 · DB 캐시만 즉시 · 버튼 클릭 시에만 compute

## 1. 문제 (형 피드백)

| 항목 | Before | After |
|------|--------|-------|
| 서버 재기동 | startup `prewarm_visible_range(±40)` 백그라운드 WF | **prewarm 제거** — 재시작만으로 계산 안 함 |
| 페이지/회차 전환 | `renderPredictionsByBrain` → pool-view API **항상 live/miss compute** | **cache-only GET** · miss 시 빈 상태 |
| 미래 1235 | 탭 진입 시 자동 pool fetch | 캐시 있으면 즉시 · 없으면 「추첨 전 · 버튼 클릭」 |
| 백테스트 DB | (변경 없음) | `testlotto_backtest_*` **재시작 시 삭제 없음** · reset 전까지 유지 |

## 2. API 변경

### `GET /api/testlotto/predict/pool-view/{회차}`

| 파라미터 | 동작 |
|----------|------|
| (없음) | **DB 캐시만** — hit 즉시 · miss `{ok:false, cache_miss:true}` |
| `?compute=1` | miss 시 WF 1회 계산+저장 · hit 즉시 |
| `?refresh=1` | 강제 재계산 |

### 관리용 reset (일반 UI 미노출)

- `DELETE /api/testlotto/predict/pool-view/cache/{draw_no}` — 회차별
- `DELETE /api/testlotto/predict/pool-view/cache` — 전체

모듈: `clear_pool_view_cache()` · `app/testlotto/pool_view_cache.py`

## 3. UI 변경

| 버튼 | 역할 |
|------|------|
| **🎯 3뇌 예측** (primary) | pool-view `?compute=1` — **유일한 pool 자동 계산 트리거** |
| 🧠 두뇌 예측 (secondary) | engine POST `/predict/{n}` (coordinator · 기존) |

### 회차 전환 (`testlottoShowDrawContext`)

- hero 당첨번호만 갱신
- 캐시 hit → 「**DB 캐시 · 저장됨** · {computed_at} · Nms」+ 15세트
- 캐시 miss → 「예측 버튼을 눌러주세요」또는 미추첨 「추첨 전 · 예측하려면 「3뇌 예측」 버튼을 클릭하세요」
- **로딩 스피너 없음** (miss 시)

### batch prewarm (유지)

- `python tools/run_testlotto_pool_view_prewarm.py --draw 1234` — 관리자용 · 브라우즈 자동 X

## 4. tier fix 회귀 (20260730d 유지)

| 회차 | hero | 비고 |
|------|------|------|
| 1214 | **5등 4** (4등 0) | pool-view SSOT 채점 · PASS |
| 1235 | 캐시 hit · 미추첨 | DB 캐시 즉시 |
| 1232 | 캐시 miss · 빈 상태 | 회차 전환 시 compute **없음** · PASS |

## 5. 변경 파일

- `app/main_v13.py` — startup prewarm 제거
- `app/testlotto/routes.py` — cache-only 기본 · compute/refresh · DELETE cache
- `app/testlotto/pool_view_cache.py` — `clear_pool_view_cache()`
- `app/static/js/testlotto.js` — `testlottoShowDrawContext` · `testlottoRunPoolPredict` · auto fetch 제거
- `app/static/index.html` — 「3뇌 예측」 버튼 · v20260730e
- `app/static/css/testlotto.css` — empty state

## 6. 검증 체크리스트

- [x] 서버 재시작 후 1234/1214 캐시 hit → 로딩 없이 instant
- [x] 1232 miss → 빈 상태 · 회차 전환 compute 없음
- [x] 「3뇌 예측」 클릭 → compute+DB 저장
- [x] 1214 tier hero 5등 4 유지
- [x] frozen/coordinator 미변경

---
*HEAD는 push 후 git rev-parse 실측*
