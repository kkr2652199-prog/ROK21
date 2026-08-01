# K-BRAIN-PACKAGE-PHASE1 — stat_brain 구현 · 동치 검증

날짜 2026-08-01 · 형 GO · WORKSTATE ACTIVE

---

## 1. 실행 요약

| 항목 | 내용 |
|------|------|
| ID | **K-BRAIN-PACKAGE-PHASE1** |
| 목적 | predict_statistical + predict_stat_fairy → stat_brain/engine·learn·aux·predict + shared/db_facts·diversity |
| 동치 | **PASS** — n=200 · draw 1035~1234 · seed=42 |
| 기존 | coordinator 미변경 · predict_stat_fairy/statistical 유지(deprecated 1줄) |

---

## 2. 동치 벤치 (`docs/benchmarks/20260801_KSTAT_BRAIN_EQUIV.json`)

| 지표 | A (predict_stat_fairy) | B (stat_brain.run) | diff | 기준 |
|------|------------------------|---------------------|------|------|
| ge3_rate | 0.15 | 0.15 | **0.0** | < 0.002 |
| mean_match | 1.81 | 1.81 | **0.0** | < 0.01 |
| nums_match_rate | — | — | **1.0** (200/200) | 100% |

**verdict: PASS**

---

## 3. 구현 파일

### shared/
- `db_facts.py` — get_number_freq · get_pair_freq · get_gap_map · get_carry_candidates
- `diversity.py` — pick · factor (set_diversity 래핑)

### stat_brain/
- `engine.py` — build_weights(L96-223) · generate(L225-302 · random.choices 동결)
- `learn.py` — get_adjustments · apply_learn_boost
- `aux.py` — aux_balance_keeper score_set/describe 래핑
- `predict.py` — run() = predict_stat_fairy.predict_sets 동치 경로

### tools/
- `_k_stat_brain_equiv_check.py` — A/B walk-forward 동치 검증

### deprecated (1줄만)
- `predict_stat_fairy.py` · `predict_statistical.py`

---

## 4. 금지 항목 준수

| 금지 | 상태 |
|------|------|
| coordinator 수정 | ✅ 미변경 |
| predict_stat_fairy/statistical 삭제 | ✅ 유지 |
| random.choices 수정 | ✅ verbatim 복사 |
| _get_draws_before 변경 | ✅ 미접촉 |
| boost cap 변경 | ✅ 미접촉 |

---

## 5. 다음 단계

**K-BRAIN-PACKAGE-PHASE2** — markov_brain 구현 · predict_flow_shaman 동치 n=200

---

## 6. 관련 문서

- `reports/20260801_KBRAIN_PACKAGE_PHASE0.md`
- `reports/20260801_KBRAIN_PACKAGE_C_PROPOSAL.md`
