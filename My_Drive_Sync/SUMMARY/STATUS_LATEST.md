# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: **K-AUX-SIGNAL-01 survey 완료 FAIL**

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-BENCH-01-WIRE | **FAIL** ge3=**0.1142** p=0.49 · tier 피드백 **롤백** |
| K-AUX-SIGNAL-01 | **FAIL** — best miss_pattern@α=0.2 ge3=**0.1303** p=0.042 · pin 0.1447 미달 |
| K-AUX-SIGNAL | **OPEN** — E1 FAIL · E2/E3 후보 · WIRE 보류 |
| K-BENCH-01 | **SIGNAL_FOUND** — 쿼터갭 43.6% · markov 52.5% · AUX↔hit 무상관 |
| K-BENCH-02 | **FAIL** — confidence/AUX 정렬 4축 ge3 0.0990~0.1024 · baseline 0.1100 최고 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (stored) |
| 권고 | **K-ATTACK-HOLD** · V2 pin 유지 · E2/E3 survey는 형 GO |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
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

**K-ATTACK-HOLD** — V2 pin ge3=0.1447 유지.  
K-AUX-SIGNAL-01 FAIL → E2 POSTMORTEM-SIGNAL-02 또는 E3 PATTERN-HINT-03 survey는 **형 GO** 후.  
coordinator·aux_*.py·predict_* **수정 금지**.

---

## 6) 산출물

- `tools/_k_bench_postmortem.py`
- `docs/benchmarks/20260729_KBENCH_POSTMORTEM.json`
- `reports/20260729_KBENCH_POSTMORTEM.md`
- `reports/20260729_4AUX_FEEDBACK_REVIEW.md`
- `docs/benchmarks/20260729_KAUX_SIGNAL_survey.json`
- `reports/20260729_KAUX_SIGNAL_SURVEY.md`

## 팩트체크

| 항목 | JSON | 보고서 | STATUS |
|------|------|--------|--------|
| n_eval | 1182 | 1182 | 1182 |
| ge3_rate | 0.11 | 0.11 | 0.11 |
| quota_missed_rate | 0.4365 | 0.4365 | 0.4365 |
| verdict | SIGNAL_FOUND | SIGNAL_FOUND | SIGNAL_FOUND |
| recommended_next | K-BENCH-01-WIRE | K-BENCH-01-WIRE | K-BENCH-01-WIRE |
