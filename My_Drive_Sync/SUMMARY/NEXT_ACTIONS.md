# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: STAT-WIRE FAIL(ge3=0.1176·Δ-0.0271·p=0.349617) · 롤백완료 · 다음 공격축 형 결정 대기
- 완료조건: 형이 다음 1축 지정 또는 HOLD 유지 확인
- 승인필요: 예
- 선행완료: 2026-07-29 (K-STAT-TUNE-WIRE FAIL·롤백)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- V2 pin ge3=0.1447 · mean=1.7504
- STAT-TUNE survey best ge3=0.1523 (stored markov/review + stat)
- STAT-WIRE live verify ge3=0.1176 (3뇌 live) → FAIL
- 근거: docs/benchmarks/20260729_KSTAT_WIRE_verify.json
