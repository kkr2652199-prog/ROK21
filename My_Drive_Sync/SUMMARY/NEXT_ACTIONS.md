# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-UI-BT-PRELOAD-DONE
- 할일: actuals+pool-index batch push 완료 · Ctrl+F5 후 백테 200회 즉시전환 확인 · 다음축 **형 GO 대기**
- 완료조건: 브라우저 QA OK + 형 GO
- 선행완료: commit `710d5a3` · JS `20260803c`

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-UI-BT-PRELOAD** — draw-index actuals 200 · pool-index 13 · per-draw fetch 제거
- **K-FUSION-INNOVATION** — ge3=0.09 tie · rolled back · V2 live
