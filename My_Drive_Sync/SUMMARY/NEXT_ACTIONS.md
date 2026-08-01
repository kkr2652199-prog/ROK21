# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: COMBO-V1/V2 wire HOLD · baseline 미개선 · 형 GO 또는 10SET·배제 재설계 전까지 survey 중단
- 완료조건: STATUS·TEST_PRIORITY 반영 · coordinator 미배선 확인
- 선행완료: K-COMBO-V2 **FAIL** · K-COMBO-SIGNAL-01 hollow PASS · SELECT-FULL FAIL

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-COMBO-V2 (20260801)** — combo_v2 ge3=**0.125** · baseline=0.145 · B3_cov=**100%** · **FAIL**
- **K-COMBO-SIGNAL-01** — AB=0% · FULL 보류(V2로 대체 시도)
- **K-SIGNAL-SELECT-FULL** — combined ge3=0.1218 · FAIL
- V2 pin ge3=0.1447 · wire HOLD
