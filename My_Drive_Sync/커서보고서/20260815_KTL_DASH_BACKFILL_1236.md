# K-TL-DASH-BACKFILL-1236 (2026-08-15)

- **판정:** `BACKFILL_PARTIAL`
- 형 요청: 예측 초기화 + **새 탭** 테스트 대시보드 + 1–1236 백필
- 근거: `docs/benchmarks/20260815_KTL_DASH_BACKFILL_1236.json`

## UI

| 항목 | 내용 |
|------|------|
| 새 탭 | 사이드바 `테스트 대시보드` · `data-view=tl-dash` |
| 기존 대시보드 | 4군 요약 **유지** |
| 표시 | 카운트다운 · 타일4 · 적중비율(기록) · 3뇌 1~5등 표 |
| 3뇌 | 과거학습(stat) · 선호번호(markov) · 금액뇌(review) |
| API | `GET /api/testlotto/focus-dashboard` · `GET /api/testlotto/focus-dash/progress` |

## 백필 실측

| 항목 | 값 |
|------|-----|
| 삭제 pred/cache/evolve | **3005** / **601** / **601** |
| fill ok / fail | **3704** / **4** |
| peek | **0** |
| pred 후 | **18520** · **2–1236** · stat **6175** · markov **6170** · review **6175** |
| cache 후 | **3704** · **2–1236** |
| pred_1237 | **0** |
| MAX | **1236** |
| ledger 보존 | **True** · stat **3000** |

## 실패 4건 (캐시 결측 실측)

| 회차 | 뇌 | 이유 |
|------|----|------|
| 1 | stat·markov·review | 과거 draws **0** → empty_build |
| 2 | markov만 | 과거 1회 → empty_build (재시도 동일) |

- 우열/hits 클레임 금지. 대시보드 1~5등 숫자는 **기록**.
- 롤백=`backups/20260815_TLDASH전_DB전체/`
- 1237아님.

## 파일

- `tools/_k_tl_dash_backfill_1236.py`
- `app/testlotto/routes.py` · `app/static/index.html` · `app/static/js/lotto4.js`
- `docs/benchmarks/20260815_KTL_DASH_BACKFILL_1236.json`
