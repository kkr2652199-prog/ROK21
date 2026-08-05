# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-TRANSITION-STEP4-WIRE-DONE
- 할일: STEP4 배선 완료 · **fusion n200 live 재검증** 또는 롤백(`K_STAT_TRANSITION_V1=0`) 결정
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260805_KTRANSITION_STEP4_WIRE.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- TRANSITION_V1_WIRE=**True** (형 A GO) · smoke PASS · solo n50 ge3=**0.06** (약함)
- 롤백: env `K_STAT_TRANSITION_V1=0` 또는 `TRANSITION_V1_WIRE=False`
- STEP3 HOLD 상태에서 패치함 · fusion 전체 재검증 권고
