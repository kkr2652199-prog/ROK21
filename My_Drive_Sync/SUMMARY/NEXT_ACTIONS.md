# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-POST-LIST-HOLD
- 할일: **양산前**. 분석LOCK완료 · W_CROWD markov/review **0.90** APPLY · SCORE **cand_B**(0.65/0.15/0.20) APPLY · evolve/FGJ **AUDIT_DONE**(evolve0·referee균등·K-F OPEN·K-G DORMANT·K-J DUAL). **다음후보**=합동smoke재검증 / K-F markov learn배선 / K-J referee SSOT. **1237 양산아님**. 형 다음 지시 1건.
- 완료조건: 형 새 지시 1건
- 선행완료: K-ANALYSIS-LOCK · K-W-CROWD-BY-BRAIN APPLY · K-SCORE-WEIGHTS-RETUNE APPLY · K-EVOLVE-FGJ-AUDIT
- 승인필요: 형 다음 지시
- 선행조건: 없음
- 최종갱신: 2026-08-11


## WORKSTATE
IDLE

---

## 메모
- 서버: `python run_v13.py` · 7021
- knobs: BLEND m0.55/r0.85 · W 0.90/0.10 · SCORE cand_B · HINT stat52
- 강제 재백테(노브변경 후 권장): `python tools/_k_force_pool_backtest_100.py`
