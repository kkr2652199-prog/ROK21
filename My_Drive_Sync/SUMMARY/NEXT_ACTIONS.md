# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-BENCH-01-WIRE
- 할일: K-BENCH-01 postmortem SIGNAL_FOUND — 쿼터갭 43.6%·markov best 52.5% · 형 GO 후 피드백축 WIRE 검토 (coordinator 수정은 별도 GO)
- 완료조건: 형이 WIRE 축 지정 또는 HOLD 유지 확인
- 승인필요: 예
- 선행완료: 2026-07-29 (K-BENCH-01 — postmortem WF n=1182 · SIGNAL_FOUND · AUX↔hit 무상관)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- V2 pin ge3=0.1447 · mean=1.7504 (stored)
- **4AUX_FEEDBACK_REVIEW** — 4보조=채점(분업분석 아님)·WIRE-V2 set_no_asc라 AUX 컷 없음·피드백 부분구현·형 감각=맞음/우리=보수 · `reports/20260729_4AUX_FEEDBACK_REVIEW.md`
- **K-BENCH-05·03 완료** — BENCH_PROTOCOL §6 baseline행 · §7 WF/tier 분리 · BENCH_REPORT_TEMPLATE.md
- **K-BENCH-02 완료 FAIL** — baseline ge3=0.1100 최고 · confidence/AUX 4축 하회 · K-BENCH-02-WIRE 불필요
- K-BENCH-01 **SIGNAL_FOUND** — 쿼터갭43.6%·markov best 52.5% · AUX↔hit 무상관 · `20260729_KBENCH_POSTMORTEM.json`
- REVIEW-TUNE best ge3=0.1117 (carry=2.2·decay=0.8·window=0)
- AUX-WEIGHT live baseline ge3=0.1100 · 13조합 동일
- 근거: docs/benchmarks/20260729_KREVIEW_TUNE_survey.json
