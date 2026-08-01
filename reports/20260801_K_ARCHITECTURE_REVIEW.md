# K-ARCHITECTURE-REVIEW — 학습·3뇌·V2 pin READ-ONLY 감사

날짜 2026-08-01 · **코드 수정 없음** · coordinator·predict_* 미수정 · DB READ-ONLY  
HEAD `dbae16b` · SSOT `D:\ROK21` · 포트 7021

---

## Executive Summary

| 질문 | 한줄 결론 |
|------|-----------|
| Q1 학습 작동 | **부분 작동** — stat·walkforward 피드백·referee 갱신은 동작. **markov learn_state 미소비**, review는 carry만 소비, referee 분산≈0 |
| Q2 3뇌 다양성 | **서로 다른 번호** — set 단위 cross-brain Jaccard ≈0.086 (K-BENCH 감사 0.11대와 동급) |
| Q3 V2 pin 0.1447 | **FULL n=1182 stored verify** (`20260729_KMARKOV_WIRE_V2_verify.json`) · commit `3b0f619` · tail-200 ge3=**0.165**로 pin보다 높음 → **구간 artifact 가능** |

---

## Q1. 학습이 실제로 작동하는가?

### K-F — markov · learn_state 소비

| 구분 | 내용 |
|------|------|
| **사실** | `app/testlotto/brains/predict_flow_shaman.py` → `_markov_predict`만 호출. `load_learn_state` / `learn_state` **grep 0건** |
| **사실** | `app/testlotto/predict_markov.py`에도 learn_state 참조 **없음** |
| **사실** | DB `testlotto_brain_learn_state` markov 행 존재 · `review_count=2065` · adjustments 전부 cap 도달 |
| **사실** | `walkforward.py` L117~118 → markov에도 `apply_feedback` **기록은 됨** |
| **판정** | **미작동(소비)** — 피드백 저장만 되고 markov 예측 경로에서 **읽지 않음** |

### K-G — ending_boost 현재값

| 구분 | 내용 |
|------|------|
| **사실** | `learn_state.py` DEFAULT `ending_digit_boost=0.0` · BOOST_CAPS 상한 **0.3** |
| **사실** | DB global(2026-08-01 실측): stat/markov/review 모두 `ending_digit_boost=**0.3**` → **0.0 아님** |
| **사실** | stat: `predict_statistical.py` L199~207 — `ending_b>0` **且** `miss_counts.ending_digit>0`일 때만 weights 적용. stat `miss_counts.ending_digit=**252**` → **적용 조건 충족** |
| **사실** | review: `predict_review_king.py` — `carry_over_boost`만 사용 · `neutralize_ending_digit_mass(K-P3)`로 끝수 균등화. **`ending_digit_boost` 미참조** |
| **사실** | markov: predict 경로 learn 미참조 → ending_boost **미소비** |
| **판정** | **질문 전제(0.0) 불일치** — 런타임 DB는 0.3. stat만 실효 적용 · markov/review는 ending_boost **미작동** |

### K-N — apply_feedback · best 기준

| 구분 | 내용 |
|------|------|
| **사실** | `walkforward.py` L94~96: `apply_coordinator_scoring` 후 `_score_sets` → `pick_best_set_index(scored)` |
| **사실** | L117~118: `apply_feedback(tag, draw_no, item["matched"], item["missed"])` — `matched`는 **best 세트**의 `matched_count` |
| **사실** | `learn_state.py` L132~183: miss_counts 누적 → recent≥3 시 boost_key 매핑 → cap 적용 → save |
| **판정** | **작동** — best-of-5 tier 기준 피드백 경로 확인 |

### K-M — get_referee_weights 실효 분산

| 구분 | 내용 |
|------|------|
| **사실** | `learn_state.py` L117~129: `weight = 1.0 + recent_avg_match × 0.15` → 정규화 |
| **사실** | as_of=1235 실측(READ-ONLY python): stat=**0.3351** · markov=**0.3298** · review=**0.3351** · **σ≈0.002529** |
| **사실** | DB global `recent_avg_match`: stat/review **1.6667** · markov **1.5333** (window=30 슬라이딩) |
| **판정** | **작동하나 실효≈균등(1/3)** — 분산 극소 · coordinator `get_referee_weights()` 경유 가중 **체감 무효** |

### Q1 — 학습 미작동·약작동 항목 목록

| ID | 항목 | 상태 |
|----|------|------|
| K-F | markov → learn_state predict 소비 | **미작동** |
| K-G | markov ending_boost 소비 | **미작동** |
| K-G | review ending_boost 소비 | **미작동** (carry만) |
| K-M | referee 가중 분산 | **약작동** (σ≈0.0025) |
| — | stat freq 배선 (carry/ending/overdue) | **작동** |
| — | review carry_boost | **작동** |
| K-N | apply_feedback best 기준 | **작동** |

---

## Q2. 3뇌가 실제로 서로 다른 번호를 내는가?

### 측정 방법 (READ-ONLY)

