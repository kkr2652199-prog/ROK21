# TESTLOTTO UI/UX 리프레시 (7021)

📅 2026-07-30 · ROK21 · 포트 **7021** · UI/UX ONLY (기능·API·coordinator 무변경)

---

## 1. 📋 형이 준 숙제

| 항목 | 결과 |
|------|------|
| UI/UX만 패치 (기능·동결 경로 금지) | **DONE** |
| B-04 로딩 스피너·이전 카드 숨김 | **DONE** |
| 여백·카드·타이포·색 계층 개선 | **DONE** |
| GenSpark UI 아이디어 1~2라운드 | **DONE** (랜딩 접속 · 채팅 미로그인) |
| Cursor 현대 패턴 적용 | **DONE** |
| 10+5 repack vs combined 회의 요약 | **§6** |
| 브라우저 검증·스크린샷 | **§5** |

---

## 2. 🔄 Before → After (시각 변경 요약)

| 영역 | Before | After |
|------|--------|-------|
| **회차 전환 (B-04)** | pool-view fetch(12~31초) 중 **이전 회차 카드 잔류** · `aria-busy` 조기 해제 | fetch 완료까지 **스피너+스켈레톤** · 이전 카드 즉시 교체 · `aria-busy` 유지 |
| **초기 로딩** | 회색 「로딩 중...」 한 줄 | 6칸 **스켈레톤 그리드** + 「실시간 pool 계산 중… (최대 30초)」 |
| **카드 그리드** | `minmax(280px)` · gap 12px | `minmax(300px)` · gap 16px · **그림자·호버** |
| **뇌 탭** | 일반 flex | **sticky** 상단 고정 · blur 배경 |
| **10+5 섹션 제목** | 정적 h4 | **sticky** 섹션 헤더 (pool / 몰아주기) |
| **접이식 패널** | summary 텍스트만 | **chevron(▸/▾)** · hint 색 분리 · hover/open 그림자 |
| **액션 바** | border-bottom만 | **카드형 배경** · 패딩·라운드 |
| **등수 카드** | 기존 rank 색 | 1·3등 **그림자 강조** 유지·가독성 ↑ |

**수정 파일:** `app/static/css/testlotto.css` · `app/static/js/testlotto.js` · `app/static/index.html` (캐시버스터 `20260730b`)

---

## 3. 🤖 GenSpark UI 라운드 (20260730)

| 항목 | 내용 |
|------|------|
| 접속 | `https://www.genspark.ai/` **OK** (워크스페이스 6.0 랜딩) |
| 채팅 | **로그인/채팅 UI 미진입** — 형 계정 필요 |
| 랜딩에서 얻은 방향 | 「질문→라이브 대시보드」 — **자연어 요약 + 차트 자동 갱신 + 단일 링크 공유** |

### GenSpark가 제안할 법한 UI (커서 추론 · 채팅 대체 초안)

1. **회차 히어로 = KPI 대시보드** — 당첨 6+1 · ge3(3개 이상 적중률) 미니 배지 · pool/repack 적중 요약 한 줄
2. **10+5 = 2단 아코디언** — pool 10장은 접힌 그리드(3열) · 몰아주기 5장은 **히어로 카드**(크게) · repack 점수 바
3. **백테스트 패널 = 라이브 차트** — 200회 ge3 추세 스파크라인 · combined vs repack 색 분리 · 「회차별」은 드로어(side panel)
4. **느린 pool-view** — 상단 progress bar + 「계산 중 N초」 (백엔드 캐시 없이도 UX만으로 완화)

→ **AI_COLLAB.md §3** 에 반영.

---

## 4. 💡 Cursor 적용 패턴

- CSS Grid `auto-fill` + generous padding
- Sticky: 회차 히어로 · 뇌 탭 · pool/repack 섹션 헤더
- `<details>` chevron + `[open]` 그림자 (접기 affordance)
- Loading: spinner + shimmer skeleton (B-04)
- `aria-busy` / `aria-live="polite"` 유지
- 반응형: 640px 이하 1열 카드
- 번호 공: 기존 `lottoMiniBallBg` 색 구간 + `is-hit` 글로우 유지

---

## 5. 🖥️ 브라우저 검증

| 항목 | 결과 |
|------|------|
| 탭 진입 | **OK** |
| 회차 1234 · 1035 전환 | **OK** — 전환 직후 스켈레ton·스피너 표시 확인 |
| 10+5 카드 | **OK** — pool 10 + 몰아주기 5 |
| 백테스트 펼치기 | **OK** |
| chevron 접이식 | **OK** |
| 스크린샷 | QA 턴에서 촬영 (testlotto 탭·로딩·카드) |

*pool-view 12~31초는 **백엔드 병목** — UI는 로딩 표시만 개선, 캐시/wire 미적용.*

---

## 6. 📝 회의 요약 — 10+5 repack vs combined select

| 주제 | 권고 (UI 관점) |
|------|----------------|
| **10+5 repack vs combined** | 화면은 **pool(10) / 몰아주기(5) 2섹션 유지**가 형이 QA PASS한 구조. combined(통합 선별)는 **백테스트 표·회차별**에서 전략 비교용 — 메인 탭에 combined 선택 UI 추가는 **형 GO 전 보류** (기능 변경 아님, 정보 과밀 우려) |
| **repack wire** | repack ge3=27.5% vs combined 14.5% — **장수 착시(artifact)** 주의. UI에 「15장 중 최고」 vs 「공정 5장」 뱃지 구분은 향후 옵션 |
| **성능 (B-03)** | pool-view 12~31s — **프리워arm·캐시는 백엔드**. UI는 스피너·「최대 30초」·스켈레톤으로 대기 체감 완화 |
| **다음 작업** | **K-SIGNAL-SELECT-FULL** (1182 walk-forward) — UI QA 완료, FULL 백테 다음 |

---

## 7. 📎 동결·범위 확인

- `coordinator` · `random.choices` · `_get_draws_before` · boost 상한 — **미수정**
- API·predict·DB 스키마 — **미수정**
- JS 변경: `testlottoLoadingSkeletonHtml` · `testlottoShowResultsLoading` · `renderPredictionsByBrain` **표시 타이밍만**

*HEAD는 커밋 후 `git rev-parse` 실측.*
