# K-BRAIN-PACKAGE-PHASE6 — markov learn_state 배선 · 성능 벤치

날짜 2026-08-01 · 형 GO · WORKSTATE ACTIVE

---

## 1. 실행 요약

| 항목 | 내용 |
|------|------|
| ID | **K-BRAIN-PACKAGE-PHASE6** |
| 목적 | markov_brain learn_state 실제 소비 — visit_count boost (feedback 후 · top_candidates 전) |
| 판정 | **PASS** — ge3 후퇴 없음 (0.125 ≥ 0.125) |
| LEARN_WIRED 확정 | **True** |
| hint_weight | **0.15** (PHASE5 유지 · 고정) |
| V2 pin 참조 | ge3=0.1447 (이상 목표 · PASS 기준 아님) |

---

## 2. 성능 벤치 (`docs/benchmarks/20260801_KPHASE6_MARKOV_LEARN_BENCH.json`)

경로: coordinator 전체 (3뇌 pool + aux scoring + wire quota)  
n=200 · draw 1035~1234 · seed=42 · HINT_WEIGHT=0.15 고정

| 지표 | A (LEARN_WIRED=False) | B (LEARN_WIRED=True) | diff | 기준 |
|------|----------------------|----------------------|------|------|
| ge3_rate | **0.125** (25/200) | **0.125** (25/200) | **0.0** | ge3_B ≥ ge3_A |
| mean_match | **1.77** | **1.695** | **-0.075** | (참고) |

**verdict: PASS** — ge3 동률 · mean 소폭 하락이나 PASS 기준(ge3) 충족

참조: PHASE5 baseline ge3=0.115 (hint=0) · PHASE5 hint ge3=0.125 (hint=0.15)

---

## 3. 변경 파일 목록

| 파일 | 변경 |
|------|------|
| `app/testlotto/brains/markov_brain/learn.py` | `apply_learn_boost` · `LEARN_WIRED=True` |
| `app/testlotto/brains/markov_brain/engine.py` | feedback 후 learn boost 배선 |
| `app/testlotto/brains/markov_brain/predict.py` | reasoning learn_note 추가 (confidence 미변경) |
| `tools/_k_phase6_markov_learn_bench.py` | A/B walk-forward 성능 벤치 |

---

## 4. apply_learn_boost 로직

| boost | 조건 | 대상 |
|-------|------|------|
| overdue | gap≥30 · adj>0 | visit_count[n] × (1+overdue_b) |
| ending | miss_counts.ending_digit>0 · adj>0 | prev_endings 끝수 일치 번호 |
| carry | adj>0 | prev_nums 6개 |
| pair | miss_counts.pair>0 · adj>0 | build_pair_freq top20 쌍 번호 |

BOOST_CAPS 준수: carry=0.2 · ending=0.3 · overdue=0.2 · pair=0.5

---

## 5. 금지 항목 준수

| 금지 | 상태 |
|------|------|
| random.choices 수정 | ✅ 미변경 |
| coordinator.py 수정 | ✅ 미변경 |
| predict_markov.py 수정 | ✅ 미변경 |
| boost cap 변경 | ✅ 미변경 |
| DB writes in bench | ✅ READ-ONLY |
| FAIL 시 revert | ✅ 해당 없음 (PASS) |

---

## 6. 직전 K-MARKOV-LEARN-SURVEY 대비

| 항목 | SURVEY (FAIL) | PHASE6 (PASS) |
|------|---------------|---------------|
| 배선 위치 | predict_flow_shaman | markov_brain/engine.generate |
| ge3 wired | 0.105 | 0.125 |
| 판정 | FAIL · 롤백 | PASS · LEARN_WIRED=True |

---

## 7. 다음 단계

**K-BRAIN-PACKAGE-PHASE7** — shared/referee + coordinator aux 1:1 (C proposal PHASE4 next step)

---

HEAD: (commit 후 갱신)  
벤치 JSON: `docs/benchmarks/20260801_KPHASE6_MARKOV_LEARN_BENCH.json`
