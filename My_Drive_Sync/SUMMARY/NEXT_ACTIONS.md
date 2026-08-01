# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-BRAIN-SIGNAL-B1-BACKTEST-100
- 할일: B1 virtual draws stack walk-forward n=100 · ge3 vs 0.0600 · **형 GO 대기**
- 완료조건: 형 GO + 백테 실행·보고서
- 선행완료: K-BRAIN-SIGNAL-B1 **PASS** (make_signal_draws + coordinator weights 경로 · smoke 10/10 virtual)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-BRAIN-SIGNAL-B1** — **PASS** (2026-08-01) · virtual draws weights 주입 · smoke virtual 10/10
- **K-BRAIN-SIGNAL-BACKTEST-100** — **FAIL** · ge3=0.0600 · confidence blend (방향1)
- **K-BRAIN-SIGNAL-TUNE** — _MIN_MAX_SIM 조정 · B1 우선 · **형 GO 대기**
- **K-HIGHWAY-PHASE1-HOLD** — ge3=0.0600 · 롤백/HOLD/튜닝 **형 GO 대기**
