# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-30 KST  
📌 사유: **K-SIGNAL-SELECT-01 QUICK PASS** · combined ge3=0.145 · K-QUICK-GATE-01 foundation

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-SIGNAL-SELECT-01 | **QUICK PASS** — combined ge3=**0.145** p=0.102 · tail n=200 |
| K-QUICK-GATE-01 | **DONE** — BENCH §9 · bench_quick_gate.py · `--n-eval` |
| K-WINDOW-SIGNAL-01 | **FAIL** — best w4_zone_mix@α=0.1 ge3=**0.1328** p=0.023 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (stored) |
| 권고 | **K-SIGNAL-SELECT-FULL** (1182) · wire는 형 GO 전 금지 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-SIGNAL-SELECT-01** | 10pool/brain×3뇌 → 통합5 선별 · overlap/bin/jaccard/combined · QUICK n=200 | **QUICK PASS** · combined ge3=0.145 |
| **K-QUICK-GATE-01** | BENCH §9 · tail-200 · bench_quick_gate.py · window survey `--n-eval` | **DONE** |
| **K-WINDOW-SIGNAL-01** | DHLOTTERY 4/8/12/52/all×4signal hint inject · 61 variants · n=1182 seed=42 | **FAIL** · best ge3=0.1328 |
| **K-POSTMORTEM-SIGNAL-02** | ge3+ draw_features bin stratification · READ-ONLY | **DONE** · lift 미약 |
| **K-AUX-SIGNAL-01** | 4보조 hint inject live WF · 5 variants×α · n=1182 seed=42 | **FAIL** · best ge3=0.1303 |
| **DHLOTTERY-AUDIT** | 동행복권 lt645 추첨·통계·판매점 READ-ONLY · K-AUX 3아이디어 | **AUDIT OK** |
| **K-BENCH-01** | postmortem WF n=1182 · tier·쿼터갭·AUX상관 · seed=42 | **SIGNAL_FOUND** |
| **4AUX_FEEDBACK_REVIEW** | 4보조=채점·set_no_asc면 컷없음·피드백 부분구현 · GenSpark 일치 | **REVIEW OK** |
| **K-BENCH-02** | confidence/AUX 5축 live WF · set_no_asc vs confidence/quota | **FAIL** · baseline 최고 |
| K-BENCH-05·03 | BENCH_PROTOCOL §6·§7 · BENCH_REPORT_TEMPLATE | **PROTOCOL OK** |
| K-POSTHOC-ANALYSIS | 50시드×50회 역추적 | **무신호** |

---

## 2) K-BENCH-01 핵심

| 지표 | 값 | 비고 |
|------|-----|------|
| n_eval | **1182** | draw 53~1234 · seed=42 |
| ge3_rate (selected best-of-5) | **0.11** | mean=1.7191 · pin 미달(진단) |
| 쿼터 갭 | **43.6%** (516/1182) | 15중 best > 선택5 best · avg gap=1.188 |
| markov 15중 best | **52.5%** | stat 29.9% · review 17.5% |
| AUX↔hit spearman | **~0** | miss/referee constant · pattern/balance 무상관 |
| tier (selected 5) | r4=7 · r5=132 | ge3=139/5910 sets |
| verdict | **SIGNAL_FOUND** | ge3 PASS/FAIL 아님 |

근거: `docs/benchmarks/20260729_KBENCH_POSTMORTEM.json`

---

## 3) K-BENCH-02 핵심

| variant | ge3_rate | mean | Δ vs pin | p (null) | verdict |
|---------|----------|------|----------|----------|---------|
| baseline_set_no_asc | **0.1100** | 1.7191 | −0.0347 | 0.669622 | FAIL |
| confidence_desc | 0.1024 | 1.6997 | −0.0423 | 0.899894 | FAIL |
| aux_quota | 0.1007 | 1.6878 | −0.0440 | 0.929290 | FAIL |
| confidence_quota | 0.0998 | 1.6760 | −0.0449 | 0.941286 | FAIL |
| aux_total_desc | 0.0990 | 1.6853 | −0.0457 | 0.951647 | FAIL |

| 항목 | 값 |
|------|-----|
| n_eval | **1182** (draw 53~1234) |
| pipeline | WF live · seed=42 · SETS_PER_PREDICT_BRAIN=5 |
| 관측 | confidence/AUX 정렬은 set_no_asc **대비 ge3 하락** (역효과) |
| coordinator | **미수정** · K-BENCH-02-WIRE **불필요** |

근거: `docs/benchmarks/20260729_KBENCH_CONFIDENCE_survey.json`

---

## 3e) K-SIGNAL-SELECT-01 핵심 (QUICK tail-200)

| selector | ge3_rate | mean | Δ vs pin | Δ vs null | p (null) | verdict |
|----------|----------|------|----------|-----------|----------|---------|
| **combined** | **0.145** | 1.715 | +0.0003 | +0.0313 | **0.102** | **QUICK PASS** |
| bin_match | 0.115 | 1.68 | −0.0297 | +0.0013 | 0.510 | FAIL |
| jaccard_div | 0.115 | 1.595 | −0.0297 | +0.0013 | 0.510 | FAIL |
| set_no_asc (control) | 0.08 | 1.68 | −0.0647 | −0.0337 | 0.952 | FAIL |
| window_overlap | 0.08 | 1.64 | −0.0647 | −0.0337 | 0.952 | FAIL |

| 항목 | 값 |
|------|-----|
| n_eval | **200** (draw 1035~1234) · seed=42 · elapsed 18s |
| pool | 3뇌×10 (survey 2-pass) → 통합 5 신호셋트 |
| window hint | w4_zone_mix (K-WINDOW best) |
| QUICK gate | ge3>null AND p<0.15 → **PASS** (combined) |
| coordinator | **미수정** · wire **형 GO 전 금지** |

