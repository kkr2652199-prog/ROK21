# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: **K-BENCH-05·03** — baseline행·WF/tier 분리 프로토콜·템플릿 · NEXT=K-ATTACK-HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-BENCH-05 | **PATCHED** — E[match]=0.8 · ge3 null=0.1137 · SUMMARY baseline 행 필수 |
| K-BENCH-03 | **PATCHED** — WF live vs stored 분리 · tier 1~5등 집계 규칙 |
| K-POSTHOC-ANALYSIS | **무신호** · 50시드×50회 · best ge3=0.18 p=0.109 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (stored) |
| 권고 | **K-ATTACK-HOLD** · V2 pin 유지 · 형 GO 후 K-BENCH-02 survey |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-BENCH-05·03** | BENCH_PROTOCOL §6·§7 · BENCH_REPORT_TEMPLATE · 보고서 baseline 예시 2건 | **PROTOCOL OK** |
| K-POSTHOC-ANALYSIS | 50시드×50회 역추적 · 뇌별/특성 패턴 분석 | **무신호** |
| K-REVIEW-TUNE-SURVEY | review carry/decay/window 15조합 | **FAIL** |
| K-AUX-WEIGHT-SURVEY | 13조합 live · set_no 쿼터 | **FAIL** · 티켓불변 |

---

## 2) BENCH 프로토콜 핵심 (K-BENCH-05·03)

| 항목 | 값 |
|------|-----|
| theory mean | **0.8000** (= 6×6/45) |
| theory ge3 (null) | **0.1137** |
| WF vs stored | **표 2개 또는 `pipeline` 컬럼** — 혼용 금지 |
| tier 규칙 | 1등=6 · 2등=5+bonus · 3등=5 · 4등=4 · 5등=3 (`routes.py` 동일) |
| ge3 단독 표 | tier 피벗 표 **함께** 병기 (UI 착시 방지) |
| 템플릿 | `reports/BENCH_REPORT_TEMPLATE.md` |

근거: `My_Drive_Sync/SUMMARY/BENCH_PROTOCOL.md` §6·§7

---

## 3) POSTHOC 핵심 (유지)

| 항목 | 값 |
|------|-----|
| n_seeds | **50** |
| overall mean ge3 | **0.1052** · std=0.0417 |
| best seed | #44 ge3=**0.18** p=**0.109** (유의하지 않음) |
| 결론 | 체계적 활용 가능 신호 없음 |

근거: `docs/benchmarks/20260729_KPOSTHOC_analysis.json`

---

## 4) 다음

K-ATTACK-HOLD — POSTHOC 무신호 · V2 pin 유지 · 형 GO 후 K-BENCH-02 confidence survey.

---

## 5) 산출물

- `My_Drive_Sync/SUMMARY/BENCH_PROTOCOL.md` (§6·§7)
- `reports/BENCH_REPORT_TEMPLATE.md`
- `reports/20260729_KCOVER_SURVEY.md` · `reports/20260729_KPOSTHOC_ANALYSIS.md` (baseline 행 예시)

## 팩트체크

| 항목 | BENCH_PROTOCOL | TEMPLATE | STATUS |
|------|----------------|----------|--------|
| E[match] baseline | 0.8 | 0.8000 | 0.8 |
| ge3 null | 0.1137 | 0.1137 | 0.1137 |
| WF/stored 분리 | §7.1 | pipeline 컬럼 | 필수 |
| tier 1~5 | §7.2 | r1~r5 표 | routes 동일 |
