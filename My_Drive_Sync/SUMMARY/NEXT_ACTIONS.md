# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-BRAIN-SIGNAL-TUNE
- 할일: B1-BACKTEST-100 **FAIL** ge3=0.0600(=방향1·highway 동일) · _MIN_MAX_SIM 0.90→0.85 또는 B1 롤백 · **형 GO 대기**
- 완료조건: 형 GO + 튜닝/롤백 결정·실행·재백테
- 선행완료: K-BRAIN-SIGNAL-B1-BACKTEST-100 **FAIL** (ge3=0.0600 · virtual_active=100% · delta=0)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-BRAIN-SIGNAL-B1-BACKTEST-100** — **FAIL** (2026-08-01) · ge3=0.0600 · virtual 100% · B1 weights도 ge3 무개선
- **K-BRAIN-SIGNAL-B1** — PASS · smoke 10/10
- **K-BRAIN-SIGNAL-BACKTEST-100** — FAIL · 방향1 conf blend
- **K-HIGHWAY-PHASE1-HOLD** — 별도 트랙 · 형 GO 대기
