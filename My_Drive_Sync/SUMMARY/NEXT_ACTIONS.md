# NEXT_ACTIONS.md — 다음 1건만 커서가 읽음 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 여러 건 나열 금지.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: SUM-SELECT FAIL(hit 전게이트false · 최근접 Δge3-0.0043) · WIRE금지 · V2유지 · SUM-SELECT재탕금지 · 형·커서 다음 축 1건 재선정
- 선행조건: K-SUM-SELECT 관측완료 · recommended=없음(HOLD·V2유지)
- 승인필요: 예
- 최종갱신: 2026-07-29 (K-SUM-SELECT FAIL)

## WORKSTATE
IDLE

---

## 참고 (커서 아님 · guard 미읽음)

- V2 pin ge3=0.1447 · mean=1.7504 · mean_sum=137.1042
- 이론합 근접(sum_near) 시 ge3↓ (Δ=-0.0170) · 최근접 far Δ=-0.0043
- 근거: docs/benchmarks/20260729_KSUM_select.json · reports/20260729_KSUM_SELECT.md
