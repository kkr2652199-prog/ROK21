# kweon 정리 + FINDINGS 갱신 + K-00 착수 준비

📅 2026-07-26 KST · HEAD 작업 전 `616db13`

---

## 1. STEP 0 정찰 기록 확인

| 항목 | 결과 |
|------|------|
| 기존 보고서 | ✅ `reports/20260726_kweon_인프라구축.md` §STEP 0 존재 |
| 재실측 | ✅ 20260726 오후 — DB·git ls-files 갱신분 아래 반영 |

### (1) app/lotto · app/lotto2 소속 (재확인)

| 패키지 | `__init__.py` | main_v13 `include_router` | 정의 prefix | 실제 노출 |
|--------|---------------|---------------------------|-------------|-----------|
| `app/lotto/` | 1군 독립 패키지 | **없음** (init+scheduler만) | `/api/lotto` | ❌ 미마운트 |
| `app/lotto2/` | 2군(V9) 전용 | **없음** (init만) | `/api/lotto2/v11` | ❌ 미마운트 |
| `app/lotto4/` | 4군 | ✅ | `/api/lotto4/v13` | ✅ |
| `app/testlotto/` | — | ✅ | `/api/testlotto` | ✅ |
| `app/hyodo/` | — | ✅ | `/api/hyodo` | ✅ |

**K-03 확정:** 1~2군 **레거시 잔존** · 4군 런타임 API **비노출**

### (2) 동결 토큰 (재확인)

**random.choices in predict_statistical.py:**

| 파일 | 라인 |
|------|------|
| `app/testlotto/predict_statistical.py` | 234 |
| `app/hyodo/predict_statistical.py` | 188 |
| `app/lotto/predict_statistical.py` | 188 |

**`_get_draws_before` def:**

| 파일 | 라인 |
|------|------|
| `app/testlotto/data_service.py` | 684 |
| `app/hyodo/data_service.py` | 684 |
| `app/lotto/data_service.py` | 760 |

### (3) git ls-files `*.db` (20260726 재실측)

| 파일 | bytes |
|------|------:|
| `data/lotto.db` | 0 |
| `data/lotto4.db` | 17,944,576 |
| `data/combos/lotto_part_01.db` ~ `_20.db` | 각 14~15 MB |
| `backups/20260718_테스트뇌_배선전/data/lotto_testlotto.db` | 37,974,016 |
| `tools/pair_periodicity_analysis.db` | 258,048 |
| **합계** | **24 files · 306.08 MB (320,983,040 byte)** |

※ `backups/20260718_.../lotto_testlotto.db` git blob **0 byte** (빈 추적 파일)

---

## 2. FINDINGS.md 갱신

| ID | 변경 |
|----|------|
| K-01 | OPEN → **CLOSED** (STATUS 07-26 갱신) |
| K-03 | OPEN → **CLOSED** (1~2군 레거시 확정) |
| K-04 | OPEN → **CLOSED** (`0a1a55c`) |
| K-06 | **신규** per-draw fan-out · `app/lotto/draw_scheduler.py` |
| K-07 | **신규** fetch-latest 수동 · testlotto/hyodo routes |

---

## 3. 훅 실동작 검증

| # | 테스트 | 결과 |
|---|--------|------|
| 1 | Cursor Settings → Hooks 3개 | ⚠️ **수동 미확인** (IDE 재시작 필요) |
| 2 | STATUS_LATEST + `1군` → guard_paths | ✅ **exit 2** (파일 미변경) |
| 3 | predict_statistical + `random.choices` 편집 | ✅ **exit 2** (파일 미변경) |

---

## 4. DB gap (K-06/K-07 근거 · 20260726 실측)

| DB | lotto_draws MAX |
|----|-----------------|
| lotto4.db | 1234 (2026-07-25) |
| lotto_testlotto.db | 1231 (2026-07-04) |
| lotto_hyodo.db | 1231 (2026-07-04) |

---

## 5. 미확인

- `testlotto_brain_review` MAX draw — **미확인** (본 작업 범위 외)
- Cursor Hooks UI 로드 — **수동 미확인**

---

## 다음

- **K-00** `app/lotto4/` 정밀분석 착수
- **K-07** `POST /api/testlotto/fetch-latest` · `POST /api/hyodo/fetch-latest` 수동 실행
