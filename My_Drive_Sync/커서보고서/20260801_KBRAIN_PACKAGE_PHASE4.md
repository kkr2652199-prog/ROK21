# K-BRAIN-PACKAGE-PHASE4 — coordinator 3뇌 패키지 배선 · 동치 검증

날짜 2026-08-01 · 형 GO · WORKSTATE ACTIVE

---

## 1. 실행 요약

| 항목 | 내용 |
|------|------|
| ID | **K-BRAIN-PACKAGE-PHASE4** |
| 목적 | coordinator PREDICT_MODULES → stat/markov/review_brain 패키지 배선 |
| 동치 | **PASS** — n=200 · draw 1035~1234 · seed=42 · 3뇌 전부 |
| 변경 | coordinator imports + PREDICT_MODULES 값만 · predict_sets 어댑터 3건 |

---

## 2. 동치 벤치 (`docs/benchmarks/20260801_KCOORDINATOR_PHASE4_EQUIV.json`)

### stat

| 지표 | A (predict_stat_fairy) | B (stat_brain.run) | diff | 기준 |
|------|------------------------|----------------------|------|------|
| ge3_rate | 0.15 | 0.15 | **0.0** | < 0.002 |
| mean_match | 1.81 | 1.81 | **0.0** | < 0.01 |
| nums_match_rate | — | — | **1.0** (200/200) | 100% |

### markov

| 지표 | A (predict_flow_shaman) | B (markov_brain.run) | diff | 기준 |
|------|-------------------------|----------------------|------|------|
| ge3_rate | 0.08 | 0.08 | **0.0** | < 0.002 |
| mean_match | 1.645 | 1.645 | **0.0** | < 0.01 |
| nums_match_rate | — | — | **1.0** (200/200) | 100% |

### review

| 지표 | A (predict_review_king) | B (review_brain.run) | diff | 기준 |
|------|-------------------------|----------------------|------|------|
| ge3_rate | 0.10 | 0.10 | **0.0** | < 0.002 |
| mean_match | 1.655 | 1.655 | **0.0** | < 0.01 |
| nums_match_rate | — | — | **1.0** (200/200) | 100% |

**verdict: PASS (3/3)**

---

## 3. 구현 파일

### coordinator.py (MINIMAL)
- deprecated import 유지 (`# deprecated — PHASE4`)
- `PREDICT_MODULES` → stat_brain_predict / markov_brain_predict / review_brain_predict
- apply_markov_wire_quota · AUX · run_coordinated_prediction 로직 **미변경**

### brain predict.py (어댑터)
- `stat_brain/predict.py` — `predict_sets = run`
- `markov_brain/predict.py` — `predict_sets = run`
- `review_brain/predict.py` — `predict_sets = run`

### tools/
- `_k_coordinator_phase4_equiv_check.py` — 3뇌 A/B walk-forward 동치 검증

---

## 4. 금지 항목 준수

| 금지 | 상태 |
|------|------|
| apply_markov_wire_quota 변경 | ✅ 미변경 |
| _apply_aux_scoring 변경 | ✅ 미변경 |
| AUX_MODULES/AUX_WEIGHTS 변경 | ✅ 미변경 |
| MARKOV_WIRE_BRAIN_QUOTA 변경 | ✅ 미변경 |
| deprecated import 삭제 | ✅ 유지 |
| PHASE5 자동 시작 | ✅ 미실행 |

---

## 5. 다음 단계

**K-BRAIN-PACKAGE-PHASE5** — (형 지시 대기)

---

## 6. 관련 문서

- `reports/20260801_KBRAIN_PACKAGE_PHASE3.md`
- `reports/20260801_KBRAIN_PACKAGE_C_PROPOSAL.md`
