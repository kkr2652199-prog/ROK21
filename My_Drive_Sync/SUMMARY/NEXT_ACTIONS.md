# NEXT_ACTIONS.md — 형이 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 줄만** 읽는다. 다른 섹션 참고.

## NEXT (1건)
- ID: K-WINDOW-SIGNAL-01
- 할일: `tools/_k_window_signal_survey.py` 실행 → `docs/benchmarks/*KWINDOW*` + `reports/*KWINDOW*` · pin ge3=0.1447 대비 · stored/live 갭(Δ0.0229) 연계
- 완료조건: 형 GO 또는 survey JSON+보고서 확정
- 형승인: —
- 갱신일: 2026-07-29 (E2 K-POSTMORTEM-SIGNAL-02 완료 · 1군 vs ROK21 READ-ONLY 비교 · KWINDOW JSON 미생성)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- V2 pin ge3=0.1447 · mean=1.7504 (stored)
- **4AUX_FEEDBACK_REVIEW** — 4뇌=채널(영역분석 아님)·WIRE-V2 set_no_asc· AUX 는 피드백성· 부분비교만· 형=실전/우리=연구 → `reports/20260729_4AUX_FEEDBACK_REVIEW.md`
- **K-BENCH-05→03 완료** — BENCH_PROTOCOL §6 baseline· §7 WF/tier 분리 → BENCH_REPORT_TEMPLATE.md
- **K-BENCH-02 완료 FAIL** — baseline ge3=0.1100 최고 · confidence/AUX 4뇌 회귀 → K-BENCH-02-WIRE 불필요
- K-BENCH-01 **SIGNAL_FOUND** — 필터율43.6%·markov best 52.5% · AUX·hit 분리됨 → `20260729_KBENCH_POSTMORTEM.json`
- REVIEW-TUNE best ge3=0.1117 (carry=2.2·decay=0.8·window=0)
- AUX-WEIGHT live baseline ge3=0.1100 · 13조합 고정
- 근거: docs/benchmarks/20260729_KREVIEW_TUNE_survey.json
