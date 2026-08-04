# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-EARLY-DIAG-DONE
- 할일: early 취약성 진단 완료 · 결과 확인 · **K-NEIGHBOR-MATCH 진행**
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260805_KEARLY_DIAG.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- verdict=STRUCTURAL · early≠단독붕괴(late가 더 낮음) · cold mid에서만 VIABLE
- early 전용 wire 근거 약함 · cold-free/neighbor 우선
