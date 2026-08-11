# 순서진행 — 강제BT v2 · 몰아주기손실 · K-J

시각: 2026-08-11 · 형 「순서대로」 · 양산前 · **1237아님** · ge3 클레임 금지

## ① 강제100회 재백테 (cand_B · W0.9)

- 도구: `tools/_k_force_pool_backtest_100.py` → 산출 `_v2`
- 리셋 후 WF **1137~1236** n100 · peek OK · pool_view_cache **300** · draw_results **100**
- knobs: BLEND m0.55/r0.85 · SCORE cand_B (0.65/0.15/0.20) · HINT52 · W_CROWD 코드 live 0.90
- 모니터(클레임금지): mean_hits **2.59** · **4등=6** · **5등=48**
- 교차감사: `20260811_KBT100_DEEP_AUDIT_v2` · **NO_HARD_BUG** · bad_sets0 · bt_mismatch0
- 근거: `docs/benchmarks/20260811_KFORCE_POOL_BACKTEST_100_v2.json`

## ② 몰아주기 손실 (pool>repack)

- 도구: `tools/_k_repack_loss_audit.py`
- 판정: **AUDIT_DONE_PROPOSE_HOLD** · cause=`POOL_BEST_DROPPED_FROM_REPACK`
- 뇌별 pool>repack: stat**45** / markov**41** / review**39**
- 손실 시 pool_best∈repack: **0** (전원 탈락) · assemble=`signal_top` · slots=**2**/brain
- 티어하락(손실회): 5→0 **41** · 4→0 **3** · 4→5 **1**
- 코드 미적용. 제안 P1 slots↑ / P2 union · 기본 **P3 HOLD**(사후히트≠live신호)
- 근거: `docs/benchmarks/20260811_KREPACK_LOSS_AUDIT.json`

## ③ K-J referee SSOT

- **SSOT** = `get_referee_weights()` (발권 coordinator/aux_referee)
- DB `testlotto_brain_weights.current_weight` = **미러만** (구식 `1+avg*0.1` 제거)
- `apply_feedback` → `get_referee_weights_global()` 로 3뇌 미러 동기화
- UI `detail_service`: `current_weight`/`referee_weight`=live · `db_weight_mirror` 병기
- `tune_snapshot`에 W_CROWD/W_STRUCT_BY_BRAIN 추가
- FINDINGS K-J → **PATCHED**
- 강제리셋 직후 learn=0 → live=DB=균등 **0.333** (일치)

## 다음

형 지시 1건: 몰아주기 P1/P2 게이트 승인 여부 · 또는 다른 튜닝. **1237 양산 아님**.
