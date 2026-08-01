# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-BRAIN-SIGNAL-TUNE
- 할일: BACKTEST-100 **FAIL** ge3=0.0600(=highway 동일) · signal_active 100% · _MIN_MAX_SIM 0.90→0.85 재검증 · **형 GO 대기**
- 완료조건: 형 GO + 튜닝·재백테·보고서
- 선행완료: K-BRAIN-SIGNAL-BACKTEST-100 **FAIL** (ge3=0.0600 · signal_active=100% · UI draw1235 5장)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-BRAIN-SIGNAL-BACKTEST-100** — **FAIL** (2026-08-01) · ge3=0.0600 · signal_active=100% · DB 505행 · UI **1235회차** 5장
- **K-BRAIN-SIGNAL-A1** — **PASS** · pattern_signal + coordinator blend · e68abca
- **K-HIGHWAY-PHASE1-HOLD** — ge3=0.0600 · 롤백/HOLD/튜닝 **형 GO 대기** (별도 트랙)
- **K-10SET-DET-LAB-FULL** — pool10 ge3=**0.1218** p=0.201 · QUICK 0.145→FULL collapse · **FAIL**
- V2 pin ge3=0.1447 · wire HOLD
