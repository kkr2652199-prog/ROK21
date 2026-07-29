# K-REVIEW-TUNE-SURVEY — review carry_mult/decay/window 격자

📅 2026-07-29 · **FAIL** · coordinator **미수정** · `db_code_write=false`

## 요약

live pipeline(3뇌 `predict_sets` 중 markov/stat는 live 재생성 + review는 `review_predict_override`로 carry_mult/decay/window만 런타임 변경)
+ `apply_coordinator_scoring + apply_markov_wire_quota`로 15조합 sequential 격자 walk-forward.
best=carry=2.2|decay=0.8|window=0 ge3=**0.1117** · Δ=**-0.033** · p=**0.600284** → **FAIL** · NEXT=**K-ATTACK-HOLD**.

근거: `docs/benchmarks/20260729_KREVIEW_TUNE_survey.json`

---

## 전제

| 항목 | 값 |
|------|-----|
| n_eval | **1182** (draw 53~1234) |
| wire pin | ge3=**0.1447** · mean=**1.7504** |
| null_ge3 | 0.1137 |
| seed | 42 |
| SETS_PER_PREDICT_BRAIN | 5 (total 15) |
| 쿼터 | markov×3 + stat×1 + review×1 (set_no_asc) |
| pipeline | live predict_sets (markov/stat) + review_predict_override + apply_coordinator_scoring + apply_markov_wire_quota |

---

## STEP1 — carry_mult 격자 (decay=0.85 · window=0 고정)

| carry_mult | mean | ge3_rate | ge4_rate | ge3_count | Δ vs pin | p_value | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 2.2 | 1.6861 | 0.1100 | 0.0025 | 130 | -0.0347 | 0.669622 | FAIL |
| 2.8 | 1.6937 | 0.1049 | 0.0017 | 124 | -0.0398 | 0.840929 | FAIL |
| 1.8 | 1.6895 | 0.1041 | 0.0042 | 123 | -0.0406 | 0.862645 | FAIL |
| 1.2 | 1.6929 | 0.1024 | 0.0042 | 121 | -0.0423 | 0.899894 | FAIL |
| 1.5 | 1.6751 | 0.0964 | 0.0025 | 114 | -0.0483 | 0.974328 | FAIL |

best1: **carry_mult=2.2** (ge3=0.1100)

---

## STEP2 — decay 격자 (carry_mult=2.2 · window=0 고정)

| decay(no_carry_decay) | mean | ge3_rate | ge4_rate | ge3_count | Δ vs pin | p_value | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 0.80 | 1.7107 | 0.1117 | 0.0034 | 132 | -0.0330 | 0.600284 | FAIL |
| 0.85 | 1.6861 | 0.1100 | 0.0025 | 130 | -0.0347 | 0.669622 | FAIL |
| 0.95 | 1.6946 | 0.1074 | 0.0025 | 127 | -0.0373 | 0.763502 | FAIL |
| 0.90 | 1.6743 | 0.1041 | 0.0042 | 123 | -0.0406 | 0.862645 | FAIL |
| 0.70 | 1.6878 | 0.1007 | 0.0034 | 119 | -0.0440 | 0.929290 | FAIL |

best2: **decay=0.80** (ge3=0.1117)

---

## STEP3 — repeat_window 격자 (carry_mult=2.2 · decay=0.80)

| repeat_window | mean | ge3_rate | ge4_rate | ge3_count | Δ vs pin | p_value | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 0 (전체) | 1.7107 | 0.1117 | 0.0034 | 132 | -0.0330 | 0.600284 | FAIL |
| 200 | 1.6929 | 0.1074 | 0.0017 | 127 | -0.0373 | 0.763502 | FAIL |
| 100 | 1.7073 | 0.1066 | 0.0042 | 126 | -0.0381 | 0.791304 | FAIL |
| 500 | 1.6963 | 0.1066 | 0.0034 | 126 | -0.0381 | 0.791304 | FAIL |
| 50 | 1.6794 | 0.1024 | 0.0017 | 121 | -0.0423 | 0.899894 | FAIL |

best3: **window=0(전체)** (ge3=0.1117)

---

## best_combo / gates

| 항목 | 값 |
|------|-----|
| best_combo | **carry=2.2 · decay=0.80 · window=0** |
| best ge3 | **0.1117** |
| Δ vs pin | **-0.0330** |
| p_value | **0.600284** |
| ge3_count | **132** |
| any_ge3_gt_pin | **false** |
| gates.pass | **false** |
| recommended_next | **K-ATTACK-HOLD** |

---

## Verdict / NEXT

**FAIL → `K-ATTACK-HOLD`**
review carry_mult/decay/repeat_window 15조합 격자 전부 ge3 ≤ pin(0.1447). live baseline(0.1100~0.1117) 대비 미세 개선만. predict_review_king.py **미수정**.
오늘 탐색 전축 소진 · 승인필요=**예**.

---

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/NEXT |
|------|------|--------|-------------|
| n_eval | 1182 | 1182 | 1182 |
| best_combo | carry=2.2\|decay=0.8\|window=0 | carry=2.2\|decay=0.8\|window=0 | carry=2.2\|decay=0.8\|window=0 |
| best ge3 | 0.1117 | 0.1117 | 0.1117 |
| Δ vs pin | -0.033 | -0.033 | -0.033 |
| p_value | 0.600284 | 0.600284 | 0.600284 |
| ge3_count | 132 | 132 | 132 |
| gates.pass | false | false | false |
| recommended_next | K-ATTACK-HOLD | K-ATTACK-HOLD | K-ATTACK-HOLD |

ASCII `-` 구분 · 숫자 SSOT=`docs/benchmarks/20260729_KREVIEW_TUNE_survey.json`
