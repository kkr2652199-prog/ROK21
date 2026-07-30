# TESTLOTTO 브라우저 QA (7021)

📅 2026-07-30 · ROK21 · 포트 **7021** · HEAD `7c6e9aa` (QA 시점)

---

## 1. 📋 형이 준 숙제 (검증 항목)

| # | 항목 | 결과 |
|---|------|------|
| 1 | `http://localhost:7021/` → **테스트로또** 탭 | **PASS** |
| 2 | 뇌별(stat/markov/review) **10장 pool + 5장 몰아주기** | **PASS** (API·UI 모두 10+5) |
| 3 | **K-SIGNAL 백테스트 기록 (200회)** 펼치기 · DB 2건 | **PASS** |
| 4 | **회차별** 버튼 · 1035~1234 per-draw | **PASS** (200행) |
| 5 | 한국어 라벨 (raw ID 노출 최소화) | **PASS** (표·뇌탭 OK · 섹션 제목 1건 수정) |
| 6 | API `/pool-view/{draw}` · `/backtest/runs` | **PASS** |

**종합 판정: PASS (경미·성능 이슈 4건 · 2건 UI 수정 적용)**

---

## 2. 🔧 테스트 환경

| 항목 | 값 |
|------|-----|
| 서버 | **기동함** — `python run_v13.py` (7021, QA 중 로컬 기동) |
| 브라우저 | Cursor IDE Browser MCP |
| HEAD (QA 시작) | `7c6e9aa057e73370b898b2865e4985f35428172b` |
| DB | `testlotto_backtest_runs` 2건 · `testlotto_backtest_draw_results` 400행 |
| 스크린샷 | **3장** (테스트로또 탭·10+5·백테스트·회차별) |

---

## 3. ✅ 패치별 상세

### 3-1. 테스트로또 탭
- 좌측 **테스트로또** 클릭 → `ROK21 테스트로또` 헤더·회차 선택·뇌 탭·pool/repack 영역 표시 확인.

### 3-2. 10+5 pool (3뇌)
- **API** (`/api/testlotto/predict/pool-view/{draw}`): 1035·1100·1234 모두 stat/markov/review 각 **pool 10 · repack 5**.
- **UI**: 1234회 · markov/review 탭 각 `.lotto-set-card` **15장** (=10+5).
- 당첨번호(1234: 1·15·19·31·35·43 +27) 대비 적중 하이라이트 동작 확인.

### 3-3. 백테스트 기록 (200회)
- `<details>` 펼치기 → 2행 테이블:
  - 신호 선별 빠른 검증(200회) · 통합 선별 · ge3 **14.5%**
  - 번호 몰아주기 빠른 검증(200회) · 신호 몰아주기 · ge3 **27.5%**
- 회차 범위 **1035~1234 (200회)** 표기 일치.

### 3-4. 회차별 버튼
- 1행 **회차별** 클릭 → `신호 선별 빠른 검증 · 통합 선별` 하위 테이블 **200행**.
- 범위: 1234회(2개·미당첨) ~ 1035회(1개·미당첨) · API `draw_limit=200` 와 일치.

### 3-5. 한국어 라벨
- 뇌 탭: 통계요정 / 흐름술사 / 복습왕 (raw `stat`/`markov`/`review` 미노출).
- 백테스트 표: `survey_label_ko`·`strategy_label_ko`·`gate_mode_ko` 한국어.
- **수정:** 섹션 summary `K-SIGNAL 백테스트…` → `신호 백테스트 기록…`
- 참고: 「각 프로그램 설명·제한 사항」 접힌 패널 내부는 K-Q/K-T 등 **내부 근거 ID** 유지(참고용·의도된 것으로 판단).

### 3-6. API 직접 호출
| API | 결과 |
|-----|------|
| `GET /api/testlotto/backtest/runs` | 2 runs JSON OK |
| `GET /api/testlotto/backtest/runs/2?draw_limit=200` | 200 draws, 1035~1234 |
| `GET /api/testlotto/predict/pool-view/1234` | ok, 10+5×3뇌 |

---

## 4. 🐛 버그 목록

| ID | 심각도 | 재현 | 기대 | 실제 | 조치 |
|----|--------|------|------|------|------|
| **B-01** | 경미 | 뇌 탭(stat/markov/review) 표시 | 이모지 1회 | `🧚 🧚 통계요정` 등 **이중 이모지** (`icon` + `displayName` 중복) | **수정** — 탭에 `b.name`만 사용 |
| **B-02** | 경미 | 백테스트 `<summary>` 문구 | 한국어 | `K-SIGNAL 백테스트 기록` raw 접두 | **수정** — `신호 백테스트 기록` |
| **B-03** | 중 | 회차 변경 또는 탭 진입 후 pool 표시 | 수 초 내 10+5 갱신 | `pool-view` API **12~31초** (1035: 23.2s, 1234: 12.4s) | **보고만** — WF live 계산 병목 |
| **B-04** | 중 | 회차 콤보박스 변경 직후 | 로딩 표시 + 이전 회차 카드 숨김 | `renderPredictionsByBrain` 가 pool-view fetch **전** `aria-busy` 해제 → 최대 ~30초 **이전 회차 카드 잔류** 가능 | **보고만** — 로딩 UX 개선 필요 |
| **B-05** | 경미 | 1234회 등 당첨 후 pool-view만 표시 | pool+repack 적중 채점 | 1~5등 없음 메시지(정상) · 개별 카드 **미당첨** 표시(정상) | 해당 없음(동작 OK) |

**버그 수: 5건 (수정 2 · 보고 2 · 해당없음 1)**

---

## 5. 🖥️ 콘솔·CDP

- `Log.enable` 후 **console.error 없음**.
- 네트워크 실패·JS 예외 미관측.

---

## 6. 📝 다음 (좁은 개선)

1. **pool-view 캐시/프리워arm** — 회차 전환 30초 대기 UX (coordinator wire 금지 유지).
2. pool-view fetch 중 **스피너·이전 카드 blur** (`aria-busy` 유지).
3. **K-SIGNAL-SELECT-FULL** — 형 육안 PASS 후 full 1182 (NEXT_ACTIONS).

---

## 7. 📎 QA 중 수정 파일

| 파일 | 변경 |
|------|------|
| `app/static/js/testlotto.js` | 뇌 탭 이중 이모지 제거 |
| `app/static/index.html` | 백테스트 summary 한국어 |

*동결 경로(coordinator · random.choices · _get_draws_before) **미수정**.*
