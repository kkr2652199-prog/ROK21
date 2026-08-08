# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-BRAIN-INDEPENDENT-WIRE-DONE
- 할일: hint 분리 결과 + EV프록시 게이트 형 확인. **WIRE_CONFORMS 5/5** · EV=`MARGINAL`(delta−0.0927 · 3구간 consistent). 형 GO → 각 뇌 독립 튜닝 단계로 / PARTIAL·FAIL이었으면 추가 버그 수정 후 재검증(이번 턴은 CONFORMS)
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260808_KBRAIN_INDEPENDENT_WIRE.json · reports/20260808_KBRAIN_INDEPENDENT_WIRE.md · tools/_k_brain_independent_wire.py
- 승인필요: 형 GO (다음 튜닝 착수)
- 선행조건: 없음
- 최종갱신: 2026-08-08


## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- HOLD 복원: `lotto4.js` → `ROK21_TESTLOTTO_FOCUS_HOLD = false`
- 롤백: `K_CROWD_PREFER=0` · `K_PRIZE_EV=0`
