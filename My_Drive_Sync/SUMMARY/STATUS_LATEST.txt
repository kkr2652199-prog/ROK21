# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: **K-BENCH-01 postmortem SIGNAL_FOUND** — 쿼터갭·뇌지배 신호 · NEXT=K-BENCH-01-WIRE

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-BENCH-01 | **SIGNAL_FOUND** — 쿼터갭 43.6% · markov 15중 best 52.5% · AUX↔hit 무상관 |
| K-BENCH-02 | **FAIL** — confidence/AUX 정렬 4축 ge3 0.0990~0.1024 · baseline 0.1100 최고 |
| K-BENCH-05 | **PATCHED** — E[match]=0.8 · ge3 null=0.1137 · SUMMARY baseline 행 필수 |
| K-POSTHOC-ANALYSIS | **무신호** · 50시드×50회 · best ge3=0.18 p=0.109 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (stored) |
| 권고 | **K-BENCH-01-WIRE** (형 GO) · V2 pin 유지 · coordinator 수정 별도 GO |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
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

## 3) BENCH 프로토콜 (유지)

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

K-BENCH-01-WIRE — postmortem SIGNAL_FOUND · 쿼터갭·markov 지배 신호 · 형 GO 후 피드백축 WIRE 검토.  
K-BENCH-02 baseline(set_no_asc) 여전히 confidence/AUX 정렬보다 우수 → coordinator 수정 별도 GO.

---

## 6) 산출물

- `tools/_k_bench_postmortem.py`
- `docs/benchmarks/20260729_KBENCH_POSTMORTEM.json`
- `reports/20260729_KBENCH_POSTMORTEM.md`
- `reports/20260729_4AUX_FEEDBACK_REVIEW.md`
- `docs/benchmarks/20260729_KBENCH_CONFIDENCE_survey.json`

## 팩트체크

| 항목 | JSON | 보고서 | STATUS |
|------|------|--------|--------|
| n_eval | 1182 | 1182 | 1182 |
| ge3_rate | 0.11 | 0.11 | 0.11 |
| quota_missed_rate | 0.4365 | 0.4365 | 0.4365 |
| verdict | SIGNAL_FOUND | SIGNAL_FOUND | SIGNAL_FOUND |
| recommended_next | K-BENCH-01-WIRE | K-BENCH-01-WIRE | K-BENCH-01-WIRE |
