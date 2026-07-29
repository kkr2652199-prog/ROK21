# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-STAT-TUNE-WIRE
- 할일: STAT-TUNE PASS(best ge3=0.1523·Δ+0.0076·p=3.6e-05) · 형 승인 후 predict_statistical 리터럴(0.02/gap20/hot10·pairs30/cap0.5) 배선·verify · 승인 전 코드수정금지
- 완료조건: 형 GO → 배선+verify JSON · 또는 형 NO → HOLD/다른축
- 승인필요: 예
- 선행완료: 2026-07-29 (K-STAT-TUNE)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- V2 pin ge3=0.1447 · mean=1.7504
- STAT-TUNE best ge3=0.1523 · mean=1.7758
- 근거: docs/benchmarks/20260729_KSTAT_TUNE_survey.json
