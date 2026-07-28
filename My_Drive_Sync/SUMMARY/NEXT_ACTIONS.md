# NEXT_ACTIONS.md — 다음 1건 단일 앵커 (K-AD)

> STEP1 `guard_boot` 는 **아래 `## NEXT (1건)` 블록만** 읽는다. 여러 건 나열 금지.

## NEXT (1건)
- ID: K-SETCOUNT-WIRE
- 할일: SETCOUNT PASS(n=10·15 ge3>RR) · 배선 전 null/비용 대비 검증 후 SETS 확장 여부 결정
- 선행조건: K-SETCOUNT-SURVEY 완료 · recommended=K-SETCOUNT-WIRE · 승인필요
- 승인필요: 예
- 최종갱신: 2026-07-29 (K-SETCOUNT-SURVEY)

## WORKSTATE
IDLE

---

## 참고 (앵커 아님 · guard 미읽음)

- n=15 ge3=0.3088 ≈ null best15 0.3132 · 발권수 효과 주의(K-08)
- markov solo ge3=0.1362 · top1_3 ge3=0.1447 (부수 BRAIN-SOLO 후보)
- 근거: `docs/benchmarks/20260729_KSETCOUNT_survey.json`
