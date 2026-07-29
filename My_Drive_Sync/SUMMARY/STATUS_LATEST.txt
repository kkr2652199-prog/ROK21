# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: **K-BENCH-02** — confidence/AUX 5축 live survey FAIL · baseline ge3=0.1100 최고 · NEXT=K-ATTACK-HOLD

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

## 4) 다음

K-ATTACK-HOLD — V2 pin 유지 · 형 다음 1축 지정 (K-BENCH-01 postmortem 또는 HOLD).

---

## 5) 산출물

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
