# K-QUOTA-GAP-SURVEY — set_no_asc vs conf vs aux_hint wire 대안 (READ-ONLY)

📅 2026-08-01 · **SURVEY OK** · coordinator **미수정** · `db_code_write=false`

## 질문

C package production stack(coordinator FULL · hint=0.15 · LEARN_WIRED · AUX_1TO1)에서 **발권 선택 전략**을 바꾸면 ge3가 오르는가?  
쿼터(markov3+stat1+review1)는 고정 · selection 함수만 survey tool에서 비교.

근거: `docs/benchmarks/20260801_KQUOTA_GAP_survey.json`

---

## SUMMARY

| strategy | ge3_rate | ge3_count | mean_match | Δge3 vs set_no_asc | Δge3 vs V2 pin | wire? |
|----------|----------|-----------|------------|-------------------|----------------|-------|
| **set_no_asc (baseline)** | **0.125** | 25 | 1.695 | — | −0.0197 | **production** |
| conf_quota | 0.125 | 25 | 1.680 | 0.000 | −0.0197 | no lift |
| **conf_global_top5** | **0.135** | 27 | 1.645 | **+0.010** | −0.0097 | **beats baseline** |
| **aux_hint_quota** | **0.130** | 26 | 1.710 | **+0.005** | −0.0147 | **beats baseline** |
| oracle_best15 (ref) | 0.290 | 58 | 2.220 | +0.165 | +0.1453 | ceiling only |

| 지표 | 값 | 비고 |
|------|-----|------|
| **quota_gap_rate** | **0.430** (86/200) | oracle_best15 > set_no_asc selected best |
| arch note ref | 0.436 (516/1182) | K-BENCH-01 FULL · 본 survey n=200 |
| v2_pin_ge3 | **0.1447** | stored WIRE-V2 pin |
| n_eval | **200** | draw 1035~1234 · seed=42 |

---

## 전제

| 항목 | 값 |
|------|-----|
| path | coordinator FULL (3brain pool → aux scoring → wire alt) |
| HINT_WEIGHT | 0.15 |
| LEARN_WIRED | True |
| AUX_1TO1_ENABLED | True |
| quota | markov×3 + stat×1 + review×1 |
| 도구 | `tools/_k_quota_gap_survey.py` |
| 금지 | coordinator.py 변경 · MARKOV_WIRE_* 변경 · random.choices · DB write |

---

## 전략 정의

| ID | 선택 규칙 |
|----|-----------|
| set_no_asc | `apply_markov_wire_quota` 복제 — pred_set_no 오름차순 쿼터 (production) |
| conf_quota | 쿼터 유지 · 뇌 내 **confidence desc** (post aux scoring) |
| conf_global_top5 | 15장 풀 **confidence desc top 5** (쿼터 무시) |
| aux_hint_quota | 쿼터 유지 · 뇌 내 **aux_hint_score desc** (없으면 confidence fallback) |
| oracle_best15 | 15장 중 max matched (reference · wire 후보 아님) |

---

## quota_gap 분석

- **86/200 (43.0%)** 회차에서 15장 best matched > set_no_asc 선택 5장 best matched
- architecture note **43.6%** (K-BENCH-01 · n=1182)와 **근접** — n=200 구간에서도 동일 패턴 확인
- oracle ge3=**0.290** vs set_no_asc **0.125** → 선택 레버 여지 **+16.5%p** (천장 참고)

---

## Verdict

| gate | 결과 |
|------|------|
| any wire candidate ge3 > set_no_asc? | **YES** — conf_global_top5 (+0.01) · aux_hint_quota (+0.005) |
| any beats V2 pin 0.1447? | **NO** — best conf_global_top5=0.135 still −0.0097 |
| conf_quota (쿼터+conf) | **동률** 0.125 — set_no_asc와 ge3·count 동일 |
| auto-wire | **금지** — survey only |

**권고:** **K-WIRE-SELECT-GO-WAIT** — conf_global_top5·aux_hint_quota가 baseline 상회. 형 GO 전 coordinator **미패치**.  
V2 pin 미회복 → wire 변경 시에도 FULL n=1182 재검증 필요.

---

## 다음 후보

| ID | 조건 |
|----|------|
| **K-WIRE-SELECT-GO-WAIT** | 형 GO → conf_global_top5 또는 aux_hint_quota wire A/B |
| **K-BACKTEST-FULL-C** | C stack FULL n=1182 (wire 변경 전/후) |

---

## 산출물

- `tools/_k_quota_gap_survey.py`
- `docs/benchmarks/20260801_KQUOTA_GAP_survey.json`