근거: `docs/benchmarks/20260730_KSIGNAL_SELECT_survey.json`

---

## 3c) K-WINDOW-SIGNAL-01 핵심

| variant | window | signal | α | ge3_rate | mean | Δ vs pin | p (null) | verdict |
|---------|--------|--------|--:|---------:|-----:|---------:|---------:|---------|
| **w4_zone_mix** | 4주 | zone_mix | 0.1 | **0.1328** | 1.7453 | −0.0119 | **0.0232** | FAIL (pin 미달) |
| w4_sum_band | 4주 | sum_band | 0.2 | 0.1311 | 1.72 | −0.0136 | 0.035 | FAIL |
| w8_miss_pattern | 8주 | miss_pattern | 0.2 | 0.1303 | 1.7081 | −0.0144 | 0.042 | FAIL |
| baseline (AUX score) | — | — | 0 | 0.1108 | 1.7318 | −0.0339 | 0.635 | FAIL |

| 항목 | 값 |
|------|-----|
| n_eval | **1182** · seed=42 · elapsed 7094s |
| variants | 61 (5 windows × 4 signals × 3 α + baseline) |
| PASS gate | ge3 > 0.1447 AND p < 0.05 → **FAIL** |
| coordinator | **미수정** · K-WINDOW-SIGNAL-WIRE **보류** |

근거: `docs/benchmarks/20260729_KWINDOW_SIGNAL_survey.json`

---

## 3d) K-POSTMORTEM-SIGNAL-02 핵심

| axis | best bin | ge3_rate | lift vs overall(0.11) |
|------|----------|---------:|----------------------:|
| odd_count | odd=2 | 0.1412 | +0.0312 |
| ac | ac>=9 | 0.1206 | +0.0106 |
| sum_band | mid(120-155) | 0.1137 | +0.0037 |

판정: bin lift **미약** — E3 hint 설계 시 단일 bin 의존 비권장.

근거: `docs/benchmarks/20260729_KPOSTMORTEM_SIGNAL02.json`

---

## 3b) K-AUX-SIGNAL-01 핵심

| variant | α | ge3_rate | mean | Δ vs pin | p (null) | verdict |
|---------|--:|---------:|-----:|---------:|---------:|---------|
| **miss_pattern** | 0.2 | **0.1303** | 1.7301 | −0.0144 | **0.042** | FAIL (pin 미달) |
| pattern_store_lite | 0.05 | 0.1235 | 1.7191 | −0.0212 | 0.154 | FAIL |
| baseline (AUX score) | 0 | 0.1218 | 1.7259 | −0.0229 | 0.201 | FAIL |
| balance_hint | 0.05 | 0.1024 | 1.6988 | −0.0423 | 0.900 | FAIL |

| 항목 | 값 |
|------|-----|
| n_eval | **1182** · seed=42 · elapsed 1504s |
| inject | survey `random.choices` wrapper · predict path only |
| PASS gate | ge3 > 0.1447 AND p < 0.05 → **FAIL** |
| coordinator | **미수정** · K-AUX-SIGNAL-WIRE **보류** |

근거: `docs/benchmarks/20260729_KAUX_SIGNAL_survey.json`

---

## 4) BENCH 프로토콜 (유지)

| 항목 | 값 |
|------|-----|
| theory mean | **0.8000** |
| theory ge3 (null) | **0.1137** |
| WF vs stored | **표 2개 또는 `pipeline` 컬럼** — 혼용 금지 |
| tier 규칙 | 1등=6 · 2등=5+bonus · 3등=5 · 4등=4 · 5등=3 |

---

## 4) 4보조·피드백 (형 가설 판정 · READ-ONLY)

| 질문 | 판정 |
|------|------|
| 4보조=검증된 심사? | **아님** (미입증·기각 명분) |
| DB 분업 분석? | **아님** — 15장 채점 |
| AUX 컷으로 신호 유실? | **현 배선(set_no_asc)에선 컷 없음** · confidence 정렬은 BENCH-02에서 더 나쁨 |
| 당첨/미당첨→피드백 축적 | **뼈대 있음·등수별 부족** · markov는 learn_state 미사용 |
| 형 vs 보수 | 형 감각 맞음 · AI측 “증명 전 배선 금지”로 보수 — **둘 다 맞음** |

근거: `reports/20260729_4AUX_FEEDBACK_REVIEW.md` · GenSpark 형6문 답변

---

## 5) 다음

**K-SIGNAL-SELECT-FULL** — QUICK PASS(combined ge3=0.145) → full n=1182 확인 · wire는 형 GO 전 금지.  
V2 pin ge3=0.1447 유지 · coordinator·predict_* **수정 금지**.

---

## 6) 산출물

- `tools/bench_quick_gate.py` · `tools/_k_signal_select_survey.py`
- `docs/benchmarks/20260730_KSIGNAL_SELECT_survey.json`
- `reports/20260730_KSIGNAL_SELECT_SURVEY.md`
- `My_Drive_Sync/SUMMARY/BENCH_PROTOCOL.md` §9 QUICK_GATE
- `tools/_k_window_signal_survey.py` (`--n-eval`)

## 팩트체크

| 항목 | JSON | 보고서 | STATUS |
|------|------|--------|--------|
| n_eval | 1182 | 1182 | 1182 |
| ge3_rate | 0.11 | 0.11 | 0.11 |
| quota_missed_rate | 0.4365 | 0.4365 | 0.4365 |
| verdict | SIGNAL_FOUND | SIGNAL_FOUND | SIGNAL_FOUND |
| recommended_next | K-BENCH-01-WIRE | K-BENCH-01-WIRE | K-BENCH-01-WIRE |