- 소스: `testlotto_brain_review.predicted_sets_json` (stored WF 예측)
- 구간: draw **1215~1234** (최근 20회 · n=20)
- 뇌: stat · markov · review 각 5세트
- Jaccard: |A∩B| / |A∪B|

### 실측

| 지표 | 값 | n |
|------|-----|---|
| set_no 동일 cross-brain mean Jaccard | **0.0858** | 100 (20×5) |
| 전체 pairwise sets mean Jaccard | **0.0872** | 20 draws |
| 뇌당 5장 union-level mean Jaccard | **0.3439** | 20 draws |

### 참고 (K-BENCH)

| 구분 | 내용 |
|------|------|
| **사실** | `reports/_audit_20260701_cap2_independence.json` — stat/markov/review cross Jaccard **0.112~0.125**대 |
| **사실** | K-BENCH-01 POSTMORTEM의 ge3=**0.11**은 **적중률** 지표이지 Jaccard 아님 (혼동 주의) |
| **판정** | set 단위 Jaccard ≈0.09 → **세 뇌가 사실상 같은 번호를 내지 않음**. union-level ~0.34는 5장 합집합 overlap으로 상대적으로 높으나 여전히 다수 비공유 |

---

## Q3. V2 pin(0.1447)이 어느 구간에서 나왔는가?

### WIRE-V2 적용 시점·설정

| 구분 | 내용 |
|------|------|
| **사실** | git commit **`3b0f619`** `[K-MARKOV-WIRE-V2] set_no 쿼터 PASS · ENABLED=True` · 2026-07-29 04:39 KST |
| **사실** | `coordinator.py` L38~44: `MARKOV_WIRE_BRAIN_QUOTA={markov:3, stat:1, review:1}` · `MARKOV_WIRE_ENABLED=True` |
| **사실** | V2 변경: confidence 정렬 제거 → **set_no/pred_set_no 오름차순** 쿼터 (`apply_markov_wire_quota`) |
| **사실** | V1 대비: v1 confidence 쿼터 ge3=**0.121** FAIL → V2 set_no_asc ge3=**0.1447** PASS (동일 verify JSON) |

### pin SSOT

| 필드 | 값 | 출처 |
|------|-----|------|
| ge3_rate | **0.1447** | `docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json` |
| mean | **1.7504** | 동일 |
| n_eval | **1182** | draw 53~1234 |
| wire_quota | markov3+stat1+review1 | 동일 |
| p_value | **0.000679** | vs null 0.1137 |
| db_code_write | **false** | stored brain_review 재평가만 |

### tail-200 vs 전체-1182

| 구간 | ge3 | mean | 비고 |
|------|-----|------|------|
| **FULL 1182** (pin SSOT) | **0.1447** | 1.7504 | WIRE-V2 verify JSON |
| **tail-200** (1035~1234) | **0.1650** | 1.8450 | 본 READ-ONLY 재측 · stored review + wire quota |
| QUICK tail-200 (survey들) | ≈**0.145** | — | K10SET/COMBO/SELECT survey JSON |
| FULL live WF (최근 survey) | ≈**0.1218** | — | K10SET-DET-LAB-FULL · SELECT-FULL 동일 |

### artifact 판단

| 구분 | 내용 |
|------|------|
| **사실** | pin 0.1447 = **고정 stored 예측 + set_no_asc 쿼터** FULL 구간 산술 |
| **사실** | 동일 파이프라인 tail-200 ge3=**0.165** > pin → **최근 구간이 pin보다 높음** |
| **사실** | live WF FULL survey ge3≈**0.1218** << pin → **재생성·survey 경로와 stored verify 괴리** |
| **미확인** | pin이 특정 draw 서브구간(예: 53~800 vs 800~1234) 단독 기여분 — 이번 턴 구간별 분해 **미실행** |
| **판정** | pin은 **FULL-1182 stored verify artifact**로 고정됨. tail vs full 불일치 + survey collapse → **구간·파이프라인 의존 pin** · 단일 universal baseline으로 쓰기 **위험** |

---

## 미확인 · 한계

1. markov learn_state **의도적 미배선**인지 설계 문서 명시 — **미확인** (코드상 미소비만 확인)
2. pin 구간별(ge3 by decile) 분해 — **미실행**
3. Jaccard 측정이 stored review 기준 — live 재생성 예측과의 차이 — **미확인**

---

## 근거 파일

| 용도 | 경로 |
|------|------|
| pin SSOT | `docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json` |
| coordinator wire | `app/testlotto/brains/coordinator.py` |
| walkforward best | `app/testlotto/walkforward.py` |
| learn_state | `app/testlotto/learn_state.py` |
| stat learn 배선 | `app/testlotto/predict_statistical.py` L179~223 |
| markov predict | `app/testlotto/brains/predict_flow_shaman.py` |
| review predict | `app/testlotto/brains/predict_review_king.py` |
| FULL survey collapse | `docs/benchmarks/20260801_K10SET_DET_LAB_survey_full.json` |

---

## 다음 (형 GO 전 HOLD 유지)

- K-ATTACK-HOLD: wire·survey 중단 · V2 pin 유지
- 본 리뷰는 **진단만** — coordinator·predict_* 패치 **없음**
