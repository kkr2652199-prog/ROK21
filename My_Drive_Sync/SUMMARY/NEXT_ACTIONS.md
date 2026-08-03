# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-UI-BT-INSTANT-DONE
- 할일: 백테 DB→페이지 즉시 반응 live · QUICK/FULL reval 유지 · 다음축(pin갭 등) **형 GO 대기**
- 완료조건: 형 GO
- 선행완료: pool GET 자동WF 제거 · backtest_only 즉시표시 · revalidate pool보존

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- GET /pool-view/{n}: 캐시 or backtest_only 즉시 · compute/refresh만 WF
- 1100 실측 ~86ms (구 ~15s)
