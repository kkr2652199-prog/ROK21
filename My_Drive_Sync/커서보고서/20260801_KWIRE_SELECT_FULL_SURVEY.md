# K-WIRE-SELECT-FULL-SURVEY — wire strategy FULL n=1182 재검증 (READ-ONLY)

📅 2026-08-01 · **SURVEY OK** · coordinator **미수정** · `db_code_write=false`

## 질문

K-QUOTA-GAP-SURVEY(QUICK n=200)에서 conf_global_top5·aux_hint_quota가 set_no_asc를 상회했으나, **FULL n=1182**에서도 유지되는가?  
wire GO 판단 선행 조건 — coordinator 패치 **전** 재검증.

근거: `docs/benchmarks/20260801_KWIRE_SELECT_FULL_survey.json`

---

## SUMMARY

### QUICK(n=200) vs FULL(n=1182) — top strategies

| strategy | QUICK ge3 | FULL ge3 | Δ(FULL−QUICK) | collapse? | FULL p vs null | FULL verdict |
|----------|-----------|----------|---------------|-----------|----------------|--------------|
| **set_no_asc (baseline)** | 0.125 | **0.1015** | −0.0235 | **YES** | 0.916 | FAIL |
| conf_quota | 0.125 | 0.1117 | −0.0133 | YES | 0.600 | FAIL |
| **conf_global_top5** | **0.135** | **0.1117** | **−0.0233** | **YES** | 0.600 | FAIL |
| **aux_hint_quota** | 0.130 | **0.1134** | −0.0166 | YES | 0.528 | FAIL |
| oracle_best15 (ref) | 0.290 | 0.2809 | −0.0091 | YES | 0.000 | PASS |

| 지표 | FULL 값 | QUICK 값 | 비고 |
|------|---------|----------|------|
| **quota_gap_rate** | **0.431** (510/1182) | 0.430 (86/200) | arch note 0.436과 근접 · 안정 |
| n_eval | **1182** | 200 | draw 53~1234 · seed=42 |
| live_baseline ge3 | — | — | ref **0.1218** (K-SIGNAL-SELECT-FULL) |
| v2_pin ge3 | — | — | ref **0.1447** |

---

## FULL ge3 상세

| strategy | ge3_rate | ge3_count | mean_match | Δge3 vs set_no_asc | Δge3 vs null | Δge3 vs pin |
|----------|----------|-----------|------------|-------------------|--------------|-------------|
| set_no_asc | 0.1015 | 120 | 1.692 | — | −0.0122 | −0.0432 |
| conf_quota | 0.1117 | 132 | 1.677 | +0.0102 | −0.0020 | −0.0330 |
| conf_global_top5 | 0.1117 | 132 | 1.645 | +0.0102 | −0.0020 | −0.0330 |
| aux_hint_quota | 0.1134 | 134 | 1.680 | +0.0119 | −0.0003 | −0.0313 |
| oracle_best15 | 0.2809 | 332 | 2.217 | +0.1794 | +0.1672 | +0.1362 |

---

## 전제

| 항목 | 값 |
|------|-----|
| path | coordinator FULL (3brain pool → aux scoring → wire alt) |
| HINT_WEIGHT | 0.15 |
| LEARN_WIRED | True |
| AUX_1TO1_ENABLED | True |
| quota | markov×3 + stat×1 + review×1 |
| 도구 | `tools/_k_wire_select_full_survey.py` |
| 금지 | coordinator.py 변경 · auto-wire · DB write |

---

## PASS criterion (wire GO)

| criterion | conf_global_top5 | result |
|-----------|------------------|--------|
| ge3 > set_no_asc (FULL) | 0.1117 > 0.1015 | **PASS** |
| ge3 > live_baseline 0.1218 (optional) | 0.1117 < 0.1218 | **FAIL** |
| p < 0.05 vs null (0.1137) | p=0.600 | **FAIL** |
| QUICK→FULL collapse | 0.135→0.1117 (−2.33%p) | **COLLAPSE** |
| **wire_pass (combined)** | — | **FAIL** |

---

## Verdict

| gate | 결과 |
|------|------|
| wire GO recommendation | **wait** — baseline 상회하나 p·live_baseline·collapse 미충족 |
| auto-wire | **금지** — survey only · coordinator **미패치** |
| 형 GO 필요? | wire 변경 시에도 FULL FAIL — **HOLD 권고** · 형 명시 GO 시에만 A/B |

**권고:** **HOLD wire** — QUICK 0.135→FULL 0.1117 붕괴 패턴(K-10SET-DET-LAB-FULL 0.145→0.1218 등)과 동일.  
conf_global_top5·aux_hint_quota가 set_no_asc 대비 +1.0~1.2%p 상회하나 **통계·절대 ge3 모두 미달**.  
quota_gap 43.1%는 FULL에서도 유지 → 선택 레버 여지는 있으나 wire 교체 근거 불충분.

---

## 다음

| ID | 조건 |
|----|------|
| **K-WIRE-SELECT-GO-WAIT** | 형 GO → conf_global_top5 wire A/B (현재 FAIL 근거로 **HOLD 권고**) |
| **K-ATTACK-HOLD** | wire 유지 · set_no_asc production |

---

## 산출물

- `tools/_k_wire_select_full_survey.py`
- `docs/benchmarks/20260801_KWIRE_SELECT_FULL_survey.json`
