# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ENGINE-PHASE1-HOLD-DONE
- 할일: fusion bottleneck **AUX_PATH_BOTTLENECK** 판정 · diag ge3=0.0900 · quota 0.40/aux 0.67 · 회복 방향 결정 · **형 GO 대기**
- 완료조건: quota/aux 튜닝 또는 fusion path 변경 지시서 + 형 GO
- 선행완료: K-ENGINE-PHASE1-HOLD STEP1 window100 롤백 + STEP2 fusion diag

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-BRAIN-SIGNAL-B1-BACKTEST-100** — **FAIL** (2026-08-01) · ge3=0.0600 · virtual 100% · B1 weights도 ge3 무개선
- **K-BRAIN-SIGNAL-B1** — PASS · smoke 10/10
- **K-BRAIN-SIGNAL-BACKTEST-100** — FAIL · 방향1 conf blend
- **K-HIGHWAY-PHASE1-HOLD** — 별도 트랙 · 형 GO 대기
