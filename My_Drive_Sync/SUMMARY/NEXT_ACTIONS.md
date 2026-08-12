# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-REPACK-READ-LEDGER
- 할일: **양산前**. L3 원장 **WIRE_OK**(ledger+scatter CREATE·피드백경로쓰기·1236 45행·no_peek). 다음=**L4** 몰아주기(`focus_r1`)가 원장 SSOT **읽기**(draw_no<target · EMA단독탈피). **1237아님** · 역할슬롯 코드는 L4b · 강제BT보류.
- 완료조건: repack 경로가 `testlotto_pool_hit_ledger`/`scatter` 소비 · no_peek 유지 · prefer/prize는 L4b게이트(본건은 wire·소비검증)
- 선행완료: K-POOL-HIT-LEDGER-WIRE · L2 SPEC · L2b SPEC · L1 SMOKE_OK
- 승인필요: 없음(리스트 순서)
- 선행조건: L3 WIRE_OK
- 최종갱신: 2026-08-12


## WORKSTATE
IDLE

---

## 메모
- reports/20260812_KPOOL_HIT_LEDGER_WIRE.md
- docs/benchmarks/20260812_KPOOL_HIT_LEDGER_WIRE.json
- app/testlotto/pool_hit_ledger.py
- reports/20260812_KTIER_ROLE_SLOTS_SPEC.md
- reports/20260812_KPOOL_HIT_LEDGER_SPEC.md
