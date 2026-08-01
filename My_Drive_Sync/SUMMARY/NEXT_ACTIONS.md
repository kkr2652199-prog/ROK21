# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ENGINE-PHASE1-HOLD
- 할일: markov window100 solo **FAIL** ge3=0.0850(≤0.1300) · B1 rollback 완료 · window100 롤백 vs fusion 회복 백테 · **형 GO 대기**
- 완료조건: 형 GO + window100 유지/롤백 결정 + fusion ge3 재측정
- 선행완료: K-ENGINE-PHASE1 STEP1~3 (B1 rollback · window100 · solo n=200 FAIL)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-BRAIN-SIGNAL-B1-BACKTEST-100** — **FAIL** (2026-08-01) · ge3=0.0600 · virtual 100% · B1 weights도 ge3 무개선
- **K-BRAIN-SIGNAL-B1** — PASS · smoke 10/10
- **K-BRAIN-SIGNAL-BACKTEST-100** — FAIL · 방향1 conf blend
- **K-HIGHWAY-PHASE1-HOLD** — 별도 트랙 · 형 GO 대기
