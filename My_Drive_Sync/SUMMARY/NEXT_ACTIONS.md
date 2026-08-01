# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-FUSION-QUOTA-FIX-DONE
- 할일: fusion ge3 **0.0800** (<0.09 gate) · quota shift 40/40/20→**20/60/20** 적용 완료 · aux path 등 추가 회복 검토 · **형 GO 대기**
- 완료조건: fused ge3 > 0.0900 또는 aux/fusion path 변경 지시서 + 형 GO
- 선행완료: K-FUSION-QUOTA-FIX DEFAULT_QUOTA_WEIGHTS + n=100 bench FAIL

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-BRAIN-SIGNAL-B1-BACKTEST-100** — **FAIL** (2026-08-01) · ge3=0.0600 · virtual 100% · B1 weights도 ge3 무개선
- **K-BRAIN-SIGNAL-B1** — PASS · smoke 10/10
- **K-BRAIN-SIGNAL-BACKTEST-100** — FAIL · 방향1 conf blend
- **K-HIGHWAY-PHASE1-HOLD** — 별도 트랙 · 형 GO 대기
