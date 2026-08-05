# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-TRANSITION-STEP3-DESIGN-DONE
- 할일: 설계 결과 형 확인 → **STEP4(실제 stat 교체 패치) GO 여부** 결정 (현재 replace=**HOLD**)
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260805_KTRANSITION_STEP3_DESIGN.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- DESIGN_HOLD · nopeek mean**2.007** · ge3_rate**0.274**<rand0.311 · FULL holdout**2.178**
- REPLACE_GO 미달 · wire/brains 미수정 · STEP4는 형 GO 후만
