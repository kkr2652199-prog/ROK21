# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-AUX-DIAG-DONE
- 할일: aux ablation 완료 · worst **pattern_spotlight** · balance_keeper markov 억제 · ge3 전 시나리오 **0.0800** · 회복 방향 결정 · **형 GO 대기**
- 완료조건: spotlight/balance 튜닝 또는 aux path 변경 지시서 + 형 GO
- 선행완료: K-AUX-DIAG 6시나리오 ablation (1135~1234 n=100)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-AUX-DIAG** — baseline ge3=0.0800 · survival 0.668 · spotlight OFF→surv 0 · balance OFF→surv 0.948
- **K-FUSION-QUOTA-FIX** — ge3=0.0800 · quota 20/60/20 · FAIL (>0.09)
- **K-ENGINE-PHASE1-HOLD** — fusion diag AUX_PATH_BOTTLENECK · ge3=0.0900
