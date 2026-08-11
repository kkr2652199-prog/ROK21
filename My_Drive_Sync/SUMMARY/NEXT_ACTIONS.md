# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-FORCE-POOL-BT-HOLD
- 할일: **양산前**. 강제 리셋+1137~1236 n100 pool백테 **REBUILT_OK**(pool캐시300·bt_results100·API draw-index100). knobs=markov0.55/review0.85/statHINT52 · `_get_draws_before` nopeek. ge3는 모니터만. **1237 양산아님**. 브라우저 Ctrl+F5 후 테스트로또·백테패널/`testlotto-detail.html?draw=1236` 확인. 형 다음 지시 대기.
- 완료조건: 형 새 지시 1건
- 선행완료: K-FORCE-POOL-BACKTEST-100 REBUILT_OK · K-UI-DETAIL-POOL10x5 PATCHED
- 승인필요: 형 다음 지시
- 선행조건: 없음
- 최종갱신: 2026-08-11


## WORKSTATE
IDLE

---

## 메모
- 서버: `python run_v13.py` · 7021
- Ctrl+F5 권장 (static ?v=20260811b)
- 강제 재백테: `python tools/_k_force_pool_backtest_100.py`
