# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: **4AUX_FEEDBACK_REVIEW** — 형 6문 코드 READ-ONLY+GenSpark 교차 · NEXT=K-ATTACK-HOLD 유지

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-BENCH-02 | **FAIL** — confidence/AUX 정렬 4축 ge3 0.0990~0.1024 · baseline 0.1100 최고 |
| K-BENCH-05 | **PATCHED** — E[match]=0.8 · ge3 null=0.1137 · SUMMARY baseline 행 필수 |
| K-POSTHOC-ANALYSIS | **무신호** · 50시드×50회 · best ge3=0.18 p=0.109 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (stored) |
| 권고 | **K-ATTACK-HOLD** · V2 pin 유지 · K-BENCH-02-WIRE 불필요 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **4AUX_FEEDBACK_REVIEW** | 4보조=채점·set_no_asc면 컷없음·피드백 부분구현 · GenSpark 일치 | **REVIEW OK** |
| **K-BENCH-02** | confidence/AUX 5축 live WF · set_no_asc vs confidence/quota | **FAIL** · baseline 최고 |
| K-BENCH-05·03 | BENCH_PROTOCOL §6·§7 · BENCH_REPORT_TEMPLATE | **PROTOCOL OK** |
| K-AUX-WEIGHT-SURVEY | 13조합 live · set_no 쿼터 | **FAIL** · 티켓불변 |
| K-POSTHOC-ANALYSIS | 50시드×50회 역추적 | **무신호** |

---

## 2) K-BENCH-02 핵심

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

K-ATTACK-HOLD — V2 pin 유지 · 형 다음 1축 지정 (K-BENCH-01 postmortem 또는 HOLD).  
GenSpark 권장 최소: K-BENCH-01 → hit-draw 특성 → (GO) 등수 피드백 태그.

---

## 6) 산출물

- `reports/20260729_4AUX_FEEDBACK_REVIEW.md`
- `tools/_k_bench_confidence_survey.py`
- `docs/benchmarks/20260729_KBENCH_CONFIDENCE_survey.json`
- `reports/20260729_KBENCH_CONFIDENCE_SURVEY.md`

## 팩트체크

| 항목 | JSON | 보고서 | STATUS |
|------|------|--------|--------|
| n_eval | 1182 | 1182 | 1182 |
| baseline ge3 | 0.11 | 0.1100 | 0.1100 |
| best variant | baseline_set_no_asc | baseline_set_no_asc | baseline_set_no_asc |
| gates.pass | false | false | false |
| recommended_next | K-ATTACK-HOLD | K-ATTACK-HOLD | K-ATTACK-HOLD |
