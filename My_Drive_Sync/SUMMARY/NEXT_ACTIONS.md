# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: K-BENCH-02 FAIL(confidence/AUX 정렬 전축 ge3≤0.1100·baseline 최고) · V2 pin 유지 · 형 다음 1축 지정 대기 (K-BENCH-01 postmortem 또는 HOLD)
- 완료조건: 형이 다음 1축 지정 또는 HOLD 유지 확인
- 승인필요: 예
- 선행완료: 2026-07-29 (K-BENCH-02 — confidence survey FAIL · coordinator 미수정)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- V2 pin ge3=0.1447 · mean=1.7504 (stored)
- **4AUX_FEEDBACK_REVIEW** — 4보조=채점(분업분석 아님)·WIRE-V2 set_no_asc라 AUX 컷 없음·피드백 부분구현·형 감각=맞음/우리=보수 · `reports/20260729_4AUX_FEEDBACK_REVIEW.md`
- **K-BENCH-05·03 완료** — BENCH_PROTOCOL §6 baseline행 · §7 WF/tier 분리 · BENCH_REPORT_TEMPLATE.md
- **K-BENCH-02 완료 FAIL** — baseline ge3=0.1100 최고 · confidence/AUX 4축 하회 · K-BENCH-02-WIRE 불필요
- K-BENCH-01 — 형 GO 후 postmortem survey 대기 (GenSpark도 최소실험로 권장)
- REVIEW-TUNE best ge3=0.1117 (carry=2.2·decay=0.8·window=0)
- AUX-WEIGHT live baseline ge3=0.1100 · 13조합 동일
- 근거: docs/benchmarks/20260729_KREVIEW_TUNE_survey.json
