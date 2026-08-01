# K-BRAIN-TUNE-SURVEY — hint / look_back / wire FULL n=1182 sweep (READ-ONLY)

📅 2026-08-01 · **SURVEY OK** · coordinator **미수정** · `db_code_write=false` · auto-apply **금지**

## 질문

C package production stack(FULL ge3=0.1015 FAIL)에서 **wire · look_back · hint_weight** 단일축 튜닝으로 live_baseline ge3≥**0.1218** 달성 가능한가?

근거: `docs/benchmarks/20260801_KBRAIN_TUNE_SURVEY.json`

---

## SUMMARY

| sweep | best | ge3_rate | ge3_count | p vs null | vs baseline 0.1015 | vs live 0.1218 |
|-------|------|----------|-----------|-----------|-------------------|----------------|
| **P0 wire** | **aux_hint_top5** | **0.1091** | 129 | 0.702 | +0.0076 | −0.0127 |
| **P1 look_back** | **120** | **0.1058** | 125 | 0.817 | +0.0043 | −0.0160 |
| **P2 hint_weight** | **0.0** | **0.1058** | 125 | 0.817 | +0.0043 | −0.0160 |
| **best_combo** | aux_hint_top5 + lb120 + hint0.0 | **0.1032** | 122 | 0.882 | +0.0017 | −0.0186 |

| gate | 결과 |
|------|------|
| PASS target ge3≥0.1218 | **FAIL** (best_combo 0.1032) |
| p<0.05 vs null (0.1137) | **FAIL** (all sweeps) |
| APPLY recommendation | **HOLD** — production stack 유지 |

---

## P0 wire sweep (look_back=52, hint=0.15)

| strategy | ge3_rate | ge3_count | mean_match | p vs null | Δge3 vs set_no_asc |
|----------|----------|-----------|------------|-----------|-------------------|
| set_no_asc (baseline) | 0.1041 | 123 | 1.685 | 0.863 | — |
| conf_top5 | 0.1083 | 128 | 1.668 | 0.734 | +0.0042 |
| **aux_hint_top5** | **0.1091** | **129** | 1.677 | 0.702 | **+0.0050** |
| conf_quota | 0.1049 | 124 | 1.655 | 0.841 | +0.0008 |

**P0 best:** `aux_hint_top5` — global top 5 by aux_hint_score after enrich.

---

## P1 look_back sweep (wire=set_no_asc, hint=0.15)

| look_back | overall ge3 | ge3_count | early ge3 | mid ge3 | late ge3 |
|-----------|-------------|-----------|-----------|---------|----------|
| 30 | 0.0888 | 105 | 0.0886 | 0.0914 | 0.0865 |
| 52 | 0.1041 | 123 | 0.0987 | 0.1168 | 0.0967 |
| 80 | 0.0905 | 107 | 0.0911 | 0.0914 | 0.0891 |
| **120** | **0.1058** | **125** | 0.0886 | **0.1168** | **0.1120** |
| 200 | 0.1015 | 120 | 0.0658 | 0.1294 | 0.1094 |

**P1 best:** `look_back=120` — mid period 0.1168, late 0.1120.

---

## P2 hint_weight sweep (wire=set_no_asc, look_back=52)

| hint_weight | ge3_rate | ge3_count | mean_match | p vs null |
|-------------|----------|-----------|------------|-----------|
| **0.0** | **0.1058** | **125** | 1.675 | 0.817 |
| 0.05 | 0.1041 | 123 | 1.674 | 0.863 |
| 0.10 | 0.1041 | 123 | 1.682 | 0.863 |
| 0.15 (prod) | 0.1041 | 123 | 1.685 | 0.863 |
| 0.20 | 0.1049 | 124 | 1.684 | 0.841 |
| 0.30 | 0.1049 | 124 | 1.685 | 0.841 |

**P2 best:** `hint_weight=0.0` — hint OFF가 미세 우세(+0.0017 vs 0.15).

---

## best_combo

| param | value | single-axis ge3 |
|-------|-------|-----------------|
| wire | aux_hint_top5 | 0.1091 |
| look_back | 120 | 0.1058 |
| hint_weight | 0.0 | 0.1058 |

| metric | best_combo | note |
|--------|------------|------|
| overall ge3 | **0.1032** | single-axis 합 < 각 축 best (interaction negative) |
| ge3_count | 122/1182 | |
| by_period mid | 0.1244 | promising but early collapse |
| by_period early | 0.0937 | weak |
| p vs null | 0.882 | FAIL |

**선정_근거:** 각 축 ge3_rate 최대 (동률 시 p_value 낮은 쪽).

---

## APPLY summary (K-BRAIN-TUNE-APPLY)

| item | recommendation |
|------|----------------|
| action | **HOLD** |
| wire | set_no_asc 유지 (aux_hint_top5 +0.0050 but p FAIL · combo collapse) |
| look_back | 52 유지 (120 marginal +0.0017 on set_no_asc only) |
| hint_weight | 0.15 유지 (0.0 diff +0.0017 · not significant) |
| 형 GO 필요? | tune APPLY **비권고** — live_baseline 0.1218 미달 · p FAIL |
| auto_apply | **금지** |

형이 명시 GO 시 K-BRAIN-TUNE-APPLY에서 aux_hint_top5 wire A/B만 단독 검증 권고 (combo negative interaction).

---

## 전제

| 항목 | 값 |
|------|-----|
| n_eval | 1182 · draw 53~1234 · seed=42 |
| path | coordinator FULL (3brain → aux scoring → in-tool wire/params) |
| LEARN_WIRED | True · AUX_1TO1_ENABLED=True |
| look_back slice | draws[-look_back:] · skip if len<look_back |
| 도구 | `tools/_k_brain_tune_survey.py` |
| 금지 | app/ 변경 · coordinator 수정 · DB write · auto-apply |

---

## Verdict

| gate | 결과 |
|------|------|
| survey PASS | **OK** — P0/P1/P2 + best_combo 완료 |
| tune promising | **NO** — best_combo ge3=0.1032 < live_baseline 0.1218 |
| next | **K-BRAIN-TUNE-APPLY** — **형 GO 대기** (HOLD 권고) |
