# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-EVOLVE-AUTO-S4-DONE
- 할일: S4 ops PASS · **모니터링(1236 SCORE)** 또는 다른축 · **형 GO**
- 완료조건: 형 선택
- 선행완료: docs/benchmarks/20260805_KEVOLVE_AUTO_S4.json · phase=ops

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- 운영: `$env:EVOLVE_AUTO=1; python tools/_k_evolve_auto_tick.py --ops`
- 롤백: EVOLVE_AUTO=0 · λ/covering HOLD · weight=0
- evolve_log=1235 · cache 1236 warm · healthy_idle
