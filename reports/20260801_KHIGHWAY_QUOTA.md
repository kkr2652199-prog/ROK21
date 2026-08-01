# K-HIGHWAY-QUOTA — referee 동적 5장 배분

📅 2026-08-01 · **PASS** · `coordinator.py` 단독 · 형 GO · **K-HIGHWAY-PHASE1 COMPLETE**

## 목적

고정 쿼터 `{markov:3, stat:1, review:1}` → `get_referee_weights()` 기반 **동적 5장 배분**. K-HIGHWAY-PHASE1 마무리.

## 변경 (`coordinator.py`)

| 항목 | 내용 |
|------|------|
| `dynamic_brain_quota()` | 신규 · referee 가중 비례 · min 1장/뇌 · set_no_asc |
| `_compute_dynamic_quota()` | largest remainder · 합계 5 |
| `apply_markov_wire_quota()` | **alias** → `dynamic_brain_quota` (벤치 호환) |
| `MARKOV_WIRE_ENABLED` | **유지** · False → confidence 상위 5장 |
| `MARKOV_WIRE_BRAIN_QUOTA` | pin 참조용 상수만 보존 (production 미사용) |

### 배분 예 (지시서)

| 가중 | 쿼터 |
|------|------|
| stat 0.40 | **2** |
| markov 0.35 | **2** |
| review 0.25 | **1** |

## K-HIGHWAY-PHASE1 완료 체크

| ID | 내용 | 판정 |
|----|------|------|
| K-HIGHWAY-FEEDBACK | `_auto_feedback` · apply_feedback | **OK** |
| K-HIGHWAY-REFEREE | aux_referee score_set | **OK** |
| K-HIGHWAY-QUOTA | dynamic_brain_quota | **OK** |

## 검증

| 테스트 | 결과 |
|--------|------|
| import `run_coordinated_prediction` | **OK** |
| dynamic 5장 · 3뇌 각 ≥1 | **OK** |
| `_compute_dynamic_quota(0.4/0.35/0.25)` | stat2 markov2 review1 |
| `MARKOV_WIRE_ENABLED=False` | conf top5 **OK** |

## 동결 준수

- `random.choices` · `_get_draws_before` · `BOOST_CAPS` — **미수정**

## 다음

- **형 GO 대기** — K-NEW-ENGINE-MARKOV-A1 등 별도 트랙 · auto-apply 금지
