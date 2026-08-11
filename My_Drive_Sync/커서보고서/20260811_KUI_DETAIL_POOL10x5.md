# K-UI-DETAIL-POOL10x5

📅 2026-08-11 KST · **PATCHED** · 형 「tldSingleView 초창기→최신 10+5 · 보기좋게」

## 변경
| 영역 | 내용 |
|------|------|
| 상세 HTML | ② **3뇌 10+5** 섹션 신설 · 점프내비 · 오답노트는 ③ |
| 상세 JS | `pool-view` 연동 · knobs 스트립 · 뇌 요약칩 · sticky 탭 · 2열 세트카드 · 적중 하이라이트 |
| API | `tune_snapshot` · 캐시 schema **3→4** (튜닝 knobs 반영 재계산) |
| 메인탭 | 아코디언 카운트 `10+5` 표기 |

## 실측 (1236)
- pool-view refresh OK · schema4 · markov BLEND **0.55** · review **0.85** · stat HINT **52**
- pool×10 / repack×5 뇌별 표시 · HTTP200 · UI 스크린샷 확인

## 롤백
- static `?v=` 되돌리기 · `CACHE_SCHEMA_VERSION=3`
- 공유=lotto_draws만 원칙 유지

## 파일
- `app/static/testlotto-detail.html` · `js/testlotto-detail.js` · `css/testlotto-detail.css`
- `app/testlotto/signal_pool.py` · `pool_view_cache.py` · `js/testlotto.js`
