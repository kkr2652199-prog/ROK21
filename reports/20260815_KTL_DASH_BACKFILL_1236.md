# K-TL-DASH-BACKFILL-1236 (2026-08-15)

- **판정:** `RUNNING` (작성 시점 · 백필 프로세스 진행 중)
- 형 요청: 모든 예측번호 초기화 + **새 탭** 테스트 대시보드(기존 대시보드와 동일 레이아웃) + 1–1236 백필

## UI

| 항목 | 내용 |
|------|------|
| 새 탭 | 사이드바 `테스트 대시보드` · `data-view=tl-dash` |
| 기존 대시보드 | 4군 요약 **유지**(숨기지 않음) |
| 표시 | 카운트다운 · 타일4 · 적중비율 · 3뇌 1~5등 표 |
| 3뇌 | 과거학습(stat) · 선호번호(markov) · 금액뇌(review) |
| API | `GET /api/testlotto/focus-dashboard` · `GET /api/testlotto/focus-dash/progress` |
| 주의 | 1~5등 건수=**기록**. 우열/성능 클레임 금지 |

## 백필

| 항목 | 내용 |
|------|------|
| 초기화 | `lotto_predictions` 3뇌 전부 · `testlotto_pool_view_cache` 전부 · evolve 1–1236 · pred_1237 |
| 보존 | 원장 stat**3000** · 숙제/learn **미삭제** |
| 범위 | 1–1236 · 3뇌 · 회차당 repack **5**장 |
| 1회 | 과거 draws 0 → 3뇌 **empty_build 실패 예상** (2회부터 정상) |
| 롤백 | `backups/20260815_TLDASH전_DB전체/` |
| 1237 | 예측 **없음** |

## 파일

- `app/static/index.html` · `app/static/js/lotto4.js`
- `app/testlotto/routes.py`
- `tools/_k_tl_dash_backfill_1236.py`
- 진행파일 `docs/benchmarks/_k_tl_dash_backfill_progress.json` (완료 후 벤치 JSON으로 교체)
