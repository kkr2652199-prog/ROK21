# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ASSOC-RULE-DIAG-DONE
- 할일: 연관규칙 신호 진단 완료 · 결과 확인 · **cold-free wire 단독 진행** (신호無)
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260805_KASSOC_RULE_DIAG.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- STEP1~3 전부 NOISE (maxδ < sim p95) → assoc wire 통합 보류
- NOISE → **cold-free wire 단독 진행** 검토
- STRONG/MARGINAL 시에만 신호 통합 wire 논의
