# TESTLOTTO 백테스트 데이터 PIN — pool 캐시 + 단일 버튼

날짜: 2026-07-30 · ID: **TESTLOTTO-BACKTEST-DATA-PIN**

---

## 1. 📋 선생님이 준 숙제

| 항목 | 내용 |
|------|------|
| **버그 1** | 테스트로또 actions bar에 `🎯 3뇌 예측` + `🧠 두뇌 예측` **동시 노출** → 두뇌 버튼 완전 제거 |
| **버그 2** | tail-100 백테스트(run_id 3·4) 후 eval 구간 pool-view 캐시 삭제 → **1136 등 「데이터 없음」** |
| **버그 3** | 재발 방지 PIN 체크리스트 + JS 주석 핀 |
| **기대** | 백테스트된 회차(1135~1234)는 **예측 버튼 없이** pool/repack 또는 백테스트 요약 표시 |

---

## 2. 🔧 학생이 한 일

### 근본 원인 (1줄)

**tail-100 reset이 eval 구간 `testlotto_pool_view_cache`만 삭제했고, 백테스트 WF는 per-draw 적중만 DB에 남겨 UI pool GET이 cache miss → 「데이터 없음」.**

### 수정

| 영역 | 변경 |
|------|------|
| **API** | `resolve_pool_view_for_ui` — 백테스트 draw_results 있는 회차는 GET 시 **자동 WF 1회 + 캐시** |
| **백테스트 import** | `import_k_signal_backtest.py` — WF 루프 중 **pool+repack 캐시 저장** |
| **백필** | `tools/backfill_pool_cache_from_backtest.py` — 기존 1135~1234 일괄 채움 |
| **UI** | `index.html` 단일 버튼 SSOT · `testlottoPredict()` → `testlottoRunPoolPredict()` 위임 · PIN 주석 |
| **PIN** | `My_Drive_Sync/SUMMARY/PATCH_PINS.md` 체크리스트 5항 |

---

## 3. 📊 검증 (브라우저 · API)

| 회차 | 기대 | 확인 |
|------|------|------|
| **1135 · 1136 · 1234** | pool 10+5 × 3뇌 · 「데이터 없음」 없음 | backfill + API auto-WF |
| **1034** (범위外) | 빈 상태 · 클릭 전 OK | cache_miss 유지 |
| **actions bar** | `🎯 3뇌 예측` **1개** | index.html + `initTestlottoActionsBarPin()` |

---

## 4. ✅ 맞은 것 / ❌ 틀린 것

- ✅ 백테스트 run_id 3·4 · draw_results 400행 **유지**
- ✅ eval reset 시 **backtest 테이블 미삭제** (기존 정책 유지)
- ✅ coordinator wire **미배선**
- ❌ (과거) reset 후 pool 캐시 미복구 → **본 패치로 해소**

---

## 5. 다음

- K-SIGNAL-SELECT-FULL (1182 walk-forward) — `NEXT_ACTIONS.md`
- 패치 마감 시 **`PATCH_PINS.md` 5항** 브라우저 spot check

*PIN:* `My_Drive_Sync/SUMMARY/PATCH_PINS.md` · backfill: `python tools/backfill_pool_cache_from_backtest.py --draw-start 1135 --draw-end 1234`
