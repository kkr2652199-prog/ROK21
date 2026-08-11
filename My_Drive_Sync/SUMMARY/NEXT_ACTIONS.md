# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-BT100-FOLLOW-HOLD
- 할일: **양산前**. BT100정밀감사 **NO_HARD_BUG**(4등5·5등51·뇌별repack확인·peekOK). **tune_json PATCHED**. 잔여고우선=강제100회재실행(cand_B·W0.9) / 몰아주기손실(pool>repack) / K-J SSOT. **1237아님**. 형 다음 지시 1건.
- 완료조건: 형 새 지시 1건
- 선행완료: K-BT100-DEEP-AUDIT · tune_json 패치
- 승인필요: 형 다음 지시
- 선행조건: 없음
- 최종갱신: 2026-08-11


## WORKSTATE
IDLE

---

## 메모
- 감사: docs/benchmarks/20260811_KBT100_DEEP_AUDIT.json
- 강제 재백테: python tools/_k_force_pool_backtest_100.py
