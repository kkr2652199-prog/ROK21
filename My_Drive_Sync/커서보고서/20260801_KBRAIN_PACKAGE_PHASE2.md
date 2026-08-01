# K-BRAIN-PACKAGE-PHASE2 — markov_brain 구현 · 동치 검증

날짜 2026-08-01 · 형 GO · WORKSTATE ACTIVE

---

## 1. 실행 요약

| 항목 | 내용 |
|------|------|
| ID | **K-BRAIN-PACKAGE-PHASE2** |
| 목적 | predict_markov + predict_flow_shaman → markov_brain/engine·learn·aux·predict |
| 동치 | **PASS** — n=200 · draw 1035~1234 · seed=42 |
| 기존 | coordinator 미변경 · predict_markov/predict_flow_shaman 유지(deprecated 1줄) |

---

## 2. 동치 벤치 (`docs/benchmarks/20260801_KMARKOV_BRAIN_EQUIV.json`)

| 지표 | A (predict_flow_shaman) | B (markov_brain.run) | diff | 기준 |
|------|-------------------------|----------------------|------|------|
| ge3_rate | 0.08 | 0.08 | **0.0** | < 0.002 |
| mean_match | 1.645 | 1.645 | **0.0** | < 0.01 |
| nums_match_rate | — | — | **1.0** (200/200) | 100% |

**verdict: PASS**

---

## 3. 구현 파일

### markov_brain/
- `engine.py` — build_transition_matrix · markov_random_walk · get_markov_prob_vector · generate(_markov_predict verbatim · steps=80)
- `learn.py` — get_adjustments() (learn_state('markov') · engine 미배선 — shaman 동치)
- `aux.py` — aux_pattern_spotlight score_set/describe 래핑
- `predict.py` — run() = predict_flow_shaman.predict_sets 동치 경로

### tools/
- `_k_markov_brain_equiv_check.py` — A/B walk-forward 동치 검증

### deprecated (1줄만)
- `predict_markov.py` · `predict_flow_shaman.py`

---

## 4. 금지 항목 준수

| 금지 | 상태 |
|------|------|
| coordinator 수정 | ✅ 미변경 |
| predict_markov/predict_flow_shaman 삭제 | ✅ 유지 |
| random.choices 수정 | ✅ verbatim 복사 |
| _get_draws_before 변경 | ✅ 미접촉 |
| boost cap 변경 | ✅ 미접촉 |
| learn_state engine 배선 | ✅ 미배선 (shaman 동치) |

---

## 5. 다음 단계

**K-BRAIN-PACKAGE-PHASE3** — review_brain 구현 · predict_review_king 동치 n=200

---

## 6. 관련 문서

- `reports/20260801_KBRAIN_PACKAGE_PHASE1.md`
- `reports/20260801_KBRAIN_PACKAGE_C_PROPOSAL.md`
