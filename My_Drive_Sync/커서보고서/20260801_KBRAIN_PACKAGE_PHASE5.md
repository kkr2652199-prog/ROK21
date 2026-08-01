# K-BRAIN-PACKAGE-PHASE5 — aux 1:1 hint 주입 · 성능 벤치

날짜 2026-08-01 · 형 GO · WORKSTATE ACTIVE

---

## 1. 실행 요약

| 항목 | 내용 |
|------|------|
| ID | **K-BRAIN-PACKAGE-PHASE5** |
| 목적 | 각 뇌 predict.py에서 engine.generate 후 전용 aux hint re-rank 주입 |
| 판정 | **PASS** — ge3 후퇴 없음 (0.125 ≥ 0.115) |
| hint_weight 확정 | **0.15** |
| V2 pin 참조 | ge3=0.1447 (이상 목표 · PASS 기준 아님) |

---

## 2. 성능 벤치 (`docs/benchmarks/20260801_KPHASE5_AUX_HINT_BENCH.json`)

경로: coordinator 전체 (3뇌 pool + aux scoring + wire quota)  
n=200 · draw 1035~1234 · seed=42

| 지표 | A (hint=0) | B (hint=0.15) | diff | 기준 |
|------|------------|---------------|------|------|
| ge3_rate | **0.115** (23/200) | **0.125** (25/200) | **+0.010** | ge3_B ≥ ge3_A |
| mean_match | **1.75** | **1.77** | **+0.02** | (참고) |

**verdict: PASS** — 재시도(0.10) 불필요

---

## 3. 변경 파일 목록

| 파일 | 변경 |
|------|------|
| `app/testlotto/brains/shared/aux_hint.py` | **신규** — `rerank_by_aux` |
| `app/testlotto/brains/stat_brain/predict.py` | balance_keeper hint · `HINT_WEIGHT=0.15` |
| `app/testlotto/brains/markov_brain/predict.py` | pattern_spotlight hint · `HINT_WEIGHT=0.15` |
| `app/testlotto/brains/review_brain/predict.py` | miss_detective hint · `HINT_WEIGHT=0.15` |
| `tools/_k_phase5_aux_hint_bench.py` | A/B walk-forward 벤치 |

---

## 4. 금지 항목 준수

| 금지 | 상태 |
|------|------|
| random.choices 수정 | ✅ 미변경 |
| confidence 직접 수정 | ✅ 미변경 (aux_hint_score만 추가) |
| coordinator _apply_aux_scoring | ✅ 미변경 |
| AUX_MODULES / AUX_WEIGHTS | ✅ 미변경 |
| ge3 후퇴 시 revert | ✅ 해당 없음 (PASS) |
| PHASE6 자동 착수 | ✅ 미실행 |

---

## 5. 다음 단계

**K-BRAIN-PACKAGE-PHASE6** — markov learn_state 실제 소비 배선 (형 GO 대기)

---

HEAD: (commit 후 갱신)  
벤치 JSON: `docs/benchmarks/20260801_KPHASE5_AUX_HINT_BENCH.json`
