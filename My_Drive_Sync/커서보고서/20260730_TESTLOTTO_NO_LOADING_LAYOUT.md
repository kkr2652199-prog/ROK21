# TESTLOTTO 로딩 제거 + 15세트 UI 재배치 (20260730)

> **숙제형 보고** · 형 피드백 B-03/B-04 대응 · coordinator wire 금지 · frozen 경로 미수정

## 1. 문제 (형 피드백)

| 항목 | 내용 |
|------|------|
| **B-03 로딩** | `GET /api/testlotto/predict/pool-view/{회차}` 매 요청 live WF → **12~31초** |
| **B-04 UX** | 「최대 30초」 상시 표시 · 회차 전환 시 이전 카드 잔류 |
| **레이아웃** | ①10장 pool + ②몰아주기 5장 **세로 적층** · 뇌 탭 클릭해야 3뇌 확인 |

## 2. 로딩 해결 (캐시)

### 구현
- **SQLite** `testlotto_pool_view_cache` (draw_no, brain, pool_json, repack_json, seed, computed_at)
- 모듈: `app/testlotto/pool_view_cache.py`
- API: `get_or_build_pool_view()` — hit 즉시 반환 · miss 시 `build_pool_and_repack()` 1회 후 저장
- 응답 필드: `cached`, `cache_ms`, `compute_ms` (최초만)
- **앱 기동** `main_v13.py` startup → `prewarm_visible_range(window=40)` 백그라운드
- CLI: `python tools/run_testlotto_pool_view_prewarm.py --draw 1234`

### frozen·wire
- `signal_pool.build_pool_and_repack` **로직 변경 없음** (캐시 래퍼만)
- `coordinator` **미배선** 유지
- `random.choices` · `_get_draws_before` · boost 상한 **미접촉**

### 실측 (2026-07-30)

| 회차 | 최초 계산 | 캐시 hit (Python) | HTTP API hit |
|------|-----------|-------------------|--------------|
| 1234 | 12.9s | **4.2ms** | **28ms** (cache_ms) / 341ms HTTP 왕복 |
| 1235 | 11.4s | **3.7ms** | **48ms** |

- **목표 <500ms** ✅ (캐시 hit 기준)
- 브라우저 1234→1235→1234: 2회째부터 「캐시에서 불러옴 · 4.1ms」· 메모리 캐시 hit

### UX
- 「최대 30초」 **제거** — 최초 miss 시만 「처음 pool 계산 중… (최초 1회만…)」
- 캐시 hit 시 스피너 최소 · 「캐시에서 불러옴 · Nms」 우하단 표시

## 3. UI 재배치 (15세트 보기)

### 변경 요약
| Before | After |
|--------|-------|
| 뇌 탭 3개 · 한 번에 1뇌 | **「전체 보기」** 기본 · 3뇌 **아코디언** 스크롤 |
| pool 10 + repack 5 세로 적층 | **서브탭** 「10장 pool」\|「몰아주기 5장」 — 한 종류만 표시 |
| 뇌 헤더 분산 | 접힘 시 **이모지+이름+역대(0·0·0·0·2)** 한 줄 |

### 파일
- `app/static/js/testlotto.js` — `_testlottoPoolViewMemCache`, accordion, sub-tabs
- `app/static/css/testlotto.css` — accordion · subtab · cache note
- `app/static/index.html` — cache bust `20260730c`

### 기능 회귀
- 10+5 데이터 **동일** (`build_pool_and_repack` SSOT)
- 백테스트 `<details>` 패널 **변경 없음**
- 카톡 복사·1~5등 모달·warrant 패널 **유지**

## 4. GenSpark·협업 메모 (AI_COLLAB 반영)

1. **캐시**: SQLite per-brain row · startup prewarm ±40회 · `?refresh=1` 강제 재계산
2. **아코디언**: chevron + tier summary collapsed · stat 기본 펼침
3. **서브탭**: pool/repack 전역 1개 (뇌별 분리 불필요 — 동시에 한 종류만 보면 됨)
4. **드롭다운**: 기존 `#testlottoDrawSelect` 유지

## 5. 다음 (형 선택)

| ID | 내용 |
|----|------|
| K-SIGNAL-SELECT-FULL | full 1182 walk-forward (기존 NEXT) |
| (선택) | 캐시 miss 회차 bulk prewarm 스크립트 cron |

## 6. 검증 체크리스트

- [x] API 캐시 hit <500ms
- [x] 브라우저 1234→1235→1234 재방 instant
- [x] accordion + pool/repack sub-tabs DOM 존재
- [x] frozen/coordinator 미변경

---
*HEAD는 push 후 git rev-parse 실측*
