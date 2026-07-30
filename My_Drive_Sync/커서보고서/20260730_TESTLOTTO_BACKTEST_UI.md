# TESTLOTTO 백테스트 UI + DB 패치 (숙제형)

📅 2026-07-30 · ROK21 · 포트 **7021**

---

## 1. 📋 형이 준 숙제

| 항목 | 내용 |
|------|------|
| **목표** | K-SIGNAL 200회 백테스트를 DB에 저장하고, 브라우저에서 한국어로 보기 |
| **UI** | 뇌별 **10장 pool** + **5장 몰아주기** 표시 |
| **금지** | coordinator wire · predict_statistical 동결 경로 수정 · 미래 회차 열람(컨닝) |

---

## 2. 🔧 학생이 한 일

| 항목 | Y/N | 설명 |
|------|-----|------|
| 한국어 라벨 | **Y** | `survey_labels.py` · `REPORT_STYLE.md` · UI JS |
| DB 테이블 | **Y** | `testlotto_backtest_runs` · `testlotto_backtest_draw_results` |
| WF 재실행 적재 | **Y** | `tools/import_k_signal_backtest.py` (JSON에 per-draw 없어 재실행) |
| 10+5 pool API | **Y** | `GET /api/testlotto/predict/pool-view/{회차}` |
| 백테스트 API | **Y** | `GET /api/testlotto/backtest/runs` · `.../runs/{id}` |
| 테스트로또 UI | **Y** | index.html · testlotto.js · testlotto.css |
| coordinator 수정 | **N** | |
| random.choices / _get_draws_before | **N** (동결 유지) | |

---

## 3. 🌐 형이 브라우저에서 보는 방법

1. **앱 주소:** `http://localhost:7021/` (또는 SSOT 포트 7021)
2. 상단 **「테스트로또」** 탭 클릭
3. **회차 선택** → 자동으로 해당 회차 **10장 pool + 5장 몰아주기** 표시 (stat / markov / review 탭)
4. 아래 **「K-SIGNAL 백테스트 기록 (200회 · 펼치기)」** 클릭 → DB 저장된 2건 목록
5. **「회차별」** 버튼 → 1035~1234 각 회차 최고 적중·등수

### API (직접 확인용)

| 경로 | 용도 |
|------|------|
| `/api/testlotto/predict/pool-view/1234` | 10+5 세트 JSON |
| `/api/testlotto/backtest/runs` | 백테스트 실행 목록 |
| `/api/testlotto/backtest/runs/1?draw_limit=200` | REPACK 회차별 |

---

## 4. 📊 DB에 들어간 것 (2026-07-30 적재)

| run_id | 과제 (한국어) | 전략 | 3개 이상 적중률 | 평균 적중 | 등수 r3 | 회차 |
|--------|---------------|------|----------------:|----------:|--------:|------|
| 1 | 번호 몰아주기 빠른 검증(200회) | 신호 몰아주기 | **0.275** | 2.245 | **1** (3등) | 1035~1234 |
| 2 | 신호 선별 빠른 검증(200회) | 통합 선별 | **0.145** | 1.715 | 0 | 1035~1234 |

- per-draw **200행×2** = `testlotto_backtest_draw_results`
- seed=42 · tail-200 · `_get_draws_before` only · learn_as_of 컷오프

---

## 5. ✅ 컨닝(미래 열람) 없음 보증

- 백테스트 import: 매 회차 `set_learn_as_of(draw_no)` + `_get_draws_before(draw_no)` — **당첨 이전 데이터만**
- pool-view API: 동일 WF · coordinator **미배선** · 표시 전용
- **동결 유지:** `random.choices` · `_get_draws_before` · boost 상한 · coordinator wire **형 GO 전 금지**

---

## 6. 📝 다음 (좁은 개선 · 컷/컨닝 없음)

1. **UI+DB 안정 확인** — 형이 7021에서 10+5·백테스트 탭 육안 확인
2. **K-SIGNAL-SELECT-FULL** — 1182회 전체 검증 (QUICK PASS 후 · wire 금지)
3. **200회 복습:** combined ge3=0.145 vs signal_repack top5=0.085 → **5장 공정 기준**으로 좁은 A/B만 (세트번호순 컷 금지)

---

## 7. 📎 파일

| 파일 | 역할 |
|------|------|
| `app/testlotto/models.py` | 테이블 DDL |
| `app/testlotto/survey_labels.py` | 한국어 SSOT |
| `app/testlotto/signal_pool.py` | 10 pool + repack |
| `app/testlotto/backtest_store.py` | DB CRUD |
| `tools/import_k_signal_backtest.py` | WF 적재 |
| `app/testlotto/routes.py` | API 3종 |
| `app/static/index.html` · `testlotto.js` · `testlotto.css` | UI |

*재적재:* `python tools/import_k_signal_backtest.py --which both`
