# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-AUX-SIGNAL-01
- 할일: 4보조 역할 전환 survey (READ-ONLY) — 채점→신호벡터 힌트 시뮬 · `reports/20260729_AUX_SIGNAL_PIVOT.md` E1 참고 · coordinator 변경은 별도 GO
- 완료조건: survey JSON+보고서 · ge3 vs pin 0.1447 비교
- 승인필요: 예
- 선행완료: 2026-07-29 (K-BENCH-01-WIRE FAIL ge3=0.1142·tier 롤백 · AUX_SIGNAL_PIVOT 문서)

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
