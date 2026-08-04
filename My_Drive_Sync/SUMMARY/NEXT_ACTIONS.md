# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PATCH-1235-PREP-DONE
- 할일: 패치 후보 측정 완료 · **wire GO 대기** · **형 결정**
- 완료조건: 형 선택(quota B/C/D 중 wire GO 여부)
- 선행완료: docs/benchmarks/20260805_KPATCH_1235_PREP.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- 후보: quota B/C(+0.02)·D(+0.035)만 Δ≥+0.01 · PMI/B-sum/D-dynamic는 역방향·미등재
- wire=False · quota 실변경 금지
