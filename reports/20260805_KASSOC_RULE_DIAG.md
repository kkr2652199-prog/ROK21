# K-ASSOC-RULE-DIAG — 연관규칙 전수 진단 (2026-08-05)

- **판정:** `NOISE` · wire=`False`
- draw_range: `[1, 1235]` · P0=0.1333 · n_sim=1000

## STEP1 1-gram
- candidates(|δ|≥0.02): 905 (+/− = 455/450)
- max_delta=0.084314 · sim_p95=0.11674 · **NOISE**
- top10+: `[{'n': 20, 'm': 18, 'delta': 0.084314}, {'n': 36, 'm': 44, 'delta': 0.080081}, {'n': 24, 'm': 37, 'delta': 0.07751}, {'n': 5, 'm': 27, 'delta': 0.075817}, {'n': 19, 'm': 34, 'delta': 0.072549}]` …

## STEP2 2-gram
- antecedents≥10: 980 · checked=44100
- candidates(|δ|≥0.04): 27662
- max_delta=0.45 · sim_p95=0.558974 · **NOISE**
- top5 abs: `[{'n1': 28, 'n2': 32, 'm': 27, 'delta': 0.45, 'support': 12}, {'n1': 10, 'n2': 39, 'm': 19, 'delta': 0.438095, 'support': 14}, {'n1': 8, 'n2': 22, 'm': 4, 'delta': 0.405128, 'support': 13}, {'n1': 16, 'n2': 22, 'm': 34, 'delta': 0.366667, 'support': 10}, {'n1': 5, 'n2': 41, 'm': 27, 'delta': 0.366667, 'support': 14}]`

## STEP3 3-gram
- antecedents≥5: 410 · checked=18450
- candidates(|δ|≥0.06): 16287
- max_delta=0.666667 · sim_p95=0.866667 · **NOISE**
- top10: `[{'n1': 8, 'n2': 34, 'n3': 39, 'm': 36, 'delta': 0.666667, 'support': 5}, {'n1': 6, 'n2': 17, 'n3': 18, 'm': 5, 'delta': 0.666667, 'support': 5}, {'n1': 1, 'n2': 26, 'n3': 28, 'm': 33, 'delta': 0.666667, 'support': 5}, {'n1': 11, 'n2': 21, 'n3': 30, 'm': 43, 'delta': 0.666667, 'support': 5}, {'n1': 4, 'n2': 16, 'n3': 40, 'm': 2, 'delta': 0.666667, 'support': 5}, {'n1': 2, 'n2': 4, 'n3': 20, 'm': 7, 'delta': 0.666667, 'support': 5}, {'n1': 14, 'n2': 19, 'n3': 43, 'm': 8, 'delta': 0.666667, 'support': 5}, {'n1': 3, 'n2': 12, 'n3': 43, 'm': 35, 'delta': 0.666667, 'support': 5}, {'n1': 1, 'n2': 29, 'n3': 37, 'm': 1, 'delta': 0.666667, 'support': 5}, {'n1': 19, 'n2': 27, 'n3': 45, 'm': 11, 'delta': 0.666667, 'support': 5}]`

## 요약
- signal_summary: STEP1~3 모두 NOISE (SIGNAL 0/3). maxδ 실측이 시뮬 p95 미달 — 조건부 편차는 표본변동 범위.
- next_step_implication: 신호 없음 → cold-free wire 단독 진행 검토 (assoc wire 통합 보류)
- tool: `tools/_k_assoc_rule_diag.py`
