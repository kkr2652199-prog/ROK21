# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-EVOLVE-VIRTUAL-1235-DONE
- 할일: 1235 가상생애 PASS · **1236 실추첨 후 ops SCORE** 또는 다른축 · **형 GO**
- 완료조건: 형 선택
- 선행완료: docs/benchmarks/20260805_KEVOLVE_VIRTUAL_1235.json

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- 가상: live hybrid+mean · λ/cover OFF · weight=0
- 1235 SCORE: stat/review best=2 · markov=1 · ge3 없음
- 운영: `$env:EVOLVE_AUTO=1; python tools/_k_evolve_auto_tick.py --ops`
