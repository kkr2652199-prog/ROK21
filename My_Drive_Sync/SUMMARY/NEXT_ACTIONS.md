# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: SELECT/EXCLUDE wire HOLD 유지 · 형 GO 또는 새 축(10SET·패턴튜닝) 전까지 survey 중단
- 완료조건: STATUS·TEST_PRIORITY 반영 · wire 미배선 확인
- 선행완료: K-EXCLUDE-SURVEY **FAIL** · K-SIGNAL-SELECT-FULL **FAIL**

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-EXCLUDE-SURVEY (20260801)** — QUICK n=200 · λ=[0,0.25,0.5,0.75,1] · best exclude ge3=**0.145**=baseline · λ0.25 ge3=**0.135** · **FAIL**
- **TESTLOTTO UI+DB (20260730)** — `testlotto_backtest_runs` 2건 · pool-view API · 7021 테스트로또 탭
- V2 pin ge3=0.1447 · mean=1.7504 (stored)
- **K-SIGNAL-SELECT-FULL** — combined ge3=**0.1218** · p=0.201 · **FAIL** · wire HOLD
- **K-EXCLUDE-HIST-01** — 1~1234 패턴 catalog · 2연속+ 51.7%
- **K-SIGNAL-REPACK-01** — top5 ge3=0.085 · combined 0.145 · 5장 공정 FAIL · r3=1
- **K-QUICK-GATE-01** — BENCH §9 · tail-200 seed=42
- **4AUX_FEEDBACK_REVIEW** — set_no_asc AUX 컷 없음
