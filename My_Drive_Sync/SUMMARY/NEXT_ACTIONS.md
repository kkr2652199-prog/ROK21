# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: V2 pin ge3=0.1447 유지 · E2 POSTMORTEM-SIGNAL-02 또는 E3 PATTERN-HINT-03 survey는 형 GO 후 · coordinator/AUX 배선 금지
- 완료조건: 형 지정 축 대기 또는 E2/E3 GO
- 승인필요: 예
- 선행완료: 2026-07-29 (K-AUX-SIGNAL-01 FAIL — best miss_pattern@α=0.2 ge3=0.1303 p=0.042 · pin 미달)

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
