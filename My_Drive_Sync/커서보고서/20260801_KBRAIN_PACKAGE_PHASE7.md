# K-BRAIN-PACKAGE-PHASE7 — shared/referee + coordinator aux 1:1 · 성능 벤치

날짜 2026-08-01 · 형 GO · WORKSTATE ACTIVE

---

## 1. 실행 요약

| 항목 | 내용 |
|------|------|
| ID | **K-BRAIN-PACKAGE-PHASE7** |
| 목적 | coordinator aux 4×0.25 전역 → 뇌별 전용 aux 1:1 + shared.referee notes |
| 판정 | **PASS** — ge3 후퇴 없음 (0.125 ≥ 0.125) |
| AUX_1TO1_ENABLED 확정 | **True** |
| hint_weight | **0.15** (PHASE5 유지 · 고정) |
| learn_wired | **True** (PHASE6 유지 · 고정) |
| V2 pin 참조 | ge3=0.1447 (이상 목표 · PASS 기준 아님) |

---

## 2. 성능 벤치 (`docs/benchmarks/20260801_KPHASE7_AUX_1TO1_BENCH.json`)

경로: coordinator 전체 (3뇌 pool + aux scoring + wire quota)  
n=200 · draw 1035~1234 · seed=42 · HINT_WEIGHT=0.15 · LEARN_WIRED=True

| 지표 | A (4×0.25 global) | B (1:1 dedicated) | diff | 기준 |
|------|-------------------|-------------------|------|------|
| ge3_rate | **0.125** (25/200) | **0.125** (25/200) | **0.0** | ge3_B ≥ ge3_A |
| mean_match | **1.695** | **1.695** | **0.0** | (참고) |

**verdict: PASS** — ge3·mean 동일 · 후퇴 없음

참조: PHASE6 baseline ge3=0.125 (4 aux global + learn wired)

---

## 3. 변경 파일 목록

| 파일 | 변경 |
|------|------|
| `app/testlotto/brains/shared/referee.py` | aux_referee 래핑 — get_brain_weights · score_set · describe |
| `app/testlotto/brains/coordinator.py` | `AUX_1TO1_ENABLED=True` · `_aux_composite_score` · `_aux_notes` |
| `tools/_k_phase7_aux_1to1_bench.py` | A/B walk-forward 성능 벤치 |

---

## 4. aux 1:1 매핑 (C proposal)

| 예측뇌 | 전용 aux | coordinator scoring |
|--------|----------|---------------------|
| stat | stat_brain.aux (balance) | 단일 score |
| markov | markov_brain.aux (pattern) | 단일 score |
| review | review_brain.aux (miss) | 단일 score |
| (공용) | shared.referee | notes only · brain_w via get_referee_weights |

final_conf 공식 유지: `min(99.5, base * 0.5 * brain_w + aux_score * 40 + base * 0.1)`

---

## 5. 금지 항목 준수

| 금지 | 상태 |
|------|------|
| random.choices 수정 | ✅ 미변경 |
| apply_markov_wire_quota 수정 | ✅ 미변경 |
| PREDICT_MODULES 수정 | ✅ 미변경 |
| MARKOV_WIRE_BRAIN_QUOTA 수정 | ✅ 미변경 |
| DB writes in bench | ✅ READ-ONLY |
| FAIL 시 revert | ✅ 해당 없음 (PASS) |

---

## 6. C package core 완료

| Phase | 내용 | 판정 |
|-------|------|------|
| PHASE0 | 스켈레톤 | OK |
| PHASE1 | stat_brain | PASS |
| PHASE2 | markov_brain | PASS |
| PHASE3 | review_brain | PASS |
| PHASE4 | coordinator 3뇌 배선 | PASS |
| PHASE5 | aux hint re-rank | PASS |
| PHASE6 | markov learn wired | PASS |
| **PHASE7** | **aux 1:1 + referee** | **PASS** |

---

## 7. 다음 단계

**K-BRAIN-PACKAGE-COMPLETE** — C package core done · 형 지시 대기 (wire/repack)

---

HEAD: (commit 후 갱신)  
벤치 JSON: `docs/benchmarks/20260801_KPHASE7_AUX_1TO1_BENCH.json`
