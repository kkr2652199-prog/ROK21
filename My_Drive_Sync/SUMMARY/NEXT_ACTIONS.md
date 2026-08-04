# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-REPACK-HYBRID-WIRE-DONE
- 할일: hybrid wire PASS · 다음 **combined/FULL 재검증** 또는 I2 · **형 GO**
- 완료조건: 형 다음축 명시
- 선행완료: docs/benchmarks/20260804_KREPACK_HYBRID_WIRE.json · schema=2 · ge3 match ablation

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **WIRE** — signal_pool hy_p45_r123 (stat/review) · markov baseline · CACHE_SCHEMA_VERSION=2
- **검증 ge3** — stat 0.165 · markov 0.130 · review 0.135 (=ablation)
- coordinator/quota 미수정
